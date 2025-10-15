import os, glob
import numpy as np
from time import time
import sys
import h5py
from numba import prange, njit
from scipy.signal import find_peaks

# domestic
from .. import mask as msk
from . import baselines as bln
from .. import numba_plugins as nb
from ..misc import import_module_from_path
from .. import exceptions as exc
from ..model.model_textom import model_textom
from ...config import data_type

def import_data( sample_dir, pattern, mod:model_textom,  baseline_path,
                peak_region_path, blmask_path, detmask_path, geo_path,
                use_ion=True ):
    """Looks for data in path/data_integrated/ and prepares them for textom reconstructions

    Parameters
    ----------
    sample_dir : str
        textom base directory
    pattern : str
        substring required to be in the files in path/data_integrated/
    mod : model
        model object, needs to have projectors and diffractlets
    baseline_path : str 
        path to the desired background_subtraction module
    qmask_path : str, optional
        path to a file containing the peak-regions in q, if None will be created
        from user input, by default None
    detmask_path : str, optional
        path to a file containing the detector mask, if None will be created
        from user input, by default None
    geo_path : str, optional
        path to the desired geometry module
    flip_fov : bool, optional
        can be set to True if the fov metadata is switched by accident, by default False
    use_ion : bool, optional
        choose if normalisation by ionization chamber should be used (if present in
        data), by default True
    """
    # Load stuff
    geo = import_module_from_path('geometry', geo_path)
    bl = import_module_from_path('background_subtraction', baseline_path)
    peak_reg, hkl = load_peak_regions(peak_region_path, exclude_empty=True)
    bl_reg, _ = load_peak_regions(blmask_path, exclude_empty=False)
    mask_cake = h5py.File(detmask_path,'r')['mask_cake'][()]
    '''
    # sanity check compare number of q-values in mask and peak-regions:
    n_chi = mod.detShape[0]
    n_q_detmask = mask_detector.size//n_chi
    # if not n_q_detmask == peak_reg.shape[0]:
    #     raise exc.dimension_error('Number of q-values in peak regions and detector mask do not coincide.')
    # # reshape mask_detector because q and chi axes are defined the other way during masking
    # mask_detector = mask_detector.reshape((n_q_detmask, n_chi)).swapaxes(0,1).flatten()
    # i'll not change the masking now because it would be better to import the whole data
    # and write them in 2d to data_textom
    # and then do the masking afterwards in fitting.py
    # anyway this also replaces the sanity check above
    '''

    # get the images that show the sample
    scanmask = mod.Beams[:,:,0].astype(bool)                           ###########
    cp_threshold = False # for crazy pixel filter

    print('Starting data import')
    print('\tLoading integrated data from files')
    t0=time()
    airscat, ion = [], []
    filelist = get_data_list(sample_dir, pattern)

    for g, file in enumerate( filelist ):
        # Read data from integrated file
        with h5py.File(os.path.join(sample_dir, 'data_integrated', file),'r') as hf:
            q_in = np.squeeze(hf['radial_units'][()] ).astype(data_type)
            chi_in = np.squeeze( hf['azimuthal_units'][()]*np.pi/180 ).astype(data_type)
            fov = ( hf['fov'][()] ).astype(np.int32)
            d = ( np.array(hf['cake_integ'][()]) ).astype(data_type)
            if 'ion' in hf and use_ion:
                try:
                    ion_g = winsorize(hf['ion'][()], 1)
                except:
                    ion_g = hf['ion'][()]
                ion.append(ion_g)
            else:
                use_ion=False

        # this is just for the case fast/slow axes were chosen wrong during integration
        if geo.flip_fov:
            fov = np.flip( fov )
            
        # rescale data by primary beam intensity if known
        if use_ion:
            if g == 0:
                scale = np.mean(ion[0])
            d = _rescale( d, ion[g] ) * scale

        ## Reshaping in function of scanning mode ###
        # Base code written for column scan
        d = d.reshape( *fov, d.shape[1], d.shape[2] )
        
        if 'line' in geo.scan_mode:
            fov = np.flip( fov )
            # d = np.fliplr(np.flipud( np.transpose( d, axes=(1,0,2,3)) ) )
            d = np.transpose( d, axes=(1,0,2,3)) 

        # reorder data so that they are all treated the same in the model
        if 'snake' in geo.scan_mode:
            # Flip every second row
            for ii in range(d.shape[0]):
                if ii % 2 != 0:
                    d[ii] = d[ii][::-1]
        ##############################################

        i0=d.shape[-1]//4
        half_fov = fov[1]//2
        edge_sample = np.array([ 
            d[0,0,i0:].mean(),d[0,-1,:,i0:].mean(), 
            d[0,-half_fov,:,i0:].mean(),  d[-1,0,:,i0:].mean(), 
            d[-1,-half_fov,:,i0:].mean(),d[-1,-1,:,i0:].mean()]) 
        airscat.append( max( np.min( edge_sample), 0.) )
        # rescale by airscattering if primary beam intensity not known
        if not ion or not use_ion:
            # print('\tRescale by air scattering')
            if g==0:
                scale = airscat[0]
            else:
                d /= airscat[g] * scale

        # pad the data as in mumottize
        n_chi = chi_in.size
        proj =  np.zeros( (*mod.fov, n_chi, *q_in.shape), data_type)
        si, sj = d.shape[:2]
        i0 = (mod.fov[0] - si)//2
        j0 = (mod.fov[1] - sj)//2
        proj[i0:i0+si, j0:j0+sj] = d
        proj = proj.reshape(mod.fov[0]*mod.fov[1], n_chi, *q_in.shape)
        
        if not cp_threshold: # like this it's done only once
            print('\tChoose threshold for crazy pixels (Everything below will be processed)')
            cp_threshold = msk.select_threshold_hist( proj.flatten(), 
                        xlabel='Counts', ylabel='No of data points', 
                        title='Choose threshold for crazy pixels (Everything below will be processed)',
                        logx=True, logy=True )
            
            _, q_mask_p = get_q_mask(q_in, peak_reg)
            q_mask_bl, _ = get_q_mask(q_in, bl_reg)
            match bl.mode:
                case 'linear':
                    print('\tSubtracting linear baselines')
                    bl_fun = bln.linear_baseline
                    bl_args = (0)
                # case 'polynomial':
                #     print('\tSubtracting polynomial baselines')
                #     bl_fun = bln.polynomial_baseline       
                #     bl_order = bl.order_polynom     
                case 'chebyshev':
                    print('\tSubtracting chebyshev polynomial baselines')
                    bl_fun = bln.chebyshev_baseline
                    bl_args = (bl.order_chebyshev)
                # case 'chebyshev_auto':
                #     print('\tSubtracting chebyshev polynomial baselines with automated masking')
                #     bl_fun = bln.auto_chebyshev
                #     bl_args = (bl.order_chebyshev, bl.pre_order, bl.k_sigma, bl.q_expand)
                case 'none':
                    print('\tNot subtracting baselines')
                    bl_fun = bln.no_baseline
                    bl_args = (0)
                case _:
                    print('\tBaseline mode not recognized, revise background_subtraction.py')
                    break
            t1 = time()

        # remove hot pixels / all values above threshold
        proj[proj > cp_threshold] = np.median(proj)

        t_mask = np.where(scanmask[g])[0]
        data_fit = _regroup_q_any_baseline( 
            proj, t_mask, mask_cake,
            bl_fun, bl_args, q_in, q_mask_bl, q_mask_p )
        
        out_path = os.path.join( sample_dir, 'analysis', 'data_textom.h5')
        if g == 0:
            # give a suggestion on how to mask the peak regions based on mask_cake
            # (True if the peak region contains any valid pixel)
            # one can change the mask afterwards
            QQ,_ = np.meshgrid( q_in, chi_in )
            qmask = [np.logical_and(QQ >= start, QQ <= end) for start,end in peak_reg]
            mask_peaks = np.array([
                [np.logical_and.reduce(mask_cake[k, qmask[l][k]]) for l in range(len(peak_reg))] 
                    for k in range(chi_in.size)])

            print('\tSaving data to file: %s' % out_path)
            with h5py.File( out_path, 'w') as hf:
                hf.create_dataset( 'data',
                        shape=(0, data_fit.shape[1], data_fit.shape[2]),
                        maxshape=(None, data_fit.shape[1], data_fit.shape[2]),
                        chunks=(1, data_fit.shape[1], data_fit.shape[2]),
                        dtype=data_type,
                    )
                hf.create_dataset( 'peak_reg', data=peak_reg )
                hf.create_dataset( 'q', data = np.mean(peak_reg, axis=1))
                hf.create_dataset( 'chi', data = chi_in )
                hf.create_dataset( 'hkl', data=hkl )
                hf.create_dataset( 'detShape', data = [n_chi, q_mask_p.shape[0]] )
                hf.create_dataset( 'mask_cake', data = mask_cake)
                hf.create_dataset( 'q_in', data = q_in )
                hf.create_dataset( 'mask_peaks', data = mask_peaks )
                
        # add data to h5 file
        with h5py.File( out_path, 'r+') as hf:
            dset = hf['data']
            current_rows = dset.shape[0]
            new_rows = current_rows + data_fit.shape[0]
            dset.resize( new_rows, axis=0)
            dset[current_rows:new_rows] = data_fit

        try:
            t_it = (time()-t1)/(g)
        except:
            t_it=0
        Nrot = len(filelist)
        sys.stdout.write(f'\r\t\tProjection {(g+1):d} / {Nrot:d}, t/proj: {t_it:.1f} s, t left: {((Nrot-g-1)*t_it/60):.1f} min' )
        sys.stdout.flush()

    gt_mask = np.array( np.where(scanmask) ).T
    # add metadata to h5 file
    with h5py.File( out_path, 'r+') as hf:
        hf.create_dataset( 'scanmask', data=scanmask )
        hf.create_dataset( 'gt_mask', data=gt_mask )
        hf.create_dataset( 'baseline_mode', data=bl.mode )
        hf.create_dataset( 'baseline_order', data=bl_args )        
        hf.create_dataset( 'airscat', data = airscat )
        if ion:
            ion_av = np.array( [np.mean(i) for i in ion] ) # cannon write ion directly because shape
            hf.create_dataset( 'ion', data = ion_av )

    print(f'\n\t\ttook {(time()-t0)/60:.1f} min')

