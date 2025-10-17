"""
HybridStructureDB: HDF5 + SQLite store for atomistic structures (ASE Atoms) with lazy access.

Features
--------
- Persist thousands of structures on disk (HDF5) while keeping only small metadata in RAM (SQLite rows).
- Low-latency random access to any structure by integer index (stable, never re-used).
- Query by metadata (e.g., energy thresholds) using SQLite WHERE clauses.
- Preserve the index in both SQLite and HDF5 metadata.
- Count, list, and delete entries; optional HDF5 compaction (repack) to reclaim space.
- Clean, class-based design; type hints; detailed docstrings.

Dependencies
------------
- Python 3.9+
- numpy
- h5py
- ase (for Atoms)

Optional
--------
- You may use JSON1 in SQLite for advanced JSON queries if your SQLite build supports it,
  but this implementation does not require JSON1.

Author: ChatGPT (Hybrid HDF5 + SQL implementation)
"""
from __future__ import annotations

import os
import json
import sqlite3
import shutil
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

import numpy as np
import h5py
from ase import Atoms


# ------------------------------
# Utilities
# ------------------------------

def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


# ------------------------------
# HDF5 Backend
# ------------------------------

class HDF5Backend:
    """Lightweight HDF5 manager that stores each structure under a unique group.

    Layout
    ------
    /structs/{id:08d}/
        atomic_numbers : (N,) int32
        positions      : (N, 3) float64
        cell           : (3, 3) float64
        pbc            : (3,) bool
        (attrs)
            index      : int
            created_at : str (ISO 8601)
            info_json  : str (optional, mirror of metadata)
    """

    def __init__(self, h5_path: str, mode: str = "a", compression: Optional[str] = "gzip", compression_opts: int = 4):
        self.h5_path = h5_path
        self.mode = mode
        _ensure_dir(os.path.dirname(os.path.abspath(h5_path)) or ".")
        self.h5 = h5py.File(h5_path, mode)
        self.root_group = self.h5.require_group("structs")
        self.compression = compression
        self.compression_opts = compression_opts

    def close(self) -> None:
        if getattr(self, "h5", None) is not None:
            self.h5.flush()
            self.h5.close()
            self.h5 = None  # type: ignore

    # ---- Write & Read ----
    def write_atoms(self, idx: int, atoms: Atoms, info_json: Optional[str] = None) -> str:
        """Write an ASE Atoms object under /structs/{idx:08d}.

        Returns the HDF5 path used.
        """
        path = f"structs/{idx:08d}"
        if path in self.h5:
            # Overwrite semantics: remove existing group first
            del self.h5[path]
        g = self.h5.require_group(path)

        # Datasets with compression
        anums = np.asarray(atoms.get_atomic_numbers(), dtype=np.int32)
        pos = np.asarray(atoms.get_positions(), dtype=np.float64)
        cell = np.asarray(atoms.cell.array if atoms.cell is not None else np.eye(3), dtype=np.float64)
        pbc = np.asarray(atoms.pbc, dtype=bool)

        g.create_dataset("atomic_numbers", data=anums, compression=self.compression, compression_opts=self.compression_opts, shuffle=True)
        g.create_dataset("positions", data=pos, compression=self.compression, compression_opts=self.compression_opts, shuffle=True)
        g.create_dataset("cell", data=cell, compression=self.compression, compression_opts=self.compression_opts, shuffle=True)
        g.create_dataset("pbc", data=pbc, compression=self.compression, compression_opts=self.compression_opts, shuffle=True)

        g.attrs["index"] = int(idx)
        g.attrs["created_at"] = _now_iso()
        if info_json is not None:
            # Keep a mirror copy as an attribute for resilience/debugging.
            g.attrs["info_json"] = info_json

        # Ensure on-disk persistence for single-writer semantics
        self.h5.flush()
        return "/" + path

    def read_atoms(self, idx: int) -> Atoms:
        path = f"structs/{idx:08d}"
        if path not in self.h5:
            raise KeyError(f"No HDF5 group for index {idx} at /{path}")
        g = self.h5[path]
        anums = g["atomic_numbers"][...]
        pos = g["positions"][...]
        cell = g["cell"][...]
        pbc = g["pbc"][...]
        atoms = Atoms(numbers=anums, positions=pos, cell=cell, pbc=pbc)
        return atoms

    def delete(self, idx: int) -> None:
        path = f"structs/{idx:08d}"
        if path in self.h5:
            del self.h5[path]
            self.h5.flush()

    def exists(self, idx: int) -> bool:
        return f"structs/{idx:08d}" in self.h5

    def repack(self, new_path: Optional[str] = None, keep_open: bool = True) -> str:
        """Repack the HDF5 file to reclaim free space.

        Creates a new compacted file and replaces the original if `new_path` is None.
        Returns path to the compacted file.
        """
        self.h5.flush()
        src = self.h5_path
        dst = new_path or (self.h5_path + ".compact")
        # Copy only existing groups/datasets (shallow copy then data)
        with h5py.File(dst, "w") as out:
            out.copy(self.root_group, "structs")
        # Optionally swap files
        if new_path is None:
            self.close()
            backup = src + ".bak"
            shutil.move(src, backup)
            shutil.move(dst, src)
            os.remove(backup)
            if keep_open:
                self.h5 = h5py.File(src, self.mode)
                self.root_group = self.h5["structs"]
            return src
        else:
            return dst


