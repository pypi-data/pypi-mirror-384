import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.colors as colors
from matplotlib.widgets import Slider, Button, RangeSlider
from matplotlib.animation import FuncAnimation
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.spatial import ConvexHull
import warnings
import time

from .optimization.fitting import fitting
from ..config import data_type

############################################################################################
############################################################################################

def loss(loss, title=''):
    f,ax = plt.subplots()
    ax.plot(loss)
    ax.set_xlabel('Iterations')
    ax.set_ylabel('Loss function')
    ax.set_title(title)
    return f,ax

def singlefit2D( fit:fitting, idx, hkl=None,
        polar = False, mode='line',
        title='', log=True, show_off=False,
        output=False, show=False ):
    
    shape = fit.detShape
    PHi, QQ = np.meshgrid( fit.chi, fit.q )
    # PHi = mod.Chi_det.reshape(shape)
    # QQ = mod.Qq_det.reshape(shape)
    
    g,t = fit.gt_mask[ idx ]
    im = fit.image( fit.C, g, t )
    Fit = np.zeros( shape[0]*shape[1], data_type)
    Fit[fit.mask_detector] = im
    FIt = Fit.reshape(shape) #* fit.sim_fac # reshape and scale

    Data = np.zeros_like(Fit)
    Data[fit.mask_detector] = fit.data[idx]
    DAta = Data.reshape(shape)

    maxval = max( Data.max(), FIt.max() )
    # maxval = FIt.max()

    if mode=='colors':
        if polar:
            f,ax = plt.subplots(1,3,figsize=(8,3),subplot_kw=dict(projection='polar'))
        else:
            f,ax = plt.subplots(1,3,figsize=(8,3),sharey=True)
            PHi = PHi*180/np.pi
        lognrm = colors.LogNorm(vmin=maxval*1e-2, vmax=maxval)
        if log:
            nrm = colors.LogNorm(vmin=maxval*1e-2, vmax=maxval)
            res = abs(DAta-FIt)
            ax[2].set_title('abs(Residuals)')
        else:
            nrm = colors.Normalize(vmin=-maxval, vmax=maxval)
            res = DAta - FIt
            ax[2].set_title('Data-Fit')
        if show_off:
            DAta[DAta<=0] = maxval*1e-2
            FIt[FIt<=0] = maxval*1e-2
        ax[0].pcolormesh(PHi, QQ, DAta, norm=lognrm, cmap='plasma')
        m= ax[1].pcolormesh(PHi, QQ, FIt, norm=lognrm, cmap='plasma')
        m=ax[2].pcolormesh(PHi, QQ, res, norm=nrm, cmap='RdBu_r' )
        ax[0].set_title('Data')
        ax[1].set_title('Fit')
        ax[0].set_xticks([0, 90, 180, 270])
        ax[1].set_xticks([0, 90, 180, 270])
        ax[0].set_xlabel('$\chi$')
        ax[1].set_xlabel('$\chi$')
        ax[0].set_ylabel('q [nm$^{-1}$]')
        f.suptitle(title)
        f.colorbar(m, label='Scattering Intensity', ax=ax[2])
        f.tight_layout()
    
    else: #line
        f = line_qplot(fit.q, fit.chi*180/np.pi, DAta, FIt, hkl)
        # ax.set_xlabel('$\chi$ / deg')
        # ax.set_ylabel('q [nm$^{-1}$]')
        f.suptitle(title)

    if output:
        if not os.path.exists('output'):
            os.makedirs('output')
        f.savefig('output/fitimage.pdf')
    
    if show:
        plt.show()

############################################################################################

