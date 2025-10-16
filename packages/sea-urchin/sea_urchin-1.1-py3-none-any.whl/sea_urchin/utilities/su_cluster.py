#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  8 09:53:43 2022

Set of auxiliary functions for the electrolyte machine.


@author: electrolyte-machine
"""

# ase stuff
import ase
from ase import neighborlist

# graph theory to make clusters more clustery
import networkx as nx

# numpy best package evah
import numpy as np

# sea urchin modules
import sea_urchin.utilities.auxiliary_functions as aux

#%%

# use networking algo to merge SeaUrchin coordination environments
def merge_clusters(cluster_idxs, tar_idxs=None):

    def to_edges(l):
        """
            treat `l` as a Graph and returns it's edges
            to_edges(['a','b','c','d']) -> [(a,b), (b,c),(c,d)]
        """
        it = iter(l)
        last = next(it)

        for current in it:
            yield last, current
            last = current

    clusters_graph = nx.Graph()

    if tar_idxs is not None:
        clusters_graph.add_nodes_from(tar_idxs)

    for idx in cluster_idxs:
        clusters_graph.add_edges_from(to_edges(idx))

    return [list(ii) for ii in nx.connected_components(clusters_graph)]

# reconstruct clusters according to system graph
def reconstruct_clusters(clusters_idxs, system_graph, urchin_data,
                      tar_idxs, reconstruct):

        # merge clusters into dimers, trimers und so weiter
        if reconstruct["inverse"]:

            # copy of system graph
            inv_system_graph = system_graph.copy()

            # remove cluster_indexes
            inv_system_graph.remove_nodes_from(urchin_data["ori_idx"][
                np.concatenate(clusters_idxs)])

            merged_clusters = []
            for indexes in nx.connected_components(inv_system_graph):

                ori_idxs = np.concatenate(np.argwhere(np.isin(
                    urchin_data["ori_idx"], list(indexes)))).tolist()

                merged_clusters.append(ori_idxs)

        elif reconstruct["merge"]:
            merged_clusters = merge_clusters(clusters_idxs, tar_idxs)

        else:
            merged_clusters = [ii.tolist() for ii in clusters_idxs]

        # fixes something ( I think if single cluster)
        if not all(isinstance(elem, list) for elem in merged_clusters):
            merged_clusters = [merged_clusters]

        return merged_clusters

def sort_cluster_indexes(cluster):

    if not bool(cluster.info):
        return np.argsort(cluster.get_atomic_numbers())
    
    if "mol_typ" not in cluster.info:
        return np.argsort(cluster.get_atomic_numbers())

    if cluster.info["mol_typ"] is None:
        return np.argsort(cluster.get_atomic_numbers())

    key = (
        cluster.info["ato_typ"],
        cluster.info["mol_idx"],
        [cluster.info["mol_idx"].count(ele)
          for cc, ele in enumerate(cluster.info["mol_idx"])],
        cluster.info["mol_typ"],
        cluster.get_atomic_numbers().tolist(),
        )
    return np.lexsort(key)

def generate_id_print(cluster):

    key = (
        cluster.info["ato_typ"],
        cluster.info["mol_idx"],
        [cluster.info["mol_idx"].count(ele)
          for cc, ele in enumerate(cluster.info["mol_idx"])],
        cluster.info["mol_typ"],
        cluster.get_atomic_numbers(),
        )

    key2 = np.array(key).T
    unique_keys = np.unique(key2, axis=0)
    mylist = []
    for kk in key2:
        indexes = [all(ii) for ii in kk == unique_keys]
        mylist.append(np.where(indexes)[0][0])

    return mylist

def generate_cutoffs(frame, cutoff_distances, target_indices):
    """
    Calculate cutoff distances between specified target indices in the given frame
    and all other atoms in the frame, including element-specific distances for pairs.

    Parameters:
    - frame: An object that contains the chemical structure with a method get_chemical_symbols().
    - cutoff_distances: A dictionary where keys can be element symbols or element pairs (tuples) 
                        and values are cutoff distances.
    - target_indices: A list of indices for which to calculate the cutoff distances relative 
                      to all other atoms.

    Returns:
    - A list of lists containing cutoff distances for each target index to all other atoms.
    """
    # Get the symbols array from the frame
    sym = np.array(frame.get_chemical_symbols())
    
    # Initialize a list to store cutoff distances for the target indices
    cutoff_values = []
    
    # Iterate through each target index
    for target_index in target_indices:
        # Get the symbol of the target atom
        target_element = sym[target_index]
        cutoff_row = []

        # Iterate through all atoms in the frame to calculate distances
        for i in range(len(sym)):
            if i == target_index:
                # If it's the same atom, you could assign a certain distance, or append 0
                cutoff_row.append(0.0)  # or some other value to represent self-interaction
                continue
            
            other_element = sym[i]

            # Check for direct cutoffs for the target element
            if other_element in cutoff_distances:
                cutoff_row.append(cutoff_distances[other_element])
            # Check pair-specific cutoffs
            elif (target_element, other_element) in cutoff_distances:
                cutoff_row.append(cutoff_distances[(target_element, other_element)])
            elif (other_element, target_element) in cutoff_distances:
                cutoff_row.append(cutoff_distances[(other_element, target_element)])  # Check symmetric cutoff
            else:
                cutoff_row.append(0.0)  # Default if no cutoff is defined

        cutoff_values.append(cutoff_row)

    return cutoff_values

# def generate_cutoff(frame, cutoff_distances):

#     if not isinstance(cutoff_distances, dict):
#         return cutoff_distances

#     # get symbols
#     sym = np.array(frame.get_chemical_symbols())

#     cds = np.zeros(len(frame))
#     for ele in cutoff_distances:
#         cds[np.where(sym == ele)[0]] = cutoff_distances[ele]

#     return cds


def find_neighbors(starting_indexes, urchin_data, system_graph,
                   reconstruct):

    rtypes = reconstruct["type"]

    # empty dict
    if rtypes is None:
        return []

    def connect(system_graph, rtype, idx, depth):

        if rtype is None:
            return []

        elif rtype == "molecules":
            mol_idxs = list(nx.node_connected_component(system_graph, idx))

        if rtype == "neighbors":
            subgraph = nx.ego_graph(system_graph, idx,
                                    radius=depth)
            mol_idxs = list(subgraph.nodes())

        return mol_idxs

    # iterate and find relevant neighbors
    new_neigh = []
    for cc, sidx in enumerate(urchin_data["ori_idx"][starting_indexes]):

        if sidx in new_neigh:
            continue

        # make dict of info of how to reconstruct:
        if isinstance(rtypes, dict):
            try:
                rtype = rtypes[urchin_data["ato_typ"][starting_indexes[cc]]]
            except:
                rtype = None
        else:
            rtype = rtypes

        mol_idxs = connect(system_graph, rtype, sidx, reconstruct["depth"])

        new_neigh.extend(mol_idxs)

    return np.argwhere(np.isin(urchin_data["ori_idx"], new_neigh)).ravel().tolist()



def translate_molecules(cluster, ref_idx):

    #Move cluster to origin (i.e. move target element to origin)
    origin = cluster.get_positions()[ref_idx[0]]
    origin += np.mean(
        cluster.get_distances(ref_idx[0], ref_idx,
                               vector=True, mic=True), axis=0)

    cluster.translate(-origin)

    closest_atoms = []
    closest_dists = []
    for ridx in ref_idx[1:]:

        distances = cluster.get_distances(ridx, range(len(cluster)), mic=True)
        distances[ridx] = np.inf

        cidx = np.argmin(distances)
        closest_atoms.append(cidx)

        closest_dists.append(cluster.get_distances(cidx, ridx,
                                                   vector=True, mic=True))


    # # add dummy atom at the end
    cluster.append(ase.Atom(position=[0,0,0]))

    # fix pbc of molecules
    if "mol_idx" in cluster.info and cluster.info["mol_idx"] is not None:

        # get indexes of molecules in the coordination environment
        mol_idxs = np.array(cluster.info["mol_idx"])

        # iterate over every molecule
        for mol_idx in set(cluster.info["mol_idx"]):

            # find indexes of atoms belonging to molecule
            atoms_idx = np.where(mol_idxs == mol_idx)[0]

            # make molecule object
            molecule = cluster[atoms_idx]

            # find COM of the molecule and add dummy atom at pos
            COM = molecule.get_positions()[0]
            COM += np.mean(
                molecule.get_distances(0, range(len(molecule)),
                                       vector=True, mic=True), axis=0)

            cluster.append(ase.Atom(position=COM))

            # vector from origin to COM
            COM_vec = cluster.get_distances(-2, -1, vector=True, mic=True)

            # find relative positions of atoms of one molecule wrt COM
            rel_pos = cluster.get_distances(-1, atoms_idx, vector=True, mic=False)

            # update their positions accordingly
            cluster.positions[atoms_idx] = COM_vec + rel_pos

            # remove the dummy atom
            del cluster[-1]

    else:
        # update positions centerd around origin
        new_pos = cluster.get_distances(-1, range(len(cluster)),
                                    vector=True, mic=True)
        cluster.set_positions(new_pos)

    for cc, ridx in enumerate(ref_idx[1:]):
        cluster.positions[ridx] = cluster.positions[closest_atoms[cc]] + closest_dists[cc]

    # remove dummy atom if any left
    del cluster[cluster.numbers == 0]

    return cluster


def assign_metadata(cluster, urchin_data, cluster_idx, colvars_data,
                    timestamp, counter, coord_env, ref_atom):

    #make a new cluster object with the appropriate metadata
    cluster_metadata = {}
    for element in urchin_data:

        if element != "mol_nam" and urchin_data[element] is not None:
            cluster_metadata[element]  = urchin_data[
                element][cluster_idx].tolist()
        else:
            cluster_metadata[element] = urchin_data[element]


    cluster_metadata["colvars_data"] = colvars_data.iloc[counter].to_dict()


    cluster_metadata["replica_id"]      = cluster_metadata[
                                            "colvars_data"]["replica_id"]
    cluster_metadata["timestamp"]       = timestamp
    cluster_metadata["frame_number"]    = counter
    cluster_metadata["coord_env"]       = coord_env
    cluster_metadata["ref_atom"]        = ref_atom

    # assign info
    cluster.info.update(cluster_metadata)

    return

# build sequence with atomic identities according to the bonding of the atoms
def build_sequence(molecule, ignore_atoms=""):

    # generate cutoff
    cutOff = np.array(neighborlist.natural_cutoffs(molecule))
    cutOff[aux.atoms_to_indexes(molecule, ignore_atoms)] = 0

    # calculate neighbor list
    neighborList = neighborlist.NeighborList(cutOff,
                                             self_interaction=False,
                                             bothways=True)
    neighborList.update(molecule)

    # get chem symbols
    symbols = molecule.get_chemical_symbols()

    # generate graph
    G = nx.Graph()
    G.add_nodes_from(list(range(len(molecule))))
    G.add_edges_from([[ii, jj] for ii, bonds in
                        enumerate(neighborList.nl.neighbors) for jj in bonds])

    sequence = []
    for atoidx in range(len(molecule)):

        dfs_tree = np.array(nx.dfs_tree(G, atoidx))[1:]

        split_idxs = np.where(
            np.sum([dfs_tree == ii for ii in G.neighbors(atoidx)], axis=0))[0]

        branches = np.split(dfs_tree, split_idxs)

        bond_lists = []
        for branch in branches:

            if not len(branch):
                continue

            chem_seq = "".join([symbols[xx] for xx in branch])

            bond_lists.append(chem_seq)

        bond_lists.sort(key = len)
        sequence.append([symbols[atoidx]] + bond_lists)

    return sequence