import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.patches import Rectangle
from matplotlib.widgets import Button, TextBox
from skimage.measure import marching_cubes
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy import ndimage
plt.ion()

""" Library for creating masks """
####################################################
class RegionSelector:
    def __init__(self, ax, ymin, ymax, max_regions=None, peaks=None):
        """
        Initialize the RegionSelector class.

        Parameters:
        ax (matplotlib.axes.Axes): The Axes object where the data is plotted.
        ymin (float): minimum value of the data.
        ymax (float): maximum value of the data.
        max_regions (int, optional): The maximum number of regions to select. If None, an arbitrary number of regions can be selected.
        """
        self.ax = ax
        self.ymin = ymin
        self.ymax = ymax
        self.max_regions = max_regions
        self.press = None
        self.rects = []
        self.current_rect = None
        self.peaks = peaks # this is to put another color if no peak is contained

        self.cidpress = ax.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease = ax.figure.canvas.mpl_connect('button_release_event', self.on_release)
        # self.cidmotion = ax.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.cidclick = ax.figure.canvas.mpl_connect('button_press_event', self.on_rightclick)

    def on_press(self, event):
        """
        Handle the mouse press event.

        Parameters:
        event (matplotlib.backend_bases.MouseEvent): The mouse event.
        """
        if event.inaxes != self.ax: return
        if self.ax.figure.canvas.toolbar.mode == 'zoom rect': return # does nothing when zooming
        if event.button != 1: return  # Only respond to left mouse button
        if self.max_regions is not None and len(self.rects) >= self.max_regions: return

        self.press_x = event.xdata
        self.ax.figure.canvas.draw()

    def on_release(self, event):
        """
        Handle the mouse release event.

        Parameters:
        event (matplotlib.backend_bases.MouseEvent): The mouse event.
        """
        if self.ax.figure.canvas.toolbar.mode == 'zoom rect': return # does nothing when zooming
        if event.button != 1: return  # Only respond to left mouse button
        if event.inaxes != self.ax: return

        release_x = event.xdata
        left = min(self.press_x,release_x)
        width = np.abs(self.press_x - release_x)

        if np.any(self.peaks):
            if np.any(np.logical_and(self.peaks>left, self.peaks<left+width)):
                col = 'yellow'
            else:
                col = 'red'
        else:
            col= 'yellow'

        self.current_rect = Rectangle((left, self.ymin),
                                      width, self.ymax - self.ymin,
                                      facecolor=col, edgecolor='magenta', alpha=0.3)
        self.ax.add_patch(self.current_rect)
        self.rects.append(self.current_rect)

        self.press = None
        self.ax.figure.canvas.draw()

    def on_rightclick(self, event):
        """
        Handle the mouse click event for removing selected regions.

        Parameters:
        event (matplotlib.backend_bases.MouseEvent): The mouse event.
        """
        if event.inaxes != self.ax: return
        if self.ax.figure.canvas.toolbar.mode == 'zoom rect': return # does nothing when zooming
        if event.button != 3: return  # Only respond to right mouse button
        for rect in self.rects:
            contains, _ = rect.contains(event)
            if contains:
                rect.remove()
                self.rects.remove(rect)
                self.ax.figure.canvas.draw()
                break

    def get_regions(self):
        """
        Get the selected peak regions.

        Returns:
        list of tuple: List of tuples representing the start and end of each selected region in x-axis coordinates.
        """
        regions = [(rect.get_x(), rect.get_x() + rect.get_width()) for rect in self.rects]
        return regions

