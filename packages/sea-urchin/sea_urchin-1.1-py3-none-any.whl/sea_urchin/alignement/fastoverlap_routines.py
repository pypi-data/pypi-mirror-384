#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 13 10:22:37 2024

@author: roncofaber
"""
# numpy the numpy package to do numpy stuff
import numpy as np
import itertools

# turn off warnings
import warnings
warnings.filterwarnings("ignore")

# parallel computation
from joblib import Parallel, delayed

# fastoverlap
from fastoverlap import SphericalAlignFortran as SphericalAlign

# sea urchin modules
import sea_urchin.utilities.permutations        as per
import sea_urchin.utilities.auxiliary_functions as aux

# other random stuff (got the joke?)
import copy
from   typing import Any, Dict

#%%
# define default parameters for alignment
default_parameters: Dict[str, Any] = {
    "alignment" : {
        "permute"   : "elements",
        "inversion" : True,
        #FASTOVERLAP
        "fo_scale"  : 0.8,
        "fo_maxl"   : 10,
        },

    }

#%%

# wrapper to run fastoverlap. pos1 is the reference and is the translation
# since the transformation is defined as wrt the origin
def run_fastoverlap(pos1, pos2, permlist, invert, scale, maxl):

    aligner  = SphericalAlign(scale=scale, Jmax=maxl, perm=permlist)

    #Fastoverlap returns: distance, aligned cluster 1 and aligned cluster 2
    fastdist = aligner(pos1, pos2, invert=invert, perm=permlist)
    
    return *fastdist, pos1.mean(axis=0)

# dummy function to set new pos to cluster (allow parallel loop)
def set_new_pos(cluster, pos):

    # return cluster
    new_cluster = cluster.copy()
    new_cluster.set_positions(pos)

    return new_cluster

# rotate, translate, permute, inverse a structure
def rotate_structure(structure, rot, tr, perm, inv):
    
    new_structure = structure.copy()
    
    # get COM (not mass)
    O = np.mean(structure.get_positions(), axis=0)
    
    npos = inv*(structure.get_positions() - O).dot(rot.T)
    
    new_structure.set_positions(npos + tr, apply_constraint=False)
    
    return new_structure[perm]

# main function to calculate the rotation, translation, permutation and inversion
def get_RTPI(clusters, references, alignment):
    
    # make sure wwe are working with lists
    if not isinstance(clusters, list):
        clusters = [clusters]
    if not isinstance(references, list):
        references = [references]
    
    # update alignment parameters from default dict
    alipar = copy.deepcopy(default_parameters["alignment"])
    alipar.update(alignment)
    
    # generate info for alignment
    permlist = per.get_permutation_list(clusters[0], alipar["permute"])
    invert   = alipar["inversion"]
    scale    = alipar["fo_scale"]  # Set this to be ~ half interatomic separation
    maxl     = alipar["fo_maxl"]   # Max degree of spherical harmonic
    
    # get all coords
    coords1_list = [reference.get_positions() for reference in references]
    coords2_list = [cluster.get_positions() for cluster in clusters]
    
    # generate data combination
    data = itertools.product(coords2_list, coords1_list)
    
    # get nclusters, natoms, nreps, ...
    nclu = len(clusters)
    nrep = len(references)
    natm = len(clusters[0])
    
    # select number of cores
    num_cores = aux.optimal_n_jobs(nclu*nrep, full=True)
    
    # run loop on all data
    with Parallel(n_jobs=num_cores, backend="loky") as PAR:
        de, __, npos, rot, perm, inv, tr = zip(*PAR(delayed(run_fastoverlap)
                                (coords1, coords2, permlist, invert, scale, maxl)
                                for coords2, coords1 in data))
        
    # reshape to match initial conf
    rot  = np.reshape(rot,  (nclu, nrep, 3, 3))
    tr   = np.reshape(tr,   (nclu, nrep, 3))
    perm = np.reshape(perm, (nclu, nrep, len(clusters[0])))
    de   = np.reshape(de,   (nclu, nrep))
    inv  = np.reshape(inv,  (nclu, nrep))
    npos = np.reshape(npos, (nclu, nrep, natm, 3))
    
    return np.squeeze(rot), np.squeeze(tr), np.squeeze(perm), np.squeeze(inv),\
        np.squeeze(de), np.squeeze(npos)
