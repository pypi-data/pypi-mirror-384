import numpy as np
import os, re, sys
import matplotlib.pyplot as plt
from numba import njit, prange
from time import time

from .. import handle as hdl
from . import rotation as rot
from . import symmetries as sym
from ..odf import hsh
from ..odf import gridbased as grd
from .. import numba_plugins as nb
from .. import plotting as plot
from ..analysis import orix_plugins as orx
from ...config import data_type, hex_notation

def parse_cif(file_path):
    """
    Parse a CIF file and calculate the positions of all atoms in the unit cell.
    
    Parameters:
        file_path (str): Path to the CIF file.

    Returns:
        dict: Contains lattice vectors, 
        atomic positions in fractional and Cartesian coordinates, and symmetry operations.
    """
    atom_labels = []
    atom_fractions = []
    space_group = None
    lattice_vectors = []
    symmetry_operations = []
    positions_cartesian = []
    occupancy = []
    B = []

    def parse_number(s):
        # this makes sure we can read numbers with given uncertainty, e.g. '4.9614(3)'
        return float(s.split('(')[0])

    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Parse the CIF file line by line
        for i, line in enumerate(lines):
            # Extract space group
            if line.startswith('_space_group_IT_number'):
                space_group = int( line.split()[-1].strip("'\"") )
            
            # Extract lattice vectors
            if line.startswith('_cell_length_a'):
                a = parse_number(line.split()[-1])
            elif line.startswith('_cell_length_b'):
                b = parse_number(line.split()[-1])
            elif line.startswith('_cell_length_c'):
                c = parse_number(line.split()[-1])
            elif line.startswith('_cell_angle_alpha'):
                alpha = parse_number(line.split()[-1])
            elif line.startswith('_cell_angle_beta'):
                beta = parse_number(line.split()[-1])
            elif line.startswith('_cell_angle_gamma'):
                gamma = parse_number(line.split()[-1])

            # Find atomic data section
            if line.strip().startswith('loop_'):
                # Look for atomic position headers in the following lines
                headers = []
                j = i + 1
                while j < len(lines) and lines[j].strip().startswith('_'):
                    headers.append(lines[j].strip())
                    j += 1

                # Check if this block contains atomic positions
                if ('_atom_site_fract_x' in headers and
                        '_atom_site_fract_y' in headers and
                        '_atom_site_fract_z' in headers):
                    # Start reading data rows
                    while j < len(lines) and not lines[j].strip().startswith('loop_') and lines[j].strip():
                        split_line = lines[j].split()
                        atom_labels.append(split_line[headers.index('_atom_site_type_symbol')])  # Assume first column is atom type
                        atom_fractions.append([parse_number(split_line[headers.index('_atom_site_fract_x')]),
                                            parse_number(split_line[headers.index('_atom_site_fract_y')]),
                                            parse_number(split_line[headers.index('_atom_site_fract_z')])])
                        occupancy.append(parse_number(split_line[headers.index('_atom_site_occupancy')]))

                        # B.append(float(split_line[headers.index('_atom_site_U_iso_or_equiv')]))
                        j += 1

        # Convert lattice parameters to lattice vectors
        alpha, beta, gamma = np.radians([alpha, beta, gamma])
        lattice_vectors = [
            [a, 0, 0],
            [b * np.cos(gamma), b * np.sin(gamma), 0],
            [
                c * np.cos(beta),
                c * (np.cos(alpha) - np.cos(beta) * np.cos(gamma)) / np.sin(gamma),
                c * np.sqrt(1 - np.cos(beta) ** 2 - (np.cos(alpha) - np.cos(beta) * np.cos(gamma)) ** 2 / np.sin(gamma) ** 2),
            ],
        ]
        lattice_vectors = np.array(lattice_vectors)

        # Extract symmetry operations
        symmetry_mode = False
        for line in lines:
            if '_space_group_symop_operation_xyz' in line:
                symmetry_mode = True
            elif symmetry_mode and line.strip() == '':
                symmetry_mode = False
            elif symmetry_mode:
                op = line.strip().strip("'")
                symmetry_operations.append(op)

        # Apply symmetry operations to fractional coordinates
        atom_fractions = np.array(atom_fractions)
        full_fractions, atom_list, occupancy_list, B_list = [], [], [], []
        for op in symmetry_operations:
            # for (frac, at, oc, b) in zip(atom_fractions, atom_labels, occupancy, B):
            for (frac, at, oc) in zip(atom_fractions, atom_labels, occupancy):
                full_fractions.append(apply_symmetry_operation(op, frac))
                atom_list.append(at)
                occupancy_list.append(oc)
                # B_list.append(b)
        full_fractions = np.array(full_fractions)
        full_fractions = np.mod(full_fractions, 1)  # Ensure all coordinates are within [0, 1)
        full_fractions, indices = np.unique(np.squeeze(np.round(full_fractions,5)), axis=0, return_index=True)

        # Convert fractional to Cartesian coordinates
        positions_cartesian = np.array(
            [np.dot(frac, lattice_vectors) for frac in full_fractions]
        )
        # for frac in full_fractions:
        #     cart = np.dot(frac, lattice_vectors)
        #     positions_cartesian.append(cart)

        return {
            "atom_types": atom_labels,
            "coordinates": np.array(atom_fractions),
            "lattice_vectors": lattice_vectors,
            "space_group": space_group or "Unknown",
            'symmetry_operations': symmetry_operations,
            'atom_list': np.array(atom_list)[indices],
            'fractional_positions': full_fractions,
            'cartesian_positions': positions_cartesian,
            'occupancy': np.atleast_1d(occupancy_list)[indices],
            # 'B': np.atleast_1d(B_list)[indices],
        }

    except Exception as e:
        print(f"Error parsing CIF file: {e}")
        return None

def wavelength_from_E_keV(E_keV):
    h = 4.135667696e-18 # keV*s
    c = 299792458 # m/s
    wavelength = h*c*1e9 / E_keV # nm
    return wavelength

def get_reciprocal_space_coordinates(Qq_det, Chi_det, E_keV, geo):
    """Calculates the coordinates of the detector points based on
    polar coordinates q_det, chi_det and X-ray energy E_kev

    Returns
    -------
    ndarray
        3D reciprocal space coordinates and number of detector points
    """

    wavelength = wavelength_from_E_keV(E_keV)

    Two_theta = 2 * np.arcsin(Qq_det * wavelength / (4*np.pi))
    QX,QY,QZ = np.empty_like(Two_theta), np.empty_like(Two_theta), np.empty_like(Two_theta)
    for k in range(QY.shape[0]):
        QX[k], QY[k], QZ[k] = reciprocal_lattice_point(Two_theta[k], Chi_det[k], wavelength,
            u_beam=geo.beam_direction,
            u0=geo.detector_direction_origin,
            u90=geo.detector_direction_positive_90,
        )

    # import matplotlib.pyplot as plt
    # fig = plt.figure(figsize=(8, 6))
    # ax = fig.add_subplot(121, projection='3d')
    # ax.scatter(QX, QY, QZ)
    # ax.set_xlabel('x')
    # ax.set_ylabel('y')
    # ax.set_zlabel('z')
    return np.column_stack([QX, QY, QZ])

