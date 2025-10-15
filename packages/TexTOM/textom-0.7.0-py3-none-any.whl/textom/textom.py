import os, glob, sys, shutil
import numpy as np
import h5py, hdf5plugin
import matplotlib.pyplot as plt
from matplotlib import colors
from importlib import reload # this is to reload
import imageio.v3 as iio
from time import time
from typing import Union, Optional

from .src.integration import pyfai_plugins as pyf
from .src.data_treatment import mumott_plugins as mum
from .src.model.model_textom import model_textom
from .src.data_treatment import data as dat
from .src.data_treatment import baselines as bln
from .src.optimization.fitting import fitting
from .src import handle as hdl
from .src import plotting as plot
from .src.optimization import optimizer 
from .src.model import symmetries as sym
from .src import mask as msk
from .src import misc as msc
from .src.analysis import orix_plugins as orx
from .src import exceptions as exc
from .src.model import rotation as rot
from .src.analysis import segmentation as seg
from .src.analysis import orderparameters as ord
from .src import numba_plugins as nb
# from .src.data_treatment import absorption_corrector as abc
from .src.model import model_crystal as cry
from .src.creator import creator
from .config import use_gpu, n_threads, data_type

sample_dir = os.getcwd()
mod, fit, opt  = None, None, None
results = {}

def set_path( path ):
    """Set the path where integrated data and analysis is stored

    Parameters
    ----------
    path : str
        full path to the directory, must contain a folder '/data_integrated'
    """    
    global sample_dir
    sample_dir = path
    os.makedirs(os.path.join(sample_dir,'analysis','fits'), exist_ok=True)
    os.makedirs(os.path.join(sample_dir,'results','images'), exist_ok=True)
    print(f'Set sample path to: {sample_dir}')

def check_state( ):
    """Prints in terminal which parts of the reconstruction are ready
    """    
    print('Checking state of analysis')
    to_check = [
        ['Alignment', os.path.join(sample_dir,'analysis','alignment_result.h5')],
        ['Model (diffractlets)', os.path.join(sample_dir,'analysis','diffractlets.h5')],
        ['Model (projectors)', os.path.join(sample_dir,'analysis','projectors.h5')],
        ['Data', os.path.join(sample_dir,'analysis','data_textom.h5')],
    ]
    for ch in to_check:
        state = 'ready' if os.path.isfile(ch[1]) else 'missing'
        print(f'\t{ch[0]} - {state}')
    to_count = [
        ['Integrated projections', os.path.join(sample_dir,'data_integrated')],
        ['Optimisations', os.path.join(sample_dir,'analysis','fits')],
        ['Results', os.path.join(sample_dir,'results')],
    ]
    for co in to_count:
        try:
            h5_count = sum(1 for file in os.listdir(co[1]) if file.endswith(".h5"))
            print(f'\t{co[0]} - {h5_count} files')
        except:
            print(f'\tNo {co[0]} found')
    
def integration_test(dset_no=0):
    """Set up integration parameters, perform a 2D and 1D integration and plot them

    Parameters
    ----------
    dset_no : int, optional
        allows to choose a different file from the raw data folder
        (they will be assigned indices in alphabetic order), by default 0
    """
    test_filenames = pyf.start_test_integration(sample_dir, dset_no=dset_no)
    # print('\tWrote test data: '+test_filenames)
    f,ax = plt.subplots(2, sharex=True, figsize=(6,8))
    with h5py.File(test_filenames[0], 'r') as hf:
        q = hf['radial_units'][()]
        chi = hf['azimuthal_units'][()]
        data = hf['cake_integ'][()]
    ax[0].pcolormesh(*np.meshgrid(q,chi), data.max(axis=0), norm=colors.LogNorm())
    ax[0].set_ylabel('chi / degree')
    with h5py.File(test_filenames[1], 'r') as hf:
        q = hf['radial_units'][()]
        data = hf['cake_integ'][()]
    ax[1].plot(q.flatten(), data.max(axis=0))
    ax[1].set_ylabel('Intensity')
    ax[1].set_xlabel('q / nm^-1')
    f.tight_layout()
    f.savefig('test_integration.pdf')

def generate_sample():
    """Allows the creation of custom samples for testing the pipeline.
    Input of parameters occurs via a custom generation.py file, which opens automatically,
    in addition to usual textom input files.
    """
    global mod
    gen_path_sample = os.path.join(sample_dir,'analysis','generation.py')
    if not os.path.isfile( gen_path_sample ):
        gen_path_module = hdl.get_file_path('textom',os.path.join('input','generation.py'))
        os.makedirs(os.path.join(sample_dir,'analysis'), exist_ok=True )
        shutil.copyfile(gen_path_module, gen_path_sample )
    hdl.open_with_editor(gen_path_sample)
    
    crt = creator(sample_dir)
    crt.setup_generated_sample()
    crt.define_coefficients()
    crt.save_projections()
    
def integrate( parallel=True, wait=5., confirm=True, ignore=[], parallel_gpu=False ):
    """Integrates raw 2D diffraction data via pyFAI

    All necessary input will be handled via the file integration_parameters.py
    
    Parameters
    ----------
    mode : str
        'online' does one by one, updates filelist after each integration
        'parallel' loads filelist when started, can be parallelized over CPUs
    wait : float
        waits this number of seconds after integrating the last file before
        stopping, by default 5.
    confirm : bool
        if True, will open integration_parameters.py and ask for confirmation
        else, takes current file and starts
    ignore : list
        here you can provide a list of datasets you want to skip (if they crash
        they will automatically be skipped)
    """
    if parallel:
        pyf.start_integration_parallel( sample_dir, confirm=confirm, ignore=ignore )
    else:
        pyf.start_integration_online( sample_dir, wait=wait, confirm=confirm, ignore=ignore, parallel=parallel_gpu )

def mask_detector_azimuthal( projection=0, datafile_pattern='.h5'):
    """Opens a window that allows excluding detector pixels by mouse clicks
    Gives the average of a whole projection to find regions to mask.

    Parameters
    ----------
    projection : int, optional
        projection index, by default 0
    datafile_pattern : str, optional
        allows use a certain file that contains the pattern, by default '.h5'
    """
    # load some data for testing
    filelist = dat.get_data_list(sample_dir, datafile_pattern)
    with h5py.File(os.path.join(sample_dir,'data_integrated',filelist[projection]), 'r') as hf:
        q = hf['radial_units'][()].flatten()
        chi = hf['azimuthal_units'][()].flatten()
        data = hf['cake_integ'][()].sum(axis=0)
    
    cakemask_path = os.path.join(sample_dir, 'analysis', 'mask_detector_cake.h5')
    try:
        cake_mask = h5py.File(cakemask_path,'r')['mask_cake'][()].astype(bool)
    except:
        cake_mask = np.ones(data.shape, bool)
        with h5py.File(cakemask_path,'w') as hf:
            hf.create_dataset('mask_cake', shape=data.shape, dtype=bool)

    # directly exclude nan-values from data
    cake_mask[ np.isnan(data) ] = 0
    cake_mask[ data == 0 ] = 0

    new_mask = msk.mask_detector( data, cake_mask )
    with h5py.File(cakemask_path,'r+') as hf:
        hf['mask_cake'][()] = new_mask

def check_geometry(testfile_path,testfile_h5path,dset_no=0,
                    vmin=1, vmax = 10, logscale = False
                    ):     
    #####
    # i would like to make the first 2 arguments auto, maybe also this function could replace "integrate_test"
    ####
    # get geometry file from input/ if not present in sample_dir
    geo_path_sample = os.path.join(sample_dir,'analysis','geometry.py')
    if not os.path.isfile( geo_path_sample ):
        geo_path_module = hdl.get_file_path('textom',os.path.join('input','geometry.py'))
        os.makedirs(os.path.join(sample_dir,'analysis'), exist_ok=True )
        shutil.copyfile( geo_path_module, geo_path_sample )
    hdl.open_with_editor(geo_path_sample)
    pyf.check_detector_geometry(
        os.path.join(sample_dir,'integration_parameters.py'),
        testfile_path,testfile_h5path,
        dset_no,
        geo_path_sample,
        vmin,vmax,logscale,
        )

