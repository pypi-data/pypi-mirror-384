import numpy as np
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

    def query2(self, x, k=1, eps=0, p=2, distance_upper_bound=np.inf):
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

# ----------------------
# Test utilities
# ----------------------
import numpy as np
import itertools
import matplotlib.pyplot as plt

# ---------- Paste your PeriodicCKDTree class definition above this line ----------

# ----------------------
# Helpers
# ----------------------
def triclinic_bounds_2d():
    """
    Simple skewed 2D cell (non-orthogonal). Rows are lattice vectors (a, b).
    """
    #a = np.array([1.8, 1.0])
    #b = np.array([1.6, 1.4])
    a = np.array([1.8, .0])
    b = np.array([.6, 1.4])
    return np.vstack([a, b])  # shape (2,2)

def frac_to_cart(frac, bounds):
    return frac @ bounds

def enumerate_shifts_2d(pbc=(True, True), m=1):
    axes = [range(-m, m+1) if p else (0,) for p in pbc]
    return np.array(list(itertools.product(*axes)), dtype=int)

def min_image_nn(point, data, bounds, pbc=(True,True), m=1):
    """
    Brute-force minimum-image nearest neighbor (index, distance, winning integer shift).
    """
    shifts = enumerate_shifts_2d(pbc, m=m)
    shifts_cart = shifts @ bounds  # (S,2)
    # For each data point, check all images
    best_d = np.inf
    best_i = -1
    best_shift = None
    for i, y in enumerate(data):
        # distances to all images of y
        diffs = point - (y + shifts_cart)
        dists = np.linalg.norm(diffs, axis=1)
        j = np.argmin(dists)
        if dists[j] < best_d:
            best_d = dists[j]
            best_i = i
            best_shift = shifts[j]
    return best_i, best_d, best_shift

def plot_cell_and_images(ax, bounds, m=1, **kw):
    # draw central cell as a polygon and its neighbors
    a, b = bounds[0], bounds[1]
    cell = np.array([[0,0], a, a+b, b, [0,0]])
    for i in range(-m, m+1):
        for j in range(-m, m+1):
            T = i*a + j*b
            poly = cell + T
            ax.plot(poly[:,0], poly[:,1], **kw)

def visualize_mismatch(tree, bounds, data, q, naive_idx, true_idx, true_shift):
    fig, ax = plt.subplots(figsize=(6.0, 6.0))
    ax.set_aspect('equal', adjustable='box')

    # draw unit cell + neighbors
    plot_cell_and_images(ax, bounds, m=1, color='0.8', linewidth=1.0)

    # plot data and query
    ax.scatter(data[:,0], data[:,1], s=20, label='Data', zorder=3)
    ax.scatter([q[0]],[q[1]], marker='*', s=180, color='red', label='Query', zorder=4)

    # naive neighbor (no PBC tiling in query)
    y_naive = data[naive_idx]
    ax.scatter([y_naive[0]],[y_naive[1]], s=80, facecolors='none', edgecolors='orange', linewidths=2.0,
               label='naive query() NN', zorder=4)
    ax.plot([q[0], y_naive[0]], [q[1], y_naive[1]], linestyle='--', linewidth=1.5, color='orange')

    # true min-image neighbor (may require shifting the data point)
    a, b = bounds[0], bounds[1]
    y_true_img = data[true_idx] + true_shift[0]*a + true_shift[1]*b
    ax.scatter([y_true_img[0]],[y_true_img[1]], s=80, marker='s', facecolors='none',
               edgecolors='green', linewidths=2.0, label='true min-image NN', zorder=5)
    ax.plot([q[0], y_true_img[0]], [q[1], y_true_img[1]], linewidth=2.0, color='green')

    ax.legend(loc='upper right', frameon=True)
    ax.set_title('Nearest neighbor under triclinic PBC:\nnaive query() vs. true minimum-image')
    plt.tight_layout()
    plt.show()


# ----------------------
# Brute-force ball reference + visualization
# ----------------------
import matplotlib.patches as mpatches