def line_qplot_old(q, chi, data, fit, hkl=None):
    """Plots data and fit for every q-value above each other
    (in an admittedly weird fashion but it gives a good overview over many
    fits at a time.  )
    The y-scale does not correspond to to the scale of the data, but just
    marks at which q the data is located!

    Parameters
    ----------
    q : ndarray
        radial variable on detector
    chi : ndarray
        azimuthal detector angle
    data : ndarray
        collection of data for each q-value
    fit : ndarray
        collection of fits for each q-value

    Returns
    -------
    _type_
        _description_
    """
    norm=1
    if q.size > 1:
        norm = np.mean(np.abs(np.diff(q))) / max( np.max(data), np.max(fit))
    f, ax = plt.subplots( figsize=(6,9) )
    ax.plot( chi[0], norm*data[0,0]+q[0],'k-x', label='data', linewidth=0.5 )
    ax.plot( chi[0], norm*data[0,0]+q[0],'k:', label='fit' )
    for k in range(q.size):
        mask = data[:,k] > 0
        ax.plot( chi[mask], norm*data[mask, k]+q[k], '-x', linewidth=0.5 )
    # Reset the color cycle
    ax.set_prop_cycle(None)
    for k in range(q.size):
        ax.plot( chi, norm*fit[:,k]+q[k], ':' )
        if hkl:
            plt.text(chi[chi.size//2], q[k]-0.3, hkl[k], va='top', ha='center')

    ax.legend()
    return f, ax

def line_qplot(q, chi, data, fit, hkl=None):
    """Plots data and fit for every q-value in different axes

    Parameters
    ----------
    q : ndarray
        radial variable on detector
    chi : ndarray
        azimuthal detector angle
    data : ndarray
        collection of data for each q-value
    fit : ndarray
        collection of fits for each q-value

    Returns
    -------
    f : matplotlib figure handle
    """
    f, ax = plt.subplots( q.size, 1, figsize=(6,9), sharex=True )
    ax[0].plot( chi[0], data[0,0],'kx', label='data', linewidth=0.5 )
    ax[0].plot( chi[0], data[0,0],'r', label='fit' )
    for k in range(q.size):
        mask = data[:,k] > 0
        ax[k].plot( chi[mask], data[mask, k], 'kx', linewidth=0.5 )
        if hkl:
            ax[k].set_ylabel('Intensity '+hkl[k])
            # maybe add also q?
        else:
            ax[k].set_ylabel('Intensity')
    for k in range(q.size):
        ax[k].plot( chi, fit[:,k], 'r' )

    ax[-1].set_xlabel('$\chi$ / deg')
    ax[0].legend()
    return f

############################################################################################

def compare_projection_av( data, fit, title='', log=False, output=False, show=False ):

    maxval = max( data.max(), fit.max() )
    f,ax = plt.subplots(1,3,figsize=(8,3),sharey=True)
    
    ax[0].imshow( data, vmax=maxval, cmap='plasma')
    ax[1].imshow( fit, vmax=maxval, cmap='plasma')
    ax[2].imshow( np.abs(data-fit), vmax=maxval,  cmap='plasma' )
    ax[0].set_title('Data')
    ax[1].set_title('Fit')
    ax[2].set_title('Residuals')
    f.suptitle(title)
    f.tight_layout()

    if output:
        if not os.path.exists('output'):
            os.makedirs('output')
        f.savefig('output/cmp_proj_av.pdf')
    if show:
        plt.show()

############################################################################################

def compare_projection_ori( ori_dat, ori_fit, qs, hkl=None, title='', output=False, show=False ):
    nq = qs.size
    fig = plt.figure(figsize=(10, min(16, 3*nq)))
    gs = gridspec.GridSpec(nq, 3, width_ratios=[1, 1, 0.3])#, wspace=0.4)
    axes = []#np.atleast_2d( ax ) 
    for iq in range(nq):
        if iq==0:
            ax = fig.add_subplot(gs[iq, 0])
        else:
            ax = fig.add_subplot(gs[iq, 0], sharex=axes[0], sharey=axes[0])
        ax.imshow(ori_dat[iq].T, cmap='hsv', vmin=0, vmax=np.pi)   
        ylabel =  f'q = {qs[iq]:.1f} nm-1'
        if hkl is not None:
            ylabel = str(hkl[iq]) + '\n' + ylabel
        ax.set_ylabel( ylabel )
        axes.append(ax)
        ax = fig.add_subplot(gs[iq, 1], sharex=axes[0], sharey=axes[0])
        ax.imshow(ori_fit[iq].T, cmap='hsv', vmin=0, vmax=np.pi)
        axes.append(ax)
        # f.colorbar(m1)
        # f.colorbar(m2)
    axes[0].set_title('Data')
    axes[1].set_title('Fit')
    for k, ax in enumerate(axes):
        if k<len(axes)-2:
            ax.tick_params(axis='x',          # changes apply to the x-axis
                        which='both',      # both major and minor ticks are affected
                        bottom=False,      # ticks along the bottom edge are off
                        labelbottom=False) # labels along the bottom edge are off)
        if k%2:
            ax.tick_params(axis='y',          # changes apply to the x-axis
                        which='both',      # both major and minor ticks are affected
                        left=False,      # ticks along the bottom edge are off
                        labelleft=False) # labels along the bottom edge are off)
    ax_cbar = fig.add_subplot(gs[0, 2], projection='polar') 
    round_colorbar(ax_cbar)
    fig.suptitle(title)
    fig.tight_layout()

    if output:
        if not os.path.exists('output'):
            os.makedirs('output')
        fig.savefig('output/cmp_proj_ori.pdf')
    if show:
        plt.show()
        
def image_residuals(fit:fitting, g, fov, hkl=None, title=''):

    res = fit.projection_residuals(g).reshape(fov)
    mask = fit.scanmask[g].reshape(fov)
    # t_mask = fit.gt_mask[fit.gt_mask[:,0]==g, 1]

    fig,ax = plt.subplots( figsize=(7,7) )
    im = ax.matshow( res.T )
    ax.set_title(title)
    cbar = fig.colorbar(im)
    cbar.set_label('Residuals', rotation=90)
    fig.tight_layout()

    # Function to handle mouse clicks (printing pixel coordinates)
    def on_click(event):
        if event.inaxes != ax:
            return # does nothing if the click is outside
        if ax.figure.canvas.toolbar.mode == 'zoom rect': return # does nothing when zooming

        x, y = int(np.round(event.xdata)), int(np.round(event.ydata))
        
        if mask[x,y]:
            idx = np.ravel_multi_index((x,y), fov)
            idx = np.where( np.logical_and(
                fit.gt_mask[:,0]==g, fit.gt_mask[:,1]==idx ))[0][0]
            singlefit2D( fit, idx, hkl,
                title = f'Projection {g}, pixel ({x}/{y})',
                polar = False, mode='line',
                log=True, show_off=False,
                output=False, show=True )
    # Connect the click event
    fig.canvas.mpl_connect('button_press_event', on_click)

    # Add a range slider to adjust the color scale
    plt.subplots_adjust(bottom=0.10)#, hspace=0.3)

    ax_slider = plt.axes([0.25, 0.05, 0.5, 0.03])
    slider = RangeSlider(ax_slider, "Colorscale min/max", 
                         res.min(), res.max(), valinit=(res.min(),res.max()))
    # ax_ymin = plt.axes([0.15, 0.04, 0.3, 0.03])
    # ax_ymax = plt.axes([0.55, 0.04, 0.3, 0.03])
    # slider_ymin = Slider(ax_ymin, 'min', res.min(), res.max(), valinit=res.min())
    # slider_ymax = Slider(ax_ymax, 'max', res.min(), res.max(), valinit=res.max()) 
    def update(val):
        ymin, ymax = slider.val
        im.set_clim(ymin, ymax)
        # ax.set_ylim(ymin, ymax)
        fig.canvas.draw_idle()
    # def update_lim(val):
    #     im.set_clim(slider_ymin.val, slider_ymax.val)
    #     fig.canvas.draw_idle()
    # slider_ymin.on_changed(update_lim)
    # slider_ymax.on_changed(update_lim)
    slider.on_changed(update)

    plt.show()

############################################################################################

def projection_residuals( fit:fitting, show=False ):
    fit.choose_projections('full') ## doesn't work with less projections yet (else modify fit.data_av)
    if np.all(fit.ns == np.array([0])):
        if not hasattr( fit, 'data_av' ):
            fit.prepare_fit_c0()
        proj = fit.projections_c0( fit.C )
        data = fit.data_0D
        res = fit.insert_fov( (proj-data)**2 ).sum(axis=1)
        proj = fit.insert_fov( proj )
    else:
        print('\tCalculating projections')
        proj = np.array( [fit.projection( g, fit.C, info=False ) for g in range(fit.scanmask.shape[0])])
        data = fit.data
        res =  fit.insert_fov(((proj[fit.scanmask]-data)**2).sum(axis=1)).sum(axis=1)
        proj = proj.sum(axis=1)
        data = data.sum(axis=1)
    # print(proj.shape)

    f,ax = plt.subplots(2, sharex=True)
    ax[0].plot(proj.sum(axis=1), label='simulation')
    ax[0].plot(fit.insert_fov( data ).sum(axis=1), label='data')
    ax[0].set_ylabel( 'integrated intensity' )
    ax[0].legend()
    ax[1].plot(res)
    ax[1].set_xlabel( 'projection' )
    ax[1].set_ylabel( 'squared residuals' )
    f.tight_layout()

    if show:
        plt.show()

############################################################################################

def interactive_tomogram( datasets, names, fctn, borders=None,
            minmax=None, sliceplane='z', cmap='inferno', cut=1, save_vid_path=False,
            title='',  fps=5, show=True ):
    if sliceplane == 'x':
        xlabel,ylabel = 'y','z'
        if borders:
            xlim=range(borders[2],borders[3])
            ylim=range(borders[4],borders[5])
            sllim=borders[0:2]
    elif sliceplane == 'y':
        datasets=datasets.transpose(0,2,1,3)
        xlabel,ylabel = 'x','z'
        if borders:
            xlim=range(borders[0],borders[1])
            ylim=range(borders[4],borders[5])
            sllim=borders[2:4]
    else:
        datasets=datasets.transpose(0,3,1,2)
        xlabel,ylabel = 'x','y'
        if borders:
            xlim=range(borders[0],borders[1])
            ylim=range(borders[2],borders[3])
            sllim=borders[4:6]
    
    num_datasets = datasets.shape[0]
    num_images = datasets.shape[1]
    if not borders:
        sllim = [0,num_images]
    # Initial dataset and image index
    current_dataset_index = 0
    current_image_index =  sllim[0]
    current_stack = datasets[current_dataset_index]

    # Initial display: display the first image of the first dataset
    fig, ax = plt.subplots( figsize=(10,8) )
    plt.subplots_adjust(left=0.25, bottom=0.2)
    ax.set_title(title)
    
    # Achieve an adaptive colorbar with tunable borders
    if not minmax:
        minmax = [[
            # np.nanmin(stack),
            # np.nanmax(stack)
            np.percentile(stack[~np.isnan(stack)], cut),
            np.percentile(stack[~np.isnan(stack)], 100-cut)
            ] for stack in datasets]

    # Display the first image in the initial dataset
    img_display = ax.imshow(current_stack[0].T, cmap=cmap,
                             vmin=minmax[0][0],
                             vmax=minmax[0][1],
                             )
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if borders:
        x_ticks = ax.get_xticks()  # Positions of the x-ticks
        y_ticks = ax.get_yticks()  # Positions of the y-ticks
        new_x_labels = [f"{int(tick) + xlim[0]}" for tick in x_ticks if tick.is_integer()]
        new_y_labels = [f"{int(tick) + ylim[0]}" for tick in y_ticks if tick.is_integer()]
        ax.set_xticklabels(new_x_labels)
        ax.set_yticklabels(new_y_labels)
        # ax.set_xticks(ticks=np.arange(len(xlim)), labels=xlim)  # Set custom x-axis labels
        # ax.set_yticks(ticks=np.arange(len(ylim)), labels=ylim)  # Set custom y-axis labels
    cbar = fig.colorbar(img_display)
    cbar.ax.set_autoscale_on(True)
    cbar.set_label(names[0])

    # Create a slider for switching between images within a dataset
    ax_image_slider = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor='lightgoldenrodyellow')
    image_slider = Slider(ax_image_slider, sliceplane, sllim[0], sllim[1], valinit=sllim[0], valstep=1)

    if num_datasets > 1:
        # Create a slider for switching between datasets
        ax_dataset_slider = plt.axes([0.25, 0.05, 0.65, 0.03], facecolor='lightblue')
        dataset_slider = Slider(ax_dataset_slider, 'Dataset', 0, num_datasets - 1, valinit=0, valstep=1)

    def update(val):
        current_image_index = int(image_slider.val)  # Get the image index from the slider
        if num_datasets > 1:
            current_dataset_index = int(dataset_slider.val)  # Get the dataset index from the slider
        else:
            current_dataset_index = 0
        current_stack = datasets[current_dataset_index]  # Update the dataset
        current_image = current_stack[current_image_index - sllim[0]]
        img_display.set_data(current_image.T)  # Update the image data
        img_display.set_clim(vmin=minmax[current_dataset_index][0],
                      vmax=minmax[current_dataset_index][1])
        cbar.update_normal(img_display)
        cbar.set_label(names[current_dataset_index])
        # cbar.set_clim(vmin=current_image.min(),vmax=current_image.max())
        # cbar.draw_all() 
        # tcks = np.linspace(current_image.min(),current_image.max(),endpoint=True)
        # cbar.set_ticks(tcks)
        # cbar.update_normal(img_display)
        fig.canvas.draw_idle()  # Redraw the figure

    # Attach the update functions to the sliders
    image_slider.on_changed(update)
    if num_datasets > 1:
        dataset_slider.on_changed(update)

    # Add a button for playing the video
    ax_button = plt.axes([0.1, 0.095, 0.1, 0.04])
    button = Button(ax_button, 'Play')

    playing = [False]  # Use a mutable object to toggle playing state

    def toggle_play(event):
        playing[0] = not playing[0]  # Toggle state
        if playing[0]:
            button.label.set_text("Pause")
            ani.event_source.start()
        else:
            button.label.set_text("Play")
            ani.event_source.stop()

    button.on_clicked(toggle_play)

    # Automatic playback with animation
    def update_frame(i):
        if playing[0]:
            next_frame = (int(image_slider.val) - sllim[0] + 1) % num_images + sllim[0]
            image_slider.set_val(next_frame)

    ani = FuncAnimation(fig, update_frame, frames=num_images, interval=100)  #  Interval in milliseconds

    if save_vid_path:
        toggle_play(None)
        # Save the animation as an MP4 file
        ani.save(save_vid_path, writer='pillow', fps=fps)

    if show:
        # Function to handle mouse clicks (printing pixel coordinates)
        def on_click(event):
            if event.inaxes != ax: return # does nothing if the click is outside
            if ax.figure.canvas.toolbar.mode == 'zoom rect': return # does nothing when zooming
            current_image_index = int(image_slider.val)
            if sliceplane=='x':
                y, z = int(np.round(event.xdata)+xlim[0]), int(np.round(event.ydata+ylim[0]))
                x = current_image_index
            elif sliceplane=='y':
                x, z = int(np.round(event.xdata+xlim[0])), int(np.round(event.ydata+ylim[0]))
                y = current_image_index
            elif sliceplane=='z':
                x, y = int(np.round(event.xdata+xlim[0])), int(np.round(event.ydata+ylim[0]))
                z = current_image_index
            fctn(x,y,z)
            # print(f"Clicked on pixel ({x}, {y}) in dataset {current_dataset_index}, image {current_image_index}")

        # Connect the click event
        fig.canvas.mpl_connect('button_press_event', on_click)

        plt.show()

def tomo_hull( data ):
    # Create a 3D scatter plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # # Scatter plot of data points
    # ax.scatter(data[:, 0], data[:, 1], data[:, 2], c='r', marker='o')

    # Convex Hull for the points
    hull = ConvexHull(data)

    # Plot the convex hull with colored faces
    for simplex in hull.simplices:
        # Create a polygon for each face of the convex hull
        triangle = Poly3DCollection([data[simplex]], color='cyan', alpha=0.4)#, edgecolor='k')
        ax.add_collection3d(triangle)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.grid(False)
    ax.set_xlim([data[:,0].min(), data[:,0].max()])
    ax.set_ylim([data[:,1].min(), data[:,1].max()])
    ax.set_zlim([data[:,2].min(), data[:,2].max()])
    set_axes_equal_3d(ax)

    # Show plot
    plt.show()

def round_colorbar(ax=None, ang_max=180, cmap='hsv'):
    """
    Creates a half-circle colorbar for visualizing orientations from 0? to 180?.

    Parameters:
    ax (matplotlib axis object): axis where to put the colorbar, if None creates an axis, default=None.
    ang_max (int): maximum angle in degree, optimized for 360 or 180, default=180.
    cmap (str): Colormap to use for the colorbar, default 'hsv'.
    """
    if not ax:
        # Create a polar plot
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(6, 3))

    # Generate data for the colorbar
    theta = np.linspace(0, ang_max*np.pi/180, 100) 
    r = np.linspace(0.9, 1.0, 2)  # Radius positions
    theta, r = np.meshgrid(theta, r)
    z = theta  # Map the angle to the colormap

    # Normalize and map the data to the colormap
    norm = colors.Normalize(vmin=0, vmax=ang_max*np.pi/180)
    cmap = plt.get_cmap(cmap)

    # Plot the half-circle colorbar
    cbar = ax.pcolormesh(theta, r, z, cmap=cmap, norm=norm, shading='auto')

    # Customize the polar plot
    ax.set_yticks([])  # Remove radial ticks
    ax.set_xticks(np.linspace(0, ang_max*np.pi/180, 
                              num=5 if ang_max<=180 else 8, 
                              endpoint= False if ang_max>=360 else True ))  # Angular ticks
    ax.set_xticklabels([f'{int(np.degrees(tick))}\u02DA' for tick in ax.get_xticks()])
    ax.set_rgrids([])  # Remove grid lines
    ax.set_theta_zero_location('N')  # Set 0 degrees at the top
    ax.set_theta_direction(-1)  # Clockwise direction

    # Limit the plot to the half-circle
    ax.set_thetamin(0)
    ax.set_thetamax(ang_max)

    plt.show()



