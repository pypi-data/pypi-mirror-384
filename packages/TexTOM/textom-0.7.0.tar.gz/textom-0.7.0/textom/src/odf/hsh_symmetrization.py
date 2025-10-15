import numpy as np
# import scipy.sparse as sp
from scipy.linalg import null_space, qr
from numba import njit

from ..model import symmetries as sym

# Original Matlab code:
# Copyright 2019 Jeremy Mason
#
# Licensed under the Apache License, Version 2.0, <LICENSE-APACHE or
# http://apache.org/licenses/LICENSE-2.0> or the MIT license <LICENSE-MIT or
# http://opensource.org/licenses/MIT>, at your option. This file may not be
# copied, modified, or distributed except according to those terms.
#
# Rewritten in python by Moritz Frewein 2025

def check_matlab_matrix(M, tol):
    data = np.genfromtxt('/Users/moritz/Documents/code/textom/textom/ressources/symmetrizedHSH/output/matrix.csv',
                         delimiter=',',dtype=np.complex128)
    print(np.allclose(data,M, atol=tol))

def HSH_symmetrization_matrix(n_max, symmetry):
    gen = sym.generators(symmetry)
    gen_sample = sym.generators('1')
    X = collect_symm(gen,gen_sample, n_max=n_max, 
                    precision=1e-12
                    # precision=1e-15
                    )
    return X

def collect_symm(gc, gs, n_max, precision, skip_ghosts=True):
    # collect_symm find sets of coefficients up to n_max that make the
    # hyperspherical harmonic expansion invariant to the cubic crystal point
    # group generators. These can  be interpreted as defining a compact basis
    # for an orientation distribution obeying the required symmetry, namely,
    # the symmetrized hyperspherical harmonics.
    # 
    # Inputs:
    #   gc, gs - crystal and sample symmetry generators (sample not allowed for textom)
    #   n_max - maximum value of N for which sets of coefficients are found.
    # 
    # Outputs:
    #   symm  - a cell array containing three columns which are the outputs X,
    #           L and M of the make_symm_pq function. The value of N starts at
    #           zero and increases with the row.

    # symm = np.empty((n_max + 1, 3), dtype=object)
    symm = {'0': np.array([[1.]], np.complex128)}

    if skip_ghosts:
        step=4
    else:
        step=2

    n = step
    while n <= n_max:
        X, L, M = make_symm(gc, gs, n, precision)
        if X is not None and np.size(X) > 0:
            # symm[n, 0] = X
            # symm[n, 1] = L
            # symm[n, 2] = M
            symm[str(n)] = X.T
        n += step

    return symm

