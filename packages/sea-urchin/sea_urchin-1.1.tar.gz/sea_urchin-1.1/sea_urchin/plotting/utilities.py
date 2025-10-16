#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  7 12:21:05 2025

@author: roncofaber
"""

import numpy as np

def align_bonds(atoms, atom1, atom6, atom3, tolerance=1e-6, max_iterations=100):
    def rotation_matrix_from_vectors(vec1, vec2):
        """ Find the rotation matrix that aligns vec1 to vec2 """
        a, b = (vec1 / np.linalg.norm(vec1)).reshape(3), (vec2 / np.linalg.norm(vec2)).reshape(3)
        v = np.cross(a, b)
        c = np.dot(a, b)
        s = np.linalg.norm(v)
        kmat = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        return np.eye(3) + kmat + kmat.dot(kmat) * ((1 - c) / (s ** 2))

    # center atoms to first
    atoms = atoms.copy()
    atoms.positions -= atoms.positions[atom1]
    
    # do it iteratively
    for ii in range(max_iterations):
        # Save the current positions to check for convergence
        old_positions = atoms.get_positions().copy()
        
        # Extract positions
        pos = atoms.get_positions()
        p1 = pos[atom1]
        p6 = pos[atom6]
        p3 = pos[atom3]
    
        # Compute bond vectors
        bond_1_6 = p6 - p1
        bond_1_3 = p3 - p1
    
        # Normalize bond vectors
        bond_1_6_norm = bond_1_6 / np.linalg.norm(bond_1_6)
        bond_1_3_norm = bond_1_3 / np.linalg.norm(bond_1_3)
    
        # Find the rotation matrix to align bond_1_6 with the z-axis
        atoms.rotate(bond_1_6_norm, [0,0,1])
    
        # Recompute the positions after rotation
        atoms.positions -= atoms.positions[atom1]
        pos = atoms.get_positions()
        p1 = pos[atom1]
        p3 = pos[atom3]
    
        bond_1_3 = p3 - p1
        bond_1_3_norm = bond_1_3 / np.linalg.norm(bond_1_3)
    
        # Project bond_1_3 onto the yz plane
        bond_1_3_yz = bond_1_3_norm.copy()
        bond_1_3_yz[0] = 0
        bond_1_3_yz_norm = bond_1_3_yz / np.linalg.norm(bond_1_3_yz)
        
        atoms.rotate(bond_1_3_norm, bond_1_3_yz_norm)
        
        # Check for convergence
        new_positions = atoms.get_positions()
        max_change = np.max(np.linalg.norm(new_positions - old_positions, axis=1))
        if max_change < tolerance:
            break

    return atoms