# ============================
# storage_backend.py (updated)
# ============================
from __future__ import annotations

import os
import json
import glob
import pickle
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Union, Tuple

import h5py
import numpy as np

StorageType = Union[List[Any], Dict[int, Any]]

class StorageBackend(ABC):
    """
    Abstract interface for container storage backends.

    Notes
    -----
    - `add` accepts an optional `metadata` mapping. Backends that do not use metadata
      may ignore it.
    - `get(obj_id=None)` may return a *lazy sequence* view (rather than a concrete list)
      when `obj_id` is None, to avoid loading everything into RAM. Code that needs a real
      list can call `list(...)` on that view.
    """

    @abstractmethod
    def add(self, obj: Any, metadata: Optional[Dict[str, Any]] = None) -> int:
        """Store object and return its integer ID."""
        raise NotImplementedError

    @abstractmethod
    def get(self, obj_id: Optional[int] = None):
        """
        Retrieve object by ID. If `obj_id` is None, return a *lazy* container view
        over all objects (implementing `__len__`, `__iter__`, and `__getitem__`).
        """
        raise NotImplementedError

    @abstractmethod
    def remove(self, obj_id: int) -> None:
        """Delete object by ID (no-op if already deleted)."""
        raise NotImplementedError

    @abstractmethod
    def list_ids(self) -> List[int]:
        """Return list of all object IDs (ascending)."""
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        """Return total number of stored objects."""
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Remove all objects from the store."""
        raise NotImplementedError

    # ---------- Optional (metadata-aware) API ----------
    def get_meta(self, obj_id: int) -> Dict[str, Any]:  # pragma: no cover (optional)
        raise NotImplementedError

    def set_meta(self, obj_id: int, meta: Dict[str, Any]) -> None:  # pragma: no cover
        raise NotImplementedError

    def query_ids(self, where: str, params: Sequence[Any] = ()) -> List[int]:  # pragma: no cover
        """SQL-like query support (if available)."""
        raise NotImplementedError

    # ---------- Convenience iteration (can be overridden) ----------
    def iter_ids(self, batch_size: Optional[int] = None) -> Iterator[int]:
        for cid in self.list_ids():
            yield cid

    def iter_objects(self, batch_size: Optional[int] = None) -> Iterator[tuple[int, Any]]:
        for cid in self.iter_ids(batch_size):
            yield cid, self.get(cid)


# -----------------------------
# In-memory (list/dict) backend
# -----------------------------
class MemoryStorage(StorageBackend):
    """
    Generic in-memory storage.

    The container can be either a list (sequential storage) or a dict that maps
    integer IDs to objects. IDs are always integers.
    """

    def __init__(self, initial: StorageType | None = None) -> None:
        self._data: StorageType = initial if initial is not None else []
        self._meta: Dict[int, Dict[str, Any]] = {}

    def add(self, obj: Any, metadata: Optional[Dict[str, Any]] = None) -> int:
        if isinstance(self._data, list):
            self._data.append(obj)
            idx = len(self._data) - 1
        else:
            idx = max(self._data.keys(), default=-1) + 1
            self._data[idx] = obj
        if metadata is not None:
            self._meta[idx] = metadata
        return idx

    def set(self, container: StorageType) -> int:
        if not isinstance(container, (list, dict)):
            raise TypeError("container must be a list or a dict[int, Any]")
        self._data = container
        self._meta.clear()
        return len(self._data) - 1 if isinstance(self._data, list) else (max(self._data.keys(), default=-1))

    def remove(self, obj_id: int) -> None:
        try:
            del self._data[obj_id]
        except (IndexError, KeyError):
            raise KeyError(f"No object found with id {obj_id}") from None
        self._meta.pop(obj_id, None)

    def get(self, obj_id: Optional[int] = None):
        if obj_id is None:
            return self._data
        try:
            return self._data[obj_id]
        except (IndexError, KeyError):
            raise KeyError(f"No object found with id {obj_id}") from None

    def list_ids(self) -> List[int]:
        return list(range(len(self._data))) if isinstance(self._data, list) else list(self._data.keys())

    def count(self) -> int:
        return len(self._data)

    def clear(self) -> None:
        if isinstance(self._data, list):
            self._data.clear()
        else:
            self._data = {}
        self._meta.clear()

    # Optional metadata helpers
    def get_meta(self, obj_id: int) -> Dict[str, Any]:
        return dict(self._meta.get(obj_id, {}))

    def set_meta(self, obj_id: int, meta: Dict[str, Any]) -> None:
        self._meta[obj_id] = dict(meta)

# -----------------------------
# SQLite (pickle BLOB) backend
# -----------------------------
class SQLiteStorage(StorageBackend):
    """SQLite-based storage, pickling objects into a BLOB."""

    def __init__(self, db_path: str):
        dir_path = os.path.dirname(db_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS containers (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                data BLOB NOT NULL
            );
            """
        )
        self.conn.commit()

    def add(self, obj: Any, metadata: Optional[Dict[str, Any]] = None) -> int:
        blob = pickle.dumps(obj)
        cur = self.conn.cursor()
        cur.execute("INSERT INTO containers (data) VALUES (?);", (blob,))
        self.conn.commit()
        return int(cur.lastrowid)

    def get(self, obj_id: Optional[int] = None):
        if obj_id is None:
            # Return a lightweight proxy of all objects (loads on iteration)
            return _LazySQLiteView(self)
        cur = self.conn.cursor()
        cur.execute("SELECT data FROM containers WHERE id = ?;", (obj_id,))
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"No container with id {obj_id}")
        return pickle.loads(row[0])

    def remove(self, obj_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM containers WHERE id = ?;", (obj_id,))
        if cur.rowcount == 0:
            raise KeyError(f"No container with id {obj_id}")
        self.conn.commit()

    def list_ids(self) -> List[int]:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM containers ORDER BY id ASC;")
        return [int(row[0]) for row in cur.fetchall()]

    def count(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM containers;")
        return int(cur.fetchone()[0])

    def clear(self) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM containers;")
        self.conn.commit()

    def iter_ids(self, batch_size: Optional[int] = 1000) -> Iterator[int]:
        cur = self.conn.cursor()
        last = 0
        while True:
            if batch_size:
                cur.execute(
                    "SELECT id FROM containers WHERE id > ? ORDER BY id ASC LIMIT ?;",
                    (last, batch_size),
                )
            else:
                cur.execute(
                    "SELECT id FROM containers WHERE id > ? ORDER BY id ASC;",
                    (last,),
                )
            rows = cur.fetchall()
            if not rows:
                break
            for (cid,) in rows:
                yield int(cid)
            last = int(rows[-1][0])

class _LazySQLiteView:
    """Lazy sequence-like view over all objects in SQLiteStorage."""

    def __init__(self, store: SQLiteStorage):
        self._s = store

    def __len__(self) -> int:
        return self._s.count()

    def __iter__(self):
        for cid in self._s.iter_ids():
            yield self._s.get(cid)

    def __getitem__(self, i):
        if isinstance(i, slice):
            ids = self._s.list_ids()[i]
            return [self._s.get(cid) for cid in ids]
        else:
            cid = self._s.list_ids()[i]
            return self._s.get(cid)


# -----------------------------
# Hybrid (HDF5 + SQLite) backend
# -----------------------------
"""IO/storage_backend.py

Hybrid storage backend combining SQLite (index + metadata) and HDF5 (object
payloads) for efficient, scalable persistence of Python objects related to
atomistic simulations.

This module provides the :class:`HybridStorage` class, which stores a pickled
payload per object in an HDF5 dataset and mirrors essential metadata (energy,
atom count, composition, empirical formula) in a lightweight SQLite schema to
enable fast queries without loading full objects.

Design goals:
    * **Performance**: metadata queries are served from SQLite indices; payloads
      are compressed with gzip inside HDF5 for efficient disk usage.
    * **Convenience**: automatic extraction of energy and species labels from
      common attribute names (e.g., ``obj.E`` or
      ``obj.AtomPositionManager.atomLabelsList``).
    * **Stability**: robust to arrays or scalars for energies and labels.

Notes:
    - The composition table uses an Entity–Attribute–Value (EAV) layout to
      efficiently query per-species counts across objects.
    - Formulas are rendered with alphabetical element ordering for simplicity.

Example:
    >>> store = HybridStorage("./hybrid_store")
    >>> obj_id = store.add(obj)  # obj carries .E and AtomPositionManager
    >>> meta = store.get_meta(obj_id)
    >>> payload = store.get(obj_id)

"""
class HybridStorage:
    """
    Hybrid backend:
      - SQLite: index + metadata (species registry, compositions, scalars)
      - HDF5:   payload pickled & compressed
    Guarantees:
      - Stable species-to-column mapping via `species.rank` (first-seen order).
      - Sparse compositions, dense export on request.
      - Generic scalar store (E, E1, E2, ...).
    """


    """Hybrid SQLite + HDF5 object store.

    The storage model separates **metadata** (SQLite) from **payloads** (HDF5):

    - *SQLite* stores: ``id``, ``energy``, ``natoms``, ``formula``, and a JSON
      blob ``meta_json`` (currently including the composition map). A second
      table, ``compositions(object_id, species, count)``, holds an EAV view of
      per-species counts to enable selective queries.
    - *HDF5* stores: one dataset per object under the group ``/objs`` named as
      zero-padded IDs (``00000001``, ...). Each dataset contains the raw pickled
      bytes and carries attributes for quick inspection (``id``, ``energy`` when
      available).

    Attributes:
        root_dir: Absolute path to the storage root directory.
        h5_path: File path to the HDF5 file (``db_objects.h5``).
        sqlite_path: File path to the SQLite index (``db_index.sqlite``).

    Forward-looking:
        The schema leaves room for additional indices (e.g., ranges over energy
        or natoms) and user-defined metadata; ``meta_json`` can be extended
        without schema migration.
    """
    # scalar keys we auto-pick if present as numeric attrs in SingleRun/APM
    _SCALAR_PREFIXES = ("E", "energy", "Etot", "Ef", "free_energy")

    def __init__(self, root_dir: str = "./hybrid_store", access: str = "rw"):
        """
        access: 'rw' (default) or 'ro'
        """
        if access not in ("rw", "ro"):
            raise ValueError("access must be 'rw' or 'ro'")
        self.read_only = (access == "ro")

        self.root_dir = os.path.abspath(root_dir)
        os.makedirs(self.root_dir, exist_ok=True)

        self.h5_path = os.path.join(self.root_dir, "db_objects.h5")
        self.sqlite_path = os.path.join(self.root_dir, "db_index.sqlite")

        # --- SQLite ---
        if self.read_only:
            # Read-only URI; do not mutate schema
            self._conn = sqlite3.connect(f"file:{self.sqlite_path}?mode=ro",
                                         uri=True, check_same_thread=False)
            self._conn.execute("PRAGMA foreign_keys = ON;")
        else:
            self._conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
            self._conn.execute("PRAGMA foreign_keys = ON;")
            self._init_schema()

        # --- HDF5 ---
        h5_mode = "r" if self.read_only else "a"
        self._h5 = h5py.File(self.h5_path, h5_mode)
        # Ensure the group exists in RW; in RO, require it to be present
        if self.read_only:
            if "objs" not in self._h5:
                raise RuntimeError("Read-only open requires existing 'objs' group in HDF5.")
            self._grp = self._h5["objs"]
        else:
            self._grp = self._h5.require_group("objs")

    # Guard for any mutating method
    def _assert_writable(self):
        if self.read_only:
            raise RuntimeError("HybridStorage is read-only; writing is not allowed.")

    # ---------------- Schema ----------------
    def _init_schema(self):
        cur = self._conn.cursor()
        # One atomic transaction for everything
        with self._conn:  # BEGIN; ... COMMIT; (or ROLLBACK on exception)
            # --- DDL ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS species (
                    species_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol     TEXT UNIQUE NOT NULL,
                    rank       INTEGER NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS objects (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    energy    REAL,
                    natoms    INTEGER,
                    formula   TEXT,
                    meta_json TEXT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS compositions (
                    object_id  INTEGER NOT NULL,
                    species_id INTEGER NOT NULL,
                    count      REAL NOT NULL,
                    PRIMARY KEY (object_id, species_id),
                    FOREIGN KEY (object_id)  REFERENCES objects(id)  ON DELETE CASCADE,
                    FOREIGN KEY (species_id) REFERENCES species(species_id) ON DELETE RESTRICT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scalars (
                    object_id INTEGER NOT NULL,
                    key       TEXT    NOT NULL,
                    value     REAL,
                    PRIMARY KEY (object_id, key),
                    FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS object_hashes (
                    object_id INTEGER PRIMARY KEY,
                    hash      TEXT NOT NULL,
                    FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
                );
            """)

            # --- Indexes ---
            cur.execute("CREATE INDEX IF NOT EXISTS idx_objects_energy     ON objects(energy);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_comp_sp            ON compositions(species_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_scalars_key        ON scalars(key);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_object_hashes_hash ON object_hashes(hash);")

            # --- Backfill hashes from meta_json when missing ---
            cur.execute("""
                SELECT o.id, o.meta_json
                FROM objects o
                LEFT JOIN object_hashes h ON h.object_id = o.id
                WHERE h.object_id IS NULL;
            """)
            rows = cur.fetchall()
            to_insert = []
            for oid, meta_json in rows:
                if not meta_json:
                    continue
                try:
                    meta = json.loads(meta_json)
                except Exception:
                    continue
                h = None
                if isinstance(meta, dict):
                    h = meta.get("hash") or meta.get("content_hash") or meta.get("sha256")
                if isinstance(h, str) and h:
                    to_insert.append((int(oid), h))

            if to_insert:
                cur.executemany(
                    "INSERT OR IGNORE INTO object_hashes(object_id, hash) VALUES (?, ?);",
                    to_insert
                )

    # ---------------- Helpers ----------------
    @staticmethod
    def _to_float_or_none(x) -> Optional[float]:
        try:
            import numpy as _np
            if isinstance(x, _np.ndarray):
                if x.size == 0:
                    return None
                return float(x.reshape(-1)[0])
            if isinstance(x, (_np.floating, _np.integer)):
                return float(x)
        except Exception:
            pass
        if isinstance(x, (int, float)):
            return float(x)
        return None

    @staticmethod
    def _is_scalar(x) -> bool:
        try:
            import numpy as _np
            if isinstance(x, (int, float, _np.integer, _np.floating)):
                return True
            if isinstance(x, _np.ndarray) and x.ndim == 0:
                return True
        except Exception:
            pass
        return False

    @classmethod
    def merge_roots(
        cls,
        src_a: str,
        src_b: str,
        dst_root: str,
        *,
        dedup: str = "hash",   # "hash" | "payload" | "none"
        compact: bool = True
    ) -> dict:
        """
        Merge two HybridStorage databases (SQLite + HDF5) into a fresh destination.

        Args:
            src_a, src_b: Paths to the *root directories* of the two databases.
                          (If you pass a file path, its directory will be used.)
            dst_root: Path to a *new* root directory to create/populate.
            dedup:   - "hash": skip objects whose content hash already exists in the destination
                     - "payload": compute SHA256 of the pickled payload and skip duplicates
                     - "none": copy everything
            compact: If True, compact the destination HDF5 at the end.

        Returns:
            A small report dict with counts:
              {
                "added_from_a": int,
                "added_from_b": int,
                "skipped_duplicates": int,
                "total_in_dst": int,
                "dst_root": str,
                "dst_sqlite": str,
                "dst_h5": str
              }

        Notes:
            - Species ordering follows the combined first-seen order (all from A, then any new ones from B).
            - Hash-based dedup relies on `object_hashes.hash` or meta_json["hash"/"content_hash"/"sha256"].
              If you choose "payload", a SHA256 of the pickled object bytes is used instead.
            - This implementation re-adds objects using `add(obj)`, which (by design) re-derives scalars
              via `_extract_scalars`. If your source SQLite has extra ad-hoc scalars that are *not*
              present on the object itself, those will not carry over.
        """
        import hashlib
        
        def _normalize_root(p: str) -> str:
            p = os.path.abspath(p)
            if os.path.isdir(p):
                return p
            return os.path.dirname(p)

        # Normalize roots
        src_a = _normalize_root(src_a)
        src_b = _normalize_root(src_b)
        dst_root = os.path.abspath(dst_root)

        # Guard: destination must not already contain a database
        os.makedirs(dst_root, exist_ok=True)
        existing = set(os.listdir(dst_root))
        if {"db_index.sqlite", "db_objects.h5"} & existing:
            raise FileExistsError(
                f"Destination '{dst_root}' already contains a database; choose an empty directory."
            )

        # Helpers for dedup
        def _extract_src_hash_from_meta(meta: dict) -> Optional[str]:
            for k in ("hash", "content_hash", "sha256"):
                h = meta.get(k)
                if isinstance(h, str) and h:
                    return h
            return None

        def _payload_sha256(obj) -> str:
            blob = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
            return hashlib.sha256(blob).hexdigest()

        # Open storages
        srcA = cls(src_a, access="ro")
        srcB = cls(src_b, access="ro")
        dst  = cls(dst_root, access="rw")

        # Local dedup registries to reduce DB chatter
        seen_hashes = set(dst.get_all_hashes()) if dedup in ("hash",) else set()
        seen_payloads = set() if dedup == "payload" else set()

        skipped = 0
        added_a = 0
        added_b = 0

        def _copy_all(src: "HybridStorage") -> int:
            nonlocal skipped, seen_hashes, seen_payloads
            added_here = 0

            for oid, obj in src.iter_objects(batch_size=1000):
                # Prefer fast dedup before any writes
                meta = src.get_meta(oid)  # merged dict: includes meta_json pieces
                h = _extract_src_hash_from_meta(meta)

                # Decide if duplicate
                is_dup = False
                if dedup == "hash":
                    if isinstance(h, str) and (h in seen_hashes or dst.has_hash(h)):
                        is_dup = True
                elif dedup == "payload":
                    ph = _payload_sha256(obj)
                    if ph in seen_payloads:
                        is_dup = True
                # dedup == "none" => never duplicate

                if is_dup:
                    skipped += 1
                    continue

                # Insert object using public API to ensure consistency
                new_id = dst.add(obj)

                # Keep dedup registries up to date
                if dedup == "hash":
                    if isinstance(h, str) and h:
                        # ensure object_hashes + meta_json carry the hash for future robustness
                        dst._conn.execute(
                            "INSERT OR REPLACE INTO object_hashes(object_id, hash) VALUES (?,?);",
                            (new_id, h)
                        )
                        try:
                            cur = dst._conn.cursor()
                            cur.execute("SELECT meta_json FROM objects WHERE id=?;", (new_id,))
                            row = cur.fetchone()
                            mjson = row[0] if row else None
                            payload = json.loads(mjson) if mjson else {}
                            if "hash" not in payload:
                                payload["hash"] = h
                                cur.execute(
                                    "UPDATE objects SET meta_json=? WHERE id=?;",
                                    (json.dumps(payload), new_id)
                                )
                            dst._conn.commit()
                        except Exception:
                            # Non-fatal: hash is already in object_hashes
                            pass
                        seen_hashes.add(h)

                elif dedup == "payload":
                    ph = _payload_sha256(obj)
                    seen_payloads.add(ph)

                # Optionally backfill free_energy from source meta_json if not extracted via add()
                try:
                    src_F = meta.get("free_energy", None)
                    if src_F is not None:
                        cur = dst._conn.cursor()
                        cur.execute("SELECT meta_json FROM objects WHERE id=?;", (new_id,))
                        row = cur.fetchone()
                        mjson = row[0] if row else None
                        payload = json.loads(mjson) if mjson else {}
                        if "free_energy" not in payload:
                            payload["free_energy"] = float(src_F)
                            cur.execute(
                                "UPDATE objects SET meta_json=? WHERE id=?;",
                                (json.dumps(payload), new_id)
                            )
                            dst._conn.commit()
                except Exception:
                    # Non-fatal metadata improvement
                    pass

                added_here += 1

            return added_here

        try:
            added_a = _copy_all(srcA)
            added_b = _copy_all(srcB)

            # Optional compaction to defragment HDF5
            if compact:
                try:
                    dst.compact_hdf5()
                except Exception:
                    # Compaction failures should not invalidate the merge
                    pass

            report = {
                "added_from_a": int(added_a),
                "added_from_b": int(added_b),
                "skipped_duplicates": int(skipped),
                "total_in_dst": int(dst.count()),
                "dst_root": dst_root,
                "dst_sqlite": dst.sqlite_path,
                "dst_h5": dst.h5_path,
            }
            return report

        finally:
            # Be diligent about closing file handles
            try:
                srcA.close()
            except Exception:
                pass
            try:
                srcB.close()
            except Exception:
                pass
            try:
                dst.close()
            except Exception:
                pass


    @classmethod
    def merge_roots_recursive(
        cls,
        root_dir: str,
        *,
        dst_root: Optional[str] = None,
        dedup: str = "hash",          # "hash" | "payload" | "none"
        compact: bool = True,
        progress_every: int = 5000,
        quiet: bool = False,
        chunk_size: int = 10000,      # tune per machine / dataset
    ) -> dict:
        """
        FAST: copy SQLite rows + HDF5 datasets without unpickling.
        De-dup via object_hashes/meta_json hash, or by payload SHA256 if requested.
        Optimized vs. previous version by batching hash probes, streaming SHA,
        single IN-queries per chunk, and fewer round trips.
        """
        import hashlib, os, json
        from datetime import datetime
        import numpy as _np

        assert dedup in ("hash", "payload", "none")

        root_dir = os.path.abspath(root_dir)

        # --- discover sources (hybrid roots = have both files) ---
        def _is_hybrid_root(d: str) -> bool:
            return (
                os.path.isfile(os.path.join(d, "db_index.sqlite")) and
                os.path.isfile(os.path.join(d, "db_objects.h5"))
            )

        sources: List[str] = []
        # If root_dir contains glob characters, treat it as a pattern; else walk as before.
        if any(ch in root_dir for ch in "*?[]"):
            candidates = glob.glob(root_dir, recursive=True)
            for p in candidates:
                if not os.path.isdir(p):
                    continue
                dp = os.path.abspath(p)
                if dst_root and dp == os.path.abspath(dst_root):
                    continue
                if _is_hybrid_root(dp):
                    sources.append(dp)
        else:
            for dirpath, _, _ in os.walk(root_dir):
                if dst_root and os.path.abspath(dirpath) == os.path.abspath(dst_root):
                    continue
                if _is_hybrid_root(dirpath):
                    sources.append(dirpath)

        sources = sorted(set(sources))


        if dst_root is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dst_root = os.path.join(root_dir, f"_merged_{ts}")
        dst_root = os.path.abspath(dst_root)
        os.makedirs(dst_root, exist_ok=True)

        if {"db_index.sqlite", "db_objects.h5"} & set(os.listdir(dst_root)):
            raise FileExistsError(
                f"Destination '{dst_root}' already contains a database; choose an empty directory."
            )

        # ---------- helpers ----------
        def _sha256_ds_stream(ds) -> str:
            """Stream SHA256 over a 1D uint8 dataset without materializing the whole array."""
            m = hashlib.sha256()
            # 1 MB window; adjust if you like
            win = 1_000_000
            total = int(ds.size)
            off = 0
            buf = _np.empty((win,), dtype=_np.uint8)
            # Use read_direct with selections
            while off < total:
                n = min(win, total - off)
                ds.read_direct(buf[:n], source_sel=_np.s_[off:off+n], dest_sel=_np.s_[:n])
                m.update(memoryview(buf[:n]))
                off += n
            return m.hexdigest()

        def _extract_hash_from_meta_json(mjson: Optional[str]) -> Optional[str]:
            if not mjson:
                return None
            # cheap prefilter to avoid json.loads when irrelevant
            if ("hash" not in mjson) and ("content_hash" not in mjson) and ("sha256" not in mjson):
                return None
            try:
                meta = json.loads(mjson)
                if isinstance(meta, dict):
                    for k in ("hash", "content_hash", "sha256"):
                        v = meta.get(k)
                        if isinstance(v, str) and v:
                            return v
            except Exception:
                pass
            return None

        # ---------- open destination (rw) ----------
        dst = cls(dst_root, access="rw")
        try:
            con = dst._conn
            # Speed PRAGMAs (bulk window only)
            con.execute("PRAGMA journal_mode=WAL;")
            con.execute("PRAGMA synchronous=OFF;")
            con.execute("PRAGMA temp_store=MEMORY;")
            con.execute("PRAGMA cache_size=-200000;")   # ~200MB page cache
            con.execute("PRAGMA cache_spill=OFF;")
            try:
                con.execute("PRAGMA mmap_size=268435456;")  # 256 MB if available
            except Exception:
                pass
            con.execute("PRAGMA foreign_keys=OFF;")    # re-enable at the end

            # preload dedup registry (cross-source) when using "hash"
            seen_hashes: set[str] = set(dst.get_all_hashes()) if dedup in ("hash",) else set()

            total_scanned = total_added = total_skipped = sources_merged = 0

            # cross-file HDF5 dataset copy (no re-pickle)
            def _copy_ds(src_h5: h5py.File, dst_h5: h5py.File, src_oid: int, dst_oid: int):
                sname = f"{src_oid:08d}"
                dname = f"{dst_oid:08d}"
                if "objs" not in src_h5 or sname not in src_h5["objs"]:
                    raise KeyError(f"HDF5 dataset not found for id {src_oid}")
                dst_grp = dst_h5.require_group("objs") if "objs" not in dst_h5 else dst_h5["objs"]
                if dname in dst_grp:
                    del dst_grp[dname]
                dst_h5.copy(src_h5["objs"][sname], dst_grp, name=dname)

            # one-shot ensure for species symbols
            def _ensure_species_bulk(symbols: Iterable[str]) -> Dict[str, int]:
                symbols = [s for s in set(map(str, symbols)) if s]
                if not symbols:
                    return {}
                cur = con.cursor()
                q = "SELECT symbol, species_id FROM species WHERE symbol IN (%s);" % \
                    ",".join("?" for _ in symbols)
                cur.execute(q, symbols)
                mapping = {sym: int(spid) for sym, spid in cur.fetchall()}
                missing = [s for s in symbols if s not in mapping]
                if missing:
                    cur.execute("SELECT COALESCE(MAX(rank), -1) FROM species;")
                    start_rank = int(cur.fetchone()[0]) + 1
                    rows = [(s, start_rank + i) for i, s in enumerate(missing)]
                    cur.executemany("INSERT INTO species(symbol, rank) VALUES (?, ?);", rows)
                    con.commit()
                    # fetch new ones
                    q2 = "SELECT symbol, species_id FROM species WHERE symbol IN (%s);" % \
                         ",".join("?" for _ in missing)
                    cur.execute(q2, missing)
                    mapping.update({sym: int(spid) for sym, spid in cur.fetchall()})
                return mapping

            # chunked IN helper (SQLite param limit ~999)
            def _chunked(lst, n=900):
                for i in range(0, len(lst), n):
                    yield lst[i:i+n]

            for si, src_root in enumerate(sources, start=1):
                try:
                    src = cls(src_root, access="ro")
                except Exception as e:
                    if not quiet:
                        print(f"[{si}/{len(sources)}] Skip '{src_root}' (open error: {e})")
                    continue

                if not quiet:
                    print(f"[{si}/{len(sources)}] Merging: {src_root}")

                try:
                    cur_s = src._conn.cursor()

                    # fast map id->hash if table populated
                    id2hash: Dict[int, Optional[str]] = {}
                    if dedup in ("hash", "payload"):
                        try:
                            pairs = src.get_all_hashes(with_ids=True)
                            id2hash = {int(oid): (h if isinstance(h, str) and h else None) for oid, h in pairs}
                        except Exception:
                            id2hash = {}

                    cur_s.execute("SELECT id, energy, natoms, formula, meta_json FROM objects ORDER BY id ASC;")
                    scanned_here = added_here = skipped_here = 0

                    while True:
                        rows = cur_s.fetchmany(chunk_size)
                        if not rows:
                            break
                        scanned_here += len(rows)
                        total_scanned += len(rows)

                        # Precompute hashes and defer DB checks to one batched probe
                        pre: List[Tuple[int, float, int, str, Optional[str], Optional[str]]] = []
                        # (oid, energy, natoms, formula, meta_json, hash)
                        for oid, energy, natoms, formula, meta_json in rows:
                            h = None
                            if dedup == "hash":
                                h = id2hash.get(oid) or _extract_hash_from_meta_json(meta_json)
                            elif dedup == "payload":
                                h = id2hash.get(oid)
                                if not h:
                                    # compute SHA over raw pickled bytes in HDF5
                                    ds = src._h5["objs"][f"{int(oid):08d}"]
                                    h = _sha256_ds_stream(ds)
                            pre.append((int(oid), energy, natoms, formula, meta_json, h))

                        # Batched dedup probe in destination
                        present: set[str] = set()
                        if dedup != "none":
                            chunk_hashes = [h for *_, h in pre if isinstance(h, str) and h]
                            if chunk_hashes:
                                hitmap = dst.find_hashes(chunk_hashes)  # {hash: [dst_ids]}
                                present = {h for h, ids in hitmap.items() if ids}

                        # Filter to-copy rows (skip those already present or seen in this run)
                        will_copy: List[Tuple[int, float, int, str, Optional[str], Optional[str]]] = []
                        local_dups: set[str] = set()
                        for (oid, energy, natoms, formula, meta_json, h) in pre:
                            if dedup != "none" and isinstance(h, str) and h:
                                if (h in present) or (h in seen_hashes) or (h in local_dups):
                                    skipped_here += 1
                                    total_skipped += 1
                                    continue
                                local_dups.add(h)
                            will_copy.append((oid, energy, natoms, formula, meta_json, h))

                        if not will_copy:
                            if (not quiet) and (total_scanned % progress_every == 0):
                                print(f"    ... scanned={total_scanned}, added={total_added}, skipped={total_skipped}")
                            continue

                        # Gather compositions in one IN query
                        src_oids = [oid for (oid, *_rest) in will_copy]
                        comp_rows_all: List[Tuple[int, str, float]] = []  # (oid, symbol, count)
                        for sub in _chunked(src_oids):
                            q = "SELECT c.object_id, s.symbol, c.count FROM compositions c JOIN species s ON s.species_id=c.species_id WHERE c.object_id IN (%s);" % \
                                ",".join("?" for _ in sub)
                            cur_c = src._conn.cursor()
                            cur_c.execute(q, sub)
                            comp_rows_all.extend([(int(oid), str(sym), float(ct)) for oid, sym, ct in cur_c.fetchall()])

                        # Ensure species in bulk (union of symbols)
                        to_symbols = {sym for (_oid, sym, _ct) in comp_rows_all}
                        sym2id = _ensure_species_bulk(to_symbols)

                        # Scalars in one IN query
                        scalar_rows_all: List[Tuple[int, str, float]] = []
                        for sub in _chunked(src_oids):
                            cur_s2 = src._conn.cursor()
                            cur_s2.execute(
                                "SELECT object_id, key, value FROM scalars WHERE object_id IN (%s);" %
                                ",".join("?" for _ in sub),
                                sub
                            )
                            scalar_rows_all.extend([(int(oid), str(k), (float(v) if v is not None else _np.nan))
                                                    for oid, k, v in cur_s2.fetchall()])

                        # Insert into destination inside one transaction
                        con.execute("BEGIN IMMEDIATE;")
                        cur_d = con.cursor()

                        new_ids: Dict[int, int] = {}
                        # Insert objects; add hash into meta_json if present & ensure object_hashes row
                        for (oid, energy, natoms, formula, meta_json, h) in will_copy:
                            # ensure hash is in meta_json for robustness
                            if isinstance(h, str) and h:
                                try:
                                    payload = json.loads(meta_json) if meta_json else {}
                                    if not isinstance(payload, dict):
                                        payload = {}
                                    if "hash" not in payload:
                                        payload["hash"] = h
                                    meta_json = json.dumps(payload)
                                except Exception:
                                    pass
                            cur_d.execute(
                                "INSERT INTO objects (energy, natoms, formula, meta_json) VALUES (?,?,?,?);",
                                (energy, natoms, formula, meta_json)
                            )
                            nid = int(cur_d.lastrowid)
                            new_ids[oid] = nid
                            if isinstance(h, str) and h:
                                cur_d.execute(
                                    "INSERT OR REPLACE INTO object_hashes(object_id, hash) VALUES (?, ?);",
                                    (nid, h)
                                )
                                seen_hashes.add(h)

                        # compositions → dst
                        if comp_rows_all:
                            comp_inserts = []
                            for oid, sym, ct in comp_rows_all:
                                nid = new_ids.get(oid)
                                if nid is not None:
                                    spid = sym2id.get(sym)
                                    if spid is not None:
                                        comp_inserts.append((nid, spid, float(ct)))
                            if comp_inserts:
                                cur_d.executemany(
                                    "INSERT INTO compositions(object_id, species_id, count) VALUES (?,?,?);",
                                    comp_inserts
                                )

                        # scalars → dst
                        if scalar_rows_all:
                            scalar_inserts = []
                            for oid, key, val in scalar_rows_all:
                                nid = new_ids.get(oid)
                                if nid is not None:
                                    scalar_inserts.append((nid, key, float(val)))
                            if scalar_inserts:
                                cur_d.executemany(
                                    "INSERT INTO scalars(object_id, key, value) VALUES (?,?,?);",
                                    scalar_inserts
                                )

                        con.commit()

                        # HDF5 copy for this chunk (outside SQL transaction)
                        for oid in src_oids:
                            _copy_ds(src._h5, dst._h5, int(oid), new_ids[int(oid)])
                        dst._h5.flush()

                        added_here += len(src_oids)
                        total_added += len(src_oids)

                        if (not quiet) and (total_scanned % progress_every == 0):
                            print(f"    ... scanned={total_scanned}, added={total_added}, skipped={total_skipped}")

                    sources_merged += 1
                    if not quiet:
                        print(f"    -> source summary: scanned={scanned_here}, added={added_here}, skipped={skipped_here} "
                              f"(cumulative: scanned={total_scanned}, added={total_added}, skipped={total_skipped})")

                finally:
                    src.close()

            # maintenance
            con.execute("PRAGMA foreign_keys=ON;")
            if compact:
                try:
                    dst.compact_hdf5()
                    if not quiet:
                        print("[merge-fast] HDF5 compacted.")
                except Exception as e:
                    if not quiet:
                        print(f"[merge-fast] HDF5 compaction skipped (non-fatal): {e}")

            report = {
                "sources_found": len(sources),
                "sources_merged": sources_merged,
                "objects_scanned": int(total_scanned),
                "objects_added": int(total_added),
                "skipped_duplicates": int(total_skipped),
                "dst_root": dst_root,
                "dst_sqlite": dst.sqlite_path,
                "dst_h5": dst.h5_path,
                "sources": sources,
            }
            if not quiet:
                print("[merge-fast] DONE.", json.dumps(report, indent=2))
            return report

        finally:
            dst.close()

    @classmethod
    def merge_roots_recursive_attach(
        cls,
        root_dir: str,
        *,
        dst_root: Optional[str] = None,
        dedup: str = "hash",          # supports "hash" or "none" here
        compact: bool = True,
        quiet: bool = False,
        chunk_size: int = 20000,
    ):
        """
        Faster merge using SQLite ATTACH to filter already-present rows by hash
        inside SQL. Only 'hash' or 'none' dedup are supported in this path.
        """
        import os, json
        from datetime import datetime

        assert dedup in ("hash", "none")
        root_dir = os.path.abspath(root_dir)

        def _is_hybrid_root(d: str) -> bool:
            return (
                os.path.isfile(os.path.join(d, "db_index.sqlite")) and
                os.path.isfile(os.path.join(d, "db_objects.h5"))
            )

        sources: List[str] = []
        for dirpath, _, _ in os.walk(root_dir):
            if dst_root and os.path.abspath(dirpath) == os.path.abspath(dst_root):
                continue
            if _is_hybrid_root(dirpath):
                sources.append(dirpath)
        sources.sort()

        if dst_root is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dst_root = os.path.join(root_dir, f"_merged_{ts}")
        dst_root = os.path.abspath(dst_root)
        os.makedirs(dst_root, exist_ok=True)

        if {"db_index.sqlite", "db_objects.h5"} & set(os.listdir(dst_root)):
            raise FileExistsError(
                f"Destination '{dst_root}' already contains a database; choose an empty directory."
            )

        dst = cls(dst_root, access="rw")
        try:
            con = dst._conn
            con.execute("PRAGMA journal_mode=WAL;")
            con.execute("PRAGMA synchronous=OFF;")
            con.execute("PRAGMA temp_store=MEMORY;")
            con.execute("PRAGMA cache_size=-200000;")
            con.execute("PRAGMA foreign_keys=OFF;")

            total_added = total_skipped = 0
            for si, src_root in enumerate(sources, start=1):
                if not quiet:
                    print(f"[{si}/{len(sources)}] Merging (ATTACH): {src_root}")
                src = cls(src_root, access="ro")
                try:
                    con.execute("BEGIN IMMEDIATE;")
                    con.execute("ATTACH DATABASE ? AS src", (src.sqlite_path,))

                    # stage candidate rows (filter out existing by hash if requested)
                    con.execute("DROP TABLE IF EXISTS temp.t_src_new;")
                    con.execute("""
                    CREATE TEMP TABLE t_src_new AS
                    SELECT o.id AS src_oid, o.energy, o.natoms, o.formula, o.meta_json, h.hash AS h
                    FROM src.objects o
                    LEFT JOIN src.object_hashes h ON h.object_id = o.id
                    """ + ("""
                    LEFT JOIN object_hashes d ON d.hash = h.hash
                    WHERE d.object_id IS NULL
                    """ if dedup == "hash" else "")
                    )

                    # insert objects in a stable order, capture new ids with RETURNING (SQLite ≥3.35)
                    rows = con.execute("SELECT src_oid, energy, natoms, formula, meta_json, h FROM t_src_new ORDER BY src_oid ASC;").fetchall()
                    if not rows:
                        con.execute("DETACH DATABASE src;")
                        con.commit()
                        src.close()
                        continue

                    # bulk insert and map ids
                    mapping = {}  # src_oid -> new dst id
                    for src_oid, energy, natoms, formula, meta_json, h in rows:
                        # ensure hash present in meta_json for future robustness
                        mjson = meta_json
                        try:
                            if h and (not mjson or "hash" not in mjson):
                                payload = json.loads(mjson) if mjson else {}
                                if not isinstance(payload, dict):
                                    payload = {}
                                if "hash" not in payload:
                                    payload["hash"] = h
                                mjson = json.dumps(payload)
                        except Exception:
                            pass
                        cur = con.execute(
                            "INSERT INTO objects (energy, natoms, formula, meta_json) VALUES (?,?,?,?) RETURNING id;",
                            (energy, natoms, formula, mjson)
                        )
                        nid = int(cur.fetchone()[0])
                        mapping[int(src_oid)] = nid
                        if h:
                            con.execute("INSERT OR REPLACE INTO object_hashes(object_id, hash) VALUES (?,?);", (nid, h))

                    # species ensure (union of symbols)
                    sym_rows = con.execute("""
                    SELECT DISTINCT s.symbol
                    FROM src.compositions c JOIN src.species s ON s.species_id = c.species_id
                    WHERE c.object_id IN (SELECT src_oid FROM t_src_new)
                    """).fetchall()
                    sym2id = {}
                    if sym_rows:
                        symbols = [str(sym) for (sym,) in sym_rows]
                        sym2id = dst._ensure_species_bulk(symbols)

                    # compositions → dst
                    if sym2id:
                        comp_rows = con.execute("""
                        SELECT c.object_id, s.symbol, c.count
                        FROM src.compositions c JOIN src.species s ON s.species_id = c.species_id
                        WHERE c.object_id IN (SELECT src_oid FROM t_src_new)
                        """).fetchall()
                        if comp_rows:
                            con.executemany(
                                "INSERT INTO compositions(object_id, species_id, count) VALUES (?,?,?);",
                                [(mapping[int(oid)], sym2id[str(sym)], float(ct)) for (oid, sym, ct) in comp_rows]
                            )

                    # scalars → dst
                    sc_rows = con.execute("""
                    SELECT object_id, key, value FROM src.scalars
                    WHERE object_id IN (SELECT src_oid FROM t_src_new)
                    """).fetchall()
                    if sc_rows:
                        con.executemany(
                            "INSERT INTO scalars(object_id, key, value) VALUES (?,?,?);",
                            [(mapping[int(oid)], str(k), float(v) if v is not None else None) for (oid, k, v) in sc_rows]
                        )

                    con.execute("DETACH DATABASE src;")
                    con.commit()

                    # HDF5 copy (outside SQL)
                    for soid, did in mapping.items():
                        # copy raw dataset
                        sname = f"{int(soid):08d}"
                        dname = f"{int(did):08d}"
                        dst_grp = dst._h5.require_group("objs") if "objs" not in dst._h5 else dst._h5["objs"]
                        if dname in dst_grp:
                            del dst_grp[dname]
                        dst._h5.copy(src._h5["objs"][sname], dst_grp, name=dname)
                    dst._h5.flush()

                    total_added += len(mapping)
                    if not quiet:
                        print(f"    -> added={len(mapping)} (cumulative added={total_added})")

                finally:
                    src.close()

            con.execute("PRAGMA foreign_keys=ON;")
            if compact:
                try:
                    dst.compact_hdf5()
                    if not quiet:
                        print("[merge-attach] HDF5 compacted.")
                except Exception as e:
                    if not quiet:
                        print(f"[merge-attach] HDF5 compaction skipped (non-fatal): {e}")

            return {
                "sources_found": len(sources),
                "objects_added": int(total_added),
                "skipped_duplicates": int(total_skipped),  # only known if you add a COUNT in SQL
                "dst_root": dst_root,
                "dst_sqlite": dst.sqlite_path,
                "dst_h5": dst.h5_path,
                "sources": sources,
            }
        finally:
            dst.close()
    @classmethod
    def _extract_scalars(cls, obj: Any) -> Dict[str, float]:
        """Collect numeric scalar attrs from obj and obj.AtomPositionManager whose names
        start with allowed prefixes. Returns a {key: float} dict."""
        out: Dict[str, float] = {}
        def _harvest(ns: Dict[str, Any]):
            for k, v in ns.items():
                k_lower = k.lower()
                if not any(k_lower.startswith(p.lower()) for p in cls._SCALAR_PREFIXES):
                    continue
                val = v
                try:
                    import numpy as _np
                    if isinstance(v, _np.ndarray):
                        if v.size == 0: 
                            continue
                        if v.ndim == 0:
                            val = float(v.item())
                        else:
                            # prefer first element convention
                            val = float(v.ravel()[0])
                    else:
                        if cls._is_scalar(v):
                            val = float(v)
                        else:
                            continue
                except Exception:
                    continue
                out[str(k)] = float(val)

        try:
            _harvest(getattr(obj, "__dict__", {}))
        except Exception:
            pass
        apm = getattr(obj, "AtomPositionManager", None)
        if apm is not None:
            try:
                _harvest(getattr(apm, "__dict__", {}))
            except Exception:
                pass
        return out

    @staticmethod
    def _extract_labels(obj: Any) -> List[str]:
        apm = getattr(obj, "AtomPositionManager", None)
        if apm is None:
            return []
        labels = getattr(apm, "atomLabelsList", None)
        if labels is None:
            labels = getattr(apm, "_atomLabelsList", None)
        if labels is None:
            return []
        try:
            import numpy as _np
            if isinstance(labels, _np.ndarray):
                return [str(x) for x in labels.tolist()]
        except Exception:
            pass
        return [str(x) for x in labels]

    @staticmethod
    def _extract_energy(obj: Any) -> Optional[float]:
        apm = getattr(obj, "AtomPositionManager", None)
        if apm is None:
            return None
        for name in ("energy", "_energy", "E", "_E"):
            val = getattr(apm, name, None)
            f = HybridStorage._to_float_or_none(val)
            if f is not None:
                return f
        return None

    @staticmethod
    def _extract_free_energy(obj: Any) -> Optional[float]:
        apm = getattr(obj, "AtomPositionManager", None)
        if apm is None:
            return None
        metadata = getattr(apm, "metadata", None)
        if isinstance(metadata, dict) and "F" in metadata:
            return HybridStorage._to_float_or_none(metadata["F"])
        return None


    def _ensure_species(self, symbol: str) -> int:
        cur = self._conn.cursor()
        # try fast path
        cur.execute("SELECT species_id FROM species WHERE symbol=?;", (symbol,))
        row = cur.fetchone()
        if row:
            return int(row[0])
        # assign next rank = max(rank)+1
        cur.execute("SELECT COALESCE(MAX(rank), -1) + 1 FROM species;")
        next_rank = int(cur.fetchone()[0])
        cur.execute("INSERT INTO species(symbol, rank) VALUES(?,?);", (symbol, next_rank))
        self._conn.commit()
        return int(cur.lastrowid)

    @staticmethod
    def _formula_from_counts(counts: Dict[str, float]) -> str:
        # ordered by symbol alphabetically for normalized display (mapping is separate)
        parts = []
        for sp in sorted(counts):
            c = counts[sp]
            c = int(round(c)) if abs(c - round(c)) < 1e-8 else c
            parts.append(f"{sp}{'' if c == 1 else c}")
        return "".join(parts)

    def _save_payload_h5(self, obj_id: int, obj: Any):
        blob = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        arr = np.frombuffer(blob, dtype=np.uint8)
        dname = f"{obj_id:08d}"
        if dname in self._grp:
            del self._grp[dname]
        self._grp.create_dataset(dname, data=arr, compression="gzip", shuffle=True)
        ds = self._grp[dname]
        # convenience attrs
        scal = self._extract_scalars(obj)
        if "E" in scal:
            ds.attrs["E"] = float(scal["E"])
        ds.attrs["id"] = int(obj_id)

    def _load_payload_h5(self, obj_id: int) -> Any:
        dname = f"{obj_id:08d}"
        if dname not in self._grp:
            raise KeyError(f"HDF5 dataset not found for id {obj_id}")
        arr = np.array(self._grp[dname][...], dtype=np.uint8)
        return pickle.loads(arr.tobytes())

    @staticmethod
    def _extract_hash(obj: Any) -> Optional[str]:
        """
        Try to extract a content hash from the object.
        Priority:
          1) obj.AtomPositionManager.metadata['hash'|'content_hash'|'sha256']
          2) obj.hash (string-like)
        """
        # 1) From APM metadata
        apm = getattr(obj, "AtomPositionManager", None)
        if apm is not None:
            meta = getattr(apm, "metadata", None)
            if isinstance(meta, dict):
                for k in ("hash", "content_hash", "sha256"):
                    h = meta.get(k)
                    if isinstance(h, str) and h:
                        return h
        # 2) From top-level attribute
        h2 = getattr(obj, "hash", None)
        if isinstance(h2, str) and h2:
            return h2
        return None

    # ---------------- Public API ----------------
    def add(self, obj: Any) -> int:
        self._assert_writable()

        labels = self._extract_labels(obj)
        natoms = len(labels) if labels else None

        counts: Dict[str, float] = {}
        for s in labels:
            counts[s] = counts.get(s, 0.0) + 1.0
        formula = self._formula_from_counts(counts) if counts else None

        scalars = self._extract_scalars(obj)
        energy = self._extract_energy(obj)
        free_energy = self._extract_free_energy(obj)

        content_hash = self._extract_hash(obj)

        meta_payload = {"composition": counts}
        if free_energy is not None:
            meta_payload["free_energy"] = free_energy
        if content_hash is not None:
            meta_payload["hash"] = content_hash  # keep it in meta_json for convenience


        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO objects (energy, natoms, formula, meta_json) VALUES (?,?,?,?);",
            (energy, natoms, formula, json.dumps(meta_payload))
        )
        obj_id = int(cur.lastrowid)

        if counts:
            rows = []
            for sym, ct in counts.items():
                spid = self._ensure_species(sym)
                rows.append((obj_id, spid, float(ct)))
            cur.executemany(
                "INSERT INTO compositions(object_id, species_id, count) VALUES (?,?,?);",
                rows
            )

        if scalars:
            cur.executemany(
                "INSERT INTO scalars(object_id, key, value) VALUES (?,?,?);",
                [(obj_id, k, float(v)) for k, v in scalars.items()]
            )

        if content_hash is not None:
            cur.execute(
                "INSERT OR REPLACE INTO object_hashes(object_id, hash) VALUES (?, ?);",
                (obj_id, content_hash)
            )

        self._conn.commit()
        self._save_payload_h5(obj_id, obj)
        self._h5.flush()
        return obj_id

    def _ensure_species_bulk(self, symbols):
        symbols = [s for s in dict.fromkeys(map(str, symbols)) if s]  # unique, keep order
        if not symbols:
            return {}

        cur = self._conn.cursor()

        # helper to select any set of symbols with the right number of placeholders
        def _select_map(items):
            if not items:
                return {}
            q = "SELECT symbol, species_id FROM species WHERE symbol IN (%s);" % \
                ",".join("?" for _ in items)
            cur.execute(q, items)
            return {sym: int(spid) for sym, spid in cur.fetchall()}

        # existing ones
        mapping = _select_map(symbols)

        # insert missing with proper ranks
        missing = [s for s in symbols if s not in mapping]
        if missing:
            cur.execute("SELECT COALESCE(MAX(rank), -1) FROM species;")
            start_rank = int(cur.fetchone()[0]) + 1
            rows = [(s, start_rank + i) for i, s in enumerate(missing)]
            cur.executemany("INSERT INTO species(symbol, rank) VALUES (?, ?);", rows)
            # re-select ONLY the missing with a query rebuilt for their length
            mapping.update(_select_map(missing))

        return mapping

    def add_many(self, objs) -> list[int]:
        """
        High-throughput ingest. One SQL transaction, one HDF5 flush.
        """
        self._assert_writable()
        con = self._conn
        cur = con.cursor()

        # Speed PRAGMAs for bulk load (temporary; safe on a single-writer workflow)
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=OFF;")
        cur.execute("PRAGMA temp_store=MEMORY;")
        cur.execute("PRAGMA cache_size=-200000;")

        # Precompute lightweight metadata in Python
        pre = []  # (obj, counts, scalars, energy, natoms, formula, hash)
        species_universe = set()
        for obj in objs:
            labels = self._extract_labels(obj)
            counts = {}
            if labels:
                for s in labels:
                    counts[s] = counts.get(s, 0.0) + 1.0
                species_universe.update(counts.keys())
            formula = self._formula_from_counts(counts) if counts else None
            scalars = self._extract_scalars(obj)
            energy  = self._extract_energy(obj)
            natoms  = len(labels) if labels else None
            free_E  = self._extract_free_energy(obj)
            h       = self._extract_hash(obj)
            meta_payload = {"composition": counts}
            if free_E is not None:
                meta_payload["free_energy"] = free_E
            if h is not None:
                meta_payload["hash"] = h
            pre.append((obj, counts, scalars, energy, natoms, formula, h, meta_payload))

        # Begin transaction for *all* rows
        con.execute("BEGIN;")

        # Bulk species resolution
        sym2id = self._ensure_species_bulk(species_universe)

        # Insert objects; capture new ids
        ids = []
        for (_obj, _counts, _scalars, energy, natoms, formula, _h, meta_payload) in pre:
            cur.execute(
                "INSERT INTO objects (energy, natoms, formula, meta_json) VALUES (?,?,?,?);",
                (energy, natoms, formula, json.dumps(meta_payload))
            )
            ids.append(int(cur.lastrowid))

        # compositions/scalars/hash in batches
        comp_rows, scalar_rows, hash_rows = [], [], []
        for oid, (_obj, counts, scalars, _e, _n, _f, h, _meta) in zip(ids, pre):
            for sym, ct in counts.items():
                comp_rows.append((oid, sym2id[sym], float(ct)))
            for k, v in scalars.items():
                scalar_rows.append((oid, str(k), float(v)))
            if h:
                hash_rows.append((oid, h))

        if comp_rows:
            cur.executemany(
                "INSERT INTO compositions(object_id, species_id, count) VALUES (?,?,?);",
                comp_rows
            )
        if scalar_rows:
            cur.executemany(
                "INSERT INTO scalars(object_id, key, value) VALUES (?,?,?);",
                scalar_rows
            )
        if hash_rows:
            cur.executemany(
                "INSERT OR REPLACE INTO object_hashes(object_id, hash) VALUES (?,?);",
                hash_rows
            )

        con.commit()

        # HDF5 writes (single flush at the end)
        for oid, (obj, *_rest) in zip(ids, pre):
            self._save_payload_h5(oid, obj)
        self._h5.flush()

        return ids

    def get(self, obj_id: int):
        return self._load_payload_h5(int(obj_id))

    def remove(self, obj_id: int) -> None:
        self._assert_writable()

        obj_id = int(obj_id)
        # HDF5
        dname = f"{obj_id:08d}"
        if dname in self._grp:
            del self._grp[dname]
        # SQL
        cur = self._conn.cursor()
        cur.execute("DELETE FROM objects WHERE id=?;", (obj_id,))
        self._conn.commit()

    def list_ids(self) -> List[int]:
        cur = self._conn.cursor()
        cur.execute("SELECT id FROM objects ORDER BY id ASC;")
        return [int(r[0]) for r in cur.fetchall()]

    def count(self) -> int:
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) FROM objects;")
        return int(cur.fetchone()[0])

    def clear(self) -> None:
        self._assert_writable()

        # SQL
        cur = self._conn.cursor()
        cur.execute("DELETE FROM compositions;")
        cur.execute("DELETE FROM scalars;")
        cur.execute("DELETE FROM objects;")
        self._conn.commit()
        # HDF5
        for k in list(self._grp.keys()):
            del self._grp[k]
        self._h5.flush()

    def iter_ids(self, batch_size: Optional[int] = 1000):
        cur = self._conn.cursor()
        last = 0
        while True:
            if batch_size:
                cur.execute(
                    "SELECT id FROM objects WHERE id > ? ORDER BY id ASC LIMIT ?;",
                    (last, batch_size)
                )
            else:
                cur.execute(
                    "SELECT id FROM objects WHERE id > ? ORDER BY id ASC;",
                    (last,)
                )
            rows = cur.fetchall()
            if not rows:
                break
            for (cid,) in rows:
                yield int(cid)
            last = int(rows[-1][0])

    def iter_objects(self, batch_size: Optional[int] = 1000):
        for cid in self.iter_ids(batch_size=batch_size):
            yield cid, self.get(cid)

    def get_all_hashes(self, with_ids: bool = False):
        """
        Return all stored content hashes.

        Args:
            with_ids: if True, returns List[Tuple[int, str]] as (object_id, hash).
                      otherwise List[str] (ordered by object_id ASC).

        Notes:
            Only objects that have a hash recorded are returned.
            Falls back to scanning meta_json if legacy DB lacks `object_hashes`.
        """
        cur = self._conn.cursor()
        try:
            # Fast, indexed path
            cur.execute("SELECT object_id, hash FROM object_hashes ORDER BY object_id ASC;")
            rows = [(int(oid), str(h)) for oid, h in cur.fetchall()]
            return rows if with_ids else [h for _, h in rows]
        except sqlite3.OperationalError:
            # Legacy fallback: scan objects.meta_json
            cur.execute("SELECT id, meta_json FROM objects ORDER BY id ASC;")
            pairs = []
            for oid, mjson in cur.fetchall():
                if not mjson:
                    continue
                try:
                    meta = json.loads(mjson)
                except Exception:
                    continue
                h = None
                for k in ("hash", "content_hash", "sha256"):
                    v = meta.get(k)
                    if isinstance(v, str) and v:
                        h = v
                        break
                if h:
                    pairs.append((int(oid), h))
            return pairs if with_ids else [h for _, h in pairs]

    def has_hash(self, hash_str: str) -> bool:
        """
        Fast membership check: does any object carry this hash?
        """
        cur = self._conn.cursor()
        cur.execute("SELECT 1 FROM object_hashes WHERE hash = ? LIMIT 1;", (str(hash_str),))
        return cur.fetchone() is not None

    def find_ids_by_hash(self, hash_str: str) -> List[int]:
        cur = self._conn.cursor()
        cur.execute("SELECT object_id FROM object_hashes WHERE hash = ?;", (str(hash_str),))
        return [int(oid) for (oid,) in cur.fetchall()]

    def find_hashes(self, hashes: Sequence[str]) -> Dict[str, List[int]]:
        """Batched lookup: hash -> [object_id,...]. Keeps O(k) with chunked IN() queries."""
        if not hashes:
            return {}
        out: Dict[str, List[int]] = {str(h): [] for h in hashes}
        cur = self._conn.cursor()

        # SQLite has a parameter limit (~999). Chunk accordingly.
        CHUNK = 900
        hs = [str(h) for h in hashes]
        for i in range(0, len(hs), CHUNK):
            chunk = hs[i:i+CHUNK]
            q = "SELECT hash, object_id FROM object_hashes WHERE hash IN (%s);" % ",".join("?" for _ in chunk)
            cur.execute(q, chunk)
            for h, oid in cur.fetchall():
                out[h].append(int(oid))
        return out

    # ---------------- Fast metadata access ----------------
    def get_species_universe(self, order: str = "stored") -> List[str]:
        """All species present. order='stored' (first-seen) or 'alphabetical'."""
        cur = self._conn.cursor()
        if order == "alphabetical":
            cur.execute("SELECT symbol FROM species ORDER BY symbol ASC;")
        else:
            cur.execute("SELECT symbol FROM species ORDER BY rank ASC;")
        return [r[0] for r in cur.fetchall()]

    def get_species_mapping(self, order: str = "stored") -> Dict[str, int]:
        """Symbol → column index mapping for dense composition matrices."""
        syms = self.get_species_universe(order=order)
        return {s: i for i, s in enumerate(syms)}

    def get_all_compositions(
        self,
        species_order: Optional[Sequence[str]] = None,
        return_species: bool = False,
        order: str = "stored",
    ):
        """
        Dense (n_samples, n_species) composition matrix in the requested species order.
        If species_order is None, uses order='stored' (first-seen stable).
        """
        cur = self._conn.cursor()
        # list of object ids, stable order
        cur.execute("SELECT id FROM objects ORDER BY id ASC;")
        ids = [int(r[0]) for r in cur.fetchall()]
        n = len(ids)
        if n == 0:
            res = np.zeros((0, 0), dtype=float)
            return (res, []) if return_species else res

        if species_order is None:
            species_order = self.get_species_universe(order=order)
        species_order = list(species_order)
        m = len(species_order)
        id_to_row = {oid: i for i, oid in enumerate(ids)}
        sp_to_col = {sp: j for j, sp in enumerate(species_order)}

        # join compositions with species symbols
        cur.execute("""
            SELECT c.object_id, s.symbol, c.count
            FROM compositions c
            JOIN species s ON s.species_id = c.species_id;
        """)
        M = np.zeros((n, m), dtype=float)
        for oid, sym, ct in cur.fetchall():
            i = id_to_row.get(int(oid))
            j = sp_to_col.get(sym)
            if i is not None and j is not None:
                try:
                    M[i, j] = float(ct)
                except Exception:
                    pass

        return (M, species_order) if return_species else M

    def get_scalar_keys_universe(self) -> List[str]:
        cur = self._conn.cursor()
        cur.execute("SELECT DISTINCT key FROM scalars ORDER BY key ASC;")
        return [r[0] for r in cur.fetchall()]

    def get_all_scalars(
        self,
        keys: Optional[Sequence[str]] = None,
        return_keys: bool = False
    ):
        """
        Dense (n_samples, n_keys) matrix of numeric scalar properties.
        Missing values are np.nan. Rows follow objects.id ascending.
        """
        cur = self._conn.cursor()
        cur.execute("SELECT id FROM objects ORDER BY id ASC;")
        ids = [int(r[0]) for r in cur.fetchall()]
        n = len(ids)
        if n == 0:
            res = np.zeros((0, 0), dtype=float)
            return (res, []) if return_keys else res

        if keys is None:
            keys = self.get_scalar_keys_universe()
        keys = list(keys)
        k = len(keys)
        id_to_row = {oid: i for i, oid in enumerate(ids)}
        key_to_col = {key: j for j, key in enumerate(keys)}

        A = np.full((n, k), np.nan, dtype=float)
        # fill from scalars
        cur.execute("SELECT object_id, key, value FROM scalars;")
        for oid, key, val in cur.fetchall():
            i = id_to_row.get(int(oid))
            j = key_to_col.get(key)
            if i is not None and j is not None and val is not None:
                A[i, j] = float(val)

        return (A, keys) if return_keys else A

    def get_all_energies(self) -> np.ndarray:
        """Convenience: objects.energy column; if empty, fallback to scalar 'E'."""
        cur = self._conn.cursor()
        cur.execute("SELECT energy FROM objects ORDER BY id ASC;")
        vals = [r[0] for r in cur.fetchall()]
        arr = np.array([v for v in vals if v is not None], dtype=float)
        if arr.size > 0:
            return arr
        # fallback
        A, keys = self.get_all_scalars(keys=["E"], return_keys=True)
        return A[:, 0] if A.size else np.array([], dtype=float)

    # Debug/meta
    def get_meta(self, obj_id: int) -> Dict[str, Any]:
        cur = self._conn.cursor()
        cur.execute("SELECT energy, natoms, formula, meta_json FROM objects WHERE id=?;", (int(obj_id),))
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"No object with id {obj_id}")
        energy, natoms, formula, meta_json = row
        meta = json.loads(meta_json) if meta_json else {}
        meta.update(dict(energy=energy, natoms=natoms, formula=formula))
        return meta

    def close(self):
        try:
            self._h5.flush(); self._h5.close()
        except Exception:
            pass
        try:
            self._conn.close()
        except Exception:
            pass

    # ---- maintenance ----
    def compact_hdf5(self, new_path: Optional[str] = None) -> str:
        self._assert_writable()
        self._h5.flush()
        src = self.h5_path
        dst = new_path or (self.h5_path + ".compact")
        with h5py.File(dst, "w") as out:
            out.copy(self._grp, "objs")
        if new_path is None:
            self._h5.close()
            os.replace(dst, src)
            self._h5 = h5py.File(src, "a")
            self._grp = self._h5["objs"]
            return src
        return dst


class _LazyHybridView:
    """Lazy sequence-like view over all objects in HybridStorage."""

    def __init__(self, store: HybridStorage):
        self._s = store

    def __len__(self) -> int:
        return self._s.count()

    def __iter__(self):
        for cid in self._s.iter_ids():
            yield self._s.get(cid)

    def __getitem__(self, i):
        if isinstance(i, slice):
            ids = self._s.list_ids()[i]
            return [self._s.get(cid) for cid in ids]
        else:
            cid = self._s.list_ids()[i]
            return self._s.get(cid)

class CompositeHybridStorage(StorageBackend):
    """
    Unified, read/write *view* over two stores:
      - base: usually HybridStorage(opened 'ro'), immutable here
      - local: usually HybridStorage(opened 'rw'), all writes go here

    IDs exposed by this adapter are **composite indices**: 0..(N_base_active + N_local_active - 1)
    in the order [base_active, then local_active]. Internally we map each composite
    id to (part='base'|'local', backend_id). Removing a 'base' object sets a tombstone.
    """

    def __init__(self, base_store: StorageBackend, local_store: StorageBackend, allow_shadow_delete: bool = True):
        self.base = base_store
        self.local = local_store
        self.allow_shadow_delete = allow_shadow_delete

        # Tombstones hide items from 'base' (and optionally 'local' if you want soft deletes there too)
        self._base_tombs: set[int] = set()
        # For symmetry; not typically used because local deletes are hard-deletes
        self._local_tombs: set[int] = set()

    @classmethod
    def from_composite(cls, base_root: str, local_root: str, *args, **kwargs) -> "PartitionManager":
        kwargs = dict(kwargs)
        kwargs['base_root'] = base_root
        kwargs['local_root'] = local_root
        return cls(storage='composite', db_path=base_root, *args, **kwargs)

    # ---------- internal helpers ----------
    def _active_count(self, part: str) -> int:
        """
        Count ACTIVE items for a part ('base' or 'local'), i.e., excluding tombstones.
        """
        if part not in ("base", "local"):
            raise ValueError("part must be 'base' or 'local'")
        store = self.base if part == "base" else self.local
        tombs = self._base_tombs if part == "base" else self._local_tombs
        try:
            ids = store.list_ids()
        except Exception:
            return 0
        if not tombs:
            return len(ids)
        # Avoid materializing large sets when tombs is empty/small
        return sum(1 for i in ids if i not in tombs)

    def _active_count_fast(self, part: str) -> int:
        """
        O(1) active count using backend COUNT(*) and subtracting tombstones.
        Falls back to the slower path if a backend lacks count().
        """
        if part == "base":
            try:
                return int(self.base.count()) - len(self._base_tombs)
            except Exception:
                return self._active_count("base")
        elif part == "local":
            try:
                return int(self.local.count()) - len(self._local_tombs)
            except Exception:
                return self._active_count("local")
        else:
            raise ValueError("part must be 'base' or 'local'")

    def _compose_pairs(self) -> List[Tuple[str, int]]:
        """
        Returns a list of (part, backend_id) in composite order:
        all active base ids (ascending) then all active local ids (ascending).
        """
        pairs: List[Tuple[str, int]] = []
        # base (skip tombstoned)
        try:
            base_ids = self.base.list_ids()
        except Exception:
            base_ids = []
        for bid in base_ids:
            if bid not in self._base_tombs:
                pairs.append(("base", int(bid)))
        # local (skip tombstoned if you use them)
        try:
            local_ids = self.local.list_ids()
        except Exception:
            local_ids = []
        for lid in local_ids:
            if lid not in self._local_tombs:
                pairs.append(("local", int(lid)))
        return pairs

    def _resolve(self, composite_id: int) -> Tuple[str, int]:
        pairs = self._compose_pairs()
        if composite_id < 0 or composite_id >= len(pairs):
            raise KeyError(f"No object found with composite id {composite_id}")
        return pairs[composite_id]

    # ---------- mandatory API ----------
    def add(self, obj: Any) -> int:
        # All writes go to local
        self.local.add(obj)
        return self.count() - 1

    def add(self, obj: Any) -> int:
        # Compute composite index without scanning pairs
        base_active  = self._active_count_fast("base")
        local_active = self._active_count_fast("local")
        self.local.add(obj)
        return base_active + local_active


    def add_many(self, objs: Sequence[Any]) -> List[int]:
        """
        Add multiple objects at once to the *local* store (RW) using its bulk path if available.
        Returns the composite IDs of the newly added objects (in the same order as `objs`).

        Assumptions:
        - local.add_many returns backend IDs (ascending/new at end; SQLite AUTOINCREMENT).
        - Composite ordering: [active base asc] + [active local asc].
        """
        # Fast path: local backend supports bulk ingest
        bulk = getattr(self.local, "add_many", None)
        if callable(bulk):
            # Compute where the new block will appear in composite space
            base_active = self._active_count_fast("base")
            local_active_before = self._active_count_fast("local")

            new_local_ids = bulk(objs)  # backend IDs; may be needed by callers elsewhere
            # Composite IDs are contiguous at the end of the local-active block
            start = base_active + local_active_before
            return list(range(start, start + len(new_local_ids)))

        # Fallback: no bulk support; degrade gracefully while preserving IDs
        base_active = self._active_count_fast("base")
        local_active_before = self._active_count_fast("local")
        start = base_active + local_active_before
        comp_ids: List[int] = []
        for j, obj in enumerate(objs):
            # Route single adds directly to local (don’t call self.add to avoid O(N) count())
            self.local.add(obj)
            comp_ids.append(start + j)
        return comp_ids

    def get(self, obj_id: Optional[int] = None):
        if obj_id is None:
            # Return a lazy view over the composite
            return _LazyContainerView(self)
        part, bid = self._resolve(int(obj_id))
        return (self.base if part == "base" else self.local).get(bid)

    def remove(self, obj_id: int) -> None:
        part, bid = self._resolve(int(obj_id))
        if part == "base":
            if not self.allow_shadow_delete:
                raise RuntimeError("Cannot remove from base store in composite view (read-only).")
            # soft delete (tombstone)
            self._base_tombs.add(bid)
        else:
            # hard delete in local
            self.local.remove(bid)

    def list_ids(self) -> List[int]:
        return list(range(self.count()))

    def count(self) -> int:
        return self._active_count_fast("base") + self._active_count_fast("local")

    def clear(self) -> None:
        """
        Clear composite view:
          - base: shadow-delete (tombstone) everything,
          - local: hard-delete everything.
        """
        # tombstone all base
        try:
            self._base_tombs = set(self.base.list_ids())
        except Exception:
            self._base_tombs = set()
        # clear local
        try:
            self.local.clear()
        except Exception:
            # fallback: remove one by one
            for lid in getattr(self.local, "list_ids", lambda: [])():
                self.local.remove(lid)
        self._local_tombs.clear()

    def get_all_hashes(self, with_ids: bool = False):
        """
        Composite view of content hashes in composite order:
        [active base objects (ASC by base id), then active local objects (ASC by local id)].

        Args:
            with_ids: if True, returns List[Tuple[int, Optional[str]]] as (composite_id, hash_or_None).
                      If an item lacks a hash, the value is None.
                      If False, returns List[Optional[str]] aligned with composite indices.
        """
        # Fetch per-store (id -> hash) maps
        def _pairs_to_dict(store):
            f = getattr(store, "get_all_hashes", None)
            if f is None:
                return {}
            try:
                return dict(f(with_ids=True))
            except TypeError:
                # fallback if backend only supports without ids
                hs = f(with_ids=False)
                # cannot align without ids; return empty to avoid misreporting
                return {}

        base_map  = _pairs_to_dict(self.base)
        local_map = _pairs_to_dict(self.local)

        out = []
        pairs = self._compose_pairs()  # already excludes tombstoned base/local
        for comp_idx, (part, bid) in enumerate(pairs):
            h = base_map.get(bid) if part == "base" else local_map.get(bid)
            if with_ids:
                out.append((comp_idx, h if isinstance(h, str) and h else None))
            else:
                out.append(h if isinstance(h, str) and h else None)
        return out


    def has_hash(self, hash_str: str) -> bool:
        target = str(hash_str)

        # Base store fast path
        finder = getattr(self.base, "find_ids_by_hash", None)
        if callable(finder):
            for oid in finder(target):
                if oid not in self._base_tombs:
                    return True
        else:
            # Fallback to the (slower) legacy path only if necessary
            if self._has_hash_slow(self.base, target, self._active_ids("base")):
                return True

        # Local store fast path
        finder = getattr(self.local, "find_ids_by_hash", None)
        if callable(finder):
            for oid in finder(target):
                if oid not in self._local_tombs:
                    return True
        else:
            if self._has_hash_slow(self.local, target, self._active_ids("local")):
                return True

        return False

    def _has_hash_slow(self, store, target: str, active_ids: list[int]) -> bool:
        """Compatibility fallback; still avoids false positives on tombstoned items."""
        f = getattr(store, "get_all_hashes", None)
        if f is None:
            return False
        try:
            pairs = dict(f(with_ids=True))  # backend_id -> hash
        except TypeError:
            return False
        for oid in active_ids:
            h = pairs.get(oid)
            if isinstance(h, str) and h == target:
                return True
        return False


    def has_hashes(self, hashes: Sequence[str]) -> Dict[str, bool]:
        """
        Vectorized membership with tombstone awareness.
        Returns: {hash -> bool} for ACTIVE objects only.
        """
        hashes = [str(h) for h in hashes]
        result = {h: False for h in hashes}

        # Base
        finder = getattr(self.base, "find_hashes", None)
        if callable(finder):
            base_hits = finder(hashes)  # hash -> [backend_ids]
            for h, ids in base_hits.items():
                if ids and any(oid not in self._base_tombs for oid in ids):
                    result[h] = True
        else:
            # fallback: singletons via has_hash (still O(k) but not O(N))
            for h in hashes:
                if self.has_hash(h):
                    result[h] = True

        # Local (only fill remaining False)
        remaining = [h for h, ok in result.items() if not ok]
        if remaining:
            finder = getattr(self.local, "find_hashes", None)
            if callable(finder):
                loc_hits = finder(remaining)
                for h, ids in loc_hits.items():
                    if ids and any(oid not in self._local_tombs for oid in ids):
                        result[h] = True
            else:
                for h in remaining:
                    if self.has_hash(h):
                        result[h] = True

        return result
        
    # ---------- optional / metadata-aware ----------
    def get_meta(self, obj_id: int) -> Dict[str, Any]:
        part, bid = self._resolve(int(obj_id))
        getter = getattr(self.base if part == "base" else self.local, "get_meta", None)
        if getter is None:
            raise NotImplementedError("Underlying store does not implement get_meta")
        return getter(bid)

    # pass-through iterators using composite ids
    def iter_ids(self, batch_size: Optional[int] = None) -> Iterator[int]:
        # ignore batch_size; composite space is in-memory merged
        for i in range(self.count()):
            yield i

    def iter_objects(self, batch_size: Optional[int] = None) -> Iterator[tuple[int, Any]]:
        for i in self.iter_ids(batch_size):
            yield i, self.get(i)

    # ---------- fast metadata over the union ----------
    def get_species_universe(self, order: str = "stored") -> List[str]:
        # union of species; for 'stored', take base order then append locals not in base, preserving each store's order
        def _syms(store) -> List[str]:
            f = getattr(store, "get_species_universe", None)
            if f is not None:
                try:
                    return f(order="stored")
                except Exception:
                    pass
            # slow fallback
            syms = set()
            for _, obj in getattr(store, "iter_objects", lambda: [])():
                apm = getattr(obj, "AtomPositionManager", None)
                if apm is None: continue
                labels = getattr(apm, "atomLabelsList", None)
                if labels is None: continue
                lab_list = labels.tolist() if hasattr(labels, "tolist") else labels
                for s in lab_list:
                    syms.add(str(s))
            return sorted(syms)

        b = _syms(self.base)
        l = _syms(self.local)
        if order == "alphabetical":
            return sorted(set(b) | set(l))
        seen = set(b)
        tail = [s for s in l if s not in seen]
        return list(b) + tail

    def get_species_mapping(self, order: str = "stored") -> Dict[str, int]:
        syms = self.get_species_universe(order=order)
        return {s: i for i, s in enumerate(syms)}

    def _active_ids(self, part: str) -> List[int]:
        if part == "base":
            ids = getattr(self.base, "list_ids", lambda: [])()
            return [i for i in ids if i not in self._base_tombs]
        else:
            ids = getattr(self.local, "list_ids", lambda: [])()
            return [i for i in ids if i not in self._local_tombs]

    def get_all_compositions(
        self,
        species_order: Optional[Sequence[str]] = None,
        return_species: bool = False,
        order: str = "stored",
    ):
        import numpy as _np

        # combined species order
        if species_order is None:
            species_order = self.get_species_universe(order=order)
        species_order = list(species_order)
        m = len(species_order)
        sp2col = {sp: j for j, sp in enumerate(species_order)}

        def _fetch_align(store, tombs: set[int]):
            ids_all = getattr(store, "list_ids", lambda: [])()
            id2row = {oid: i for i, oid in enumerate(ids_all)}
            active = [oid for oid in ids_all if oid not in tombs]
            f = getattr(store, "get_all_compositions", None)
            if f is None:
                return np.zeros((0, m), dtype=float)
            M_store, sp_store = f(species_order=None, return_species=True, order=order)
            if M_store.size == 0 or len(ids_all) == 0 or len(sp_store) == 0:
                return np.zeros((0, m), dtype=float)
            rows = [id2row[oid] for oid in active]
            Ms = M_store[rows, :] if rows else np.zeros((0, len(sp_store)), dtype=float)
            out = np.zeros((Ms.shape[0], m), dtype=float)
            for j_old, sp in enumerate(sp_store):
                j_new = sp2col.get(sp)
                if j_new is not None:
                    out[:, j_new] = Ms[:, j_old]
            return out

        Mb = _fetch_align(self.base, self._base_tombs)
        Ml = _fetch_align(self.local, self._local_tombs)
        M = Ml if Mb.size == 0 else (Mb if Ml.size == 0 else np.vstack([Mb, Ml]))
        return (M, species_order) if return_species else M

    def get_scalar_keys_universe(self) -> List[str]:
        keys = set()
        for store in (self.base, self.local):
            f = getattr(store, "get_scalar_keys_universe", None)
            if f is not None:
                try:
                    keys.update(map(str, f()))
                except Exception:
                    pass
        return sorted(keys)

    def get_all_scalars(self, keys: Optional[Sequence[str]] = None, return_keys: bool = False):
        if keys is None:
            keys = self.get_scalar_keys_universe()
        keys = list(keys)
        m = len(keys)
        k2col = {k: j for j, k in enumerate(keys)}

        def _fetch_align(store, tombs: set[int]):
            ids_all = getattr(store, "list_ids", lambda: [])()
            id2row = {oid: i for i, oid in enumerate(ids_all)}
            active = [oid for oid in ids_all if oid not in tombs]
            f = getattr(store, "get_all_scalars", None)
            if f is None:
                return np.zeros((0, m), dtype=float)
            A_store, k_store = f(keys=None, return_keys=True)
            if A_store.size == 0 or len(ids_all) == 0:
                return np.zeros((0, m), dtype=float)
            rows = [id2row[oid] for oid in active]
            As = A_store[rows, :] if rows else np.zeros((0, A_store.shape[1]), dtype=float)
            out = np.full((As.shape[0], m), np.nan, dtype=float)
            kmap = {key: j for j, key in enumerate(k_store)}
            for key, j_new in k2col.items():
                j_old = kmap.get(key)
                if j_old is not None:
                    out[:, j_new] = As[:, j_old]
            return out

        Ab = _fetch_align(self.base, self._base_tombs)
        Al = _fetch_align(self.local, self._local_tombs)
        A = Al if Ab.size == 0 else (Ab if Al.size == 0 else np.vstack([Ab, Al]))
        return (A, keys) if return_keys else A

    def get_all_energies(self) -> np.ndarray:
        """
        Devuelve un vector 1D concatenando (base_activos, local_activos) con la energía por objeto.
        Prioridad de claves escalares: E > energy > Etot > Ef > free_energy.
        Si falta, cae a objects.energy del backend.
        """

        PRIORITY = ["E", "energy", "Etot", "Ef", "free_energy"]

        def _energies_from_store(store, tombs: set[int]) -> np.ndarray:
            # ids del store en orden estable (objects.id ASC)
            ids_all = getattr(store, "list_ids", lambda: [])()
            if not ids_all:
                return np.zeros((0,), dtype=float)

            # filas activas (no tombstoned)
            active_rows = [i for i, oid in enumerate(ids_all) if oid not in tombs]

            # 1) Intentar con get_all_scalars(keys=PRIORITY)
            g = getattr(store, "get_all_scalars", None)
            e = None
            if g is not None:
                A_store, k_store = g(keys=PRIORITY, return_keys=True)
                if A_store.size:
                    # seleccionar solo filas activas
                    As = A_store[active_rows, :] if active_rows else np.zeros((0, A_store.shape[1]), dtype=float)
                    e = np.full((As.shape[0],), np.nan, dtype=float)
                    # completar por prioridad
                    kpos = {k: j for j, k in enumerate(k_store)}
                    for key in PRIORITY:
                        j = kpos.get(key)
                        if j is None:  # esa columna no existe en este store
                            continue
                        mask = np.isnan(e) & ~np.isnan(As[:, j])
                        if mask.any():
                            e[mask] = As[mask, j]

            # 2) Fallback a objects.energy del backend
            if e is None or np.isnan(e).any():
                f = getattr(store, "get_all_energies", None)
                if f is not None:
                    v = np.asarray(f(), dtype=float)
                    # v viene ordenado por objects.id ASC (mismo orden que ids_all)
                    if v.size == len(ids_all):
                        v = v[active_rows]
                        if e is None:
                            e = v
                        else:
                            # rellenar NaNs con la columna de objects.energy
                            nan_mask = np.isnan(e) & ~np.isnan(v)
                            if nan_mask.any():
                                e[nan_mask] = v[nan_mask]

            if e is None:
                # nada disponible
                return np.zeros((0,), dtype=float)
            return e

        eb = _energies_from_store(self.base,  self._base_tombs)
        el = _energies_from_store(self.local, self._local_tombs)
        if eb.size == 0:
            return el
        if el.size == 0:
            return eb
        return np.concatenate([eb, el], axis=0)

    # optional passthroughs
    def set_meta(self, obj_id: int, meta: Dict[str, Any]) -> None:  # pragma: no cover
        part, bid = self._resolve(int(obj_id))
        setter = getattr(self.base if part == "base" else self.local, "set_meta", None)
        if setter is None:
            raise NotImplementedError("Underlying store does not implement set_meta")
        return setter(bid, meta)

    def query_ids(self, where: str, params: Sequence[Any] = ()) -> List[int]:  # pragma: no cover
        # Not implemented for composite; could be added by union over both stores
        raise NotImplementedError("query_ids is not supported on CompositeHybridStorage")



def merge_hybrid_stores(main_root: str, agent_roots: Sequence[str]) -> None:
    """
    One-shot consolidation of multiple HybridStorage roots into a single main root.
    - Copies rows in SQLite tables (objects, compositions, scalars).
    - Rewrites species references using the symbol (robust to different species_id mappings).
    - Copies HDF5 payloads (pickled objects) to new autoincremented IDs in main.
    - Commits per agent; safe to run once after all agents finish.

    Parameters
    ----------
    main_root : str
        Target HybridStorage root directory to consolidate into (must be writable).
    agent_roots : Sequence[str]
        List of source HybridStorage root directories produced by agents.

    Notes
    -----
    * This function does NOT deduplicate payloads. If you need de-dup, add a
      content hash (e.g., SHA-256 of the payload) to meta_json and skip repeats.
    * Do not run concurrently from multiple processes.
    """
    main_root_abs = os.path.abspath(main_root)
    main = HybridStorage(main_root_abs)  # opens RW in your current implementation
    try:
        cur_main = main._conn.cursor()

        for agent_root in agent_roots:
            if agent_root is None:
                continue
            agent_root_abs = os.path.abspath(agent_root)
            # Skip accidental self-merge
            if agent_root_abs == main_root_abs:
                continue
            # Skip non-existent or empty roots gracefully
            if not os.path.isdir(agent_root_abs):
                continue

            agent = None
            try:
                agent = HybridStorage(agent_root_abs)  # opens RW in current code; we'll only read
                cur_agent = agent._conn.cursor()

                # Iterate agent objects in stable order
                cur_agent.execute(
                    "SELECT id, energy, natoms, formula, meta_json "
                    "FROM objects ORDER BY id ASC;"
                )
                rows = cur_agent.fetchall()
                if not rows:
                    continue

                # Single transaction per agent for speed and atomicity
                cur_main.execute("BEGIN;")

                for oid, energy, natoms, formula, meta_json in rows:
                    # 1) Insert into main.objects
                    cur_main.execute(
                        "INSERT INTO objects (energy, natoms, formula, meta_json) VALUES (?,?,?,?);",
                        (energy, natoms, formula, meta_json),
                    )
                    new_id = int(cur_main.lastrowid)

                    # 2) compositions: remap by symbol → species_id in main
                    cur_agent.execute(
                        """
                        SELECT s.symbol, c.count
                        FROM compositions c
                        JOIN species s ON s.species_id = c.species_id
                        WHERE c.object_id = ?;
                        """,
                        (int(oid),),
                    )
                    comp_rows = cur_agent.fetchall()
                    if comp_rows:
                        rows_to_insert = []
                        for sym, ct in comp_rows:
                            spid = main._ensure_species(sym)  # creates if missing
                            rows_to_insert.append((new_id, spid, float(ct)))
                        cur_main.executemany(
                            "INSERT INTO compositions(object_id, species_id, count) VALUES (?,?,?);",
                            rows_to_insert,
                        )

                    # 3) scalars: straight copy
                    cur_agent.execute(
                        "SELECT key, value FROM scalars WHERE object_id = ?;",
                        (int(oid),),
                    )
                    scal_rows = cur_agent.fetchall()
                    if scal_rows:
                        cur_main.executemany(
                            "INSERT INTO scalars(object_id, key, value) VALUES (?,?,?);",
                            [(new_id, k, v) for (k, v) in scal_rows],
                        )

                    # 4) payload: load from agent HDF5, store in main HDF5
                    obj = agent.get(int(oid))
                    main._save_payload_h5(new_id, obj)

                # Commit per agent and flush datasets
                main._conn.commit()
                main._h5.flush()

            finally:
                if agent is not None:
                    agent.close()

    finally:
        main.close()
