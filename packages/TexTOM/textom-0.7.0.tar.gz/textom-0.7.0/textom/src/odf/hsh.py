import numpy as np
from scipy import special as sp
from numba import njit, prange
import math
import os, sys

from .hsh_symmetrization import HSH_symmetrization_matrix, R
from .. import handle as hdl
from ...config import data_type

class odf:
    def __init__(self, n_max, symmetry, orientation_grid):
        """Initializes a model to calculate Orientation Distribution Functions from 
        HyperSpherical Harmonics

        Parameters
        ----------
        n_max : int
            highest order of the harmonics expansion
        symmetry : str
            proper point group in notation
        orientation_grid : ndarray, shape(n,3)
            array of orientations in OTP notation
        """
        print('\tInitializing hyperspherical harmonics model')
        self.odf_mode = 'hsh'
        self.n_max = n_max
        self.symmetry = symmetry
        self.orders = get_orders( symmetry, n_max, info=True )
        self.G_odf = orientation_grid
        # Properties to be initialized when needed:
        self._basis_functions = None
        self._symmetrization_matrix = None
        self._slices_hsh = None
        self._slices_shsh = None

    @property
    def slices_shsh( self ):
        if self._slices_shsh is None:
            # Number sHSHs for each n
            n_sHSHs  =  np.array( [get_NsHSH(self.symmetry,n) for n in self.orders] ) 
            self._slices_shsh = np.array(
                [ [ n_sHSHs[:k].sum(), n_sHSHs[:k+1].sum() ] 
                    for k in range(n_sHSHs.shape[0]) ]) # 'slices' of coefficients as numbers for each n
        return self._slices_shsh

    @property
    def slices_hsh( self ):
        if self._slices_hsh is None:
            n_HSHs = np.array([(n+1)**2 for n in self.orders])
            self._slices_hsh = np.array(
                [ [ n_HSHs[:k].sum(), n_HSHs[:k+1].sum() ] 
                    for k in range(n_HSHs.shape[0]) ]) # 'slices' of coefficients as numbers for each n
        return self._slices_hsh
    
    @property
    def symmetrization_matrix( self ):
        if self._symmetrization_matrix is None:
            # calculate the matrix that transforms HSHs to sHSHs
            # Xsn = HSH_symmetrization_matrix(np.max(orders), symmetry)
            self._symmetrization_matrix = {'0': np.array([[1.]], np.complex128)}
            for n in self.orders[1:]:
                _, csym = cSymmHSH(self.symmetry, n) # get sSHSs and orders
                self._symmetrization_matrix[str(n)] = csym

            # X_new = HSH_symmetrization_matrix(self.n_max, self.symmetry)
            # stop=1
            # self.symmetrization_matrix, self.slices_hsh, self.slices_shsh
        return self._symmetrization_matrix

    @property
    def basis_functions(self):
        if self._basis_functions is None:
            print('\t\tCalculating sHSH basis functions')
            # first calculate the HSHs, then symmetrize, then sum over coefficients
            n_hsh = self.slices_hsh[-1,1]
            n_shsh = self.slices_shsh[-1,1]

            nlm = np.empty((n_hsh, 3), dtype=np.int64)
            idx = 0
            for n in self.orders:
                for l in range(n+1):
                    for m in range(-l, l+1):
                        nlm[idx, 0] = n
                        nlm[idx, 1] = l
                        nlm[idx, 2] = m
                        idx += 1

            hsh_basis = Z_all_parallel(self.G_odf, nlm)
            
            self._basis_functions = np.empty((n_shsh, self.G_odf.shape[0]))
            for i_n, n_str  in enumerate(self.symmetrization_matrix.keys()):
                self._basis_functions[self.slices_shsh[i_n,0]:self.slices_shsh[i_n,1]] = np.real(
                    self.symmetrization_matrix[n_str] @ hsh_basis[self.slices_hsh[i_n,0]:self.slices_hsh[i_n,1]])
        return self._basis_functions

    def get_odf( self, coefficients ):
                
        return coefficients @ self.basis_functions

    def get_odf_batch( self, coefficients_batch ):
        
        odf_batch = odf_batch_parallel(coefficients_batch.astype(data_type), self.basis_functions.astype(data_type))

        # odf_batch = np.empty( (coefficients_batch.shape[0], G_odf.shape[0]) )
        # for c, coefficients in enumerate(coefficients_batch):
        #     odf_batch[c] = coefficients @ shsh_basis

        return odf_batch

    def get_odf_centered( self, coefficients ):

        odf = coefficients @ self.basis_functions
        g_mu = self.G_odf[ np.argmax(odf) ]

        c_centered = np.empty_like(coefficients)
        c_centered[0] = coefficients[0]
        for n in range(1,self.orders.size):
            order = self.orders[n]
            R_centering = Rs_n( np.array([-g_mu[0], g_mu[1], g_mu[2]], np.float64),
                                        order, self.symmetrization_matrix[str(order)] )
            c_centered[self.slices_shsh[n,0]:self.slices_shsh[n,1]] = R_centering @ coefficients[self.slices_shsh[n,0]:self.slices_shsh[n,1]]

        return c_centered @ self.basis_functions

    def get_odf_centered_batch( self, coefficients_batch, mean_orientations ):

        C_centered = np.empty_like(coefficients_batch)
        C_centered[:,0] = coefficients_batch[:,0]
        for n in range(1,self.orders.size):
            order = self.orders[n]
            C_centered[:, self.slices_shsh[n,0]:self.slices_shsh[n,1]] = rotate_coefficients_n_parallel(
                np.column_stack( (-mean_orientations[:,0], mean_orientations[:,1], mean_orientations[:,2]) ).astype(np.float64),
                coefficients_batch[:,self.slices_shsh[n,0]:self.slices_shsh[n,1]].astype(np.float64), order, 
                self.symmetrization_matrix[str(order)])


            # R_centering = Rs_n_stack( np.column_stack( (-G_mu[:,0], G_mu[:,1], G_mu[:,2]) ).astype(np.float64),
            #                             order, symmetrization_matrix[str(order)] )
            # for v in range(C_centered.shape[0]):
            #     C_centered[v, slices[n,0]:slices[n,1]] = R_centering[v] @ coefficients_batch[v,slices[n,0]:slices[n,1]]

        odf_batch = odf_batch_parallel(C_centered.astype(data_type), self.basis_functions.astype(data_type))

        # odf_batch = np.empty( (coefficients_batch.shape[0], G_odf.shape[0]) )
        # for c, coefficients in enumerate(C_centered):
        #     odf_batch[c] = coefficients @ shsh_basis

        return odf_batch

