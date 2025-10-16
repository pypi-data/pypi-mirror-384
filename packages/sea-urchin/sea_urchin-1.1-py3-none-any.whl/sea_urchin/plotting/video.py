#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 18:03:11 2023

@author: roncoroni
"""

import os
import subprocess
import glob

import ase

import numpy as np

import matplotlib.pyplot as plt

#%%
def make_video(clusters, rotation="", pad=0.35,
               name="su_video", figsize=(6,6)):

    old_folder = os.getcwd()
    folder     = "/tmp/sea_urchin_videos"

    if not os.path.exists(folder):
        os.makedirs(folder)


    fig, cax = plt.subplots(figsize=figsize)

    dummy_fig, dummy_ax = plt.subplots()

    centers = []
    custom_lim = np.array([0, -np.inf])
    for cc, cluster in enumerate(clusters):

        ase.visualize.plot.plot_atoms(cluster, ax=dummy_ax,
                                      rotation=rotation,
                                      show_unit_cell = 0)

        centers.append([(np.diff(dummy_ax.get_xlim())/2)[0],
                        (np.diff(dummy_ax.get_ylim())/2)[0]])

        custom_lim[1] = np.maximum(custom_lim[1],
                                   np.maximum(dummy_ax.get_xlim()[1],
                                              dummy_ax.get_ylim()[1]))
        dummy_ax.clear()
    plt.close()


    for cc, cluster in enumerate(clusters):

        # center all structures
        dx = np.diff(custom_lim)[0]/2 - centers[cc][0]
        dy = np.diff(custom_lim)[0]/2 - centers[cc][1]

        ase.visualize.plot.plot_atoms(cluster, ax=cax,
                                      rotation=rotation,
                                      show_unit_cell = 0,
                                      offset=(dx, dy))


        cax.axis('off')
        cax.set_xlim(custom_lim + [-pad, pad])
        cax.set_ylim(custom_lim + [-pad, pad])

        cax.set_xticklabels([])
        cax.set_yticklabels([])

        plt.savefig(folder + "/file%02d.png" % cc)

        cax.clear()
    plt.close()

    os.chdir(folder)
    subprocess.call([
        'ffmpeg', '-framerate', '12', '-y', '-i', 'file%02d.png', '-r', '30',
        '-pix_fmt', 'yuv420p', old_folder + '/{}.mp4'.format(name)
        ])

    for file_name in glob.glob("*.png"):
        os.remove(file_name)

    os.chdir(old_folder)

    return