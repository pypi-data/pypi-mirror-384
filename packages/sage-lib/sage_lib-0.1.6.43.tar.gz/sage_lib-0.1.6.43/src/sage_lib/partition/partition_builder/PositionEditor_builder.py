try:
    import numpy as np
    from tqdm import tqdm
    import copy
    from typing import List, Dict, Tuple

    from .BasePartition import BasePartition
except ImportError as e:
    import sys
    sys.stderr.write(f"An error occurred while importing numpy: {str(e)}\n")
    del sys

class PositionEditor_builder(BasePartition):
    """
    A class for managing and editing atomic positions in various ways, inheriting from PartitionManager.

    Methods
    -------
    handle_rattle(values, file_location=None)
        Applies a random displacement to atomic positions.

    handle_compress(container, values, container_index, file_location=None)
        Compresses a given container along a defined direction.

    handle_widening(values, file_location=None)
        Stacks atoms from different containers to widen atomic layers.

    handle_interpolation(values, file_location=None)
        Interpolates between atomic positions using splines.

    handle_exfoliation(values, file_location=None)
        Separates atomic layers to simulate exfoliation.
    """
    def __init__(self, file_location: str = None, name: str = None, *args, **kwargs):
        """
        Initialize the PositionEditorBuilder instance.

        Parameters
        ----------
        file_location : str, optional
            The file location for the atomic data.
        name : str, optional
            The name for this instance.
        """
        super().__init__(*args, **kwargs)

    def handle_rattle(self, values, file_location=None):
        """
        Applies random displacements to atom positions within containers to simulate atomic 'rattling'.
        
        Parameters
        ----------
        values : dict
            Contains parameters for the rattling process (e.g., standard deviation 'std', number of iterations 'N').
        file_location : str, optional
            Directory to store rattled configurations.

        Returns
        -------
        list
            A list of containers with rattled atom positions.
        """
        containers = []

        # Iterate through each container and apply random rattling 'N' times.
        for container_index, container in enumerate(self.containers):
            for n in range(values['N']):
                # Create a copy of the container and apply the random displacement.
                container_copy = self.copy_and_update_container(container, f'/rattle/{container_index}_{n}', file_location)
                container_copy.AtomPositionManager.rattle(stdev=values['std'], seed=n)

                containers.append(container_copy)
        
        # Update the current containers with the rattled containers.
        self.containers = containers

        return containers

    def handle_compress(self, values, file_location=None):
        """
        Compresses the atom positions within a container by applying different compression factors.
        
        Parameters
        ----------
        container : object
            The container whose atom positions will be compressed.
        values : dict
            Contains parameters like 'compress_min', 'compress_max', and 'N' for the compression range.
        container_index : int
            Index of the container.
        file_location : str, optional
            Directory to store compressed configurations.

        Returns
        -------
        list
            A list of containers with compressed atom positions.
        """
        sub_directories, containers = [], []

        # Create a vector of compression factors.
        compress_vector = self.interpolate_vectors(values['compress_min'], values['compress_max'], values['N'])

        # Iterate through each container and compress.
        for container_index, container in enumerate(tqdm(self.containers, desc="Processing Containers")):

            for v_i, v in enumerate(compress_vector):
                # Create a copy of the container and apply the compression factor.
                container_copy = self.copy_and_update_container(container, f'/compress/{v_i}', file_location)
                container_copy.AtomPositionManager.compress(compress_factor=v, verbose=False)
                    
                sub_directories.append(f'/{v_i}')
                containers.append(container_copy)

        return containers

    def handle_widening(self, values, file_location=None):
        """
        Stacks multiple atomic configurations to create wider layers of atoms.
        
        Parameters
        ----------
        values : list of dict
            Each dictionary contains indices and stacking direction information.
        file_location : str, optional
            Directory to store widened configurations.

        Returns
        -------
        list
            A list of containers with widened atomic layers.
        """
        sub_directories, containers = [], []

        # Iterate over the provided values to stack atomic configurations.
        for v_i, v in enumerate(values):
            container_init = self.containers[v['init_index']]
            container_mid = self.containers[v['mid_index']]
            container_end = self.containers[v['end_index']]
            
            # Create a copy of the initial container.
            container_copy = self.copy_and_update_container(container_init, f'/widening/{v_i}', file_location)

            # Stack the middle container 'N' times, then add the end container.
            for n in range(v['N']):
                container_copy.AtomPositionManager.stack(AtomPositionManager=container_mid.AtomPositionManager, direction=v['direction'])
            container_copy.AtomPositionManager.stack(AtomPositionManager=container_end.AtomPositionManager, direction=v['direction'])

            sub_directories.append(f'/{v_i}')
            containers.append(container_copy)
    
        return containers

    def handle_interpolation(self, values, file_location=None):
        """
        Interpolates atom positions between given configurations using spline interpolation.
        
        Parameters
        ----------
        values : dict
            Contains parameters for interpolation like 'images' and 'degree'.
        file_location : str, optional
            Directory to store interpolated configurations.

        Returns
        -------
        list
            A list of containers with interpolated atom positions.
        """
        interpolation_data = np.zeros((self.containers[0].AtomPositionManager.atomCount, 3, len(self.containers)), dtype=np.float64)

        # Collect atomic positions from each container.
        for container_index, container in enumerate(self.containers):
            if values.get('first_neighbor', False):
                container.AtomPositionManager.wrap()
            interpolation_data[:, :, container_index] = container.AtomPositionManager.atomPositions_fractional

        # Adjust positions for periodic boundaries if specified.
        if values.get('first_neighbor', False):
            diff = np.diff(interpolation_data, axis=2)
            interpolation_data[:, :, 1:][diff > 0.5] -= 1
            interpolation_data[:, :, 1:][diff < -0.5] += 1

        # Perform spline interpolation on the collected data. 
        new_interpolated_data = self.interpolate_with_splines(interpolation_data, M=values['images'], degree=values['degree'])

        containers = [self.copy_and_update_container(self.containers[0], f'/interpolation/init', file_location)]
        for container_index, container in enumerate(self.containers[1:]):
            for n in range(values['images'] + 1):
                container_copy = self.copy_and_update_container(container, f'/interpolation/{container_index}_{n}', file_location)
                container_copy.AtomPositionManager.set_atomPositions_fractional(new_interpolated_data[:, :, container_index * (values['images'] + 1) + n + 1])
                if values.get('first_neighbor', False):
                    container_copy.AtomPositionManager.wrap()
                containers.append(container_copy)

        apm_cr = containers[0].AtomPositionManager.covalent_radii
        pair_min_dist = {(ua1, ua2): (apm_cr[ua1]+apm_cr[ua2])*.9  for ua1 in self.uniqueAtomLabels for ua2 in self.uniqueAtomLabels }

        self._physics_relax_images(
            containers,
            first_neighbor=values.get('first_neighbor', False),
            # per-pair hard minima (optional)
            pair_min_dist=values.get('pair_min_dist', None ),
            # repulsive wall scale r0_ij = s_rep * (r_i + r_j) unless pair_min_dist overrides it
            s_rep=values.get('s_rep', 0.85),
            k_rep=values.get('k_rep', 100.0),     # eV/Å^2 (quadratic wall strength)
            k_tether=values.get('k_tether', 2.0), # eV/Å^2 (how tightly to follow the spline)
            max_steps=values.get('relax_steps', 60),
            step0=values.get('relax_step0', 0.10),# initial step in Å
            gtol=values.get('relax_gtol', 1e-2),  # max |grad| stop
            ls_shrink=values.get('ls_shrink', 0.5),
            ls_expand=values.get('ls_expand', 1.2)
        )

        self.set_container(containers)
        return containers

    def handle_exfoliation(self, values, file_location=None):
        """
        Simulates the exfoliation of atomic layers by separating them along a specified axis.
        
        Parameters
        ----------
        values : dict
            Contains parameters such as 'direction' and 'threshold' to determine layers.
        file_location : str, optional
            Directory to store exfoliated configurations.

        Returns
        -------
        list
            A list of containers with exfoliated atomic layers.
        """
        containers = []
        separation_distance = values.get('separation_distance', 20.0)   # Default separation distance between layers.
        layer_direction = values.get('direction', 'y') 
        layer_threshold = values.get('threshold', 2.0) 

        # Iterate through each container and separate layers.
        for container_index, container in enumerate(tqdm( copy.deepcopy(self.containers), desc="Processing Containers")):
            # Wrap atom positions within simulation boundaries to ensure all atoms are inside the box.
            container.AtomPositionManager.wrap()

            # Get indices of atoms in each layer based on the specified direction and threshold.
            layers_index_list = container.AtomPositionManager.get_layers(direction=layer_direction, 
                                                                         threshold=layer_threshold)
            
            # Create a deep copy of the original container to add solvent in the slab form.
            container_original = copy.deepcopy(container)
            
            container_original_water = self.handleCLUSTER(    values = {'ADD_SOLVENT':{
                                            'density': 1.01,
                                            'solvent': ['H2O'],
                                            'slab': True,
                                            'shape': None,
                                            'size': None,
                                            'vacuum_tolerance': 0,
                                            'colition_tolerance': 1.75,
                                            'translation': None,
                                            'wrap': True,
                                            'seed':0,
                                            'max_iteration':100000,
                                            'verbose':True
                                        }}, 
                                    containers=container_original)

            # Add the modified container with water to the list of results.
            containers += container_original_water

            # Iterate through possible separation points and generate configurations for exfoliated layers.
            for cut_index in range(1, len(layers_index_list)):
                # Create a deep copy of the container for each new configuration.
                container_copy = copy.deepcopy(container)

                # Move atoms in different directions to simulate the exfoliation process.
                for i, layer_indices in enumerate(layers_index_list):
                    if i > cut_index:
                        container_copy.AtomPositionManager.move_atom(layer_indices, [0, separation_distance / 2, 0])
                    #else:
                    #    container_copy.AtomPositionManager.move_atom(layer_indices, [0, -separation_distance / 2, 0])

                # Determine the vacuum box dimensions (used if further modification is needed).
                vacuum_box, vacuum_start = container.AtomPositionManager.get_vacuum_box(tolerance=0)
                
                # Add solvent to the exfoliated container using more customizable parameters.
                container_copy_water = self.handleCLUSTER(values={'ADD_SOLVENT': {
                                        'density': 1.0,
                                        'solvent': ['H2O'],
                                        'slab': False,
                                        'shape': 'CELL',
                                        'size': None,
                                        'vacuum_tolerance': 0,
                                        'colition_tolerance': 1.75,
                                        'molecules_number':self.molecules_number,
                                        'translation': None,
                                        'wrap': True,
                                        'seed':0,
                                        'max_iteration':100000,
                                        'verbose':True
                                    }}, 

                                containers=[container_copy])

                # Attempt to add the modified container with water to the list of results.
                try:
                    containers += container_copy_water
                except:
                    print('Warning: Could not add solvent to the container. Consider trying a lower density.')
                        
        return containers


    def _physics_relax_images(
        self,
        containers: List[object],
        *,
        first_neighbor: bool,
        pair_min_dist: Dict[Tuple[str, str], float],
        s_rep: float,
        k_rep: float,
        k_tether: float,
        max_steps: int,
        step0: float,
        gtol: float,
        ls_shrink: float,
        ls_expand: float,
    ) -> None:
        """Relax each interpolated image with a cheap repulsive + tether potential."""
        if not containers:
            return

        # Precompute covalent radii per-atom from the first container
        labels0 = containers[0].AtomPositionManager.atomLabelsList
        cov_rad = np.array([containers[0].AtomPositionManager.covalent_radii[el] for el in labels0], float)
        N = len(labels0)

        # Build reference fractional positions for each image (the current positions)
        refs_frac = [c.AtomPositionManager.atomPositions_fractional.copy() for c in containers]

        for idx, cont in enumerate(containers):
            # Relax every image except maybe the very first/last if you want to pin them
            # (comment out these lines if you want to relax all)
            # if idx == 0 or idx == len(containers)-1:
            #     continue
            x_ref_f = refs_frac[idx]
            self._physics_relax_one(
                cont, x_ref_f, labels0, cov_rad,
                first_neighbor=first_neighbor,
                pair_min_dist=pair_min_dist,
                s_rep=s_rep, k_rep=k_rep,
                k_tether=k_tether,
                max_steps=max_steps, step0=step0,
                gtol=gtol, ls_shrink=ls_shrink, ls_expand=ls_expand
            )


    def _physics_relax_one(
        self, container, x_ref_frac, labels, cov_rad,
        *, first_neighbor: bool,
        pair_min_dist: Dict[Tuple[str, str], float],
        s_rep: float, k_rep: float, k_tether: float,
        max_steps: int, step0: float, gtol: float,
        ls_shrink: float, ls_expand: float
    ) -> None:
        """Minimize E = Σ_{i<j} 0.5*k_rep*max(0, r0_ij - r_ij)^2 + 0.5*k_tether*Σ_i ||x_i - x_i^ref||^2."""
        # Work in Cartesian for gradients; keep fractional for wrapping/setting
        x_f = container.AtomPositionManager.atomPositions_fractional.copy()
        x = _frac_to_cartesian(container, x_f)           # (N,3)
        x_ref = _frac_to_cartesian(container, x_ref_frac)# (N,3)
        N = x.shape[0]

        def r0_ij(i, j):
            # explicit per-pair override in Å takes precedence
            if pair_min_dist:
                key = (labels[i], labels[j])
                keyr = (labels[j], labels[i])
                if key in pair_min_dist: return pair_min_dist[key]
                if keyr in pair_min_dist: return pair_min_dist[keyr]
            return s_rep * (cov_rad[i] + cov_rad[j])

        # simple backtracking line search gradient descent
        step = float(step0)

        for it in range(max_steps):
            E, g = _energy_and_grad_rep_tether(
                container, x, x_ref, labels, cov_rad,
                r0_ij_fn=r0_ij,
                k_rep=k_rep, k_tether=k_tether,
                first_neighbor=first_neighbor
            )
            gmax = float(np.abs(g).max())
            if gmax < gtol:
                break

            # trial step with backtracking
            desc_dir = -g
            ok = False
            for _ in range(20):
                x_trial = x + step * desc_dir
                # project to fractional, wrap if needed, then back to Cartesian (keeps PBC sane)
                x_trial_f = _cartesian_to_frac(container, x_trial)
                if first_neighbor:
                    x_trial_f = np.mod(x_trial_f, 1.0)
                x_trial = _frac_to_cartesian(container, x_trial_f)

                E_trial, _ = _energy_and_grad_rep_tether(
                    container, x_trial, x_ref, labels, cov_rad,
                    r0_ij_fn=r0_ij,
                    k_rep=k_rep, k_tether=k_tether,
                    first_neighbor=first_neighbor
                )
                if E_trial <= E:
                    x = x_trial
                    step *= ls_expand
                    ok = True
                    break
                step *= ls_shrink

            if not ok:
                # step became too small; stop
                break

        # Commit positions
        x_f_new = _cartesian_to_frac(container, x)
        container.AtomPositionManager.set_atomPositions_fractional(x_f_new)
        if first_neighbor:
            container.AtomPositionManager.wrap()


