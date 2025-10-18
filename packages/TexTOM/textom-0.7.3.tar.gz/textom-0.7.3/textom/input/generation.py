import numpy as np
import textom.src.model.rotation as rot

# Sample rotations
angular_stepsize_vertical_rotation = 30 # degree
tilt_angles = (0,30,60)
omega, kappa = rot.samplerotations_eq3D(d_rot=angular_stepsize_vertical_rotation, tilts=tilt_angles)

# Sample size and shape
sample_outline_size = (4,5,6) # no of voxels in (x,y,z)
buffer = 1 # number of zero-voxels around the sample
sample_mask = np.zeros( sample_outline_size, bool )
sample_mask[buffer:-buffer,buffer:-buffer,buffer:-buffer] = 1

# detector points
q_det = np.linspace( 10, 35, num=100 )
chi_det = np.linspace(0, 360, num=120, endpoint=False)

# odf coefficients
intensity_style = 'uniform' # ...
coefficient_style = 'single_first' # 'single_random' #...
load_file = False # enable to load the parameters from a path