def get_data_list(sample_dir, pattern, subdir='data_integrated'):
    """Looks for all data in data_integrated and makes a list. 
    One can choose a pattern include only the desired files.

    Parameters
    ----------
    sample_dir : str
        sample base directory
    pattern : str
        integrated data filename with * placeholders

    Returns
    -------
    list
        list of filenames to process
    """
    filelist = sorted( glob.glob(os.path.join(sample_dir,subdir,'*h5')) )
    # the exception is for the coefficients for generated samples
    filelist = [s for s in filelist if pattern in s]#[:2]
    filelist = [s for s in filelist if 'sample_coeff' not in s]
    try:
        filelist = sort_data_list_by_angles( filelist, 'tilt_angle', 'rot_angle' )
    except:
        print('\t\tDid not find angles in files, just sorted data alphabetically')
    return filelist

def mask_peak_regions( mod:model_textom, q_data, powder_1D, peak_reg_path):
    # t_inter = time() # this is to subtract the time it takes for user input for remaining time estimation
    # set up boolean mask for filtering data
    q = mod.Qq_det.reshape(mod.detShape)[0]
    q_mask = np.ones_like(q_data, dtype=bool)
    # select peak regions from data and simulated powder pattern
    print('\tChoose regions containing Bragg peaks, then close the figure')
    # happy = 'n'
    # while happy != 'y':
    powder = mod.powder_pattern * powder_1D.max()/mod.powder_pattern.max()

    peak_reg = msk.select_regions( q_data[q_mask], powder_1D[q_mask], q, powder, hkl=mod.hkl,
            max_regions=None,
            title='Select individual Bragg peaks by holding LMB, remove by RMB' )
        # happy = input('\thappy? (y/n) ')
    peak_reg = peak_reg.get_regions()

    with open( peak_reg_path,'w') as fid:
        for reg in peak_reg:
            peak_hkl = mod.hkl[ np.logical_and( q>=reg[0], q<=reg[1] ) ]
            peak_hkl_str = ",".join("[" + ",".join(map(str, row)) + "]" for row in peak_hkl)
            fid.write(f'{reg[0]}\t{reg[1]}\t{peak_hkl_str}\n')
    print(f'\tSaved peak regions to {peak_reg_path}')