def _energy_and_grad_rep_tether(
    container, x, x_ref, labels, cov_rad,
    *, r0_ij_fn, k_rep: float, k_tether: float, first_neighbor: bool
):
    """Return (E, grad) for repulsive wall + path tether."""
    N = x.shape[0]
    g = np.zeros_like(x)
    E = 0.0

    # Pair repulsion: quadratic wall when r < r0_ij; 0 otherwise
    for i in range(N - 1):
        for j in range(i + 1, N):
            # minimum-image vector in fractional → Cartesian
            vij_f = _cartesian_to_frac(container, x[j:j+1] - x[i:i+1])[0]
            if first_neighbor:
                vij_f = _min_image_fractional(vij_f)
            rij_vec = _frac_to_cartesian(container, vij_f[None, :])[0]
            rij = float(np.linalg.norm(rij_vec))
            if rij < 1e-12:
                # avoid singular; small random axis
                n = np.array([1.0, 0.0, 0.0], float); rij = 1e-12
            else:
                n = rij_vec / rij

            r0 = float(r0_ij_fn(i, j))
            if rij < r0:
                overlap = (r0 - rij)
                E += 0.5 * k_rep * overlap * overlap
                dE_drij = -k_rep * overlap              # d/d r
                # grad contribution: dE/dx_i = dE/dr * dr/dx_i = dE/dr * (-n)
                gi = dE_drij * (-n)
                gj = dE_drij * (+n)
                g[i] += gi
                g[j] += gj

    # Path tether: harmonic to the interpolated geometry
    dx = x - x_ref
    E += 0.5 * k_tether * float(np.sum(dx * dx))
    g += k_tether * dx

    return E, g