def set_axes_equal_3d(ax):
    """Set equal scaling for the 3D plot axes."""
    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    x_range = abs(x_limits[1] - x_limits[0])
    y_range = abs(y_limits[1] - y_limits[0])
    z_range = abs(z_limits[1] - z_limits[0])

    max_range = max(x_range, y_range, z_range)

    x_middle = np.mean(x_limits)
    y_middle = np.mean(y_limits)
    z_middle = np.mean(z_limits)

    ax.set_xlim3d([x_middle - max_range / 2, x_middle + max_range / 2])
    ax.set_ylim3d([y_middle - max_range / 2, y_middle + max_range / 2])
    ax.set_zlim3d([z_middle - max_range / 2, z_middle + max_range / 2])

############################################################################################

def check_simulated_dose( fit:fitting ):
    sim_dose = fit.Beams.sum(axis=2).sum(axis=1)
    plt.figure()
    plt.plot(sim_dose)

############################################################################################

def plot_orientations_slice( vectors_slice, scaling=np.array([1]), title='' ):

    # print(scaling.shape)
    # print(vectors_slice.shape)
    # scaling=np.array([1])
    x = np.arange(vectors_slice.shape[0])
    y = np.arange(vectors_slice.shape[1])
    Y,X = np.meshgrid(y,x)
    vectors_slice_flat = vectors_slice.reshape((vectors_slice.size//3, 3))
    scal = scaling.flatten() / scaling.max()

    # Create a 3D scatter plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.quiver(X.flatten(),
              Y.flatten(),
              np.zeros(X.size),
              scal*vectors_slice_flat[:,0],
              scal*vectors_slice_flat[:,1],
              scal*vectors_slice_flat[:,2],
              pivot='middle')
    set_axes_equal_3d(ax)
    ax.set_title(title)

    plt.show()

# def make_slice_coordinates(bounds):
#     # get coordinates in the slice
#     x = np.arange(vectors_slice.shape[0])
#     y = np.arange(vectors_slice.shape[1])
#     X,Y = np.meshgrid(x,y)

def array3D_slider( values, coordinates=None, minmax=None, cut=1, cmap='inferno',xlabel='',ylabel='',collabel='',invert_x=False,invert_y=False ):

    if coordinates:
        X,Y = coordinates[0], coordinates[1]

    # Initial dataset and image index
    current_image_index = 0

    # Initial display: display the first image of the first dataset
    fig, ax = plt.subplots( figsize=(10,8) )
    plt.subplots_adjust(left=0.25, bottom=0.2)

    # Achieve an adaptive colorbar with tunable borders
    if not minmax:
        minmax = [
            np.percentile(values[~np.isnan(values)], cut),
            np.percentile(values[~np.isnan(values)], 100-cut)
            ]

    # Display the first image in the initial dataset
    if coordinates:
        img_display = ax.pcolormesh(X,Y,values[current_image_index], cmap=cmap,
                             vmin=minmax[0],
                             vmax=minmax[1],
                             )
    else:
        img_display = ax.imshow(values[current_image_index].T, cmap=cmap,
                             vmin=minmax[0],
                             vmax=minmax[1],
                             )
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if invert_x:
        ax.invert_xaxis()
    if invert_y:
        ax.invert_yaxis()
    cbar = fig.colorbar(img_display)
    cbar.ax.set_autoscale_on(True)
    cbar.set_label(collabel)

    # Create a slider for switching between images within a dataset
    ax_image_slider = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor='lightgoldenrodyellow')
    image_slider = Slider(ax_image_slider, '', 0, values.shape[0]-1, valinit=current_image_index, valstep=1)

    def update(val):
        current_image_index = int(image_slider.val)  # Get the image index from the slider
        current_image = values[current_image_index]
        if coordinates:
            img_display.update({'array': current_image})
        else:
            img_display.set_data(current_image)  # Update the image data
        cbar.update_normal(img_display)
        fig.canvas.draw_idle()  # Redraw the figure

    # Attach the update functions to the sliders
    image_slider.on_changed(update)

    plt.show()