@njit(parallel=True)
def odf_batch_parallel( coefficients_batch, shsh_basis ):
    odf_batch = np.empty((coefficients_batch.shape[0],shsh_basis.shape[1]))
    for c in prange(coefficients_batch.shape[0]):
        odf_batch[c] = coefficients_batch[c] @ shsh_basis
    return odf_batch

@njit(parallel=True)
def rotate_coefficients_n_parallel(G_rot, C, order, symmetrization_matrix):
    C_rotated = np.empty_like(C)
    for v in prange(C.shape[0]):
        R_centering = Rs_n( G_rot[v], order, symmetrization_matrix )
        C_rotated[v] = R_centering @ C[v]
    return C_rotated

def mason_kernel(c, ns, slices, K):
    """Applies the Mason kernel on the HSH coefficients

    J. K. Mason and O. K. Johnson, ?Convergence of the hyperspherical 
    harmonic expansion for crystallographic texture,? J Appl Crystallogr, 
    vol. 46, no. 6, pp. 1722?1728, Dec. 2013, doi: 10.1107/S0021889813022814.

    Parameters
    ----------
    c : 1D ndarray, float
        set of sHSH coefficients
    ns : 1D ndarray, int
        used orders
    slices : 2D ndarray, int
        indices for finding the orders in the c-array
    K : float
        HSH damping factor to ensure positivity, usually 1 to 2
        
    Return values
    ------------
    c : 1D ndarray, float
        set of modified sHSH coefficients
    """
    for k, Sn in enumerate(slices):
        c[Sn[0]:Sn[1]] = ( 1- ns[k]/(ns[-1]+1) )**K * c[Sn[0]:Sn[1]]

    return c
    
