import numpy as np
from numba import njit, prange

from ..model import rotation as rot
from .. import numba_plugins as nb
from ..analysis import orix_plugins as orx
from ..model import symmetries as sym
from ...config import data_type

def get_odf( coefficients, G_odf, symmetry, resolution ):
    Q_odf = rot.QfromOTP(G_odf)
    Q_grid, Q_group = setup_gridbased(symmetry, resolution)
    return odf( coefficients, Q_odf, Q_grid, Q_group, resolution )


def get_odf_batch( coefficients_batch, G_odf, symmetry, resolution ):
    Q_odf = rot.QfromOTP(G_odf)
    Q_grid, Q_group = setup_gridbased(symmetry, resolution)
    odf_batch = np.empty( (coefficients_batch.shape[0], Q_odf.shape[0]) )
    for c, coefficients in enumerate(coefficients_batch):
        odf_batch[c] = odf( coefficients, Q_odf, Q_grid, Q_group, resolution )

    return odf_batch

@njit
def odf( coefficients, Q_odf, Q_grid, Q_group, std, cutoff=1e-2 ):
    odf = np.zeros_like(Q_odf[:,0])
    for c in range(coefficients.size):
        if coefficients[c] > coefficients.max()*cutoff:
            odf += gaussian_SO3( Q_odf, Q_grid[c], std, Q_group )
            # odf += fisher_SO3( Q_odf, Q_grid[c], kappa, Q_group)
    return odf

def setup_gridbased( symmetry, resolution ):
    pg = getattr( orx.osym, sym.get_SFnotation( symmetry ) )
    Q_grid = rot.get_sample_fundamental(
                    resolution,
                    point_group= pg,
                    method='cubochoric'
            ).data.astype(data_type)
    
    # Q_grid = rot.QfromOTP(np.array([[0,0,0], [np.pi/2,np.pi/2,np.pi/2]]))
    # resolution = 10

    generators = sym.generators(symmetry)
    q_gen = rot.QfromOTP(generators)
    Q_group = rot.generate_group(q_gen)

    return Q_grid, Q_group

@njit(parallel=True)
def get_odf_max_orientations( Coefficients, Q_odf, Q_grid, Q_group, kappa ):
    Q_max = np.empty( (Coefficients.shape[0], 4), data_type )
    for v in prange(Coefficients.shape[0]):
        odf = odf( Coefficients[v], Q_odf, Q_grid, Q_group, kappa )
        Q_max[v] = Q_odf[np.argmax(odf)]
    return Q_max

@njit
def fisher_SO3(Q, q_mean, kappa, Q_group): 
    """
    von Mises-Fisher distribution on fundamental zone (fz)

    Parameters
    --------
    Q : 2d ndarray, float
        array of unit quaternions representing orientations
    q_mean: 1d ndarray, float 
        mean orientation as quaternion
    kappa: float
        concentration parameter for von Mises-Fisher distribution (~1/sigma^2) ! this value seems not correct
    Q_group: 2d ndarray, float
        array of unit quaternions with all symmetry operations of the point group
    
    Returns:
    ------------
    odf: 1d ndarray, float
        non-normalized probabilty density for each quaternion
    """
    # We put multiple (mises-fisher) bell functions on the unit quaternion sphere
    # One on every symmetry equivalent q_mu
    # Evaluate the sum of these on orientations Q
    q_mean_equivalents = rot.symmetry_equivalent_quaternions(q_mean,Q_group)
    # q_mu_equivalents = np.atleast_2d(q_mu) # this is to show what happens if you use only q_mu

    # calculate odf as a sum of distributions from equivalents
    odf = np.zeros((q_mean_equivalents.shape[0],Q.shape[0]), dtype=data_type)
    for i in range(q_mean_equivalents.shape[0]):
        mux = np.abs( q_mean_equivalents[i] @ Q.T )
        odf[i]= np.exp(kappa * (mux - 1))
    odf = np.sum(odf, axis=0)# / np.exp(kappa)
    return odf

