
import numpy as np


def unpad3(a):
    '''
    Remove all-zero trailing slices along last axis of a 3D array
    '''
    i = -1
    while True:
        if np.any( a[:,:,i] != 0 ):
           break
        i -= 1
    return a[:,:,:i]