# @njit
def reciprocal_lattice_point(two_theta_rad, chi_rad, wavelength_nm, 
                             u_beam=(1,0,0), u0=(0,0,1), u90=(0,1,0)):
    """
    Calculate (qx, qy, qz) from angles and wavelength, defining the geometry by vectors.

    Parameters:
    - two_theta_rad: scattering angle (2?) in rad
    - chi_rad: azimuthal angle in rad
    - wavelength_nm: wavelength of incident beam in nm
    Optional:
    - u_beam: beam direction vector
    - u0: direction vector pointing towards the origin of chi
    - u90: direction vector pointing towards chi of +90 degree

    Returns:
    - (qx, qy, qz): reciprocal space coordinates (nm^-1)
    """
    # axes
    u_beam = np.array(u_beam, data_type)
    u0 = np.array(u0, data_type)
    u90 = np.array(u90, data_type)

    # Magnitude of wavevector
    k = 2 * np.pi / wavelength_nm

    # Incoming wavevector:
    k_in = k * u_beam

    # Outgoing wavevector (direction from spherical coordinates)
    k_out = k * (
        np.cos(two_theta_rad) * u_beam + 
        np.sin(two_theta_rad) * ( np.cos(chi_rad) * u0 + np.sin(chi_rad) * u90 )
        )

    q = k_out - k_in
    return q

def apply_symmetry_operation(operation, position):
    """
    Apply a symmetry operation to a fractional position.

    Parameters:
        operation (str): The symmetry operation in CIF format (e.g., "x,y,z").
        position (list or np.ndarray): Fractional coordinates [x, y, z].

    Returns:
        np.ndarray: New fractional coordinates after applying the operation.
    """
    # Ensure the symmetry operation format is consistent and parse it
    operation = operation.strip().replace(' ', '')  # Remove spaces for easier parsing
    operation = operation.replace('x', '{x}').replace('y', '{y}').replace('z', '{z}')

    # Check for simple transformations (e.g., -x or x+1/2)
    operation = re.sub(r'([+-]?\d*\.\d+|\d+)', r'float("\1")', operation)  # Convert numbers to float type

    x, y, z = position
    local_dict = {'x': x, 'y': y, 'z': z}

    # Safely evaluate the operation
    try:
        new_pos = [eval(operation.format(x=x, y=y, z=z))]
        return np.array(new_pos)
    except Exception as e:
        print(f"Error applying symmetry operation: {operation}")
        raise e

"""
array([[1.3268    , 3.70216157, 4.84805619],
       [3.9804    , 5.19063843, 1.57644381],
       [3.9804    , 8.14856157, 4.78869381],
       [1.3268    , 0.74423843, 1.63580619],
       [1.3268    , 6.72562464, 5.90861265],
       [3.9804    , 2.16717536, 0.51588735],
       [3.9804    , 2.27922464, 3.72813735],
       [1.3268    , 6.61357536, 2.69636265],
       [1.3268    , 8.0124128 , 5.85593175],
       [3.9804    , 0.8803872 , 0.56856825],
       [3.9804    , 3.5660128 , 3.78081825],
       [1.3268    , 5.3267872 , 2.64368175],
       [2.43918912, 6.08356448, 5.9066853 ],
       [2.86801088, 2.80923552, 0.5178147 ],
       [2.86801088, 1.63716448, 3.7300647 ],
       [2.43918912, 7.25563552, 2.6944353 ],
       [5.09278912, 2.80923552, 0.5178147 ],
       [0.21441088, 6.08356448, 5.9066853 ],
       [0.21441088, 7.25563552, 2.6944353 ],
       [5.09278912, 1.63716448, 3.7300647 ]])
       """

def get_reciprocal_points( lattice_vectors, hkl_list):
    """
    Calculate reciprocal lattice points for the given crystal up to the given miller indices.
    """
    # Direct lattice vectors 
    a1 = lattice_vectors[0]
    a2 = lattice_vectors[1]
    a3 = lattice_vectors[2]
    
    # Reciprocal lattice vectors
    V = np.dot(a1, np.cross(a2, a3))  # Unit cell volume
    b1 = 2 * np.pi * np.cross(a2, a3) / V
    b2 = 2 * np.pi * np.cross(a3, a1) / V
    b3 = 2 * np.pi * np.cross(a1, a2) / V
    
    # Generate reciprocal lattice points
    reciprocal_points = []
    for hkl in hkl_list:
        G = hkl[0] * b1 + hkl[1] * b2 + hkl[2] * b3
        reciprocal_points.append(G)
    
    return np.array(reciprocal_points)

def group_equivalent_reflections(hkl_max, lattice_vectors, point_group_quaternions):
    """Group reflections into families using symmetry operations."""
    families = {}
    
    # Generate reciprocal lattice points
    h_vals = np.arange(-hkl_max, hkl_max + 1)
    k_vals = np.arange(-hkl_max, hkl_max + 1)
    l_vals = np.arange(-hkl_max, hkl_max + 1)
    indices = []
    for h in h_vals:
        for k in k_vals:
            for l in l_vals:
                indices.append([h,k,l])

    # Reciprocal lattice vectors
    V = np.dot(lattice_vectors[0], np.cross(lattice_vectors[1], lattice_vectors[2]))  # Unit cell volume
    reciprocal_lattice_vectors = np.column_stack([
        2 * np.pi * np.cross(lattice_vectors[1], lattice_vectors[2]) / V,
        2 * np.pi * np.cross(lattice_vectors[2], lattice_vectors[0]) / V,
        2 * np.pi * np.cross(lattice_vectors[0], lattice_vectors[1]) / V
        ])

    for hkl in indices:
        # skip (0,0,0)
        if tuple(hkl) == (0,0,0):
            continue
        equivalents = equivalents_of_hkl(hkl, reciprocal_lattice_vectors, point_group_quaternions)

        # pick representative        
        pos_eq = np.all(np.greater_equal(equivalents,0),axis=1)
        if np.any(pos_eq):
            rep = tuple(max(np.array(equivalents)[pos_eq].tolist()))
        else:
            rep = max(equivalents)

        if rep not in families:
            families[rep] = set()
            families[rep].update(equivalents)
    
    representatives = []
    equivalents = []
    for rep, eqs in families.items():
        representatives.append(rep)
        equivalents.append(eqs)
    
    return representatives, equivalents


def equivalents_of_hkl(hkl, B, rotations, include_inversion=True,
                       tol=1e-4, friedel_equivalence=True):
    """
    Determine multiplicity of Miller index hkl under provided point-group rotations.
    Inputs:
      - hkl: tuple/list (h,k,l) integers
      - B: 3x3 reciprocal basis matrix [b1 b2 b3] (columns)
      - rotations: iterable of quaternions (proper rotations)
      - include_inversion: whether to also include inversion (-I)
      - tol: acceptance tolerance in reciprocal-space (same units as B)
      - friedel_equivalence: if True, treat hkl and -h-k-l as identical (Friedel)
    Returns:
      - unique_hkls: list of unique integer (h,k,l) generated
      - count: multiplicity (len of unique_hkls)
    """
    hkl = np.asarray(hkl, dtype=int)
    G = B @ hkl.reshape(3,1) 
    Binv = np.linalg.inv(B)
    found = []

    def accept_Gprime(Gp):
        # Convert back to h' (real)
        h_real = Binv @ Gp
        h_rounded = np.rint(h_real).astype(int).flatten()
        # compute residual in reciprocal space
        resid = np.linalg.norm(B @ h_rounded - Gp)
        if resid <= tol:
            return tuple(h_rounded)
        else:
            return None

    for q in rotations:
        Gp = rot.quaternion_rotate_vector( q, G.flatten() )
        h_ = accept_Gprime(Gp)
        if h_ is not None:
            found.append(h_)
        if include_inversion:
            Gp_inv = -Gp
            h2 = accept_Gprime(Gp_inv)
            if h2 is not None:
                found.append(h2)

    # canonicalize/fold Friedel pairs if requested
    unique_set = set()
    for h in found:
        if friedel_equivalence:
            h_neg = tuple((-np.array(h)).tolist())
            rep = max(h, h_neg)
        else:
            rep = h
        unique_set.add(rep)

    unique_hkls = sorted(unique_set)
    return unique_hkls