def make_symm(gc, gs, n, TOL):
    # make_symm finds sets of coefficients that make the hyperspherical
    # harmonic expansion invariant to the specified point symmetry group
    # generators. These can then be interpreted as defining a compact basis for an
    # orientation distribution obeying the required symmetry, namely, the
    # symmetrized hyperspherical harmonics.
    # 
    # The difference with make_symm is in the way the eigenspaces are combined. The
    # more formal procedure followed here constructs projection matrices and finds
    # the subspace belonging to the intersection. This is slower, but has the
    # advantage of being supported by well-established theorems.
    # 
    # Inputs:
    #   n   - upper index of the hyperspherical harmonics. The calculation is
    #         formally independent for each value of n.
    #   lx  - rotation angle and spherical angles of the rotation axis for one of 
    #         the generators left multiplying the argument of the hyperspherical
    #         harmonics. That is, a symmetry of the sample. The angles [w, th, ph]
    #         should be in the usual intervals. x can be a, b, c or d.
    #   rx  - rotation angle and spherical angles of the rotation axis for one of 
    #         the generators right multiplying the argument of the hyperspherical
    #         harmonics. That is, a symmetry of the crystal. The angles [w, th, ph]
    #         should be in the usual intervals. x can be a, b, c or d.
    #   TOL - tolerance for the desired eigenvalue of a matrix. For all practical
    #         cases the desired eigenvalues are well-separated from the rest of the
    #         spectrum, so this does not need to be excessively small.
    #
    # Outputs:
    #   X   - matrix with orthonormal columns that forms a basis for the space of 
    #         expansion coefficients satisfying the requested symmetries. That is,
    #         a column gives the expansion coefficients required to define one of
    #         the symmetrized hyperspherical harmonics. The expansion uses complex
    #         hyperspherical harmonics and orders the coefficients
    #         lexicographically in (l, m).
    #   L   - values of l for the rows of X.
    #   M   - values of m for the rows of X.

    # store objects (since X, L, M may have different shapes)
    l = n // 2

    # symmetry generators
    la = gs[0, :]
    lb = gs[1, :]
    ra = np.array([0., 0., 0.])
    rb = np.array([0., 0., 0.])
    lc = np.array([0., 0., 0.])
    ld = np.array([0., 0., 0.])

    # crystal
    rc = gc[0, :]
    rd = gc[1, :]

    # The equation for the irreps of SO(4) below allows the Clebsch-Gordan
    # coefficients to be collected into a unitary matrix. Performing a similarity
    # transformation with this matrix has the effect of converting from the 
    # uncoupled to the coupled basis.

    dim = (n + 1) ** 2
    CG = np.zeros((dim, dim))

    j_vals = np.arange(0, n + 1)
    for a in range(n + 1):
        j = j_vals[a]
        m_vals = np.arange(-j, j + 1)
        for b, m in enumerate(m_vals):
            row = (j + 1) ** 2 - j + m
            C, m1, m2 = CleGor(l, l, j, m)
            for c in range(len(C)):
                col = (int(m1[c]) + l) * (2 * l + 1) + (int(m2[c]) + l) + 1
                CG[row - 1, col - 1] = C[c]   # MATLAB → Python index shift

    # CG = CG.tocsr()
    CR = complex_real(n)

    X = np.eye(dim) #speye(dim, format="csr")
    P = X @ X.T

    # Construct simultaneous eigenvectors of eigenvalue one of the irreps of SO(4).
    # Observe that the eigenspace of eigenvalue one of a matrix A is equivalent to
    # the right nullspace of the matrix (A - I). The irrep of SO(4) is constructed
    # using the following equation (a transform of Eq. 2 of the manuscript);
    # 
    # R^{a a}_{c \gamma d \delta}(g_l, g_r) = \sum_{\alpha' \beta' \alpha \beta}
    # C^{c \gamma}_{a \alpha' a \beta'} U^a_{\alpha' \alpha}(g_r^{-1})
    # U^a_{\beta' \beta}(g_l) C^{d \delta}_{a \alpha b \beta}
    # 
    # That is, the desired irrep of SO(4) is given by a similarity transformation
    # of the Kroneker product of irreps of SO(3). The effect of right multiplying
    # a row vector of hyperspherical harmonics with this irrep is to carry every
    # rotation g \rightarrow g_l g g_r. Since the eigenspectrum of a matrix is
    # unchanged by a unitary transformation, the calculation can be performed in
    # the uncoupled basis and transformed to the coupled basis afterwards.

    # def apply_rotation(axis, ref):
    #     Rot = R(2*l, axis, ref)
    #     # Ul = rotation_mat(l, axis[0], axis[1], axis[2])
    #     # Ur = rotation_mat(l, -ref[0], ref[1], ref[2])
    #     # R = np.kron(Ur, Ul)
    #     Y = sp_orth(null_space(Rot - np.eye(Rot.shape[0]),TOL).T)
    #     # Y = sp_orth(sp_null(Rot - np.eye(Rot.shape[0]), 1, TOL))
    #     Q = Y @ Y.T
    #     return Q

    # # apply generators
    # for axis, ref in [(la, ra), (lb, rb), (lc, rc), (ld, rd)]:
    #     Q = apply_rotation(axis, ref)
        
    #     # X = sp_orth(sp_null(P @ Q - np.eye(Q.shape[0]), 1, TOL))
    #     P = X @ X.T
    rou = int(-np.log10(TOL))

    # if np.any(gs[:,0]<2*np.pi):
    Ul = U(l, la[0], la[1], la[2])
    Ur = U(l, -ra[0], ra[1], ra[2])
    Ra = np.round( np.kron(Ur, Ul), rou)
    Y = orth(null_space((Ra - np.eye(Ra.shape[0])).T,TOL))
    Q = Y @ Y.conj().T
    X = orth(null_space(np.round((P @ Q  - np.eye(Q.shape[0])).T,rou),TOL))
    P = X @ X.conj().T

    Ul = U(l, lb[0], lb[1], lb[2])
    Ur = U(l, -rb[0], rb[1], rb[2])
    Rb = np.round( np.kron(Ur, Ul), rou)
    Y = orth(null_space((Rb - np.eye(Rb.shape[0])).T,TOL))
    Q = Y @ Y.conj().T
    X = orth(null_space(np.round((P @ Q  - np.eye(Q.shape[0])).T,rou),TOL))
    P = X @ X.conj().T

    Ul = U(l, lc[0], lc[1], lc[2])
    Ur = U(l, -rc[0], rc[1], rc[2])
    Rc = np.round( np.kron(Ur, Ul), rou)
    Y = orth(null_space((Rc - np.eye(Rc.shape[0])).T,TOL))
    Q = Y @ Y.conj().T
    X = orth(null_space(np.round((P @ Q  - np.eye(Q.shape[0])).T,rou),TOL))
    P = X @ X.conj().T

    Ul = U(l, ld[0], ld[1], ld[2])
    Ur = U(l, -rd[0], rd[1], rd[2])
    Rd = np.round( np.kron(Ur, Ul), rou)
    Y = orth(null_space((Rd - np.eye(Rd.shape[0])).T,TOL))
    Q = Y @ Y.conj().T
    X = null_space(np.round((P @ Q  - np.eye(Q.shape[0])).T,rou),TOL)

    # convert to coupled basis
    X = CG @ X
    X = np.array(CR @ clean(CR.conj().T @ np.round(X,rou), TOL))

    # numerical error checks
    def max_err(R):
        if X is None or X.size == 0:
            return 0.0
        return np.max(np.abs((CG @ R @ CG.T - np.eye(R.shape[0])) @ X))
    err_a = max_err(Ra)
    err_b = max_err(Rb)
    err_c = max_err(Rc)
    err_d = max_err(Rd)

    if X.size > 0:
        if n//2%2:
            print(f"n = {n}, sHSHs found: {X.shape[1]} (ghosts), numerical error: {max([err_a, err_b, err_c, err_d]):.3e}")
        else:
            print(f"n = {n}, sHSHs found: {X.shape[1]}, numerical error: {max([err_a, err_b, err_c, err_d]):.3e}")

    else:
        print(f"n = {n}, no sHSHs.")

    # Assign indices
    L = np.zeros(dim, dtype=int)
    M = np.zeros(dim, dtype=int)
    for l_val in range(n + 1):
        for m in range(-l_val, l_val + 1):
            ind = (l_val + 1) ** 2 - l_val + m
            L[ind - 1] = l_val  # index shift
            M[ind - 1] = m

    return X, L, M

