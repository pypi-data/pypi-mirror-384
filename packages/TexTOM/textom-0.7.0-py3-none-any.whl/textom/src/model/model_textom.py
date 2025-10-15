import os
import glob
import numpy as np
from time import time
import sys, shutil
import importlib as imp # for reading input files
from numba import njit, prange
import h5py
import hdf5plugin

# domestic
from .. import handle as hdl
from . import model_projection as prj
from . import model_crystal as cry
from ..odf import hsh
from ..odf import gridbased as grd
from . import rotation as rot
from . import symmetries as sym
from .. import mask as msk
from ..misc import integrate_c, import_module_from_path
from ...config import data_type, odf_resolution
# from . import model_difflets_odftt as dif

class model_textom:
    """ A class to that contains the theoretical description of Texture tomography.

    """

    def __init__(self, sample_dir, classic=False, single=False, q_det=False, chi_det=False, light=False, no_Isc=False, override_odf_mode=False ):
        """Initializes the texture tomography model class

        Calculates arrays that do not need to be updated when fitting/plotting

        Parameters
        ----------
        startFileName : str
            path to the input file
        single : bool
            set to True if you just want to calculate a single image
            disables the whole tomography part
        
        Attributes created
        ------------
        see returned variables in input file
        """

        print("Initializing model")
        self.title = os.path.basename(sample_dir)
        self.path_analysis = os.path.join(sample_dir,'analysis')
        self.light = light
        self.no_Isc = no_Isc

        ################ Projectors
        if single: # initializes parameters if only a single image is produced
            self._init_single()
        else:
            if os.path.isfile(os.path.join(sample_dir,'analysis','projectors.h5')): # loads a tomo model if it exists
                t0 = time()
                with h5py.File( os.path.join(sample_dir,'analysis','projectors.h5'), 'r' ) as hf:
                    self.Omega = hf['Omega'][()].astype(data_type)
                    self.Kappa = hf['Kappa'][()].astype(data_type)
                    self.Gs = hf['Gs'][()].astype(data_type)
                    self.tomogram = hf['tomogram'][()].astype(data_type)
                    try:
                        self.ty = hf['translations_y'][()].astype(data_type)
                        self.tz = hf['translations_z'][()].astype(data_type)
                    except:
                        self.ty = hf['ty'][()].astype(data_type)
                        self.tz = hf['tz'][()].astype(data_type)
                    self.shift_y = hf['shift_y'][()].astype(data_type)
                    self.shiftz = hf['shift_z'][()].astype(data_type)
                    self.fov = hf['fov'][()]
                    self.x_p = hf['x_p'][()].astype(data_type)
                    self.nVox = hf['nVox'][()]
                    self.mask_voxels = hf['mask_voxels'][()]
                    if not light:
                        self.Beams = hf['Beams'][()].astype(data_type)
                        self.iBeams = hf['iBeams'][()]
                print("\tLoaded projectors from analysis/projectors.h5 (%2.2f s)" % ( (time()-t0)) )
            
            else:
                self.Kappa, self.Omega, self.shift_y, self.shiftz, self.tomogram, self.sinogram = hdl.load_shifts_mumott(
                        os.path.join(sample_dir,'analysis/alignment_result.h5') )

                print('\tImporting geometry')
                geo = import_module_from_path('geometry', os.path.join(sample_dir,'analysis/geometry.py'))

                self.nVox, self.fov, self.Gs, ty, tz, self.x_p = prj.setup_geometry( 
                    geo, self.tomogram, self.Omega, self.Kappa )

                # mask the sample
                if not os.path.isfile(os.path.join(self.path_analysis,'voxelmask.txt')) and np.any(self.sinogram):
                    self.mask_voxels = msk.mask_voxels(self.Kappa, self.Omega, ty, tz, self.shift_y, self.shiftz,
                                                        self.x_p, self.tomogram, self.sinogram)
                        
                    # save voxel mask to file
                    with open(os.path.join(self.path_analysis,'voxelmask.txt'), 'w') as fid:
                        for iv in self.mask_voxels:
                            fid.write(f'{iv}\n')      
                    print('\t\tSaved voxelmask to analysis/voxelmask.txt')  
                elif not np.any(self.sinogram):
                    self.mask_voxels = np.arange(self.tomogram.size)
                else:
                    self.mask_voxels = np.genfromtxt(
                        os.path.join(self.path_analysis,'voxelmask.txt'),
                        np.int32 )

                # calculate beam intensities and save them
                self.Beams, self.iBeams = prj.get_projectors(geo, self.Gs, self.nVox, self.x_p,
                                                                self.mask_voxels, ty, tz, self.shift_y, self.shiftz)

                print('\tSaving results to sample path analysis/projectors.h5')
                with h5py.File( os.path.join(sample_dir,'analysis','projectors.h5'), 'w' ) as hf:
                    hf.create_dataset('Beams', data=self.Beams, compression=hdf5plugin.Blosc(cname='zstd', clevel=5, shuffle=hdf5plugin.Blosc.SHUFFLE))
                    hf.create_dataset('iBeams', data=self.iBeams,compression=hdf5plugin.Blosc(cname='zstd', clevel=5, shuffle=hdf5plugin.Blosc.SHUFFLE))                    
                    hf.create_dataset('Omega', data=self.Omega)
                    hf.create_dataset('Kappa', data=self.Kappa) 
                    hf.create_dataset('Gs', data=self.Gs) 
                    hf.create_dataset('tomogram', data=self.tomogram, compression=hdf5plugin.Blosc(cname='zstd', clevel=5, shuffle=hdf5plugin.Blosc.SHUFFLE))
                    hf.create_dataset('translations_y', data=ty) 
                    hf.create_dataset('translations_z', data=tz) 
                    hf.create_dataset('shift_y', data=self.shift_y) 
                    hf.create_dataset('shift_z', data=self.shiftz) 
                    hf.create_dataset('fov', data=self.fov) 
                    hf.create_dataset('x_p', data=self.x_p)#, compression="lzf") 
                    hf.create_dataset('nVox', data=self.nVox) 
                    hf.create_dataset('mask_voxels', data=self.mask_voxels) 
        
        ################# Diffractlets
        crystal_path = os.path.join(sample_dir,'analysis','crystal.py')
        self.cr = import_module_from_path('crystal', crystal_path)
        if override_odf_mode:
            self.odf_mode = override_odf_mode
        else:
            self.odf_mode = self.cr.odf_mode
        if self.odf_mode=='hsh':
            self.odf_module = hsh
            self.odf_parameter = self.cr.hsh_max_order
        elif self.odf_mode=='grid':
            print('grid mode currently not functional')
            self.odf_module = grd
            self.odf_parameter = self.cr.grid_resolution
            return 0
            
        ## Load or calculate stuff
        difflets_path = os.path.join(sample_dir,'analysis',f'difflets_{self.odf_mode}_{self.odf_parameter}.h5')
        if os.path.isfile(difflets_path):
            with h5py.File(difflets_path, 'r') as hf:
                self.difflets = hf['difflets'][()]
                self.powder_pattern = hf['powder_pattern'][()]
                self.Qq_det = hf['q_values'][()]
                self.Chi_det = hf['chi_values'][()]
                self.hkl = hf['hkl'][()]
                self.detector_reciprocal_coordinates = hf['detector_reciprocal_coordinates'][()]
                self.symmetry = hf['symmetry'][()].decode('utf-8')
                #
                # here check if odf_parameters are the same (?)
                #
            print('\tLoaded diffractlets')

        else:
            # print('\tImporting geometry')
            geo = import_module_from_path('geometry', os.path.join(sample_dir,'analysis/geometry.py'))

            # get detector coordinates
            if np.any(q_det) and np.any(chi_det):
                # self.q_det = q_det
                self.chi_det = chi_det * np.pi/180
            else:
                # get detector coordinates from integrated data
                int_data_file = glob.glob(os.path.join(sample_dir,'data_integrated','*2d.h5'))[0]
                with h5py.File(os.path.join(sample_dir,'data_integrated',int_data_file),'r') as hf:
                    # self.q_det = hf['radial_units'][()]
                    self.chi_det = hf['azimuthal_units'][()] * np.pi/180
                # # adapt q to desired range
                # self.q_det = self.q_det[np.logical_and(
                #     self.q_det > self.cr.q_range[0],
                #     self.q_det < self.cr.q_range[1],
                # )]

            # print('calculating diffractlets')                
            sample_rotations = rot.QfromOTP(self.Gs)
            self.Qq_det, self.Chi_det, self.detector_reciprocal_coordinates,\
                self.hkl, self.difflets, self.powder_pattern, self.symmetry, self.odf = cry.get_diffractlets(
                            self.cr, self.chi_det, geo, 
                            sample_rotations, 
                            cutoff_structure_factor=self.cr.cutoff_structure_factor, max_hkl=self.cr.max_hkl,
                            odf_mode=self.odf_mode,
                            hsh_max_order = self.odf_parameter, grid_resolution=self.odf_parameter, # might want to make these a single arg
                            )
            # cry.plot_diffractlet(Qq_det, Chi_det, hkl, difflets[0], q_bins=np.linspace(*cr.q_range),
            #                      cmap='plasma', sym_cmap=False, logscale=True
            #                      )
            # cry.plot_diffractlet(Qq_det, Chi_det, hkl, difflets[1], q_bins=np.linspace(*cr.q_range),
            #                      cmap='plasma', sym_cmap=False, logscale=True
            #                      )
            with h5py.File(difflets_path,'w') as hf:
                hf.create_dataset('difflets', data=self.difflets)
                hf.create_dataset('powder_pattern', data=self.powder_pattern)
                hf.create_dataset('cif_file', data=self.cr.cifPath)
                hf.create_dataset('Energy_keV', data=self.cr.E_keV)
                hf.create_dataset('q_values', data=self.Qq_det)
                hf.create_dataset('hkl', data=self.hkl)
                hf.create_dataset('chi_values', data=self.Chi_det)
                hf.create_dataset('detector_reciprocal_coordinates', data=self.detector_reciprocal_coordinates)
                hf.create_dataset('sample_rotations', data=self.Gs)
                hf.create_dataset('symmetry', data=self.symmetry)
                hf.create_dataset('odf_mode', data=self.odf_mode )
                hf.create_dataset('odf_parameter', data=self.odf_parameter )

        self.detShape = self.Qq_det.shape
        
        # Initialize ODF object
        Gc, dV, V_fz = rot.sample_fundamental_zone( dchi=odf_resolution*np.pi/180, 
                                sampling='cubochoric', symmetry=self.symmetry )
        self.odf = self.odf_module.odf(self.odf_parameter, self.symmetry, Gc)

    """
    Initialisation functions
    """          
    def _init_single(self):
        """ Defines experiment-related parameters for simulating only single image """
        self.fov = np.array([1,1])
        self.nVox = np.array([1,1,1])
        self.Omega = np.array([0])
        self.Kappa = np.array([0])
        self.Gs = np.array([[0,0,0]])
        self.x_p = np.array([[0,0,0]])
        self.ty = np.array([0])
        self.tz = np.array([0])
        self.Beams = np.array([[[1,0]]])
        self.iBeams = np.array([[[0,2**32-1]]])
        self.mask_voxels = np.array([True])

    def imageFromC(self, c):
        """ Computes a diffraction image from a set of sHSH coefficients

        Parameters
        ----------
        c : 1D ndarray, float
            set of sHSH coefficients
        
        Return values
        ------------
        image : ndarray, float
            array of scattering intensity for each point on the detector
        """
        image = _imageFromC( c, self.difflets )
        return image
    
    def projection( self, g, C ):
        """Simulates diffraction images from a 2D scan over the sample

        For a certain sample rotation calculates sHSH coefficients in 
        each voxel, then integrates over the beam intensity for each
        translation, calculates the diffraction patterns and saves them
        into the model object.

        Parameters
        ----------
        g : int
            index of the sample rotation, defined in self.samplerotations
        C : 2D ndarray, float
            set of sHSH coefficients for each voxel
            dim: 0: voxel index, 1: sHSH index

        Attributes modified
        ------------
        images : 3D ndarray, float
            array of resulting scattering intensity for each point on the 
            detector, for each rotation and translation
            dim: 0: rotation, 1: translation, 2: detector points
        """
        # print('\tcalculating images for projection %d' % g )
        t0 = time()
        dlt_shp = self.difflets.shape
        images = _projection(
            g, C, 
            self.Beams, self.iBeams, self.difflets[g].reshape((dlt_shp[1], dlt_shp[2]*dlt_shp[3])),
            ).reshape((self.Beams.shape[1], dlt_shp[2], dlt_shp[3]))
        # print("\t\tfinished in %.3f s" % (time()-t0))
        return images
    
    def odfFromC( self, c, recenter = False ):
        """Computes an ODF from sHSHs

        Sums over pre-calculated symmetrized spherical harmonic functions
        and weights by the given coefficients. Also adds a isotropic part
        weighted by another input parameter

        Parameters
        ----------
        c : 1D ndarray, float
            set of sHSH coefficients
        info: bool
            if True prints information about the ODF
            
        Return values
        ------------
        odf : 1D ndarray, float
            array of probabilities for each orientation self.Gc
        """
        # if not hasattr(self.odf, 'basis_functions'):
        #     Gc, dV, V_fz = rot.sample_fundamental_zone( dchi=odf_resolution*np.pi/180, 
        #                             sampling='cubochoric', symmetry=self.symmetry )
        #     self.odf._basis_functions(Gc)

        # calculate ODF
        if recenter:
            odf = self.odf.get_odf_centered( c )
        else:
            odf = self.odf.get_odf( c )
        return self.odf.G_odf, odf
    '''
    g_pref = mod.g_ML_sample( fit.C[mod.mask_voxels], truncate=truncate_expansion )
    results['g_pref'] = mod.insert_sparse_tomogram(g_pref)
    print('\tExtracting stds')
    stds = mod.std_sample( fit.C[mod.mask_voxels], g_pref )
    results['std']=mod.insert_sparse_tomogram(stds)
    # export vtk-file for paraview
    a_pref, b_pref, c_pref = mod.abc_pref_sample( g_pref )
    '''

    def preferred_orientations( self, C ):

        # if not hasattr(self.odf, 'basis_functions'):
        #     Gc, dV, V_fz = rot.sample_fundamental_zone( dchi=odf_resolution*np.pi/180, 
        #                                  sampling='cubochoric', symmetry=self.symmetry )
        #     self.odf._basis_functions(Gc)

        odfs = self.odf.get_odf_batch( C )
        ig = np.argmax(odfs, axis=1) # index of the maximum of the odf
        G_max = self.odf.G_odf[ig]
        return G_max

    def std_sample( self, C, G_mu ):

        # if not hasattr(self.odf, 'basis_functions'):
        #     Gc, dV, V_fz = rot.sample_fundamental_zone( dchi=odf_resolution*np.pi/180, 
        #                                  sampling='cubochoric', symmetry=self.symmetry )
        #     self.odf._basis_functions(Gc)

        odfs_centered = self.odf.get_odf_centered_batch( C, G_mu )
        Std = std_parallel( odfs_centered, self.odf.G_odf[:,0] )

        return Std

    def abc_pref_sample( self, g_pref, lattice_vectors ):
        """ Calculates the crystal axis orientations from OTP orientations

        Should be generalized to all crystal systems using the actual axes

        Parameters
        ----------
        g_pref : 2D ndarray, float
            dim: 0: voxel index, 1: [ome,tta,phi]

        returns: 
        ------------
        a_pref, b_pref, c_pref : 2D ndarray, float
            crystal axis unit vectors
            dim: 0: voxel index, 1: [x,y,z]
        """
        lattice_vectors_norm = lattice_vectors/np.linalg.norm(lattice_vectors,axis=1)
        a_pref, b_pref, c_pref = _abc_pref_sample( g_pref, lattice_vectors_norm.astype(data_type) )
        return a_pref, b_pref, c_pref

    def directions_from_orientations( self, direction_0=(0,0,1) ):
        Gc, dV, V_fz = rot.sample_fundamental_zone( dchi=odf_resolution*np.pi/180, 
                                         sampling='cubochoric', symmetry=self.symmetry )
        return _directions_from_orientations(Gc, np.array(direction_0,data_type)), Gc
    
    def insert_sparse_tomogram( self, values ):
        """ Makes a 3D tomogram out of sparse data
        """
        try:
            tomogram = np.empty( (self.nVox.prod(),values.shape[1]), data_type )
            tomogram[:] = np.nan
            tomogram[self.mask_voxels] = values
            tomogram = tomogram.reshape((*self.nVox, values.shape[1]))
        except:
            tomogram = np.empty( self.nVox.prod(), data_type )
            tomogram[:] = np.nan
            tomogram[self.mask_voxels] = values
            tomogram = tomogram.reshape(self.nVox)
        return tomogram

    def odfFromC_old( self, c, K = None, clip = False, info = False ):
        """Computes an ODF from sHSHs

        Sums over pre-calculated symmetrized spherical harmonic functions
        and weights by the given coefficients. Also adds a isotropic part
        weighted by another input parameter

        Parameters
        ----------
        c : 1D ndarray, float
            set of sHSH coefficients
        K : float or None for not applying
            HSH damping factor to ensure positivity, usually between 1 and 2
        clip: bool
            if True, negative values get clipped and ODF renormalized
        info: bool
            if True prints information about the ODF
            
        Return values
        ------------
        odf : 1D ndarray, float
            array of probabilities for each orientation self.Gc
        """
        if K == 'auto':
            K, neg = 1., 1.
            c_in=c.copy()
            while neg>0.01:
                c_in = self.apply_kernel( c, K, info=False )
                odf = _odfFromC( self.sHSHs, c )
                neg = ( odf[odf<0] @ self.dV[odf<0] ) 
                K += 0.1
        elif isinstance(K,(int, float)): # apply the Mason kernel on coefficients
            c_in = self.apply_kernel( c, K )
        else:
            c_in = c.copy()
        
        # calculate ODF
        odf = _odfFromC( self.sHSHs, c_in )

        if clip:
            neg_percent = - odf[odf<0].sum() / np.abs(odf).sum()
            odf[odf<0] = 0 # clip negative values
            odf = odf / ( odf @ self.dV ) # renormalize

        if info:
            self.get_c_weights(c_in)
            print('Made ODF')
            print('\tMaximum: %.3e' % odf.max() )
            print('\tMinimum: %.3e' % odf.min() )


            # estimate mean value from distribution truncated at lowest order
            if c.size > 1:
                ic_max = self.Sn[1,1]
                i_mu = np.argmax(
                    _odfFromC( self.sHSHs[:ic_max-1], c[:ic_max]))
                mu = self.Gc[i_mu]
                std = self.std_sample(
                    np.array([c_in]), np.array([mu])
                )[0]
            print('\tMean orientation: ome %.2f, tta %.2f, phi %.2f' % (
                mu[0],mu[1],mu[2]))
            print('\tStandard deviation [%s]: %.2f' % (chr(176), std*180/np.pi))
            
            if np.any(odf<0):
                odf_pos = odf.copy()
                odf_pos[odf_pos<0]=0
                tmp = odf_pos @ self.dV - 1
                rel_neg = tmp / (1 + 2*tmp)
                print('\t%.2f percent of the distribution is negative' % (rel_neg*100) )

        return odf