# def plot_powder_pattern(reciprocal_points, energy_keV, num_bins=100):
#     """Compute and plot the powder diffraction pattern (Intensity vs 2??)."""
#     wavelength = 12.398 / energy_keV  # Convert energy to wavelength (Å?)
#     G_magnitudes = np.linalg.norm(reciprocal_points, axis=1)  # Compute |G|
    
#     # Convert |G| to 2?? using Bragg's Law: 2?? = 2 * arcsin(??G / 4??)
#     theta_2 = 2 * np.arcsin(wavelength * G_magnitudes / (4 * np.pi)) * (180 / np.pi)  # Convert to degrees
    
#     # Create histogram (powder diffraction pattern)
#     hist, bin_edges = np.histogram(theta_2, bins=num_bins, density=True)
#     bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
#     # Plot powder pattern
#     plt.figure(figsize=(8, 5))
#     plt.plot(bin_centers, hist, '-k', lw=1.5)
#     plt.xlabel('2?? (degrees)')
#     plt.ylabel('Intensity (arb. units)')
#     plt.title('Simulated Powder Diffraction Pattern')
#     plt.grid(True)
#     plt.show()

#####
## there is the possibility to get the structure factor and others (Lorenz factor, solid angle correction, Debye-Waller factor, polarization correction)
## directly out of an average over the data
## Marc will not like this, but in many cases it might be more stable - it changes however the weights of the q-bins
# solidangle_factor = np.abs(np.sin(np.deg2rad(azim_angles)))[np.newaxis, np.newaxis, np.newaxis, :, np.newaxis] * np.ones(data_array.shape)
# intensity_scaling_factors = np.mean(data_array * solidangle_factor, axis = (0,1,2,3)) / np.mean(solidangle_factor, axis = (0,1,2,3))
# intensity_scaling_factors = intensity_scaling_factors/intensity_scaling_factors[0]
#####

# def structure_factor(hkl, lattice_vectors, frac_coords, species,
#                      form_factor_fn, occupancy=None, B=None):
#     """
#     hkl: tuple/list (h,k,l)
#     lattice_vectors: 3x3 array-like, columns = a, b, c (in angstroms)
#     frac_coords: Nx3 array of fractional coordinates (x,y,z)
#     species: list of length N with element symbols matching form_factor_fn
#     form_factor_fn: callable f(element, s) -> scalar real (atomic form factor)
#                     where s = sin(theta)/lambda
#     occupancy: optional list/array length N (default 1)
#     B: optional list/array length N of isotropic B factors (angstrom^2) (default 0)
#     Returns complex F and intensity |F|^2
#     """
#     h, k, l = hkl
#     A = np.asarray(lattice_vectors).reshape(3,3)
#     # compute G vector (reciprocal space)
#     A_inv = np.linalg.inv(A)
#     G = 2*np.pi * (A_inv.T @ np.array([h,k,l]))   # cartesian reciprocal vector
#     s = np.linalg.norm(G) / (4*np.pi)             # sin(theta)/lambda
#     coords = np.asarray(frac_coords)
#     N = coords.shape[0]
#     occ = np.ones(N) if occupancy is None else np.asarray(occupancy)
#     Barr = np.zeros(N) if B is None else np.asarray(B)
#     F = 0+0j
#     for j in range(N):
#         x,y,z = coords[j]
#         f = form_factor_fn(species[j], s)
#         phase = np.exp(2j*np.pi*(h*x + k*y + l*z))
#         thermal = np.exp(-Barr[j]*s*s)
#         F += occ[j] * f * thermal * phase
#     I = (F.real**2 + F.imag**2)
#     return F, I

def structure_factor_q(hkl, lattice_vectors, frac_coords,
                       form_factors, occupancy=None, B=None):
    """
    
    """
    h, k, l = hkl
    A = np.asarray(lattice_vectors).reshape(3,3)
    A_inv = np.linalg.inv(A)
    G = 2*np.pi * (A_inv.T @ np.array([h,k,l]))
    q = np.linalg.norm(G)
    coords = np.asarray(frac_coords)
    N = coords.shape[0]
    occ = np.ones(N) if occupancy is None else np.asarray(occupancy)
    Barr = np.zeros(N) if B is None else np.asarray(B)
    F = 0+0j
    for j in range(N):
        x,y,z = coords[j]
        f = form_factors[j]
        thermal = np.exp(-Barr[j]*(q/(4*np.pi))**2)
        phase = np.exp(2j*np.pi*(h*x + k*y + l*z))
        F += occ[j] * f * thermal * phase
    I = (F.real**2 + F.imag**2)

    return F, I

# @njit       
def structure_factor( reciprocal_points, atomic_form_factors, atom_positions, bool_pos_el ):
    '''
    reciprocal_points: 2D ndarray, float
        dim 0: reciprocal lattice points, 1: [qx,qy,qz]
    atomic_form_factors : 2D ndarray, float
        atomic form factors for different elements
        dim0: elements, dim1: q
    unit_cell_pos: 2D ndarray, float
        real space atomic positions
    bool_pos_el : 2D ndarray, string
        mask for uc_pos to find elements
        dim0: element dim1: mask for positions in uc

    Return values
    -------------
    SU_complex: 1D ndarray, complex128
        structure factor of the unit cell, function of Q
        dim0: complex structure factor
    '''
    S_complex=np.zeros_like(reciprocal_points[:,0], np.complex128)
    nEl=bool_pos_el.shape[0]
    
    for i in range(nEl): #for all elements 
        # f=atomic_form_factors[i] #get atomic form factor (for all Qs)
        S_element=np.zeros_like(S_complex)
        for r in atom_positions[bool_pos_el[i,:]]: #all atom positions of that element
            qr = np.dot(reciprocal_points,r)
            S_element += np.exp(qr*1j)
        S_complex += atomic_form_factors[i] * S_element
    return np.real(S_complex*S_complex.conjugate())

