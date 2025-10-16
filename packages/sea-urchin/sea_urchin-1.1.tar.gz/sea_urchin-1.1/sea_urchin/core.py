#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  8 09:53:43 2022

SeaUrchin object.


@author: electrolyte-machine
"""

#%% Import relevant modules

# ase stuff
import ase
import ase.io
import ase.build
import ase.visualize

# numpy my best friend
import numpy as np

# can't work with dataframes without good ol' pandas
import pandas as pd

# parallel computation
from joblib import Parallel, delayed

# iteration are a thing, and other libraries as well
import itertools
import collections

# os and save stuff
import dill
import os
import glob
import copy
import sys

# electrolyte machine packages
import sea_urchin.utilities.auxiliary_functions as aux
import sea_urchin.utilities.su_cluster as suc
import sea_urchin.read.read as read
from   .colvars import pmf
from   .taxionomy.coordination import CoordCluster
from   .utilities.volume import estimate_cluster_volume_libarvo, estimate_cluster_volume_volmol
from   .utilities.logger import get_logger, configure_logging, print_header, print_startup_info

# graphs and networks
import networkx as nx

# more stuff
import time
import matplotlib.pyplot as plt
from   pathlib import Path
from   typing import Any, Dict
from functools import partial

#%% MAIN CLASS

class SeaUrchin(object):

    # define default parameters
    default_parameters: Dict[str, Any] = {
        "reconstruct" : {
            "type"    : None,
            "depth"   : 1,
            "merge"   : True,
            "inverse" : False,
            },

        }

    def __init__(self,
                 input_file,
                 path        = None,
                 ref_atom    = None,
                 coord_env   = None,
                 cutoff_dist = 4.0,
                 bgf_file    = None,
                 pmf_file    = None,
                 col_file    = None,
                 nframes     = None,
                 nstrides    = None,
                 skip_frames = False,
                 save        = True,          # save or not
                 save_name   = "urchin.pkl" , # name of the saved pkl file
                 save_path   = None,          # path where to save the object
                 multiple_replica = False,  # True if it's a MR calculation with subfolders
                 parallel         = True,   # parallel compute of clusters, WIP
                 free_energy      = True,   # assign free energy from pmf (SLOW!)
                 reconstruct      = None,   # reconstruct molecules of what is found in coord. env.
                 verbose          = True,   # enable verbose logging
                 log_level        = "INFO", # logging level (DEBUG, INFO, WARNING, ERROR)
                 log_file         = None    # optional log file path
                 ):

        # Print beautiful header
        print_header()

        # initialize object variables and such
        self.savename = save_name
        self.__start_time  = time.time()

        # Configure logging based on user preferences
        if verbose:
            configure_logging(level=log_level, log_file=log_file)
        else:
            configure_logging(level="WARNING", log_file=log_file)

        # Get logger instance
        self.logger = get_logger()

        # Print startup information
        print_startup_info(verbose=verbose, log_level=log_level, log_file=log_file)

        if path is None:
            cpath      = Path(input_file)
            self.cpath = str(cpath.parent) + "/"
            input_file = cpath.name
        else:
            self.cpath = path
            input_file = Path(input_file).name

        # save internal variables
        self.__is_parallel = parallel

        # set default parameters
        if reconstruct is None:
            reconstruct = self.get_default_parameters("reconstruct")
        else:
            def_reconstruct = self.get_default_parameters("reconstruct")
            def_reconstruct.update(reconstruct)
            reconstruct = def_reconstruct

        # check input file type
        self.logger.info(f"Starting to read input file: {input_file}")
        file_type = aux.check_file_type(input_file)
        self.logger.info("File format detected: {}".format(file_type))

        if file_type == "pickle":
            self.restart_from_pickle(self.cpath + input_file)

        else:
            self.logger.info("Initializing from scratch. Hang in there.")
            self.initialize_from_scratch(input_file, file_type, ref_atom,
                                        coord_env, cutoff_dist, bgf_file,
                                        multiple_replica, skip_frames, nframes,
                                        nstrides, col_file, reconstruct)

            if pmf_file is not None:
                self.logger.info("PMF file provided. Reading metadynamics information.")
                self.initialize_pmf_object(pmf_file, multiple_replica)

                if free_energy:
                    self.logger.info("Assigning free energy to each frame.")
                    self.assign_frame_free_energy()

            # get path of file as save path
            if save_path is None:
                self.save_path = self.cpath
            else:
                self.save_path = save_path

            if save: # save object if yes
                self.save_object(save_name, save_path)

        self.logger.info("SeaUrchin operation completed in {:.3f} s.".format(
            time.time() - self.__start_time))

        return

    def initialize_from_scratch(self, input_file, file_type, ref_atom,
                                coord_env, cutoff_dist, bgf_file,
                                multiple_replica, skip_frames, nframes, nstrides,
                                col_file, reconstruct):

        # decorate a bit this class
        self.sea_urchin_object = True
        self.__start_time  = time.time()

        # save some variables
        self.relevant_atoms = aux.as_list(ref_atom) + aux.as_list(coord_env)

        if file_type == "lammps":

            if not os.path.isfile(bgf_file):
                assert os.path.isfile(self.cpath + bgf_file)
                bgf_file = self.cpath + bgf_file

            self.logger.debug("Reading topology file: {}".format(os.path.abspath(bgf_file)))
            std_data = read.read_topology_file(bgf_file)

            lammps_traj, timestamps, colvars_traj = self.read_lammps_file(
                input_file, std_data,
                col_file          = col_file,
                skip_frames       = skip_frames,
                nframes           = nframes,
                nstrides          = nstrides,
                multiple_replica  = multiple_replica
                )

            # find indexes of all relevant atoms in the system
            # helps removing everything we don't need
            relevant_indexes = aux.atoms_to_indexes(self.first_frame,
                                                    self.relevant_atoms)

            # indexes of reference atoms
            reference_indexes = aux.atoms_to_indexes(self.first_frame,
                                                    ref_atom)

            start = time.time()
            # convert lammps to ase.Atoms
            trajectory, urchin_data, system_graph = self.convert_to_ase(
                lammps_traj, std_data, relevant_indexes)

            ctime = time.time() - start
            self.logger.info("Converted in ASE format in {:.2f} s.".format(ctime))
            
        #TODO check here
        self.system_graph = system_graph
        self.urchin_data = urchin_data
            
        # if file_type == "ase":
            # trajectory = self.read_ase_file(input_file)


        self.logger.info("Trajectory done. Dividing into clusters.")
        start = time.time()
        # make clusters
        self.clusters = self.divide_into_clusters(trajectory, reference_indexes,
                                                  cutoff_dist, timestamps,
                                                  urchin_data    = urchin_data,
                                                  system_graph   = system_graph,
                                                  colvars_data   = colvars_traj,
                                                  coord_env      = coord_env,
                                                  parallel       = self.__is_parallel,
                                                  reconstruct = reconstruct)
        ctime = time.time() - start
        self.logger.info("Clusters created in {:.2f} s - finishing the object.".format(ctime))

        self.cluster_formulas = np.array(
            [ii.get_chemical_formula() for ii in self.clusters])
        self.cluster_types = collections.Counter(self.cluster_formulas)

          #Save colvar values for each frame/cluster
        if col_file is not None:
            self._colvars = colvars_traj

        return

    def read_single_replica(self, lmp_file, std_data, skip_frames, nframes,
                            nstrides, col_file, replica_id=None):

        # get current path
        cpath = "/".join(os.path.abspath(lmp_file).split("/")[:-1]) + "/"

        # read lammps trajectory from lmp file
        lammps_traj = self.read_lammps_trajectory(lmp_file,
                                                  skip_frames,
                                                  nframes,
                                                  nstrides)

        # get timestamps of the trajectory
        timestamps = self.get_lammps_timestamps(lmp_file,
                                                len(lammps_traj[0]),
                                                skip_frames, nstrides)

        if col_file is not None:
            col_path = cpath + col_file
            self.logger.debug("Reading colvars file: {}".format(os.path.abspath(col_path)))
            colvars_traj = self.read_col_file(col_path)
            colvars_traj = colvars_traj[colvars_traj['step'].isin(timestamps)]
        else:
            colvars_traj = pd.DataFrame()

        colvars_traj["replica_id"] = len(timestamps)*[replica_id]

        return lammps_traj, timestamps, colvars_traj

    def read_multiple_replica(self, lmp_file, std_data, skip_frames, nframes,
                              nstrides, col_file):

        # get list of mr files
        mr_path = "/".join(os.path.abspath(lmp_file).split("/")[:-2]) + "/"

        self.cpath = mr_path

        lmp_file = lmp_file.split("/")[-1]

        self.logger.debug("Searching for multiple replica files in: {}".format(os.path.abspath(mr_path)))
        files_list =  glob.glob(mr_path + "/*/" + lmp_file)
        files_list.sort()

        # check long enough
        assert len(files_list) > 0, "No files found, are you in the right directory?"

        self.logger.info("Found MR trajectory with {} files".format(len(files_list)))
        for i, f in enumerate(files_list[:5]):  # Show first 5 files
            self.logger.debug("  [{}] {}".format(i+1, os.path.abspath(f)))
        if len(files_list) > 5:
            self.logger.debug("  ... and {} more files".format(len(files_list) - 5))

        # generate list of MR directories
        mr_dirs = ["/".join(sdir.split("/")[:-1]) + "/" for sdir in files_list]

        num_cores = aux.optimal_n_jobs(len(mr_dirs), parallel=self.__is_parallel)

        self.logger.info("Reading trajectories, parallelizing over {} cores".format(
            num_cores))

        with Parallel(n_jobs=num_cores, backend="loky") as PAR:
            data = PAR(delayed(self.read_single_replica)(
                sdir + lmp_file, std_data, skip_frames, nframes, nstrides,
                col_file, replica_id=cc)
                for cc, sdir in enumerate(mr_dirs))

        positions    = []
        cells        = []
        angles       = []
        timestamps   = []
        colvars_traj = []

        for rep_data in data:
            positions.append(rep_data[0][0])
            cells.append(rep_data[0][1])
            angles.append(rep_data[0][2])
            timestamps.extend(rep_data[1])
            colvars_traj.append(rep_data[2])

        lammps_traj = (np.concatenate(positions, axis=0),
                        np.concatenate(cells,     axis=0),
                        np.concatenate(angles,    axis=0)
                        )

        return lammps_traj, timestamps, pd.concat(colvars_traj, ignore_index=True)

    # initialize analysis from new trajectory
    def read_lammps_file(self, lmp_file, std_data, col_file=None,
                       skip_frames=False, nframes=None, nstrides=None,
                       multiple_replica=False):

        lmp_file = self.cpath + lmp_file

        start = time.time()
        self.logger.info("Reading trajectory with parameters (skip: {}, nframes: {}, stride: {})".format(
            skip_frames, nframes, nstrides))

        if not multiple_replica:
            self.logger.debug("Reading LAMMPS trajectory file: {}".format(os.path.abspath(lmp_file)))
            lammps_traj, timestamps, colvars_traj = self.read_single_replica(
                lmp_file, std_data, skip_frames, nframes, nstrides, col_file)

        else:
            lammps_traj, timestamps, colvars_traj = self.read_multiple_replica(
                lmp_file, std_data, skip_frames, nframes, nstrides, col_file)

        self.logger.info("All trajectories read in in {:.3f} s.".format(
            time.time() - start))

        # store a frame and molecues (if possible) as reference
        self.first_frame, self.molecules = self.store_first_frame(lammps_traj,
                                                                      std_data)

        return lammps_traj, timestamps, colvars_traj

    def initialize_pmf_object(self, pmf_file, multiple_replica=False):

        cpath    = os.path.dirname(pmf_file) + "/"
        pmf_file = os.path.basename(pmf_file)

        if multiple_replica:

            try:
                self.pmf = pmf.MultipleReplica(cpath, pmf_file)
            except:
                self.pmf = pmf.SingleReplica(cpath, pmf_file)
        else:
            self.pmf = pmf.SingleReplica(cpath, pmf_file)
        return

    #ASM - EDIT!!
    # This is bad cause we're reading the trajectory twice,
    # and if frames are skipped we're missing that too.
    # So, really temporary patch!!
    def get_lammps_timestamps(self, lmp_file, nframes,
                              skip_frames, nstrides):

        #ASM - add timestamps cause mdtraj ignores them. not great
        sf = 0 if skip_frames is None else skip_frames
        ns = 1 if nstrides is None else nstrides

        t0, dt = self.get_lammps_delta_time(lmp_file)

        timestamps = t0 + np.array((range(sf, sf+nframes*ns, ns)))*dt

        return timestamps

    @staticmethod
    def get_lammps_delta_time(lmp_file):

        t0 = None
        t1 = None
        with open(lmp_file, "r") as myfile:
            for line in myfile:
                if 'ITEM: TIMESTEP' in line:

                    if t0 is None:
                        line = next(myfile)
                        t0 = int(line.split()[0])
                    elif t1 is None:
                        line = next(myfile)
                        t1 = int(line.split()[0])
                    else:
                        break
        if t0 is None or t1 is None:
            return 0, 0
        return t0, t1-t0

    @staticmethod
    def convert_to_ase(trajdata, std_data, relevant_indexes):

        # have more details of molecular structure
        assert isinstance(std_data, tuple), "Give a valid data file."

        # calculate some int
        n_atoms_tot = len(std_data[0])

        # keep track of original indexes
        ori_idx = np.array(list(range(n_atoms_tot)))

        # generate graph of system
        system_graph = nx.Graph()
        system_graph.add_nodes_from(list(range(n_atoms_tot)))
        system_graph.add_edges_from([[ii, jj] for ii, bonds in
                                     enumerate(std_data[-1]) for jj in bonds])
        system_graph.remove_nodes_from(np.delete(ori_idx, relevant_indexes))

        # start reducing size of frame by isolating relevant atoms

        # remove unnecessary symbols
        symbols = std_data[0][relevant_indexes]

        # generate dict with relevant atomic informations
        urchin_data = {
            "mol_idx" : std_data[1][relevant_indexes],
            "mol_typ" : std_data[2][relevant_indexes],
            "mol_nam" : std_data[3],
            "ato_typ" : std_data[4][relevant_indexes],
            "ori_idx" : ori_idx[relevant_indexes],
            "bnd_idx" : std_data[5][relevant_indexes],
            }

        # function to make a ASE frame from trajectory object
        def make_frame(trajdata, pos, cc):

            # calculate unit cell
            cell = trajdata[1][cc].tolist() + trajdata[2][cc].tolist()

            # generate frame and wrap it
            frame = ase.Atoms(symbols, pos[relevant_indexes], cell=cell, pbc=True)
            return frame

        # convert trajectory in ASE atoms objects
        num_cores = aux.optimal_n_jobs(len(trajdata[0]), full=True)
        with Parallel(n_jobs=num_cores, backend="loky") as PAR:
            trajectory = PAR(delayed(make_frame)
                                    (trajdata, pos, cc)
                                    for cc, pos in enumerate(trajdata[0]))

        return trajectory, urchin_data, system_graph

    # go through a trajectory and make a cluster of the coord. environment
    # around the reference atom
    def divide_into_clusters(self, trajectory, ref_atom, cutoff_dist,
                             timestamps,
                             urchin_data  = None,
                             system_graph = None,
                             colvars_data = None,
                             coord_env    = None,
                             parallel     = False,
                             reconstruct  = False
                             ):

        assert reconstruct and urchin_data["mol_idx"] is not None,\
            "cannot reconstruct molecules and not provide urchin data (data.lammps)"


        #get indices of target elements of trimmed frames
        tar_idxs = np.where([cc in ref_atom for cc in urchin_data["ori_idx"]])[0]
        
        # build cutoff for target indexes
        cutoffs = suc.generate_cutoffs(self.first_frame, cutoff_dist, tar_idxs)

        num_cores = aux.optimal_n_jobs(len(trajectory), parallel=parallel)
        with Parallel(n_jobs=num_cores, backend="loky") as PAR:
            data = PAR(delayed(self.make_clusters_from_frame)(
                frame, tar_idxs, cutoffs,system_graph, timestamps[cc],
                colvars_data, urchin_data, coord_env=coord_env, counter=cc,
                reconstruct=reconstruct)
                for cc, frame in enumerate(trajectory))

        clusters = list(itertools.chain.from_iterable(data))

        return clusters

    # Function that takes each frame and divides it into an "atoms" object for
    # each instance of a target element in that frame (e.g. Ca). Each "atoms"
    # contains the target + coordination sphere within cutoff.
    @staticmethod
    def make_clusters_from_frame(frame, tar_idxs, cutoffs, system_graph,
                                 timestamp, colvars_data, urchin_data,
                                 coord_env=None, counter=None, reconstruct=None):



        #Chop into clusters, make atoms object for each
        clusters_idxs = []
        for cc, tar_idx in enumerate(tar_idxs):

            # calculate distances from target atom
            distances = frame.get_distances(tar_idx,
                                            list(range(len(frame))), mic=True)

            # atoms within cutoff
            cutoff = cutoffs[cc]
            cutoff_idxs = np.where(distances <= cutoff)[0].tolist()

            # find neighbors or entire molecules
            new_neighbors = suc.find_neighbors(cutoff_idxs, urchin_data,
                                               system_graph,
                                               reconstruct)

            cutoff_idxs.extend(new_neighbors)

            # append to list of clusters (make sure stuff is unique)
            clusters_idxs.append(np.unique(cutoff_idxs))

        # reconstruct clusters according to mode
        merged_clusters = suc.reconstruct_clusters(clusters_idxs, system_graph,
                                                   urchin_data, tar_idxs,
                                                   reconstruct)

        # now let's make the clusters
        clusters = []
        for cluster_idx in merged_clusters:

            # generate cluster from labels
            cluster = CoordCluster(frame[cluster_idx])

            # find atoms of interest
            if not reconstruct["inverse"]:
                ref_idx = [cc for cc, idx in enumerate(cluster_idx)
                            if idx in tar_idxs]
            else:
                ref_idx = list(range(len(cluster_idx)))

            # add metadata
            suc.assign_metadata(cluster, urchin_data, cluster_idx, colvars_data,
                                timestamp, counter, coord_env, ref_idx)

            # move molecules in cluster to make pretty
            cluster = suc.translate_molecules(cluster, ref_idx)

            # remove cell and PBC
            cluster.set_cell(None)
            cluster.set_pbc(False)

            # sort according to key (reshuffle to at least have atoms together)
            cluster = cluster.sorted_cluster()

            # add ID print (if possible)
            if cluster.info["mol_idx"] is not None:
                cluster.info["id_print"] = suc.generate_id_print(cluster)

            # append cluster
            clusters.append(cluster)

        return clusters

    @staticmethod
    def store_first_frame(trajdata, std_data):

        if isinstance(std_data, tuple):
            symbols = std_data[0]
        else:
            symbols = std_data


        frame = ase.Atoms(symbols,
                          trajdata[0][0],
                          cell = trajdata[1][0].tolist() + trajdata[2][0].tolist(),
                          pbc  = True)

        if not isinstance(std_data, tuple):
            return frame, None

        molecules = []
        for mol_idx in set(std_data[1]):

            indexes = np.where(std_data[1] ==  mol_idx)[0]

            molecule = frame[indexes]

            origin = np.mean(molecule.get_positions(), axis=0)
            molecule.translate(-origin)

            molecule.cell = None

            molecules.append(molecule)

        return frame, molecules

    @staticmethod
    def read_ase_file(ase_file):
        return read.read_ase_file(ase_file)


    @staticmethod
    def read_lammps_trajectory(lmp_file, skip_frames=False, nframes=None,
                               nstrides=None):
        return read.read_lammps_trajectory(lmp_file, skip_frames,
                                           nframes, nstrides)

    #ASM
    @staticmethod
    def read_col_file(col_file):
        return read.read_colvars_traj_file(col_file)

    # view all clusters
    def view(self, formula=None):
        
        if formula is not None:
            clusters = self.get_cluster_with_formula(formula)
        else:
            clusters = self.clusters
            
        ase.visualize.view(clusters)
        return

    def get_cluster_types(self):
        return list(self.cluster_types.keys())

    def get_cluster_with_formula(self, formula, id_print={},
                                 single=False):
        assert formula in self.cluster_types, "Wrong chemical formula"
        idxs = np.where(self.cluster_formulas == formula)[0]

        clusters = [self.clusters[ii].copy() for ii in idxs]

        if not bool(id_print):
            return clusters
        else:
            new_clusters = []

            for clu in clusters:
                if all([id_print[ele] == clu.info[ele] for ele in id_print]):
                    new_clusters.append(clu)
                    if single:
                        return new_clusters
            return new_clusters

    # colvars needs to be a vector in right order
    def get_cluster_with_colvars(self, colvars):

        dataframe = self._colvars.loc[:, self.pmf.colvars_name]

        index = aux.closest_node(colvars, dataframe)

        print(self._colvars.loc[index])

        return self.clusters[index].copy()
    
    def get_volumes(self, formula=None, parallel=True, probe_rad=0.0,
                    vorlength=0.2, mode="libarvo", atom_radii=None):
        
        if mode == "libarvo":
            vol_calc = partial(estimate_cluster_volume_libarvo,
                               probe_rad=probe_rad, radii=atom_radii)
        elif mode == "volume":
            vol_calc = partial(estimate_cluster_volume_volmol,
                               probe_rad=probe_rad, vorlength=vorlength)
        
        if formula is None:
            clusters = self.clusters
        else:
            clusters = self.get_cluster_with_formula(formula)
             
        num_cores = aux.optimal_n_jobs(len(clusters), parallel=parallel)
        with Parallel(n_jobs=num_cores, backend="loky") as PAR:
            volumes = PAR(delayed(vol_calc)(cluster) for cluster in clusters)
        
        return np.array(volumes)
        
        

    def plot_abundance(self, ignore=None, group_mol=True):

        # CALCULATE ABUNDANCE
        abundance = collections.Counter(self.cluster_formulas)

        if ignore is not None:
            for ii in aux.as_list(ignore):
                abundance.pop(ii)

        # sort by pop
        D  = dict(sorted(abundance.items(), key=lambda item:item[1], reverse=True))

        if group_mol:
            strings = []
            for formula in D:
                clusters = self.get_cluster_with_formula(formula, single=True)
                strings.append(aux.generate_chemical_string(clusters[0]))
        else:
            strings = D.keys()


        values = np.array(list(D.values()))
        values = values/values.sum()

        # plot figure
        fig, ax = plt.subplots(figsize=(5,6))

        ax.barh(len(D) - np.arange(len(D)), values, align='center')
        ax.set_yticks(len(D) - np.arange(len(D)), strings)

        ax.set_xlabel("abundance [-]")
        ax.set_ylabel("chemical specie [-]")

        fig.tight_layout()

        fig.show()
        print(abundance)

        return

    #add free energy data to clusters #TODO very slow
    def assign_frame_free_energy(self):

        #Energy within step of the target colvars
        def give_energy(cluster):

            coord  = [cluster.info["colvars_data"][ii] for ii in self.pmf.colvars_name]
            energy = self.pmf.get_free_energy(coord)

            cluster.info["colvars_data"][
                "free_energy"] = energy
            return cluster, energy

        num_cores = aux.optimal_n_jobs(len(self.clusters), full=True)
        with Parallel(n_jobs=num_cores, backend="loky") as PAR:
            clusters, energies = zip(*PAR(delayed(give_energy)(
                cluster) for cluster in self.clusters))

        self.clusters = list(clusters)
        self._colvars["free_energy"] = energies

        return

    def get_default_parameters(self, element):
        return copy.deepcopy(self.default_parameters[element])

    # save object as pkl file
    def save_object(self, oname=None, save_path=None):

        if oname is None:
            oname = self.savename

        if save_path is None:
            path = self.save_path
        else:
            path = save_path

        if oname.endswith(".pkl"):
            oname =  path + "/" + oname
        else:
            oname = path + "/" + oname.split(".")[-1] + ".pkl"

        with open(oname, 'wb') as fout:
            dill.dump(self, fout)

        self.logger.info("Saved everything as {}".format(oname))
        return

    # restart object from pkl file previously saved
    def restart_from_pickle(self, lmp_file):

        start_time = self.__start_time

        # # quick fix to allow reloads
        try:
            import sea_urchin.colvars
        except:
            import pycolvars
            sys.modules["colvars"] = pycolvars

        # open previously generated gpw file
        with open(lmp_file, "rb") as fin:
            restart = dill.load(fin)

        self.__dict__ = restart.__dict__.copy()

        assert hasattr(self, "sea_urchin_object"), "Cannot load non compatible object!"

        self.__start_time = start_time

        return
