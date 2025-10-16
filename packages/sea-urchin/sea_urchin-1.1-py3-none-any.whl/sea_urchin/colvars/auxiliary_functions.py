#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 13 10:35:08 2023

@author: roncoroni
"""

from itertools import zip_longest
import numpy as np

#%% AUXILIARY FUNCTIONS

# trnasform integer in list with single element
def as_list(x):
    if type(x) is int or type(x) is float:
        return [x]
    else:
        return x

# from list of float/int, make formatted string
def list2string(lst, fmt="sci"):
    string = ""
    for item in as_list(lst):
        if fmt == "sci":
            string += " {:.14e}".format(item)
        elif fmt == "int":
            string += " {}".format(item)
    string += "\n"
    return string

# group a list as units of n, remove all other elements
def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n

    tuples = zip_longest(*args, fillvalue=fillvalue)

    argument_list = []

    for line in tuples:
        carg = []
        for element in line:
            if element is not None:
                carg.append(element)
        argument_list.append(carg)

    return argument_list

# finds nearest grid point to a value and return its index and value
def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx, array[idx]

def slice_ndarray(arr, axis1, axis2, indexes=None):

    arr_slice = []
    counter = 0
    for cc in range(arr.ndim):
        if cc in [axis1, axis2]:
            arr_slice.append(slice(None))
        else:
            if indexes is not None:
                arr_slice.append(indexes[counter])
            else:
                index = int(arr.shape[cc]/2)
                arr_slice.append(index)
            counter += 1

    return arr[tuple(arr_slice)]