@njit
def R( n, gl, gr=np.array([0.,0.,0.]) ):
    """Function that computes a HSH rotation matrix for a given order n

    Source: Mason, J. K., Acta Crystallographica Section A Foundations of 
        Crystallography 65, no. 4 (July 1, 2009): 259?66. 
        https://doi.org/10.1107/S0108767309009921.
        equation (10)

    Parameters
    ----------
    n : int/float
        order of the HSH
    gl, gr : 2D ndarray, float
        axis-angle rotations given by angles: [omega, theta, phi]
        dimensions: 0: rotation, 1: ome,tta,phis
        
    Return values
    ------------
    R : 2D ndarray, complex
        matrix to convert a vector of HSH coefficients to a different
        vector that results in the same ODF but rotated
    """
    Ul = U( n/2, gl[0],gl[1],gl[2])
    Ur_inv = U( n/2, gr[0], gr[1], gr[2], True)
    UrUl = np.kron( Ur_inv, Ul ).astype(np.complex128)
    CG = CGn( n ).astype(np.complex128)
    R = ( CG @ UrUl @ np.conj(CG.T) )
    return R

@njit
def U(j,ome,tta,phi,invert=False):
    # U converts a rotation angle and spherical angles of the rotation
    # axis into the equivalent irrep of SO(3).
    # 
    # Inputs:
    #   j  - specifies dimension of the irrep.
    #   ome  - rotation angle in the interval [0, 2 \pi].
    #   tta - polar angle of rotation axis in the interval [0, \pi].
    #   phi - aximuthal angle of rotation axis in the interval [0, 2 \pi].
    #
    # Outputs:
    #   U  - (2 j + 1)-dimensional representation of SO(3), using the conventions
    #        established in Eq. 6 on page 81 of D. A. Varshalovich et al, Quantum
    #        Theory of Angular Momentum, 1988. Rows and columns ordered in
    #        increasing values of m' and m.

    if invert:
        ome = - ome

    tmp = np.tan(ome / 2) * np.cos(tta)
    tmp = (1 - 1j * tmp) / np.sqrt(1 + tmp**2)
    r_base = 1j * np.exp(-1j * phi) * tmp
    c_base = -1j * np.exp(1j * phi) * tmp
    
    # Require w to be in [-\pi, \pi]
    w = np.mod(ome + np.pi, 2 * np.pi) - np.pi
    xi = 2. * np.arcsin(np.sin(w / 2.) * np.sin(tta))
    U = wigner_d(j, xi).astype(np.complex128)
    
    m = np.arange(-j,j+1)
    n = int( 2 * j + 1 )
    for a in range(n):
        U[a, :] = U[a, :] * r_base**m[a]
        U[:, a] = U[:, a] * c_base**m[a]

    # tmp = tan(w / 2.) * cos(th);
    # tmp = (1. - 1i * tmp) / realsqrt(1 + tmp^2.);
    # r_base = 1i * exp(-1i * ph) * tmp;
    # c_base = -1i * exp(1i * ph) * tmp;
    
    # % Require w to be in [-\pi, \pi]
    # w = mod(w + pi, 2. * pi) - pi;
    # xi = 2. * asin(sin(w / 2.) * sin(th));
    # U = wigner_little_d(j, xi);
    
    # m = -j:j;
    # n = 2 * j + 1;
    # for a = 1:n
    #     U(a, :) = U(a, :) * r_base^m(a);
    #     U(:, a) = U(:, a) * c_base^m(a);
    return U

