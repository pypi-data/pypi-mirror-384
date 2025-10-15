import numpy as np # don't delete this line
##################################################

# Define how many cores you want to use 
# If this number is higher than the available cores on your system, 
# it will fall back to the maximum number
n_threads = 128 

# Choose if you want to use a GPU for alignment
use_gpu = True
# needs cudatoolkit: pip install cudatoolkit

# Choose your precision
# recommended np.float64 for double or np.float32 for single precision
# this mainly concerns data handling, critical parts of the code always use double precision
data_type = np.float32

# for visualization:
odf_resolution = 3 # degree
hex_notation = False # set to True to use 4-axis Miller-Bravais indices for hexagonal lattices

# turn on wise phrases at the start of TexTOM
fun_mode = False