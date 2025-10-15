import os
import glob
import numpy as np
from time import time
import sys, shutil
from numba import njit, prange

from .. import numba_plugins as nbp
from . import rotation as rot
from ...config import data_type

def setup_geometry( geo, tomogram, Omega, Kappa ):
    # define sample size and field of view
    fov = np.array( tomogram.shape[1:3], np.int32)
    nVox = np.array( tomogram.shape[:3], np.int32)

    # # convert omega/kappa rotations in lab frame to axis/angle notation via quaternions
    Q_ome = np.column_stack(
            (np.cos(Omega/2),np.outer(np.sin(Omega/2), np.array(geo.inner_axis))))
    Q_kap = np.column_stack(
            (np.cos(Kappa/2),np.outer(np.sin(Kappa/2), np.array(geo.outer_axis))))
    # zer = np.zeros_like(self.Omega)
    # Q_ome = np.column_stack(
    #         (np.cos(self.Omega/2), zer, zer, np.sin(self.Omega/2) ) )
    # #                         , sin(inner_angle)*(0,0,1)
    # Q_kap = np.column_stack(
    #         (np.cos(self.Kappa/2), zer, np.sin(self.Kappa/2), zer ) )
    Q_srot = np.array([rot.quaternion_multiply(qk,qo) for qo,qk in zip(Q_ome,Q_kap)])
    Gs = rot.OTPfromQ(Q_srot)

    # Set up translations of the beam (should make it possible to change directions no?)
    ny = fov[0]
    nz = fov[1]
    ty = np.arange(ny)-ny/2+1/2 # scan from left to right
    tz = np.arange(nz)-nz/2+1/2 # scan up to down

    # voxel coordinates
    xy = np.arange(ny)-ny/2+1/2
    z = np.arange(nz)-nz/2+1/2
    YY,XX,ZZ = np.meshgrid(xy,xy,z)
    Xb = XX.flatten()
    Yb = YY.flatten()
    Zb = ZZ.flatten()
    x_p = np.column_stack([Xb,Yb,Zb]) # voxel coordinates for (omega, kappa) = (0,0)
    return nVox, fov, Gs, ty, tz, x_p