def structure_factor_from_cif(cif_path, cutoff_structure_factor=1e-4, max_hkl=4, q_min=0, q_max=60, wavelength=None, powder=False):

    crystal_data = parse_cif(cif_path)
    lattice_vectors = crystal_data['lattice_vectors']/10 # assumes angstroem and converts to nm
    chem = crystal_data['atom_list'] # chemical symbols of all atoms in the unit cell
    atom_positions = crystal_data['cartesian_positions']/10 # coordinates of all atoms in the unit cell converted to nm
    space_group_no = crystal_data['space_group']
    # # alternatively import with ase:
    # import ase
    # unit = ase.io.read(cif_path)
    # atom_positions1 = unit.positions/10 # coordinates of all atoms converted to nm
    # chem = np.array( unit.get_chemical_symbols() ) # chemical symbols of all atoms
    # lattice_vectors = np.array( unit.get_cell() )/10 # converted to nm
    # space_group_no = unit.info['spacegroup'].no
    #

    #### Calculate reciprocal lattice points
    symmetry = sym.get_proper_point_group(space_group_no)
    gen = sym.generators(symmetry)
    Q_gen = rot.QfromOTP(gen)
    Q_group = rot.generate_group(Q_gen) # point group rotational symmetries
    hkl_list_full, hkl_equivalents_full = group_equivalent_reflections(max_hkl, lattice_vectors, Q_group)

    reciprocal_points_full = get_reciprocal_points( lattice_vectors, hkl_list_full )
    q_abs_full = np.linalg.norm(reciprocal_points_full, axis=1)
    # cut at max q
    mask = np.logical_and(q_abs_full < q_max, q_abs_full > q_min )
    hkl_list = np.array(hkl_list_full)[mask]
    hkl_equivalents = np.array(hkl_equivalents_full)[mask]
    reciprocal_points = reciprocal_points_full[mask]
    q_abs = q_abs_full[mask]

    #### Calculate atomic form factors
    elements = np.unique(chem)
    Nel = elements.size
    #bool mask for the unit cell
    atom_types_bool = np.empty( (Nel, chem.shape[0]), bool )
    for k in range(Nel):
        # determinate the positions of element k 
        atom_types_bool[k,:] = chem == elements[k]
    # load Cromer??Mann coefficients
    ff_path = hdl.get_file_path('textom',
        os.path.join('ressources','atomic_formfactors.txt'))
    ffcoeff = np.genfromtxt( ff_path, dtype="|U8", skip_header=2 )
    ffcoeff_used = np.array([ ffcoeff[ np.where( el == ffcoeff )[0][0], 1: ] for el in elements]).astype(data_type)
    a = ffcoeff_used[:,0:-1:2]
    b = ffcoeff_used[:,1:-1:2]
    c = ffcoeff_used[:,-1]
    FF_element = np.empty( (Nel, q_abs.size), np.float64 ) # atomic form factors for all used elements
    for k in range(Nel):
        A, Qf = np.meshgrid( a[k], q_abs/10 ) # using angstroems^-1 here for simplicity
        B, _ = np.meshgrid( b[k], q_abs/10 )
        C = c[k]
        #Calculate form factor http://lampx.tugraz.at/~hadley/ss1/crystaldiffraction/atomicformfactors/formfactors.php
        F = ( A * np.exp( -B * (Qf/(4*np.pi))**2  ) ).sum(axis=1) + C
        # _, FF = np.meshgrid( self.Chi_det.reshape(self.detShape)[0], F )
        FF_element[k,:] = F
    #
    # plot to verify form factors:
    # idcs = np.argsort(q_abs)
    # plt.plot(q_abs[idcs],FF_element[0,idcs])
    # #

    ### Calculate structure factor from unit cell
    form_factors = np.array([FF_element[np.where(e==elements)[0][0]] for e in chem])
    structure_factors = np.empty_like(form_factors[0])
    for k in range(hkl_list.shape[0]):
        F,I=structure_factor_q(
            hkl_list[k], 
            crystal_data['lattice_vectors'].T, # note that it takes input in angstroem
            crystal_data['fractional_positions'], 
            form_factors[:,k], crystal_data['occupancy'], None )#crystal_data['B'])
        structure_factors[k] = I

    # structure_factors = structure_factor( reciprocal_points, FF_element, atom_positions, atom_types_bool)
    # # plot to verify structure factors:
    # idcs = np.argsort(q_abs)
    # plt.plot(q_abs[idcs],structure_factors[idcs], 'x')
    # #

    # exclude non-diffracting peaks from here (cut-off - corresponds to extinction conditions)
    mask_diffracting_peaks = structure_factors > cutoff_structure_factor*structure_factors.max()
    mask_diffracting_peaks[0] = False # exclude [0 0 0]
    q_used = q_abs[mask_diffracting_peaks]
    hkl_used = hkl_list[mask_diffracting_peaks]
    structure_factors_used = structure_factors[mask_diffracting_peaks]
    hkl_equivalents_used = hkl_equivalents[mask_diffracting_peaks]
    multiplicities_used = np.array([len(eq) for eq in hkl_equivalents_used])
    reciprocal_points_used = reciprocal_points[mask_diffracting_peaks]
    # and sort
    order = np.argsort(q_used)
    q_used = q_used[order]
    hkl_used = hkl_used[order]
    structure_factors_used = structure_factors_used[order]
    multiplicities_used = multiplicities_used[order] * 2 # for the friedel pairs
    hkl_equivalents_used = hkl_equivalents_used[order] # not returned atm
    reciprocal_points_used = reciprocal_points_used[order]

    reciprocal_points_used_full = np.concatenate([
        get_reciprocal_points(lattice_vectors, np.array(list(hkl_eq))) for hkl_eq in hkl_equivalents_used]
    )

    if hex_notation and symmetry[0] == '6':
        hkl_used = miller_to_hex(hkl_used)

    if powder:
        return q_used, hkl_used, structure_factors_used, multiplicities_used
    else:
        return q_used, reciprocal_points_used_full, structure_factors_used, multiplicities_used, hkl_used, symmetry
    # schreit nach einem structure_dict oder object

def miller_to_hex(indices):
    """
    Convert 3-index Miller indices (h,k,l) to 4-index hexagonal (h,k,i,l).
    
    Parameters
    ----------
    indices : array-like, shape (3,) or (N,3)
        Input Miller indices (h,k,l).
    
    Returns
    -------
    hex_indices : ndarray, shape (4,) or (N,4)
        Converted hexagonal indices (h,k,i,l).
    """
    arr = np.atleast_2d(indices).astype(int)
    h, k, l = arr[:, 0], arr[:, 1], arr[:, 2]
    i = -(h + k)
    hex_arr = np.stack([h, k, i, l], axis=1)
    return hex_arr if indices.ndim > 1 else hex_arr[0]


def hex_to_miller(indices, check=True):
    """
    Convert 4-index hexagonal (h,k,i,l) to 3-index Miller (h,k,l).
    
    Parameters
    ----------
    indices : array-like, shape (4,) or (N,4)
        Input hexagonal indices (h,k,i,l).
    check : bool
        If True, enforce i = -(h+k).
    
    Returns
    -------
    miller_indices : ndarray, shape (3,) or (N,3)
        Converted Miller indices (h,k,l).
    """
    arr = np.atleast_2d(indices).astype(int)
    h, k, i, l = arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3]

    if check:
        expected = -(h + k)
        if not np.all(i == expected):
            raise ValueError(f"Inconsistent indices: expected i={expected}, got {i}")

    miller_arr = np.stack([h, k, l], axis=1)
    return miller_arr if indices.ndim > 1 else miller_arr[0]

