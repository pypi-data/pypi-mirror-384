#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  8 09:53:43 2022

Set of functions to perform alignment of SeaUrchin objects.


@author: electrolyte-machine
"""
#%%

# turn off warnings
import warnings
warnings.filterwarnings("ignore")

import sea_urchin.clustering.metrics as met

# sea urchin modules
try:
    import sea_urchin.alignement.ira_routines as ira
    is_ira = True
except:
    is_ira = False
try:
    import sea_urchin.alignement.fastoverlap_routines as fov
    is_fo = True
except:
    is_fo = False

# other random stuff (got the joke?)
import numpy as np
from colorama import Fore, Style
UP = '\033[1A'
CLEAR = '\x1b[2K'

#%%
# function to check that the alignment types have been properly implemented
def check_alignment_type(alignment):
    
    assert "type" in alignment, "Specify alignment type"
    
    if alignment["type"] == "fastoverlap":
        assert is_fo, "Fastoverlap is not implemented."
    if alignment["type"] == "ira":
        assert is_ira, "IRA is not implemented."
    return

# get rotation, permutation, translation and inversion
def get_RTPI(clusters, references, alignment):
    check_alignment_type(alignment)
    if alignment["type"] == "fastoverlap":
        rot, tr, perm, inv, de, __ = fov.get_RTPI(clusters, references, alignment)
        return rot, tr, perm, inv, de
    elif alignment["type"] == "ira":
        rot, tr, perm, inv, dh = ira.get_RTPI(clusters, references, alignment)
        return rot, tr, perm, inv, dh
    
def align_structure(structure, rot, tr, perm, inv, rtype):
    if rtype == "fastoverlap":
        return fov.rotate_structure(structure, rot, tr, perm, inv)
    elif rtype == "ira":
        return ira.rotate_structure(structure, rot, tr, perm, inv)

# help us pick
def RTPI_picker(clusters, references, cc, labels, rot, tr, perm, inv, dist):

    # Handle cases based on cluster and reference counts, using early returns for clarity:
    if len(clusters) == 1 and len(references) == 1:
        return rot, tr, perm, inv  # No need for indexing if only one cluster

    if len(references) == 1:
        return rot[cc], tr[cc], perm[cc], inv[cc]  # No need for further checks if only one reference

    # Determine the appropriate index for selection:
    cidx = labels[cc] if labels is not None else np.argmin(dist[cc])
    
    if len(clusters) == 1:
        return rot[cidx], tr[cidx], perm[cidx], inv[cidx]

    # Return the selected values:
    return rot[cc][cidx], tr[cc][cidx], perm[cc][cidx], inv[cc][cidx]

# align set of clusters to multiple references in parallel (works for all scenarios)
def align_clusters_to_references(clusters, references, alignment, labels=None):
    
    # make sure wwe are working with lists
    if not isinstance(clusters, list):
        clusters = [clusters]
    if not isinstance(references, list):
        references = [references]
        
    # first get rot perm dist tr and blah blah
    rot, tr, perm, inv, dist = get_RTPI(clusters, references, alignment)
    
    # now, apply correct transformation given smallest distance or labels
    new_clusters = []
    for cluidx, cluster in enumerate(clusters):
        
        R, T, P, I = RTPI_picker(clusters, references, cluidx, labels,
                                 rot, tr, perm, inv, dist)

        new_cluster = align_structure(cluster, R, T, P, I, alignment["type"])
        new_clusters.append(new_cluster)
    
    if len(new_clusters) == 1:
        return new_clusters[0]
    return new_clusters

# align a trajectory to its mean structure, iteratively
def align_to_mean_structure(structures, alignment, start_structure=None,
                            nmax=30, conv=1e-5):

    # start from mean structure
    if start_structure is None:
        mean_structure = structures[-1].copy()
        # mean_structure.set_positions(np.mean([cc.get_positions() for cc in structures], axis=0))
    else:
        mean_structure = start_structure.copy()
        
    # adapt convergence
    conv = conv*np.sum(met.get_distances([structures[0]]))

    mean_structures = [mean_structure]
    new_structures = [clu.copy() for clu in structures]

    for ii in range(nmax):
        
        # run alignment
        new_structures = align_clusters_to_references(new_structures,
                                                      mean_structures, alignment)
        
        # get new mean structure
        new_mean_structure = structures[0].copy()

        new_mean_structure.set_positions(
            np.mean([cc.get_positions() for cc in new_structures], axis=0))
        
        # calculate rmsd
        rmsd = met.rmsd_calculator(mean_structure, new_mean_structure)

        mean_structure = new_mean_structure.copy()
        mean_structures.append(mean_structure)

        if  rmsd < conv:

            print(UP, end=CLEAR)
            print("{:4}| ".format(ii) + Fore.GREEN +
                  "{:5.6e}".format(rmsd) + Style.RESET_ALL, end="\r")
            print("")

            break

        print(UP, end=CLEAR)
        print("{:4}| ".format(ii) + Fore.RED +
              "{:5.6e}".format(rmsd) + Style.RESET_ALL, end="\r")

    return new_structures, mean_structures

# use it to calculate distance matrix (dont' make it too big pls)
def calculate_distance_matrix(clusters, alignment):
    _, _, _, _, dm = get_RTPI(clusters, clusters, alignment)
    return dm

# perform a chain alignment using DM
def chain_alignment(structures, alignment, DM=None):
    
    # calculate distance matrices
    if DM is None:
        DM = calculate_distance_matrix(structures, alignment)
    else:
        DM = DM.copy()
        
    DM[np.diag_indices_from(DM)] = np.inf

    oidx = 0

    linkage = []
    for ii in range(len(DM)-1):
        
        nidx = np.argmin(DM[oidx])
        DM[nidx] += DM[oidx]

        linkage.append([oidx, nidx])
        oidx = nidx
        
    for link in linkage[::-1]:
        
        to_move_idx = link[0]
        target_idx  = link[1]
        
        new_structure = align_clusters_to_references([structures[to_move_idx]],
                                                    structures[target_idx],
                                                    alignment)
            
        structures[to_move_idx] = new_structure
    
    return structures

# align a sequence in timely fashion (eg each frame with previous one)
def sequence_align(structures, alignment):
    
    new_structures = []
    
    for cc, structure in enumerate(structures):
        if cc == 0:
            new_structures.append(structure.copy())
            continue
        new_structure = align_clusters_to_references(structure, new_structures[-1], alignment)
        new_structures.append(new_structure)
    
    return new_structures