def mask_for_baseline( mod:model_textom, q_data, powder_1D, bl_reg_path):
    # t_inter = time() # this is to subtract the time it takes for user input for remaining time estimation
    # set up boolean mask for filtering data
    q = mod.Qq_det.reshape(mod.detShape)[0]
    q_mask = np.ones_like(q_data, dtype=bool)
    # select peak regions from data and simulated powder pattern
    print('\tSelect regions excluded in baseline subtraction, then close the figure')
    # happy = 'n'
    # while happy != 'y':
    powder = mod.powder_pattern * powder_1D.max()/mod.powder_pattern.max()

    peak_reg = msk.select_regions( q_data[q_mask], powder_1D[q_mask], q, powder, hkl=mod.hkl,
            max_regions=None,
            title='Select regions excluded in baseline subtraction by holding LMB, remove by RMB' )
        # happy = input('\thappy? (y/n) ')
    peak_reg = peak_reg.get_regions()

    with open( bl_reg_path,'w') as fid:
        for reg in peak_reg:
            fid.write(f'{reg[0]}\t{reg[1]}\n')
    print(f'\tSaved regions to {bl_reg_path}')

    # q_peaks = np.mean(peak_reg, axis=1)

    # # find out prominence of the highest peak for filtering data
    # I_mx = 0.                   
    # q_mask_k = []
    # for k, (start, end) in enumerate( peak_reg ):
    #     q_mask_k.append( ((q_data >= start) & (q_data <= end)) )
    #     q_mask &= ~q_mask_k[k]
    #     dat_peak = powder_1D[q_mask_k[k]]
    #     if dat_peak.max() > I_mx:
    #         q_mask_hp = q_mask_k[k]
    #         _, info = find_peaks(dat_peak, prominence=0.)
    #         try:
    #             prom = info['prominences'].max()
    #         except:
    #             prom=0.
    #         I_mx = dat_peak.max()
    # q_mask_k = np.array(q_mask_k)#.astype(data_type)  

    # t_inter = time()-t_inter
    # return peak_reg, q_mask, q_mask_k, q_mask_hp, prom, q_peaks, t_inter