"""
Class-external functions compiled in numba and called from wrappers inside the class
"""
@njit()
def _imageFromC( c, difflets ):
    """Computes a diffraction image from custom parameters
    Statically typed to enable jitting
    Weights pre-calculated sHSH diffraction patterns with coefficients
    to make a custom diffraction pattern

    Parameters
    ----------
    c : 1D ndarray, float
        set of sHSH coefficients
    difflets : 2D ndarray, float
        diffractlets to be summed
        dim 0: sHSH index, 1: detector point index
    
    Return values
    ------------
    image : 1D ndarray, float
        simulated diffraction pattern
    """
    image = c @ difflets # sum over sHSH-images without isotropic part
    return image

@njit()
def _odfFromC( sHSHs, c ):
    """ Computes a diffraction image from a set of sHSH coefficients

    Parameters
    ----------
    c : 1D ndarray, float
        set of sHSH coefficients
    
    Return values
    ------------
    odf : 1D ndarray, float
        probability for each orientation
    """
    # renormalize to c0 = 1    
    c1plus = c[1:]/c[0]

    ## produces an ODF from HSH-coefficients
    odf = 1 + c1plus @ sHSHs

    return odf.astype(data_type)

@njit(parallel=True)
def std_parallel( Odf, omega ):
    Std = np.empty( Odf.shape[0], Odf.dtype )
    for o in prange(Odf.shape[0]):
        Std[o] = np.sqrt( ( Odf[o] * omega**2 ).sum() / Odf[o].sum() )
    return Std