def select_regions(data_x, data_y, data_x2=None, data_y2=None, hkl=None,
                            xlabel='q', ylabel='Intensity',
                            title = 'Select Regions by Holding LMB, Remove by RMB',
                            max_regions=None):
    """
    Plot the 2D XRD data and allow the user to select peak regions.

    Parameters:
    data_x (array-like): The x-axis data (e.g., 2? values).
    data_y (array-like): The y-axis data (e.g., intensity values).
    max_regions (int, optional): The maximum number of regions to select. If None, an arbitrary number of regions can be selected.

    Returns:
    list of tuple: List of tuples representing the start and end of each selected region in x-axis coordinates.
    """
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(data_x, data_y, '-x', label='Data')
    if np.any(data_y2):
        for (xi, yi, l) in zip(data_x2, data_y2, hkl):
            ax.plot([xi,xi],[0,yi],'r')
            ax.text(xi, yi, l, va='bottom', ha='center')
        # ax.plot(data_x2, data_y2, label='Powder pattern')
        minval = min(data_y.min(), data_y2.min())
        maxval = max(data_y.max(), data_y2.max())
    else:
        minval = data_y.min()
        maxval = data_y.max()
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    selector = RegionSelector(ax, minval, maxval, 
                    max_regions=max_regions, peaks=data_x2)
    plt.show(block=True)  # Keeps the plot open until it is manually closed
    return selector#.get_regions()


####################################################
class LineSelector:
    def __init__(self, ax, data, vertical=False, func=False):
        """
        Initialize the LineSelector class.

        Parameters:
        ax (matplotlib.axes.Axes): The Axes object where the data is plotted.
        """
        self.ax = ax
        self.data = data
        self.line = None
        self.value = None
        self.vertical = vertical

        self.cidclick = ax.figure.canvas.mpl_connect('button_press_event', self.on_click)

    def on_click(self, event):
        """
        Handle the mouse click event.

        Parameters:
        event (matplotlib.backend_bases.MouseEvent): The mouse event.
        """
        if event.inaxes != self.ax: return # does nothing if the click is outside
        if self.ax.figure.canvas.toolbar.mode == 'zoom rect': return # does nothing when zooming
        if self.line is not None:
            self.line.remove()
        if self.vertical:
            self.line = self.ax.axvline(x=event.xdata, color='red', linestyle='--')
            self.value = event.xdata    
        else:
            self.line = self.ax.axhline(y=event.ydata, color='red', linestyle='--')
            self.value = event.ydata
        self.ax.figure.canvas.draw()

        n_points_selected = (self.data > self.value).sum()
        print(f'\t\tNumber of points above threshold: {n_points_selected:d}')

    def get_value(self):
        """
        Get the y-value of the last drawn horizontal line.

        Returns:
        float: The y-value of the horizontal line.
        """
        return self.value

def select_threshold(data):
    """
    Plot a 1D array and allow the user to draw a horizontal line by clicking in the window.

    Parameters:
    data (array-like): The 1D data array to plot.

    Returns:
    float: The y-value of the last drawn horizontal line.
    """
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(data, label='1D Data')
    ax.set_xlabel('Voxel index')
    ax.set_ylabel('SAXS signal')
    ax.set_title('Click to Draw Horizontal Line')
    selector = LineSelector(ax, data)
    # plt.legend()
    plt.show()
    plt.ioff()
    plt.show(block=True)  # Keeps the plot open until it is manually closed
    return selector.get_value()

def select_threshold_hist(data, xlabel='Intensity', ylabel='Number of Voxels', 
                          title='Click to set the lower threshold', logx=False, logy=False):
    """
    Plot a histogram and allow the user to draw a vertical line by clicking in the window.

    Parameters:
    data (array-like): The 1D data array to plot.

    Returns:
    float: The x-value of the last drawn vertical line.
    """
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 6))
    nbins = 50
    if logx:
        bins = np.geomspace(data[data>0].min(), data.max(), nbins+1)
        # bins = np.logspace(np.log10(data[data>0].min()),np.log10(data.max()), nbins)
    else:
        bins=nbins

    ax.hist(data, bins=bins, label='1D Data')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if logx:
        ax.set_xscale('log')
    if logy:
        ax.set_yscale('log')
    selector = LineSelector(ax, data, vertical=True)
    # plt.legend()
    plt.show()
    plt.ioff()
    plt.show(block=True)  # Keeps the plot open until it is manually closed
    plt.ion()
    return selector.get_value()

