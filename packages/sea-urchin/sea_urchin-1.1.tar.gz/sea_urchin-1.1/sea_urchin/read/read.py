#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  7 15:53:14 2022

@author: roncoroni
"""
#%% Import relevant modules
import mdtraj # --> cite if we use, but I would write a custom function to load the traj
import os

# ase stuff
import ase
import ase.io
import ase.io.lammpsdata
import ase.build
import ase.visualize

# numpy my best friend
import numpy as np

# can't work with dataframes without good ol' pandas
import pandas as pd

# su
from sea_urchin.utilities.su_cluster import merge_clusters
from sea_urchin.utilities.logger import get_logger

#%% auxiliary read functions

def label_to_element(atostr, atomss):

    new_label = ''.join(ii for ii in atostr if ii.isalpha()).capitalize()

    #TODO make this cleaner
    is_ready = False
    tried_last_resort = False
    while not is_ready:

        try:
            try_atom = ase.Atom(new_label)
            existent = True
        except:
            existent = False

        if existent and np.abs(try_atom.mass - atomss) < 1:
                is_ready = True

        # not ready, reduce string
        if not is_ready:
            new_label = new_label[:-1]

            # empty string
            if not new_label:

                elements      = ase.data.chemical_symbols
                atomic_masses = ase.data.atomic_masses

                new_label = elements[np.argmin(np.abs(atomss-atomic_masses))]

                if tried_last_resort:
                    raise ValueError(
                        "{} is not a valid element".format(new_label))

                tried_last_resort = True

    return new_label


#%% MAIN read functions

# main read function -- calls the other ones depending on file extension
def read_topology_file(filein):

    logger = get_logger()
    logger.debug("Parsing topology file: {} (type: {})".format(
        os.path.basename(filein),
        filein.split('.')[-1] if '.' in filein else 'unknown'))

    # read atom symbols
    if filein.endswith(".bgf"):
        std_data = read_bgf_file(filein)
    elif filein.endswith(".lammps"):
        std_data = read_data_file(filein)
    elif filein.endswith(".std"):
        std_data = read_std_file(filein)
    else:
        try:
            std_data = read_data_file(filein)
        except:
            raise RuntimeError(
                "{} is not a recognized data file.\
                    Allowed: .bgf, .lammps, .std".format(filein))

    return std_data

# bgf file reader
def read_bgf_file(bgf_file):

    # read bgf file and get info about atomic species
    with open(bgf_file) as fin:
        atoms   = []
        id_list = []
        for line in fin:
            if line.startswith('HETATM'):

                # get name ID of element
                atonr  = int(line.strip().split()[1])
                atostr = line.strip().split()[2]

                if atonr not in id_list:
                    atoms.append(''.join(ii for ii in atostr if not ii.isdigit()))

                    # use id_list to make sure that that atom is not present
                    # at all in the file (if error in making bgf occurs and
                    # some atoms are duplicate)
                    id_list.append(atonr)

    return np.array([ii.capitalize() for ii in atoms])

# SeaUrchin Topological Data -- custom data structure a bit legacy use with caution
def read_std_file(std_file):

    # read bgf file and get info about atomic species
    with open(std_file) as fin:
        ato_sym = []
        mol_idx  = []
        ato_typ    = []

        id_list = []
        for line in fin:

            cline = line.strip().split()

            # get name ID of element
            atonr  = int(cline[0])
            atostr = cline[1]
            molnr  = int(cline[2])
            atotp  = cline[3]

            # prevent to add duplicate atoms
            if atonr in id_list:
                continue

            ato_sym.append(
                ''.join(ii for ii in atostr if not ii.isdigit()).capitalize()
                )
            mol_idx.append(molnr)
            ato_typ.append(atotp)

            # use id_list to make sure that that atom is not present
            # at all in the file (if error in making bgf occurs and
            # some atoms are duplicate)
            id_list.append(atonr)

    mol_idx = np.array(mol_idx)

    frame = ase.Atoms(ato_sym)

    # molecules = []
    mol_names = []
    mol_typ = np.array(len(mol_idx)*[-1])
    for  mol_id in set(mol_idx):

        indexes = np.where(mol_idx == mol_id)[0]
        cmol = frame[indexes]

        chem_formula = cmol.get_chemical_formula()

        if chem_formula not in mol_names:
            mol_names.append(chem_formula)

        idnr = np.where([chem_formula == mol_type for mol_type in mol_names])[0]
        mol_typ[indexes] = idnr

    return np.array(ato_sym), np.array(mol_idx),\
        np.array(mol_typ), mol_names, np.array(ato_typ)

# use a data.lammps file, BEST for lammps trajectories!
def read_data_file(dta_file, type2sym=False):

    logger = get_logger()
    logger.debug("Reading LAMMPS data file: {}".format(os.path.basename(dta_file)))

    def nonblank_lines(f):
        for l in f:
            line = l.rstrip()
            if line:
                yield line

    with open(dta_file) as fin:

        read_types = False
        read_atoms = False
        read_bonds = False
        labels = []
        atoms  = []
        bonds  = []
        for line in nonblank_lines(fin):
            if line.endswith("atoms"):
                n_atoms = int(line.strip().split()[0])

            if line.endswith("atom types"):
                n_types = int(line.strip().split()[0])

            if line.startswith("Masses"):
                read_types = True
                continue

            if line.startswith("Atoms"):
                read_atoms = True
                continue

            if line.startswith("Bonds"):
                read_bonds = True
                continue

            if line.startswith("Angles"):
                break

            if read_types:
                atostr = line.strip().split()[-1]
                atomss = float(line.strip().split()[1])

                labels.append(label_to_element(atostr, atomss))

                if len(labels) >= n_types:
                    read_types = False

            if read_atoms:
                atoms.append(int(line.strip().split()[2]))

                if len(atoms) >= n_atoms:
                    read_atoms = False

            if read_bonds:
                cline = line.split()
                bonds.append([int(cline[ii])-1 for ii in [2,3]])
                
    if not atoms:
        raise RuntimeError("No atoms found in file -- check again!")

    # make list of atomic symbols
    symbols = np.array([labels[ii-1] for ii in atoms])

    # use bonding info to calculate connectivity
    connectivity = [[] for _ in range(len(atoms))]
    for bond in bonds:
        for atom in bond:
            connectivity[atom].extend([ii for ii in bond if ii != atom])

    # remove duplicate entries
    connectivity = [list(set(ii)) for ii in connectivity]

    # generate atomic types depending on their environment (bonded to same elements)
    connected_elements = ["".join(sorted([symbols[ii] for ii in con]))
                          for con in connectivity]

    atom_types = np.unique(connected_elements)
    ato_typ = []
    for atom_type in connected_elements:
        ato_typ.append(np.where(atom_type == atom_types)[0][0])

    # create list of atoms belonging to same molecule
    list_of_molecules   = merge_clusters(bonds)

    # generate bonding data
    frame = ase.Atoms(symbols)

    # TODO soooooo messy but works thanks God

    # generate unique molecule ID number to recognize it later
    mol_idx = []
    counter = 0
    for cc in range(len(frame)):

        index = np.where([cc in ii for ii in list_of_molecules])[0].tolist()

        # not in a molecule
        if index == []:
            mol_idx.append(counter + len(list_of_molecules))
            counter += 1
        else:
            mol_idx.append(index[0])

    mol_idx = np.array(mol_idx)

    # generate the molecule names
    mol_names = []
    mol_typ = np.array(len(mol_idx)*[-1])
    for  mol_id in set(mol_idx):

        indexes = np.where(mol_idx == mol_id)[0]
        cmol = frame[indexes]

        chem_formula = cmol.get_chemical_formula()

        if chem_formula not in mol_names:
            mol_names.append(chem_formula)

        idnr = np.where([chem_formula == mol_type for mol_type in mol_names])[0]
        mol_typ[indexes] = idnr
        
    logger.debug("Successfully parsed {} atoms, {} molecule types, {} bonds".format(
        len(symbols), len(mol_names), len(bonds)))

    if type2sym:
        return labels , symbols, np.array(mol_idx), np.array(mol_typ), mol_names,\
            np.array(ato_typ), np.array(connectivity, dtype=object)

    return symbols, np.array(mol_idx), np.array(mol_typ), mol_names,\
        np.array(ato_typ), np.array(connectivity, dtype=object)


def read_ase_file(ase_file):
    trajectory = ase.io.read(ase_file + "@:")

    output = []

    for frame in trajectory:
        output.append((frame, None, None, None, None))

    return output


def read_lammps_trajectory(lmp_file, skip_frames=False,
                           nframes=None, nstrides=None):

    # load traj file with low level API from mdtraj - could be better
    # this is very dump because no matter what you have to read the entire
    # file even when you skip some frames...
    with mdtraj.formats.LAMMPSTrajectoryFile(lmp_file, mode='r') as trajfile:
        # skip first frames if necessary
        if skip_frames:
            trajfile.seek(skip_frames)
        # read file and close it
        trajdata = trajfile.read(n_frames = nframes,
                                 stride   = nstrides)
        trajfile.close()

    logger = get_logger()
    logger.debug("Successfully read {} frames from trajectory".format(len(trajdata[0])))
    return trajdata

def read_colvars_traj_file(colvars_traj_file):

    logger = get_logger()
    logger.debug("Parsing colvars trajectory file: {}".format(os.path.basename(colvars_traj_file)))

    df = pd.read_csv(colvars_traj_file, sep='\s+',
                     on_bad_lines='warn', header=0, escapechar="#",
                     skip_blank_lines=True)

    df.columns = df.columns.str.replace(' ', '')

    df = df.loc[:, ~df.columns.str.startswith('r_')]
    df = df.loc[:, ~df.columns.str.startswith('fa_')]
    df[:] = df[:].apply(pd.to_numeric, errors='coerce')

    result_df = df.dropna(how="all").reset_index(drop=True)
    logger.debug("Successfully parsed {} colvars data points with {} columns".format(
        len(result_df), len(result_df.columns)))

    return result_df
