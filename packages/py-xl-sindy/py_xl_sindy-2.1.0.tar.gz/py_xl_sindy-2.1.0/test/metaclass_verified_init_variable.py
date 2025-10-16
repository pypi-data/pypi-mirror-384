

import xlsindy
import numpy as np

class BadClass(xlsindy.catalog.CatalogCategory):
    def __init__(self, *args, **kwargs):

        #Missing variable
        print("This class should raise error")

    def create_solution_vector(self, *args, **kwargs):
        raise NotImplementedError

    def expand_catalog(self):
        raise NotImplementedError

    def label(self):
        raise NotImplementedError

class GoodClass(xlsindy.catalog.CatalogCategory):
    def __init__(self, *args, **kwargs):

        self.catalog_length = 2
        self.num_coordinate = 3

        print("This class shouldn't raise error")

    def create_solution_vector(self):
        # Check for the output compliance


        #return "prout"
        return np.ones((self.catalog_length,2))

    def expand_catalog(self):
        raise NotImplementedError

    def label(self):
        raise NotImplementedError


if __name__=="__main__":

    good_class = GoodClass()

    good_class.create_solution_vector()

    bad_class = BadClass()