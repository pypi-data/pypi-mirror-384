#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Set of routines to work with IRA

Created on Tue Feb 13 10:18:40 2024

@author: roncofaber
"""

# IRA stuff
import ira_mod

# SeaUrchin packages
import sea_urchin.utilities.auxiliary_functions as aux
import sea_urchin.utilities.permutations        as per

# parallel computation
from joblib import Parallel, delayed

# various
import copy
import numpy as np
import itertools
from   typing import Any, Dict

#%%
# define default parameters for alignment
default_parameters: Dict[str, Any] = {
    "alignment" : {
        "permute"   : "elements",
        #IRA
        "ira_kmax"  : 5.5,
        },

    }

#%%

ira = ira_mod.IRA()

# basic wrapper to run IRA in parallel
def run_IRA(nat1, typ1, coords1, nat2, typ2, coords2, kmax):
    
    rot, tr, perm, dh = ira.match(nat1, typ1, coords1, nat2, typ2, coords2, kmax)
    
    inv = np.round(np.linalg.det(rot))
    
    return inv*rot, tr, perm, dh, inv

# rotate, translate, permute, inverse a structure
def rotate_structure(structure, rot, tr, perm, inv):
    
    new_structure = structure.copy()
    
    npos = (structure.get_positions()@(inv*rot.T) + tr)

    new_structure.set_positions(npos)
    
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
    
    # extract alignment parameters
    kmax    = alipar["ira_kmax"]
    permute = alipar["permute"] 

    # generate permutation list
    permlist = per.get_type(clusters[0], permute)
    
    # get all coords
    coords1_list = [reference.get_positions() for reference in references]
    coords2_list = [cluster.get_positions() for cluster in clusters]
    
    # get nclusters, natoms, nreps, ...
    nclu = len(clusters)
    nrep = len(references)
    nat1 = len(references[0])
    nat2 = len(clusters[0])
    
    # generate data combination
    data = itertools.product(coords2_list, coords1_list)
    
    # select number of cores
    num_cores = aux.optimal_n_jobs(nclu*nrep, full=True)
    
    # run loop on all data
    with Parallel(n_jobs=num_cores, backend="loky") as PAR:
        rot, tr, perm, dh, inv = zip(*PAR(delayed(run_IRA)
                                (nat1, permlist, coords1, nat2, permlist, coords2, kmax)
                                for coords2, coords1 in data))
        
    # reshape to match initial conf
    rot  = np.reshape(rot,  (nclu, nrep, 3, 3))
    tr   = np.reshape(tr,   (nclu, nrep, 3))
    perm = np.reshape(perm, (nclu, nrep, nat2))
    dh   = np.reshape(dh,   (nclu, nrep))
    inv  = np.reshape(inv,  (nclu, nrep))
    
    return np.squeeze(rot), np.squeeze(tr), np.squeeze(perm), np.squeeze(inv),\
        np.squeeze(dh)