def min_image_ball(point, data, bounds, r, pbc=(True, True), m=None):
    """
    Return indices, best shifts, and distances of all points whose
    minimum-image distance to `point` is <= r in a 2D triclinic cell.
    """
    # choose a safe tiling reach if not provided
    a, b = bounds[0], bounds[1]
    la, lb = np.linalg.norm(a), np.linalg.norm(b)
    if m is None:
        # cover at least r along the shorter lattice, +1 for safety
        m = int(np.ceil(r / max(1e-12, min(la, lb)))) + 1

    shifts = enumerate_shifts_2d(pbc, m=m)         # (S,2) integer shifts
    shifts_cart = shifts @ bounds                  # (S,2) cartesian shifts

    best_d = np.full(len(data), np.inf, float)
    best_s = np.zeros((len(data), 2), int)

    for si, t in enumerate(shifts_cart):
        diffs = point - (data + t)                 # (n,2)
        dists = np.linalg.norm(diffs, axis=1)      # (n,)
        improved = dists < best_d
        best_d[improved] = dists[improved]
        best_s[improved] = shifts[si]

    inside = np.where(best_d <= r + 1e-12)[0]
    return inside, best_s[inside], best_d[inside]

def visualize_ball(tree, bounds, data, q, r, true_idxs, true_shifts, idxs_tree):
    fig, ax = plt.subplots(figsize=(6.4, 6.4))
    ax.set_aspect('equal', adjustable='box')

    # draw the cell mesh
    plot_cell_and_images(ax, bounds, m=1, color='0.85', linewidth=1.0)

    # query point and radius circle
    ax.scatter([q[0]], [q[1]], marker='*', s=160, color='red', zorder=5, label='Query')
    circ = mpatches.Circle((q[0], q[1]), r, fill=False, linewidth=1.5)
    ax.add_patch(circ)

    # True (reference) neighbor image positions
    a, b = bounds[0], bounds[1]
    true_img = data[true_idxs] + (true_shifts[:,0,None] * a + true_shifts[:,1,None] * b)
    ax.scatter(true_img[:,0], true_img[:,1], marker='s', s=64, facecolors='none',
               edgecolors='green', linewidths=2.0, zorder=4, label='True min-image')

    # Compare sets
    set_true = set(map(int, true_idxs))
    set_tree = set(map(int, np.atleast_1d(idxs_tree)))
    missed   = sorted(set_true - set_tree)   # FN
    extra    = sorted(set_tree - set_true)   # FP

    # Plot missed (red X)
    if missed:
        # compute their winning images for clarity
        mi, ms, _ = min_image_ball(q, data[missed], bounds, r, pbc=(True,True))
        # mi are local indices; map back
        ms_global = np.array(missed, int)[mi]
        shifts_missed = np.zeros((len(ms_global), 2), int)
        shifts_missed[:] = ms[range(len(ms_global))]
        missed_img = data[ms_global] + (shifts_missed[:,0,None] * a + shifts_missed[:,1,None] * b)
        ax.scatter(missed_img[:,0], missed_img[:,1], marker='x', s=80, linewidths=2.0,
                   color='red', zorder=6, label='Missed by tree')

    # Plot extra (orange triangle)
    if extra:
        # show their min-image positions relative to q
        ei, es, _ = min_image_ball(q, data[extra], bounds, r, pbc=(True,True))
        es_global = np.array(extra, int)[ei]
        shifts_extra = np.zeros((len(es_global), 2), int)
        shifts_extra[:] = es[range(len(es_global))]
        extra_img = data[es_global] + (shifts_extra[:,0,None] * a + shifts_extra[:,1,None] * b)
        ax.scatter(extra_img[:,0], extra_img[:,1], marker='^', s=70,
                   edgecolors='orange', facecolors='none', linewidths=2.0,
                   zorder=6, label='Extra in tree')

    ax.legend(loc='upper right', frameon=True)
    ax.set_title(f'query_ball_point under triclinic PBC (r = {r:.3f})')
    plt.tight_layout()
    plt.show()