def get_order_weights(c, ns, slices):
    """ Evaluate the contributions from each order to the ODF """
    print('Coefficient weights sum(c^2):')
    weights = []
    for k, Sn in enumerate(slices):
        weights.append( (c[Sn[0]:Sn[1]]**2).sum() )
        print( '\tOrder %d: %.4f' % (ns[k], weights[k]))
    return np.array(weights)

"""
Functions to calculate and rotate hyperspherical harmonics
"""
# Original Matlab code:
# Copyright 2019 Jeremy Mason
#
# Licensed under the Apache License, Version 2.0, <LICENSE-APACHE or
# http://apache.org/licenses/LICENSE-2.0> or the MIT license <LICENSE-MIT or
# http://opensource.org/licenses/MIT>, at your option. This file may not be
# copied, modified, or distributed except according to those terms.
#
# Rewritten in python by Moritz Frewein 2025

def Z( omega,theta,phi, n,l,m ):
    """Compute the hyperspherical harmonic function Z^n_{l,m}

    This function is used to construct orientation distribution functions
    for axis-angle rotations. theta and phi are the polar and azimutal
    angles, respectively, defining the rotation axis. omega is the rotation
    angle.
    The function uses the scipy package to compute factorials, Gegenbauer
    polynomials and Associated Legendre functions.

    Source: Mason, J.K., and C.A. Schuh. Acta Materialia 56, no. 20 
        (December 2008): 6141?55. https://doi.org/10.1016/j.actamat.2008.08.031.

    Parameters
    ----------
    omega : ndarray, float
        rotation angle, usually ?[0,pi)
    theta : ndarray, float
        polar angle of the rotation axis, usually ?[0,pi)
    phi : ndarray, float
        azimutal angle of the rotation axis, usually ?[0,2pi)
    n, l, m : int/float
        Indices of the hyperspherical harmonic function
        Usually integer or half-integer, with the conditions:
            n >= 0
            l <= n
            -l <= m <= l

    Return values
    ------------
    Z : ndarray, complex
        returns values on the complex plane with |Z| <= 1
    """
    
    #Check indices
    if n < 0:
        print('n smaller than zero, check that!, n= ',n)
    elif l < 0:
        print('l smaller than zero, check that!, l= ',l)
    elif l > n:
        print(' l larger than n, check that!, l= ',l,' n= ',n)
    elif m < l*-1:
        print ('m smaller than -l, check that!, m = ',m,' -l ',l*-1)
    elif m > l:
        print ('m larger than l, check that!, m= ',m,' l= ',l)

    Z = (-1j)**l * 2**(l+0.5) * sp.factorial(l) / (2*np.pi) * \
        np.sqrt( (2*l+1) * sp.factorial(l-m) * (n+1) * sp.factorial(n-l) / \
        ( sp.factorial(l+m) * sp.factorial(n+l+1) ) ) * \
        (np.sin(omega/2))**l * sp.eval_gegenbauer(n-l,l+1,np.cos(omega/2)) * \
        sp.lpmv(m,l,np.cos(theta)) * np.exp(1j*m*phi)
    
    return Z