def mask_voxels( Kappa, Omega, ty, tz, shifty, shiftz, x_p, tomogram, sinogram ):
    print('Identify your sample by drawing a rectangle over it')
    # find the images at angles to check sample geometry
    to_try = np.array([[0,0],[0,np.pi/2]])
    rgl = []
    for b in to_try:
        A = np.column_stack((Kappa, Omega % 2*np.pi))
        # check which of the projections is closest to the angles defined in totry
        distances = np.linalg.norm(A - b, axis=1)
        g_match = np.argmin(distances)
        # plot the projection in textom scale
        Y,Z = np.meshgrid( ty+shifty[g_match], tz+shiftz[g_match] )
        rgl.append( draw_rectangle_on_image( 
            sinogram[:,:,g_match].T, xy=(Y,Z),
            title=f'Projection No {g_match}, tilt = {A[g_match,0]*180/np.pi} \u00b0, rot = {A[g_match,1]*180/np.pi} \u00b0' 
        ))

    zmin = np.min( [rgl[0].start_point[1], rgl[0].end_point[1],
                    rgl[1].start_point[1], rgl[1].end_point[1],])
    zmax = np.max( [rgl[0].start_point[1], rgl[0].end_point[1],
                    rgl[1].start_point[1], rgl[1].end_point[1],])
    ymin = min( rgl[0].start_point[0], rgl[0].end_point[0] )
    ymax = max( rgl[0].start_point[0], rgl[0].end_point[0] )
    xmin = min( rgl[1].start_point[0], rgl[1].end_point[0] )
    xmax = max( rgl[1].start_point[0], rgl[1].end_point[0] )
    vmask_0 = np.logical_and.reduce((
            x_p[:,0] > xmin, x_p[:,0] < xmax,
            x_p[:,1] > ymin, x_p[:,1] < ymax,
            x_p[:,2] > zmin, x_p[:,2] < zmax,
    ))

    happy = 'n'
    while happy != 'y':
        print('\tMasking empty voxels. Choose lower threshold in figure.')
        tomo_flat = tomogram.flatten()
        # # draw all data in a sausage and choose a threshold directly
        # self.cutoff_low = msk.select_threshold( tomo_flat[vmask_0] )
        # draw a horizontal cutoff in a histogram
        cutoff_low = select_threshold_hist( tomo_flat[vmask_0] )

        # apply the cutoff and region exclusion to the mask
        vmask = np.logical_and.reduce((
            tomo_flat > cutoff_low,
            vmask_0))

        # # erosion dilation of noise
        # structure_size = 2
        # structuring_element = ndimage.generate_binary_structure(3, 1)
        # structuring_element = ndimage.iterate_structure(
        #     structuring_element, structure_size)
        # vmask = ndimage.binary_opening(vmask, structure=structuring_element)

        # smooth surface with a filter (and grow slightly)
        filled = ndimage.binary_fill_holes(vmask.reshape(tomogram.shape))
        smoothed = ndimage.gaussian_filter(filled.astype(float), sigma=1) > 0.4
        # keep largest component
        labeled, n = ndimage.label(smoothed)
        sizes = ndimage.sum(smoothed, labeled, range(1, n + 1))
        largest = labeled == (np.argmax(sizes) + 1)
        vmask = largest.flatten()
        print(f'\tSmoothed surface. New number of voxels: {vmask.sum()}')

        # print('\tMasking empty voxels. Choose regions to exclude in figure.')
        # sphere_mask = msk.sphere_exclusion(x_p[vmask])
        # vmask[vmask] = sphere_mask
        
        mask_voxels = np.where( vmask )[0]
        check_tomogram(tomogram, mask_voxels)
        happy = input('\thappy? (y/n) ')
    
    return mask_voxels

