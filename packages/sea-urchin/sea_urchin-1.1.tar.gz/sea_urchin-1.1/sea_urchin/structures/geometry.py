#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 30 15:58:46 2023

@author: roncoroni
"""

import numpy as np

#%%


def distance_matrix_to_coords(v):
    """ Converts a (2D square) distance matrix representation of a structure to Cartesian coordinates (first 3 columns
    correspond to 3D xyz coordinates) via a Gram matrix.
    :param v: 1D vector, numpy array
    :return: 3D Cartesian coordinates, numpy array
    """

    d = vector_to_matrix(v)

    d_one = np.reshape(d[:, 0], (d.shape[0], 1))

    m = (-0.5) * (d - np.matmul(np.ones((d.shape[0], 1)), np.transpose(d_one)) - np.matmul(d_one,
                                                                                           np.ones((1, d.shape[0]))))

    values, vectors = np.linalg.eig(m)

    idx = values.argsort()[::-1]
    values = values[idx]
    vectors = vectors[:, idx]

    assert np.allclose(np.dot(m, vectors), values * vectors)

    coords = np.dot(vectors, np.diag(np.sqrt(values)))

    # Only taking first three columns as Cartesian (xyz) coordinates
    coords = np.asarray(coords[:, 0:3])

    return coords