### Test to check if Z and Z_numba_array are the same
# from textom.src import hsh
# import numpy as np
# n_points = 100
# test_omega = np.pi * np.random.rand(n_points)
# test_theta = np.pi * np.random.rand(n_points)
# test_phi = 2*np.pi * np.random.rand(n_points)
# old_Z = hsh.Z(test_omega,test_theta,test_phi, 4,3,2)
# new_Z = hsh.Z_numba_array(test_omega,test_theta,test_phi, 4,3,2)
# print(f'maximum deviation: {np.max(np.abs(old_Z - new_Z))}') # was about 1e-15
###

@njit(parallel=True)
def Z_all_parallel(orientations, nlm):
    n_hsh = nlm.shape[0]
    hsh_basis = np.empty((n_hsh, orientations.shape[0]), np.complex128)
    for z in prange(n_hsh):
        for i in range(orientations.shape[0]):
            hsh_basis[z,i] = Z_numba( orientations[i,0], orientations[i,1], orientations[i,2], 
                                     nlm[z,0], nlm[z,1], nlm[z,2] )
    return hsh_basis

@njit
def Z_numba(omega, theta, phi, n, l, m):
    """
    Numba-friendly version of Z.
    All inputs are scalars. n,l,m are integers with n>=l>=0 and |m|<=l.
    Returns complex128.
    """
    # sanity (no Python exceptions in njit; keep cheap guards)
    if l < 0 or n < 0 or l > n or abs(m) > l:
        return np.nan + 0j

    # pieces
    half_omega = 0.5 * omega
    s = np.sin(half_omega)
    c_half = np.cos(half_omega)
    ct = np.cos(theta)

    # (-1j)**l
    p_neg_i = pow_neg_i(l)

    # real prefactor before special functions
    # 2**(l+0.5) * fac(l) / (2*pi)
    ln_fac_l = ln_factorial(l)
    ln_pref_real = (l + 0.5) * np.log(2.0) + ln_fac_l - np.log(2.0 * np.pi)
    pref_real = np.exp(ln_pref_real)

    # sqrt( (2l+1) * fac(l-m) * (n+1) * fac(n-l) / ( fac(l+m) * fac(n+l+1) ) )
    ln_num = np.log(2.0 * l + 1.0) \
             + ln_factorial(l - abs(m)) \
             + np.log(n + 1.0) \
             + ln_factorial(n - l)
    ln_den = ln_factorial(l + abs(m)) + ln_factorial(n + l + 1)
    ln_ratio = 0.5 * (ln_num - ln_den)
    sqrt_ratio = np.exp(ln_ratio)

    # (sin(omega/2))**l
    sin_pow = s ** l if l > 0 else 1.0

    # Gegenbauer: C_{n-l}^{(l+1)}(cos(omega/2))
    C = gegenbauer_C(n - l, l + 1.0, c_half)

    # Associated Legendre: P_l^m(cos(theta))
    P = associated_legendre_P(l, m, ct)

    # exp(i m phi)
    e_imphi = np.cos(m * phi) + 1j * np.sin(m * phi)

    # assemble
    out = p_neg_i * (pref_real * sqrt_ratio) * sin_pow * C * P * e_imphi
    return out

# ---------- helpers (nopython-safe) ----------

@njit
def pow_neg_i(l):
    # (-1j)**l cycles every 4
    r = l % 4
    if r == 0:
        return 1.0 + 0.0j
    elif r == 1:
        return 0.0 - 1.0j
    elif r == 2:
        return -1.0 + 0.0j
    else:
        return 0.0 + 1.0j

@njit
def ln_factorial(n):
    # ln(n!) via lgamma
    return math.lgamma(n + 1.0)

@njit
def gegenbauer_C(n, alpha, x):
    # C_n^{(alpha)}(x), n>=0, alpha>0
    if n == 0:
        return 1.0
    if n == 1:
        return 2.0 * alpha * x
    Cnm2 = 1.0
    Cnm1 = 2.0 * alpha * x
    for k in range(1, n):
        # k goes 1..n-1 to produce C_{k+1}
        kp1 = k + 1.0
        num = 2.0 * (k + alpha) * x * Cnm1 - (k + 2.0 * alpha - 1.0) * Cnm2
        Cn = num / kp1
        Cnm2 = Cnm1
        Cnm1 = Cn
    return Cnm1