def plot_powder_pattern(cif_path, cutoff_structure_factor=1e-4, max_hkl=4, q_min=0, q_max=60, 
                        wavelength=None, q_dat=None, chi_dat=None, I_dat=None):
    
    q, hkl, S, M = structure_factor_from_cif(cif_path, cutoff_structure_factor, max_hkl,  
                                             q_min=q_min, q_max=q_max, wavelength=wavelength,
                                             powder=True)
    
    if wavelength:
        # compute theta in radians
        theta = np.arcsin(wavelength * q / (4*np.pi))
        Lorentz = 1/np.sin(2*theta)
    else:
        Lorentz = 1

    powder_intensities = S * M * Lorentz
    # plt.plot( q_used, powder_intensities, 'x' )
    # print('hkl\tq\tInt\t\tRelative I\tMultiplicity')
    print('hkl\tq\tRelative I\tMultiplicity')
    # plt.figure()
    # plt.plot([q[0],q[0]],[0,0],'r',label='Powder diffraction pattern')
    for (xi, yi, l, m) in zip(q, powder_intensities, hkl, M):
        # plt.plot([xi,xi],[0,yi],'r')
        # plt.text(xi, yi, l, va='bottom', ha='center')
        # print(f'{l}\t{xi:5.3}\t{yi:8.1f}\t{100*yi/powder_intensities.max():.1f}\t{m}')
        print(f'{l}\t{xi:5.3}\t{100*yi/powder_intensities.max():.1f}\t\t{m}')
    # if np.any(q_dat):
    #     
    #     q_dat = q_dat[msk_q]
    #     I_dat = I_dat[msk_q] * powder_intensities.max() / I_dat[msk_q].max()
    #     plt.plot(q_dat, I_dat, label='Data')
    #     plt.legend()
    # plt.ylim(bottom=0)
    # plt.xlabel('q / nm^-1')
    # plt.ylabel('Intensity')
    # plt.show(block=True)

    if np.any(q_dat):
        msk_q = np.logical_and(q_dat>q_min, q_dat<q_max)
        plot.compare_data_powder( q_dat[msk_q], chi_dat, I_dat[:,:,msk_q],
                                 q, powder_intensities, hkl )
    else:
        plt.figure()
        for (xi, yi, l) in zip(q, powder_intensities, hkl):
            plt.plot([xi,xi],[0,yi],'r')
            plt.text(xi, yi, l, va='bottom', ha='center')
        plt.ylim(bottom=0)
        plt.xlabel('q / nm^-1')
        plt.ylabel('Intensity')
        plt.show(block=True)
# @njit
# def quaternion_to_match_vectors(u, v):
#     """
#     Returns the quaternion (w, x, y, z) that rotates unit vector u into v.
#     u and v must be 3D unit vectors.
#     """
#     u = np.asarray(u, dtype=np.float64)
#     v = np.asarray(v, dtype=np.float64)
#     u /= np.linalg.norm(u)
#     v /= np.linalg.norm(v)

#     dot = np.dot(u, v)

#     if np.isclose(dot, 1.0):
#         # Vectors are the same
#         return np.array([1.0, 0.0, 0.0, 0.0])
#     elif np.isclose(dot, -1.0):
#         # Vectors are opposite
#         # Find an orthogonal vector
#         orthogonal = np.array([1.0, 0.0, 0.0])
#         if np.isclose(abs(u[0]), 1.0):
#             orthogonal = np.array([0.0, 1.0, 0.0])
#         axis = np.cross(u, orthogonal)
#         axis /= np.linalg.norm(axis)
#         return np.array([0.0, *axis])  # 180°? rotation: w=0
#     else:
#         axis = np.cross(u, v)
#         axis /= np.linalg.norm(axis)
#         angle = np.arccos(nb.nb_clip(dot, -1.0, 1.0))
#         w = np.cos(angle / 2.0)
#         xyz = axis * np.sin(angle / 2.0)
#         return np.concatenate(([w], xyz))

@njit
def quaternion_to_match_vectors(u, v):
    """
    Returns the quaternion (w, x, y, z) that rotates unit vector u into v.
    u and v must be 3D unit vectors.
    """
    u = u/nb.nb_vectornorm(u.astype(np.float64))
    v = v/nb.nb_vectornorm(v.astype(np.float64))

    d = nb.nb_dot(u, v)

    # Same direction
    if abs(d - 1.0) < 1e-12:
        return np.array([1.0, 0.0, 0.0, 0.0])

    # Opposite direction
    elif abs(d + 1.0) < 1e-12:
        # Find an orthogonal axis
        if abs(u[0]) < 0.9:
            ortho = np.array([1.0, 0.0, 0.0])
        else:
            ortho = np.array([0.0, 1.0, 0.0])
        axis = nb.nb_cross(u, ortho)
        axis = axis/nb.nb_vectornorm(axis)
        return np.array([0.0, axis[0], axis[1], axis[2]])

    # General case
    else:
        axis = nb.nb_cross(u, v)
        axis = axis/nb.nb_vectornorm(axis)
        # Clip dot to [-1,1] manually to avoid NaNs
        dd = d
        if dd > 1.0: dd = 1.0
        elif dd < -1.0: dd = -1.0
        angle = np.arccos(dd)
        w = np.cos(angle/2.0)
        s = np.sin(angle/2.0)
        return np.array([w, axis[0]*s, axis[1]*s, axis[2]*s])

@njit
def get_orientations_seen_on_pixel(q_detector, q_peak, sampling):
    '''
    q_peak is the reciprocal coordinate of the bragg-peak connected to no crystal rotation
        (center of the ODF)
    q_detector is the detector point reciprocal coordinate
    sampling is the number of rotation angles around the axis that are calculated
    '''

    if np.abs(nb.nb_vectornorm(q_detector)-nb.nb_vectornorm(q_peak)) > 1e-3: # 1e-10 is maybe a bit strict
        print("Can't rotate peak into desired q - check input")
        return # np.nan
    
    # Find a rotation that rotates the bragg peak on the detector pixel
    R_align = quaternion_to_match_vectors( q_peak, q_detector )

    # Define quaternion orientations that will produce the same bragg peaks
    axis = q_detector/nb.nb_vectornorm(q_detector) # i,j,k parts of Rot2
    ome = np.linspace(-np.pi, np.pi, sampling)
    w = np.cos(ome/2)
    ijk = np.zeros((sampling, 3)) 
    for i in range(3):
        ijk[:,i] = np.sin(ome/2) * axis[i]
    R_sampling = np.hstack((np.atleast_2d(w).T , ijk))
    # # invert all quaternions with negative first component (doesn't happen)
    # R_sampling[R_sampling[:,0]<0] = -R_sampling[R_sampling[:,0]<0]

    Rotations = np.zeros_like(R_sampling)
    for i in range(sampling):
        Rotations[i] = rot.quaternion_multiply( R_sampling[i], R_align)
        # xxxxx Rotations[i] = rot.quaternion_multiply( R_align, R_sampling[i] )
    
    return Rotations

@njit
def get_probability(q_peak, q_detector, odf_basis_function, odf_args, sampling=300):
    ''' 
    Paramters:
    --------
    q_peak: 1d ndarray, float 
        peak location in reciprocal space (in base orientation)
    q_detector: 1d ndarray, float
        desired peak location after rotation
    orientation_distribution: function
        probability function
    odf_args : tuple
        input for the function

    Returns:
    -------------
    proba: float
        probability that a peak appears at q_detector, given the ODF(mu,sig/kap)
    '''

    Rotations = get_orientations_seen_on_pixel(q_detector, q_peak, sampling)

    # orot = Rotation(Rotations)
    # oori = Orientation(orot, symmetry=point_group)
    # orot_fz = oori < OrientationRegion(point_group)

    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')
    # ax.scatter(Rotations[:,1],Rotations[:,2],Rotations[:,3])
    # ax.set_xlim((-1,1))
    # ax.set_ylim((-1,1))
    # ax.set_zlim((-1,1))

    # evaluate the basis function at these orientations
    Probabilities = odf_basis_function( Rotations, *odf_args )
    # plt.plot(np.linspace(-180,180,num=Probabilities.size),Probabilities)

    probability_integrated = nb.trapz( Probabilities, 2*np.pi/sampling )
    return probability_integrated