def get_projectors(geo, Gs, sample_shape, voxel_coordinates, mask_voxels, ty, tz, shift_y, shift_z):
    """Calculates the beam intensity in each voxel for each configuration

    Attributes created
    ------------
    tomogram : 1D ndarray, float
        saves the tomogram loaded from the alignment by SASTT
        dim: 0: voxel index
    nVox : int
        number of voxels simulated
    Omega, Kappa : 1D ndarray, float
        sample rotation angles (Euler) for each unique rotation
        dim: 0: rotation index
    Gs : 2D ndarray, float
        sample rotation angles (axis-angle) for each unique rotation
        dim: 0: rotation index, 1: [omega, theta, phi]     
    Ty, Tz : 1D ndarray, float
        y- and z-distance from the central pixel for each translation
        dim: 0: translation index
    t0 : int
        translation index of the central pixel
    x_p : 2D ndarray, float
        array of coordinates of each voxel
        dim: 0: voxel index, 1: [x,y,z]
    p0 : int
        index of the central voxel (rotation center)
    mask_voxels : 1D ndarray, bool
        mask for including the voxel in the analysis or not
        dim: 0: voxel index
    cutoff_low : float
        chosen level below which voxels are masked
    Beams : 3D ndarray, float
        array of X-ray beam intensity in each voxel for each rotation
        and translation state
        dim: 0: rotation, 1: translation, 2: voxel sparse index
    iBeams : 3D ndarray, int
        array of indices for the sparse Beams array
        dim: 0: rotation, 1: translation, 2: voxel sparse index
    """

    TZ,TY = np.meshgrid(tz,ty)
    Ty,Tz = TY.flatten(), TZ.flatten()
    n_trans = Ty.shape[0]
    n_rot = Gs.shape[0]

    print('\tCalculating projectors')
    t0 = time()
    # make sparse arrays for the beams
    beam_precision = 1e-2 # cut all values below this
    Dmax = np.ceil( np.sqrt(sample_shape[0]**2+sample_shape[1]**2+sample_shape[2]**2)/2 )*2 # diagonal of the voxel-cuboid
    lb_max_approx = int(Dmax*10) # this is an estimation for the max No of entries in the sparse direction
    lb_max = 0 # will be eventually stripped to this
    Beams  = np.zeros( (n_rot, n_trans, lb_max_approx), data_type)
    Beam_idcs = np.full((n_rot, n_trans, lb_max_approx), 2**32-1, dtype=np.uint32)
    tau = np.linspace(-Dmax/2, Dmax/2, int(Dmax*2)) # parameter for the beam trajectory
    neighbors = np.transpose(np.indices((3,3,3)) - 1).reshape(-1, 3) # indices of a 3x3x3 cube
    pminmax = np.array([
        [np.min(voxel_coordinates[:,0]), np.max(voxel_coordinates[:,0])],
        [np.min(voxel_coordinates[:,1]), np.max(voxel_coordinates[:,1])],
        [np.min(voxel_coordinates[:,2]), np.max(voxel_coordinates[:,2])]
    ])

    # print('')
    t0=time()
    for g in range(n_rot): # rotations
        # rotated beam direction vector B0 = R(omega,kappa)*(1,0,0)
        B0 = np.array([1,0,0]) @ rot.MatrixfromOTP(Gs[g,0],Gs[g,1],Gs[g,2])

        # make a vector of voxels that are actually touched by the beam
        BB0, TTau = np.meshgrid( B0, tau )
        Bpath0 = np.unique(np.round(BB0*TTau),axis=0) # the closest voxels touched by the untranslated beam

        Bpath0n = np.empty( (Bpath0.shape[0]*27,3), data_type ) # the voxels above plus their neighbors
        for k in range(Bpath0.shape[0]):
            Bpath0n[k*27:(k+1)*27,:] = neighbors + Bpath0[k]
        Bpath0n = np.unique(Bpath0n, axis=0) # drop duplicates
        
        # Calculate beam intensities for every voxel and translation
        Beam_g, Beam_idcs_g = beamtranslations(
                lb_max_approx, geo.Dbeam/geo.Dstep,
                voxel_coordinates, pminmax, mask_voxels,
                B0, Bpath0n,
                Gs[g],
                Ty+shift_y[g], Tz+shift_z[g], 
                beam_precision
            )
        # Beams, iBeams = beamtranslations_full(
        #         lb_max_approx, geo.Dbeam/geo.Dstep,
        #         points_filtered,
        #         B0,
        #         Gs[g],
        #         Ty+self.shifty[g], Tz+self.shiftz[g]
        #     )
        Beam_idcs[g,:,:] = Beam_idcs_g
        Beams[g,:,:] = Beam_g

        lb = max([np.searchsorted(ib,2**32-1) for ib in Beam_idcs[g]])
        lb_max = max(lb,lb_max)
        
        t_it = (time()-t0)/(g+1)
        sys.stdout.write(f'\r\t\tProjection {(g+1):d} / {n_rot:d}, t/it: {t_it:.2f}, t left: {((n_rot-g-1)*t_it/60):.1f} min' )
        sys.stdout.flush()
    
    # strip away voxels without intensity
    Beams = Beams[:,:,:lb_max+1]
    Beam_idcs = Beam_idcs[:,:,:lb_max+1]

    print(f', finished ({(time()-t0)/60:.1f} min)' )
    return Beams, Beam_idcs