@njit
def gaussian_SO3(Q, q_mean, std, Q_group): 
    """
    Normal-like distribution

    Parameters
    --------
    Q : 2d ndarray, float
        array of unit quaternions representing orientations
    q_mean: 1d ndarray, float 
        mean orientation as quaternion
    std: float
        standard deviation in radians
    Q_group: 2d ndarray, float
        array of unit quaternions with all symmetry operations of the point group
    
    Returns:
    ------------
    odf: 1d ndarray, float
        non-normalized probabilty density for each quaternion
    """
    
    dQ = rot.misorientation_angle_stack(Q, nb.nb_full(Q.shape,q_mean), Q_group)
    odf = np.exp( - dQ**2/(2*std**2) )

    return odf

@njit(parallel=True)
def get_rotated_diffractlets(Qc, Qs, Q_grid, Q_group, kappa, I_single_crystal, detShape ):
    difflets_rot = np.empty( (Qs.shape[0], Q_grid.shape[0], *detShape), data_type )
    # s,gr=0,0
    for s in prange(Qs.shape[0]):
        for gr in range(Q_grid.shape[0]):
            q_mean = rot.quaternion_multiply( Qs[s], Q_grid[gr] )
            odf = fisher_SO3( Qc, q_mean, kappa, Q_group )
            # sparse calculate the projections (only points in odf that are high)
            diff_pattern = np.zeros(detShape, data_type)
            idcs_odf = np.nonzero( odf > 0.01 * odf.max() )[0] # cut small values of the odf
            for h in idcs_odf:
                diff_pattern += I_single_crystal[h] * odf[h]
            difflets_rot[s,gr] = diff_pattern
    return difflets_rot





# @njit
# def gaussian_3d( Q, q_mu, std, gen, dV=1 ):
#     """
#     Gauss bell on FZ
#     Parameters
#     --------
#     Q : 2d ndarray, float
#         array of unit quaternions representing orientations
#     mu: 1d ndarray, float 
#         mean orientation as quaternion
#     std: float
#         standard deviation - sigma
#     gen: 2d ndarray, float
#         OTP of the two generators for the point group symmetries
#         dim0: generators, dim1: OTP
    
#     Returns:
#     ------------
#     odf: 1d ndarray, float
#         non-normalized probabilty (mass) for each of the orientations g
#     """
#     # for omega_mu = 0, then dg is omega
#     dg = rot.ang_distance(Q, nb.nb_full(Q.shape,q_mu), gen)
#     odf = np.exp( - dg**2/(2*std**2) )
#     return odf #/( odf @ dV ) Does not return a valid pmf at the moment

# from .misc import integrate_c
# from numba import prange
# # @njit(parallel=True)
# def projection( g, Qc, Isc, gen, Q_mu, c_sample, kappa, Qs, Beams, iBeams, detShape, dV ):
#     diff_patterns_g = np.empty((Beams.shape[1],detShape[0],detShape[1]), data_type)
#     for t in prange(Beams.shape[1]):
#         # project the coefficients
#         iend = np.searchsorted(iBeams[g,t,:],2**32-1) # for sparsearray
#         c_proj = integrate_c( Beams[g,t,:iend], iBeams[g,t,:iend], c_sample )
#         # get the resulting odf from rotated mu
#         odf_proj = np.zeros( Qc.shape[0], data_type )
#         idcs_basis = np.nonzero(c_proj > 0.01 * c_proj.max())[0]
#         for c in idcs_basis:
#             q_mu = rot.quaternion_multiply(  Q_mu[c], Qs[g] )
#             odf_proj += c_proj[c] * fisher_SO3(Qc, q_mu, kappa, gen, dV )
#         # sparse calculate the projections (only points in odf that are high)
#         diff_pattern = np.zeros(Isc.shape[1], data_type)
#         idcs_odf = np.nonzero(odf_proj> 0.01 * odf_proj.max())[0]
#         for h in idcs_odf:
#             diff_pattern += Isc[h] * odf_proj[h]
#         diff_patterns_g[t] = diff_pattern.reshape((detShape[0],detShape[1]))
#     return diff_patterns_g



