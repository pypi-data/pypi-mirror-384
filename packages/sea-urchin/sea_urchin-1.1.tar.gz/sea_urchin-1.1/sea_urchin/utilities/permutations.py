#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  8 09:53:43 2022

Set of auxiliary functions for the electrolyte machine. PERMUTATIONS AMIRITE.


@author: electrolyte-machine
"""

import collections
import itertools
import numpy as np

#%%

def get_type(cluster, permute):
    # generate allowed permutations
    if   permute == "elements":
        count = cluster.get_atomic_numbers()
    elif permute == "mol_typ":
        count = cluster.info["mol_typ"]
    elif permute == "none":
        count = list(range(len(cluster)))
    elif permute == "id_print":
        count = cluster.info["id_print"]
    elif permute == "ato_typ":
        count = cluster.info["ato_typ"]
    elif isinstance(permute, list):
        count = permute#[np.array(pp) for pp in permute]
    elif permute == "all":
        count = [0]*len(cluster)
    else:
        raise "WRONG permutation type raised"
    return np.array(count)

# given a cluster generate a list of allowed permutations that do not change
# the chemistry of the material
def get_permutation_list(cluster, permute):

    count = get_type(cluster, permute)

    permlist = []
    for element in set(count):
        permlist.append(np.where(count == element)[0])

    return permlist