def check_tomogram( tomogram, mask ):
    """Plots the surface of a masked 3D object

    Parameters
    ----------
    tomogram : 4D ndarray, float
        data shape (nx,ny,nz,1)
    mask : 1D ndarray, int
        list of not masked voxels
    """
    masked_array = np.zeros_like(tomogram.flatten())
    masked_array[mask] = True
    masked_array = masked_array.reshape(tomogram.shape[:-1])
    
    verts, faces, _, _ = marching_cubes(masked_array, level=0.5, step_size=1)
    
    fig = plt.figure()#figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    ax.plot_trisurf(verts[:, 0], verts[:, 1], verts[:, 2], triangles=faces, cmap='viridis', lw=0.2, alpha=0.5)

    # Add labels for clarity
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Surface of the masked object. Verify and close figure")

    set_axes_equal(ax)
    plt.show(block=True)

def mask_detector( image, mask ):
    """Creates a mask on a 2D image by user-input

    Left-click on pixels to exclude, right-click to include
    Close window to confirm

    Parameters
    ----------
    image : 2D ndarray, float
        example image
    mask : 2D ndarray, bool
        a priori guess for the mask

    Returns
    -------
    2D ndarray, bool
    """
    maxval = image.max()

    fig, ax = plt.subplots( figsize = (10,10))
    ax.imshow(image, norm=colors.LogNorm(vmin=maxval*1e-2, vmax=maxval) )
    # Overlay the mask in red
    mask_color = np.zeros((*mask.shape, 4))  # Create an RGBA array
    mask_color[~mask] = [1, 0, 0, 0.5]  # Red with 50% transparency for True values
    ax.imshow( mask_color ) # plot the mask on top
    ax.set_title('Click pixels or draw lines. LMB mask, RMB unmask')

    def on_click(event):
        global start_point
        if event.inaxes != ax:
            return
        start_point = (event.xdata, event.ydata)

    def on_release(event):
        global start_point
        if event.inaxes != ax or start_point is None:
            return
        # calculate the line in pixels
        end_point = (event.xdata, event.ydata)
        distance = np.sqrt(
            (end_point[0] - start_point[0])**2 +\
            (end_point[1] - start_point[1])**2)
        if distance > 0.5:
            steps = np.arange(0, distance, step=0.5)
            points = np.unique(
                ( 
                np.round(start_point[0] + steps*(end_point[0]-start_point[0])/distance).astype(int),
                np.round(start_point[1] + steps*(end_point[1]-start_point[1])/distance).astype(int) ),
                axis=1, 
            ).T
        else:
            points = np.array([np.round(end_point)],dtype=int)

        if event.button == 1:  # Left mouse button: mask
            for p in points:
                mask[ p[1], p[0] ] = 0

        elif event.button == 3:  # Right mouse button: unmask
            for p in points:
                mask[ p[1], p[0] ] = 1

        # replot
        plt.gca().clear() 
        ax.set_title('Click pixels or draw lines. LMB mask, RMB unmask')
        ax.imshow(image, norm=colors.LogNorm(vmin=maxval*1e-2, vmax=maxval) )
        # Overlay the mask in red
        mask_color = np.zeros((*mask.shape, 4))  # Create an RGBA array
        mask_color[~mask] = [1, 0, 0, 0.5]  # Red with 50% transparency for True values
        ax.imshow( mask_color ) # plot the mask on top
        fig.canvas.draw_idle()

    cid_click = fig.canvas.mpl_connect('button_press_event', on_click)
    cid_release = fig.canvas.mpl_connect('button_release_event', on_release)

    plt.show(block=True)

    plt.figure()
    plt.imshow(mask)
    plt.title('Dark regions are masked')
    plt.show()

    return mask#.flatten()