def load_peak_regions( peak_reg_path, exclude_empty=False ):
    peak_reg,hkl = [],[]
    with open(peak_reg_path) as f:
        for line in f:
            # parts = line.strip().split("\t")
            # parts = list(filter(None, parts)) # this removes empty tabs
            parts = [s.strip() for s in line.split()]
            if len(parts) != 3:
                if exclude_empty:
                    continue
                else:
                    parts.append('')
            peak_reg.append((float(parts[0]), float(parts[1])))
            hkl.append(parts[2])

    # peak_reg = np.genfromtxt(peak_reg_path)
    # peak_reg = peak_reg.reshape( (peak_reg.size//2, 2)  )
    return np.array(peak_reg), hkl

def get_powder1d( path_projection, path_cakemask ):
    with h5py.File(path_projection, 'r') as hf:
        data_2d = hf['cake_integ'][()].sum(axis=0) # load data and sum over all good images in the projection
        q_powder = hf['radial_units'][()].flatten()
    if os.path.isfile(path_cakemask): # get the mask from pyfai (might not be completely accurate though)
        with h5py.File(path_cakemask,'r') as hf:
            mc = hf['mask_cake'][()].astype(bool)
    else:
        mc = np.ones_like(data_2d)
    data_2d[~mc] = np.nan # exclude masked values
    powder = np.nansum(data_2d, axis=0) # sum over all angles to get the powder pattern
    return q_powder, powder

def get_q_mask( q, peak_regions ):
    q_mask_p = []
    for (start, end) in peak_regions:
        q_mask_p.append( ((q >= start) & (q <= end)) )
    q_mask_p = np.array(q_mask_p)
    q_mask = np.logical_not( q_mask_p.sum(axis=0) )
    return q_mask, q_mask_p

def mask_detector( cakemask, detmask_path, powder_2D_masked, peak_reg, q_in, chi_in ):

    QQ,_ = np.meshgrid( q_in, chi_in )
    qmask = [np.logical_and(QQ >= start, QQ <= end) for start,end in peak_reg]
    mask_detector = np.array([
        [np.logical_or.reduce(cakemask[k, qmask[l][k]]) for k in range(chi_in.size)] 
            for l in range(len(peak_reg))])

    print('\tCreate mask by removing (left mouse button) or restoring pixels (right mouse button)')
    # start = np.argmax(q_mask) # this could be useful if taking a full mask, then partially regroup ? have to do it with diffractlets too maybe
    # end = len(q_mask) - 1 - np.argmax(q_mask[::-1]) # then make these values None and when regrouping do np.mean * number of points to make up for Nones
    mask_detector = msk.mask_detector( powder_2D_masked, mask_detector )
    with open( detmask_path, 'w' ) as fid:
        for pxl in mask_detector:
            fid.write(f'{pxl}\n')
    return mask_detector

