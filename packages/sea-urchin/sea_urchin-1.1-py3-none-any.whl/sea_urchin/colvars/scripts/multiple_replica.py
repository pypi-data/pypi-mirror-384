#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 27 11:22:00 2021

@author: roncofaber
"""

import matplotlib.pyplot as plt
import glob
import FaberCOLVAR as fco


# %%
baseenv = "/home/roncoroni/ETNA_SCRATCH/"
# baseenv = "/home/roncofaber/ETNA_SCRATCH/"

path_to_find = baseenv + "10_BH4_task_force/02_LAMMPS/01_Ca_1_BH4_2/12_dZ_Ca-G_CN_Ca-B/02_multiple_replica/*IDNR*"



dirlist = glob.glob(path_to_find)
dirlist.sort()

yshift = 0#-2.55


fs = 12
xlab = "Coord. Ca - O [-]"
ylab = r"Ca - G distance [$\AA$]"

# generate figure
fig, axs = plt.subplots(nrows=4, ncols=4, figsize=(11,9))

for cc, cdir in enumerate(dirlist):
    potential, [xrange, yrange] = fco.read_colvars_data(cdir + "/colvar.out.partial.pmf")

    cax = axs.flat[cc]


        # plot energy surface
    pos = cax.imshow(potential.T, aspect="auto", origin="lower",
               extent=(xrange[0], xrange[-1], yrange[0]+yshift, yrange[-1]+yshift),
               interpolation="none", cmap="viridis")

    cax.set_xlim(xrange[0], xrange[-1])
    cax.set_ylim(bottom=0)

    # if cc in [9, 10, 11]:
    #     cax.set_xlabel(xlab, fontsize=fs, fontweight="bold")
    # if cc in [0, 3, 6, 9]:
    #     cax.set_ylabel(ylab, fontsize=fs, fontweight="bold")
    # if cc in [2,5,8,11]:
    #     # colorbar
    #     cbar = plt.colorbar(pos, ax=cax)
    #     cbar.set_label(r"$\Delta$G [kT]", fontsize=fs+1, fontweight="bold")

fig.tight_layout()
fig.show()


#%%

fig, ax = plt.subplots(figsize=(8,6))

potential, [xrange, yrange] = fco.read_colvars_data(cdir + "/colvar.out.pmf")



    # plot energy surface
pos = ax.imshow(potential.T, aspect="auto", origin="lower",
           extent=(xrange[0], xrange[-1], yrange[0]+yshift, yrange[-1]+yshift),
           interpolation="none", cmap="viridis")

ax.set_xlim(xrange[0], xrange[-1])
ax.set_ylim(bottom=0)


ax.set_xlabel(xlab, fontsize=fs, fontweight="bold")
ax.set_ylabel(ylab, fontsize=fs, fontweight="bold")
cbar = plt.colorbar(pos, ax=ax)
cbar.set_label(r"$\Delta$G [kT]", fontsize=fs+1, fontweight="bold")

fig.tight_layout()
fig.show()

#%%

fco.plot_colvars_slice(potential, [6.025, 8.625, 10.025, 18.025],
                       xlabel = xlab,
                       title  = None,
                       zshift = 0,
                       label  = "dist: ")