def align_data( 
        pattern='.h5', sub_data='data_integrated', 
        align_by_transmission=False,
        q_index_range=(0,5), q_range = False,
        crop_image=False, mode='optical_flow',
        redo_import=False, regroup_max=16,
        align_horizontal=True, align_vertical=True,
        pre_rec_it = 5, pre_max_it = 5,
        last_rec_it = 40, last_max_it = 5,
        do_align=True
          ):
    """Align data using the Mumott package

    Requires that data has been integrated and that sample_dir contains
    a subfolder with the data

    Parameters
    ----------
    pattern : str, optional
        substring contained in all files you want to use, by default '.h5'
    sub_data : str, optional
        subfolder containing the data, by default 'data_integrated'
    q_index_range : tuple, optional
        determines which q-values are used for alignment (sums over them), by default (0,5)
    q_range : tuple, optional
        give the q-range in nm instead of indices e.g. (15.8,18.1), by default False
    mode : str, optional
        choose alignment mode, 'optical_flow' or 'phase_matching', by default 'optical_flow'
    crop_image : bool or tuple of int, optional
        give the range you want to use in x and y, e.g. ((0,-1),(10,-10))
        only available with the 'phase_matching'-option, by default False
    redo_import : bool, optional
        set True if you want to recalculate data_mumott.h5, by default False
    regroup_max : int, optional
        maximum size of groups when downsampling for faster processing, by default 16
    align_horizontal : bool, optional
        align your data horizontally, by default True
    align_vertical : bool, optional
        align your data vertically, by default True
    pre_rec_it : int, optional
        reconstruciton iterations for downsampled data, by default 5
    pre_max_it : int, optional
        alignment iterations for downsampled data, by default 5
    last_rec_it : int, optional
        reconstruciton iterations for full data, by default 40
    last_max_it : int, optional
        alignment iterations for full data, by default 5
    """    
    t0=time()
    # get geometry file from input/ if not present in sample_dir
    geo_path_sample = os.path.join(sample_dir,'analysis','geometry.py')
    if not os.path.isfile( geo_path_sample ):
        geo_path_module = hdl.get_file_path('textom',os.path.join('input','geometry.py'))
        os.makedirs(os.path.join(sample_dir,'analysis'), exist_ok=True )
        shutil.copyfile( geo_path_module, geo_path_sample )
    hdl.open_with_editor(geo_path_sample)
    # do data preprocessing if not yet done
    if ( os.path.isfile(os.path.join(sample_dir,'analysis/data_mumott.h5')) and
        not redo_import ):
        mm_file = os.path.join(sample_dir,'analysis','data_mumott.h5')
    else:
        mm_file = mum.mumottize(sample_dir, 
            sub_data=sub_data, pattern=pattern, 
            q_index_range=q_index_range, q_range=q_range,
            align_by_transmission=align_by_transmission,
            geo_path=geo_path_sample,
            )
    if do_align:
        # downsample data
        mum.regroup(mm_file, regroup_max=regroup_max,
                    horizontal=align_horizontal, vertical=align_vertical,
                    )
        if crop_image:
            # crop_image = ()
            with h5py.File(mm_file, 'r') as hf:
                im_test = hf['projections']['0']['diode'][()]
            plt.figure()
            plt.imshow(im_test[slice(*crop_image[0]), slice(*crop_image[1])])
            plt.show(block=True)
            # happy = input('happy? (y/n)')
            # if 'n' in happy:
            #     break
            if mode=='optical_flow':
                print('\tcropping not possible for optical flow alignment, switching to phase-matching')
                mode='phase_matching'
    # run the alignment
    mum.align_regrouped(os.path.join(sample_dir,'analysis'), use_gpu=use_gpu,
                            regroup_max=regroup_max,
                            crop_image=crop_image, mode=mode,
                            pre_rec_it = pre_rec_it, pre_max_it = pre_max_it,
                            last_rec_it = last_rec_it, last_max_it = last_max_it,
                            align_horizontal=align_horizontal, align_vertical=align_vertical,
                            do_align=do_align
                            )
    if do_align:
        # plot a rough consistency check
        mum.check_consistency( 
            os.path.join(sample_dir,'analysis','alignment_result.h5'), 
            os.path.join(sample_dir,'analysis','data_mumott.h5'),
            save_to_result=True  )
        print(f'\tTotal time: {(time()-t0)/60:.2f} min')
    
def check_alignment_consistency( ):
    """Plots the squared residuals between data and the projected tomograms,
    with data shifted according to the alignment.
    """  
    mum.check_consistency( 
        os.path.join(sample_dir,'analysis','alignment_result.h5'), 
        os.path.join(sample_dir,'analysis','data_mumott.h5'),  )

def check_alignment_projection( g=0 ):
    """Plots the data and the projected tomogram of projection g

    Parameters
    ----------
    g : int, optional
        projection running index, by default 0
    """     
    mum.show_aligned_projection( g,
        os.path.join(sample_dir,'analysis','alignment_result.h5'), 
        os.path.join(sample_dir,'analysis','data_mumott.h5'),  )
    # check all as a movie

# def exclude_projections(G:Union[list,int]):
#     """_summary_

#     Parameters
#     ----------
#     G : Union[list,int]
#         _description_
#     """
#     if isinstance(G,int):
#         G = [G]
#     with open(os.path.join(sample_dir,'analysis','excluded_projections.txt'),'a') as fid:
#         for g in G:
#             fid.write(f'{g}\n')

def reconstruct_1d_full( q_index_range=None, redo_import=False, only_mumottize=False, batch_size=10 ):
    """Reconstructs scalar tomographic data such as azimutally averaged
    diffraction data. Uses the same alignment as textom

    Parameters
    ----------    
    q_index_range : list or ndarray or None, optional
        [starting_q_index, end_q_index], takes the whole range if None, by default None
    redo_import : bool, optional
        set true if you want to redo the preprocessing, by default False
    only_mumottize : bool, optional
        only preprocesses a file analysis/rec1d/data_rec1d.h5, by default False
    batch_size : int, optional
        number of q-values to load at the same time. Needs to be an integer fraction
        of the total number of q-values, else it will crash at the last batch. Higher
        numbers will decrease i/o time, but require more memory, by default 10
    """
    os.makedirs(os.path.join(sample_dir,'analysis','rec_1d'),exist_ok=True)
    input_path_sample = os.path.join(sample_dir,'analysis','rec_1d','input_1Drec.py')
    if not os.path.isfile( input_path_sample ):
        input_path_module = hdl.get_file_path('textom',os.path.join('input','input_1Drec.py'))
        shutil.copyfile(input_path_module, input_path_sample ) # copy to the sample directory
    else:
        msc.cp_add_dt(input_path_sample, sample_dir, now=False) # save the old version with modification date
    hdl.open_with_editor(input_path_sample) # edit and use the same file

    datapath = os.path.join(sample_dir,'analysis','rec_1d','data_rec1d.h5')
    if not os.path.isfile(datapath) or redo_import:
        datapath=None
    out_path = mum.backproject_all( sample_dir, input_path_sample, path_data=datapath, 
                            range_q=q_index_range,
                            only_mumottize=only_mumottize, batch_size=batch_size)
    if out_path is not None:
        with h5py.File(os.path.join(sample_dir,'analysis','projectors.h5'), 'r') as hf:
            mask = hf['mask_voxels'][()]
            nVox = hf['nVox'][()]
        mask_voxels = np.zeros(np.prod(nVox), bool)
        mask_voxels[mask] = True 
        mask_voxels = mask_voxels.reshape(nVox)
        with h5py.File(out_path, 'r+') as hf:
            hf.create_dataset('mask_voxels', data=mask_voxels, compression=hdf5plugin.LZ4())

def check_powder_pattern( projection=0, datafile_pattern='.h5', check=False ):
    """Calculates the theoretical powder pattern according to the input in crystal.py
    and plots it together with the average over a given projection.

    Parameters
    ----------
    projection : int, optional
        Index of the projection from the data_integrated directory,
        (sorted by rotation angles or alphabetical, as stated in the terminal) by default 0
    datafile_pattern : str, optional
        allows use a certain file that contains the pattern, by default '.h5'
    """
    crystal_path_sample = os.path.join(sample_dir,'analysis','crystal.py')
    if not os.path.isfile( crystal_path_sample ):
        crystal_path_module = hdl.get_file_path('textom',os.path.join('input','crystal.py'))
        os.makedirs(os.path.join(sample_dir,'analysis'), exist_ok=True )
        shutil.copyfile(crystal_path_module, crystal_path_sample )
        hdl.open_with_editor(crystal_path_sample)

    # try to get some data:
    try:
        filelist = dat.get_data_list(sample_dir, datafile_pattern)
        with h5py.File(os.path.join(sample_dir,'data_integrated',filelist[projection]), 'r') as hf:
            I_dat = hf['cake_integ'][()]#.sum(axis=0).sum(axis=0)
            q_dat = hf['radial_units'][()].flatten()
            chi_dat = hf['azimuthal_units'][()].flatten()
    except:
        print('\tNo data found in sample_dir/data_integrated/')
        q_dat,I_dat=None,None

    happy = 'n'
    while happy == 'n':
        cr = msc.import_module_from_path('crystal', os.path.join(sample_dir,'analysis','crystal.py'))
        cry.plot_powder_pattern( cr.cifPath,
                cutoff_structure_factor=cr.cutoff_structure_factor,
                max_hkl = cr.max_hkl, q_min= cr.q_range[0], q_max=cr.q_range[1],
                q_dat=q_dat, chi_dat=chi_dat, I_dat=I_dat, wavelength=cry.wavelength_from_E_keV(cr.E_keV))
        print('\tPowder diffraction pattern. Check agreement with data and revise crystal.py and the .cif file. Type n to replot with new parameters')
        if check:
            happy = input('\t\thappy? (y/n) ')
        else:
            happy='y'

