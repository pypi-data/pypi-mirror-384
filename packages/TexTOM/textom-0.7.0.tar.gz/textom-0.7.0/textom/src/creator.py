import os, glob, sys, shutil
os.environ["MKL_NUM_THREADS"] = "1" 
os.environ["NUMEXPR_NUM_THREADS"] = "1" 
os.environ["OMP_NUM_THREADS"] = "1"
import numpy as np
import h5py, hdf5plugin
import matplotlib.pyplot as plt
from importlib import reload # this is for debugging
from time import time

# domestic
from .model import rotation as rot
from .model import symmetries as sym
from .analysis import orix_plugins as orx
from .model.model_textom import model_textom
from .misc import import_module_from_path
from .odf import gridbased as grd
from ..config import data_type

# sample_dir = '/Users/moritz/Documents/papers/benchmark/gen_sample/'

class creator:
    """ A class to that contains the theoretical description of Texture tomography.

    Takes input from a designated input file, see input/input_template.py
    for how it has to be stuctured
    """

    def __init__(self, sample_dir):
        os.makedirs(os.path.join(sample_dir,'analysis'), exist_ok=True)
        os.makedirs(os.path.join(sample_dir,'data_integrated'), exist_ok=True)
        self.sample_dir = sample_dir
        gen_path = os.path.join(sample_dir,'analysis','generation.py')
        self.gen = import_module_from_path('generation', gen_path)

    def setup_generated_sample(self):

        # save alignment file for projectors
        tomogram=self.gen.sample_mask.astype(data_type)
        with h5py.File(os.path.join(self.sample_dir,'analysis','alignment_result.h5'),'w') as hf:
            hf.create_dataset('kappa', data=self.gen.kappa)
            hf.create_dataset('omega', data=self.gen.omega)
            hf.create_dataset('shifts', data=np.zeros((self.gen.kappa.size,2)))
            hf.create_dataset('tomogram', data=tomogram)
            hf.create_dataset('sinogram', data=[])    

        # save voxelmask
        with open(os.path.join(self.sample_dir,'analysis','voxelmask.txt'), 'w') as fid:
            for iv in np.where(self.gen.sample_mask.flatten())[0]:
                fid.write(f'{iv}\n')      
        
        # initialize the model
        self.mod = model_textom( self.sample_dir, classic=False,
                         q_det=self.gen.q_det, # careful! this does nothing
                         chi_det=self.gen.chi_det )
        
    def define_coefficients(self):

        # find out how many voxels and coefficients
        n_voxels = np.prod(self.mod.nVox)
        n_coefficients = self.mod.difflets.shape[1]

        if self.gen.intensity_style == 'uniform':
            intensity = np.ones((n_voxels, n_coefficients), data_type)
        # 
        self.coefficients = np.zeros((n_voxels, n_coefficients), data_type)
        for v in np.atleast_1d(self.mod.mask_voxels):
            if self.gen.coefficient_style == 'single_first':
                self.coefficients[v,0] = 1
            elif self.gen.coefficient_style == 'single_middle':
                self.coefficients[v, self.coefficients.shape[1]//2] = 1
            elif self.gen.coefficient_style == 'single_random':
                idx = np.random.randint( n_coefficients )
                self.coefficients[v, idx] = 1
            else:
                print('\nCoefficient style not recognized\n')
                sys.exit(1)
                
        self.coefficients *= intensity

        with h5py.File(os.path.join(self.sample_dir,'data_integrated','sample_coefficients.h5'), 'w') as hf:
            hf.create_dataset('coefficients', data=self.coefficients)
            hf.create_dataset('odf_mode', data=self.mod.odf_mode )
            hf.create_dataset('odf_parameter', data=self.mod.odf_parameter )
            hf.create_dataset('intensity_style', data=self.gen.intensity_style)
            hf.create_dataset('coefficient_style', data=self.gen.coefficient_style)

    def save_projections(self):
        # gen_path = os.path.join(sample_dir,'analysis','generation.py')
        # gen = import_module_from_path('generation', gen_path)

        # n_basis_functions, q_odf = setup_grid(gen.grid_resolution, mod.symmetry)
        # generators = sym.generators(mod.symmetry)

        # # set up sample coefficients
        # sample_bf_coefficients = np.zeros((np.prod(mod.nVox), n_basis_functions), data_type)
        # flatmask = np.where(mod.mask_voxels.flatten())[0]
        # for v in flatmask:
        #     i_dir = np.random.randint(n_basis_functions)
        #     sample_bf_coefficients[v,i_dir] = 1
        
        # Qs = rot.QfromOTP( mod.Gs )
        # Qc = rot.QfromOTP( mod.Gc )

        # for g in range(mod.Beams.shape[0]):
        #     diff_patterns_g = projection( 
        #         Qc, mod.Isc, Qs, mod.Beams, mod.iBeams, mod.detShape, mod.dV,
        #         sample_bf_coefficients, q_odf, gen.grid_resolution, generators )
        
        # # set up sample coefficients
        # n_basis_functions = mod.difflets.shape[1]
        # sample_bf_coefficients = np.zeros((np.prod(mod.nVox), n_basis_functions), data_type)
        # flatmask = np.where(mod.mask_voxels.flatten())[0]
        # for v in flatmask:
        #     i_dir = np.random.randint(n_basis_functions)
        #     sample_bf_coefficients[v,i_dir] = 1
        n_rot = self.mod.Beams.shape[0]
        path_int = os.path.join(self.sample_dir,'data_integrated')
        print('\tCalculating projections')
        for g in range(n_rot):
            diff_patterns_g = self.mod.projection( g, self.coefficients )
            n_trans = diff_patterns_g.shape[0]
            detector_images = np.zeros( (n_trans, diff_patterns_g.shape[1], self.gen.q_det.size),
                                      data_type )
            for q in range(diff_patterns_g.shape[2]):
                upper = np.argmax(self.mod.Qq_det[0,q] < self.gen.q_det)
                detector_images[:,:,upper-1] = diff_patterns_g[:,:,q]

            with h5py.File(os.path.join(path_int,f'gen_sample_proj{g:03d}_2d.h5'), 'w') as hf:
                hf.create_dataset('cake_integ', data=detector_images)        
                hf.create_dataset('fov', data=self.mod.fov)
                hf.create_dataset('radial_units', data=self.gen.q_det )#self.mod.Qq_det[:,0])
                hf.create_dataset('azimuthal_units', data=self.mod.Chi_det[:,0] * 180/np.pi)
                hf.create_dataset('tilt_angle', data=self.mod.Kappa[g])
                hf.create_dataset('rot_angle', data=self.mod.Omega[g])
                hf.create_dataset('ion', data=np.ones(n_trans, data_type) )

            sys.stdout.write(f'\r\t\t{(g+1):d} / {n_rot:d}')#, t/it: {t_it:.2f}, t left: {((Nrot-g-1)*t_it/60):.1f} min' )
            sys.stdout.flush()
        
        print(f'\n\tsaved to {path_int}')

# # @njit(parallel=True)
# def projection( Qc, Isc, Qs, Beams, iBeams, detShape, dV, 
#                sample_bf_coefficients, q_odf, resolution, gen ):
#     diff_patterns_g = np.empty((Beams.shape[1],detShape[0],detShape[1]), data_type)
#     for t in prange(Beams.shape[1]):
#         # project the coefficients
#         iend = np.searchsorted(iBeams[g,t,:],2**32-1) # for sparsearray
#         c_proj = integrate_c( Beams[g,t,:iend], iBeams[g,t,:iend], sample_bf_coefficients )
#         # get the resulting odf from rotated mu
#         odf_proj = np.zeros( Qc.shape[0], data_type )
#         idcs_basis = np.nonzero(c_proj > 0.01 * c_proj.max())[0]
#         for c in idcs_basis:
#             q_mu = rot.quaternion_multiply(  q_odf[c], Qs[g] )
#             odf_proj += c_proj[c] * gaussian_3d(Qc, q_mu, resolution*np.pi/180, gen, dV )
#         # sparse calculate the projections (only points in odf that are high)
#         diff_pattern = np.zeros(Isc.shape[1], data_type)
#         idcs_odf = np.nonzero(odf_proj> 0.01 * odf_proj.max())[0]
#         for h in idcs_odf:
#             diff_pattern += Isc[h] * odf_proj[h]
#         diff_patterns_g[t] = diff_pattern.reshape((detShape[0],detShape[1]))
#     return diff_patterns_g

def plot_basefunction_texture(resolution, mod, g_center=(0,0,0)):
    
    q_center = rot.QfromOTP(np.atleast_2d(g_center)).flatten()
    Qc = rot.QfromOTP( mod.Gc )
    generators = sym.generators(mod.symmetry)
    q_gen = rot.QfromOTP(generators)
    Q_group = rot.generate_group(q_gen)

    # show the center of the distribution
    orx.plot_points_in_fz(q_center,mod.symmetry)
    plt.title('mean')
    # plot gaussian distribution
    # odf = fisher_SO3(Qc,q_center,10/(resolution*np.pi/180)**2,Q_group)
    odf = grd.gaussian_SO3(Qc, q_center, resolution*np.pi/180, Q_group)

    # orx.odf_cloud_general(mod.Gc,
    #     gaussian_3d(Qc,q_center,resolution*np.pi/180,generators,1),
    #     mod.symmetry,num_samples=1000)
    # plt.title('gauss')
    # plot fisher distribution
    orx.plot_odf(rot.QfromOTP(mod.Gc),
        odf,
        mod.symmetry,
        )
    # plt.title('fisher')
    # plot a polefigure
    orx.plot_pole_figure_from_odf(mod.Gc,odf,
                    mod.symmetry, hkl=(1,0,0) )
    orx.plot_pole_figure_from_odf(mod.Gc,odf,
                    mod.symmetry, hkl=(0,1,0) )
    orx.plot_pole_figure_from_odf(mod.Gc,odf,
                    mod.symmetry, hkl=(0,0,1) )