def sort_data_list_by_angles( filelist, h5_outer_rotaxis_path, h5_inner_rotaxis_path ):

    inner_angle = []
    outer_angle = []
    for file in filelist:
        with h5py.File( file, 'r') as hf:
            inner_angle.append( hf[h5_inner_rotaxis_path][()] )
            outer_angle.append( hf[h5_outer_rotaxis_path][()] )
    # first sort by outer angles:
    order = np.lexsort([inner_angle, outer_angle])

    return [filelist[k] for k in order]

def winsorize(data, percent = 1):
    """Very simple filter, setting the upper and lower percentile to the next smaller/larger value
    """
    lower = np.percentile(data, percent)
    upper = np.percentile(data, 100-percent)
    data[data < lower] = lower
    data[data > upper] = upper
    return data

################## numba compiled functions
@njit
def any_peak( curve, prominence_threshold ):
    # numba-optimized function to check if there is a peak
    # with the given prominence in the data
    i_peak = np.argmax( curve )
    left_min = np.min(curve[:i_peak]) if i_peak > 0 else 0
    right_min = np.min(curve[i_peak + 1:]) if i_peak < curve.size-1 else 0
    prominence = curve[i_peak] - max(left_min, right_min)
    if prominence >= prominence_threshold:
        return True
    return False

@njit(parallel=True)
def _regroup_q_any_baseline( projection, t_mask, mask_detector, bl_fun, bl_args, q_in, q_mask_bl, q_mask_p ):
    n_data = t_mask.shape[0] # effective number of images
    n_peaks = q_mask_p.shape[0]
    regrouped_data = np.empty( (n_data, projection.shape[1], n_peaks), data_type )

    for k in prange(n_data):
        t = t_mask[k] # index within projection
        # get image and subtract baseline
        data_k = projection[t]
        # data_k_1d = nb.nb_mean_ax0( projection[t] )
        data_k_1d = nb.masked_mean_axis0( projection[t], mask_detector )
        baseline = bl_fun( q_in, data_k_1d, q_mask_bl, bl_args )

        # regroup data into peaks
        data_k_regrouped = np.empty( (data_k.shape[0], n_peaks), data_type )
        for p in range(n_peaks):
            #calculate integrated baseline:
            base_p = baseline[q_mask_p[p]].sum()
            # subtract from peak-integral
            data_k_regrouped[:,p] = nb.masked_sum_axis1(data_k[:,q_mask_p[p]], mask_detector[:,q_mask_p[p]]) - base_p

        regrouped_data[k] = data_k_regrouped#.flatten()[mask_detector] # Attention! change! -> masking moved to fitting
    return regrouped_data

@njit(parallel=True)
def _rescale( data, norm ):
    for k in prange( data.shape[0] ):
        if norm[k] == 0:
            data[k] = 0
        else:
            data[k] /= norm[k]
    return data