@njit(parallel=True)
def beamtranslations_full(
        beam_maxlength, dBeam,
        points,
        beam_direction,
        gs,
        Ty, Tz
    ):
    """ Calculation of beam intensities for one sample orientation
    -- inactive -- maybe this approach could speed up the calculation

    Parameters
    ----------
    beam_maxlength : int
        approximate maximum number of voxels involved in a calculation
    dBeam : float
        beam FWHM relative to the voxel size
    p : 2D ndarray, float
        dim 0: voxel index, 1: [x,y,z]
    mask_voxels : 1D ndarray, bool
        dim 0: voxel index
    B0 : 1D ndarray, float
        beam direction vector at translation 0
    gs : 1D ndarray
        sample orientation (ome,tta,phi)
    Ty, Tz : 1D ndarray, float
        beam translations with a common index
    beam_precition : float
        relative treshold for beam intensity below which values will be cut
    
    Return values
    ------------    
    values, indices
        2 arrays, together forming a sparse array

    """
    # get Gaussian standard deviation from the FWHM
    sigma = dBeam/(2*np.sqrt(2*np.log(2))) 

    # set up sparse arrays
    ntrans = Ty.shape[0]
    Beams  = np.zeros( ( ntrans, beam_maxlength), data_type)
    iBeams = (2**32-1) * np.ones( ( ntrans, beam_maxlength), np.uint32)

    for t in prange(ntrans): # translations
        # rotated translation vector (some point on the beam)
        T = np.array([0,Ty[t], Tz[t]],data_type) @ rot.MatrixfromOTP(gs[0],gs[1],gs[2])
        # get beam intensities for this configuration
        values, idcs = beamintensity(points, T, beam_direction, sigma )
        # save to sparse array
        nb = idcs.size
        Beams[t,:nb] = values
        iBeams[t,:nb] = idcs
    return Beams, iBeams

@njit(parallel=True)
def beamtranslations(
            beam_maxlength, dBeam,
            points, pminmax, mask_voxels,
            B0, Bpath0n,
            gs,
            Ty, Tz,
            beam_precision
        ):
    """ Calculation of beam intensities for one sample orientation

    Parameters
    ----------
    beam_maxlength : int
        approximate maximum number of voxels involved in a calculation
    dBeam : float
        beam FWHM relative to the voxel size
    p : 2D ndarray, float
        dim 0: voxel index, 1: [x,y,z]
    pminmax : 2D ndarray, float
        minimum and maximum voxel position for each dimension
    mask_voxels : 1D ndarray, bool
        dim 0: voxel index
    B0 : 1D ndarray, float
        beam direction vector at translation 0
    Bpath0n : 1D ndarray, int
        beam trajectory at translation 0 in voxel indices
    omega, kappa : float
        rotation angles for this projection
    Ty, Tz : 1D ndarray, float
        beam translations with a common index
    beam_precition : float
        relative treshold for beam intensity below which values will be cut
    
    Return values
    ------------    
    values, indices
        2 arrays, together forming a sparse array

    """
    ntrans = Ty.shape[0]
    Beams  = np.zeros( ( ntrans, beam_maxlength), data_type)
    iBeams = (2**32-1) * np.ones( ( ntrans, beam_maxlength), np.uint32)

    for t in prange(ntrans): # translations
        ty,tz = Ty[t], Tz[t]
        # rotated translation vector
        T = np.array([0,ty,tz],data_type) @ rot.MatrixfromOTP(gs[0],gs[1],gs[2])

        # translated beam direction vector (actually just a point on the beam)
        B = B0 + T

        # translated voxel indices supposedly touched by the beam
        Bpath = Bpath0n + T   
        # filter out voxels outside the sample
        insample = (
            (Bpath[:,0] >= pminmax[0,0] )&
            (Bpath[:,1] >= pminmax[1,0] )&
            (Bpath[:,2] >= pminmax[2,0] )&
            (Bpath[:,0] <= pminmax[0,1] )&
            (Bpath[:,1] <= pminmax[1,1] )&
            (Bpath[:,2] <= pminmax[2,1] )
        )
        Bpath = Bpath[insample]

        # voxel indices of the path points
        ib0 = (
            np.floor(Bpath[:,0]-pminmax[0,0])*(pminmax[1,1]-pminmax[1,0]+1)*(pminmax[2,1]-pminmax[2,0]+1) + \
            np.floor(Bpath[:,1]-pminmax[1,0])  *(pminmax[2,1]-pminmax[2,0]+1) + \
                np.ceil(Bpath[:,2]-pminmax[2,0]) 
            ).astype(np.uint32)                                                                        

        # filter out filled voxels by mask
        ib_msk = np.intersect1d(ib0,mask_voxels)

        # coordinates of voxels on the path
        p_path = points[ib_msk]

        # distance to beam normal to beam direction (https://mathworld.wolfram.com/Point-LineDistance3-Dimensional.html)
        w = np.empty( p_path.shape[0], data_type )
        for k in range(p_path.shape[0]):
            w[k] = np.linalg.norm(np.cross((p_path[k]-T),(p_path[k]-B)))/np.linalg.norm(B-T)

        # cumulative gaussian distribution in function of the distance from the beam
        sigma = dBeam/(2*np.sqrt(2*np.log(2))) # if dBeam is the FWHM
        beam = 1/2 * ( nbp.nb_erf( (1/2+w)/(np.sqrt(2)*sigma) ) + nbp.nb_erf( (1/2-w)/(np.sqrt(2)*sigma) ) )

        # cut away small values
        ib2 = (beam>=beam_precision)
        ib = ib_msk[ib2]
        nb = ib.shape[0] # effective number of touched voxels
        Beams[t,:nb] = beam[ib2]
        iBeams[t,:nb] = ib
    return Beams, iBeams

