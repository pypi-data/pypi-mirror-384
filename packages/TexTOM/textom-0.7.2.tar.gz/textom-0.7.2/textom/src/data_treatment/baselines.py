import numpy as np
from numba import njit, prange

from .. import numba_plugins as nb
from ...config import data_type

@njit
def no_baseline( q, data, mask, args=0 ):
    """
    Returns zeros with the same shape and type as data

    Parameters
    ----------
    x : 1D float array (monotonic increasing assumed)
    data : 1D float array
    mask : 1D boolean array, same length as x

    Returns
    -------
    baseline : 1D float array, same length as data
    """
    return np.zeros_like(data)

@njit
def linear_baseline(q, data, mask, args=0):
    """
    Build a baseline where:
    - baseline[i] = data[i] if mask[i] is True
    - baseline[i] = linear interpolation between the nearest True values
      on the left and right otherwise.

    Parameters
    ----------
    x : 1D float array (monotonic increasing assumed)
    data : 1D float array
    mask : 1D boolean array, same length as x

    Returns
    -------
    baseline : 1D float array, same length as data
    """
    n = len(q)
    baseline = np.empty(n, dtype=data.dtype)

    # First, copy True positions directly
    for i in range(n):
        if mask[i]:
            baseline[i] = data[i]

    # Then, interpolate False regions
    i = 0
    while i < n:
        if not mask[i]:
            # find previous True
            i0 = i - 1
            while i0 >= 0 and not mask[i0]:
                i0 -= 1

            # find next True
            i1 = i + 1
            while i1 < n and not mask[i1]:
                i1 += 1

            if i0 >= 0 and i1 < n:
                # interpolate between (x[i0], data[i0]) and (x[i1], data[i1])
                x0, y0 = q[i0], data[i0]
                x1, y1 = q[i1], data[i1]
                for j in range(i0 + 1, i1):
                    t = (q[j] - x0) / (x1 - x0)
                    baseline[j] = (1.0 - t) * y0 + t * y1
                i = i1  # jump ahead
            else:
                # no bounding True on one side → just copy data
                baseline[i] = data[i]
                i += 1
        else:
            i += 1

    return baseline

@njit
def polynomial_baseline( x, y, mask, order ):
    """
    Fit polynomial background using masked points.

    Parameters
    ----------
    x : (N,) ndarray float64
        Independent variable (will be scaled to [-1,1]).
    y : (N,) ndarray float64
        Measured intensity.
    mask : (N,) ndarray bool
        True for points to use in the fit (i.e. outside peaks).
    order : int
        Polynomial order (N_coeff = order+1).

    Returns
    -------
    Background evaluated at all x.
    """
    c = nb.nb_polyfit( x[mask], y[mask], order )
    return nb.nb_polyval( c, x )