@njit
def diffractlet( detector_coordinates, reciprocal_points, structure_factors, multiplicities, dtype_odf,
                odf_basis_function, odf_args ):

    n_peaks = structure_factors.size
    odf = np.zeros( detector_coordinates.shape[:2], dtype_odf ) # need complex for HSH
    for i_peak in range(n_peaks):
        for i_chi, q_detector in enumerate(detector_coordinates[:,i_peak]): 
            # for q in Q_group:
            #     point = rot.quaternion_rotate_vector(q, reciprocal_points[i_peak].copy())
            #     odf[i_peak, i_chi] += get_probability( 
            #         point, q_detector.copy(), 
            #         odf_basis_function, odf_args, sampling=100)
            #     # # friedel partner 
            #     # odf[i_peak, i_chi] += get_probability( 
            #     #     -point, q_detector.copy(), 
            #     #     odf_basis_function, odf_args, sampling=100)
            half_multiplicities = multiplicities//2 # don't need to include friedel pairs (test for symmetries without implied inversion symmetry)
            for k in range(half_multiplicities[i_peak]):
                idx = half_multiplicities[:i_peak].sum() + k
                odf[i_chi, i_peak] += get_probability( 
                    reciprocal_points[idx].copy(), q_detector.copy(), 
                    odf_basis_function, odf_args, sampling=100)
        # # ### test good sampling
        # samplings = np.logspace(np.log(50),np.log(10000),num=50,base=np.exp(1)).astype(int)
        # probabilities = []
        # for s in samplings:
        #     probabilities.append(get_probability( # angular coordinate missing
        #         reciprocal_points[i_peak].copy(), q_detector.copy(), 
        #         odf_basis_function, odf_args, sampling=s ))
        # plt.semilogx( samplings, np.array(probabilities)/probabilities[-1] )
        # # 100 - 1% off
        # # 200 - 0.5% off
        # # 900 - 0.1% off
        
        # print(f'\n\tFinished peak Nr.{i_peak+1}/{n_peaks}')

    difflet = odf * structure_factors[np.newaxis,:]
    return difflet

@njit
def hsh_wrapper(orientations_q, n, l, m):
    """
    Vectorized version: orientations in OTP notation
    Returns a 1D complex128 array of results.
    """
    OTP = rot.OTPfromQ(orientations_q)
    N = orientations_q.shape[0]
    out = np.empty(N, dtype=np.complex128)
    for i in range(N):
        out[i] = hsh.Z_numba(OTP[i,0], OTP[i,1], OTP[i,2], n, l, m)
    return out

@njit(parallel=True)
def diffractlets_parallel_hsh( order, symmetrization_matrix, 
                                detector_coordinates, Q_sample_rotations,
                                reciprocal_points, multiplicities, structure_factors):
    
    n_difflets, n_hsh = symmetrization_matrix.shape

    lm = np.empty((n_hsh, 2), dtype=np.int64)
    idx = 0
    for l in range(order+1):
        for m in range(-l, l+1):
            lm[idx, 0] = l
            lm[idx, 1] = m
            idx += 1

    n_rotations = Q_sample_rotations.shape[0]
    Gs = rot.OTPfromQ(Q_sample_rotations)

    difflets_hsh = np.empty( (n_hsh, n_difflets, *detector_coordinates.shape[:2]), np.complex128 )
    for k in prange( n_hsh ):
        # calculate complex HSH diffractlet
        hsh_difflet = diffractlet( 
                detector_coordinates.astype(np.float64), 
                reciprocal_points.astype(np.float64), structure_factors.astype(np.float64), multiplicities,
                difflets_hsh.dtype,
                hsh_wrapper, (order,lm[k,0],lm[k,1]) )
        # symmetrize
        for i_shsh in range(n_difflets):
                difflets_hsh[k, i_shsh] = symmetrization_matrix[i_shsh, k] * hsh_difflet
    difflets = np.real( difflets_hsh.sum(axis=0) )

    difflets_rot = np.empty( (n_rotations, n_difflets, detector_coordinates.shape[0], detector_coordinates.shape[1]), 
                data_type )
    rotations_sHSH = hsh.Rs_n_stack( np.column_stack( (-Gs[:,0], Gs[:,1], Gs[:,2]) ).astype(np.float64),
                                    order, symmetrization_matrix )
    for g, Rs_g in enumerate(rotations_sHSH):
        # difflets_rot[g] = (Rs_g @ difflets.reshape((difflets.shape[0], difflets.shape[1]*difflets.shape[2]))).reshape(difflets.shape)
        difflets_rot[g] = rotate_HSH_difflets( Rs_g, difflets)

    return difflets_rot, difflets_hsh

@njit
def rotate_HSH_difflets(Rs_g, difflets):
    n, _ = Rs_g.shape
    _, m, l = difflets.shape
    C = np.zeros((n, m, l), Rs_g.dtype)
    for i in range(n):
        for j in range(m):
            s = np.zeros(l, Rs_g.dtype)
            for k in range(n):
                s += Rs_g[i, k] * difflets[k, j]
            C[i, j] = s
    return C

@njit(parallel=True)
def diffractlets_parallel_grid( resolution, Q_grid, Q_group, 
                                detector_coordinates, Q_sample_rotations,
                                reciprocal_points, multiplicities, structure_factors ):
    
    n_rotations = Q_sample_rotations.shape[0]
    n_difflets = Q_grid.shape[0]
    difflets = np.empty( (n_rotations, n_difflets, *detector_coordinates.shape[:2]), np.float64 )
    for g in prange(n_rotations):
        detector_coordinates_rot = np.empty_like(detector_coordinates)
        for c in range(detector_coordinates.shape[0]):
            for q in range(detector_coordinates.shape[1]):
                detector_coordinates_rot[c,q] = rot.quaternion_inverse_rotate_vector(
                                            Q_sample_rotations[g], detector_coordinates[c,q])
                
        for k in range( n_difflets ):
            difflets[g,k] = diffractlet( 
                    detector_coordinates_rot.astype(np.float64), 
                    reciprocal_points.astype(np.float64), structure_factors.astype(np.float64), multiplicities,            
                    difflets.dtype,
                    grd.gaussian_SO3, 
                    (Q_grid[k].astype(np.float64), resolution*np.pi/180 / 2, Q_group.astype(np.float64))                    
                    # grd.fisher_SO3, 
                    # (Q_grid[k].astype(np.float64), 10/(resolution*np.pi/180)**2, Q_group.astype(np.float64))    
                    )

    return np.real(difflets).astype(data_type)

