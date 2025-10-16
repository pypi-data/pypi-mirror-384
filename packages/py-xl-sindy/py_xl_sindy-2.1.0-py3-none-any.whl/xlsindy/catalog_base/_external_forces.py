"""
Contains the function responsible for the external forces part of the catalog.
"""

from typing import List
import numpy as np

from ..catalog import CatalogCategory

class ExternalForces(CatalogCategory):
    """
    External forces catalog. 

    Args:
        interlink_list (List[List[int]]) : Presence of the forces on each of the coordinate, 1-indexed can be negative for retroactive forces.
        symbol_matrix (np.ndarray) : Symbolic variable matrix for the system.
    """
    def __init__(
            self,
            interlink_list:List[List[int]],
            symbol_matrix:np.ndarray
            ):
        
        self.interlink_list = interlink_list
        self.symbolic_matrix = symbol_matrix
        ## Required variable
        self.catalog_length = 1
        self.num_coordinate = len(self.interlink_list)

    def create_solution_vector(self):
        return np.array(-1).reshape(1, 1)

    def expand_catalog(self):

        res = np.empty((1, self.num_coordinate), dtype=object)

        for i,additive in enumerate(self.interlink_list):

            for index in additive:

                if res[0,i] is None :

                    res[0,i] = np.sign(index)*self.symbolic_matrix[0,np.abs(index)-1]

                else:
                    
                    res[0,i] += np.sign(index)*self.symbolic_matrix[0,np.abs(index)-1]

        return res

    def label(self):
        """
        Return a place holder lab for the external forces.
        """
        
        return ["$$F_{{ext}}$$"]
    
    # externl forces are not separable by mask
    def separate_by_mask(self, mask):
        return ExternalForces(
            interlink_list=self.interlink_list,
            symbol_matrix=self.symbolic_matrix
        ),ExternalForces(
            interlink_list=self.interlink_list,
            symbol_matrix=self.symbolic_matrix
        )

