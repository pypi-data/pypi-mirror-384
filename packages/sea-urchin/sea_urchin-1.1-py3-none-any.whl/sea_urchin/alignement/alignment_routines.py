#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 11:57:24 2023

List of alignment routines implemented in the alignment algorithms.

@author: electrolyte-machine
"""
#%%

# turn off warnings
import warnings
warnings.filterwarnings("ignore")

# try to load alignment routines
try:
    try:
        from fastoverlap import SphericalAlignFortran as SphericalAlign
        from fastoverlap import SphericalHarmonicAlignFortran
        fo_fortran = True
    except:
        from fastoverlap import SphericalAlign
        fo_fortran = False
    is_fo = True
except:
    is_fo = False

try:
    from fastoverlap import BranchnBoundAlignment
    is_bnb = True
except:
    is_bnb = False

try:
    from molalignlib import assign_atoms
    is_molalign = True
except:
    is_molalign = False


#%%

def run_fastoverlap(reference, cluster, scale, maxl, invert, permlist):

    aligner  = SphericalAlign(scale=scale, Jmax=maxl, perm=permlist)

    # get positions of clusters
    pos1 = reference.get_positions()
    pos2 = cluster.get_positions()

    #Fastoverlap returns: distance, aligned cluster 1 and aligned cluster 2
    fastdist = aligner(pos1, pos2, invert=invert, perm=permlist)

    if fo_fortran:
        return fastdist
    else:
        return *fastdist, None, None
    
def run_fastoverlap_harm(reference, cluster, scale, maxl, invert, permlist):

    aligner  = SphericalHarmonicAlignFortran(scale=scale, Jmax=maxl, perm=permlist)

    # get positions of clusters
    pos1 = reference.get_positions()
    pos2 = cluster.get_positions()

    #Fastoverlap returns: distance, aligned cluster 1 and aligned cluster 2
    fastdist = aligner.malign(pos1, pos2, invert=invert, perm=permlist)

    if fo_fortran:
        return fastdist
    else:
        return *fastdist, None, None

def run_bnb(reference, cluster, permlist, invert, niter):

    aligner  =  BranchnBoundAlignment(perm=permlist, invert=invert)

    pos1 = reference.get_positions()
    pos2 = cluster.get_positions()

    #Fastoverlap returns: distance, aligned cluster 1 and aligned cluster 2
    fastdist = aligner(pos1, pos2, perm=permlist,
                       invert=invert, niter=niter)

    return fastdist

def run_molalign(reference, cluster, biasing, iteration, massweighted,
                 bonding, tolerance):

    assignment = assign_atoms(reference, cluster,
                              biasing      = biasing,
                              iteration    = iteration,
                              massweighted = massweighted,
                              bonding      = bonding,
                              tolerance    = tolerance)

    new_cluster = cluster[assignment[0].order]

    rmsd = new_cluster.align_to(reference)

    return rmsd, None, new_cluster.get_positions()