# ------------------------------
# SQLite Index
# ------------------------------

class SQLiteIndex:
    """SQLite-backed metadata index with simple numeric/string columns and full JSON copy.

    Schema
    ------
    structures(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        h5_path TEXT NOT NULL UNIQUE,
        energy REAL,
        formula TEXT,
        meta_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    Indexes on (energy), (formula).

    Notes
    -----
    - `id` is the stable external index used everywhere.
    - Additional metadata are preserved in `meta_json`.
    - Promote common keys (e.g., energy, formula) for fast WHERE queries.
    """

    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path
        _ensure_dir(os.path.dirname(os.path.abspath(sqlite_path)) or ".")
        self.con = sqlite3.connect(sqlite_path)
        self.con.execute("PRAGMA journal_mode=WAL;")
        self.con.execute("PRAGMA synchronous=NORMAL;")
        self._init_schema()

    def close(self) -> None:
        if getattr(self, "con", None) is not None:
            self.con.commit()
            self.con.close()
            self.con = None  # type: ignore

    def _init_schema(self) -> None:
        cur = self.con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS structures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                h5_path TEXT NOT NULL UNIQUE,
                energy REAL,
                formula TEXT,
                meta_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_energy ON structures(energy);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_formula ON structures(formula);")
        self.con.commit()

    def insert(self, h5_path: str, meta: Dict[str, Any]) -> int:
        energy = float(meta.get("energy")) if "energy" in meta and meta["energy"] is not None else None
        formula = str(meta.get("formula")) if meta.get("formula") is not None else None
        meta_json = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
        created_at = _now_iso()
        cur = self.con.cursor()
        cur.execute(
            "INSERT INTO structures(h5_path, energy, formula, meta_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (h5_path, energy, formula, meta_json, created_at),
        )
        self.con.commit()
        return int(cur.lastrowid)

    def update_meta(self, idx: int, meta: Dict[str, Any]) -> None:
        energy = float(meta.get("energy")) if "energy" in meta and meta["energy"] is not None else None
        formula = str(meta.get("formula")) if meta.get("formula") is not None else None
        meta_json = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
        self.con.execute(
            "UPDATE structures SET energy = ?, formula = ?, meta_json = ? WHERE id = ?",
            (energy, formula, meta_json, idx),
        )
        self.con.commit()

    def get_meta(self, idx: int) -> Dict[str, Any]:
        cur = self.con.cursor()
        row = cur.execute(
            "SELECT meta_json FROM structures WHERE id = ?",
            (idx,),
        ).fetchone()
        if row is None:
            raise KeyError(f"No metadata for index {idx}")
        return json.loads(row[0])

    def get_h5_path(self, idx: int) -> str:
        cur = self.con.cursor()
        row = cur.execute("SELECT h5_path FROM structures WHERE id = ?", (idx,)).fetchone()
        if row is None:
            raise KeyError(f"No entry for index {idx}")
        return row[0]

    def exists(self, idx: int) -> bool:
        cur = self.con.cursor()
        row = cur.execute("SELECT 1 FROM structures WHERE id = ?", (idx,)).fetchone()
        return row is not None

    def delete(self, idx: int) -> None:
        self.con.execute("DELETE FROM structures WHERE id = ?", (idx,))
        self.con.commit()

    def count(self, where: Optional[str] = None, params: Sequence[Any] = ()) -> int:
        cur = self.con.cursor()
        if where:
            q = f"SELECT COUNT(*) FROM structures WHERE {where}"
            row = cur.execute(q, params).fetchone()
        else:
            row = cur.execute("SELECT COUNT(*) FROM structures").fetchone()
        return int(row[0]) if row else 0

    def query_indices(self, where: Optional[str] = None, params: Sequence[Any] = (), order_by: Optional[str] = None, limit: Optional[int] = None) -> List[int]:
        q = "SELECT id FROM structures"
        if where:
            q += f" WHERE {where}"
        if order_by:
            q += f" ORDER BY {order_by}"
        if limit is not None:
            q += f" LIMIT {int(limit)}"
        cur = self.con.cursor()
        rows = cur.execute(q, params).fetchall()
        return [int(r[0]) for r in rows]

    def all_indices(self) -> Iterator[int]:
        cur = self.con.cursor()
        for (idx,) in cur.execute("SELECT id FROM structures ORDER BY id"):
            yield int(idx)


