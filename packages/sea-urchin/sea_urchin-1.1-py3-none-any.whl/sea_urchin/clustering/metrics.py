#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  8 09:53:43 2022

Set of functions to calculate metrics of SeaUrchin objects.


@author: electrolyte-machine
"""

# sea urchin stuff
import sea_urchin.alignement.align as ali
import sea_urchin.utilities.auxiliary_functions as aux
from sea_urchin.utilities.auxiliary_functions import as_list

# numpee
import numpy as np
import itertools

# parallel computation
from joblib import Parallel, delayed


#%%

# get flattened upper triangular distance matrix
def get_distances(clusters):
    indexes = np.triu_indices(len(clusters[0]), k=1)
    return np.array([cc.get_all_distances()[indexes] for cc in clusters])

# calculate euclidian distance bet clusters (positions)
def rmsd_calculator(cluster, reference, optimized=False):

    if optimized:
        cluster = cluster.copy()
        aux.minimize_rotation_and_translation(reference, cluster)

    pos1 = cluster.get_positions()
    pos2 = reference.get_positions()

    diff = pos1 - pos2

    return np.sqrt((diff * diff).sum() / pos1.shape[0])

#Obtain distance matrix for a list of same-composition clusters using fastoverlap
def get_all_distances_matrix(clusters, alignment):
    return ali.calculate_distance_matrix(clusters, alignment)

def get_simple_distance_matrix(clusters, parallel=True, optimized=False):

    # initialize distance matrix
    distances = np.zeros([len(clusters), len(clusters)])

    # get indices for computing distances
    indices = np.triu_indices_from(distances, k=1)

    if parallel:
        num_cores = aux.optimal_n_jobs(len(indices[0]), full=True)
        with Parallel(n_jobs=num_cores, backend="loky") as PAR:
            dists = PAR(delayed(rmsd_calculator)
                                    (clusters[i0], clusters[i1], optimized)
                                    for i0, i1 in zip(*indices))
    else:
        dists = []
        for i0, i1 in zip(*indices):
            dists.append(rmsd_calculator(clusters[i0], clusters[i1], optimized))

    distances[indices] = dists
    distances += distances.T

    return distances

def get_simple_distances(references, clusters, optimized=False):

    data = list(itertools.product(clusters, references))

    # align in parallel
    num_cores = aux.optimal_n_jobs(len(data), full=True)

    with Parallel(n_jobs=num_cores, backend="loky") as PAR:
        dists = PAR(delayed(rmsd_calculator)
                                (cluster, reference, optimized)
                                for cluster, reference in data)

    return np.reshape(dists, (len(clusters),len(references)))

def get_relevant_distances(clusters, idxs):
    
    distances = []
    for cluster in as_list(clusters):
        dm = cluster.get_all_distances()
        distances.append(dm[idxs[:,0], idxs[:,1]])
    
    return np.array(distances)