@njit
def chebyshev_baseline(x, y, mask, order, reg=1e-10):
    """
    Fit Chebyshev polynomial background using masked points.
    Numba-friendly: uses explicit loops and basic linear-algebra.

    Parameters
    ----------
    x : (N,) ndarray float64
        Independent variable (will be scaled to [-1,1]).
    y : (N,) ndarray float64
        Measured intensity.
    mask : (N,) ndarray bool
        True for points to use in the fit (i.e. outside peaks).
    order : int
        Polynomial order (N_coeff = order+1).
    reg : float
        Small Tikhonov regularization added to normal matrix diagonal.

    Returns
    -------
    y_bg : (N,) ndarray float64
        Background evaluated at all x.

        disabled:
    coeffs : (order+1,) ndarray float64
        Chebyshev coefficients (c0..c_order).
    """
    # --- basic checks (kept simple for njit compatibility) ---
    n = x.shape[0]
    if y.shape[0] != n or mask.shape[0] != n:
        raise ValueError("x, y, mask must have same length")

    # scale x to [-1, 1]
    x_min = x[0]
    x_max = x[0]
    for i in range(1, n):
        if x[i] < x_min:
            x_min = x[i]
        if x[i] > x_max:
            x_max = x[i]
    # avoid division by zero
    span = x_max - x_min
    if span == 0.0:
        raise ValueError("x has zero range")
    x_scaled = np.empty(n, dtype=np.float64)
    two_over_span = 2.0 / span
    for i in range(n):
        x_scaled[i] = (x[i] - x_min) * two_over_span - 1.0

    m = order + 1
    # Normal matrix A (m x m) and right-hand side b (m)
    A = np.zeros((m, m), dtype=np.float64)
    b = np.zeros(m, dtype=np.float64)

    # accumulate A = T^T T and b = T^T y over masked points
    # We'll compute Chebyshev basis values T_j(x) via recurrence for each masked x
    for idx in range(n):
        if not mask[idx]:
            continue
        xi = x_scaled[idx]
        # compute T_0..T_order at xi
        # T0 = 1
        # T1 = xi
        Tprev = 1.0   # T_0
        # fill row vector t_j = [T0, T1, ...]
        t = np.empty(m, dtype=np.float64)
        t[0] = Tprev
        if m > 1:
            Tcur = xi
            t[1] = Tcur
            for j in range(2, m):
                Tnext = 2.0 * xi * Tcur - Tprev
                t[j] = Tnext
                Tprev = Tcur
                Tcur = Tnext
        val = y[idx]
        # update A and b
        for i_row in range(m):
            bi = t[i_row] * val
            b[i_row] += bi
            for j_col in range(i_row, m):
                Aij = t[i_row] * t[j_col]
                A[i_row, j_col] += Aij
                if j_col != i_row:
                    A[j_col, i_row] += Aij  # exploit symmetry

    # regularize A slightly to avoid singularity
    # add reg * trace(A)/m or reg if A diagonal zeros
    traceA = 0.0
    for i in range(m):
        traceA += A[i, i]
    if traceA == 0.0:
        alpha = reg
    else:
        alpha = reg * traceA / float(m)
    for i in range(m):
        A[i, i] += alpha

    # solve A coeffs = b
    coeffs = np.linalg.solve(A, b)

    # evaluate background at all x using recurrence
    y_bg = np.empty(n, dtype=np.float64)
    for idx in range(n):
        xi = x_scaled[idx]
        # evaluate Chebyshev series via Clenshaw-like recurrence or direct
        # We'll use direct accumulation with recurrence for basis (safe & simple)
        Tprev = 1.0
        s = coeffs[0] * Tprev
        if m > 1:
            Tcur = xi
            s += coeffs[1] * Tcur
            for j in range(2, m):
                Tnext = 2.0 * xi * Tcur - Tprev
                s += coeffs[j] * Tnext
                Tprev = Tcur
                Tcur = Tnext
        y_bg[idx] = s

    return y_bg

@njit
def auto_chebyshev(x, y, mask, args=(10, 6, 3.0, 3)):
    # pre_order=6,  k_sigma=3.0, peak_expand=3
    order=int(args[0])
    pre_order=int(args[1])
    k_sigma=args[2]
    peak_expand=int(args[3])
    mask_auto = auto_mask_by_cheby(x, y, pre_order, k_sigma, peak_expand)
    mask_auto[0] = True # always fit first and last points
    mask_auto[-1] = True
    return chebyshev_baseline(x, y, mask_auto, order, reg=1e-10)

@njit
def auto_mask_by_cheby(x, y, pre_order=6, k_sigma=2.0, peak_expand=2):
    """
    Create mask for baseline fitting: True = keep, False = peak.
    
    Parameters
    ----------
    y : (N,) ndarray
        Intensity values.
    smooth_sd : float
        Sigma of Gaussian (in points) for baseline smoothing.
        Should be much larger than peak width.
    k_sigma : float
        Threshold in units of residual std for calling a point a peak.
    peak_expand : int
        Expand mask around detected peaks by this many points.
    
    Returns
    -------
    mask : (N,) bool ndarray
    """
    n = y.shape[0]

    ys = chebyshev_baseline(x, y, np.ones_like(y), pre_order, reg=1e-10)

    # residuals
    resid = y - ys
    mean = 0.0
    for i in range(n):
        mean += resid[i]
    mean /= n
    var = 0.0
    for i in range(n):
        d = resid[i] - mean
        var += d * d
    var /= n
    s = np.sqrt(var)

    mask = np.ones(n, dtype=np.bool_)
    for i in range(n):
        if resid[i] > k_sigma * s:
            lo = max(0, i - peak_expand)
            hi = min(n, i + peak_expand + 1)
            for j in range(lo, hi):
                mask[j] = False
    return mask