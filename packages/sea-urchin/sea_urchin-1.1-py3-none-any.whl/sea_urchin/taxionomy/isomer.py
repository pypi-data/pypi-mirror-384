#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  8 09:53:43 2022

Classes that go well with the TaxSeaUrchin object.


@author: electrolyte-machine
"""

# numpy my best friend
# import numpy as np

# more stuff
import ase.visualize
import copy

# sea urchin stuff
# import sea_urchin.alignement.align as ali

#%%

class Isomer():

    def __init__(self,
                structures,
                representative = None
                ):

        # assign values and variables
        self.representative = representative
        self.formula        = structures[0].get_chemical_formula()
        self.hdb_type       = structures[0].info["hdb_type"]["label"]
        self.structures     = structures

        return

    # @staticmethod
    # def align(clusters, reference):
    #     return ali.align_clusters_in_parallel(reference, clusters)

    # # realign to a new reference
    # def realign_to_reference(self, reference):
    #     self.structures = self.align(self.structures, reference)
    #     return

    # view object
    def view(self):
        ase.visualize.view(self.structures)
        return

    # return copy
    def copy(self):
        """Return a copy."""
        return copy.deepcopy(self)