def demo_query_ball_point():
    rng = np.random.default_rng(123)
    bounds = triclinic_bounds_2d()
    pbc = (True, True)

    # random data in [0,1)^2 mapped to triclinic
    n = 520
    data = frac_to_cart(rng.random((n, 2)), bounds)

    # Build the periodic tree (non-native path for triclinic)
    tree = PeriodicCKDTree(bounds=bounds, data=data, pbc=pbc, force_orth=False)
    assert not tree.use_native

    # try multiple queries/radii until a mismatch is found
    # choose r up to ~1.2 * min(|a|, |b|) to stress tiling
    la, lb = np.linalg.norm(bounds[0]), np.linalg.norm(bounds[1])
    r_min, r_max = 0.05 * min(la, lb), 1.2 * min(la, lb)

    for _ in range(600):
        q = frac_to_cart(rng.random(2), bounds)
        r = float(rng.uniform(r_min, r_max))

        idxs_tree = tree.query_ball_point(q, r, p=2, eps=0)
        idxs_true, shifts_true, _ = min_image_ball(q, data, bounds, r, pbc, m=None)

        set_tree = set(map(int, np.atleast_1d(idxs_tree)))
        set_true = set(map(int, idxs_true))
        if set_tree != set_true:
            print("Mismatch found!")
            print(f"  |true|={len(set_true)}  |tree|={len(set_tree)}")
            print(f"  missed: {sorted(set_true - set_tree)}")
            print(f"  extra : {sorted(set_tree - set_true)}")
            visualize_ball(tree, bounds, data, q, r, idxs_true, shifts_true, idxs_tree)
            break
    else:
        print("No mismatch found in this sweep. Showing a representative success case.")
        # Plot one successful example for sanity
        q = frac_to_cart(rng.random(2), bounds)
        r = float(rng.uniform(r_min, r_max))
        idxs_tree = tree.query_ball_point(q, r, p=2, eps=0)
        idxs_true, shifts_true, _ = min_image_ball(q, data, bounds, r, pbc, m=None)
        visualize_ball(tree, bounds, data, q, r, idxs_true, shifts_true, idxs_tree)


# ----------------------
# Main demo
# ----------------------
if __name__ == "__main__":
    rng = np.random.default_rng(72)
    bounds = triclinic_bounds_2d()
    pbc = (True, True)

    # random data in [0,1)^2 then mapped to triclinic
    n = 200
    frac = rng.random((n, 2))
    data = frac_to_cart(frac, bounds)

    # Build your tree (ensure non-native path)
    tree = PeriodicCKDTree(bounds=bounds, data=data, pbc=pbc, force_orth=False)
    assert not tree.use_native, "Expecting non-native path for triclinic cell."

    # Hunt for a mismatch between naive query() and brute-force min-image
    found = False
    for _ in range(500):
        q_frac = rng.random(2)
        q = frac_to_cart(q_frac, bounds)

        # naive (current implementation)
        d_naive, i_naive = tree.query(q, k=1, p=2)

        # brute-force min-image (reference)
        i_true, d_true, shift = min_image_nn(q, data, bounds, pbc, m=1)

        # Consider a mismatch if indices differ or distances differ notably
        if (int(i_naive) != int(i_true)) or (abs(float(d_naive) - float(d_true)) > 1e-10):
            print("Mismatch found!")
            print(f" naive: idx={i_naive}, dist={d_naive:.6f}")
            print(f" true : idx={i_true}, dist={d_true:.6f}, shift={tuple(shift)}")
            visualize_mismatch(tree, bounds, data, q, int(i_naive), int(i_true), shift)
            found = True
            break

    if not found:
        print("No mismatch found in this run. (Common after applying the tiled query() fix.)")
        # Optionally, still visualize a random query to see geometry
        q_frac = rng.random(2); q = frac_to_cart(q_frac, bounds)
        i_true, d_true, shift = min_image_nn(q, data, bounds, pbc, m=1)
        visualize_mismatch(tree, bounds, data, q, int(i_true), int(i_true), shift)

    demo_query_ball_point()