def get_diffractlets( cr, chi_det, geo, Q_sample_rotations, hsh_max_order=4, grid_resolution=25, 
                     cutoff_structure_factor=1e-4, max_hkl=4, odf_mode='hsh' ):
    """aa

    Parameters
    ----------
    cr : _type_
        _description_
    chi_det : _type_
        _description_
    geo : _type_
        _description_
    sample_rotations : _type_
        _description_
    orders : list or int, optional
        HSH orders, by default 4
    resolution : int, optional
        _description_, by default 25
    cutoff_structure_factor : float, optional
        _description_, by default 1e-4
    mode : str, optional
        _description_, by default 'hsh'

    Returns
    -------
    _type_
        _description_
    """

    q_hkl, reciprocal_points_full, structure_factors, multiplicities, hkl, symmetry = structure_factor_from_cif( 
        cr.cifPath, q_max=cr.q_range[1], cutoff_structure_factor=cutoff_structure_factor, max_hkl=max_hkl )
    Qq_det, Chi_det, detShape = rot.qchi(q_hkl, chi_det)
    detector_coordinates = get_reciprocal_space_coordinates( Qq_det, Chi_det, cr.E_keV, geo )
    detector_coordinates = detector_coordinates.reshape((*detShape,3))
    # pg = getattr( orx.osym, sym.get_SFnotation( symmetry ) )
    powder_pattern = structure_factors * multiplicities

    print('\tRetrieved reciprocal space coordinates, calculating diffractlets')
    t0 = time()
    if odf_mode=='hsh':
        odf_obj = hsh.odf(hsh_max_order, symmetry, None)
        # ns = hsh.get_orders(symmetry, hsh_max_order, info=False)
        difflets_n = []
        for order in odf_obj.orders:
            if order==0:
                difflets = np.array(np.full( (Q_sample_rotations.shape[0],1,*detShape), 
                                np.atleast_2d( structure_factors*multiplicities) ), data_type)
            else:
                # symmetrization_matrix, _,_ = hsh.get_symmetrization_matrix( np.atleast_1d(ns), symmetry )
                difflets,_ = diffractlets_parallel_hsh( order, odf_obj.symmetrization_matrix[str(order)],
                            detector_coordinates, Q_sample_rotations,
                            reciprocal_points_full, multiplicities, structure_factors)
                # n_difflets = symmetrization_matrix[str(order)].shape[0]
                # difflets = np.zeros( (n_difflets, *detector_coordinates.shape[:2]), np.complex128 )
                # k = 0
                # for l in range(order):
                #     for m in range(-l,l+1):
                #         # calculate complex HSH diffractlet
                #         hsh_difflet = diffractlet( detector_coordinates, reciprocal_points, structure_factors, 
                #                     hsh.Z, (order,l,m) )
                #         # symmetrize
                #         for i_shsh in range(n_difflets):
                #                 difflets[i_shsh] += symmetrization_matrix[str(order)][i_shsh, k] * hsh_difflet
                #         k+=1
                #         # print(f'\tfinished n={order}, l={l}, m={m}')
            difflets_n.append(difflets)
            print(f'\t\tfinished order {order}')
        
        difflets_full = np.concatenate(difflets_n, axis=1)

    elif odf_mode=='grid':
        # Q_grid = rot.get_sample_fundamental(
        #                 resolution,
        #                 point_group= pg,
        #                 method='cubochoric'
        #         ).data.astype(data_type)
        
        # # Q_grid = rot.QfromOTP(np.array([[0,0,0], [np.pi/2,np.pi/2,np.pi/2]]))
        # # resolution = 10
        # [[738,47,697]] with resolution 10:
            # [1., 0., 0., 0.]
            # [ 0.7361178 , -0.6768535 ,  0.        ,  0.        ],
            # [ 0.7361178 ,  0.        , -0.6768535 ,  0.        ],

        # generators = sym.generators(symmetry)
        # q_gen = rot.QfromOTP(generators)
        # Q_group = rot.generate_group(q_gen)
        Q_grid, Q_group = grd.setup_gridbased(symmetry, grid_resolution)
        difflets_full = diffractlets_parallel_grid( grid_resolution, Q_grid[[738,47,697]] , 
                    Q_group, detector_coordinates, Q_sample_rotations,
                    reciprocal_points_full, multiplicities, structure_factors, )
        # print(Q_grid)

    else:
        print('\n\tMode not recognized, choose hsh or grid\n')
        sys.exit(1)
    
    # apply Lorentz correction
    theta = np.arcsin(wavelength_from_E_keV(cr.E_keV) * Qq_det / (4*np.pi))
    Lorentz = 1/np.sin(2*theta)
    difflets_full = difflets_full * Lorentz.reshape(detShape)[np.newaxis,np.newaxis,:,:]

    print(f'\t\ttook {(time()-t0)/60:.2f} min')
    return Qq_det.reshape(detShape), Chi_det.reshape(detShape), detector_coordinates, hkl, difflets_full, powder_pattern, symmetry, odf_obj

def plot_diffractlet( Qq_det, Chi_det, hkl, difflet, q_bins=50, cmap='bwr', logscale=False, sym_cmap=True ):

    f = plt.figure(figsize=(12,6))
    ax1 = f.add_subplot(121)
    ax2 = f.add_subplot(122, projection='polar')

    chi = Chi_det[:,0] 
    q_peaks = Qq_det[0]

    if isinstance(q_bins,np.ndarray):
        q_plot = q_bins
    else:
        q_plot = np.linspace(q_peaks[0],q_peaks[-1],num=q_bins)
    difflet_plot = np.zeros((difflet.shape[0], q_plot.size))
    for k in range(q_peaks.size):
        l = np.argmin(np.abs(q_plot-q_peaks[k]))
        difflet_plot[:,l] += difflet[:,k]
    Q_plot, Chi_plot = np.meshgrid(q_plot, chi)

    from matplotlib.colors import LogNorm, TwoSlopeNorm
    if logscale:
        difflet_log = difflet_plot - difflet_plot.min() + 1e-3
        ax1.pcolormesh(Q_plot, Chi_plot* 180/np.pi, difflet_log, cmap=cmap, norm=LogNorm())
        im=ax2.pcolormesh(Chi_plot, Q_plot, difflet_log, cmap=cmap, norm=LogNorm())
    elif sym_cmap:
        ax1.pcolormesh(Q_plot, Chi_plot* 180/np.pi, difflet_plot, cmap=cmap, norm=TwoSlopeNorm(vcenter=0))
        im=ax2.pcolormesh(Chi_plot, Q_plot, difflet_plot, cmap=cmap, norm=TwoSlopeNorm(vcenter=0))
    else:
        ax1.pcolormesh(Q_plot, Chi_plot* 180/np.pi, difflet_plot, cmap=cmap )
        im=ax2.pcolormesh(Chi_plot, Q_plot, difflet_plot, cmap=cmap )

    ax1.set_xlabel('q [nm^-1]')
    ax1.set_ylabel('chi [degree]')
    ax_top = ax1.twiny()
    ax_top.set_xlim(ax1.get_xlim())  # sync limits
    ax_top.set_xticks(q_peaks, labels=hkl)
    ax_top.tick_params(axis='x', labelrotation=45) 
    # ax1.set_xticks(q_peaks, labels=hkl )
    f.colorbar(im)
    f.tight_layout()

def plot_single_crystal_pattern(cr, cutoff_structure_factor=1e-4, axis=0):
    "very simple plot, axis (either 0,1,2) defines the beam direction with respect to the crystal structure"
    q_hkl, reciprocal_points_full, structure_factors, multiplicities, hkl, symmetry = structure_factor_from_cif( 
        cr.cifPath, q_max=cr.q_range[1], cutoff_structure_factor=cutoff_structure_factor )

    def other_axes(n:int):
        if n==0:
            return (1,2)
        elif n==1:
            return (2,0)
        elif n==2:
            return (0,1)
    det_axes = other_axes(axis)

    peaks = []
    for point in reciprocal_points_full:
        if np.abs(point[axis]) < 1e-2:
            peaks.append((point[det_axes[0]], point[det_axes[1]]))
    peaks = np.array(peaks)
    plt.scatter(peaks[:,0], peaks[:,1])

@njit
def get_odf_bin_indices(Q_sample, Q_bins, Q_group):
    """ bins quaternion in a predefined grid based on the maximum dot product with the bins
    """
    idcs = np.zeros(Q_sample.shape[0], dtype=np.int32)
    for s, q_s in enumerate(Q_sample):
        dots_bin = np.zeros(Q_bins.shape[0])
        for b, q_b in enumerate(Q_bins):
            dots_eq = np.zeros(Q_group.shape[0])
            for g, q_g in enumerate(Q_group):
                q_probed = rot.quaternion_multiply(q_g,q_s)
                q_probed *= q_probed[0] # invert quaternions with first 
                dot = rot.quaternion_dot(q_probed, q_b)
                # idcs_eq[g] = dot
                dots_eq[g] = dot
            dots_bin[b] = np.max(dots_eq)
        idcs[s] = np.argmax(dots_bin)
            
    return idcs
                 