@njit
def CGn(n):
    """ Calculates all Clebsch-Gordan coefficients for an order n
    and assigns them into a matrix for further handling
    """
    l = n/2
    CG = np.zeros( ((n + 1)**2, (n + 1)**2), np.float64)
    for a in np.arange( 0, n+1, 1, np.int64 ):
        for b in np.arange( -a, a+1, 1, np.int64 ):
            row = np.array( (a + 1)**2 - a + b -1 , np.int64 )
            C, m1, m2 = CleGor( l, l, a, b )
            for c in np.arange( 0, len(C), 1, np.int64 ):
                col = int( (m1[c] + l) * (2 * l + 1) + (m2[c] + l) )
                CG[row, col] = C[c,0]
    return CG

def rotation_mat(j, w, th, ph):
    # rotation_mat converts a rotation angle and spherical angles of the rotation
    # axis into the equivalent irrep of SO(3).
    # 
    # Inputs:
    #   j  - specifies dimension of the irrep.
    #   w  - rotation angle in the interval [0, 2 \pi].
    #   th - polar angle of rotation axis in the interval [0, \pi].
    #   ph - aximuthal angle of rotation axis in the interval [0, 2 \pi].
    #
    # Outputs:
    #   U  - (2 j + 1)-dimensional representation of SO(3), using the conventions
    #        established in Eq. 6 on page 81 of D. A. Varshalovich et al, Quantum
    #        Theory of Angular Momentum, 1988. Rows and columns ordered in
    #        increasing values of m' and m.

    tmp = np.tan(w / 2.0) * np.cos(th)
    tmp = (1.0 - 1j * tmp) / np.sqrt(1.0 + tmp**2)
    r_base = 1j * np.exp(-1j * ph) * tmp
    c_base = -1j * np.exp(1j * ph) * tmp

    # force w into [-pi, pi]
    w = np.mod(w + np.pi, 2.0 * np.pi) - np.pi
    xi = 2.0 * np.arcsin(np.sin(w / 2.0) * np.sin(th))

    U = wigner_d(j, xi).astype(np.complex128)  # expected shape (2j+1, 2j+1)

    m = np.arange(-j, j + 1)
    n = 2 * j + 1

    # apply phase factors
    for a in range(n):
        U[a, :] *= r_base**m[a]
        U[:, a] *= c_base**m[a]

    return U

