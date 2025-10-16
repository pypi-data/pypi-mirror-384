#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  8 09:53:43 2022

Set of auxiliary functions for the electrolyte machine.


@author: electrolyte-machine
"""

import psutil
import re

# graph theory to make clusters more clustery
import networkx
from networkx.algorithms.components.connected import connected_components

# numpy best package evah
import numpy as np

# ase stuff
import ase
from ase.build.rotate import rotation_matrix_from_points

import collections

#%% Auxiliary functions

# return copy of input as list if not one
def as_list(inp):
    return [inp] if not isinstance(inp, list) else inp.copy()

# return list of indexes from mixed input of indexes and string (elements)
def atoms_to_indexes(system, symbols):

    # check if symbols is a list of strings
    if symbols == "all":
        return list(range(len(system.get_chemical_symbols())))

    symbols = as_list(symbols)

    indexes = []
    for symbol in symbols:
        if not isinstance(symbol, str):
            indexes.append(symbol)
        else:
            for cc, atom in enumerate(system.get_chemical_symbols()):
                if atom == symbol:
                    indexes.append(cc)
    return np.unique(indexes).tolist()



# check file type of input
def check_file_type(filein):

    file_types = {
        ".lammps"    : "lammps",
        ".lammpstrj" : "lammps",
        ".lammpstraj": "lammps",
        ".traj"      : "ase",
        ".xyz"       : "ase",
        ".pkl"       : "pickle",
        }

    assert(isinstance(filein, str)), "Input file must be a string!"

    for file_type in file_types:
        if filein.endswith(file_type):
            return file_types[file_type]

    raise NameError("Wrong input file specified, check again!")

# given a length of jobs returns the best parallelization option to maximize
# the speed
def optimal_n_jobs(njobs, full=False, parallel=True):

    if not parallel:
        return 1

    cpu_count = psutil.cpu_count(logical = False)

    if full:
        return cpu_count

    nbatches = np.ceil(njobs/cpu_count)

    return int(np.ceil(njobs/nbatches))


# finds nearest grid point to a value and return its index and value
def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx, array[idx]

# find closest node to a point
def closest_node(node, nodes):
    nodes = np.asarray(nodes)
    dist_2 = np.sum((nodes - node)**2, axis=1)
    return np.argmin(dist_2)

def minimize_rotation_and_translation(target, atoms,
                                      center=None, indexes=None):

    """Minimize RMSD between atoms and target.

    Rotate and translate atoms to best match target.  For more details, see::

        Melander et al. J. Chem. Theory Comput., 2015, 11,1055
    """

    full_pos = atoms.get_positions()

    if indexes is None:
        p  = atoms.get_positions()
        p0 = target.get_positions()
    else:
        p  = atoms[indexes].get_positions()
        p0 = target[indexes].get_positions()

    if center is None:
        mp  = atoms.get_positions()
        mp0 = target.get_positions()
    else:
        center = as_list(center)
        mp  = atoms[center].get_positions()
        mp0 = target[center].get_positions()


    # centeroids to origin
    c = np.mean(mp, axis=0)
    p -= c

    c0 = np.mean(mp0, axis=0)
    p0 -= c0

    # Compute rotation matrix
    R = rotation_matrix_from_points(p.T, p0.T)

    atoms.set_positions(np.dot(full_pos-c, R.T) + c0)
    return

# link structures from closest to the one further away
def make_linkage(dist_mat0, to_move=0, hard_link=True):

    dist_mat = dist_mat0.copy()
    dist_mat[np.diag_indices_from(dist_mat)] = np.inf

    linkage = []
    idx     = to_move
    sequence = [to_move]
    while len(linkage) < len(dist_mat)-1:

        if not hard_link:
            # get probability of linking
            p0 = np.exp(-dist_mat[idx])
            p = p0/np.sum(p0)
            target = np.random.choice(len(dist_mat), p=p)

        else:
            target = np.argmin(dist_mat[idx])

        linkage.append([idx, target])
        sequence.append(target)
        dist_mat[:, idx] = np.inf
        idx              = target

    return linkage, sequence

def generate_chemical_string(cluster):

    def sub_numbers(s):
        return re.sub(r'(\d+)', r'$_{\1}$', s)


    molecules = []
    for molidx in set(cluster.info["mol_idx"]):
        mol = cluster[np.array(cluster.info["mol_idx"]) == molidx]
        molecules.append(mol.get_chemical_formula())

    mol_count = collections.Counter(molecules)

    string = r""
    for mol in mol_count:

        molecule = ase.Atoms(mol)

        if mol_count[mol] == 1 and len(molecule) == 1:
            string = mol + string
        elif len(molecule) == 1:
            string = "{}{}".format(mol, mol_count[mol]) + string
        elif mol_count[mol] == 1:
            string += "[{}]".format(mol)
        else:
            string += "[{}]{}".format(mol, mol_count[mol])

    return sub_numbers(string)


def vector_to_matrix(v):
    """ Converts a representation from 1D vector to 2D square matrix. Slightly altered from rmsd package to disregard
    zeroes along diagonal of matrix.
    :param v: 1D input representation.
    :type v: numpy array
    :return: Square matrix representation.
    :rtype: numpy array
    """
    if not (np.sqrt(8 * v.shape[0] + 1) == int(np.sqrt(8 * v.shape[0] + 1))):
        print("ERROR: Can not make a square matrix.")
        exit(1)

    n = v.shape[0]
    w = ((-1 + int(np.sqrt(8 * n + 1))) // 2) + 1
    m = np.zeros((w, w))

    index = 0
    for i in range(w):
        for j in range(w):
            if i > j - 1:
                continue

            m[i, j] = v[index]
            m[j, i] = m[i, j]

            index += 1
    return m

def rearrange_labels(labels, energies):
    
    E2f_av = []
    for llab in set(labels):
        
        idxs = np.where(labels == llab)[0]

        if llab != -1:
            E2f_av.append(np.mean(energies[idxs]))

    # reorder labels according to their averaspge energy
    new_labels = labels.copy()
    lab_set    = np.unique(labels[labels != -1])
    for cc, idx in enumerate(np.argsort(E2f_av)):
        
        lab = lab_set[idx]
        
        new_labels[labels == lab] = cc
    
    return new_labels