def calculate_experimental_odf_coverage(cr, geo, 
                chi_det=np.linspace(0,2*np.pi,num=120), sample_rotations=[0,0,0], 
                cutoff_structure_factor=1e-4 ):

    q_hkl, reciprocal_points_full, structure_factors, multiplicities, hkl, symmetry = structure_factor_from_cif( 
        cr.cifPath, q_max=cr.q_range[1], cutoff_structure_factor=cutoff_structure_factor )
    
    # chosen_peaks = np.arange( multiplicities.size )
    chosen_peaks = [0,1] # check indices: hkl

    Qq_det, Chi_det, detShape = rot.qchi(q_hkl, chi_det)
    detector_coordinates = get_reciprocal_space_coordinates( Qq_det, Chi_det, cr.E_keV, geo )
    detector_coordinates = detector_coordinates.reshape((*detShape,3))

    q_gen = rot.QfromOTP(sym.generators(symmetry))
    Q_group = rot.generate_group(q_gen)

    Gc, dV, V_fz = rot.sample_fundamental_zone( dchi=5*np.pi/120 )
    Q_bins = rot.QfromOTP(Gc)
    odf_coverage = np.zeros(Gc.shape[0])
    for q in chosen_peaks:
        odf_coverage_q = np.zeros(Gc.shape[0])
        for q_d in detector_coordinates[:,q]:
            for q_p in reciprocal_points_full[multiplicities[:q].sum():multiplicities[:q+1].sum()]:

                ori_detected = get_orientations_seen_on_pixel(q_d, q_p, sampling=100)
                idcs = get_odf_bin_indices(ori_detected, Q_bins, Q_group)
                odf_coverage_q[np.unique(idcs)] += 1
        
        # not 100% sure about this but probably we should only count an orientation once per ring
        odf_coverage += odf_coverage_q.astype(bool)
        # maybe double-cover by equivalent points is ok but not by angle bins

            # plot a single q-point
            # orx.plot_points_in_fz( Q_bins[np.unique(idcs)], symmetry )
        # plot a full azimuthal coverage of a q-vector
        # orx.plot_points_in_fz( Q_bins[np.where(odf_coverage_q)[0]], symmetry ) 
        # plot double-covered bins
        # orx.plot_points_in_fz( Q_bins[np.where(odf_coverage_q > 1)[0]], symmetry ) 

    # plot a full azimuthal coverage of all qs
    # orx.plot_points_in_fz( Q_bins[np.where(odf_coverage)[0]], symmetry )
    # orx.plot_points_in_fz( Q_bins[np.where(odf_coverage > 1)[0]], symmetry )

    stop=1

@njit(parallel=True)
def inversion_matrix_parallel(chosen_peaks, chi_det, Q_samplerot, Q_bins,
                              detector_coordinates, reciprocal_points_full, multiplicities,
                              Q_group):
    n_data_proj = chosen_peaks.size * chi_det.size
    n_proj = Q_samplerot.shape[0]
    n_parameters = Q_bins.shape[0]
    A = np.zeros( (n_proj, n_data_proj, n_parameters), np.int8 )
    for r in prange(Q_samplerot.shape[0]):
        quat_rot = Q_samplerot[r]
        k = 0
        for q in chosen_peaks:
            for q_d in detector_coordinates[:,q]:
                q_d_rot = rot.quaternion_inverse_rotate_vector( quat_rot, q_d )
                for q_p in reciprocal_points_full[multiplicities[:q].sum():multiplicities[:q+1].sum()]:
                    ori_detected = get_orientations_seen_on_pixel(q_d_rot, q_p, sampling=100)
                    idcs = get_odf_bin_indices(ori_detected, Q_bins, Q_group)
                    A[r, k, np.unique(idcs)] += 1
                k+=1
    return A

def get_inversion_matrix( cr, geo, chosen_peaks, d_rot=10, tilts=[0,15,30,45], 
                               chi_resolution=6, cutoff_structure_factor=1e-4):

    # let's see for a single ODF
    q_hkl, reciprocal_points_full, structure_factors, multiplicities, hkl, symmetry = structure_factor_from_cif( 
        cr.cifPath, q_max=cr.q_range[1], cutoff_structure_factor=cutoff_structure_factor )

    # chosen_peaks = [0,1] # check indices: hkl

    Gc, dV, V_fz = rot.sample_fundamental_zone( dchi=chi_resolution*np.pi/180, 
                                        sampling='cubochoric', symmetry=symmetry )  
    Q_bins = rot.QfromOTP( Gc )  
    
    Omega, Kappa = rot.samplerotations_eq3D(d_rot, tilts)
    Q_ome = np.column_stack(
            (np.cos(Omega/2),np.outer(np.sin(Omega/2), np.array(geo.inner_axis))))
    Q_kap = np.column_stack(
            (np.cos(Kappa/2),np.outer(np.sin(Kappa/2), np.array(geo.outer_axis))))
    Q_samplerot = np.array([rot.quaternion_multiply(qk,qo) for qo,qk in zip(Q_ome,Q_kap)])
    Gs = rot.OTPfromQ(Q_samplerot)

    chi_det=np.linspace(0,2*np.pi,num=360//chi_resolution)
    Qq_det, Chi_det, detShape = rot.qchi(q_hkl, chi_det)
    detector_coordinates = get_reciprocal_space_coordinates( Qq_det, Chi_det, cr.E_keV, geo )
    detector_coordinates = detector_coordinates.reshape((*detShape,3))

    q_gen = rot.QfromOTP(sym.generators(symmetry))
    Q_group = rot.generate_group(q_gen)

    A = inversion_matrix_parallel(np.array(chosen_peaks), chi_det, Q_samplerot, Q_bins,
                              detector_coordinates, reciprocal_points_full, multiplicities//2,
                              Q_group)

    return np.concatenate(A)

    # n_data_points = len(chosen_peaks) * chi_det.size * Q_samplerot.shape[0]
    # n_parameters = Gc.shape[0]
    # A = np.zeros( (n_data_points, n_parameters), np.int8 )
    # k = 0
    # for quat_rot in Q_samplerot:
    #     for q in chosen_peaks:
    #         for q_d in detector_coordinates[:,q]:
    #             q_d_rot = rot.quaternion_inverse_rotate_vector( quat_rot, q_d )
    #             for q_p in reciprocal_points_full[multiplicities[:q].sum():multiplicities[:q+1].sum()]:
    #                 ori_detected = get_orientations_seen_on_pixel(q_d_rot, q_p, sampling=100)
    #                 idcs = get_odf_bin_indices(ori_detected, Q_bins, Q_group)
    #                 A[k, np.unique(idcs)] += 1

    #             k+=1

    # U, s, Vt = np.linalg.svd(A)

    # # Small singular values -> unstable directions
    # tol = 1e-12  # or relative threshold like s[0]*1e-6
    # unstable = np.where(s < tol)[0]

    # # Look at rows of Vt corresponding to unstable singular values
    # print("Unstable directions in coefficient space:")
    # print(Vt[unstable])
    
    # # The ratio (largest ÷? smallest) is the condition number. 
    # # If this number is huge, your inversion will be numerically unstable: 
    # # tiny changes or noise in d will blow up in the solution c
    # condition_number = np.max(s) / np.min(s)
    
    # The smallest singular value tells you how close A is to being rank-deficient (losing information). 
    # If a singular value is exactly zero, that means some directions in coefficient space can??t be 
    # recovered from d ?? the system is underdetermined.

