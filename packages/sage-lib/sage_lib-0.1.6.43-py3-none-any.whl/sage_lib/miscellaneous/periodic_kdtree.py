import numpy as np
import itertools
from scipy.spatial import cKDTree

class PeriodicCKDTree(cKDTree):
    """
    cKDTree subclass supporting periodic boundary conditions.

    Behaviors:
      - Orthorhombic box (1D bounds) with full periodicity: uses native cKDTree methods.
      - General box (2D bounds matrix): uses query tiling to implement PBC.
    """
    def __init__(self, bounds, data, leafsize=10, pbc=None, force_orth:bool=False):
        data = np.asarray(data, float)
        d    = data.shape[1]

        # Normalize pbc
        if pbc is None:
            pbc = (True,) * d
        elif len(pbc) != d:
            raise ValueError(f"pbc must have length {d}")
        self.pbc = tuple(pbc)

        # Force float-array form
        # Ensure bounds is a float array
        bounds = np.asarray(bounds, float)

        # Determine if we can use the native orthorhombic periodic support
        is_orth = force_orth and ((bounds.ndim==1 and bounds.size==d) \
                  or (bounds.ndim==2 and bounds.shape==(d,d) \
                      and not np.any(np.abs(bounds[~np.eye(d, dtype=bool)])>1e-12)))

        if is_orth and all(self.pbc):
            # Use native cKDTree periodic support for orthorhombic box
            # Orthorhombic periodic box: use native cKDTree periodic support
            box = bounds if bounds.ndim == 1 else np.diag(bounds)
            super().__init__(data, leafsize=leafsize, boxsize=box)
            self._use_native = True
            self.bounds = np.diag(box)
        else:
            # Fallback: plain cKDTree + manual tiling
            # General case: build plain cKDTree on data (no tiling)
            super().__init__(data, leafsize=leafsize)
            self._use_native = False
            if bounds.ndim == 1:
                self.bounds = np.diag(bounds)
            elif bounds.ndim == 2 and bounds.shape == (d, d):
                self.bounds = bounds
            else:
                raise ValueError(f"bounds must be length-{d} or {d}x{d} matrix")

        self._n_orig = data.shape[0]

    def __reduce__(self):
        fn, args, state = super().__reduce__()  
        extra = (self._use_native, self.pbc, self.bounds, self._n_orig)
        return (self.__class__._rebuild, (fn, args, state) + extra)

    @staticmethod
    def _rebuild(fn, args, state, use_native, pbc, bounds, n_orig):
        tree = fn(*args)
        super(PeriodicCKDTree, tree).__setstate__(state)
        tree._use_native = use_native
        tree.pbc          = pbc
        tree.bounds       = bounds
        tree._n_orig      = n_orig
        return tree
    
    @property
    def use_native(self) -> bool:
        """
        Whether this tree is using SciPy’s native periodic-box support
        (True) or the custom tiling implementation (False).
        """
        return self._use_native

    @use_native.setter
    def use_native(self, flag: bool):
        """
        Manually enable or disable native-box support.

        Parameters
        ----------
        flag : bool
            True to force native periodic support; False to force the
            fallback tiling implementation.
        """
        self._use_native = bool(flag)

    def _make_shifts(self, r):
        # Compute integer shifts needed to cover radius r
        lengths = np.linalg.norm(self.bounds, axis=0)
        max_shifts = np.ceil(r / lengths).astype(int)
        axes = [range(-m, m + 1) if p else (0,)
                for m, p in zip(max_shifts, self.pbc)]
        return np.array(list(itertools.product(*axes)), int)

    def query(self, x, k=1, eps=0, p=2, distance_upper_bound=np.inf):
        if self.use_native:
            return super().query(x, k=k, eps=eps, p=p, distance_upper_bound=distance_upper_bound)

        x_arr = np.asarray(x, float)
        single = (x_arr.ndim == 1)
        Q = x_arr.reshape(-1, x_arr.shape[-1])
        d = Q.shape[1]

        # generate shifts for triclinic PBC: {-1,0,1} on periodic axes
        axes = [(-1, 0, 1) if p else (0,) for p in self.pbc]
        shifts_i = np.array(list(itertools.product(*axes)), dtype=int)
        shifts_r = shifts_i.dot(self.bounds)  # shape (S, d), lattice-vector shifts

        # tile queries and run a single kNN on the base tree
        tiledQ = (Q[:, None, :] + shifts_r[None, :, :]).reshape(-1, d)
        dists, idxs = super().query(
            tiledQ, k=k, eps=eps, p=p, distance_upper_bound=distance_upper_bound
        )

        # reshape to (nQ, S*k) and keep best k per original query
        S = shifts_r.shape[0]
        dists = dists.reshape(Q.shape[0], S * k)
        idxs  = idxs.reshape(Q.shape[0], S * k)

        # select top-k along axis=1
        part = np.argpartition(dists, kth=np.minimum(k-1, dists.shape[1]-1), axis=1)[:, :k]
        row_idx = np.arange(Q.shape[0])[:, None]
        d_best = dists[row_idx, part]
        i_best = idxs[row_idx, part]

        # sort those top-k to maintain ascending order
        order = np.argsort(d_best, axis=1)
        d_best = np.take_along_axis(d_best, order, axis=1)
        i_best = np.take_along_axis(i_best, order, axis=1)

        i_best = np.mod(i_best, self._n_orig)

        if single and k == 1:
            return d_best[0, 0], i_best[0, 0]
        if single:
            return d_best[0], i_best[0]
        if k == 1:
            return d_best[:, 0], i_best[:, 0]
        return d_best, i_best
        
    def query_ball_point(self, x, r, p=2., eps=0):
        if self.use_native:
            return super().query_ball_point(x, r, p, eps)

        x_arr = np.asarray(x, float)
        single = (x_arr.ndim == 1)
        Q = x_arr.reshape(-1, x_arr.shape[-1])

        shifts_i = self._make_shifts(r)
        shifts_r = shifts_i.dot(self.bounds)
        tiled = (Q[:, None, :] + shifts_r[None, :, :]).reshape(-1, Q.shape[1])
        raw = super().query_ball_point(tiled, r, p, eps)

        raw = np.array(raw, object).reshape(Q.shape[0], -1)
        out = []
        for row in raw:
            idxs = np.concatenate(row) % self._n_orig
            out.append( np.unique(idxs).astype(np.int64) )

        return out[0] if single else out

    def query_ball_tree(self, other, r, p=2., eps=0):
        if self.use_native and getattr(other, 'use_native', False):
            return super().query_ball_tree(other, r, p, eps)
        if not isinstance(other, PeriodicCKDTree):
            raise ValueError("Other tree must be PeriodicCKDTree")
        return other.query_ball_point(self.data, r, p, eps)

    def query_pairs(self, r, p=2., eps=0):
        if self.use_native:
            return super().query_pairs(r, p, eps)
        pairs = set()
        neighbors = self.query_ball_point(self.data, r, p, eps)
        for i, nbrs in enumerate(neighbors):
            for j in nbrs:
                if i < j:
                    pairs.add((i, j))
        return sorted(pairs)

    def count_neighbors(self, other, r, p=2.):
        '''
        if self._use_native and getattr(other, '_use_native', False):
            return super().count_neighbors(other, r, p)
        if not isinstance(other, PeriodicCKDTree):
            raise ValueError("Other tree must be PeriodicCKDTree")
        raw = super().count_neighbors(other, r, p)
        return np.array(raw).reshape(-1, self._n_orig).sum(axis=0)
        '''
        if self.use_native and getattr(other, 'use_native', False):
            return super().count_neighbors(other, r, p)
        if not isinstance(other, PeriodicCKDTree):
            raise ValueError("Other tree must be PeriodicCKDTree")

        counts = np.zeros(other.n, dtype=int)
        for i, point in enumerate(other.data):
            indices = self.query_ball_point(point, r, p)
            counts[i] = len(indices)
            
        return counts

    def sparse_distance_matrix(self, other, max_distance, p=2.):
        if self.use_native and getattr(other, 'use_native', False):
            return super().sparse_distance_matrix(other, max_distance, p)
        if not isinstance(other, PeriodicCKDTree):
            raise ValueError("Other tree must be PeriodicCKDTree")
        raw = super().sparse_distance_matrix(other, max_distance, p)
        result = {}
        for (i_t, j_t), dist in raw.items():
            i, j = i_t % self._n_orig, j_t % other._n_orig
            key = (i, j) if i < j else (j, i)
            if key not in result or dist < result[key]:
                result[key] = dist

        return result

    def sparse_distance_matrix2(self, other, max_distance, p=2.):
        """
        Periodic sparse distance matrix under a general lattice.

        Returns a dict mapping (i, j) -> distance for all pairs with
        minimum-image distance <= max_distance.

        Behavior:
          - If both trees use native orthorhombic periodic support, defer to SciPy.
          - Otherwise, tile 'other' by the lattice shifts sufficient to cover
            max_distance and compute a single sparse matrix query.
          - If self is other, exclude (i,i) and return only i<j, matching SciPy.

        Parameters
        ----------
        other : PeriodicCKDTree
            The other tree (must share the same dimensionality and lattice).
        max_distance : float
            Distance cutoff (must be finite).
        p : float
            Minkowski norm parameter (as in cKDTree).
        """
        # Fast path: both trees can rely on SciPy’s native orthorhombic support
        if self.use_native and getattr(other, 'use_native', False):
            return super().sparse_distance_matrix(other, max_distance, p)

        if not isinstance(other, PeriodicCKDTree):
            raise ValueError("Other tree must be PeriodicCKDTree")

        if not np.isfinite(max_distance):
            raise ValueError("max_distance must be finite for periodic tiling")

        # Basic sanity checks
        if self.data.shape[1] != other.data.shape[1]:
            raise ValueError("Dimensionality mismatch between trees")
        if self.bounds.shape != other.bounds.shape or not np.allclose(self.bounds, other.bounds, atol=1e-12):
            raise ValueError("Both trees must share the same lattice (bounds)")
        if self.pbc != other.pbc:
            raise ValueError("Both trees must share the same PBC tuple")

        # Compute lattice shifts to cover the search radius
        shifts_i = self._make_shifts(max_distance)              # (S, d) integer shifts
        shifts_r = shifts_i.dot(self.bounds)                    # (S, d) Cartesian shifts
        S        = shifts_r.shape[0]
        d        = self.data.shape[1]

        # Tile 'other' points by all shifts: shape (S * n_other, d)
        O = np.asarray(other.data, float)
        tiled_other = (O[None, :, :] + shifts_r[:, None, :]).reshape(S * other._n_orig, d)

        # Build a plain cKDTree on the tiled 'other' points (no periodicity here)
        tiled_tree = cKDTree(tiled_other, leafsize=other.leafsize)

        # Query sparse distances from *this* base tree to the tiled-other tree
        raw = super(PeriodicCKDTree, self).sparse_distance_matrix(tiled_tree, max_distance, p)

        # Fold back tiled indices to base indices, keeping the minimum distance per (i,j)
        result = {}
        same_obj = (self is other)

        # Identify the index of the zero lattice shift to drop (i,i) when self is other
        zero_shift_idx = None
        zmask = np.all(shifts_i == 0, axis=1)
        if np.any(zmask):
            zero_shift_idx = int(np.nonzero(zmask)[0][0])

        for (i, j_tiled), dist in raw.items():
            # Recover the original j and the image (shift) index
            j = j_tiled % other._n_orig
            img_idx = j_tiled // other._n_orig

            # If querying the same object, exclude the zero-shift self-pair and enforce (i<j)
            if same_obj:
                if (zero_shift_idx is not None) and (img_idx == zero_shift_idx) and (i == j):
                    continue
                if j < i:
                    i, j = j, i

            key = (i, j)
            prev = result.get(key)
            if (prev is None) or (dist < prev):
                result[key] = dist

        return result