def import_data_1d( path, pattern, mod:model_textom,
                geo_path='input/geometry.py',
                flip_fov=False, use_ion=True ):

    geo = import_module_from_path('geometry', geo_path)
    # get the images that show the sample
    scanmask = mod.Beams[:,:,0].astype(bool)                           ###########

    print('Starting data import')
    print('\tLoading integrated data from files')
    t0=time()
    airscat, ion = [], []
    filelist = sorted( os.listdir( os.path.join(path,'data_integrated_1d')) )
    filelist = [s for s in filelist if pattern in s]#[:2]
    t1=time()
    for g, file in enumerate( filelist ):
        # Read data from integrated file
        with h5py.File(os.path.join(path, 'data_integrated_1d', file),'r') as hf:
            q_in = ( hf['radial_units'][0] ).astype(data_type)
            fov = ( hf['fov'][()] ).astype(np.int32)
            d = np.array(hf['cake_integ'])[()]
            if 'ion' in hf:
                ion.append(hf['ion'][()])

        if flip_fov:
            fov = np.flip( fov )
            
        if ion and use_ion:
            # print('\tRescale by beam intensity')
            d = _rescale( d, ion[g] )

        ## Reshaping in function of scanning mode ###
        # Base code written for column scan
        d = d.reshape( *fov, d.shape[1] )
        
        if 'line' in geo.scan_mode:
            fov = np.flip( fov )
            d = np.transpose( d, axes=(1,0,2)) 

        # reorder data so that they are all treated the same in the model
        if 'snake' in geo.scan_mode:
            # Flip every second row
            for ii in range(d.shape[0]):
                if ii % 2 != 0:
                    d[ii] = d[ii][::-1]
        ##############################################

        i0=d.shape[-1]//4
        # get airscattering:
        edge_sample = np.array([ 
            d[0,0,i0:].mean(), 
            d[0,-1,:,i0:].mean(), 
            d[0,-fov[1]//2,:,i0:].mean(),  
            d[fov[0]//2,0,i0:].mean(), 
            d[fov[0]//2,-1,:,i0:].mean(), 
            d[-1,0,:,i0:].mean(), 
            d[-1,-fov[1]//2,:,i0:].mean(),
            d[-1,-1,:,i0:].mean()
            ]) 
        airscat.append( np.min( edge_sample[edge_sample > 0.] ))
        if not ion or not use_ion:
            # print('\tRescale by air scattering')
            d /= airscat[g]

        max_shape = mod.fov
        # pad the data as in mumottize
        # fill projections with air scattering
        proj =  np.random.normal(airscat[g],np.sqrt(airscat[g])/2,(*max_shape, d.shape[2]))
        si, sj = d.shape[:2]
        i0 = (max_shape[0] - si)//2
        j0 = (max_shape[1] - sj)//2
        proj[i0:i0+si, j0:j0+sj] = d
        proj = proj.reshape(max_shape[0]*max_shape[1], *q_in.shape)

        scanmask_g = scanmask[g].copy()
        proj = _remove_crazypixels_1d(proj, scanmask_g)

        out_path = os.path.join( path, 'analysis', 'data_1drec.h5')
        if g == 0:
            print('\tSaving data to file: %s' % out_path)
            with h5py.File( out_path, 'w') as hf:
                hf.create_dataset( 'data',
                        shape=(0, proj.shape[1]),
                        maxshape=(None, proj.shape[1]),
                        chunks=(1, proj.shape[1]),
                        dtype='float64'
                    )
                hf.create_dataset( 'radial_units', data = q_in )

        # add data to h5 file
        with h5py.File( out_path, 'r+') as hf:
            dset = hf['data']
            current_rows = dset.shape[0]
            new_rows = current_rows + proj.shape[0]
            dset.resize( new_rows, axis=0)
            dset[current_rows:new_rows, :] = proj


        t_it = (time()-t1)/(g+1)
        Nrot = len(filelist)
        sys.stdout.write(f'\r\t\tProjection {(g+1):d} / {Nrot:d}, t/proj: {t_it:.1f} s, t left: {((Nrot-g-1)*t_it/60):.1f} min' )
        sys.stdout.flush()

    ion_av = np.array( [i.mean() for i in ion] ) # cannon write ion directly because shape
    gt_mask = np.array( np.where(scanmask) ).T
    # add metadata to h5 file
    with h5py.File( out_path, 'r+') as hf:
        hf.create_dataset( 'scanmask', data=scanmask )
        hf.create_dataset( 'gt_mask', data=gt_mask )
        hf.create_dataset( 'airscat', data = airscat )
        hf.create_dataset( 'ion', data = ion_av )
        hf.create_dataset( 'q', data=q_in)

    print(f'\t\ttook {time()-t0:.2f} s')

@njit(parallel=True)
def _remove_crazypixels_1d( projection, scanmask ):
    dat_new = projection.copy()
    for k in prange(projection.shape[0]):
        if scanmask[k]:
            for m in range(-1,projection.shape[1]-1):
                sample = np.array([
                    projection[k,m-2],projection[k,m-1],projection[k,m+1],projection[k,m+2]
                ])
                base = np.median(sample)
                if projection[k,m] > 10*np.abs(base):
                    dat_new[k,m] = base
    return dat_new