# def sp_null(A, opt=0, TOL=1e-12):
#     """
#     Find null spaces of sparse or dense matrix A.
    
#     Parameters
#     ----------
#     A : array_like or sparse matrix
#         Input matrix.
#     opt : int
#         0 = right null space, 1 = left null space
#     TOL : float
#         Tolerance for singular values.

#     Returns
#     -------
#     N : ndarray
#         Orthonormal basis for the chosen null space.
#     """
#     if opt == 0:
#         N = null_space(A, rcond=TOL)
#     elif opt == 1:
#         N = null_space(A.T, rcond=TOL).T
#     else:
#         raise ValueError("Invalid option. Use 0 for right null space, 1 for left null space.")

#     # zero small values for consistency with MATLAB's cleanup
#     N[np.abs(N) < TOL] = 0.0
#     return N

# # import numpy as np
# # import scipy.sparse as sp
# # import scipy.sparse.linalg as spla
# from scipy.linalg import lu

# def sp_null(A, opt, TOL=1e-12):
#     """
#     Find left or right null space of a sparse matrix A.

#     Parameters
#     ----------
#     A : (m, n) sparse or dense array
#         Input matrix.
#     opt : int
#         0 -> left null space, 1 -> right null space.
#     TOL : float
#         Threshold for considering pivots as significant.

#     Returns
#     -------
#     N : ndarray
#         Left or right null space basis (not orthonormal).
#     """
#     if not sp.isspmatrix(A):
#         A = sp.csr_matrix(A)

#     if opt == 0:
#         # Zero-out tiny entries
#         A = A.tocoo()
#         mask = np.abs(A.data) >= TOL
#         A = sp.coo_matrix((A.data[mask], (A.row[mask], A.col[mask])), shape=A.shape).tocsr()

#         L, U, Q = luq(A, TOL)

#         diagU = np.abs(U.diagonal())
#         r = np.count_nonzero(diagU > TOL)

#         inv_L = np.linalg.inv(L.toarray())  # L is sparse but invert to dense
#         N = inv_L[r:, :]

#         # clean small values
#         N[np.abs(N) < TOL] = 0.0
#         return N

#     elif opt == 1:
#         return sp_null(A.T, 0, TOL).T
#     else:
#         raise ValueError("Invalid option. Use 0 (left) or 1 (right).")


# def luq(A, TOL=1e-12):
#     """
#     Perform LU-like factorization with permutation to construct
#     A = L * U * Q with block-triangular U.

#     Returns
#     -------
#     L : sparse matrix (m x m)
#     U : sparse matrix (m x n)
#     Q : sparse matrix (n x n)
#     """
#     if not sp.isspmatrix(A):
#         A = sp.csr_matrix(A)

#     m, n = A.shape

#     # Dense LU decomposition (SciPy's sparse lu does not expose P, Q in same way)
#     A_dense = A.toarray()
#     P, L, U = lu(A_dense)  # A = P @ L @ U

#     # Convert to A = L * U * Q form
#     if n < m:
#         p = m - n
#         L = np.hstack([L, np.vstack([np.zeros((n, p)), np.eye(p)])])
#         U = np.vstack([U, np.zeros((p, n))])

#     L = P.T @ L
#     Q = np.eye(n)

#     # Identify pivots
#     diagU = np.abs(np.diag(U))
#     p1 = np.where(diagU > TOL)[0]
#     p = len(p1)

#     # Permute rows and columns
#     r2 = np.setdiff1d(np.arange(m), p1)
#     r_perm = np.concatenate([p1, r2])
#     L = L[:, r_perm]
#     U = U[r_perm, :]

#     c2 = np.setdiff1d(np.arange(n), p1)
#     c_perm = np.concatenate([p1, c2])
#     U = U[:, c_perm]
#     Q = Q[c_perm, :]

