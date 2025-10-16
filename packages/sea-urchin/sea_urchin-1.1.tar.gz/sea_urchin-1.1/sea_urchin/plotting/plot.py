#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 15:18:33 2022

@author: roncofaber
"""

import colorcet
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.ticker import FormatStrFormatter
import seaborn as sns
import numpy as np
#%%

# activate latex text rendering
# rc('text', usetex=True)
mpl.rcParams['mathtext.default'] = 'regular'

#sns parameters
sns.set()
sns.set_style("white")

fs = 13


def plot_UMAP_projection(data, labels, str_labels=None):

    fs = 13

    # generate colormap (noise is zero)
    colors = sns.color_palette(colorcet.glasbey_dark, n_colors=np.max(labels)+1)

    if -1 in labels:
        # tcolors = [(0,0,0)] + colors
        # colors =  colors[:-1] + [(0,0,0)]
        colors =  colors + [(0,0,0)]



    fig, ax = plt.subplots(figsize=(6,3.15))

    ax.set_position([0.1, 0.2, 0.35, 0.6666])

    for lab in set(labels):

        cdata = data[labels == lab]

        ax.scatter(
            x         = cdata[:, 0],
            y         = cdata[:, 1],
            marker = ".",
            color   = colors[lab],
            s         = 6,
            # alpha     = alpha,
            # linewidth = 0,
            label = lab,
            zorder = lab
                   )

    ax.set_title('UMAP projection', fontsize=fs+1, fontweight="bold")

    ax.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))


    ax.set_xlabel("coord 1", fontsize=fs)
    ax.set_ylabel("coord 2", fontsize=fs)
    
    ax.yaxis.set_tick_params(pad=-1)

    # pie options
    legend_properties = {'weight':'normal', "size":fs-2}


    # generate legend
    labs, counts = np.unique(labels, return_counts=True)

    if -1 in labels:
        labs   = np.roll(labs, -1)
        counts = np.roll(counts, -1)

    percentage = np.array([np.count_nonzero(labels == ii) for ii in labs])
    percentage = np.round(100*percentage/percentage.sum(),2)
    # print(percentage)

    if str_labels is None:
        leg_labels = ["{: >3d} : {:>4.1f}%".format(lab, percentage[cc])
                      for cc, lab in enumerate(labs)]
    else:
        leg_labels = ["{}".format(str_labels[lab])
                      for cc, lab in enumerate(labs)]

    ax.legend(leg_labels, ncol=2, loc='upper left', title = "HDBSCAN groups:",
               bbox_to_anchor=(1.05, 1.0), framealpha=1, edgecolor="k",
               prop = legend_properties, markerscale    = 12,
               alignment= "center")


    plt.show()

    return

def plot_UMAP_projection_3D(data, labels):

    # generate colormap (noise is zero)
    colors = sns.color_palette(colorcet.glasbey, n_colors=len(set(labels)))

    colors = ListedColormap(colors.as_hex())


    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    ax.scatter(
        data[:, 0],
        data[:, 1],
        data[:, 2],
        c    = labels,
        cmap = colors,
        s    = 6,
        # legend  = "full"
               )

    plt.title('UMAP projection', fontsize=fs+2)

    fig.legend(ncol=1,
               bbox_to_anchor=(1.005, 1),
               framealpha=1,
               fontsize=8) # Move the legend outside the plot

    ax.set_xlabel("coord 1", fontsize=fs)
    ax.set_ylabel("coord 2", fontsize=fs)
    ax.set_zlabel("coord 3", fontsize=fs)


    return

def plot_pie_chart(labels, explode=False,
                   save=False):

    labs, sizes = np.unique(labels, return_counts=True)

    if explode:
        explode = tuple([0.02 for cc in range(len(sizes))])
    else:
        explode = tuple([0.0 for cc in range(len(sizes))])

    # select colors
    colors = sns.color_palette(colorcet.glasbey, n_colors=len(set(labels)))

    if -1 in labels:
        colors = [(0,0,0)] + colors[:-1]

    # patches, text = plt.pie(sizes, colors = colors)

    # pie options
    wp = { 'linewidth' : 1, 'edgecolor' : "black" }
    legend_properties = {'weight':'normal', "size":9}

    fig1, ax1 = plt.subplots(figsize=(6,6))
    patches, text = ax1.pie(sizes,
            explode     = explode,
            labels      = labs,
            # autopct     = '%1.1f%%',
            # pctdistance = 0.6,
            shadow      = False,
            startangle  = -140,
            colors      = colors,
            textprops   = dict(fontweight ="bold"),
            wedgeprops  = wp,
            # rotatelabels = -45,
            )

    # generate legend
    percentage = 100*sizes/sizes.sum()
    leg_labels = ["{: >3d} : {: >4.1f}%".format(lab, percentage[cc])
                  for cc, lab in enumerate(labs)]

    ax1.legend(patches, leg_labels, ncol=3, loc='lower center',
               bbox_to_anchor=(0.5, -0.2), framealpha=1, edgecolor="k",
               prop = legend_properties)


    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    fig1.tight_layout()

    if save:
        plt.savefig(save, dpi=300)

    return fig1


def plot_many_pies(labels, train_size, titles,
                   save=False, plotargs={}, nrow=None):

    # select colors
    colors = sns.color_palette(colorcet.glasbey, n_colors=len(set(labels)))

    tcolors = colors.copy()
    if -1 in labels:
        tcolors = [(0,0,0)] + tcolors

    # pie options
    wp = { 'linewidth' : 1, 'edgecolor' : "black" }
    legend_properties = {'weight':'normal', "size":9}

    # A standard pie plot need to build legend later

    labs, counts = np.unique(labels, return_counts=True)

    tfig, tax = plt.subplots()
    patches, text = tax.pie(counts, colors = tcolors)
    plt.close(tfig)

    # get good grid, maybe...
    if nrow is None:
        n = int(np.floor(np.sqrt(len(titles))))
    else:
        n = nrow
    m = int(np.ceil(len(titles)/n))

    # Make figure and axes
    fig, axs = plt.subplots(n, m, figsize=(m*3, n*4))

    # plot subplots
    for cc, title in enumerate(titles):

        temp_labels = labels[cc*train_size:(cc+1)*train_size]

        # get labels and counts
        clab, ccount = np.unique(temp_labels,
                         return_counts=True)

        # select proper colors
        tcolor = [tcolors[np.where(ii == labs)[0][0]] for ii in clab]

        # operate on current axis
        cax = axs.flat[cc]
        cax.set_title(title, fontweight="bold")

        # plot subpie
        cax.pie(ccount,
                labels      = [ii if ii != -1 else "" for ii in clab],
                # autopct     = '%1.1f%%',
                # pctdistance = 0.6,
                startangle  = 40,
                shadow      = False,
                colors      = tcolor,
                textprops   = dict(fontweight ="bold"),
                wedgeprops  = wp,
                **plotargs,
                )

        # generate legend
        percentage = np.array([np.count_nonzero(temp_labels == ii) for ii in labs])
        percentage = 100*percentage/percentage.sum()
        leg_labels = ["{: >3d} : {: >4.1f}%".format(lab, percentage[cc])
                      for cc, lab in enumerate(labs)]

        cax.legend(patches, leg_labels, ncol=2, loc='lower center',
                   bbox_to_anchor=(0.5, -0.33), framealpha=1, edgecolor="k",
                   prop = legend_properties)

    fig.tight_layout()

    plt.show()

    if save:
        plt.savefig(save, dpi=300)

    return fig