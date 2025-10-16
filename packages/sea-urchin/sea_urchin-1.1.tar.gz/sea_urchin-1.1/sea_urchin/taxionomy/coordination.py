#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  8 09:53:43 2022

Classes that go well with the SeaUrchin object.


@author: electrolyte-machine
"""

# ase stuff
import ase
import ase.io
import ase.build
import ase.visualize

# copy
import copy

# numpy my best friend
import numpy as np

# electrolyte machine packages
import sea_urchin.utilities.su_cluster as suc
import sea_urchin.utilities.auxiliary_functions as aux

# other stuff
import numbers
#%%

class CoordCluster(ase.Atoms):

    # calculate coordination number
    def get_coordination_environment(self, atom2=None, d0=3.0, n=6, m=12):

        a1_idxs = aux.atoms_to_indexes(self, self.ref_atom)

        if atom2 is not None:
            a2_idxs = aux.atoms_to_indexes(self, atom2)
        else:
            a2_idxs = aux.atoms_to_indexes(self, self.coord_env)

        coordNum = []
        for idx in a1_idxs:

            dist = self.get_distances(idx, a2_idxs, mic=True)

            up = 1 - (dist/d0)**n
            dn = 1 - (dist/d0)**m
            coordNum.append(np.sum(up/dn))

        return coordNum[0] if len(coordNum) == 1 else coordNum

    def view(self):
        ase.visualize.view(self)
        return


    def __getitem__(self, i):
        """Return a subset of the atoms.

        i -- scalar integer, list of integers, or slice object
        describing which atoms to return.

        If i is a scalar, return an Atom object. If i is a list or a
        slice, return an Atoms object with the same cell, pbc, and
        other associated info as the original Atoms object. The
        indices of the constraints will be shuffled so that they match
        the indexing in the subset returned.

        """

        if isinstance(i, numbers.Integral):
            natoms = len(self)
            if i < -natoms or i >= natoms:
                raise IndexError('Index out of range.')

            return ase.Atom(atoms=self, index=i)

        elif not isinstance(i, slice):
            i = np.array(i)
            if len(i) == 0:
                i = np.array([], dtype=int)
            # if i is a mask
            if i.dtype == bool:
                if len(i) != len(self):
                    raise IndexError('Length of mask {} must equal '
                                     'number of atoms {}'
                                     .format(len(i), len(self)))
                i = np.arange(len(self))[i]

        # make new info
        new_info = dict(self.info)

        # reshuffle SU data
        if "mol_idx" in self.info:

            # fix slice, potentially slow TODO
            if isinstance(i, slice):
                indexes = list(range(*i.indices(len(self))))
            else:
                indexes = i

            for element in ['mol_idx', 'mol_typ', 'ato_typ', "id_print",
                            "ori_idx", "bnd_idx"]:
                if element not in self.info:
                    continue
                if self.info[element] is not None:
                    new_info[element] = [self.info[element][ii] for ii in indexes]
                else:
                    new_info[element] = None

        conadd = []
        # Constraints need to be deepcopied, but only the relevant ones.
        for con in copy.deepcopy(self.constraints):
            try:
                con.index_shuffle(self, i)
            except (IndexError, NotImplementedError):
                pass
            else:
                conadd.append(con)

        atoms = self.__class__(cell=self.cell, pbc=self.pbc, info=new_info,
                               # should be communicated to the slice as well
                               celldisp=self._celldisp)
        # TODO: Do we need to shuffle indices in adsorbate_info too?

        atoms.arrays = {}
        for name, a in self.arrays.items():
            atoms.arrays[name] = a[i].copy()

        atoms.constraints = conadd
        return atoms

    def insert(self, index, atom):
        """Append atom to end."""
        self.insert(self.__class__(index, [atom]))


    def sorted_cluster(self):
        sorted_idxs = suc.sort_cluster_indexes(self)
        return self[sorted_idxs].copy()