#     # Update indices
#     p1 = np.arange(p)
#     r2 = np.arange(p, m)
#     c2 = np.arange(p, n)

#     # Eliminate U21 block
#     if p > 0 and r2.size > 0:
#         X = np.linalg.solve(U[p1, p1], U[p1, :][:, c2])
#         U[np.ix_(p1, c2)] = 0.0
#         Q[p1, :] = Q[p1, :] + X @ Q[c2, :]

#         X = np.linalg.solve(U[p1, p1], U[np.ix_(r2, p1)].T).T
#         L[:, p1] = L[:, p1] + L[:, r2] @ X
#         U[np.ix_(r2, p1)] = 0.0
#         U[np.ix_(r2, c2)] -= X @ U[np.ix_(p1, c2)]

#     # Clean up block structure
#     if r2.size > 0 and c2.size > 0:
#         r3 = p + np.where(np.max(np.abs(U[np.ix_(r2, c2)]), axis=1) > TOL)[0]
#         c3 = p + np.where(np.max(np.abs(U[np.ix_(r2, c2)]), axis=0) > TOL)[0]

#         if r3.size > 0 or c3.size > 0:
#             # Recursively decompose U22
#             Lr, Ur, Qr = luq(sp.csr_matrix(U[np.ix_(r3, c3)]), TOL)
#             U[np.ix_(r3, c3)] = Ur
#             L[:, r3] = L[:, r3] @ Lr
#             Q[c3, :] = Qr @ Q[c3, :]

#             q = np.count_nonzero(np.abs(np.diag(U)) > TOL)
#             U = np.block([
#                 [U[:q, :q], np.zeros((q, n - q))],
#                 [np.zeros((m - q, q)), np.zeros((m - q, n - q))]
#             ])
#         else:
#             U[np.ix_(r2, c2)] = 0.0

#     return sp.csr_matrix(L), sp.csr_matrix(U), sp.csr_matrix(Q)

def orth(A):
    """
    Compute an orthonormal basis for the columns of A.
    """
    Q,_,_ = qr(A, mode='economic', pivoting=True)  # 'economic' = reduced QR
    # Q,_ = qr(A, mode='economic')  # 'economic' = reduced QR
    return Q

def complex_real(n):
    # complex_real constructs a sparse matrix that performs the similarity
    # transformation to convert from the complex harmonics to the real
    # harmonics. Rows ordered by increasing l and by increasing m. Columns
    # ordered by increasing l, by increasing m, and by c before s.
    # 
    # Inputs:
    #   n - maximum value of l.
    # 
    # Outputs:
    #   U - sparse matrix that performs the transformation. 

    sqrt2 = np.sqrt(2.0)
    dim = (n + 1) ** 2
    # U = sp.lil_matrix((dim, dim), dtype=complex)
    U = np.zeros((dim, dim), np.complex128)

    for L in range(n + 1):
        row0 = (L + 1)**2 - L - 1  # MATLAB 1-based → Python 0-based
        col0 = (L + 1)**2 - 2*L - 1
        U[row0, col0] = 1j**L

        for M in range(1, L + 1):
            row_minus = row0 - M
            row_plus  = row0 + M
            col1 = col0 + 2*M - 1
            col2 = col0 + 2*M

            U[row_minus, col1] = (-1)**M * (1j)**L / sqrt2
            U[row_plus,  col1] = (1j)**L / sqrt2
            U[row_minus, col2] = (-1)**(M-1) * (1j)**(L-1) / sqrt2
            U[row_plus,  col2] = (1j)**(L-1) / sqrt2

    return U
    # return U.tocsr()

def clean_col(A, a, TOL):
    """
    Zero out small entries in column `a` of matrix A below tolerance TOL.

    % clean_col strips out any real and imaginary components of the entries in
    % A(:, a) with magnitudes below the threshold.

    % Inputs:
    %   A   - matrix containing the column.
    %   a   - column index.
    %   TOL - threshold below which a component is considered insignificant.
    %
    % Outputs:
    %   A   - matrix containing the column. 
    """
    col = A[:, a]
    col[np.abs(col.real) < TOL] = 0.0
    col[np.abs(col.imag) < TOL] = 0.0
    A[:, a] = col
    return A