####################################################
class RectangleDrawer:
    def __init__(self, ax, image):
        self.ax = ax
        self.image = image
        self.rect = None
        self.press = None
        self.start_point = None
        self.end_point = None
        self.cid_press = ax.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release = ax.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion = ax.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event):
        if event.inaxes != self.ax:
            return
        if self.rect is not None:
            self.rect.remove()
            self.rect = None
            self.ax.figure.canvas.draw()
        self.start_point = (event.xdata, event.ydata)
        self.rect = plt.Rectangle(self.start_point, 0, 0, fill=False, edgecolor='red')
        self.ax.add_patch(self.rect)
        self.press = event.xdata, event.ydata

    def on_motion(self, event):
        if self.press is None:
            return
        if event.inaxes != self.ax:
            return
        x0, y0 = self.press
        x1, y1 = event.xdata, event.ydata
        self.rect.set_width(x1 - x0)
        self.rect.set_height(y1 - y0)
        self.ax.figure.canvas.draw()

    def on_release(self, event):
        if self.press is None:
            return
        if event.inaxes != self.ax:
            return
        self.press = None
        self.end_point = (event.xdata, event.ydata)
        self.ax.figure.canvas.draw()

    def disconnect(self):
        self.ax.figure.canvas.mpl_disconnect(self.cid_press)
        self.ax.figure.canvas.mpl_disconnect(self.cid_release)
        self.ax.figure.canvas.mpl_disconnect(self.cid_motion)

def draw_rectangle_on_image(image, xy = None, title=''):
    fig, ax = plt.subplots()

    if xy:
        ax.pcolormesh(xy[0], xy[1], image, cmap='jet', 
                    #   norm=colors.LogNorm()
                      )
    else:
        ax.imshow(image, cmap='jet', 
                  #norm=colors.LogNorm()
                  )
    ax.set_title(title)

    drawer = RectangleDrawer(ax, image)
    plt.show(block=True)
    return drawer

# ####################################################
# def sphere_exclusion( data ):
#     # Initialize the plot
#     fig = plt.figure(figsize=(10, 6))
#     ax = fig.add_subplot(111, projection='3d')
#     ax.set_box_aspect([1, 1, 1])
#     ax.set_title("3D Scatter with Interactive Spheres")
#     ax.set_xlabel('x')
#     ax.set_ylabel('y')
#     ax.set_zlabel('z')

#     points = filter_grid_points(data)

#     # Initial scatter plot data
#     x = points[:,0] # np.random.rand(10)
#     y = points[:,1] # np.random.rand(10)
#     z = points[:,2] # np.random.rand(10)
#     colors = np.full(len(points), 'blue')  # Initial color for all points
#     scatter = ax.scatter(x, y, z, color=colors)

#     # Lists to store sphere data and plot objects
#     spheres = []
#     sphere_patches = []

#     # Lists to store sphere data (center and radius) and plot objects
#     spheres = []
#     sphere_patches = []

#     # Function to check if points are inside any sphere
#     def points_within_spheres(points, spheres):
#         bool_array = np.zeros(len(points), dtype=bool)
#         for (x_center, y_center, z_center, radius) in spheres:
#             distances = np.sqrt((points[:, 0] - x_center) ** 2 +
#                                 (points[:, 1] - y_center) ** 2 +
#                                 (points[:, 2] - z_center) ** 2)
#             bool_array |= distances <= radius
#         return bool_array
    
#     # Function to update scatter plot colors based on spheres
#     def update_point_colors():
#         inside_spheres = points_within_spheres(points, spheres)
#         colors = np.where(inside_spheres, 'red', 'blue')
#         scatter._facecolor3d = colors
#         scatter._edgecolor3d = colors
#         fig.canvas.draw_idle()

#     # Function to add a sphere
#     def add_sphere(event):
#         try:
#             x_center = float(text_box_x.text)
#             y_center = float(text_box_y.text)
#             z_center = float(text_box_z.text)
#             radius = float(text_box_radius.text)

