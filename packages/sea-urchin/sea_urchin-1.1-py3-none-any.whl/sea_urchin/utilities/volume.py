#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 14 16:24:17 2025

@author: roncofaber
"""

from ase.data import vdw_radii

# method to estimate the volume of the specie
def estimate_cluster_volume_libarvo(cluster, probe_rad=0, radii=None):
    
    try:
        from libarvo import molecular_vs as volcalc

    except:
        raise ImportError("libarvo NOT found. Install it.")

    centers = cluster.get_positions()
    
    if radii is None:
        ato_radii = [vdw_radii[ii] for ii in cluster.get_atomic_numbers()]
    else:
        ato_radii = [radii[ii] for ii in cluster.get_chemical_symbols()]

    volume, surface = volcalc(centers, ato_radii, probe_rad)

    return volume

def estimate_cluster_volume_volmol(cluster, probe_rad=0.0, vorlength=0.2):
    
    try:
        import volume
    except:
        raise ImportError("libarvo NOT found. Install it.")
    
    clu_pos  = cluster.get_positions()
    clu_rad  = vdw_radii[cluster.get_atomic_numbers()]
    
    return volume.volume(clu_pos, clu_rad, probe_rad, vorlength)