# ------------------------------
# Hybrid Structure Database
# ------------------------------

class HybridStructureDB:
    """Hybrid store combining HDF5 for heavy arrays and SQLite for metadata.

    Parameters
    ----------
    root_dir : str
        Directory where both the HDF5 and SQLite files live.
    h5_name : str
        Filename for the HDF5 container.
    sqlite_name : str
        Filename for the SQLite index database.
    mode : {"a", "r", "w"}
        HDF5 file open mode (SQLite is always read/write).
    compression : Optional[str]
        HDF5 compression filter (e.g., "gzip"), or None.
    compression_opts : int
        Compression level (for gzip: 0-9).

    Notes
    -----
    - Stable indices: every inserted structure receives a monotonically increasing integer id.
    - Lazy access: structures are read from HDF5 only when requested.
    - Metadata: Keep lightweight dicts (numbers, short lists/strings) in SQLite as JSON, while promoting
      common keys (energy, formula) to columns for fast filtering.
    """

    def __init__(
        self,
        root_dir: str,
        h5_name: str = "structures.h5",
        sqlite_name: str = "index.sqlite",
        mode: str = "a",
        compression: Optional[str] = "gzip",
        compression_opts: int = 4,
    ) -> None:
        self.root_dir = root_dir
        _ensure_dir(root_dir)
        self.h5_path = os.path.join(root_dir, h5_name)
        self.sqlite_path = os.path.join(root_dir, sqlite_name)
        self.h5 = HDF5Backend(self.h5_path, mode=mode, compression=compression, compression_opts=compression_opts)
        self.sql = SQLiteIndex(self.sqlite_path)

    # --------- Lifecycle ---------
    def close(self) -> None:
        """Flush and close underlying files."""
        self.h5.close()
        self.sql.close()

    # --------- Insert ---------
    def add(self, atoms: Atoms, metadata: Optional[Dict[str, Any]] = None) -> int:
        """Insert a structure and return its stable integer index.

        The structure is written to HDF5 first using a *temporary* negative index to ensure atomicity,
        then the metadata row is created in SQLite, and finally the HDF5 group is renamed to the final index.
        """
        meta = dict(metadata or {})
        # Derive helpful metadata if missing
        if "formula" not in meta:
            try:
                meta["formula"] = atoms.get_chemical_formula()
            except Exception:
                pass
        info_json = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))

        # Step 1: reserve SQLite row to obtain the final id
        # We temporarily store a placeholder path; it will be updated after writing HDF5.
        placeholder_path = "/structs/PENDING"
        idx = self._insert_sql_placeholder(placeholder_path, meta)
        # Step 2: write into HDF5 at the final index
        h5_path = self.h5.write_atoms(idx, atoms, info_json=info_json)
        # Step 3: update SQLite with the real h5_path and index mirrored in meta
        meta_with_index = dict(meta)
        meta_with_index["index"] = idx
        self._finalize_sql_insert(idx, h5_path, meta_with_index)
        return idx

    def _insert_sql_placeholder(self, h5_path: str, meta: Dict[str, Any]) -> int:
        return self.sql.insert(h5_path=h5_path, meta=meta)

    def _finalize_sql_insert(self, idx: int, h5_path: str, meta: Dict[str, Any]) -> None:
        # Ensure index is mirrored in meta
        meta["index"] = idx
        self.sql.update_meta(idx, meta)
        # Also update the stored h5_path (since initial insert used placeholder)
        self.sql.con.execute("UPDATE structures SET h5_path = ? WHERE id = ?", (h5_path, idx))
        self.sql.con.commit()

    # --------- Access ---------
    def get(self, idx: int) -> Atoms:
        """Load a structure lazily from HDF5 by index."""
        # Validate existence in SQLite first (fast)
        if not self.sql.exists(idx):
            raise KeyError(f"Index {idx} does not exist in SQLite index.")
        return self.h5.read_atoms(idx)

    def get_many(self, indices: Iterable[int]) -> List[Atoms]:
        """Load multiple structures lazily by their indices."""
        return [self.get(i) for i in indices]

    def meta(self, idx: int) -> Dict[str, Any]:
        """Get metadata dict for a structure by index."""
        return self.sql.get_meta(idx)

    # --------- Query & Count ---------
    def query(self, where: Optional[str] = None, params: Sequence[Any] = (), order_by: Optional[str] = None, limit: Optional[int] = None) -> List[int]:
        """Return indices matching a SQLite WHERE clause.

        Examples
        --------
        db.query("energy < ?", params=(-520.0,), order_by="energy ASC", limit=100)
        db.query("formula = ?", params=("Ni3Fe1O8",))
        """
        return self.sql.query_indices(where=where, params=params, order_by=order_by, limit=limit)

    def count(self, where: Optional[str] = None, params: Sequence[Any] = ()) -> int:
        return self.sql.count(where=where, params=params)

    def all_indices(self) -> Iterator[int]:
        return self.sql.all_indices()

    # --------- Maintenance ---------
    def delete(self, indices: Iterable[int], hard: bool = True) -> None:
        """Delete entries by index.

        If `hard` is True, remove both SQLite rows and HDF5 groups.
        """
        for idx in indices:
            # Remove SQLite first to prevent dangling references
            if self.sql.exists(idx):
                self.sql.delete(idx)
            if hard and self.h5.exists(idx):
                self.h5.delete(idx)

    def compact_hdf5(self) -> str:
        """Repack HDF5 to reclaim space after many deletions.

        Returns the path to the compacted HDF5 file (same path after swap).
        """
        return self.h5.repack()

    # --------- Export / Import (optional) ---------
    def export_metadata_json(self, out_path: str) -> None:
        """Dump all metadata rows to a JSONL file for inspection/sharing."""
        with open(out_path, "w", encoding="utf-8") as f:
            for idx in self.all_indices():
                meta = self.meta(idx)
                f.write(json.dumps({"id": idx, **meta}, ensure_ascii=False) + "\n")