#             # Generate sphere points for plotting
#             u = np.linspace(0, 2 * np.pi, 30)
#             v = np.linspace(0, np.pi, 30)
#             x_sphere = x_center + radius * np.outer(np.cos(u), np.sin(v))
#             y_sphere = y_center + radius * np.outer(np.sin(u), np.sin(v))
#             z_sphere = z_center + radius * np.outer(np.ones(np.size(u)), np.cos(v))

#             # Plot the sphere and add it to the lists
#             sphere = ax.plot_surface(x_sphere, y_sphere, z_sphere, color='r', alpha=0.3)
#             spheres.append((x_center, y_center, z_center, radius))
#             sphere_patches.append(sphere)

#             # Update point colors based on new spheres
#             update_point_colors()
#         except ValueError:
#             print("Please enter valid numerical values for center and radius.")

#     # Function to delete the last sphere added
#     def delete_sphere(event):
#         if sphere_patches:
#             sphere = sphere_patches.pop()
#             sphere.remove()
#             spheres.pop()
#             # Update point colors based on remaining spheres
#             update_point_colors()
#         else:
#             print("No spheres to delete.")

#     # Event handler for window close to return the boolean array
#     def on_close(event):
#         fig.canvas.stop_event_loop()  # Stop event loop if run interactively

#     fig.canvas.mpl_connect('close_event', on_close)

#     # Create TextBox and Button widgets on the right side of the plot
#     plt.subplots_adjust(left=0.05, right=0.75)

#     axbox_x = plt.axes([0.8, 0.75, 0.15, 0.05])
#     text_box_x = TextBox(axbox_x, 'X Center', initial="0")

#     axbox_y = plt.axes([0.8, 0.65, 0.15, 0.05])
#     text_box_y = TextBox(axbox_y, 'Y Center', initial="0")

#     axbox_z = plt.axes([0.8, 0.55, 0.15, 0.05])
#     text_box_z = TextBox(axbox_z, 'Z Center', initial="0")

#     axbox_radius = plt.axes([0.8, 0.45, 0.15, 0.05])
#     text_box_radius = TextBox(axbox_radius, 'Radius', initial="1")

#     add_button_ax = plt.axes([0.8, 0.35, 0.15, 0.05])
#     add_button = Button(add_button_ax, 'Add Sphere')
#     add_button.on_clicked(add_sphere)

#     delete_button_ax = plt.axes([0.8, 0.25, 0.15, 0.05])
#     delete_button = Button(delete_button_ax, 'Delete Sphere')
#     delete_button.on_clicked(delete_sphere)

#     set_axes_equal(ax)

#     # Display the plot and wait for it to close
#     plt.show(block=True)

#     # Calculate and return the boolean array indicating which points are in any sphere
#     cheese = ~points_within_spheres(data, spheres)
#     return cheese

def set_axes_equal(ax):
    """
    Make axes of 3D plot have equal scale so that spheres appear as spheres,
    cubes as cubes, etc.

    Input
      ax: a matplotlib axis, e.g., as output from plt.gca().
    """

    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    x_range = abs(x_limits[1] - x_limits[0])
    x_middle = np.mean(x_limits)
    y_range = abs(y_limits[1] - y_limits[0])
    y_middle = np.mean(y_limits)
    z_range = abs(z_limits[1] - z_limits[0])
    z_middle = np.mean(z_limits)

    # The plot bounding box is a sphere in the sense of the infinity
    # norm, hence I call half the max range the plot radius.
    plot_radius = 0.5*max([x_range, y_range, z_range])

    ax.set_xlim3d([x_middle - plot_radius, x_middle + plot_radius])
    ax.set_ylim3d([y_middle - plot_radius, y_middle + plot_radius])
    ax.set_zlim3d([z_middle - plot_radius, z_middle + plot_radius])
