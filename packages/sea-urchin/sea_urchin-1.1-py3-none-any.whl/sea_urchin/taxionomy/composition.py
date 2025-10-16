#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  8 09:53:43 2022

Classes that go well with the TaxSeaUrchin object.


@author: electrolyte-machine
"""

import numpy as np
import ase
import ase.visualize
import hdbscan

# os and save stuff
import dill

# more stuff
import copy

# sea urchin stuff
import sea_urchin.plotting.plot as plf
import sea_urchin.alignement.align as ali
from sea_urchin.taxionomy.isomer import Isomer
import sea_urchin.clustering.clusterize as clf
from sea_urchin.plotting.rendering import plot_structures
from sea_urchin.plotting.utilities import align_bonds
#%%
class ClusterComposition():

    def __init__(self,
                 clusters       = None,
                 distances      = None,
                 feature_vec    = None,
                 clusterer      = None,
                 pipe           = None,
                 ref_structures = None,
                 alignment      = None,
                 post_align     = False,
                 clean_align    = False,
                 pkl_file       = None,
                 user_labels  = None,
                 user_coords  = None,
                 user_probs   = None,
                 ):

        if pkl_file is None:
            self.initialize_from_scratch(clusters, distances, feature_vec,
                                         clusterer, pipe, ref_structures,
                                         alignment, post_align, clean_align,
                                         user_labels, user_coords, user_probs)

        else:
            self.restart_from_pickle(pkl_file)

        return

    def initialize_from_scratch(self, clusters, distances, feature_vec,
                                clusterer, pipe, ref_structures, alignment,
                                post_align, clean_align, user_labels,
                                user_coords, user_probs):

        # get formula
        self.formula    = clusters[0].get_chemical_formula()
        # assert all([cc.get_chemical_formula() == self.formula for cc in clusters])

        # initialize variables
        self.distances      = distances
        self.clusterer      = clusterer
        self.pipe           = pipe
        self.ref_structures = ref_structures
        self.feature_vec    = feature_vec
        self.alignment      = alignment

        # assign manual labels instead of using the clusterer
        # ugly and probably buggy #TODO
        if clusterer is not None:
            if user_labels is None:
                labels = clusterer.labels_
            else:
                labels = user_labels
            if user_coords is None:
                coordinates = clusterer._raw_data
            else:
                coordinates = user_coords
            if user_probs is None:
                probabilities = clusterer.probabilities_
            else:
                probabilities = user_probs
        else:
            assert user_labels is not None
            labels = user_labels
            if user_probs is None:
                probabilities = np.array([1]*len(labels))
            else:
                probabilities = user_probs
            if user_coords is None:
                coordinates = np.array([[0,0]]*len(labels))
            else:
                coordinates = user_coords

        # assign variables
        self.labels        = labels
        self.probabilities = probabilities
        self.coordinates   = coordinates

        if pipe is not None:
            try:
                self.umap_obj  = pipe["umap"]
            except:
                self.umap_obj = None
        else:
            self.umap_obj  = None

        self.post_align     = post_align

        # generate set of representatives
        representatives, __ = clf.generate_representatives(
                                            clusters,
                                            clusterer     = clusterer,
                                            labels        = labels,
                                            coordinates   = coordinates,
                                            probabilities = probabilities,
                                            post_align = False, #TODO changed here
                                            sampling   = False,
                                            nsamples   = 1,
                                            alignment  = alignment,
                                            )
        
        if post_align: #TODO make cleaner
            representatives = ali.chain_alignment(representatives, alignment)

        # align groups to their mean structures
        if clean_align:
            self.clean_align(clusters, representatives, labels, alignment)

        # get labels
        unique_labels = np.unique(labels)
        if -1 in unique_labels:
            unique_labels = np.roll(unique_labels, -1)

        isomers = []
        for cc, label in enumerate(unique_labels):

            if label == -1:
                rep = None
            else:
                rep = representatives[cc]

            indexes = np.where(labels == label)[0]

            iso_clusters = []
            for index in indexes:

                cluster = clusters[index].copy()

                cluster.info["hdb_type"] = {
                    "label"       : labels[index],
                    "probability" : probabilities[index]
                    }

                # add to isomers
                iso_clusters.append(cluster)

            isomers.append(Isomer(iso_clusters, rep))


        self.representatives = representatives
        self.clusters        = clusters
        self.isomers         = isomers

        return

    def view(self, isomer=None):

        if isomer is None:
            ase.visualize.view(self.clusters)
        else:
            self.isomers[isomer].view()
        return

    def view_reps(self):
        ase.visualize.view(self.representatives)
        return

    # return representatives, ignoring noise
    def get_representatives(self):
        return [rep.copy() for rep in self.representatives]

    def get_mean_structure(self, label):

        cluster = self.isomers[label].structures[0].copy()

        positions = [cc.get_positions() for cc in self.isomers[label].structures]

        cluster.set_positions(np.mean(positions, axis=0))

        return cluster

    def get_mean_structures(self):

        structures = []

        for iso in self.isomers:

            if iso.hdb_type == -1:
                continue

            structures.append(self.get_mean_structure(iso.hdb_type))

        return structures

    # plot clustering mode
    def plot_clustering(self):
        plf.plot_UMAP_projection(self.coordinates, self.labels)
        return

    def plot_distribution(self, explode=False,
                          save=False):

        plf.plot_pie_chart(self.labels, explode=explode,
                           save=save)
        return

    # save object as pkl file
    def save(self, oname, save_path=None):

        if save_path is None:
            path = "./"
        else:
            path = save_path

        if oname.endswith(".pkl"):
            oname =  path + "/" + oname
        else:
            oname = path + "/" + oname.split(".")[-1] + ".pkl"

        with open(oname, 'wb') as fout:
            dill.dump(self, fout)

        print("Saved everything as {}".format(oname))
        return

    def copy(self):
        """Return a copy."""
        return copy.deepcopy(self)

    # restart object from pkl file previously saved
    def restart_from_pickle(self, pkl_file):

        # open previously generated gpw file
        with open(pkl_file, "rb") as fin:
            restart = dill.load(fin)

        self.__dict__ = restart.__dict__.copy()

        return

    # return relevant clusters
    def get_clusters(self):
        return [cc.copy() for cc in self.clusters]

    def get_clusters_with_label(self, label):
        return [clu.copy() for cc, clu in enumerate(self.clusters)
                if self.labels[cc] == label]

    # def realign_groups(self):

    #     clusterer = self.clusterer
    #     clusters  = self.clusters

    #     new_clusters = [clu.copy() for clu in clusters]
    #     for lab in set(clusterer.labels_):

    #         if lab == -1:
    #             continue

    #         t_clusters = [clu for ii, clu in enumerate(clusters)
    #                       if clusterer.labels_[ii] == lab]

    #         new_structures, mstru = ali.optimally_align_v2(t_clusters)

    #         counter = 0
    #         for cc in range(len(clusters)):
    #             if clusterer.labels_[cc] == lab:
    #                 new_clusters[cc].set_positions(
    #                     new_structures[counter].get_positions())
    #                 counter += 1

    #     self.clusters = new_clusters
    #     return

    def clean_align(self, clusters, representatives, labels, alignment):

        print("Performing clean alignment of {} groups:".format(
            len(representatives)))

        for lab in set(labels):

            if lab == -1: #ignore noise
                continue

            t_clusters = [clu for ii, clu in enumerate(clusters) if labels[ii] == lab]

            new_structures, mstru = ali.align_to_mean_structure(
                t_clusters, alignment, start_structure=representatives[lab],
                conv=1e-4)

            counter = 0
            for cc in range(len(clusters)):
                if labels[cc] == lab:
                    clusters[cc] = new_structures[counter]
                    counter += 1

        return

    def plot_representatives(self, rotation="", size=4, edges=True,
                             facecolor=False, pad=0.35, n=None, alpha=1,
                             mean_structures=False, rearrange=False):

        # get reps
        if not mean_structures:
            clusters = self.get_representatives()
        else:
            clusters = self.get_mean_structures()
            
        if rearrange:
            assert len(rearrange) == 3
            for cc, cluster in enumerate(clusters):
                clusters[cc] = align_bonds(cluster.copy(), *rearrange)
            
        labels = list(range(len(clusters)))

        plot_structures(clusters, size=size, labels=labels,
                        edges=edges, facecolor=facecolor,
                        rotation=rotation, pad=pad, n=n, alpha=alpha)

        return
    
    # project using UMAP
    def project(self, X):
        return self.pipe.transform(X)
    
    # predict HDBSSCAN labels from distance data
    def predict_labels(self, X):
        
        if not self.clusterer.prediction_data:
            self.clusterer.generate_prediction_data()
        
        Xs = self.project(X)
        
        return hdbscan.approximate_predict(self.clusterer, Xs)