def plot_points_quaternionspace( Q, odf=None, thresh=0.01, att=0.1 ):

    Q=np.atleast_2d(Q)
    extr = np.max(np.abs(Q[:,1:]))

    if np.any(odf):
        odf /= odf.max()
        Q = Q[odf < thresh]
        odf = odf[odf < thresh]
        # Define a color (e.g. red) with variable alpha
        colors = np.zeros((odf.size, 4))  # RGBA
        colors[:, 2] = 1.0           # Blue channel
        colors[:, 3] = (1-odf)*att         # Alpha channel
    else:
        colors='b'

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(Q[:, 1], Q[:, 2], Q[:, 3], 
            color=colors, marker='o')
    
    ax.set_xlim([-extr,extr])
    ax.set_ylim([-extr,extr])
    ax.set_zlim([-extr,extr])
    set_axes_equal_3d(ax)

    plt.show()
    
def plot_odf_slices_euler( euler_angles, odf, phi2_sections = [0, 45, 65], tol=5 ):
    # euler_angles: phi1, Phi, phi2
    # Plot ?2 sections (most common representation)
    # phi2_sections = [0, 45, 65] # degrees
    phi1, Phi, phi2 = euler_angles[:,0]*180/np.pi,euler_angles[:,1]*180/np.pi,euler_angles[:,2]*180/np.pi
    # fig, axes = plt.subplots(1, len(phi2_sections), figsize=(15, 5))
    # for ax, val in zip(axes, phi2_sections):
    #     # find closest phi2 index
    #     idx = (np.abs(phi2 - val)).argmin()
    #     section = odf[:, :, idx].T # transpose so Phi is y-axis


    #     im = ax.imshow(
    #     section,
    #     origin='lower',
    #     extent=[phi1[0], phi1[-1], Phi[0], Phi[-1]],
    #     aspect='auto',
    #     cmap='viridis'
    #     )
    #     ax.set_title(f"?? = {phi2[idx]:.1f}??")
    #     ax.set_xlabel("?? (??)")
    #     ax.set_ylabel("? (??)")
    #     fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.8, label="ODF intensity")
    #     plt.tight_layout()
    #     plt.show()

    fig, axes = plt.subplots(1, len(phi2_sections), figsize=(15, 5))
    for ax, val in zip(axes, phi2_sections):
        mask = np.abs(phi2 - val) < tol
        h = ax.hexbin(phi1[mask], Phi[mask], C=odf, gridsize=50, cmap='viridis')
        ax.set_title(f"?? ? {val}??")
        ax.set_xlabel("?? (??)")
        ax.set_ylabel("? (??)")

    fig.colorbar(h, ax=axes.ravel().tolist(), shrink=0.8, label="Counts")
    plt.tight_layout()
    plt.show()