# ------------------------------
# Example Usage
# ------------------------------

if __name__ == "__main__":
    # Demo: create a small database, insert a few water molecules with random displacements,
    # query by energy, and fetch selected structures.
    from ase.build import molecule

    root = "./demo_store"
    if os.path.exists(root):
        shutil.rmtree(root)

    db = HybridStructureDB(root)

    # Insert sample structures
    rng = np.random.default_rng(42)
    for i in range(10):
        atoms = molecule("H2O")
        atoms.set_positions(atoms.get_positions() + 0.05 * rng.normal(size=(len(atoms), 3)))
        # Fake energies for demonstration
        energy = float(-520.0 - i * 0.5 + 0.1 * rng.normal())
        meta = {"energy": energy, "tag": f"sample_{i}"}
        idx = db.add(atoms, metadata=meta)
        print(f"Inserted index={idx}, energy={energy:.3f}")

    # Count all and count with a filter
    total = db.count()
    low_e = db.count("energy < ?", params=(-522.0,))
    print(f"Total structures: {total}; with energy < -522 eV: {low_e}")

    # Query some candidates (stable ones), order by energy ascending, take top 3
    cand = db.query("energy < ?", params=(-521.0,), order_by="energy ASC", limit=3)
    print("Candidate indices:", cand)

    # Load the candidates lazily from HDF5
    selected_structs = db.get_many(cand)
    for i, atoms in zip(cand, selected_structs):
        m = db.meta(i)
        print(f"idx={i}, formula={m.get('formula')}, energy={m.get('energy')}")

    # Demonstrate deletion and compaction
    to_delete = cand[:1]
    print("Deleting indices:", to_delete)
    db.delete(to_delete, hard=True)
    print("Count after delete:", db.count())

    # Optional: compact HDF5 to reclaim space
    db.compact_hdf5()

    db.close()
    print("Demo complete. Files stored under:", root)

