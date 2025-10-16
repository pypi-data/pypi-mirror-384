try:
    from ..master.FileManager import *   
except ImportError as e:
    import sys
    sys.stderr.write(f"An error occurred while importing FileManager: {str(e)}\n")
    del sys

try:
    from ..master.AtomicProperties import AtomicProperties
except ImportError as e:
    import sys
    sys.stderr.write(f"An error occurred while importing AtomicProperties: {str(e)}\n")
    del sys

try:
    from ..single_run.SingleRun import SingleRun
except ImportError as e:
    import sys
    sys.stderr.write(f"An error occurred while importing SingleRun: {str(e)}\n")
    del sys

try:
    from ..IO.OutFileManager import OutFileManager
    from ..IO.storage_backend import MemoryStorage, SQLiteStorage, HybridStorage, StorageBackend, CompositeHybridStorage

except ImportError as e:
    import sys
    sys.stderr.write(f"An error occurred while importing OutFileManager: {str(e)}\n")
    del sys

try:
    from ..IO.structure_handling_tools.AtomPosition import AtomPosition
except ImportError as e:
    import sys
    sys.stderr.write(f"An error occurred while importing AtomPosition: {str(e)}\n")
    del sys

try:
    import os, sys
    import traceback
    import re
    import numpy as np
    from typing import List, Optional, Union, Iterable, Iterator, Sequence, Dict, Any
    import copy
    import logging
    from tqdm import tqdm
    import mmap

except ImportError as e:
    import sys
    sys.stderr.write(f"An error occurred while importing traceback: {str(e)}\n")
    del sys

try:
    from ase.io import Trajectory
except ImportError as e:
    import sys
    sys.stderr.write(f"An error occurred while importing ase.io.Trajectory: {str(e)}\n")
    del sys

class _LazyContainerView:
    def __init__(self, store: StorageBackend):
        self._s = store
    def __len__(self):
        return self._s.count()
    def __iter__(self):
        for cid in self._s.iter_ids():
            yield self._s.get(cid)
    def __getitem__(self, i):
        ids = self._s.list_ids()
        if isinstance(i, slice):
            return [self._s.get(cid) for cid in ids[i]]
        return self._s.get(ids[i])

