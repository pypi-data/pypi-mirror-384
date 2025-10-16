#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 09:25:46 2021

@author: roncofaber
"""

import numpy as np

import FaberCOLVAR as col
import matplotlib.pyplot as plt

#%%

path = "/home/roncofaber/PhD_data/02_lbl_cluster/11_elephant_walker/01_dummy_walker_debug/10_control_walker/"
file = "colvar.out.colvars.mtd.hills.traj"
pmf_file = "colvar.out.pmf"

#%%





#%%


xlims = [0, 20]
ylims = [0, 20]
dx, dy = 0.05, 0.05


# pmf, xr, yr = col.generate_pmf_from_hilltraj(path+file, xlims, dx, ylims, dy)


pivotted, [xrange, yrange] = col.read_colvars_data(path + pmf_file)


col.plot_colvars_data(pivotted, xrange, yrange)
# col.plot_colvars_data(pmf, xr, yr)
#%%

# fs = 13


# fig, ax = plt.subplots(figsize=(7,6))

# ax.imshow(rsz_pmf.T, aspect="auto", origin="lower",
#            extent=(0, 3, 0, 20),
#            interpolation="none", cmap="viridis")

# ax.grid(linestyle="--")

# ax.set_xlabel("Coord.", fontsize=fs, fontweight="bold")
# ax.set_ylabel("Dist.", fontsize=fs, fontweight="bold")

# fig.show()



