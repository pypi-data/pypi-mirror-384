try:
    from ...IO.structure_handling_tools.AtomPosition import AtomPosition
    from ...miscellaneous.marching_cubes import generate_offset_mesh
    from .BasePartition import BasePartition
except ImportError as e:
    import sys
    sys.stderr.write(f"An error occurred while importing AtomPosition: {str(e)}\n")
    del sys
    
try:
    import numpy as np
    import copy
    from tqdm import tqdm
except ImportError as e:
    import sys
    sys.stderr.write(f"An error occurred while importing numpy: {str(e)}\n")
    del sys

class MoleculeCluster_builder(BasePartition):
    """
    Utility to build, augment, and manipulate molecular clusters inside containers.

    Features
    --------
    - Compute cluster volumes for placement regions (box/sphere).
    - Determine solvent molecule counts from target density.
    - Add single molecules or bulk solvent using collision-avoidant random packing.
    - Add adsorbates on an offset surface mesh around anchor atoms.
    - *NEW*: Move existing atoms (by species or set) to bound/anchor sites
      at a target bond length while enforcing global collision tolerances.
    - Orchestrate the above via `handleCLUSTER` operations:
        • 'ADD_SOLVENT'
        • 'ADD_ADSOBATE'   (legacy misspelling retained)
        • 'MOVE_TO_BOUND'  (new)

    Notes
    -----
    - This class assumes `container.AtomPositionManager` exposes:
        atomLabelsList, atomPositions, latticeVectors,
        add_atom(...), count_neighbors(...), get_cell(), pack_to_unit_cell(),
        get_vacuum_box(...), and (optionally) a KD-tree with .kdtree and helpers.
    - For molecule templates, `AtomPosition` is expected to provide:
        .build(symbol), .mass, .atomLabelsList, .atomPositions,
        .generate_random_rotation_matrix(), .generate_uniform_translation_from_fractional(...),
        .set_atomPositions(...).

    Examples
    --------
    - Create a MoleculeCluster_builder instance
    cluster_builder = MoleculeCluster_builder(name="WaterCluster", file_location="/path/to/cluster")

    - Add a molecule template
    cluster_builder.add_molecule_template(name="H2O", atoms=water_atoms)

    - Add molecules to the cluster
    cluster_builder.add_molecule(container, water_molecule, shape='box')
    """

    # --------------------------------------------------------------------- #
    # Construction / State
    # --------------------------------------------------------------------- #
    def __init__(self, *args, **kwargs):
        """
        Constructor method for initializing the MoleculeCluster_builder instance.
        """
        self._molecule_template = {}
        self._density = None
        self._cluster_lattice_vectors = None

        super().__init__(*args, **kwargs)

    # --------------------------------------------------------------------- #
    # Basic geometry helpers
    # --------------------------------------------------------------------- #
    @staticmethod
    def is_point_inside_unit_cell(unit_cell: np.ndarray, point: np.ndarray) -> bool:
        """
        Check if a Cartesian point lies inside a unit cell defined by row-wise lattice vectors.

        Parameters
        ----------
        unit_cell : (3,3) ndarray
            Lattice vectors as rows.
        point : (3,) ndarray
            Cartesian coordinates.

        Returns
        -------
        bool
        """
        # Compute the fractional coordinates of the point relative to the unit cell
        # by solving the linear system: unit_cell * fractional = point
        # Solve unit_cell * frac = point  -> frac in [0,1)

        fractional_coords = np.linalg.solve(unit_cell, point)
        # Check if all fractional coordinates are in the interval [0, 1)
        return np.all(fractional_coords >= 0.0) and np.all(fractional_coords < 1.0)

    @staticmethod
    def generate_points_in_sphere(radius: float, num_points: int,
                                  distribution: str = 'uniform') -> np.ndarray:
        """
        Random points inside a sphere of given radius.

        Parameters
        ----------
        radius : float
            Sphere radius in Å.
        num_points : int
            Number of points to sample.
        distribution : {'uniform','center'}
            'uniform': uniform in volume (r ∝ u^(1/3)).
            'center' : all points at r = radius (useful for shells).

        Returns
        -------
        (num_points, 3) ndarray
        """
        points = np.zeros((num_points, 3), dtype=np.float64)
        for i in range(num_points):
            # Generate a random point in spherical coordinates
            phi = np.random.uniform(0.0, 2.0 * np.pi)  # azimuthal angle
            costheta = np.random.uniform(-1.0, 1.0)  # cosine of polar angle
            theta = np.arccos(costheta)  # polar angle

            if distribution == 'uniform':
                u = np.random.uniform(0.0, 1.0)  # random number for radius
                r = radius * (u ** (1.0/3.0))  # cubic root to ensure uniform distribution
            elif distribution == 'center':
                r = radius   # cubic root to ensure center distribution
            else:
                raise ValueError("distribution must be 'uniform' or 'center'")

            # Convert spherical coordinates to Cartesian coordinates
            s = np.sin(theta)
            points[i, 0] = r * s * np.cos(phi)
            points[i, 1] = r * s * np.sin(phi)
            points[i, 2] = r * np.cos(theta)

        return points

    # --------------------------------------------------------------------- #
    # Volume / counts
    # --------------------------------------------------------------------- #
    def get_cluster_volume(self, shape: str = 'box',
                           cluster_lattice_vectors: np.ndarray | None = None) -> float:
        """
        Compute the region volume used for placement.

        Parameters
        ----------
        shape : {'box','sphere'}
            'box'    : volume = |det(lattice_vectors)| (Å^3) -> cm^3
            'sphere' : volume = (4/3)π R^3 (R = cluster_lattice_vectors[0])
        cluster_lattice_vectors : ndarray | None
            If None, uses self.cluster_lattice_vectors.

        Returns
        -------
        float
            Volume in cm^3.

        Notes
        -----
        1 Å = 1e-8 cm  ->  Å^3 to cm^3 = 1e-24.
        """
        clv = cluster_lattice_vectors if cluster_lattice_vectors is not None else self.cluster_lattice_vectors
        if clv is None:
            raise ValueError("cluster_lattice_vectors is required")
            
        if shape.lower() == 'box':
            return float(abs(np.linalg.det(clv))) * 1.0e-24
        if shape.lower() == 'sphere':
            R = float(clv[0])
            return (4.0 / 3.0) * np.pi * (R ** 3) * 1.0e-24

        raise ValueError(f"Undefined shape '{shape}'. Expected 'box' or 'sphere'.")


    def get_molecules_number_for_target_density(self,
                                                density: float = 1.0,
                                                cluster_volume: float | None = None,
                                                molecules: dict[str, float] = None) -> dict[str, int]:
        """
        Translate target density to integer counts per molecule type.

        Parameters
        ----------
        density : float
            Target mass density (g/cm^3).
        cluster_volume : float | None
            Region volume in cm^3. If None, computed from builder state.
        molecules : dict[str, float]
            Molecule name -> fraction (sums to 1).

        Returns
        -------
        dict[str,int]
            Molecule name -> count.

        Notes
        -----
        Uses: N_total = (density * NA * volume) / (Σ_i fraction_i * mass_i)
        """
        if molecules is None:
            molecules = {'H2O': 1.0}
        if cluster_volume is None:
            cluster_volume = self.get_cluster_volume(shape='box', cluster_lattice_vectors=self.cluster_lattice_vectors)

        # Mass of mixture (weighted by fractions)
        mass_mix = 0.0
        for m_name, frac in molecules.items():
            if m_name not in self._molecule_template:
                raise KeyError(f"Molecule template '{m_name}' not present. Call add_molecule_template(...) first.")
            mass_mix += self._molecule_template[m_name].mass * float(frac)

        factor = density * self.NA * float(cluster_volume) / mass_mix
        return {m_name: int(np.round(factor * float(frac))) for m_name, frac in molecules.items()}

    # --------------------------------------------------------------------- #
    # Templates
    # --------------------------------------------------------------------- #
    def add_molecule_template(self, name: str, atoms: AtomPosition) -> bool:
        """
        Register a molecule template for later use.

        Parameters
        ----------
        name : str
            Template name (e.g., 'H2O').
        atoms : AtomPosition
            Prepared AtomPosition containing labels, positions, mass, etc.

        Returns
        -------
        bool
        """
        self._molecule_template[name] = atoms
        return True

    def _random_rotations(self, rng: np.random.RandomState, batch: int) -> np.ndarray:
        """
        Generate `batch` random rotation matrices using unit quaternions (Marsaglia).
        Returns
        -------
        (batch, 3, 3) ndarray
        """
        u1 = rng.rand(batch)
        u2 = rng.rand(batch) * 2.0 * np.pi
        u3 = rng.rand(batch) * 2.0 * np.pi
        s1 = np.sqrt(1.0 - u1)
        s2 = np.sqrt(u1)
        # quaternion (w, x, y, z)
        w = np.cos(u2) * s1
        x = np.sin(u2) * s1
        y = np.cos(u3) * s2
        z = np.sin(u3) * s2

        R = np.empty((batch, 3, 3), dtype=np.float64)
        R[:, 0, 0] = 1 - 2*(y*y + z*z)
        R[:, 0, 1] = 2*(x*y - z*w)
        R[:, 0, 2] = 2*(x*z + y*w)
        R[:, 1, 0] = 2*(x*y + z*w)
        R[:, 1, 1] = 1 - 2*(x*x + z*z)
        R[:, 1, 2] = 2*(y*z - x*w)
        R[:, 2, 0] = 2*(x*z - y*w)
        R[:, 2, 1] = 2*(y*z + x*w)
        R[:, 2, 2] = 1 - 2*(x*x + y*y)
        return R

    def _fibonacci_directions(self, m: int, slab: bool = False) -> np.ndarray:
        """
        Evenly distributed unit vectors on the sphere using a spherical Fibonacci grid.
        If slab=True, keep only +z hemisphere (guaranteeing at least one vector).
        """
        m = max(1, int(m))
        i = np.arange(m, dtype=np.float64) + 0.5
        phi = (1.0 + 5.0**0.5) / 2.0  # golden ratio
        theta = (2.0 * np.pi) * ((i / phi) % 1.0)
        z = 1.0 - 2.0 * i / m
        r = np.sqrt(np.maximum(0.0, 1.0 - z*z))
        dirs = np.stack([r*np.cos(theta), r*np.sin(theta), z], axis=1)
        if slab:
            dirs = dirs[dirs[:, 2] >= 0.0]
            if dirs.size == 0:
                dirs = np.array([[0.0, 0.0, 1.0]], dtype=np.float64)
        # normalize for safety
        dirs /= (np.linalg.norm(dirs, axis=1, keepdims=True) + 1e-15)
        return dirs


    def _poisson_disk_thin(self,
                           verts: np.ndarray,
                           min_sep: float,
                           cell_size: float | None = None,
                           rng_seed: int | None = None) -> np.ndarray:
        """
        Poisson-disk thinning via 3D grid-hash. Returns a subset of `verts`
        such that all pairwise distances are >= min_sep.

        Parameters
        ----------
        verts : (N,3) array
            Candidate points.
        min_sep : float
            Minimum allowed separation between retained points.
        cell_size : float | None
            Grid cell size. Default is min_sep / sqrt(3), which ensures that
            neighbors closer than min_sep must lie in the current or adjacent cells.
        rng_seed : int | None
            Optional seed to randomize sampling order (useful when verts have structure).

        Returns
        -------
        (M,3) array
            Thinned vertex set.
        """
        verts = np.asarray(verts, dtype=np.float64)
        N = len(verts)
        if N == 0 or min_sep <= 0.0:
            return verts

        rng = np.random.RandomState(rng_seed)
        order = rng.permutation(N)

        cs = float(cell_size) if cell_size is not None else (min_sep / np.sqrt(3.0))
        inv = 1.0 / cs

        # Grid: tuple(i,j,k) -> list of accepted indices that live in this cell
        grid: dict[tuple[int, int, int], list[int]] = {}
        accepted_idx: list[int] = []

        # Neighbor offsets (3x3x3 Moore neighborhood)
        offs = [(dx, dy, dz) for dx in (-1, 0, 1)
                           for dy in (-1, 0, 1)
                           for dz in (-1, 0, 1)]

        r2_min = min_sep * min_sep

        for idx in order:
            p = verts[idx]
            key = tuple(np.floor(p * inv).astype(int))
            ok = True
            for dx, dy, dz in offs:
                nb_key = (key[0] + dx, key[1] + dy, key[2] + dz)
                cell = grid.get(nb_key)
                if not cell:
                    continue
                # Check against all points accepted in neighbor cell(s)
                q = verts[cell]  # shape (K, 3)
                d2 = np.einsum('ij,ij->i', q - p, q - p)
                if np.any(d2 < r2_min):
                    ok = False
                    break
            if ok:
                accepted_idx.append(idx)
                grid.setdefault(key, []).append(idx)

        return verts[np.asarray(accepted_idx, dtype=int)]


    # --------------------------------------------------------------------- #
    # Placement core
    # --------------------------------------------------------------------- #
    def add_molecule(self,
                     container,
                     molecule: AtomPosition,
                     shape: str = 'box',
                     cluster_lattice_vectors: np.ndarray = np.array([[10.0, 0.0, 0.0],
                                                                     [0.0, 10.0, 0.0],
                                                                     [0.0, 0.0, 10.0]], dtype=np.float64),
                     translation: np.ndarray | None = None,
                     distribution: str = 'random',
                     surface: np.ndarray | None = None,
                     tolerance: float = 1.6,
                     max_iteration: int = 6000,
                     batch: int = 64,
                     rng_seed: int | None = None,
                     probability: np.ndarray | None = None) -> bool:
        """
        Attempt to place a single molecule without collisions.

        Parameters
        ----------
        container : object
            Target container with AtomPositionManager.
        molecule : AtomPosition
            Molecule to insert.
        shape : {'box','sphere','surface'}
            Sampling region. 'surface' expects surface points (verts).
        cluster_lattice_vectors : ndarray
            Placement lattice (box) or [R] (sphere).
        translation : (3,) ndarray | None
            Rigid shift of placement region origin.
        distribution : {'random','center'}
            'center' only applies to 'sphere' (shell placement).
        surface : (K,3) ndarray | None
            Discrete surface points (for 'surface').
        tolerance : float
            Min interatomic distance to existing structure.
        max_iteration : int
            Max random trials.
        probability : (K,) ndarray | None
            Optional sampling weights over surface points.

        Returns
        -------
        bool
            True if placed successfully, False otherwise.
        """
        rng = np.random.RandomState(rng_seed)
        apm = container.AtomPositionManager

        translation = np.array(translation if translation is not None else [0,0,0], dtype=np.float64)
        # Pre-center molecule around its COM
        mol_pos0 = np.asarray(molecule.atomPositions, dtype=np.float64)
        mol_com  = mol_pos0.mean(axis=0)
        mol_rel  = mol_pos0 - mol_com                      # (n,3)
        r_max    = np.sqrt((mol_rel**2).sum(axis=1)).max() # molecule bounding radius

        def _sample_displacements(n: int) -> np.ndarray:
            if shape.lower() == 'box':
                # Uniform in cell spanned by cluster_lattice_vectors
                U = rng.rand(n, 3)
                disp = (cluster_lattice_vectors.T @ U.T).T + translation
                return disp
            if shape.lower() == 'sphere':
                R = float(cluster_lattice_vectors[0])
                # uniform-in-volume sphere sampling
                phi = rng.uniform(0, 2*np.pi, size=n)
                cost = rng.uniform(-1, 1, size=n)
                theta = np.arccos(cost)
                u = rng.uniform(0, 1, size=n)
                r = R * (u ** (1/3))
                s = np.sin(theta)
                return np.stack([r*s*np.cos(phi), r*s*np.sin(phi), r*np.cos(theta)], axis=1) + translation
            if shape.lower() == 'surface':
                if surface is None or len(surface) == 0:
                    raise ValueError("For shape='surface' you must provide `surface`.")
                if probability is not None:
                    idx = rng.choice(surface.shape[0], size=n, p=probability)
                else:
                    idx = rng.randint(0, surface.shape[0], size=n)
                return surface[idx] + translation
            raise ValueError(f"Unknown shape '{shape}'.")

        tries = 0
        while tries < max_iteration:
            B = min(batch, max_iteration - tries)
            tries += B

            disps = _sample_displacements(B)              # (B,3)
            Rmats = self._random_rotations(rng, B)        # (B,3,3)

            # Coarse KD check on COM: if no neighbors within tol+r_max, auto-accept
            coarse_r = tolerance + r_max
            # Query KD-tree in a Python loop (B times) but far cheaper than per-atom checks
            coarse_hits = apm.kdtree.query_ball_point(disps, r=coarse_r, p=2.0, eps=0.0)

            for b in range(B):
                if len(coarse_hits[b]) == 0:
                    # Accept immediately
                    cand_pos = (mol_rel @ Rmats[b].T) + disps[b]  # (n,3)
                    apm.add_atom(molecule.atomLabelsList, cand_pos, getattr(molecule, "atomicConstraints", None))
                    return True

                # Detailed check only if something is nearby
                cand_pos = (mol_rel @ Rmats[b].T) + disps[b]      # (n,3)
                # Per-atom neighbor queries; quick exit on first collision
                collided = False
                for pa in cand_pos:
                    nb = apm.kdtree.query_ball_point(pa[None, :], r=tolerance, p=2.0, eps=0.0)[0]
                    if len(nb) > 0:
                        collided = True
                        break
                if not collided:
                    apm.add_atom(molecule.atomLabelsList, cand_pos, getattr(molecule, "atomicConstraints", None))
                    return True

        return False

    def add_solvent(self,
                    container,
                    shape: str = 'box',
                    cluster_lattice_vectors: np.ndarray = np.array([[10.0, 0.0, 0.0],
                                                                    [0.0, 10.0, 0.0],
                                                                    [0.0, 0.0, 10.0]], dtype=np.float64),
                    translation: np.ndarray = np.array([0.0, 0.0, 0.0], dtype=np.float64),
                    distribution: str = 'random',
                    tolerance: float = 1.6,
                    molecules: dict[str, float] = None,
                    density: float = 1.0,
                    max_iteration: int = 60000,
                    molecules_number: dict[str, int] | None = None,
                    verbosity: bool = False) -> bool:
        """
        Pack solvent molecules into a region until counts are satisfied.

        Parameters
        ----------
        container : object
            Target container.
        shape : {'box','sphere'}
        cluster_lattice_vectors : ndarray
        translation : (3,) ndarray
        distribution : {'random','center'}
        tolerance : float
        molecules : dict[str,float]
            Molecule fractions (default: {'H2O': 1.0}).
        density : float
            Target density if molecules_number not provided.
        max_iteration : int
            Global cap for individual molecule attempts.
        molecules_number : dict[str,int] | None
            Explicit counts per molecule. Overrides 'density' if given.
        verbosity : bool

        Returns
        -------
        bool
        """
        max_iteration = max_iteration if isinstance(max_iteration, int) else 100000
        molecules = molecules or {'H2O': 1.0}
        cluster_volume = self.get_cluster_volume(shape=shape, cluster_lattice_vectors=cluster_lattice_vectors)

        if isinstance(molecules_number, dict):
            counts = molecules_number
        else:
            counts = self.get_molecules_number_for_target_density(density=density,
                                                                  cluster_volume=cluster_volume,
                                                                  molecules=molecules)

        for m_name, m_count in counts.items():
            iterable = range(m_count)
            if verbosity:
                iterable = tqdm(iterable, desc=f"Adding {m_name} into empty space")

            # Ensure template present
            if m_name not in self._molecule_template:
                mol = AtomPosition()
                mol.build(m_name)
                self.add_molecule_template(m_name, mol)

            for _ in iterable:
                ok = self.add_molecule(container=container,
                                       molecule=self._molecule_template[m_name],
                                       translation=translation,
                                       tolerance=tolerance,
                                       shape=shape,
                                       cluster_lattice_vectors=cluster_lattice_vectors,
                                       distribution=distribution,
                                       max_iteration=max_iteration)
                if not ok:
                    if verbosity:
                        print("[MoleculeCluster_builder] Could not complete solvent packing. Try lower density or higher tolerance.")
                    return False

        self.molecules_number = counts
        return True

    # NOTE: Public name kept as in your original code for compatibility.
    def add_adsobate(self,
                     container,
                     shape: str = 'surface',
                     translation: np.ndarray = np.array([0.0, 0.0, 0.0], dtype=np.float64),
                     distribution: str = 'random',
                     tolerance: float = 1.6,
                     surface: np.ndarray | None = None,
                     molecules: dict[str, float] = None,
                     density: float = 1.0,
                     max_iteration: int = 60000,
                     molecules_number: dict[str, int] | None = None,
                     verbosity: bool = True,
                    probability: np.ndarray | None = None) -> bool:
        """
        Add "adsorbate" molecules onto a surface (discrete 'surface' points).

        Parameters
        ----------
        container : object
        shape : 'surface' (fixed)
        translation : (3,) ndarray
        distribution : 'random'
        tolerance : float
        surface : (K,3) ndarray
            Set of candidate surface positions (e.g., offset mesh vertices).
        molecules : dict[str,float]
            Fractions; used only when 'molecules_number' omitted (scaled relatively).
        density : float
            Unused placeholder for parity with `add_solvent`.
        max_iteration : int
        molecules_number : dict[str,int] | None
            Explicit counts per molecule. If None, derived from `molecules` fractions.
        verbosity : bool

        Returns
        -------
        bool
        """
        max_iteration = max_iteration if isinstance(max_iteration, int) else 60000
        molecules = molecules or {'H2O': 1.0}

        # Convert fractional recipe to relative integer counts if numbers not provided
        if isinstance(molecules_number, dict):
            counts = molecules_number
        else:
            # Relative scaling: normalize by smallest fraction
            vals = list(molecules.values())
            if len(vals) == 0:
                return True
            min_val = min(vals)
            counts = {k: int(abs(v / min_val)) for k, v in molecules.items()}

        for m_name, m_count in counts.items():
            iterable = range(m_count)
            if verbosity:
                iterable = tqdm(iterable, desc=f"Adding {m_name} to surface")

            if m_name not in self._molecule_template:
                mol = AtomPosition()
                mol.build(m_name)
                self.add_molecule_template(m_name, mol)

            for _ in iterable:
                ok = self.add_molecule(
                    container=container,
                   molecule=self._molecule_template[m_name],
                   translation=translation,
                   tolerance=tolerance,
                   surface=surface,
                   shape=shape,
                   distribution=distribution,
                   max_iteration=max_iteration,
                   probability=probability
                )
                if not ok:
                    if verbosity:
                        print("[MoleculeCluster_builder] Surface packing failed. Consider reducing counts.")
                    return False

        self.molecules_number = counts
        return True

    def add_adsorbate(self, *args, **kwargs):
        """Alias of `add_adsobate` (legacy public name kept)."""
        return self.add_adsobate(*args, **kwargs)

    # --------------------------------------------------------------------- #
    # Orchestration
    # --------------------------------------------------------------------- #
    def handleCLUSTER(self, values:dict, containers:list=None):
        """
        High-level dispatcher for cluster operations.

        Supported keys (case-insensitive)
        ---------------------------------
        - 'ADD_SOLVENT':
            {
              'solvent': ['H2O', 'MeOH', ...],
              'density': float,
              'collision_tolerance': float,
              'shape': 'BOX'|'SPHERE'|'PARALLELEPIPED'|'CELL'  (or slab mode)
              'size': [..]  (depends on shape),
              'translation': [x,y,z],
              'distribution': 'random'|'center',
              'wrap': bool,
              'slab': bool,
              'vacuum_tolerance': float,   # when slab=True
              'molecules_number': dict|list|None,
              'max_iteration': int|None,
              'seed': int|float|None,
              'verbose': bool
            }

        - 'ADD_ADSOBATE' (legacy spelling; kept for compatibility):
            {
              'adsobate': ['H2O', ...],
              'ID': list[int|str],             # anchors to build offset surface
              'd': float,                      # offset distance
              'resolution': int,
              'padding': float,
              'collision_tolerance': float,
              'molecules_number': dict|list|None,
              'translation': [x,y,z],
              'distribution': 'random',
              'density': float (unused),
              'slab': bool,
              'verbosity': bool,
              'prioritize_connectivity': bool, # weight surface verts by local density
              'wrap': bool,
              'max_iteration': int|None,
              'seed': int|float|None,
              'verbose': bool
            }

        - 'MOVE_TO_BOUND' (new):
            {
              'species': str|list[str],
              'ID': list[int|str],             # anchors (indices and/or labels)
              'bond_length': float,
              'collision_tolerance': float,
              'moves': int|list|dict,
              'slab': bool,
              'wrap': bool,
              'max_iteration': int|None,
              'constraints': list|None,        # callables (idx, container)->bool
              'seed': int|float|None,
              'verbose': bool
            }

        Parameters
        ----------
        values : dict
            Operation -> config dict.
        containers : list | None
            Containers to process. Defaults to self.containers.

        Returns
        -------
        list | bool
            New containers list, or False on failure.
        """
        containers_new = []
        containers = containers if isinstance(containers, list) else self.containers

        for container_index, container in enumerate(containers):
            for v_key, v_item in values.items():
                # Normalize float seeds coming from some YAML/JSON sources
                if 'seed' in v_item and isinstance(v_item['seed'], float): 
                    np.random.seed(int(v_item['seed'])) 

                # ---------------------------------------------------------- #
                # ADD_SOLVENT
                # ---------------------------------------------------------- #
                if v_key.upper() == 'ADD_SOLVENT':
                    # Copy and update container for each set of k-point values
                    container_copy = self.copy_and_update_container(container, f'/solvent/', '')
                    
                    # Ensure templates exist
                    for s in v_item['solvent']:
                        molecule = AtomPosition()
                        molecule.build(s)
                        self.add_molecule_template(s, molecule)
                    molecules= {s:1 for s in v_item['solvent']}

                    # Region selection
                    if 'slab' in v_item and v_item['slab']:
                        vacuum_box, vacuum_start = container_copy.AtomPositionManager.get_vacuum_box(tolerance=v_item['vacuum_tolerance']) 
                        shape = 'box'
                        distribution = 'random'
                    else:
                        shape = v_item['shape']
                        if shape.upper() == 'BOX':
                            shape = 'box'
                            vacuum_box, vacuum_start = np.array([[v_item['size'][0],0,0],[0,v_item['size'][1],0],[0,0,v_item['size'][2]]], dtype=np.float64), v_item['translation']
                        elif shape.upper() == 'SPHERE':
                            shape = 'sphere'
                            vacuum_box, vacuum_start = [float(v_item['size'][0])], v_item['translation']
                        elif shape.upper() == 'PARALLELEPIPED':
                            shape = 'box'
                            if len(v_item['size'].shape) > 1:
                                v_item['size'] = v_item['size'].flatten()
                            vacuum_box, vacuum_start = np.array([
                                                            [v_item['size'][0],v_item['size'][1],v_item['size'][2]],
                                                            [v_item['size'][3],v_item['size'][4],v_item['size'][5]],
                                                            [v_item['size'][6],v_item['size'][7],v_item['size'][8]]], 
                                                        dtype=np.float64), v_item['translation']
                        elif shape.upper() == 'CELL':
                            shape = 'box'
                            vacuum_box, vacuum_start = np.array(container_copy.AtomPositionManager.get_cell() ,dtype=np.float64), np.array([0,0,0] ,dtype=np.float64)

                        distribution = v_item.get('distribution', 'random')

                    tolerance = v_item['collision_tolerance']
                    density = v_item['density']

                    molecules_number = v_item.get('molecules_number')
                    # If 'molecules_number' is a list, convert it into a dictionary using 'solvent' as keys
                    if isinstance(molecules_number, (list, np.ndarray)):
                        molecules_number = {solvent: int(mn) for solvent, mn in zip(v_item['solvent'], molecules_number)}
                    # If 'molecules_number' is neither a list nor a dict, set it to None
                    elif not isinstance(molecules_number, dict):
                        molecules_number = None

                    max_iteration = v_item.get('max_iteration', None)
                    ok = self.add_solvent(container=container_copy,
                                          shape=shape,
                                          cluster_lattice_vectors=vacuum_box,
                                          translation=vacuum_start,
                                          distribution=distribution,
                                          density=density,
                                          tolerance=tolerance,
                                          molecules=molecules,
                                          molecules_number=molecules_number,
                                          max_iteration=max_iteration)
                    
                    if not ok:
                        return False

                    if v_item.get('verbose', False):
                        print("[MoleculeCluster_builder] Solvent added.")

                    if v_item['wrap']:
                        container_copy.AtomPositionManager.pack_to_unit_cell()

                    containers_new.append(container_copy)
                
                # ---------------------------------------------------------- #
                # ADD_ADSOBATE (legacy name preserved)
                # ---------------------------------------------------------- #
                if v_key.upper() == 'ADD_ADSOBATE':
                    container_copy = self.copy_and_update_container(container, f'/adsobate/', '')
                    shape = 'surface'

                    # Ensure templates
                    for s in v_item['adsobate']:
                        molecule = AtomPosition()
                        molecule.build(s)
                        self.add_molecule_template(s, molecule)
                    molecules= {s:1 for s in v_item['adsobate']}

                    # Build anchor list from IDs (indices or labels)
                    d = v_item['d']
                    resolution = v_item['resolution']
                    padding = v_item['padding']

                    # Retrieve the list of IDs from v_item
                    ID_label_list = v_item['ID']

                    # Convert elements that are int or float to integers
                    ID_number = [int(x) for x in ID_label_list if isinstance(x, (int, float))]

                    # Append indices from container.AtomPositionManager.atomLabelsList where the label is present in ID_label_list
                    ID_number.extend(
                        i for i, label in enumerate(container.AtomPositionManager.atomLabelsList)
                        if label in ID_label_list
                    )

                    positions = np.atleast_2d(container.AtomPositionManager.atomPositions[ID_number])
                    verts, faces = generate_offset_mesh(positions, d, resolution=resolution, padding=padding)
                    if len(verts) == 0:
                        verts = self.generate_points_in_sphere(radius=d, num_points=resolution**2, distribution='center') + positions[0]

                    tolerance = v_item['collision_tolerance']
                    molecules_number = v_item.get('molecules_number')
                    translation = v_item.get('translation', [0,0,0])
                    distribution = v_item.get('distribution', 'random')
                    density = v_item.get('density', 1.0) # NOT IMPLEMENTED
                    slab = v_item.get('slab', False)
                    verbosity =  v_item.get('verbosity', False)
                    prioritize_connectivity = v_item.get('prioritize_connectivity', False)

                    # Slab: keep upper side by z
                    if slab:
                        z_mean = np.mean(container.AtomPositionManager.atomPositions, axis=0)[2]
                        z_mean = np.mean(verts, axis=0)[2]
                        mask = verts[:, 2] > z_mean

                        # Old-to-new index mapping
                        old_to_new = -np.ones(len(verts), dtype=int)
                        old_to_new[mask] = np.arange(mask.sum())

                        # Filter verts
                        verts = verts[mask]

                        # Keep only faces with all 3 vertices in the mask
                        faces_mask = np.all(mask[faces], axis=1)
                        faces = faces[faces_mask]

                        # Remap face indices to new verts
                        faces = old_to_new[faces]
                        
                    
                    #'''
                    #results = container.AtomPositionManager.kdtree.query_ball_point(verts, tolerance, p=2., eps=0)
                    #verts = np.array([x for x, r in zip(verts, results) if not r], dtype=np.float64)
                    #'''

                    # Optional vertex weighting by local connectivity
                    if prioritize_connectivity:
                        results = container.AtomPositionManager.kdtree.query_ball_point(verts, d+padding, p=2., eps=0)
                        verts_probability = np.array([len(r)*10 for r in results], dtype=np.float64)
                        verts_probability /= np.sum(verts_probability)

                    else:
                        verts_probability = np.ones(len(verts))

                    if v_item.get('verbose', False):
                        print(f' {len(verts)} vertices found')

                    '''    
                    print(f' {len(verts)} vertices found')
                    # DEBBUG #
                    import matplotlib.pyplot as plt
                    fig2 = plt.figure()
                    ax2 = fig2.add_subplot(projection='3d')
                    ax2.plot_trisurf(verts[:, 0], verts[:, 1], faces, verts[:, 2], linewidth=0.2, antialiased=True)
                    ax2.set_title(f"Offset Surface at d={d}")
                    ax2.set_xlabel("X")
                    ax2.set_ylabel("Y")
                    ax2.set_zlabel("Z")

                    plt.show()
                    '''

                    """
                    import matplotlib.pyplot as plt
                    vals_v = verts_probability

                    fig2 = plt.figure()
                    ax2 = fig2.add_subplot(projection='3d')

                    # Compute one color value per triangle by averaging its 3 vertices
                    vals_tri = vals_v[faces].mean(axis=1)

                    surf = ax2.plot_trisurf(
                        verts[:, 0], verts[:, 1], verts[:, 2],
                        triangles=faces,
                        linewidth=0.2, antialiased=True, shade=False, cmap='viridis'
                    )

                    # Attach the triangle-wise scalar array to the surface
                    surf.set_array(vals_tri)
                    surf.autoscale()  # rescale color limits to data
                    # ---- Equal aspect ratio ----
                    x_limits = [verts[:, 0].min(), verts[:, 0].max()]
                    y_limits = [verts[:, 1].min(), verts[:, 1].max()]
                    z_limits = [verts[:, 2].min(), verts[:, 2].max()]

                    x_range = x_limits[1] - x_limits[0]
                    y_range = y_limits[1] - y_limits[0]
                    z_range = z_limits[1] - z_limits[0]
                    max_range = max(x_range, y_range, z_range) / 2.0

                    mid_x = np.mean(x_limits)
                    mid_y = np.mean(y_limits)
                    mid_z = np.mean(z_limits)

                    ax2.set_xlim(mid_x - max_range, mid_x + max_range)
                    ax2.set_ylim(mid_y - max_range, mid_y + max_range)
                    ax2.set_zlim(mid_z - max_range, mid_z + max_range)

                    ax2.set_title(f"Offset Surface at d={d}")
                    ax2.set_xlabel("X"); ax2.set_ylabel("Y"); ax2.set_zlabel("Z")
                    fig2.colorbar(surf, ax=ax2, shrink=0.65, pad=0.1, label="Value")
                    plt.show()
                    """

                    # If 'molecules_number' is a list, convert it into a dictionary using 'solvent' as keys
                    if isinstance(molecules_number, (list, np.ndarray)):
                        molecules_number = {solvent: int(mn) for solvent, mn in zip(v_item['adsobate'], molecules_number)}
                    # If 'molecules_number' is neither a list nor a dict, set it to None
                    elif not isinstance(molecules_number, dict):
                        molecules_number = None
    
                    max_iteration = v_item.get('max_iteration', None)

                    ok = self.add_adsobate(
                        container=container_copy,
                        shape=shape,
                        surface=verts,
                        translation=translation,
                        distribution=distribution,
                        density=density,
                        tolerance=tolerance,
                        molecules=molecules,
                        molecules_number=molecules_number,
                        max_iteration=max_iteration,
                        verbosity=verbosity,
                        probability=verts_probability  
                    )
                    if not ok:
                        return False

                    if v_item.get('verbose', False):
                        print("[MoleculeCluster_builder] Adsorbate added.")

                    if v_item['wrap']:
                        container_copy.AtomPositionManager.pack_to_unit_cell()

                    containers_new.append(container_copy)

        self.set_container(containers_new)
        return containers_new