@njit
def associated_legendre_P(l, m, x):
    """
    Unnormalized associated Legendre P_l^m(x) with Condon-Shortley phase.
    l>=0, |m|<=l, x in [-1,1]
    """
    if m < 0:
        # P_l^{-m} = (-1)^m (l-m)!/(l+m)! P_l^{m}
        mp = -m
        Plmp = associated_legendre_P(l, mp, x)
        sign = -m
        ln_ratio = ln_factorial(l - mp) - ln_factorial(l + mp)
        return ((-1.0)**mp) * np.exp(ln_ratio) * Plmp

    # m >= 0 from here
    # P_m^m(x) = (-1)^m (2m-1)!! (1-x^2)^{m/2}
    # use logs: (2m-1)!! = 2^m * Gamma(m+1/2) / sqrt(pi)
    if m == 0:
        Pmm = 1.0
    else:
        ln_double_fact = m * np.log(2.0) + math.lgamma(m + 0.5) - 0.5 * np.log(np.pi)
        ln_base = 0.5 * m * np.log(max(0.0, 1.0 - x * x))
        Pmm = ((-1.0)**m) * np.exp(ln_double_fact + ln_base)

    if l == m:
        return Pmm

    # P_{m+1}^m(x) = x (2m+1) P_m^m(x)
    Pm1m = x * (2.0 * m + 1.0) * Pmm
    if l == m + 1:
        return Pm1m

    # upward recurrence for l >= m+2
    Plm2 = Pmm
    Plm1 = Pm1m
    for ell in range(m + 2, l + 1):
        num = (2.0 * ell - 1.0) * x * Plm1 - (ell + m - 1.0) * Plm2
        Pl = num / (ell - m)
        Plm2 = Plm1
        Plm1 = Pl
    return Plm1

# -------------------------------------------------------------
@njit
def Rs_n_stack( Gs, n, Xsn ):
    ''' calculates sHSH rotation matrices for all rotation Gs and order n
    '''
    Rs_stack = np.zeros( (Gs.shape[0], Xsn.shape[0], Xsn.shape[0]), np.float64 )
    for g in range(Gs.shape[0]):
        Rs_stack[g] = Rs_n( Gs[g], n, Xsn )
    
    return Rs_stack

@njit
def Rs_n( g, n, Xsn ):
    ''' calculates a single sHSH rotation matrix for a rotation g and order n
    '''
    rot_HSH = R( n, g, np.array([0.,0.,0.]) ) # this is the HSH rotation matrix
    rot_sHSH = np.real( np.conj( Xsn ) @ rot_HSH @ Xsn.T ) # here it's converted to sHSH
    return rot_sHSH


############################################################################################
############################################################################################
### helper functions to access hsh arrays
def get_idx(n,l,m,ns):
    ## input: 
    # n,l,m     desired n,l and m values, e.g. 2,2,0
    # ns        used n's in ascending order, e.g. [0,2,4]
    ## output:
    # idx       index of the coefficient in a 1D array
    
    npos = np.where(ns==n)[0][0]
    ## needed to unroll that one np.sum([2*ll+1 for ll in range(l)])
    idx_temp = 0
    for ll in range(l):
        idx_temp = idx_temp+2*ll+1
    idx = npos + idx_temp + l + m
    return int(idx)

def get_nlm(idx,ns):
    ## input: 
    # idx       index of the coefficient in a 1D array
    # ns        used n's in ascending order, e.g. [0,2,4]
    ## output:
    # n,l,m     corresponding n,l and m values, e.g. 2,2,0

    Ln = [(n+1)**2 for n in ns] # number of unique combinations [l,m] for every n
    Ll = [2*l+1 for l in range(np.max(ns)+1)] # number of m for every l
    ni = 0
    while idx > np.sum(Ln[:ni+1])-1:
        ni += 1
    l = 0
    while idx > np.sum(Ln[:ni]) + np.sum(Ll[:l+1])-1:
        l += 1
    m = idx - np.sum(Ln[:ni]) - np.sum(Ll[:l]) - l
    return ns[ni],l,int(m)

