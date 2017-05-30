"""
This script gives a brief example of the usage of the Pickle class combining
with the creation of City
of ExtendedBuilding objects from pyCity
"""

import os
import pickle
import warnings
import pycity_calc.examples.example_city as city_ex
import pycity_calc.examples.example_building as bldg_ex


def save_pickle_city():
    """
    Creates a Pickle File of a city Object
    """

    city_object = city_ex.run_example()

    this_path = os.path.dirname(os.path.abspath(__file__))

    #  filename to save to
    save_filename = 'city_object2.p'

    #  Connect pathes to save path
    path_to_save = os.path.join(this_path, 'Pickle', save_filename)
    print(path_to_save)

    #  Pickle and dump city objects
    try:
        pickle.dump(city_object, open(path_to_save, 'wb'))
        print('Pickled and dumped city object at', path_to_save)
    except:
        warnings.warn('Could not pickle and save city object')


def save_pickle_building():
    """
    Creates a Pickle File of a Building Object
    """

    #  Execute example
    bldg_object = bldg_ex.run_example()

    this_path = os.path.dirname(os.path.abspath(__file__))

    #  filename to save to
    save_filename = 'Extended_Building1.p'

    #  Connect pathes to save path
    path_to_save = os.path.join(this_path, 'Pickle', save_filename)
    print(path_to_save)

    #  Pickle and dump city objects
    try:
        pickle.dump(bldg_object, open(path_to_save, 'wb'))
        print('Pickled and dumped Extended Building object at', path_to_save)
    except:
        warnings.warn('Could not pickle and save city object')


if __name__ == '__main__':
    # save_pickle_building()

    save_pickle_city()
