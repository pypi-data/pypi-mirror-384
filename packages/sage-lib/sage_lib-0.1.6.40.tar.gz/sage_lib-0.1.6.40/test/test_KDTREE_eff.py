import numpy as np, time, itertools
from scipy.spatial import cKDTree
import itertools

# --- Paste your PeriodicCKDTree class here ---
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

    def query1(self, x, k=1, eps=0, p=2, distance_upper_bound=np.inf):
        if self.use_native:
            return super().query(x, k=k, eps=eps, p=p, distance_upper_bound=distance_upper_bound)
        dists, idxs = super().query(x, k=k, eps=eps, p=p, distance_upper_bound=distance_upper_bound)
        return dists, np.mod(idxs, self._n_orig)
        
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

# ---------------------------
# Benchmark configuration
# ---------------------------
SEED = 123
D = 3                    # dimensionality
N_DATA = 40_000          # number of data points
N_QUERY = 3_000          # number of queries (the user asked for 1000)
K = 4                    # k-NN
P_NORM = 2               # use Euclidean
USE_UPPER_BOUND = False  # set True to test with distance_upper_bound
VERIFY_ON = 100          # number of queries to verify correctness (0 to skip)
REPEATS = 5              # repeat timing to reduce variance
WARMUP = 1               # warmup loops

# ---------------------------
# Geometry helpers
# ---------------------------
def triclinic_bounds_3d():
    # clearly skewed 3D cell (rows are lattice vectors)
    a = np.array([2.00, 0.00, 0.00])
    b = np.array([0.80, 1.70, 0.10])
    c = np.array([0.30, 0.40, 1.60])
    return np.vstack([a, b, c])

def frac_to_cart(frac, bounds):
    # rows-as-basis → right-multiply
    return frac @ bounds

# brute-force minimum-image for correctness checks
def enumerate_shifts(pbc=(True,True,True), m=1):
    axes = [range(-m, m+1) if p else (0,) for p in pbc]
    return np.array(list(itertools.product(*axes)), dtype=int)

def brute_force_knn(xq, data, bounds, p=2, k=1, pbc=(True,True,True), m=1):
    shifts = enumerate_shifts(pbc, m)
    shifts_cart = shifts @ bounds  # (S,3)
    diffs = xq[None, None, :] - (data[None, :, :] + shifts_cart[:, None, :])  # (S,N,3)
    dists = np.linalg.norm(diffs, axis=-1) if p == 2 else np.linalg.norm(diffs, ord=p, axis=-1)
    dmin = dists.min(axis=0)            # (N,)
    # get top-k indices
    k = min(k, data.shape[0])
    part = np.argpartition(dmin, kth=k-1)[:k]
    part_sorted = part[np.argsort(dmin[part])]
    return dmin[part_sorted], part_sorted

# ---------------------------
# Data
# ---------------------------
rng = np.random.default_rng(SEED)
bounds = triclinic_bounds_3d()
pbc = (True, True, True)

# random fractional → Cartesian in triclinic cell
data_frac = rng.random((N_DATA, D))
data = frac_to_cart(data_frac, bounds)

queries_frac = rng.random((N_QUERY, D))
queries = frac_to_cart(queries_frac, bounds)

# ---------------------------
# Build trees (one instance)
# ---------------------------
tree = PeriodicCKDTree(bounds=bounds, data=data, pbc=pbc, force_orth=False)
assert not tree.use_native, "Benchmark targets non-native triclinic path."

# distance_upper_bound (optional)
if USE_UPPER_BOUND:
    # conservative upper bound: ~half the shortest lattice vector length
    lengths = np.linalg.norm(bounds, axis=1)
    dub = 0.5 * float(np.min(lengths))
else:
    dub = np.inf

# ---------------------------
# Utility: timed run
# ---------------------------
def time_method(callable_query, label):
    # warmup
    for _ in range(WARMUP):
        _ = callable_query(queries)

    times = []
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        _ = callable_query(queries)
        t1 = time.perf_counter()
        times.append(t1 - t0)

    best = min(times)  # take best-of-REPEATS to reduce noise
    per_query_us = best / N_QUERY * 1e6
    print(f"{label:>10s} | total = {best:8.4f} s | per-query = {per_query_us:8.2f} μs")
    return best

# Wrapper so both methods are exercised identically (supports k>1 and upper bound)
def run_query_batch_q(tree_inst, X):
    # vectorized call: pass the full array of queries
    d, i = tree_inst.query(X, k=K, p=P_NORM, distance_upper_bound=dub)
    # touch results to avoid elision
    return (np.asarray(d).sum(), np.asarray(i).sum())

def run_query1_batch_q(tree_inst, X):
    d, i = tree_inst.query1(X, k=K, p=P_NORM, distance_upper_bound=dub)
    return (np.asarray(d).sum(), np.asarray(i).sum())

# ---------------------------
# Correctness spot-checks
# ---------------------------
def check_correctness():
    idxs = rng.choice(N_QUERY, size=min(VERIFY_ON, N_QUERY), replace=False)
    max_dist_err = 0.0
    mismatches = 0
    for qi in idxs:
        xq = queries[qi]
        # reference with min-image (use m=1 stencil; enlarge if your cell is tiny)
        d_ref, i_ref = brute_force_knn(xq, data, bounds, p=P_NORM, k=K, pbc=pbc, m=1)

        # method A
        d0, i0 = tree.query(xq, k=K, p=P_NORM, distance_upper_bound=dub)
        d0 = np.atleast_1d(d0); i0 = np.atleast_1d(i0)

        # method B
        d1, i1 = tree.query1(xq, k=K, p=P_NORM, distance_upper_bound=dub)
        d1 = np.atleast_1d(d1); i1 = np.atleast_1d(i1)

        # sets to be robust to equal-distance permutations
        if set(i0.tolist()) != set(i_ref.tolist()):
            mismatches += 1
        if set(i1.tolist()) != set(i_ref.tolist()):
            mismatches += 1

        # distance comparison (sorted)
        err0 = float(np.max(np.abs(np.sort(d0) - np.sort(d_ref))))
        err1 = float(np.max(np.abs(np.sort(d1) - np.sort(d_ref))))
        max_dist_err = max(max_dist_err, err0, err1)

    print(f"[verify] Checked {len(idxs)} queries | max |Δdist| = {max_dist_err:.3e} | index-mismatches×2 = {mismatches}")

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    if VERIFY_ON > 0:
        check_correctness()

    print(f"\nBenchmarking with N={N_DATA}, Q={N_QUERY}, k={K}, p={P_NORM}, "
          f"upper_bound={'on' if np.isfinite(dub) else 'off'} (triclinic, non-native)\n")

    t_query  = time_method(lambda X: run_query_batch_q(tree, X),  "query")
    t_query1 = time_method(lambda X: run_query1_batch_q(tree, X), "query1")

    # speed ratios
    if t_query1 > 0 and t_query > 0:
        ratio = t_query1 / t_query
        print(f"\nRelative speed: query1 / query = {ratio:.2f}×")