def make_model( light_mode=False ):
    """Calculates the TexTOM model for reconstructions

    Is automatically performed by the functions that require it
    """    
    global mod
    if not os.path.isfile(os.path.join(sample_dir,'analysis/alignment_result.h5')):
        # print('Alignment not done, not calculating beam intensities\n\trun align_data() first')
        ans = input('Alignment not done, skip alignment? (y/n)')
        if ans == 'y':
            align_data(do_align=False)
            # save alignment file for projectors
                    #     tomogram= 1 # run SIRT reconstruction? .. or run my own optimizer - would be better maybe
                    #                                                  anyway i need to go through a round of data-reading
                    #     with h5py.File(os.path.join(sample_dir,'analysis','alignment_result.h5'),'w') as hf:
                    #         hf.create_dataset('kappa', data=self.gen.kappa)
                    #         hf.create_dataset('omega', data=self.gen.omega)
                    #         hf.create_dataset('shifts', data=np.zeros((self.gen.kappa.size,2)))
                    #         hf.create_dataset('tomogram', data=tomogram)
                    #         hf.create_dataset('sinogram', data=[])    
    cr = msc.import_module_from_path('crystal', os.path.join(sample_dir,'analysis','crystal.py'))
    if not os.path.isfile(os.path.join(sample_dir,'analysis',f'difflets_{cr.odf_mode}_{cr.hsh_max_order}.h5')):
        check_powder_pattern()

    mod = model_textom( sample_dir, light=light_mode )

def list_sample_rotations():
    """Gives a list in the terminal of all projections present in the model, with rotation and tilt angle. 
    Useful to choose a certain projection for other functions using index.
    """
    print('Index\tInner\tOuter')
    for g in range(mod.Omega.size):
        print(f'{g}\t{np.round(mod.Omega[g]*180/np.pi,1)}\t{np.round(mod.Kappa[g]*180/np.pi,1)}')

def show_sample_outline( ):
    """Plots the sample outline after masking.
    """
    with h5py.File(os.path.join(sample_dir,'analysis','projectors.h5'), 'r') as hf:
        tomogram = hf['tomogram'][()]
        mask_voxels = hf['mask_voxels'][()]
    msk.check_tomogram(tomogram, mask_voxels)

def mask_peak_regions( projection=0, datafile_pattern='.h5' ):
    """lets the user choose the regions that contain the peaks for fitting

    Parameters
    ----------
    projection : int, optional
        projection index, by default 0
    datafile_pattern : str, optional
        allows use a certain file that contains the pattern, by default '.h5'
    """
    filelist = dat.get_data_list(sample_dir, datafile_pattern) # get integrated files
    cakemask_path = os.path.join(sample_dir, 'analysis', 'mask_detector_cake.h5')
    q_powder, powder = dat.get_powder1d(
        os.path.join(sample_dir,'data_integrated',filelist[projection]),
        cakemask_path
    )
    cr = msc.import_module_from_path('crystal', os.path.join(sample_dir,'analysis','crystal.py'))
    powder = powder[ np.logical_and(q_powder>=cr.q_range[0],q_powder<=cr.q_range[1]) ] # limit q-range
    q_powder = q_powder[ np.logical_and(q_powder>=cr.q_range[0],q_powder<=cr.q_range[1]) ]
    path_peak_regions = os.path.join(sample_dir,'analysis','peak_regions.txt') # here the peak regions will be saved
    dat.mask_peak_regions(mod,q_powder,powder,path_peak_regions) # interactive masking by user
    detmask_path = os.path.join(sample_dir,'analysis','fit_detmask.txt') # reset detector mask, as of q-bins might have changed
    if os.path.isfile(detmask_path):
        msc.cp_add_dt(detmask_path, os.path.join(sample_dir,'analysis'),now=False) # saves the old mask with date
        os.remove(detmask_path)
    return path_peak_regions

def mask_baseline_regions( projection=0, datafile_pattern='.h5' ):
    """lets the user choose the regions that contain the peaks for fitting

    Parameters
    ----------
    projection : int, optional
        projection index, by default 0
    datafile_pattern : str, optional
        allows use a certain file that contains the pattern, by default '.h5'
    """
    filelist = dat.get_data_list(sample_dir, datafile_pattern) # get integrated files
    cakemask_path = os.path.join(sample_dir, 'analysis', 'mask_detector_cake.h5')
    q_powder, powder = dat.get_powder1d(
        os.path.join(sample_dir,'data_integrated',filelist[projection]),
        cakemask_path )
    cr = msc.import_module_from_path('crystal', os.path.join(sample_dir,'analysis','crystal.py'))
    powder = powder[ np.logical_and(q_powder>=cr.q_range[0],q_powder<=cr.q_range[1]) ] # limit q-range
    q_powder = q_powder[ np.logical_and(q_powder>=cr.q_range[0],q_powder<=cr.q_range[1]) ]
    path_baseline_regions = os.path.join(sample_dir,'analysis','baseline_regions.txt') # here the peak regions will be saved
    dat.mask_for_baseline(mod,q_powder,powder,path_baseline_regions) # interactive masking by user
    return path_baseline_regions

