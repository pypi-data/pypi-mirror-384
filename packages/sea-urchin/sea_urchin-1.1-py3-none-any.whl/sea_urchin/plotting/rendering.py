#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 17:03:14 2023

@author: roncoroni
"""

import ase
import ase.visualize
import ase.visualize.plot

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import colorcet
import seaborn as sns
#%%
def subplots_centered(nrows, ncols, figsize, nfigs):
    """
    Modification of matplotlib plt.subplots(),
    useful when some subplots are empty.

    It returns a grid where the plots
    in the **last** row are centered.

    Inputs
    ------
        nrows, ncols, figsize: same as plt.subplots()
        nfigs: real number of figures
    """
    if nfigs == nrows * ncols:
        fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize)
        return fig, list(axs.flat)

    fig = plt.figure(figsize=figsize)
    axs = []

    m = nfigs % ncols
    m = range(1, ncols+1)[-m]  # subdivision of columns
    gs = gridspec.GridSpec(nrows, m*ncols)

    for i in range(0, nfigs):
        row = i // ncols
        col = i % ncols

        if row == nrows-1: # center only last row
            off = int(m * (ncols - nfigs % ncols) / 2)
        else:
            off = 0

        ax = plt.subplot(gs[row, m*col + off : m*(col+1) + off])
        axs.append(ax)

    return fig, axs

#%%
def plot_structures(clusters, labels=None, cmap=None, pad=0.35,
                    rotation="", n=None, facecolor=False,
                    size=5, edges=True, alpha=1):

    if labels is not None:
        # generate colormap (noise is zero)
        colors = sns.color_palette(colorcet.glasbey_dark, n_colors=np.max(labels)+1)

    # get good grid, maybe...
    if n is None:
        n = int(np.floor(np.sqrt(len(clusters))))
    m = int(np.ceil(len(clusters)/n))

    resize = size/n

    # generate figure
    # fig, axs = plt.subplots(nrows=n, ncols=m, figsize=(size*m/n, size))

    fig, axs = subplots_centered(n, m, (size*m/n, size), len(clusters))

    # generate common axis for making a grid
    common_ax = fig.add_subplot(111, facecolor='none')
    common_ax.tick_params(labelcolor='none', which='both', top=False,
                          bottom=False, left=False, right=False)
    common_ax.set_position([0, 0, 1, 1])

    common_ax.set_yticks(np.linspace(0, 1, n+1))
    common_ax.set_xticks(np.linspace(0, 1, m+1))

    # add edges to structures and image
    if edges:
        common_ax.grid(color="k", linewidth=3*resize)
        for spine in common_ax.spines.values():
            spine.set_linewidth(6*resize)
            spine.set_position(('outward',0))
            spine.set_edgecolor('black')

    # adjust subplots
    fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

    custom_lim = np.array([0, -np.inf])

    # plot structures
    centers = []
    for cc, cluster in enumerate(clusters):

        cax = axs[cc]

        ase.visualize.plot.plot_atoms(cluster, ax=cax,
                                      rotation=rotation,
                                      show_unit_cell = 0)

        cax.set_xticklabels([])
        cax.set_yticklabels([])
        # cax.axis('off')
        for spine in cax.spines.values():
            spine.set_visible(False)

        centers.append([(np.diff(cax.get_xlim())/2)[0],
                        (np.diff(cax.get_ylim())/2)[0]])

        custom_lim[1] = np.maximum(custom_lim[1],
                                   np.maximum(cax.get_xlim()[1], cax.get_ylim()[1]))

        if facecolor:
            cax.patch.set_facecolor(colors[labels[cc]])
            cax.patch.set_alpha(alpha)

    # center all structures
    for cc in range(len(clusters)):

        # cax = axs.flat[cc]
        cax = axs[cc]

        dx = np.diff(custom_lim)[0]/2 - centers[cc][0]
        dy = np.diff(custom_lim)[0]/2 - centers[cc][1]

        cax.set_xlim(custom_lim - dx + [-pad, pad])
        cax.set_ylim(custom_lim - dy + [-pad, pad])

    # remove end plots
    # for ii in range(n*m-len(clusters)):
        # axs[-ii-1].remove()
        # axs.flat[-ii-1].remove()

    return