@njit(parallel=True)
def _directions_from_orientations( orientations, direction_0 ):
    """ Calculates the crystal axis orientations from OTP orientations

    Should be generalized to all crystal systems using the actual axes

    Parameters
    ----------
    g_pref : 2D ndarray, float
        dim: 0: voxel index, 1: [ome,tta,phi]

    returns: 
    ------------
    a_pref, b_pref, c_pref : 2D ndarray, float
        crystal axis unit vectors
        dim: 0: voxel index, 1: [x,y,z]
    """
    Nvox = orientations.shape[0]
    directions = np.empty((Nvox,3), data_type)

    for k in prange(Nvox):
        # get preferred orientation for all axes
        R_pref  = rot.MatrixfromOTP( orientations[k,0], orientations[k,1], orientations[k,2])
        directions[k] = direction_0 @ R_pref 
    return directions

@njit(parallel=True)
def _abc_pref_sample( g_pref, lattice_vectors ):
    """ Calculates the crystal axis directions from OTP orientations

    Parameters
    ----------
    g_pref : 2D ndarray, float
        dim: 0: voxel index, 1: [ome,tta,phi]

    returns: 
    ------------
    a_pref, b_pref, c_pref : 2D ndarray, float
        crystal axis unit vectors
        dim: 0: voxel index, 1: [x,y,z]
    """
    g_pref, lattice_vectors = g_pref.astype(data_type), lattice_vectors.astype(data_type)
    Nvox = g_pref.shape[0]
    a_pref = np.empty((Nvox,3), data_type)
    b_pref = np.empty((Nvox,3), data_type)
    c_pref = np.empty((Nvox,3), data_type)

    for k in prange(Nvox):
        # get preferred orientation for all axes
        R_pref  = rot.MatrixfromOTP( g_pref[k,0], g_pref[k,1], g_pref[k,2])
        a_pref[k] = lattice_vectors[0] @ R_pref 
        b_pref[k] = lattice_vectors[1] @ R_pref 
        c_pref[k] = lattice_vectors[2] @ R_pref 
    return a_pref, b_pref, c_pref

