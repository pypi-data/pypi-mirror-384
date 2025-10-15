'''
make another option for if you know we have fibre textures (maybe also make platelet)
the problem reduces to 2D -> SH

sth like this:
def get_odf( Q, v, odf_2D ):

    odf = np.zeros_like(Q[:,0])
    for q in range(odf):
        z_vector = rot.quaternion_rotate_vector(Q(q), np.array([0,0,1]))
        dot = np.dot(z_vector, v) # maybe sparsify, maybe gaussian like Mads
        odf[q] = np.sum( dot * odf_2D )

'''