def clean(A, TOL=1e-12):
    """
    Clean matrix A: normalize columns, remove tiny entries, 
    enforce orthonormality with forward/backward sweep.

    % clean attempts to construct an orthonormal column space for A with the 
    % minimum number of nonzero entries. Assumes that A has full column rank.

    % Inputs:
    %   A   - matrix specifying the column space.
    %   TOL - threshold below which an entry is considered insignificant.
    %
    % Outputs:
    %   A   - matrix whose columns form an orthonormal column space for A.
    """
    m, n = A.shape
    rou = int(-np.log10(TOL))

    # Initial processing
    for a in range(n):
        norm = np.linalg.norm(A[:, a])
        if norm > 0:
            A[:, a] /= norm
        # A = clean_col(A, a, TOL)

    # Forward sweep
    r1 = 0
    for a in range(n):
        # Find column containing most significant entry
        p = 0.0
        while p < TOL and r1 < m:
            r1 += 1
            slice_abs = np.abs(A[r1-1, a:n])
            p_idx = np.argmax(slice_abs)
            p = slice_abs[p_idx]
        b = a + p_idx

        # Should not happen
        if r1 >= m:
            print("A is not full column rank")
            break

        # Swap column into leading position (Swap column a with column b)
        # swap = A[:,a].copy()
        # A[:,a] = A[:,b]
        # A[:,b] = swap
        A[:, [a, b]] = A[:, [b, a]]

        # Make leading entry real
        lead = A[r1-1, a]
        if np.abs(lead) > 0:
            A[:, a] *= np.conj(lead) / np.abs(lead)

        # Cancel leading entries, breaks orthogonality and normality
        cols = np.where(np.abs(A[r1-1, a+1:n]) > TOL)[0] + (a+1)
        for col_idx in cols:
            factor = A[r1-1, col_idx] / A[r1-1, a]
            A[:, col_idx] -= factor * A[:, a]
            # A = clean_col(A, col_idx, TOL)
        # for col_idx in range(a+1, n):
        #     if np.abs(A[r1-1, col_idx]) > TOL:
        #         A[:, col_idx] -= (A[r1-1, col_idx] / lead) * A[:, a]
                # A = clean_col(A, col_idx, TOL)

    # Backward sweep to restore orthonormality
    # Q, _, _ = qr(np.fliplr(A), mode='economic', pivoting=True)
    Q, _ = qr(np.fliplr(A), mode='economic')
    A = np.round(np.fliplr(Q), rou) # this is my "clean_col"

    for a in range(n):
        # A = clean_col(A, a, TOL)
        # Make leading entry positive
        nz = np.flatnonzero(A[:, a])
        if len(nz) > 0:
            A[:, a] *= np.sign(A[nz[0], a])

    return np.round(A, rou)

@njit
def CleGor(j1, j2, J, M):
    # CleGor returns the Clebsch-Gordan coefficients for the specified
    # total angular momenta and coupled z angular momentum component. This form
    # is particularly convenient from a computational standpoint. Follows the
    # approach of W. Straub in viXra:1403.0263.
    # 
    # Inputs:
    #   j1 - first uncoupled total angular momentum.
    #   j2 - second uncoupled total angular momentum.
    #   j  - coupled total angular momentum.
    #   m  - coupled z angular momentum component.
    #
    # Outputs:
    #   C  - all of the nonzero Clebsch-Gordan coefficients for the specified
    #        inputs. Ordered in increasing values of m1.
    #   m1 - first uncoupled z angular momentum components.
    #   m2 - second uncoupled z angular momentum components.
    
    if (J < abs(j1 - j2) or J > j1 + j2 or abs(M) > J):
        # Nothing to do
        # But to the silly list for numba with a type
        ## THis is not working yet, just here to see if jitting helps
        print('asdf')
        # l = List.empty_list(int64)
        # return l, l, l
    else:
        m11 = (M - j1 - j2 + abs(j1 - j2 + M)) / 2
        m1n = (M + j1 + j2 - abs(j1 - j2 - M)) / 2
        
        m1 = np.arange(m11,m1n+1,1,np.float64)
        m2 = M - m1
        
        j_const = j1 * (j1 + 1) + j2 * (j2 + 1) - J * (J + 1)
        
        n = int(m1n - m11 + 1)
        # A is a tridiagonal symmetric matrix
        ## Switched from list to tuple here to enable numba typing
        A = np.zeros( (n, n), np.float64 )
        for a in range(n):
            A[a,a] = j_const + 2 * m1[a] * m2[a]
        for a in range(n-1):
            tmp = np.sqrt(j1 * (j1 + 1) - m1[a] * m1[a+1]) * np.sqrt(j2 * (j2 + 1) - m2[a] * m2[a+1])
            A[a, a + 1] = tmp
            A[a + 1, a] = tmp
        
        # A determines C up to sign and normalization
        ## Here, we have the problem that the la.null_space isn't numba supported, can we switch to 
        ##numpy.linalg.svd?
        # C = la.null_space(A)
        C = nullspace(A)
        C = np.sign(C[n-1]) * C / np.sqrt( np.conj(C.T) @ C )
        return C, m1, m2
    