def check_baselines( projection=0, datafile_pattern='.h5' ):
    """Picks some data containing from the given projection and calculates baselines with all available methods,
    using the input parameters from the background_subtraction.py file.
        
    Parameters
    ----------
    projection : int, optional
        projection index, by default 0
    datafile_pattern : str, optional
        allows use a certain file that contains the pattern, by default '.h5'
    """
    bl_path_sample = os.path.join(sample_dir,'analysis','background_subtraction.py')
    if not os.path.isfile( bl_path_sample ):
        bl_path_module = hdl.get_file_path('textom',os.path.join('input','background_subtraction.py'))
        os.makedirs(os.path.join(sample_dir,'analysis'), exist_ok=True )
        shutil.copyfile(bl_path_module, bl_path_sample )
    
    cakemask_path = os.path.join(sample_dir, 'analysis', 'mask_detector_cake.h5')
    cake_mask = h5py.File(cakemask_path,'r')['mask_cake'][()].astype(bool)

    happy = 'n'
    while happy != 'y':
        hdl.open_with_editor(bl_path_sample)
        bl = msc.import_module_from_path('background_subtraction', bl_path_sample)
        # load some data for testing
        filelist = dat.get_data_list(sample_dir, datafile_pattern)
        hf = h5py.File(os.path.join(sample_dir,'data_integrated',filelist[projection]), 'r')
        q_1d = hf['radial_units'][()].flatten()
        qmsk = np.logical_and(q_1d>=bl.q_min, q_1d<=bl.q_max )
        q_1d = q_1d[qmsk]
        data_2d = hf['cake_integ']#[:,:,qmsk]

        # get chosen baseline regions for masking q-values
        path_bl_regions = os.path.join(sample_dir,'analysis','baseline_regions.txt')
        if not os.path.isfile( path_bl_regions ):
            mask_baseline_regions()
        bl_reg, _ = dat.load_peak_regions(path_bl_regions)
        q_mask, _ = dat.get_q_mask( q_1d, bl_reg )
        # get peak regions for hkl and choosing 
        path_peak_regions = os.path.join(sample_dir,'analysis','peak_regions.txt')
        if not os.path.isfile( path_peak_regions ):
            mask_peak_regions()
        peak_reg, hkl = dat.load_peak_regions(path_peak_regions)

        # make a graph with several random data and fits
        f,ax = plt.subplots(3,3, figsize=(14,12), sharex=True,sharey=True)
        k,s = 0,0
        pk = np.where(hkl)[0][0] # get the index of a non-empty peak
        while k < 9:
            r = np.random.randint(data_2d.shape[0])
            pattern_1d = nb.masked_mean_axis0(data_2d[r,:,qmsk], cake_mask[:,qmsk])
            hfreg = (peak_reg[pk,1] - peak_reg[pk,0])/2
            if dat.any_peak(
                pattern_1d[np.logical_and(q_1d > peak_reg[pk,0]-hfreg, q_1d < peak_reg[pk,1]+hfreg)],0.8) :
                ax[k//3,k%3].plot(q_1d, pattern_1d, '-x', label='data')
                ax[k//3,k%3].plot(q_1d, bln.no_baseline(q_1d, pattern_1d, q_mask), label='no baseline')
                ax[k//3,k%3].plot(q_1d, bln.linear_baseline(q_1d, pattern_1d, q_mask), label='linear')
                ax[k//3,k%3].plot(q_1d, bln.chebyshev_baseline(q_1d, pattern_1d, q_mask, order=bl.order_chebyshev), label='chebyshev')
                # ax[k//3,k%3].plot(q_1d, bln.auto_chebyshev(q_1d, pattern_1d, q_mask, np.array(
                #     (bl.order_chebyshev, bl.pre_order, bl.k_sigma, bl.peak_expand))), label='auto_chebyshev')
                if mod:
                    q = mod.Qq_det.reshape(mod.detShape)[0]
                    powder = mod.powder_pattern * pattern_1d.max()/mod.powder_pattern.max()
                    for (xi, yi, l) in zip(q, powder, mod.hkl):
                        ax[k//3,k%3].plot([xi,xi],[0,yi],'r')
                        ax[k//3,k%3].text(xi, yi, l, va='bottom', ha='center')
                k += 1
            s+=1 # safety counter
            if s==5000:
                break
        ax[2,0].set_xlabel('q / nm^-1')
        ax[2,1].set_xlabel('q / nm^-1')
        ax[2,2].set_xlabel('q / nm^-1')
        ax[0,0].set_ylabel('Intensity')
        ax[1,0].set_ylabel('Intensity')
        ax[2,0].set_ylabel('Intensity')
        ax[0,0].legend()
        f.suptitle('Check baseline subtraction and choose the desired method')
        f.tight_layout()
        print('\tPlotted baselines with different modes. Choose the best one and enter parameters in your background_subtraction.py file. Close figure and type n to replot with new parameters')
        plt.show(block=True)
        happy = input('\t\thappy? (y/n) ')

# def absorption_correction(absorption_tomogram=False, absorption_constant_voxel=False):
#     abc.absorption_correction(sample_dir, mod,
#         absorption_constant_voxel=absorption_constant_voxel, absorption_tomogram=absorption_tomogram)

def preprocess_data( proj_test=0, pattern='.h5', use_ion=True, check_baselines_flag=True ):
    """Loads integrated data and pre-processes them for TexTOM

    Parameters
    ----------
    proj_test : int, optional
        projection index (only for displaying), by default 0
    pattern : str, optional
        substring contained in all files you want to use, 
        (this actually filters the files you process), by default '.h5'
    use_ion : bool, optional
        choose if you want to normalize data by the field 'ion' in the 
        data files, by default True
    """    
    if mod is None:
        make_model()
    path_peak_regions = os.path.join(sample_dir,'analysis','peak_regions.txt')
    if not os.path.isfile( path_peak_regions ):
        mask_peak_regions(proj_test, pattern)
    path_bl_regions = os.path.join(sample_dir,'analysis','baseline_regions.txt')
    if not os.path.isfile( path_peak_regions ):
        mask_baseline_regions(proj_test, pattern)
    path_background_subtraction = os.path.join(sample_dir,'analysis','background_subtraction.py')
    # if not os.path.isfile( path_background_subtraction ):
    if check_baselines_flag:
        check_baselines(proj_test, pattern)
    cakemask_path = os.path.join(sample_dir, 'analysis', 'mask_detector_cake.h5')

    # path_detector_mask = os.path.join(sample_dir,'analysis','fit_detmask.txt')
    # if not os.path.isfile( path_detector_mask ):
    #     mask_detector_pixels(proj_test, pattern)
    dat.import_data( sample_dir, pattern, mod, 
                     path_background_subtraction, path_peak_regions, path_bl_regions, cakemask_path,
                     geo_path=os.path.join(sample_dir,'analysis/geometry.py'),
                     use_ion=use_ion,
                     )

def mask_detector_regrouped( ):
    """ Re-check the mask for the data reduced to only peaks

    """
    # detmask_path = os.path.join(sample_dir,'analysis','fit_detmask.txt')
    with h5py.File(os.path.join(sample_dir,'analysis','data_textom.h5'), 'r') as hf:
        # q_in = hf['q_in'][()].flatten()
        # hkl = hf['hkl'][()]
        # peak_reg = hf['peak_reg'][()]
        # chi = hf['chi'][()].flatten()
        scanmask_0 = hf['scanmask'][0]
        data = hf['data'][np.where(scanmask_0)[0]].sum(axis=0)
        # cakemask = hf['mask_cake'][()]
        mask_peaks = hf['mask_peaks'][()]
    mask_peaks = msk.mask_detector( data.T, mask_peaks.T ).T
    with h5py.File(os.path.join(sample_dir,'analysis','data_textom.h5'), 'r+') as hf:
        hf['mask_peaks'] = mask_peaks

    # dat.mask_detector( cakemask, detmask_path, data, peak_reg, q_in, chi )

def make_fit( redo=True ):
    """Initializes a TexTOM fit object for reconstructions

    Is automatically performed by the functions that require it

    Parameters
    ----------
    redo : bool, optional
        set True for recalculating, by default True
    """    
    global fit
    if mod is None:
        make_model()
    if (fit is None or redo):
        fit = fitting( sample_dir, mod )

def optimize( mode=4,
             proj='full', zero_peak=None,
             redo_fit=False,
             step_size_0=1.,
             tol=1e-3, minstep=1e-9, max_iter=500,
             alg='simple', save_h5=True,
              ):
    """Performs a single TexTOM parameter optimization

    Parameters
    ----------
    mode : int, optional
        set 0 for only optimizing order 0, 1 for highest order, 2 for all,
        3 for all but the lowest order, 4 for all with enhanced stepsize calibration
        by default 4
    proj : str, optional
        choose projections to be optimized: 'full', 'half', 'third', 'notilt', 
        by default 'full'
    zero_peak : int or None
        index of the peak you want to use for 0-order fitting (should be as
        isotropic as possible), if None uses the whole dataset, default None
    redo_fit : bool, optional
        recalculate the fit object, by default False
    step_size_0 : float, optional
        starting value for automatic stepsize tuning, by default 1.
    tol : float, optional
        tolerance for precision break criterion, by default 1e-3
    minstep : float, optional
        minimum stepsize in line search (another break criterion), by default 1e-9
    max_iter : int, optional
        maximum number of iterations, by default 500
    alg : str, optional
        choose algorithm between 'backtracking', 'simple', 'quadratic', 
        by default 'simple'
    save_h5 : bool, optional
        choose if you want to save the result to the directory analysis/fits, 
        by default True    
    """    
    global opt, results
    make_fit( redo=redo_fit )
    fit.choose_projections( proj )
    if mod.odf_mode =='hsh' and not np.any(fit.C):
        print( 'Optimizing 0 order intensities')
        fit.prepare_fit_c0(zero_peak)
        # opimize c0 from average intensity
        fit.C, opt = optimizer.optimize( fit, 0, tol=1e-3, minstep=1e-9, alg=alg, itermax=max_iter, step_size_0=step_size_0 ) 
    proj_c0 = False if mode==1 else True
    fit.C, opt = optimizer.optimize( fit, mode,
                alg=alg, tol=tol, minstep=minstep, itermax=max_iter, project_c0=proj_c0, step_size_0=step_size_0 )
    plot.loss(opt['loss'],opt['resname'])
    results['optimization'] = opt['resname']
    results['scaling'] = fit.C[:,0].reshape(mod.nVox)
    if save_h5:
        os.makedirs(os.path.join(sample_dir,'analysis','fits'), exist_ok=True)
        hdl.save_dict_to_h5( opt, os.path.join(sample_dir,'analysis','fits',opt['resname']))
    os.makedirs(os.path.join(sample_dir,'results'), exist_ok=True)

# def optimize_auto( max_order=8, start_order=None, zero_peak=None,
#                 tol_0 = 1e-7, tol_1 = 1e-3, tol_2 = 1e-4,
#                 step_size_0=1,
#                 minstep_0 = 1e-9, minstep_1 = 1e-9, minstep_2 = 1e-9,
#                 max_iter = 500,
#                 projections='full', alg='simple', adj_scal = False,
#                 redo_fit=False,
#               ):
#     """Automated TexTOM reconstruction workflow

#     Parameters
#     ----------
#     max_order : int, optional
#         maximum HSH order to be used, by default 8    
#     start_order : int or None, optional
#         lowest order to be fitted, if None continues where you are standing, 
#         by default None
#     zero_peak : int or None
#         index of the peak you want to use for 0-order fitting (should be as
#         isotropic as possible), if None uses the whole dataset, default None
#     tol_0 : _type_, optional
#         tolerance for precision break criterion, mode 0, by default 1e-7
#     tol_1 : _type_, optional
#         tolerance for precision break criterion, mode 1, by default 1e-3
#     tol_2 : _type_, optional
#         tolerance for precision break criterion, mode 2, by default 1e-4
#     minstep_0 : _type_, optional
#         minimum stepsize in line search, mode 0, by default 1e-9
#     minstep_1 : _type_, optional
#         minimum stepsize in line search, mode 1, by default 1e-9
#     minstep_2 : _type_, optional
#         minimum stepsize in line search, mode 2, by default 1e-9
#     max_iter : int, optional
#         maximum number of iterations, by default 500
#     projections : str, optional
#         choose projections to be optimized: 'full', 'half', 'third', 'notilt', by default 'full'
#     alg : str, optional
#         choose algorithm between 'backtracking', 'simple', 'quadratic', 
#         by default 'simple'
#     adj_scal : bool, optional
#         rescales data after 0-order optimization, see adjust_data_scaling(), by default True
#     redo_fit : bool, optional
#         recalculate the fit object, by default False
#     """
#     global opt, results
#     make_fit( redo=redo_fit )
#     t0=time()
#     os.makedirs(os.path.join(sample_dir,'analysis','fits'), exist_ok=True)
#     fit.choose_projections( projections ) 
#     orders = mod.get_orders(n_max=max_order,info=False,exclude_ghosts=True)
#     if not isinstance(start_order, int):
#         if max(fit.ns)>0:
#             start_order = min(orders[orders>max(fit.ns)])
#         else:
#             start_order = 0
#     orders = orders[orders>=start_order]
#     if start_order==0:
#         print( 'Optimizing 0 order intensities')
#         fit.prepare_fit_c0(zero_peak)
#         # opimize c0 from average intensity
#         fit.C, opt = optimizer.optimize( fit, 0, tol=tol_0, minstep=minstep_0, alg=alg, itermax=max_iter, step_size_0=step_size_0 ) 
#         # plot.loss(opt['loss'],opt['resname'])
#         if adj_scal:
#             fit.adjust_data_scaling()
#             # fit.C, opt = optimizer.optimize( fit, 0, tol=tol_0, minstep=minstep_0, alg=alg ) 
#             # plot.loss(opt['loss'],opt['resname'])
#     print( 'Optimizing anisotropy')
#     for n in orders[orders>0]:
#         fit.set_orders( mod, n )
#         # optimize only highest
#         fit.C, opt = optimizer.optimize( fit, 3, tol=tol_1, minstep=minstep_1, alg=alg, project_c0=False, itermax=30, step_size_0=step_size_0 ) 
#         # plot.loss(opt['loss'],opt['resname'])
#         hdl.save_dict_to_h5( opt, os.path.join(sample_dir,'analysis','fits',opt['resname']))

#         # optimize all orders (mainly the 0th one though, the others converge slowly in this mode)
#         fit.C, opt = optimizer.optimize( fit, 2, tol=tol_2, minstep=minstep_2, alg=alg, itermax=30, step_size_0=step_size_0 ) 
#         # plot.loss(opt['loss'],opt['resname'])

#     fit.C, opt = optimizer.optimize( fit, 3, tol=tol_1, minstep=minstep_1, alg=alg, project_c0=False, itermax=max_iter, step_size_0=step_size_0 ) 
#     hdl.save_dict_to_h5( opt, os.path.join(sample_dir,'analysis','fits',opt['resname']))
#     print(f'Total optimization time: {(time()-t0)/60} min')
#     results['optimization'] = opt['resname']
#     results['scaling'] = fit.C[:,0].reshape(mod.nVox)
#     check_projections_average()
#     check_projections_orientations()

def list_opt(info=True):
    """Shows all stored optimizations in the terminal
    """
    opt_dir = os.path.join(sample_dir, 'analysis','fits')
    optimizations = msc.list_files_by_modification_time(opt_dir,reverse=True,extension='.h5')
    for o in optimizations:
        if info:
            try:
                path_opt = os.path.join( sample_dir, 'analysis', 'fits', o ) # path to the opt.h5 file
                with h5py.File(path_opt, 'r') as hf:
                    loss = hf['loss'][-1]
                    mdl =  hf['MDL'][()]
                    prec =  hf['prec'][()]
                print(f'\r{o} |loss: {loss:.1f} |MDL: {mdl:.2e} |prec: {prec:.2e}')
            except: # this takes care of old file where MDL was not included, can be removed a some point
                print(f'\r{o}')
        else:
            print(f'\r{o}')

def load_opt( h5path = 'last', redo_fit=False ): 
    """Loads a previous Textom optimization into memory
    seful: load_opt(results['optimization'])

    Parameters
    ----------
    h5path : str, optional
        filepath, just filename or full path
        if 'last', uses the youngest file is used in analysis/fits/, 
        by default 'last'
    """      
    if h5path == 'last':
        h5path = msc.lastfile( os.path.join(sample_dir,'analysis','fits'), '*.h5' )
    elif os.path.dirname(h5path) == '': # if only filename
        h5path = os.path.join(sample_dir,'analysis','fits',h5path)
    print(f'Loading {os.path.basename(h5path)}')
    global fit,mod,opt, results
    make_fit( redo=redo_fit )
    # i0 = h5path.find('nmax')
    # i1 = h5path.find('_', i0)
    # nmax = int( h5path[i0+4 : i1] )
    # fit.set_orders(mod,nmax, exclude_ghosts=exclude_ghosts)
    opt = hdl.load_h5_to_dict( h5path )
    fit.C = opt['c'].astype(data_type)
    results['optimization'] = opt['resname']
    results['scaling'] = fit.C[:,0].reshape(mod.nVox)
    print('Loaded opt object and hsh coefficients to fit.C')

def check_lossfunction(opt_file=None):
    """Plots the lossfunction of an optimization

    Parameters
    ----------
    opt_file : str or None, optional
        name of the file in the fit directory, if None takes currently loaded one, by default None
    """
    if not opt_file: # get the filename from the results dict
        opt_file = results['optimization']
        if isinstance(opt_file,bytes):
            opt_file = results['optimization'].decode('utf-8')
    path_opt = os.path.join( sample_dir, 'analysis', 'fits', opt_file ) # path to the opt..h5 file
    with h5py.File(path_opt, 'r') as hf:
        loss = hf['loss'][()]
    title = opt_file.split('.')[0]
    plot.loss(loss,title)

def check_fit_average( ):
    """Plots measured and reconstructed average intensity for each diffraction pattern

    """    
    ## this plot should be per tilt angle with the rotation angle at the bottom
    if not hasattr(fit, 'data_0D'):
        fit.prepare_fit_c0()
    plt.figure()
    plt.plot(fit.data_0D, label='data')
    plt.plot(fit.projections_c0(fit.C),label='fit')
    plt.legend()
    plt.xlabel('Image index')
    plt.ylabel('Average intensity')
    plt.show()

def check_fit_per_index( index, mode='line' ):
    """Plots measured and reconstructed intensity for a chosen diffraction pattern

    """    
    plot.singlefit2D(fit, index,
        polar=False, mode=mode,
        log=False, show_off=True,
        show=False)

def check_fit_random( N=10, mode='line' ):
    """Generates TexTOM reconstructions and plots them with data for random points

    Parameters
    ----------
    N : int, optional
        Number of images created, by default 10    
    mode : str, optional
        plotting mode, 'line' or 'color', by default line
    """    
    for _ in range(N):
        idx = np.random.randint(fit.gt_mask.shape[0])
        plot.singlefit2D(fit, idx,
            polar=False, mode=mode,
            log=False, show_off=True,
            show=False)
    plt.show()

def check_residuals( ):
    """Plots the squared residuals summed over each projection
    """    
    if fit is None:
        print('\tNo fit available, load or obtain result first')
        return
    # fit.choose_projections('full') ## doesn't work with less projections yet (else modify fit.data_av)
    # if np.all(fit.ns == np.array([0])):
    #     if not hasattr( fit, 'data_av' ):
    #         fit.prepare_fit_c0()
    #     proj = fit.projections_c0( fit.C )
    #     res = fit.insert_fov( (proj-fit.data_av)**2 ).sum(axis=1)
    # else:
    #     #calculate full projections and get residuals for all data per proj
    #     print('todo')
    plot.projection_residuals( fit )

def check_projections_average( G=None ):
    """Plots the reconstructed average intensity for chosen projections with data
    
    Parameters
    ----------
    G : int or ndarray or None, optional
        projection indices, if None takes 10 equidistant ones, by default None
    """    
    if fit is None:
        print('\tNo fit available, load or obtain result first')
        return
    if G is None: # plot 10 projections over all angles
        G = np.linspace(0, fit.scanmask.shape[0]-1,num=10,dtype=int)
    if not hasattr( fit, 'data_av' ):
        fit.prepare_fit_c0()
    proj = fit.insert_fov( fit.projections_c0( fit.C ) )
    d_av = fit.insert_fov( fit.data_0D )
    if hasattr(mod, 'fov_single'):
        fov = mod.fov_single
    else:
        fov = mod.fov
    for g in np.atleast_1d(G):
        title = f'Projection {g}: kap {mod.Kappa[g]*180/np.pi:.1f}, ome {mod.Omega[g]*180/np.pi:.1f}'
        plot.compare_projection_av( 
            d_av[g].reshape(fov), proj[g].reshape(fov), title=title,
         )

def check_projections_residuals( g=0 ):
    """Plots the residuals per pixel for chosen projections with data
    
    Parameters
    ----------
    g : int e, optional
        projection index, by default 0
    """    
    print('Opened figures showing residuals. Click on a pixel to show the TexTOM fit')
    if fit is None:
        print('\tNo fit available, load or obtain result first')
        return
    title = f'Sum of Residuals\nProjection {g}: kap {np.round(mod.Kappa[g]*180/np.pi,1)}, ome {np.round(mod.Omega[g]*180/np.pi,1)}'
    plot.image_residuals( fit, g, mod.fov, hkl=fit.hkl, title=title, ) # hkl

def check_projections_orientations( G=None ):
    """Plots the reconstructed average orientations for chosen projections with data
    
    Parameters
    ----------
    G : int or ndarray or None, optional
        projection indices, if None takes 10 equidistant ones, by default None
    """    
    if fit is None:
        print('\tNo fit available, load or obtain result first')
        return
    if G is None: # plot 10 projections over all angles
        G = np.linspace(0, fit.scanmask.shape[0]-1,num=10,dtype=int)
    if hasattr(mod, 'fov_single'):
        fov = mod.fov_single
    else:
        fov = mod.fov
    for g in np.atleast_1d( G ):
        title = f'Projection {g}: kap {np.round(mod.Kappa[g]*180/np.pi,1)}, ome {np.round(mod.Omega[g]*180/np.pi,1)}'
        ori_dat, ori_fit = fit.check_orientations(g)
        plot.compare_projection_ori(  
            ori_dat.reshape((ori_dat.shape[0],*fov)), 
            ori_fit.reshape((ori_dat.shape[0],*fov)),
            fit.q, hkl=fit.hkl, title=title, )
        
def calculate_orientation_statistics( ):
    """Calculates prefered orientations and stds and saves them to results dict

    """
    global results
    if (mod is None or fit is None):
        print('model/fit not defined!')
        return
    results['scaling'] = fit.C[:,0].reshape(mod.nVox)
    print('\tExtracting mean orientations')
    g_pref = mod.preferred_orientations( fit.C[mod.mask_voxels] )
    results['g_pref'] = mod.insert_sparse_tomogram(g_pref)
    print('\tExtracting stds')
    stds = mod.std_sample( fit.C[mod.mask_voxels], g_pref )
    results['std']=mod.insert_sparse_tomogram(stds)
    # export vtk-file for paraview
    crystal_data = cry.parse_cif(mod.cr.cifPath)
    a_pref, b_pref, c_pref = mod.abc_pref_sample( g_pref, crystal_data['lattice_vectors'] )
    results['a_pref'] = mod.insert_sparse_tomogram(a_pref)
    results['b_pref'] = mod.insert_sparse_tomogram(b_pref)
    results['c_pref'] = mod.insert_sparse_tomogram(c_pref)
    results['inv_pf'] = orx.inverse_pf_stack(results['g_pref'], mod.symmetry, mod.mask_voxels)
    print("\tAdded to results: 'std', 'g_pref', 'a_pref', 'b_pref', 'c_pref', 'inv_pf'")

def calculate_order_parameters(axis=(0,0,1)):
    """Calculates nematic order parameters and directors per voxel and adds them to results

    Parameters
    ----------
    axis : tuple, optional
        choose the axis direction along which particles are aligned, by default (0,0,1)
    """
    global results
    if (mod is None or fit is None):
        print('model/fit not defined!')
        return
    results['scaling'] = fit.C[:,0].reshape(mod.nVox)
    directions, Gc = mod.directions_from_orientations( np.array(axis, data_type) )
    odfs = mod.odf.get_odf_batch(fit.C[mod.mask_voxels])
    order_parameters, directors = ord.order_parameters_parallel( directions, odfs )
    results['order_parameters'] = mod.insert_sparse_tomogram(order_parameters)
    results['directors'] = mod.insert_sparse_tomogram(directors)
    print("\tAdded to results: 'order_parameters', 'directors'")

def calculate_segments(thresh=10, min_segment_size=30, max_segments_number=31):
    """Segments the sample based on misorientation borders

    Parameters
    ----------
    thresh : float, optional
        misorientation angle threshold inside segment in degree, by default 10
    min_segment_size : int, optional
        minimum number of voxels in segment, by default 30
    max_segments_number : int, optional
        maximum number of segments (ordered by size), by default 32
    """
    global results
    cr = msc.import_module_from_path('crystal', os.path.join(sample_dir,'analysis','crystal.py'))
    difflets_path = os.path.join(sample_dir,'analysis',f'difflets_{cr.odf_mode}_{cr.odf_par}.h5')
    if os.path.isfile(difflets_path):
        with h5py.File(difflets_path, 'r') as hf:
            symmetry = hf['symmetry'][()].decode('utf-8')
    mx,my,mz,mori = seg.mori_3d( results['g_pref'], symmetry )
    plt.figure()
    plt.hist(mori[mori<3.14]*180/np.pi,50)
    plt.plot([thresh,thresh],[mori.shape[0],mori.shape[0]],'--')
    plt.xlabel('Misorientation [deg]')
    plt.ylabel('No of voxels')
    labeled_zones,zone_sizes = seg.label_zones(mori, thresh*np.pi/180,
                                               min_segment_size, max_segments_number)
    results['segments'] = labeled_zones
    mori[mori>3.14] = np.nan
    results['mori'] = mori * 180 / np.pi
    results['mori'][results['mori']>179] = np.nan
    # results['segments'][results['segments']==0] = np.inf
    plt.figure()
    plt.bar(range(zone_sizes.size),zone_sizes)
    plt.xlabel('Zone label')
    plt.ylabel('No of voxels in zone')
    nvseg,nvtot = zone_sizes.sum(), (mori<3.14).sum()
    show_volume(data=['segments','mori'],cut=0)
    print(f'\tSegmented voxels: {nvseg}/{nvtot} ({nvseg/nvtot*100:.1f} %)')
    print("\tAdded to results: 'mori', 'segments'")

def show_volume( data='scaling', plane='z', colormap='inferno', cut=1, save=False, show=True ):
    """Visualizes the whole sample by slices, colored by a value of your choice

    Parameters
    ----------
    data : str or list, optional
        name of one entry in the results dict or list of entries, 
        by default 'scaling'
    plane : str, optional
        sliceplane 'x'/'y'/'z', by default 'z'
    colormap : str, optional
        identifier of matplotlib colormap, default 'inferno'
        https://matplotlib.org/stable/users/explain/colors/colormaps.html
    cut : int, optional
        cut colorscale at upper and lower percentile, by default 0.1
    save : bool, optional
        saves tomogram as .gif to results/images/, by default False
    show : bool, optional
        open the figure upon calling the function, by default True
    """
    if isinstance(data,np.ndarray):
        if data.ndim==3:
            names=['custom data']
            data, borders = msc.smallest_subvolume(data)
            data=[data]
    elif isinstance(data,str):
            names = [data]
            data, borders = msc.smallest_subvolume(results[data])
            data = [data]      
    else:
        names = data
        data = [results[key] for key in data]
        borders=None
    if save:
        save = os.path.join(sample_dir, 'results', 'images', f'{names[0]}_{plane}_{msc.timestring()}.gif')
    print(f'\tPlotting tomogram using {names[0]} as colorcode.\n\tGo through layers with the slider, click on voxel to plot the local ODF')
    plot.interactive_tomogram( np.array(data), names, show_voxel_odf, 
                    title='Slice-by-slice view.\nClick on a voxel to show ODF (first time might take a few seconds)',
                    borders=borders,
                    cmap=colormap, sliceplane=plane, cut=cut, save_vid_path=save,
                    show=show )


def show_slice_ipf( h, plane='z' ):
    """Plots an inverse pole figure of a sample slice

    Parameters
    ----------
    h : int
        height of the slice
    plane : str, optional
        slice direction: x/y/z, by default 'z'
    """
    cr = msc.import_module_from_path('crystal', os.path.join(sample_dir,'analysis','crystal.py'))
    difflets_path = os.path.join(sample_dir,'analysis',f'difflets_{cr.odf_mode}_{cr.hsh_max_order}.h5')
    if os.path.isfile(difflets_path):
        with h5py.File(difflets_path, 'r') as hf:
            symmetry = hf['symmetry'][()].decode('utf-8')
    ipf_slice,_ = _slice('g_pref', h, plane)
    orx.inverse_pf_map( ipf_slice, symmetry )

def show_slice_directions( h, plane='z', direction='c' ):
    """Plots an inverse pole figure of a sample slice

    Parameters
    ----------
    h : int
        height of the slice
    plane : str, optional
        slice direction: x/y/z, by default 'z'
    """
    dir_slice, bounds = _slice(f'{direction}_pref', h, plane)
    scal_slice,_ = _slice('scaling',h,plane)
    plot.plot_orientations_slice( dir_slice, 
                                 scal_slice[bounds[0]:bounds[1]+1,bounds[2]:bounds[3]+1],
                                 title=f'{direction}-axis, {plane} = {h}' )

def show_volume_ipf( plane='z', save=False, show=True ):
    """Plots inverse pole figures as a tomogram with a slider to scroll through the sample

    Parameters
    ----------
    plane : str, optional
        slice direction: x/y/z, by default 'z'
    save : bool, optional
        saves tomogram as .gif to results/images/, by default False
    show : bool, optional
        open the figure upon calling the function, by default True
    """
    cr = msc.import_module_from_path('crystal', os.path.join(sample_dir,'analysis','crystal.py'))
    difflets_path = os.path.join(sample_dir,'analysis',f'difflets_{cr.odf_mode}_{cr.hsh_max_order}.h5')
    if os.path.isfile(difflets_path):
        with h5py.File(difflets_path, 'r') as hf:
            symmetry = hf['symmetry'][()].decode('utf-8')
    if save:
        save = os.path.join(sample_dir, 'results', 'images', f'ipf_{plane}_{msc.timestring()}.gif')
    orx.plot_ipf_movie(results['inv_pf'], symmetry, plane, save_vid_path=save, show=show)

def show_histogram(x, nbins=50, cut=0.1, segments=None, save=False):
    """plots a histogram of a result parameter

    Parameters
    ----------
    x : str,
        name of a scalar from results
    bins : int, optional
        number of bins, by default 50
    cut : int, optional
        cut upper and lower percentile, by default 0.1
    segments : list of int, optional
        list of segments or None for all data, by default None
    save : bool/str, optional
        saves image with specified file extension, e.g. 'png', 'pdf'
        if True uses png, by default False
    """
    global results
    f,ax = plt.subplots()
    if segments:
        data, high, low = [], -np.inf, np.inf
        for s in segments:
            d = results[x][results['segments']==s]
            data.append( d[~np.isnan(d)] )
            low = min(low, np.percentile(d, cut))
            high = max(high, np.percentile(d, 100-cut))
        ax.hist( data, bins=nbins, 
            range=(low,high),
            label=[str(s) for s in segments],
            # histtype='step', stacked=True, fill=False
            )
        ax.legend()
        ax.set_title('Per segment')
    else:
        with h5py.File(os.path.join(sample_dir,'analysis/projectors.h5'), 'r') as hf:
            mask = hf['mask_voxels'][()]
        data = results[x].flatten()[mask]
        data = data[~np.isnan(data)]
        ax.hist( data, bins=nbins, 
                range=(np.percentile(data, cut),np.percentile(data, 100-cut)) )
        ax.set_title('All voxels')
    ax.set_xlabel(x)
    ax.set_ylabel('No. of voxels')
    if save:
        if isinstance(save, bool):
            save='png'
        f.savefig(os.path.join(sample_dir,'results','images',f'histogram_{x}_{msc.timestring()}.{save}'))

def show_correlations( x, y, nbins=50, cut=(0.1,0.1), segments=None, save=False ):
    """Plots a 2D histogram between 2 result parameters

    Parameters
    ----------
    x : str,
        name of a scalar from results
    y : str,
        name of a scalar from results
    bins : int, optional
        number of bins, by default 50
    cut : tuple, optional
        cut upper and lower percentile of both parameters, by default (0.1,0.1)
    segments : list, optional
        list of segments or None for all data, by default None
    save : bool/str, optional
        saves image with specified file extension, e.g. 'png', 'pdf'
        if True uses png, by default False
    """

    if segments:
        for s in segments:
            f,ax = plt.subplots()
            data_x = results[x][results['segments']==s]
            data_y = results[y][results['segments']==s]
            filter_nan = ~np.logical_or(np.isnan(data_x), np.isnan(data_y))
            data_x, data_y = data_x[filter_nan], data_y[filter_nan]
            ax.hist2d( data_x, data_y, bins=nbins,
                    range=((np.percentile(data_x, cut[0]),np.percentile(data_x, 100-cut[0])),
                            (np.percentile(data_y, cut[1]),np.percentile(data_y, 100-cut[1]))) )
            ax.set_title(f'Segment {s}')
            ax.set_xlabel(x)
            ax.set_ylabel(y)
        if save:
            if isinstance(save, bool):
                save='png'
            f.savefig(os.path.join(sample_dir,'results','images',f'correlations??_{x}_{y}_segment{s}_{msc.timestring()}.{save}'))
    else:
        with h5py.File(os.path.join(sample_dir,'analysis/projectors.h5'), 'r') as hf:
            mask = hf['mask_voxels'][()]
        f,ax = plt.subplots()
        data_x = results[x].flatten()[mask]
        data_y = results[y].flatten()[mask]
        filter_nan = ~np.logical_or(np.isnan(data_x), np.isnan(data_y))
        data_x, data_y = data_x[filter_nan], data_y[filter_nan]
        ax.hist2d( data_x, data_y, bins=nbins,
                range=((np.percentile(data_x, cut[0]),np.percentile(data_x, 100-cut[0])),
                        (np.percentile(data_y, cut[1]),np.percentile(data_y, 100-cut[1]))) )
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        if save:
            if isinstance(save, bool):
                save='png'
                f.savefig(os.path.join(sample_dir,'results','images',f'correlations_{x}_{y}_{msc.timestring()}.{save}'))

def show_voxel_odf( x,y,z, num_samples=1000, representation='quaternion', info=True ):
    """Show a 3D plot of the ODF in the chosen voxel

    Parameters
    ----------
    x : int
        voxel x-coordinate
    y : int
        voxel y-coordinate
    z : int
        voxel z-coordinate
    representation : 'quaternion'|'euler'|'rodrigues'
      different styles ('euler' and 'rodrigues' still experimental)
    """
    iv = np.ravel_multi_index((x,y,z), mod.nVox)
    if np.any(fit.C[iv]):
        Gc, odf = mod.odfFromC(fit.C[iv])
        title = f'Voxel {x}/{y}/{z}'
        if representation=='euler':
            euler_angles = rot.EulerfromQ(rot.QfromOTP(Gc))
            plot.plot_odf_slices_euler(euler_angles, odf)
        if representation=='rodrigues':
            rodrigues_par = rot.RodfromOTP(Gc)
            plot.plot_odf_slices_rodrigues(rodrigues_par,odf)
        else: #'quaternion'
            orx.plot_odf( rot.QfromOTP(Gc), 
                        odf, mod.symmetry, num_samples=num_samples, title=title )
        # orx.odf_cloud(mod, fit.C[iv], num_samples=num_samples, title=title, 
        #               kernel=kernel, odf_info=info )
    else:
        print('\tNo ODF in this voxel')

def show_voxel_polefigure( x,y,z, hkl=(0,0,1), mode='density',
                     alpha=0.1, num_samples=1e4, recenter=True ):
    """Show a polefigure plot for the chosen voxel and hkl

    Parameters
    ----------
    x : int
        voxel x-coordinate
    y : int
        voxel y-coordinate
    z : int
        voxel z-coordinate
    hkl : tuple, optional
        Miller indices, by default (1,0,0)
    mode : str, optional
        plotting style 'scatter' or 'density', by default 'density'
    alpha : float, optional
        opacity of points, only for scatter, by default 0.1
    num_samples : int/float, optional
        number of samples for plot generation, by default 1e4
    """
    iv = np.ravel_multi_index((x,y,z), mod.nVox)
    title = f'Voxel {x}/{y}/{z}, hkl ({hkl[0]},{hkl[1]},{hkl[2]})'
    if np.any(fit.C[iv]):
        # calculate odf, recenter if necessary, then feed the odf to the function
        Gc, odf = mod.odfFromC(fit.C[iv], recenter=recenter)

        orx.plot_pole_figure(Gc, odf, mod.symmetry, hkl, mode=mode, title=title,
                             num_samples=num_samples, alpha=alpha )
    else:
        print('\tNo ODF in this voxel')

def show_subvolume_average_polefigure( x_range=None,y_range=None,z_range=None, 
                    custom_mask = None,
                    hkl=(1,0,0), mode='density', alpha=0.1, num_samples=1e4 ):
    """Lets you visualize the texture of a chosen part of the sample, specified by ranges or a custom mask.

    Parameters
    ----------
    x_range : tuple or None, optional
        range of voxel coordinates, e.g. (0,10), by default None
    y_range : tuple or None, optional
        range of voxel coordinates, e.g. (0,10), by default None
    z_range : tuple or None, optional
        range of voxel coordinates, e.g. (0,10), by default None
    custom_mask : 3darray(int), optional
        Input a custom voxel-mask via e.g. 
        custom_mask = np.where(results['order_parameters'].flatten() > 0.5)[0], by default None
    hkl : tuple, optional
        Miller indices, by default (1,0,0)
    mode : str, optional
        plotting style 'scatter' or 'density', by default 'density'
    alpha : float, optional
        opacity of points, only for scatter, by default 0.1
    num_samples : _type_, optional
        number of samples for plot generation, by default 1e4
    """
    
    if not x_range:
        x_range = (0, mod.nVox[0])
    if not y_range:
        y_range = (0, mod.nVox[1])
    if not z_range:
        z_range = (0, mod.nVox[2])
    if not np.any(custom_mask):
        custom_mask = mod.mask_voxels

    # bring voxel positions to coordinates
    coords = mod.x_p.copy()
    coords[:,0] -= coords[:,0].min()
    coords[:,1] -= coords[:,2].min()
    coords[:,2] -= coords[:,2].min()

    mask_subvol =  np.where(
        (coords[:,0]>=x_range[0]) & (coords[:,0]<=x_range[1]) &
        (coords[:,1]>=y_range[0]) & (coords[:,1]<=y_range[1]) &
        (coords[:,2]>=z_range[0]) & (coords[:,2]<=z_range[1])
    )[0]
    i_voxels = np.intersect1d( mask_subvol, custom_mask )
    # G_pref = mod.g_ML_sample( fit.C[i_voxels] )
    # Rs_back = mod.get_Rs_stack( np.column_stack( 
    #         (-G_pref[:,0], G_pref[:,1], G_pref[:,2])) )
    # c_av = np.zeros_like(fit.C[0])
    # for k, iv in enumerate(i_voxels):
    #     c_av += Rs_back[k] @ fit.C[iv]
    G_pref = mod.preferred_orientations(fit.C[i_voxels])
    odf_av = mod.odf.get_odf_centered_batch( fit.C[i_voxels], G_pref ).sum(axis=0)
    orx.plot_pole_figure(mod.odf.G_odf, odf_av, mod.symmetry, hkl, mode=mode, 
                        title=f'Average over range x{x_range}, y{y_range}, z{z_range}',
                        num_samples=num_samples, alpha=alpha )

def save_results( ):
    """Saves the results dictionary to a h5 file in the results/ directory

    """
    title = os.path.basename(os.path.dirname(sample_dir))
    types, names = [], []
    res_name = f'results_{msc.timestring()}'
    with h5py.File( os.path.join(sample_dir,'results',f'{res_name}.h5'), 'w' ) as hf:
        hf.create_dataset('title', data=title)
        hf.create_dataset('opt_file', data=results['optimization'])
        for key, value in results.items():
            if isinstance(value,np.ndarray):
                if value.ndim == 3:
                    types.append('Scalar')
                    names.append(key)
                elif value.ndim == 4:
                    types.append('Vector')
                    names.append(key)
                hf.create_dataset( key, data = value )
    print(f'\tCreated results file: {res_name}')

def export_paraview( ):
    """Saves the results dictionary to a h5 file in the results/ directory
    Here, the coordinate system is converted to fortran order (z,y,x)
    """

    with h5py.File(os.path.join(sample_dir,'analysis','projectors.h5'), 'r') as hf:
        nVox = hf['nVox'][()]
    title = os.path.basename(os.path.dirname(sample_dir))
    types, names = [], []
    res_name = f'resultsPV_{msc.timestring()}'
    with h5py.File( 
        os.path.join(sample_dir,'results',f'{res_name}.h5'), 'w' ) as hf:
        hf.create_dataset('title', data=title)
        for key, value in results.items():
            if isinstance(value,np.ndarray):
                if value.ndim == 3:
                    types.append('Scalar')
                    names.append(key)
                    hf.create_dataset( key, data = value.transpose((2,1,0)) )
                elif (value.ndim == 4 and not key == 'g_pref'):
                    types.append('Vector')
                    names.append(key)
                    hf.create_dataset( key, data = value.transpose((2,1,0,3)) )
    print(f'\tCreated results file: {res_name}')
    hdl.write_xdmf_reader(
        os.path.join(sample_dir,'results',f'{res_name}.xdmf'),
        os.path.join(sample_dir,'results',f'{res_name}.h5'),
        (nVox[2],nVox[1],nVox[0]), names, types
    )

def list_results():
    """Shows all results .h5 files in results directory
    """

    res_dir = os.path.join(sample_dir, 'results')
    res_files = msc.list_files_by_modification_time(res_dir,reverse=True,extension='.h5')
    for r in res_files:
        print(f'\r{r}')

def load_results( h5path='last', make_bg_nan=False ):
    """Loads the results from a h5 file do the results dictionary

    Parameters
    ----------
    h5path : str, optional
        filepath, just filename or full path
        if 'last', uses the youngest file is used in results/, 
        by default 'last'
    make_bg_nan : bool, optional
        if true, replaces all excluded voxels by NaN
    """
    global results
    t0=time()
    print('Loading results')
    if h5path == 'last':
        h5path = msc.lastfile( os.path.join(sample_dir,'results'), 'results_*.h5' )
    elif os.path.dirname(h5path) == '': # if only filename
        h5path = os.path.join(sample_dir,'results',h5path)
    with h5py.File( h5path, 'r' ) as hf:
        for key in hf.keys():
            results[key] = hf[key][()]
        if make_bg_nan:
            with h5py.File(os.path.join(sample_dir,'analysis','projectors.h5')) as hf:
                mask = hf['mask_voxels'][()]
                nvox = hf['nVox'][()]
            results[key] = msc.insert_sparse_tomogram(nvox, mask, results[key].flatten()[mask])
            # tmp = np.empty_like(results[key])
            # tmp[:] = np.nan
            # tmp[mask] = results[key][mask]
            # results[key] = tmp
    print(f'\ttook {time()-t0:.2f} s')
    # del results['title']

def list_results_loaded():
    """Shows all results currently in memory
    """
    print('\tLoaded:')
    for res in results.keys():
        print(f'\r\tresults[\'{res}\']')

def save_images( x, ext='raw' ):
    """Export results as .raw or .tiff files for dragonfly

    Parameters
    ----------
    x : str,
        name of a scalar from results, e.g. 'scaling'
    ext : str,
        desired file type by extension, can do 'raw' or 'tiff', default: 'raw'
    """

    if results[x].dtype == np.float64:
        data = results[x].astype(np.float32)
    else:
        data = results[x]
    # data[np.isnan(data)] = 0
    if ext=='raw':
        with open(os.path.join(sample_dir,'results',x+'.raw'), 'wb') as file:
            file.write(data.tobytes())
    elif 'tif' in ext:
        iio.imwrite(
            os.path.join(sample_dir,'results',x+'.tiff'),
            data, plugin="tifffile")
    else:
        print('format not recognized')

def help( method=None, module=None, filter='' ):
    """Prints information about functions in this library

    Parameters
    ----------
    method : str or None, optional
        get more information about a function or None for overview over all functions, by default None
    module : str or None, optional
        choose python module or None for the base TexTOM library, by default None
    filter : str, optional
        filter the displayed functions by a substring, by default ''
    """    
    if module is None:
        module = __import__(__name__)
    if method is None:
        msc.print_library_functions_and_docstrings(module, filter=filter)
    elif method in msc.list_library_functions(module):
        msc.print_function_docstring(module,method)
    else:
        print('Method name not recognized')
        msc.print_library_functions_and_docstrings(module)

def _slice( x, h, plane='z'):
    """Extracts a slice from the sample and reduces it to non-Nan regions

    Parameters
    ----------
    x : str,
        name of a scalar from results
    h : int
        height of the slice
    plane : str, optional
        slice direction: x/y/z, by default 'z'

    Returns
    -------
    ndarray
        2D slice
    """
    # global results
    array = results[x]
    if plane=='x':
        sl = array[h,:,:]  
    elif plane=='y':
        sl = array[:,h,:] 
    else:
        sl = array[:,:,h] 
    return msc.crop_to_non_nan_region(sl)