@njit
def beamintensity( points, beam_center, beam_direction, sigma, threshold=0.01 ):
    """Calculates a gaussian beam intensity for a given rotation and translation
    defined by the vectors beam_center (arbitrary point on the beam path) and 
    beam_direction. Values are unnormalized and cut at the value treshold.
    They are returned as sparse array, the second returned array are the indices
    which link the values to the points.

    Parameters
    ----------
    points : ndarray
        dim 0: voxel index, 1: [x,y,z]    beam_center : ndarray
    beam_direction : ndarray
        point in 3D
    sigma : float
        beam width (gaussian standard deviation)
    threshold : float, optional
        lowest value entering in the sparse array, by default 0.01

    Returns
    -------
    values, indices
        2 arrays, together forming a sparse array
    """
    beam_direction = beam_direction / np.linalg.norm(beam_direction)

    # Project each point onto the plane using the normal
    # Compute the vector from center to each point
    r = points - beam_center
    # Distance from each point to the plane
    dist_to_plane = np.dot(r, beam_direction)
    # Project onto the plane
    proj = points - np.outer(dist_to_plane, beam_direction)

    # Now compute local coordinates (u,v) in the plane to define the 2D Gaussian
    # We need two orthonormal vectors in the plane
    def orthonormal_basis(n):
        # Choose a vector not parallel to n
        if abs(n[0]) < 0.9:
            other = np.array([1, 0, 0])
        else:
            other = np.array([0, 1, 0])
        u = np.cross(n, other)
        u /= np.linalg.norm(u)
        v = np.cross(n, u)
        return u, v

    u_vec, v_vec = orthonormal_basis(beam_direction)
    # Compute coordinates in plane
    u_coords = np.dot(proj - beam_center, u_vec)
    v_coords = np.dot(proj - beam_center, v_vec)

    # Evaluate 2D Gaussian on the plane
    # gaussian = (1 / (2 * np.pi * sigma**2)) * np.exp(-(u_coords**2 + v_coords**2) / (2 * sigma**2))
    gaussian = np.exp(-(u_coords**2 + v_coords**2) / (2 * sigma**2))

    # cut away small values
    indices = np.where(gaussian > threshold)[0]
    # nb = ib.shape[0] # effective number of touched voxels
    # Beams[t,:nb] = beam[ib2]
    # iBeams[t,:nb] = ib
    return gaussian[indices], indices