@njit
def wigner_d(j,tta):
    # wigner_d constructs a Wigner little d matrix given a total angular 
    # momenum and an angle. This corresponds to the irrep of SO(3) for a rotation
    # about the y axis. Follows the approach of X. M. Feng et al in 
    # 10.1103/PhysRevE.92.043307.
    # 
    # Inputs:
    #   j     - specifies dimension of the matrix.
    #   tta   - rotation angle in the interval [0, 2 \pi].
    #
    # Outputs:
    #   d     - Wigner little d matrix, with the rows and columns ordered in
    #           increasing values of m' and m. 

    m = np.arange(-j,j+1)#np.arange(-j,j+1,1,np.int64)
    n = int(2*j+1)

    X = np.sqrt((j + m) * (j - m + 1)) / (2 * 1j)
    # Jy is a tridiagonal Hermitian matrix
    Jy = np.zeros((n, n),np.complex128)#np.zeros([n, n],dtype=complex)
    for a in range(1,n):
        b = n - a - 1
        Jy[a - 1, a] = -X[a]
        Jy[b + 1, b] =  X[a]

    # # Requires that eigenvectors be ordered with increasing eigenvalues
    w,v = np.linalg.eig(Jy)
    w_ord = np.argsort(np.real(w))
    V_temp = v[:,w_ord]
    ## I however need to change to complex here for V and W
    V = V_temp.astype(np.complex128)
    W = np.copy(V)
    for a in range(n):
        W[:, a] = W[:, a] * np.exp(-1j * m[a] * tta)

    d = W @ np.conj(V.T)
    return np.real(d)

@njit
def nullspace(A, atol=1e-13, rtol=1e-13):
    """Compute an approximate basis for the nullspace of A.

    The algorithm used by this function is based on the singular value
    decomposition of `A`.

    Source: https://scipy-cookbook.readthedocs.io/items/RankNullspace.html
        last accessed: 7 June 2023

    Parameters
    ----------
    A : ndarray
        A should be at most 2-D.  A 1-D array with length k will be treated
        as a 2-D with shape (1, k)
    atol : float
        The absolute tolerance for a zero singular value.  Singular values
        smaller than `atol` are considered to be zero.
    rtol : float
        The relative tolerance.  Singular values less than rtol*smax are
        considered to be zero, where smax is the largest singular value.

    If both `atol` and `rtol` are positive, the combined tolerance is the
    maximum of the two; that is::
        tol = max(atol, rtol * smax)
    Singular values smaller than `tol` are considered to be zero.

    Return values
    ------------
    ns : ndarray
        If `A` is an array with shape (m, k), then `ns` will be an array
        with shape (k, n), where n is the estimated dimension of the
        nullspace of `A`.  The columns of `ns` are a basis for the
        nullspace; each element in numpy.dot(A, ns) will be approximately
        zero.
    """

    A = np.atleast_2d(A)
    u, s, vh = np.linalg.svd(A)
    tol = max(atol, rtol * s[0])
    nnz = (s >= tol).sum()
    ns = vh[nnz:].conj().T
    return ns