def plot_odf_slices_rodrigues( r, odf, r3_slices = [0.0, 1.0, -1.0], tol=0.1 ):

    # Choose slices in r3
    r3_slices = [0.0, 1.0, -1.0]

    fig, axes = plt.subplots(1, len(r3_slices), figsize=(15, 5))
    for ax, val in zip(axes, r3_slices):
        mask = np.abs(r[:,2] - val) < tol
        h = ax.hexbin(r[:,0][mask], r[:,1][mask], C=odf, gridsize=50, cmap='viridis')

        # idx = (np.abs(r - val)).argmin()
        # section = odf[:, :, idx].T

        # im = ax.imshow(
        #     section,
        #     origin='lower',
        #     extent=[r[0], r[-1], r[0], r[-1]],
        #     aspect='equal',
        #     cmap='viridis'
        # )
        ax.set_title(f"r? = {val:.2f}")
        ax.set_xlabel("r?")
        ax.set_ylabel("r?")

    fig.colorbar(h, ax=axes.ravel().tolist(), shrink=0.8, label="ODF intensity")
    plt.tight_layout()
    plt.show()


def compare_data_powder( q_values, chi_values, data2d_stack, q_powder, I_powder, hkl ):
    # Set up figure and subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 12), sharex=True,
                                        gridspec_kw={'height_ratios': [2, 1, 1]})

    # Initial plots    
    CHi, QQ = np.meshgrid( chi_values, q_values )
    pcm = ax1.pcolormesh(QQ, CHi, data2d_stack[0].T, shading='auto')
    # fig.colorbar(pcm, ax=ax1)
    ax1.set_ylabel('chi [degree]')

    line1, = ax2.plot(q_values, data2d_stack[0].max(axis=0), label='Max intensity')
    line2, = ax2.plot(q_values, data2d_stack[0].mean(axis=0), label='Mean intensity')
    ax2.legend()
    ax2.set_ylabel('Intensity')

    I_powder /= I_powder.max() # normalize to 1
    ax3.plot([q_powder[0],q_powder[0]],[0,0],'r',label='Powder diffraction pattern')
    for (xi, yi, l) in zip(q_powder, I_powder, hkl):
        ax3.plot([xi,xi],[0,yi],'r')
        ax3.text(xi, yi, l, va='bottom', ha='center')
    ax3.set_ylabel('Relative intensity')
    ax3.set_ylim((0,1.1))

    fig.tight_layout()
    plt.subplots_adjust(bottom=0.15)#, hspace=0.3)

    # Slider setup
    ax_idx = plt.axes([0.15, 0.08, 0.7, 0.03])
    ax_yscale = plt.axes([0.25, 0.04, 0.5, 0.03])
    slider_idx = Slider(ax_idx, 'Index', 0, data2d_stack.shape[0] - 1, valinit=0, valstep=1)
    slider_yscale = RangeSlider(ax_yscale, 'Intensity min/max', 
                            data2d_stack.min(), data2d_stack.max(), 
                            valinit=(ax2.get_ylim()[0],ax2.get_ylim()[1]))
    
    global block_slider
    block_slider = False
    def update_idx(val):
        global block_slider
        idx = int(slider_idx.val)
        pcm.set_array(data2d_stack[idx].T)
        line1.set_ydata(data2d_stack[idx].max(axis=0))
        line2.set_ydata(data2d_stack[idx].mean(axis=0))
        if not block_slider:
            slider_yscale.set_val((0,data2d_stack[idx].max()))
            update_lim(0)
        fig.canvas.draw_idle()
    slider_idx.on_changed(update_idx)

    def update_lim(val):
        global block_slider
        ymin, ymax = slider_yscale.val
        ax2.set_ylim(ymin, ymax)
        pcm.set_clim(ymin, ymax)
        block_slider = True
        fig.canvas.draw_idle()
    slider_yscale.on_changed(update_lim)

    plt.show(block=True)