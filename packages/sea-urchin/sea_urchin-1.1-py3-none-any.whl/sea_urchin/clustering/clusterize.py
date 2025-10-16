#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  8 09:53:43 2022

Set of functions to perform clustering of SeaUrchin objects.


@author: electrolyte-machine
"""

# numpy will be numpy
import numpy as np

import copy

# sea urchin packages
import sea_urchin.alignement.align as ali
import sea_urchin.clustering.metrics as met
import sea_urchin.utilities.auxiliary_functions as aux

# learning tools
import umap
import hdbscan
import sklearn.preprocessing as prep
from sklearn.pipeline import make_pipeline

# turn off warnings
import warnings
warnings.filterwarnings("ignore")

#%%

def generate_scaler(scaler):
    
    # match scaler:
        
    if scaler in ["none", None, "None"]:
        return prep.StandardScaler(with_mean=False, with_std=False)
    
    elif scaler == "robust":
        return prep.RobustScaler(quantile_range = (10, 90))
    
    elif scaler == "standard":
        return prep.StandardScaler()
    
    elif scaler == "maxabs":
        return prep.MaxAbsScaler()
    
    elif scaler == "minmax":
        return prep.MinMaxScaler()
    
    elif scaler == "std-mean":
        return prep.StandardScaler(with_std=False)
    
    else:
        raise "{} is not a properly implemented method".format(scaler)
    
    return
    

def cluster_with_umap(data,
                      umap_par    = None,
                      hdbscan_par = None,
                      labels      = None,
                      scaler      = "standard",
                      raw_hdbscan = False,
                      parametric  = False,
                      add_data    = None,
                      predict     = True,
                      ):

    # reshape data just to be sure
    data = np.reshape(data, (len(data), -1))

    # add extra data to the metric
    if add_data is not None:
        add_data  = np.reshape(add_data, (len(add_data), -1))
        data      = np.concatenate((data, add_data), axis=1)

    # generate scaler
    data_scaler = generate_scaler(scaler)

    # generate UMAP object in a sklearn pipeline
    # and reduce dimentionality of the data to N dimensions

    if raw_hdbscan:
        pipe = make_pipeline(data_scaler)

    if not raw_hdbscan:
        pipe = make_pipeline(
            data_scaler,
            umap.UMAP(**umap_par)
            )


    # fit data with generated pipeline
    coordinates = pipe.fit_transform(data, y=labels)

    # run HDBSCAN on scaled and reduced distances
    clusterer = hdbscan.HDBSCAN(
        **hdbscan_par,
        prediction_data = predict
        )

    # fit with calculated distances
    clusterer.fit(coordinates)

    return pipe, clusterer

def get_rep_idxs(exemplars, coordinates, sampling=False, nsamples=1):

    if sampling:

        exclu = hdbscan.HDBSCAN(
            allow_single_cluster = True,
            min_cluster_size     = 3,
            ).fit(exemplars)

        ncoord = []
        for ex in exclu.exemplars_:

            tsize = np.minimum(nsamples, len(ex))
            ncoord.extend(ex[np.random.choice(ex.shape[0], tsize, replace=False)])

    else:

        if nsamples == 1:
            mean_pos = np.mean(exemplars, axis=0)
            closest_node = aux.closest_node(mean_pos, exemplars)
            ncoord = [exemplars[closest_node]]

        else:
            tsize = np.minimum(nsamples, exemplars.shape[0])
            ncoord = exemplars[np.random.choice(exemplars.shape[0], tsize, replace=False)]
    ncoord = np.array(ncoord)

    outidx = [aux.closest_node(coord, coordinates) for coord in ncoord]

    return outidx

def generate_representatives(clusters,
                             clusterer     = None,
                             labels        = None,
                             coordinates   = None,
                             probabilities = None,
                             sampling   = True,
                             post_align = False,
                             nsamples   = 1,
                             alignment  = {},
                             nmax       = 50
                             ):

    if clusterer is not None:
        if labels is None:
            labels = clusterer.labels_
        if coordinates is None:
            coordinates = clusterer._raw_data
        if probabilities is None:
            probabilities = clusterer.probabilities_

    else:
        if probabilities is None:
            probabilities = np.array([1]*len(labels))
        if coordinates is None:
            coordinates = np.array([[0,0]]*len(labels))


    # generate representatives
    unique_labels, counts = np.unique(labels, return_counts = True)

    # all noise - temp fix
    if all(labels == -1):
        print("All noise")
        representatives = [cc.copy() for cc in clusters]
        reps_indexes    = np.arange(len(representatives))

    else:

        exemplars = []

        for label in unique_labels:
            if label == -1:
                continue

            indexes = np.where((labels == label) & (probabilities == 1))[0]

            exemplars.append(coordinates[indexes])

        representatives = []
        reps_indexes    = []
        for label in unique_labels:

            if label == -1:
                continue

            representative_indexes = get_rep_idxs(exemplars[label],
                                                  coordinates,
                                                  sampling = sampling,
                                                  nsamples = nsamples)

            for repidx in representative_indexes:
                representatives.append(clusters[repidx].copy())
                reps_indexes.append(repidx)



    if post_align:

        representatives = ali.chain_alignment(representatives, alignment)


    return representatives, np.array(reps_indexes)