def _min_image_fractional(dfrac: np.ndarray) -> np.ndarray:
    """Map fractional deltas to [-0.5, 0.5] per component."""
    out = dfrac.copy()
    out[out > 0.5] -= 1.0
    out[out < -0.5] += 1.0
    return out


def _build_identity_mapping(
    self,
    A,
    B,
    radii: np.ndarray,
    *,
    id_scale: float,
    first_neighbor: bool
) -> np.ndarray:
    """
    Greedy, radii-aware nearest-neighbour matching under PBC if requested.
    If no candidate satisfies the radii cutoff, assigns the nearest available neighbour.

    Returns
    -------
    np.ndarray
        mapping[i] = j  (indices into B)
    """
    N = len(radii)
    used = np.zeros(N, dtype=bool)
    mapping = -np.ones(N, dtype=int)

    # Precompute a distance matrix using your self.distance helper.
    # Adjust the call signature if your API differs.
    D = np.empty((N, N), dtype=float)
    for i in range(N):
        for j in range(N):
            # Expecting self.distance to respect PBC when first_neighbor is True.
            # If it needs fractional coords instead, adapt this call accordingly.
            D[i, j] = A.AtomPositionManager.distance(
                A.AtomPositionManager.atomPositions[i], 
                B.AtomPositionManager.atomPositions[j]
            )

    # For each i, preferred js sorted by distance
    pref = np.argsort(D, axis=1)

    # First pass: enforce covalent-radii identity (tight) when possible.
    cutoff = id_scale * (radii[:, None] + radii[None, :])  # shape (N, N)
    for i in range(N):
        assigned = False
        for j in pref[i]:
            if used[j]:
                continue
            if D[i, j] <= cutoff[i, j]:
                mapping[i] = j
                used[j] = True
                assigned = True
                break
        if not assigned:
            # Defer to second pass.
            continue

    # Second pass: assign any remaining i to the nearest unused j.
    for i in range(N):
        if mapping[i] != -1:
            continue
        for j in pref[i]:
            if not used[j]:
                mapping[i] = j
                used[j] = True
                break

    # Safety: ensure total mapping.
    assert np.all(mapping >= 0), "Failed to build a complete atom mapping"
    return mapping