class PartitionManager(FileManager, AtomicProperties): 
    """
    PartitionManager class for managing and partitioning simulation data.

    Inherits:
    - FileManager: For file management functionalities.

    Attributes:
    - file_location (str): File path for data files.
    - containers (list): Containers to hold various data structures.
    """
    def __init__(
        self,
        path : str = None,
        storage: str = 'memory',
        db_path: Optional[str] = 'data.db',
        local_root: Optional[str] = None,
        base_root: Optional[str] = None,
        *args,
        **kwargs
    ):
        """
        Initializes the PartitionManager object.

        Args:
        - file_location (str, optional): File path location.
        - name (str, optional): Name of the partition.
        - **kwargs: Additional arguments.
        """
        
        self._containers = []
        self._time = []
        self._N = None
        self._size = None

        self._uniqueAtomLabels = None
        self._uniqueAtomLabels_order = None

        super().__init__(path, *args, **kwargs)

        if storage == 'memory':
            self._store = MemoryStorage()
        elif storage == 'sqlite':
            if not db_path:
                raise ValueError("db_path must be provided for sqlite storage")
            self._store = SQLiteStorage(db_path)
        elif storage == 'hybrid':
            root = kwargs.pop('hybrid_root', None)
            access = kwargs.pop('hybrid_access', 'rw')  # allow future RO/RW

            if root is None:
                # If db_path looks like a file, use its directory; otherwise use db_path itself
                root = os.path.dirname(db_path) if (db_path and os.path.splitext(db_path)[1]) else (db_path or './hybrid_store')
            self._store = HybridStorage(root_dir=root)

        elif storage == 'composite':
            if not base_root or not local_root:
                raise ValueError("storage='composite' requires base_root and local_root")

            def _bootstrap_if_needed(root: str) -> None:
                """
                Ensure a valid HybridStorage root exists (HDF5 with 'objs' group + SQLite schema).
                - Try read-only open (fast path).
                - If it fails (missing files/group/schema), open RW once to create & close.
                """
                try:
                    tmp = HybridStorage(root_dir=root, access='ro')
                    tmp.close()
                except Exception:
                    # Create directory if needed and initialize store
                    os.makedirs(root, exist_ok=True)
                    tmp = HybridStorage(root_dir=root, access='rw')
                    tmp.close()

            # Make sure both roots are initialized so that 'ro' open won't fail
            _bootstrap_if_needed(base_root)
            _bootstrap_if_needed(local_root)

            # Now behave exactly as before
            base  = HybridStorage(root_dir=base_root,  access='ro')  # read-only
            local = HybridStorage(root_dir=local_root, access='rw')  # read-write
            self._store = CompositeHybridStorage(base, local)

        else:
            raise ValueError(f"Unknown storage backend: {storage}")
        
    # --- iteration ---
    def __iter__(self):
        return iter(self.containers)

    def __len__(self) -> int:
        return self._store.count()

    def __getitem__(self, index: int):
        return self.get_container(index)

    def __iadd__(self, other: object) -> 'PartitionManager':
        """
        In‑place absorb all containers from other into self, then return self.
        """
        if not isinstance(other, PartitionManager):
            return NotImplemented
        for run in other.containers:
            self.add_container(copy.deepcopy(run))
        return self

    # --- clear without breaking the `containers` property ---
    def empty_container(self) -> None:
        """
        Remove all containers from the storage (do NOT assign to self.containers).
        """
        for cid in self._store.list_ids()[::-1]:
            self._store.remove(cid)
        self._uniqueAtomLabels = None
        self._uniqueAtomLabels_order = None

    @property
    def containers(self) -> List[SingleRun]:
        """
        Legacy-style property returning the list of container objects.
        """
        return self.list_containers()

    def list_containers(self) -> Sequence[SingleRun]:
        return _LazyContainerView(self._store)

    @property
    def N(self) -> int:
        """
        Return the number of containers managed by the PartitionManager.
        
        Returns:
        int: Number of containers. Returns 0 if containers are not initialized or of unsupported type.
        """
        return self._store.count()

    @property
    def size(self) -> int:
        """
        Return the number of containers managed by the PartitionManager.
        
        Returns:
        int: Number of containers. Returns 0 if containers are not initialized or of unsupported type.
        """
        return self.N

    @property
    def uniqueAtomLabels(self) -> List[str]:
        """
        Get unique atom labels from all containers.
        
        Returns:
        list: A list of unique atom labels.
        
        Raises:
        AttributeError: If containers are not initialized.
        """
        if self._uniqueAtomLabels is None:
            uniqueAtomLabels = set()
            for c in self.containers:
                assert hasattr(c, 'AtomPositionManager'), "Container must have an AtomPositionManager attribute."
                uniqueAtomLabels.update(c.AtomPositionManager.uniqueAtomLabels)
            self._uniqueAtomLabels = list(uniqueAtomLabels)

        return self._uniqueAtomLabels

    @property
    def uniqueAtomLabels_order(self) -> dict:
        """
        Get a dictionary mapping unique atom labels to their indices.
        
        Returns:
        dict: A dictionary with unique atom labels as keys and their order as values.
        
        Raises:
        AttributeError: If containers are not initialized.
        """
        if self._uniqueAtomLabels_order is None:
            labels = self.uniqueAtomLabels
            self._uniqueAtomLabels_order = {n: i for i, n in enumerate(labels)}
        return self._uniqueAtomLabels_order

    def add_container(self, container: Union[SingleRun, List[SingleRun]]) -> Union[int, List[int]]:
        """
        Add one or multiple SingleRun containers.
        Returns a single storage ID (int) or a list of IDs.
        """
        self._uniqueAtomLabels = None
        self._uniqueAtomLabels_order = None

        if isinstance(container, list):
            ids: List[int] = []
            for obj in container:
                ids.append(self._store.add(obj))
            return ids
        return self._store.add(container)

    add = add_container

    def add_ase(self, atoms: Union["Atoms", Iterable["Atoms"]]) -> List[int]:
        """
        Add one or many ASE Atoms objects as containers, using APM's public setters.
        Also copies `atoms.info` into container metadata if it is a dict.
        Returns the storage IDs of the newly added containers.
        """
        from ase import Atoms  # runtime import

        # Normalize input
        if isinstance(atoms, Atoms):
            atoms_seq = [atoms]
        elif isinstance(atoms, (list, tuple)):
            atoms_seq = list(atoms)
        else:
            raise TypeError("`atoms` must be an ase.Atoms or a list/tuple of ase.Atoms.")

        def _as_builtin(x):
            # Make metadata JSON-/pickle-friendly (numpy → Python builtins)
            try:
                import numpy as np
                if isinstance(x, np.generic):
                    return x.item()
                if isinstance(x, np.ndarray):
                    return x.tolist()
            except Exception:
                pass
            return x

        ids: List[int] = []
        for a in atoms_seq:
            if not isinstance(a, Atoms):
                raise TypeError(f"Object {a!r} is not an ase.Atoms instance.")

            sr = SingleRun(file_location=None)
            apm = AtomPosition()

            # ---- Lattice (keep absolute positions) ----
            try:
                cell = a.get_cell()
                if cell is not None and np.size(cell) == 9:
                    mat = getattr(cell, "array", None)
                    mat = mat if mat is not None else np.array(cell, dtype=float)
                    apm.set_latticeVectors(np.array(mat, dtype=np.float64), edit_positions=False)
            except Exception:
                pass

            # ---- Positions & labels ----
            apm.set_atomPositions(np.asarray(a.get_positions(), dtype=np.float64))
            try:
                apm.set_atomLabels(a.get_chemical_symbols())
            except Exception:
                apm._atomLabelsList = np.asarray(a.get_chemical_symbols(), dtype=object)
                apm._fullAtomLabelString = None
                apm._uniqueAtomLabels = None
                apm._atomCountByType = None
                apm._atomCountDict = None

            # ---- PBC ----
            try:
                apm._pbc = list(a.get_pbc())
            except Exception:
                pass

            # ---- Optional energy ----
            E = None
            try:
                E = a.get_potential_energy()
            except Exception:
                try:
                    E = a.get_total_energy()
                except Exception:
                    E = None
            if E is not None:
                try:
                    apm.set_E(np.array([float(E)], dtype=np.float64))
                except Exception:
                    apm.E = float(E)
                try:
                    sr.E = float(E)
                except Exception:
                    pass

            # ---- Metadata from Atoms.info ----
            meta = getattr(a, "info", None)
            if isinstance(meta, dict) and meta:  # only if dict and non-empty
                meta_clean = {str(k): _as_builtin(v) for k, v in meta.items()}
                try:
                    apm.metadata = meta_clean
                except Exception:
                    pass

            sr.AtomPositionManager = apm
            ids.append(self.add_container(sr))

        return ids


    def add_empty_container(self, ):
        """
        Add a new container to the list of containers.

        Parameters:
            container (object): The container object to be added.
        """
        self.add_container( SingleRun() )
        return self.containers[-1]

    def get_container(self, container_id: int) -> SingleRun:
        """Retrieve a container by its storage ID."""
        return self._store.get(container_id)

    def set_container(self, containers_list: list) -> bool:
        """Retrieve a container by its storage ID."""
        return self._store.set(containers_list)

    def remove(self, IDs) -> None:
        """
        Remove a container either by ID (int) or by object reference.

        Parameters:
            container: storage ID or SingleRun object to remove.
        """
        if isinstance(IDs, int):
            self._store.remove(IDs)
            return

    def remove_container(self, container: Union[int, SingleRun]) -> None:
        """
        Remove a container either by ID (int) or by object reference.

        Parameters:
            container: storage ID or SingleRun object to remove.
        """
        # reset caches
        self._uniqueAtomLabels = None
        self._uniqueAtomLabels_order = None

        # remove by ID
        if isinstance(container, int):
            self._store.remove(container)
            return

        # remove by object: find matching ID
        for cid in self._store.list_ids():
            obj = self._store.get(cid)
            if obj is container or obj == container:
                self._store.remove(cid)
                return
        raise KeyError("Container not found for removal")

    def materialize_by_ids(
        self,
        ids: Sequence[int],
        *,
        dedup: bool = True,
        preserve_order: bool = True,       # keep caller's order in the returned list
        sort_backend_reads: bool = True,   # improves locality on HybridStorage/HDF5
        independent_duplicates: bool = False  # if True, deepcopy when the same id appears multiple times
    ) -> List[Any]:
        """
        Fetch a list of containers by their (view) IDs efficiently.
        Complexity: O(N) once (composite mapping) + O(k·S) for payload loads.

        Notes
        -----
        - If the underlying store is CompositeHybridStorage, the incoming IDs are
          composite indices; we resolve them to (backend, backend_id) once and then
          read directly from each backend.
        - If the same id appears multiple times and you need independent Python
          objects (e.g., mutate each copy differently before persisting), set
          independent_duplicates=True (adds a deepcopy per duplicate occurrence).
        """
        ids = [int(i) for i in ids]
        n = len(ids)
        if n == 0:
            return []

        store = self._store
        out: List[Any] = [None] * n

        # Map id -> positions where it appears (for order restoration and duplicates)
        positions: Dict[int, List[int]] = {}
        uniq_ids: List[int] = []
        if dedup:
            for pos, cid in enumerate(ids):
                lst = positions.get(cid)
                if lst is None:
                    positions[cid] = [pos]
                    uniq_ids.append(cid)
                else:
                    lst.append(pos)
        else:
            # No dedup; each occurrence is treated independently.
            positions = {cid: [i] for i, cid in enumerate(ids)}
            uniq_ids = ids

        # --- Composite-aware fast path ---
        from types import SimpleNamespace
        if store.__class__.__name__ == "CompositeHybridStorage":
            # Build composite mapping once (O(N))
            try:
                pairs = store._compose_pairs()  # [(part, backend_id), ...]
            except Exception:
                # Fallback: reconstruct mapping (equivalent to _compose_pairs)
                base_ids  = getattr(store.base,  "list_ids", lambda: [])()
                local_ids = getattr(store.local, "list_ids", lambda: [])()
                base_tombs  = getattr(store, "_base_tombs", set())
                local_tombs = getattr(store, "_local_tombs", set())
                pairs = []
                for bid in base_ids:
                    if bid not in base_tombs:
                        pairs.append(("base", int(bid)))
                for lid in local_ids:
                    if lid not in local_tombs:
                        pairs.append(("local", int(lid)))

            # Group composite ids by backend to improve locality
            by_backend: Dict[str, List[tuple[int,int]]] = {"base": [], "local": []}
            for comp_id in uniq_ids:
                part, bid = pairs[comp_id]
                by_backend[part].append((comp_id, int(bid)))

            def fetch_group(items: List[tuple[int,int]], backend) -> None:
                if not items: return
                items_sorted = sorted(items, key=lambda x: x[1]) if sort_backend_reads else items
                cache: Dict[int, Any] = {}
                # Load each backend id once
                get = backend.get
                for comp_id, bid in items_sorted:
                    cache[bid] = get(bid)
                # Place results back into the output at all positions
                for comp_id, bid in items:
                    obj = cache[bid]
                    pos_list = positions[comp_id]
                    if independent_duplicates and len(pos_list) > 1:
                        out[pos_list[0]] = obj
                        for p in pos_list[1:]:
                            out[p] = copy.deepcopy(obj)
                    else:
                        for p in pos_list:
                            out[p] = obj

            fetch_group(by_backend["base"],  store.base)
            fetch_group(by_backend["local"], store.local)

        else:
            # --- Single backend (Memory/SQLite/Hybrid) ---
            items = sorted(uniq_ids) if sort_backend_reads else uniq_ids
            cache: Dict[int, Any] = {}
            get = store.get
            for oid in items:
                cache[oid] = get(oid)

            for cid, pos_list in positions.items():
                obj = cache[cid]
                if independent_duplicates and len(pos_list) > 1:
                    out[pos_list[0]] = obj
                    for p in pos_list[1:]:
                        out[p] = copy.deepcopy(obj)
                else:
                    for p in pos_list:
                        out[p] = obj

        # Order is preserved by construction
        return out
    def apply_filter_mask(self, mask:list) -> bool:
        """
        Filters containers based on a boolean mask.

        Parameters
        ----------
        mask : list
            A list of 0/1 values indicating which containers to keep. 
            Must have the same length as `self.containers`.

        Returns
        -------
        bool
            True if filtering is successfully applied.

        Example
        -------
        If `self.containers = [A, B, C]` and `mask = [1, 0, 1]`, 
        the result will be `self._containers = [A, C]`.
        """
        self.filter_containers(mask) 

    def filter_containers(self, mask: List[int]) -> None:
        """
        Filters containers based on a boolean mask.

        Parameters
        ----------
        mask : list
            A list of 0/1 values indicating which containers to keep. 
            Must have the same length as `self.containers`.

        Returns
        -------
        bool
            True if filtering is successfully applied.

        Example
        -------
        If `self.containers = [A, B, C]` and `mask = [1, 0, 1]`, 
        the result will be `self._containers = [A, C]`.
        """
        all_ids = set(self._store.list_ids())
        for cid in sorted(all_ids - set(mask), reverse=True):
            self._store.remove(cid)

    def apply_sorting_order(self, order: List[int]) -> bool:
        """
        Reorder containers according to provided index order (legacy behavior).

        Parameters:
            order: new ordering list of indices into current containers list.
        """
        # reset caches
        self._uniqueAtomLabels = None
        self._uniqueAtomLabels_order = None

        current = self.list_containers()
        # validate
        if sorted(order) != list(range(len(current))):
            raise ValueError("Invalid sorting order list")
        # get objects in new order
        new_list = [current[i] for i in order]
        # clear and re-add
        for cid in self._store.list_ids()[::-1]:
            self._store.remove(cid)
        for obj in new_list:
            self._store.add(obj)
        return True

    # -------- Acceso directo a metadatos (sin cargar todos los SingleRun) --------
    # ---- Fast metadata pass-throughs (no full SingleRun loads when hybrid/sqlite) ----
    def get_species_universe(self, order: str = "stored") -> List[str]:
        """
        Elements present in the dataset.
        order='stored' (first-seen stable) or 'alphabetical'.
        """
        if hasattr(self._store, "get_species_universe"):
            return self._store.get_species_universe(order=order)
        # Fallback: compute from memory containers
        syms = set()
        for c in self.containers:
            apm = getattr(c, "AtomPositionManager", None)
            if apm is None: continue
            labels = getattr(apm, "atomLabelsList", None) 
            if labels is None: continue
            lab_list = labels.tolist() if hasattr(labels, "tolist") else labels
            for s in lab_list: syms.add(str(s))
        return sorted(syms) if order == "alphabetical" else list(sorted(syms))  # best effort

    def get_species_mapping(self, order: str = "stored") -> Dict[str, int]:
        """
        Mapping symbol → column index used in dense composition matrices.
        """
        if hasattr(self._store, "get_species_mapping"):
            return self._store.get_species_mapping(order=order)
        syms = self.get_species_universe(order=order)
        return {s: i for i, s in enumerate(syms)}

    def get_all_compositions(self, species_order: Optional[Sequence[str]] = None,
                             return_species: bool = False, order: str = "stored"):
        """
        Dense composition matrix. Delegates to backend when available.
        """
        if hasattr(self._store, "get_all_compositions"):
            return self._store.get_all_compositions(species_order=species_order,
                                                    return_species=return_species,
                                                    order=order)
        # Fallback to memory iteration (kept from previous answer)
        import numpy as _np
        if species_order is None:
            species_order = self.get_species_universe(order=order)
        idx = {sp: j for j, sp in enumerate(species_order)}
        rows = []
        for c in self.containers:
            vec = [0.0] * len(species_order)
            apm = getattr(c, "AtomPositionManager", None)
            if apm is not None:
                labels = getattr(apm, "atomLabelsList", None) 
                if labels is not None:
                    lab_list = labels.tolist() if hasattr(labels, "tolist") else labels
                    for s in lab_list:
                        j = idx.get(str(s))
                        if j is not None:
                            vec[j] += 1.0
            rows.append(vec)
        M = _np.asarray(rows, dtype=float)
        return (M, list(species_order)) if return_species else M

    def get_scalar_keys_universe(self) -> List[str]:
        """All numeric scalar keys present (e.g. E, E1, Etot, ...)."""
        if hasattr(self._store, "get_scalar_keys_universe"):
            return self._store.get_scalar_keys_universe()
        # Fallback: scan containers
        keys = set()
        for c in self.containers:
            for obj in (c, getattr(c, "AtomPositionManager", None)):
                if obj is None: continue
                for k, v in getattr(obj, "__dict__", {}).items():
                    try:
                        import numpy as _np
                        if isinstance(v, (int, float, _np.integer, _np.floating)) or (isinstance(v, _np.ndarray) and v.ndim == 0):
                            keys.add(str(k))
                    except Exception:
                        pass
        return sorted(keys)

    def get_all_scalars(self, keys: Optional[Sequence[str]] = None, return_keys: bool = False):
        """
        Dense (n_samples, n_keys) of scalar properties without instantiating all SingleRun (hybrid path).
        """
        if hasattr(self._store, "get_all_scalars"):
            return self._store.get_all_scalars(keys=keys, return_keys=return_keys)
        # Fallback: build from memory
        import numpy as _np
        if keys is None:
            keys = self.get_scalar_keys_universe()
        keys = list(keys)
        A = []
        for c in self.containers:
            row = []
            ns_list = [getattr(c, "__dict__", {}), getattr(getattr(c, "AtomPositionManager", None), "__dict__", {}) if hasattr(c, "AtomPositionManager") else {}]
            row_vals = {k: None for k in keys}
            for ns in ns_list:
                for k in keys:
                    if row_vals[k] is None and k in ns:
                        v = ns[k]
                        if hasattr(v, "ndim"):
                            if v.ndim == 0:
                                v = float(v.item())
                            else:
                                v = float(np.ravel(v)[0])
                        row_vals[k] = float(v) if v is not None else None
            row = [row_vals[k] if row_vals[k] is not None else np.nan for k in keys]
            A.append(row)
        A = _np.asarray(A, dtype=float)
        return (A, keys) if return_keys else A

    def get_all_energies(self) -> np.ndarray:
        """Convenience wrapper; hybrid path reads from SQL/scalars directly."""
        if hasattr(self._store, "get_all_energies"):
            return self._store.get_all_energies()
        import numpy as _np
        vals = []
        for c in self.containers:
            E = getattr(c, "E", None)
            if E is None and hasattr(c, "AtomPositionManager"):
                E = getattr(c.AtomPositionManager, "E", None)
            if E is None: 
                continue
            try:
                if hasattr(E, "ndim"):
                    vals.append(float(E.item() if E.ndim == 0 else E.ravel()[0]))
                else:
                    vals.append(float(E))
            except Exception:
                pass
        return _np.array(vals, dtype=float)

    def get_all_hashes(self) -> list:
        """
        Return all content hashes known to the current storage backend.

        For composite/hybrid backends this is read directly from the index.
        For memory/sqlite (no hash index), this falls back to scanning containers.
        """
        if hasattr(self._store, "get_all_hashes"):
            try:
                return self._store.get_all_hashes(with_ids=False)
            except TypeError:
                return self._store.get_all_hashes()
        # Fallback: scan in-memory containers
        out = []
        for c in self.containers:
            h = None
            apm = getattr(c, "AtomPositionManager", None)
            if apm is not None and isinstance(getattr(apm, "metadata", None), dict):
                h = apm.metadata.get("hash") or apm.metadata.get("content_hash") or apm.metadata.get("sha256")
            if not h:
                h = getattr(c, "hash", None)
            out.append(h if isinstance(h, str) and h else None)
        return out


    def has_hash(self, hash_str: str) -> bool:
        """
        Return True if the given hash is present in the current storage view.
        """
        if hasattr(self._store, "has_hash"):
            return bool(self._store.has_hash(hash_str))
        target = str(hash_str)
        for h in self.get_all_hashes():
            if isinstance(h, str) and h == target:
                return True
        return False


    def _update_container(self, container: SingleRun, container_setter: object) -> None:
        """
        Updates a given container with simulation parameters extracted from the simulation reader.

        Parameters:
        - container: The container to be updated with simulation settings.
        - container_setter: The simulation reader instance containing the extracted settings.

        Returns:
        None
        """
        container.InputFileManager = container_setter.InputFileManager
        container.KPointsManager = container_setter.KPointsManager
        container.PotentialManager = container_setter.PotentialManager
        container.BashScriptManager = container_setter.BashScriptManager
        container.vdw_kernel_Handler = container_setter.vdw_kernel_Handler
        container.WaveFileManager = container_setter.WaveFileManager
        container.ChargeFileManager = container_setter.ChargeFileManager

    @error_handler
    def read_config_setup(self, file_location: str = None, source: str = 'VASP', verbose: bool = False):
        """
        Reads simulation configuration from a specified file location and updates containers with the read settings.

        This method supports reading configurations specifically tailored for VASP simulations. It extracts simulation
        parameters such as input file management, k-points, potentials, and more, and applies these configurations
        across all containers managed by this instance.

        Parameters:
        - file_location (str, optional): The path to the directory containing the simulation files. Defaults to None,
                                         in which case the instance's file_location attribute is used.
        - source (str, optional): The source/format of the simulation files. Currently, only 'VASP' is supported.
                                  Defaults to 'VASP'.
        - verbose (bool, optional): If True, prints detailed messages during the process. Defaults to False.

        Returns:
        None
        """

        # Use instance's file_location if none provided or invalid
        file_location = file_location if isinstance(file_location, str) else self.file_location

        # Initialize simulation reader based on the source format
        if source.upper() == 'VASP':
            container_setter = self.read_vasp_folder(file_location=file_location, add_container=False, verbose=verbose)
            if container_setter.AtomPositionManager is not None:
                container_setter.InputFileManager.set_LDAU(container_setter.AtomPositionManager.uniqueAtomLabels)

        # Update all containers with the read configuration
        for container in self.containers:
            self._update_container(container, container_setter)

    @staticmethod
    def _identify_file_type(file_name: str) -> str:
        """
        Identifies the type of file based on common atomic input file identifiers.

        The function is case-insensitive and recognizes a variety of file types commonly
        used in computational chemistry and physics. If the file type is not recognized,
        it returns 'Unknown File Type'.

        Parameters:
        - file_name (str): The name of the file to identify.

        Returns:
        - str: The identified file type or 'Unknown File Type' if not recognized.

        Example:
        >>> identify_file_type('sample-OUTCAR.txt')
        'OUTCAR'
        """

        # Mapping of file identifiers to their respective types, case-insensitive
        file_types = {
            'poscar': 'POSCAR', 'contcar': 'POSCAR',
            'outcar': 'OUTCAR',
            'xyz': 'xyz',
            'traj': 'traj',
            'config': 'xyz',
            'gen': 'gen',
            'pdb': 'pdb',
            'cif': 'CIF',
            'vasp': 'VASP',
            'chgcar': 'CHGCAR',
            'doscar': 'DOSCAR',
            'xdatcar': 'XDATCAR',
            'incar': 'INCAR',
            'procar': 'PROCAR',
            'wavecar': 'WAVECAR',
            'kpoints': 'KPOINTS',
            'eigenval': 'EIGENVAL',
            'metadata': 'METADATA',
        }

        # Convert the file name to lowercase for case-insensitive comparison
        file_name_lower = file_name.lower()

        # Identify the file type based on the presence of identifiers in the file name
        for identifier, file_type in file_types.items():
            if identifier in file_name_lower:
                return file_type

        # Return a default value if no known identifier is found
        return 'Unknown File Type'

    @error_handler
    def read_files(self, file_location: str = None, source: str = None, subfolders: bool = False,
                   energy_tag: str = None, forces_tag: str = None, container_index:int =None,
                   n_samples:int = None, sampling:str = 'all',
                   verbose: bool = False,  **kwargs, ):
        """
        Reads simulation files from the specified location, handling both individual files and subfolders
        containing simulation data. It supports multiple file formats and structures, adapting the reading
        process according to the source parameter.

        Parameters:
        - file_location (str, optional): The path to the directory or file containing simulation data.
                                         Defaults to None, which uses the instance's file_location attribute.
        - source (str, optional): The format/source of the simulation files (e.g., 'VASP', 'TRAJ', 'XYZ', 'OUTCAR').
                                  Defaults to None.
        - subfolders (bool, optional): If True, reads files from subfolders under the specified location.
                                       Defaults to False.
        - energy_tag (str, optional): Specific tag used to identify energy data within the files, applicable for
                                      formats like 'XYZ'. Defaults to None.
        - forces_tag (str, optional): Specific tag used to identify forces data within the files, applicable for
                                      formats like 'XYZ'. Defaults to None.
        - verbose (bool, optional): If True, enables verbose output during the file reading process. Defaults to False.

        Raises:
        - ValueError: If the source format is not recognized or supported.

        Returns:
        None
        """
        source = self._identify_file_type(file_location) if source is None else source

        if subfolders:
            self.readSubFolder(file_location=file_location, source=source, container_index=container_index, verbose=verbose)
            return

        # Define a strategy for each source format to simplify the conditional structure
        source_strategy = {
            'VASP': self.read_vasp_folder,
            'DFTB': self.read_dftb_folder,
            'TRAJ': self.read_traj,
            'XYZ': self.read_XYZ,
            'OUTCAR': self.read_OUTCAR,
            'DUMP': self.read_dump,
            'METADATA': self.read_METADATA,
        }

        # Attempt to read using a specific strategy for the source format
        if source.upper() in source_strategy:
            source_strategy[source.upper()](
                file_location=file_location, 
                add_container=True,
                verbose=verbose, 
                energy_tag=energy_tag, 
                forces_tag=forces_tag,
                container_index=container_index, 
                n_samples=n_samples,
                sampling=sampling,
            )
        else:
            # Fallback for other sources
            self.read_structure(
                file_location=file_location, 
                source=source, 
                add_container=True, 
                verbose=verbose
            )

    @error_handler
    def read_METADATA(self,
                 file_location: Optional[str] = None,
                 add_container: bool = True,
                 energy_tag: Optional[str] = None,
                 forces_tag: Optional[str] = None,
                 container_index: Optional[int] = None,
                 verbose: bool = False,
                 **kwargs, ) -> List[SingleRun]:
        """
        Reads a metadata file with columns for lattice parameters, multiple elemental species counts, 
        and an energy entry. Automatically infers which columns correspond to lattice, which to species, 
        and which to energy by examining the header labels.

        .. note::

           An example of an expected header might be:

           .. code-block:: none

              l0,l1,l2,l3,l4,l5,l6,l7,l8,H,Ni,O,K,Fe,V,E

           The first 9 columns (l0..l8) represent lattice parameters, while the final column (E) is assumed
           to be energy. All remaining columns correspond to species (e.g., H, Ni, O, K, Fe, V).

        Each subsequent row of data has the corresponding values in the same order:

        1. Identifies lattice columns by detecting those whose header starts with ``l`` (e.g. l0..l8).
        2. Identifies energy columns by detecting ``E`` or ``energy`` in the header.
        3. Classifies all remaining columns as species (e.g., H, O, Ni, etc.).
        4. Creates a :class:`SingleRun` object for each row, populating:
           - Lattice vectors
           - Composition data (number of atoms of each species)
           - Energy value
           - Calls :meth:`add_atom` on :attr:`AtomPositionManager` for as many atoms as indicated by each species count.

        :param file_location: 
            The path to the metadata file. If ``None``, uses ``self.file_location``.
        :type file_location: str, optional

        :param add_container: 
            If ``True``, the newly created :class:`SingleRun` objects are appended to the current container.
        :type add_container: bool

        :param verbose: 
            If ``True``, prints progress or debug information.
        :type verbose: bool

        :returns: 
            A list of :class:`SingleRun` objects, each corresponding to one line of data in the file.
        :rtype: List[SingleRun]

        :raises ValueError:
            If no valid file location is provided or if the file fails basic structure checks (e.g., 
            insufficient lines, column mismatch, reading errors).
        """
        # 1) Determine file location
        file_location = file_location or self.file_location
        if not file_location or not isinstance(file_location, str):
            raise ValueError("A valid file location (string) must be provided.")

        # 2) Read file content using mmap (memory-mapped file)
        try:
            with open(file_location, "r+b") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    content = mm.read().decode("utf-8")
        except Exception as e:
            raise ValueError(f"Error reading file with mmap: {str(e)}")

        # Split the file into lines. 
        lines = content.splitlines()
        if len(lines) < 2:
            raise ValueError("File must contain at least one header line and one data line.")

        # 3) Parse header and classify columns
        header_cols = lines[0].strip().split(',')

        # Identify lattice columns by those that start with 'l'
        lattice_indices = [i for i, h in enumerate(header_cols) if h.startswith('l')]

        # Identify any column(s) for energy by looking for 'E' or 'energy'
        energy_indices = [i for i, h in enumerate(header_cols) if h.lower() == 'e' or 'energy' in h.lower()]

        # Remaining columns are treated as species
        species_indices = [
            i for i in range(len(header_cols))
            if i not in lattice_indices and i not in energy_indices
        ]
        species_list = [header_cols[i] for i in species_indices]

        if verbose:
            print("Header columns:", header_cols)
            print("Lattice column indices:", lattice_indices)
            print("Energy column indices:", energy_indices)
            print("Species column indices:", species_indices)
            print("Detected species:", species_list)

        # 4) Parse data lines and build SingleRun objects
        data_lines = lines[1:]  # everything after the header
        container = []
        line_count = 0

        for row in tqdm(data_lines, desc="Processing lines", unit="line"):
            line_count += 1
            row_str = row.strip()

            # Skip empty lines
            if not row_str:
                continue

            columns = row_str.split(',')
            # If a line doesn't match the column count in the header, skip it (or handle as needed).
            if len(columns) != len(header_cols):
                if verbose:
                    print(f"Skipping line {line_count} due to column mismatch: {len(columns)} != {len(header_cols)}")
                continue

            # Create a new SingleRun object with an AtomPositionManager
            sr = SingleRun(file_location)
            sr.AtomPositionManager = AtomPosition()

            # 4a) Parse lattice data
            try:
                lattice_floats = [float(columns[i]) for i in lattice_indices]
                # Reshape to 3x3 if exactly 9 lattice entries exist; adapt if different lattice dimension
                sr.AtomPositionManager.set_latticeVectors(
                    new_latticeVectors=np.array(lattice_floats).reshape(3, 3)
                )
            except ValueError:
                if verbose:
                    print(f"Failed to parse lattice data on line {line_count}.")
                continue

            # 4b) Parse energy data (if any)
            if energy_indices:
                try:
                    # If there's only one energy column, assume the first found is the main entry
                    energy_col = energy_indices[0]
                    parsed_energy = float(columns[energy_col])
                    sr.AtomPositionManager.E = parsed_energy
                    sr.E = parsed_energy  # Optionally store in sr as well
                except ValueError:
                    if verbose:
                        print(f"Failed to parse energy data on line {line_count}.")
                    continue

            # 4c) Parse composition data (species)
            # Convert each species column to float, then store in sr.composition_data
            composition_values = []
            try:
                for i, sp_idx in enumerate(species_indices):
                    count_val = float(columns[sp_idx])
                    composition_values.append(count_val)
                sr.composition_data = np.array(composition_values, dtype=float)
            except ValueError:
                if verbose:
                    print(f"Failed to parse composition data on line {line_count}.")
                continue

            # 4d) Add atoms to the AtomPositionManager for each species
            #     We assume composition values are integer counts; fractional counts are rounded.
            for i, sp_label in enumerate(species_list):
                atom_count = int(round(sr.composition_data[i]))
                # Generate an array of zeros for positions (atom_count x 3)
                
                # Each atom belongs to the same species label; multiply the label list
                if atom_count > 0:
                    positions = np.zeros((atom_count, 3), dtype=np.float64)
                    sr.AtomPositionManager.add_atom(
                        atomLabels=[sp_label] * atom_count,
                        atomPosition=positions
                    )

            # Append this SingleRun to our local container
            container.append(sr)

        # 5) Optionally add these SingleRun objects to the current container
        if add_container:
            for sr in container:
                self.add_container(sr)

        return container

    def readSubFolder(self, file_location:str=None, source:str='VASP', container_index:int=None, verbose:bool=False, ):
        """
        Reads files from a specified directory and its subdirectories.

        This function is designed to traverse through a directory (and its subdirectories) to read files 
        according to the specified source type. It handles various file-related errors gracefully, providing 
        detailed information if verbose mode is enabled.

        Args:
            file_location (str, optional): The root directory from where the file reading starts. 
                                           Defaults to the instance's file_location attribute if not specified.
            source (str): Type of the source files to be read (e.g., 'OUTCAR' for VASP output files).
            verbose (bool, optional): If True, enables verbose output including error traces.
        """
        file_location = file_location if type(file_location) == str else self.file_location
        for root, dirs, files in os.walk(file_location):
            if verbose: print(root, dirs, files)

            if source == 'OUTCAR': file_location_edited = f'{root}/OUTCAR'
            else: file_location_edited = f'{root}' 

            try:
                SR = self.read_files(file_location=file_location_edited, source=source, subfolders=False, container_index=container_index, verbose=verbose)
            except FileNotFoundError:
                self._handle_error(f"File not found at {file_location_edited}", verbose)
            except IOError:
                self._handle_error(f"IO error reading file at {file_location_edited}", verbose)
            except Exception as e:
                self._handle_error(f"Unexpected error: {e}", verbose)

    @error_handler
    def read_structure(
        self, 
        file_location:str=None, 
        source:str=None, 
        add_container:bool=True, 
        container_index:int=None, 
        verbose=False,
        **kwargs
    ):
        """
        Reads a trajectory file and stores each frame along with its time information.

        Args:
            file_location (str, optional): The file path of the trajectory file.
            verbose (bool, optional): If True, enables verbose output.

        Notes:
            This method updates the containers with SingleRun objects representing each frame.
            If available, time information is also stored.
        """
        file_location = file_location if type(file_location) == str else self.file_location
        SR = SingleRun(file_location)
        SR.read_structure(file_location=file_location, source=source, container_index=container_index) 
        self.add_container(container=SR)

    @error_handler
    def read_dump(
        self, 
        file_location:str=None, 
        add_container:bool=True, 
        container_index: Optional[int] = None, 
        verbose=False, 
        **kargs
    ):
        '''
        '''
        file_location = file_location if type(file_location) == str else self.file_location

        lines =list(self.read_files(file_location,strip=False))
        container = []

        for i, line in enumerate(lines):
            if line.startswith("ITEM: TIMESTEP"):
                SR = SingleRun(file_location)
                SR.AtomPositionManager = AtomPosition()
                SR.AtomPositionManager.read_DUMP(lines=lines[i:])

                container.append(SR)

                if add_container and SR.AtomPositionManager is not None: 
                    container.append(SR)
                    
                if verbose: 
                    try: 
                        print(f' >> READ dump :: frame {len(container)} - atoms {num_atoms}')
                    except Exception as e:
                        print(f'Verbose output failed due to an error: {e}')
                        print('Skipping line due to the above error.')

        if isinstance(container_index, int):  
            self.add_container(container=container[container_index])
        else:
            for sr in container:
                self.add_container(container=container[container_index])
          
        return container

    @error_handler
    def read_traj(
        self,
        file_location: Optional[str] = None,
        add_container: bool = True,
        container_index: Optional[int] = None,
        verbose: bool = False,
        stride=1, 
        parallel=False,
        *args,
        **kwargs
    ) -> List[object]:
        """
        Read a trajectory file and store each frame along with its time information.

        Parameters
        ----------
        file_location : str, optional
            The file path of the trajectory file. If None, uses `self.file_location`.
        add_container : bool, default=True
            If True, adds the frames as containers to the object.
        container_index : int, optional
            If specified, only the frame at this index is added as a container.
        verbose : bool, default=False
            If True, enables detailed output (logging).
        *args, **kwargs :
            Additional arguments passed to lower-level functions (reserved).

        Returns
        -------
        list of SingleRun
            A list of `SingleRun` objects for each frame read.

        Raises
        ------
        FileNotFoundError
            If the trajectory file does not exist.
        IndexError
            If `container_index` is provided but out of range.
        RuntimeError
            For unexpected errors while reading the trajectory.
        """
        try:
            from ase.io import Trajectory
        except ImportError as e:
            raise ImportError("ASE must be installed to use read_traj.") from e

        from ase.io import Trajectory
        import os
        from concurrent.futures import ProcessPoolExecutor
        from tqdm import tqdm

        path = file_location if file_location else getattr(self, "file_location", None)
        if not path or not os.path.exists(path):
            raise FileNotFoundError(f"Trajectory file not found: {path}")

        traj = Trajectory(path)
        n_frames = len(traj[::stride])
        container = [None] * n_frames

        def process_frame(i_atoms_tuple):
            i, atoms = i_atoms_tuple
            sr = SingleRun(path)
            sr.AtomPositionManager.read_ASE(ase_atoms=atoms)
            return i, sr

        frame_iter = ((i, atoms) for i, atoms in enumerate(traj[::stride]))

        if parallel:
            with ProcessPoolExecutor() as pool:
                results = pool.map(process_frame, frame_iter)
                for i, sr in tqdm(results, total=n_frames, disable=not verbose):
                    container[i] = sr
        else:
            for i, atoms in tqdm(frame_iter, total=n_frames, disable=not verbose):
                i, sr = process_frame((i, atoms))
                container[i] = sr

        # Optionally add to self
        if add_container:
            if isinstance(container_index, int):
                self.add_container(container[container_index])
            else:
                for sr in container:
                    if sr and sr.AtomPositionManager is not None:
                        self.add_container(sr)

        return container

    def read_XYZ_legacy(self,
                 file_location: Optional[str] = None,
                 add_container: bool = True,
                 energy_tag: Optional[str] = None,
                 forces_tag: Optional[str] = None,
                 container_index: Optional[int] = None,
                 verbose: bool = False,
                 **kwargs,) -> List[SingleRun]:
        """
        Read XYZ file(s) and create SingleRun objects with AtomPosition data.

        This method processes XYZ format files, extracting atomic positions and 
        optionally energy and forces data. It creates SingleRun objects for each 
        frame in the XYZ file and can add them to the current object's container.

        Args:
            file_location (str, optional): Path to the XYZ file. If None, uses self.file_location.
            add_container (bool): If True, adds created SingleRun objects to the current object's container.
            energy_tag (str, optional): Tag to identify energy data in the XYZ file.
            forces_tag (str, optional): Tag to identify forces data in the XYZ file.
            container_index (int, optional): If provided, only adds the SingleRun at this index to the container.
            verbose (bool): If True, prints progress information.

        Returns:
            List[SingleRun]: A list of created SingleRun objects.

        Raises:
            ValueError: If the file cannot be read or parsed correctly.
        """

        # --------------------------------------------------------------------------
        # 1) Determine file location
        # --------------------------------------------------------------------------
        file_location = file_location or self.file_location
        if not isinstance(file_location, str):
            raise ValueError("Invalid file location provided.")

        # --------------------------------------------------------------------------
        # 2) Use mmap to read the entire file content in binary mode
        #    We decode it into a string for further line splitting.
        #    If mmap fails for some reason, a ValueError is raised.
        # --------------------------------------------------------------------------
        try:
            with open(file_location, "r+b") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    # Read entire file content from the memory map
                    content = mm.read().decode("utf-8")
        except Exception as e:
            raise ValueError(f"Error reading file with mmap: {str(e)}")

        # --------------------------------------------------------------------------
        # 3) Convert file content into a list of lines
        #    splitlines() automatically handles various newline styles.
        # --------------------------------------------------------------------------
        lines = content.splitlines(keepends=False)

        # --------------------------------------------------------------------------
        # 4) First pass: determine total number of frames (for tqdm initialization).
        #    Each frame is denoted by a valid integer > 0 on a line (the number of atoms).
        # --------------------------------------------------------------------------
        total_frames = 0
        for line in lines:
            line_str = line.strip()
            if line_str.isdigit():
                try:
                    if int(line_str) > 0:
                        total_frames += 1
                except ValueError:
                    # If parsing fails, we ignore this line
                    pass

        # --------------------------------------------------------------------------
        # 5) Main loop: parse each frame by detecting its start, then reading
        #    'num_atoms + 2' lines for that frame.
        # --------------------------------------------------------------------------
        
        container = []

        i = 0  # line index
        idx = 0
        with tqdm(total=total_frames, desc="Reading XYZ frames", unit="frame") as pbar:
            while i < len(lines):
                line_str = lines[i].strip()
                # If this line is a valid positive integer, treat it as a frame start
                if line_str.isdigit():
                        #try:

                        num_atoms = int(line_str)
                        if num_atoms > 0:
                            # Create a SingleRun instance and parse the frame
                            
                            #sr.AtomPositionManager = AtomPosition()

                            end_idx = i + num_atoms + 2
                            # Check if the file has enough lines for this frame
                            if end_idx > len(lines):
                                if verbose:
                                    print(f"Frame extends beyond end of file at line {i}. Stopping parse.")
                                break

                            sr = SingleRun(file_location)
                            # The method 'AtomPositionManager.read_XYZ' will parse these lines

                            sr.AtomPositionManager.read_XYZ(
                                lines=lines[i:end_idx],
                                tags={'energy': energy_tag, 'forces': forces_tag}
                            )

                            container.append( sr )
                            pbar.update(1)

                            # Jump the file pointer to the end of the current frame
                            i = end_idx
                            idx += 1
                            continue
                        #except Exception as e:
                        # Any parsing errors get printed if verbose is True
                        if verbose:
                            print(f"Verbose output failed at frame {len(container)}: {e}")
                i += 1  # Move to the next line if not a valid frame start

        # --------------------------------------------------------------------------
        # 6) Optionally add these SingleRun objects to the current object's container
        # --------------------------------------------------------------------------
        if add_container:
            if isinstance(container_index, int):
                if container_index < len(container):
                    self.add_container(container=container[container_index])
                else:
                    raise IndexError("Container index out of range.")
            else:
                for sr in container:
                    if sr.AtomPositionManager is not None:
                        self.add_container(container=sr)

        return container


    @error_handler
    def read_XYZ(self,
                 file_location: Optional[str] = None,
                 add_container: bool = True,
                 energy_tag: Optional[str] = None,
                 forces_tag: Optional[str] = None,
                 container_index: Optional[int] = None,
                 verbose: bool = False,
                 *,
                 sampling: str = 'all',            # 'all' | 'stride' | 'random' | 'fraction' | 'indices'
                 stride: int = 1,
                 n_samples: Optional[int] = None,  # for 'random'
                 frac: Optional[float] = None,     # for 'fraction'
                 indices: Optional[Iterable[int]] = None,  # explicit frame indices (0-based, after window)
                 start: Optional[int] = None,
                 stop: Optional[int] = None,
                 seed: Optional[int] = None,
                 random_mode: str = "exact",        # 'fast' | 'exact'
                 index_path: Optional[str] = None,
                 index_force: bool = False,         # <-- force rebuild of the index
                 max_attempts_per_sample: int = 25,
                 **kwargs
                 ) -> List[SingleRun]:
        """
        Efficient XYZ reader with streaming + subsampling.
        Robust to malformed frames and stale indices.

        Modes:
          - sampling='all'       : stream parse, keep all
          - sampling='stride'    : keep every k-th (stride>=1)
          - sampling='fraction'  : Bernoulli(p) single pass (0<p<=1)
          - sampling='indices'   : load explicit frame indices (relative to window)
          - sampling='random'    : read only n_samples frames
                random_mode='fast'  -> approximate random (no index/full scan)
                random_mode='exact' -> uses index (.xzi.npz), seeks to sampled frames

        Windowing via [start:stop) applies before sampling in the streaming modes.

        NOTE (minimal change): when add_container=True, frames are added to the container
        on-the-fly to minimize memory usage; the function then returns [].
        """
        # --- New imports near the top of your function ---
        import math
        from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
        import os, random
        from typing import List, Callable
        import numpy as np
        from tqdm import tqdm
        import sys, multiprocessing as mp

        # --------- normalize & validate inputs ----------
        file_location = file_location or self.file_location
        if not isinstance(file_location, str) or not file_location:
            raise ValueError("file_location must be specified for reading.")
        file_location = os.path.abspath(file_location)

        # --- Add these helpers inside read_XYZ (or as privates on the class) ---
        def _parse_frame_from_mmap(mm, frame_offset, natoms, *,
                                   energy_tag: str | None,
                                   forces_tag: str | None,
                                   file_location: str,
                                   decode_to_text: bool = True,
                                   **kwargs):
            """
            Slice one XYZ frame [header, comment, natoms lines] and let your
            AtomPositionManager.read_XYZ(...) parse it.
            """
            # end of header (first newline)
            eoh = mm.find(b"\n", frame_offset)
            if eoh == -1:
                raise ValueError("Truncated frame: missing header EOL.")

            # comment line bounds
            c0 = eoh + 1
            c1 = mm.find(b"\n", c0)
            if c1 == -1:
                raise ValueError("Truncated frame: missing comment line.")

            # bounds of the atom block (exactly natoms lines)
            p = c1 + 1
            end = p
            for _ in range(natoms):
                end = mm.find(b"\n", end)
                if end == -1:
                    raise ValueError("Truncated frame: missing atom line(s).")
                end += 1  # include newline

            # take the whole frame (header + comment + atoms)
            frame_bytes = mm[frame_offset:end]

            # Build `lines` in the shape your manager expects
            if decode_to_text:
                # One decode per frame; fast and simple
                lines = frame_bytes.decode("utf-8", "ignore").splitlines()
            else:
                # If your manager can handle bytes, skip decode (faster)
                lines = frame_bytes.splitlines()

            # Construct SingleRun safely (use keywords to avoid the positional-args error)
            sr = SingleRun(file_location)

            # Delegate parsing of this frame to your manager
            sr.AtomPositionManager.read_XYZ(
                lines=lines,
                tags={"energy": energy_tag, "forces": forces_tag}
            )
            return sr

        def _parse_frames_chunk_worker(args):
            """
            Worker: open file, mmap once, parse a CHUNK of frames.
            Returns list of tuples (global_idx, SingleRun).
            """
            (path, chunk_indices, chunk_offsets, chunk_natoms,
             energy_tag, forces_tag, kwargs) = args
            import mmap
            out = []
            with open(path, "rb") as f:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                for gid, off, n in zip(chunk_indices, chunk_offsets, chunk_natoms):
                    try:
                        sr = _parse_frame_from_mmap(
                            mm,
                            int(off),
                            int(n),
                            energy_tag=energy_tag,
                            forces_tag=forces_tag,
                            file_location=file_location,
                            decode_to_text=True,
                            **kwargs,
                        )
                        out.append((int(gid), sr))
                    except Exception as e:
                        # You already have @error_handler; keep robust behavior here:
                        if kwargs.get("verbose", False):
                            print(f"[XYZ-PARSE] Skipping frame {gid}: {e}")
                        continue
            return out

        def _parallel_parse_selected(path: str,
                                     sel_indices: np.ndarray,
                                     offsets: np.ndarray,
                                     natoms: np.ndarray,
                                     energy_tag: Optional[str],
                                     forces_tag: Optional[str],
                                     *,
                                     parallel: int,
                                     parallel_chunk: int,
                                     prefer_threads: bool,
                                     # NEW knobs (compatible defaults)
                                     parallel_backend: str = "auto",     # 'auto' | 'process' | 'thread'
                                     add_fn: Optional[Callable[[ "SingleRun"], None]] = None,
                                     **kwargs) -> List["SingleRun"]:
            """
            Parse selected frames in parallel. If add_fn is provided, each SingleRun is streamed
            to add_fn as soon as available (low-memory). Otherwise, return results ordered
            like sel_indices.
            """
            # ---- progress bar ----
            show_progress = bool(kwargs.get("show_progress", kwargs.get("verbose", False)))
            total = int(len(sel_indices))
            pbar = tqdm(total=total, desc="Parsing XYZ", dynamic_ncols=True) if (show_progress and tqdm and total > 0) else None

            # Pre-slice chunks once (used by both sequential & parallel paths)
            chunks = []
            for i in range(0, len(sel_indices), parallel_chunk):
                sl = slice(i, i + parallel_chunk)
                chunks.append((
                    path,
                    sel_indices[sl],
                    offsets[sl],
                    natoms[sl],
                    energy_tag,
                    forces_tag,
                    kwargs
                ))

            def _run_sequential():
                use_sink = add_fn is not None
                results = {} if not use_sink else None
                for c in chunks:
                    out = _parse_frames_chunk_worker(c)
                    if use_sink:
                        for _, sr in out:
                            add_fn(sr)
                    else:
                        for gid, sr in out:
                            results[gid] = sr
                    if pbar is not None:
                        pbar.update(len(out))
                if use_sink:
                    return []
                return [results[i] for i in sel_indices if i in results]

            # Fast exit: no parallelism requested
            if parallel <= 1 or total == 0:
                ret = _run_sequential()
                if pbar is not None:
                    if add_fn is None:
                        ok = len(ret)
                        skipped = max(0, total - ok)
                    else:
                        ok = pbar.n
                        skipped = max(0, total - ok)
                    pbar.set_postfix({"ok": ok, "skipped": skipped})
                    pbar.close()
                return ret

            # Decide backend
            # - prefer threads if caller asked
            # - on macOS/Windows default to threads unless user forces processes
            # - user can override with parallel_backend='process' or 'thread'
            use_threads = prefer_threads
            if parallel_backend == "thread":
                use_threads = True
            elif parallel_backend == "process":
                use_threads = False
            else:  # 'auto'
                if sys.platform in ("darwin", "win32"):
                    use_threads = True

            # Helper to run threads (no pickling issues)
            def _run_threads():
                from concurrent.futures import ThreadPoolExecutor, as_completed
                use_sink = add_fn is not None
                results = {} if not use_sink else None
                with ThreadPoolExecutor(max_workers=parallel) as ex:
                    futs = [ex.submit(_parse_frames_chunk_worker, c) for c in chunks]
                    for fu in as_completed(futs):
                        out = fu.result()
                        if add_fn is not None:
                            for _, sr in out:
                                add_fn(sr)
                        else:
                            for gid, sr in out:
                                results[gid] = sr
                        if pbar is not None:
                            pbar.update(len(out))
                return [] if use_sink else results

            # Helper to run processes (may fail — we’ll catch and fall back)
            def _run_processes():
                from concurrent.futures import ProcessPoolExecutor, as_completed
                use_sink = add_fn is not None
                # Try to use 'fork' context on Unix (reduces overhead); fallback to default if unavailable
                mp_ctx = None
                try:
                    mp_ctx = mp.get_context("fork")
                except (ValueError, AttributeError):
                    mp_ctx = None
                kwargs_ex = dict(max_workers=parallel)
                if mp_ctx is not None:
                    kwargs_ex["mp_context"] = mp_ctx
                results = {} if not use_sink else None
                with ProcessPoolExecutor(**kwargs_ex) as ex:
                    futs = [ex.submit(_parse_frames_chunk_worker, c) for c in chunks]
                    for fu in as_completed(futs):
                        out = fu.result()
                        if add_fn is not None:
                            for _, sr in out:
                                add_fn(sr)
                        else:
                            for gid, sr in out:
                                results[gid] = sr
                        if pbar is not None:
                            pbar.update(len(out))
                return [] if use_sink else results

            # Execute chosen backend, with safe fallback
            try:
                results = _run_threads() if use_threads else _run_processes()
            except Exception as e:
                if pbar is not None:
                    pbar.write(f"[read_XYZ] Process pool failed ({type(e).__name__}: {e}); falling back to threads.")
                results = _run_threads()

            if pbar is not None:
                if add_fn is None and isinstance(results, dict):
                    ok = len(results)
                else:
                    ok = pbar.n
                pbar.set_postfix({"ok": ok, "skipped": max(0, total - ok)})
                pbar.close()

            if add_fn is not None:
                return []
            # Order results like sel_indices
            return [results[i] for i in sel_indices if i in results]

        start = 0 if start is None else max(0, int(start))
        stop = None if stop is None else max(0, int(stop))

        rng = random.Random(seed)

        # --------- helpers (local closures) ----------

        def _xyz_index_path(path: str, ipath: Optional[str]) -> str:
            base = os.path.splitext(os.path.abspath(path))[0]
            return os.path.abspath(ipath) if ipath else base + ".xzi.npz"

        def _build_xyz_index(path: str, ipath: Optional[str], force: bool = False) -> tuple[np.ndarray, np.ndarray]:
            """
            One-time pass to store frame start offsets and natoms as .npz, with file metadata.
            Returns (offsets, natoms).
            """
            import mmap, time

            path = os.path.abspath(path)
            ipath_final = _xyz_index_path(path, ipath)

            # File metadata for invalidation
            st = os.stat(path)
            meta_now = dict(filesize=st.st_size, mtime=int(st.st_mtime))

            if (not force) and os.path.exists(ipath_final):
                data = np.load(ipath_final, allow_pickle=True)
                meta = dict(data["meta"].item()) if "meta" in data.files else None
                if meta and meta.get("filesize") == meta_now["filesize"] and meta.get("mtime") == meta_now["mtime"]:
                    return data["offsets"], data["natoms"]
                # else: fallthrough to rebuild

            offsets: List[int] = []
            natoms_list: List[int] = []
            with open(path, "rb") as f:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                size = mm.size()
                pos = 0
                while pos < size:
                    eol = mm.find(b"\n", pos)
                    if eol == -1:
                        break
                    header = mm[pos:eol].strip()
                    # parse header
                    try:
                        n = int(header)
                        if n <= 0:
                            pos = eol + 1
                            continue
                    except Exception:
                        pos = eol + 1
                        continue

                    # comment line
                    c0 = eol + 1
                    c1 = mm.find(b"\n", c0)
                    if c1 == -1:
                        break

                    # record frame start
                    offsets.append(pos)
                    natoms_list.append(n)

                    # skip n atom lines
                    p = c1 + 1
                    ok = True
                    for _ in range(n):
                        q = mm.find(b"\n", p)
                        if q == -1:
                            ok = False
                            break
                        p = q + 1
                    pos = p if ok else size

            offsets_arr = np.asarray(offsets, dtype=np.int64)
            natoms_arr = np.asarray(natoms_list, dtype=np.int64)
            np.savez_compressed(ipath_final, offsets=offsets_arr, natoms=natoms_arr, meta=meta_now)

            if verbose:
                print(f"[XYZ-INDEX] Wrote {len(offsets_arr)} entries → {ipath_final}")
            return offsets_arr, natoms_arr

        # --- After you have (offsets, natoms) and decided on the selected frame IDs ---
        # Example of building/using the index:
        offsets_all, natoms_all = _build_xyz_index(file_location, index_path, force=index_force)

        # Apply [start:stop) window
        n_total = len(offsets_all)
        lo = start
        hi = n_total if stop is None else min(stop, n_total)
        window_ids = np.arange(lo, hi, dtype=np.int64)

        # Apply sampling:
        if sampling == 'all':
            selected_ids = window_ids
        elif sampling == 'stride':
            selected_ids = window_ids[::stride]
        elif sampling == 'fraction':
            # Bernoulli single pass guided by rng
            mask = np.fromiter((rng.random() < frac for _ in range(len(window_ids))),
                               count=len(window_ids), dtype=bool)
            selected_ids = window_ids[mask]
        elif sampling == 'indices':
            # Indices are relative to the window
            selected_ids = window_ids[np.asarray(indices, dtype=np.int64)]
        elif sampling == 'random':
            if random_mode == 'exact':
                # sample without replacement for exact n_samples
                selected_ids = np.array(rng.sample(list(window_ids), k=min(n_samples, len(window_ids))),
                                        dtype=np.int64)
                selected_ids.sort()  # keeps reading mostly forward for better locality
            else:
                # 'fast' mode: no index required; but since we're using offsets, we leverage it anyway
                selected_ids = np.array(rng.sample(list(window_ids), k=min(n_samples, len(window_ids))),
                                        dtype=np.int64)
                selected_ids.sort()
        else:
            raise ValueError("Unsupported sampling")

        # Gather offsets/natoms for the selection
        sel_offsets = offsets_all[selected_ids]
        sel_natoms  = natoms_all[selected_ids]

        # --- NEW: streaming add hook (low-memory path when add_container=True) ---
        add_fn = None
        if add_container:
            def _sink(sr):
                # Minimal, robust call; ignore container_index to avoid API coupling
                try:
                    self.add_container(container=sr)
                except TypeError:
                    # Fallback in case add_container signature differs
                    self.add_container(sr)
            add_fn = _sink

        # Parse + either stream to container or return list
        parsed: List[SingleRun] = _parallel_parse_selected(
            file_location,
            selected_ids,
            sel_offsets,
            sel_natoms,
            energy_tag,
            forces_tag,
            parallel=kwargs.get("parallel", 1),
            parallel_chunk=kwargs.get("parallel_chunk", 256),
            prefer_threads=kwargs.get("prefer_threads", False),
            verbose=verbose,
            max_attempts_per_sample=max_attempts_per_sample,  # propagate if used inside parser
            add_fn=add_fn,                                     # <- stream if provided
            **kwargs
        )

        # If you had add_container / container_index logic, the streaming path already handled it.
        if add_container:
            return []  # streamed into container; keep memory low

        return parsed

    def read_OUTCAR(self,
                    file_location: Optional[str] = None,
                    add_container: bool = True,
                    container_index: Optional[int] = None,
                    verbose: bool = False,
                    **kwargs) -> List[SingleRun]:
        """
        Read and process an OUTCAR file, creating SingleRun objects from its contents.

        This method reads an OUTCAR file using the OutFileManager, extracts relevant data,
        and creates SingleRun objects. It handles both cases where dynamical eigenvectors
        are present or not.

        Args:
            file_location (str, optional): Path to the OUTCAR file. If None, uses the default location.
            add_container (bool): If True, adds created SingleRun objects to the container.
            container_index (int, optional): If provided, only adds the SingleRun at this index to the container.
            verbose (bool): If True, prints additional information during processing.
            **kwargs: Additional keyword arguments (unused in this implementation but allows for future expansion).

        Returns:
            List[SingleRun]: A list of created SingleRun objects.

        Raises:
            FileNotFoundError: If the specified OUTCAR file is not found.
            ValueError: If container_index is out of range or if no file location is provided.
            RuntimeError: If there's an error reading the OUTCAR file.
        """
        # Validate and set file location
        file_location = file_location or self.file_location
        if not file_location:
            raise ValueError("No file location provided for OUTCAR reading.")

        # Read OUTCAR file
        try:
            of = OutFileManager(file_location)
            of.readOUTCAR()
            if verbose:
                print(f"Successfully read OUTCAR file from {file_location}")
        except FileNotFoundError:
            raise FileNotFoundError(f"OUTCAR file not found at {file_location}")
        except Exception as e:
            raise RuntimeError(f"Error reading OUTCAR file: {str(e)}")

        new_containers = []

        # Process data based on presence of dynamical eigenvectors
        if of.dynamical_eigenvector is not None:
            if verbose:
                print("Processing OUTCAR with dynamical eigenvectors.")
            for eigenvalues, eigenvector, eigenvector_diff in zip(
                of.dynamical_eigenvalues, of.dynamical_eigenvector, of.dynamical_eigenvector_diff
            ):
                sr = SingleRun(file_location)
                sr._AtomPositionManager = of.AtomPositionManager[0]
                sr._AtomPositionManager._atomPositions = eigenvector
                sr._AtomPositionManager._dynamical_eigenvector = eigenvector
                sr._AtomPositionManager._dynamical_eigenvalues = eigenvalues
                sr._AtomPositionManager._dynamical_eigenvector_diff = eigenvector_diff
                sr._InputFileManager = of.InputFileManager
                sr._KPointsManager = of._KPointsManager
                sr._PotentialManager = of._PotentialManager
                new_containers.append(sr)
        else:
            if verbose:
                print("Processing OUTCAR without dynamical eigenvectors.")

            for apm in of.AtomPositionManager:
                sr = SingleRun(file_location)
                sr._AtomPositionManager = apm
                sr._InputFileManager = of.InputFileManager
                sr._KPointsManager = of._KPointsManager
                sr._PotentialManager = of._PotentialManager
                new_containers.append(sr)

        if verbose:
            print(f"Created {len(new_containers)} SingleRun objects from OUTCAR.")

        # Add containers to the manager based on the provided index or add all
        if add_container:
            if isinstance(container_index, int):
                if 0 <= container_index < len(new_containers):
                    self.add_container(container=new_containers[container_index])
                    if verbose:
                        print(f"Added SingleRun object at index {container_index} to container.")
                else:
                    raise ValueError(f"Container index {container_index} is out of range.")
            else:
                for sr in new_containers:
                    self.add_container(container=sr)
                if verbose:
                    print(f"Added all {len(new_containers)} SingleRun objects to container.")

        return new_containers

    def read_vasp_folder(self, file_location:str=None, add_container:bool=True, verbose:bool=False, **kwargs):
        '''
        '''
        file_location = file_location if type(file_location) == str else self.file_location
        SR = SingleRun(file_location)
        SR.readVASPDirectory(file_location)        
        if add_container and SR.AtomPositionManager is not None: 
            self.add_container(container=SR)

        return SR

    def read_dftb_folder(self, file_location:str=None, add_container:bool=True, verbose:bool=False, **kwargs):
        '''
        '''
        file_location = file_location if type(file_location) == str else self.file_location
        SR = SingleRun(file_location)
        SR.readDFTBDirectory(file_location)        
        if add_container and SR.AtomPositionManager is not None: 
            self.add_container(container=SR)

        return SR

    def export_files(self, file_location:str=None, source:str=None, label:str=None, bond_factor:float=None, verbose:bool=False ):
        """
        Exports files for each container in a specified format.

        If a filename is already present in `file_location` (e.g., ends with 'POSCAR',
        'my_run.xyz', etc.), the function will use it as-is and will NOT append the
        generic default name. Otherwise, a generic name is appended.

        Args:
            file_location (str): Base directory or full path to the output file(s).
            source (str): Export format ('VASP', 'POSCAR', 'XYZ', 'PDB', 'ASE', 'GEN', or any ASE fmt).
            label (str): Labeling strategy for directories ('enumerate' or 'fixed').
            bond_factor (float): Bond factor (for PDB export).
            verbose (bool): Verbose errors.
        """
        from pathlib import Path
        import traceback
        from tqdm import tqdm

        # Identify the file type if 'source' is not specified
        source = self._identify_file_type(file_location) if source is None else source
        # Set a default labeling strategy if not provided
        label = label if isinstance(label, str) else 'fixed'
        src_upper = source.upper()

        def _ensure_named_path(base: str, default_name: str, known_names=None) -> Path:
            """
            If `base` already looks like a file (has a suffix) OR matches a known filename
            (e.g., 'POSCAR', 'structure.pdb'), return it unchanged. Otherwise append `default_name`.
            """
            p = Path(base) if base is not None else Path('.')
            if p.suffix:  # user gave '.../file.ext'
                return p
            if known_names:
                names = {n.lower() for n in known_names}
                if p.name.lower() in names:
                    return p
            return p / default_name

        file_locations = []

        # Use tqdm to show progress over the containers
        for c_i, container in enumerate(tqdm(self.containers, desc="Exporting containers", unit="container")):
            try:
                # Determine the number of digits to keep enumeration consistent (e.g., 001, 002, ...)
                num_digits = len(str(len(self.containers)))

                # Label-based path selection (directory base)
                if label == 'enumerate':
                    file_location_edited = (file_location or '.') + f'/{c_i:0{num_digits}d}'
                elif label == 'fixed':
                    file_location_edited = container.file_location
                else:
                    file_location_edited = container.file_location  # fallback

                # Export based on the specified source format
                if src_upper == 'VASP':
                    # VASP exporters typically expect a directory; honor user path as directory.
                    self.create_directories_for_path(file_location_edited)
                    container.exportVASP(file_location=file_location_edited)

                elif src_upper == 'POSCAR':
                    # If user gave a file path ending with 'POSCAR', use it; else append 'POSCAR'
                    dst = _ensure_named_path(file_location_edited, 'POSCAR', known_names=['POSCAR'])
                    self.create_directories_for_path(str(dst.parent))
                    container.AtomPositionManager.export_as_POSCAR(file_location=str(dst))

                elif src_upper == 'XYZ':
                    # Historical behavior: append all configs to a single XYZ at `file_location`
                    # Now: if user provided a filename (e.g., ".../my_run.xyz"), use it as-is,
                    # otherwise default to ".../config.xyz".
                    dst = _ensure_named_path(file_location, 'config.xyz', known_names=['config.xyz'])
                    self.create_directories_for_path(str(Path(dst).parent))
                    container.AtomPositionManager.export_as_xyz(file_location=str(dst), save_to_file='a')

                elif src_upper == 'PDB':
                    dst = _ensure_named_path(file_location_edited, 'structure.pdb', known_names=['structure.pdb'])
                    self.create_directories_for_path(str(dst.parent))
                    container.AtomPositionManager.export_as_PDB(file_location=str(dst), bond_factor=bond_factor)

                elif src_upper == 'GEN':
                    dst = _ensure_named_path(file_location_edited, 'geo_end.gen', known_names=['geo_end.gen'])
                    self.create_directories_for_path(str(dst.parent))
                    container.AtomPositionManager.export_as_GEN(file_location=str(dst))

                elif src_upper == 'ASE':
                    dst = _ensure_named_path(file_location_edited, 'ase.obj', known_names=['ase.obj'])
                    self.create_directories_for_path(str(dst.parent))
                    container.AtomPositionManager.export_as_ASE(file_location=str(dst))

                else:
                    # Generic ASE-supported format: default to 'structure.<fmt>'
                    default_name = f'structure.{source.lower()}'
                    dst = _ensure_named_path(file_location_edited, default_name, known_names=[default_name])
                    self.create_directories_for_path(str(dst.parent))
                    container.AtomPositionManager.export(file_location=str(dst), fmt=source)

                # Keep track of the exported location (preserve prior behavior: track the container base directory)
                file_locations.append(file_location_edited)

            except Exception as e:
                if verbose:
                    print(f"Failed to export container {c_i}: {e}")
                    traceback.print_exc()
                else:
                    # still continue to next container
                    pass

        # self.generate_execution_script_for_each_container(directories=file_locations, file_location='.')
        return file_locations


    def export_configXYZ(self, file_location: Optional[str] = None, verbose: bool = False) -> bool:
        """
        Export configuration data in XYZ format for all containers with OutFileManager.

        This method creates a single XYZ file containing the configuration data from all
        containers that have an OutFileManager. The data is appended to the file for each
        container.

        Args:
            file_location (str, optional): Path where the XYZ file will be saved.
                If None, uses the default location with '_config.xyz' appended.
            verbose (bool): If True, prints additional information during the export process.

        Returns:
            bool: True if the export was successful, False otherwise.

        Raises:
            IOError: If there's an error creating or writing to the file.
        """
        try:
            # Determine the file location
            file_location = file_location or f"{self.file_location}_config.xyz"
            
            if verbose:
                print(f"Preparing to export XYZ configuration to {file_location}")

            # Create an empty file or truncate existing file
            with open(file_location, 'w') as f:
                pass

            export_count = 0
            for container_index, container in enumerate(self.containers):
                if container.OutFileManager is not None:
                    try:
                        container.OutFileManager.export_configXYZ(
                            file_location=file_location, 
                            save_to_file='a',  # Append mode
                            verbose=False  # We'll handle verbosity here
                        )
                        export_count += 1
                        if verbose:
                            print(f"Exported configuration for container {container_index}")
                    except Exception as e:
                        print(f"Warning: Failed to export container {container_index}. Error: {str(e)}")

            if verbose:
                print(f"XYZ content has been saved to {file_location}")
                print(f"Exported configurations for {export_count} out of {len(self.containers)} containers")

            return True

        except IOError as e:
            print(f"Error: Failed to create or write to file {file_location}. Error: {str(e)}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            return False
    
    def _is_redundant(self, containers:list=None, new_container:object=None):
        """
        Checks if a new container is redundant within existing containers.

        Args:
        - new_container (object): The new container to check.
        - containers (list, optional): List of existing containers.

        Returns:
        - bool: True if redundant, False otherwise.
        """
        containers = containers if containers is not None else self.containers
        return any(np.array_equal(conteiner.atomPositions, new_container.atomPositions) for conteiner in containers)

    def summary(self, ) -> str:
        """
        Generates a summary string of the PartitionManager's current state.

        Returns:
            str: A summary string detailing the file location and the number of containers managed.
        """
        text_str = ''
        text_str += f'{self.file_location}\n'
        text_str += f'> Conteiners : { len(self.containers) }\n'
        return text_str
    
    def copy_and_update_container(self, container, sub_directory: str, file_location=None):
        """
        Creates a deep copy of a given container and updates its file location.

        Args:
            container (object): The container object to be copied.
            sub_directory (str): The subdirectory to append to the container's file location.
            file_location (str, optional): Custom file location for the new container. If None, appends sub_directory to the original container's file location.

        Returns:
            object: The copied and updated container object.
        """
        container_copy = copy.deepcopy(container)
        container_copy.file_location = f'{container.file_location}{sub_directory}' if file_location is None else file_location
        return container_copy

    def generate_execution_script_for_each_container(self, directories: list = None, file_location: str = None, max_batch_size:int=200):
        """
        Generates and writes an execution script for each container in the specified directories.

        Args:
            directories (list, optional): List of directory paths for which the execution script is to be generated.
            file_location (str, optional): The file path where the generated script will be saved.

        Notes:
            The script 'RUNscript.sh' will be generated and saved to each specified directory.
        """
        self.create_directories_for_path(file_location)
        script_content = self.generate_script_content(script_name='RUNscript.sh', directories=directories, max_batch_size=max_batch_size)
        self.write_script_to_file(script_content, f"{file_location}")

    def generate_script_content(self, script_name:str, directories:list=None, max_batch_size:int=200) -> str:
        """
        Generates the content for a script that runs specified scripts in given directories.

        Args:
            script_name (str): The name of the script to run in each directory.
            directories (list, optional): A list of directories where the script will be executed.

        Returns:
            str: The generated script content as a string.
        """
        directories_str_list = [  "\n".join([f"    '{directory}'," for directory in directories[i:i + max_batch_size] ]) for i in range(0, len(directories), max_batch_size)]
        
        return [f'''#!/usr/bin/env python3
import os
import subprocess

original_directory = os.getcwd()

directories = [
{directories_str}
]

for directory in directories:
    os.chdir(directory)
    subprocess.run(['chmod', '+x', '{script_name}'])
    subprocess.run(['sbatch', '{script_name}'])
    os.chdir(original_directory)
''' for directories_str in directories_str_list ] 

    def write_script_to_file(self, script_content: str, file_path: str):
        """
        Writes the provided script content to a file at the specified path.

        Args:
            script_content (str): The content of the script to be written.
            file_path (str): The file path where the script will be saved.

        Notes:
            This method creates or overwrites the file at the specified path with the given script content.
        """
        for sc_index, sc in enumerate(script_content):
            with open(file_path+f"/execution_script_for_each_container_{sc_index}.py", "w") as f:
                f.write(sc)

    def save_array_to_csv(self, array, column_names:list = None, sample_numbers: bool = False, file_path: str = '.', verbose: bool = False):
        """
        Save a NumPy array to a CSV file with specified column names and sample numbers.
        
        Parameters:
        array (np.ndarray): The data array to save.
        column_names (list of str, optional): The names of the columns. If None, no column names are written. Defaults to None.
        sample_numbers (bool, optional): If True, sample numbers (row indices) are included as the first column. Defaults to False.
        file_path (str, optional): The directory path to save the CSV file. Defaults to '.'.
        verbose (bool, optional): If True, prints additional information. Defaults to False.
        """
        # Ensure array is 2D
        if array.ndim == 1:
            array = array.reshape(1, -1)

        # Ensure column_names is a list if it is a NumPy array
        if isinstance(column_names, np.ndarray):
            column_names = column_names.tolist()

        # Create the full file path
        full_file_path = os.path.join(file_path, 'sage_data_array.csv')
        
        # Open the file in write mode
        with open(full_file_path, mode='w') as file:
            # Write the header if column names are provided
            if column_names:
                if sample_numbers:
                    header = 'Sample,' + ','.join(column_names) + '\n'
                else:
                    header = ','.join(column_names) + '\n'
                file.write(header)
            
            # Write the data rows
            for i, row in enumerate(array):
                row_str = ','.join(map(str, row))
                if sample_numbers:
                    file.write(f"{i},{row_str}\n")
                else:
                    file.write(f"{row_str}\n")
        
        if verbose:
            print(f"Array saved to {full_file_path}")