def cSymmHSH(point_group, n):
    """Loads a matrix to transform HSHs to sHSHs

    loads sets of coefficients that make the hyperspherical 
    harmonic expansion invariant a certain crystal symmetry. 
    These can  be interpreted as defining a compact basis
    for an orientation distribution obeying the required symmetry, 
    namely, the symmetrized hyperspherical harmonics (sHSHs).

    This function loads from files created separately by Matlab
    functions in ressources/symmetrizedHSH

    Parameters
    ----------
    proper_point_group : str
        name of the crystal symmetry, taken from a provided table
    n : int
        order of the HSHs

    Return values
    ------------
    nlm : ndarray, int
        HSH indices corresponding to the coefficients
    c : 2D ndarray, complex
        matrix of HSH coefficients for all sHSHs for given n and lattice
        dimensions: 0: HSH orders, 1: sHSHs
    """

    path_csym = hdl.get_file_path('textom',
            os.path.join('ressources','symmetrizedHSH','output',
                         point_group + '_n' + str(n)))
    # filename = 'ressources/symmetrizedHSH/output/' + point_group + '_n' + str(n)
    if os.path.isfile(path_csym):
        data = np.genfromtxt(
            path_csym,
            dtype=np.complex128,
            skip_header=1,
            skip_footer=0,
        )
        
        nlm = data[:,:3].real.astype(int)
        c = data[:,3:].T
        return nlm, c
    
    else:
        print('Symmetrized HSH base file does not exist. Check for typos or generate it via matlab files')
        sys.exit(1)

def get_NsHSH(point_group, n):
    """ Returns how many sHSHs exist for the respective point group and order

    Parameters
    ----------
    point_group : str
        name of the crystal symmetry, taken from a provided table
    n : int
        order of the HSHs
    """
    if np.mod(n,2):
        return 0
    elif n==0:
        return 1
    else:
        path_overview = hdl.get_file_path('textom',
            os.path.join('ressources','symmetrizedHSH','output','overview.txt'))
        with open(path_overview, "r") as file:
                NsHSH_all = eval( file.read() )[point_group]
        return NsHSH_all[int(n/2-1)]


def get_orders( symmetry, n_max = 20, info=True, exclude_ghosts=True ):
    ''' Gives the allowed orders up to n_max
    
    Parameters
    ----------
    n_max : int
        maximum HSH order used
    info : bool
        if True, the list of how many sHSHs exist at each order is printed
    
    Return values
    ------------
    n_allowed : ndarray, int
        orders where sHSHs exist for this point group
    '''
    if info:
        print('\t\torder\tNo of symmetrized HSHs')
    n_allowed = [0]
    for n in range(1,n_max+1):
        Nn = get_NsHSH(symmetry,n)
        if exclude_ghosts and (not n%2) and (n%4): # condition for ghosts
            ghost = f' ({Nn} ghosts)'
            Nn = 0
        else:
            ghost = ''
        if info and Nn > 0:
            print('\t\t%u\t %u%s' % (n, Nn, ghost) )
        if Nn > 0:
            n_allowed.append(n)
    return np.array(n_allowed)
        
def get_order_slices(max_order, symmetry):
    orders = get_orders( symmetry, max_order, info=False )
    n_sHSHs  =  np.array( [get_NsHSH(symmetry,n) for n in orders] ) 

    slices_hsh = np.array(
        [ [ n_sHSHs[:k].sum(), n_sHSHs[:k+1].sum() ] 
            for k in range(n_sHSHs.shape[0]) ]) # 'slices' of coefficients as numbers for each n
    return slices_hsh