def _frac_to_cartesian(container, dfrac: np.ndarray) -> np.ndarray:
    """
    Convert fractional vectors to Cartesian using the container's lattice.
    Adapt the lattice accessor if your codebase uses a different attribute.
    """
    # Try common names for the 3x3 lattice matrix with rows as a,b,c in Cartesian Å.
    cell = getattr(container.AtomPositionManager, 'latticeVectors', None)
    if cell is None:
        cell = getattr(container.AtomPositionManager, 'cell', None)
    if cell is None:
        cell = getattr(container.AtomPositionManager, 'lattice_cartesian', None)
    if cell is None:
        raise RuntimeError("Cannot locate lattice matrix to convert fractional → Cartesian.")
    cell = np.asarray(cell, dtype=float)  # shape (3,3)
    return dfrac @ cell  # (N,3) x (3,3) → (N,3)


def _cartesian_to_frac(container, dcart: np.ndarray) -> np.ndarray:
    """Convert Cartesian vectors to fractional using the container's lattice."""
    cell = getattr(container, 'latticeVectors', None)
    if cell is None:
        cell = getattr(container.AtomPositionManager, 'latticeVectors', None)
    if cell is None:
        cell = getattr(container.AtomPositionManager, 'lattice_cartesian', None)
    if cell is None:
        raise RuntimeError("Cannot locate lattice matrix to convert Cartesian → fractional.")
    cell = np.asarray(cell, dtype=float)  # (3,3)
    # Solve cell^T * frac = cart^T  →  frac = cart @ inv(cell)
    inv_cell = np.linalg.inv(cell)
    return dcart @ inv_cell