@njit(parallel=True)
def _projection(
        g, C, # parameters
        Beams, iBeams, difflets_rot, # pre-calculated quantities
        ):
    """Simulates diffraction images from a 2D scan over the sample

    For a certain sample rotation calculates sHSH coefficients in 
    each voxel, then integrates over the beam intensity for each
    translation and makes diffraction patterns from diffractlets

    Parameters
    ----------
    g : int
        rotation index
    C : 2D ndarray, float
        set of sHSH coefficients for each voxel
        dim: 0: voxel index, 1: sHSH index
    Beams : 3D ndarray, float
        sparse-array containing beam intensity for all configurations
        dim: 0: rotation, 1: translation, 2: voxel (sparse)
    iBeams : 3D ndarray, int
        array of indices for the sparse Beams array
        dim: 0: rotation, 1: translation, 2: voxel index
    difflets_rot : 3D ndarray, float
        diffractlets for rotation g
        dim: 0: basefunction indices, 1: detector points

    returns: 
    ------------
    images : 3D ndarray, float
        modified simulated diffraction patterns
        dim: 0: rotation, 1: translation, 2: detector points
    """
    images = np.empty((Beams.shape[1], difflets_rot.shape[1]), data_type)
    for t in prange( Beams.shape[1] ): # scan over the sample
        iend = np.searchsorted(iBeams[g,t,:],2**32-1) # for sparsearray
        # get projected coefficients for the corresponding beam rotation/translation
        c_proj = integrate_c( Beams[g,t,:iend], iBeams[g,t,:iend], C)
        # calculate the image
        images[t,:] = c_proj @ difflets_rot 
    return images

