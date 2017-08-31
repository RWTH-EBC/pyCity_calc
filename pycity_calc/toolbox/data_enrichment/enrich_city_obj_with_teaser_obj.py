# coding=utf-8
from __future__ import division
import os
import sys
import pickle

import pycity_calc.examples.example_city as ex_city
import pycity_calc.toolbox.teaser_usage.teaser_usage as teaser


def pickle_dumper(obj, filepath):
    """
    This is a defensive way to write pickle.write, allowing for very large files on all platforms
    """
    max_bytes = 2 ** 31 - 1
    bytes_out = pickle.dumps(obj)
    n_bytes = sys.getsizeof(bytes_out)
    with open(filepath, 'wb') as f_out:
        for idx in range(0, n_bytes, max_bytes):
            f_out.write(bytes_out[idx:idx + max_bytes])


def pickle_loader(filepath):
    """
    This is a defensive way to write pickle.load, allowing for very large files on all platforms
    """
    max_bytes = 2 ** 31 - 1
    try:
        input_size = os.path.getsize(filepath)
        bytes_in = bytearray(0)
        with open(filepath, 'rb') as f_in:
            for _ in range(0, input_size, max_bytes):
                bytes_in += f_in.read(max_bytes)
        obj = pickle.loads(bytes_in)
    except:
        return None
    return obj




def run_example_city(osm_in_path, osm_out_path):
    """
    Create TypeBuildings form a pycity City Object

    Returns
    -------
    city_object : Pycity city object
        return the edited city object
    """
    pickle_loader(osm_in_path)

    # (open(path_to_file, 'rb'))
    city_object = pickle_loader(osm_in_path)    #ex_city.run_example()

    # create the teaser project
    project = teaser.create_teaser_project('Bonn_Bad_Godesberg')

    # create the typeBuilding
    teaser.create_teaser_typecity(project, city_object,
                                  generate_Output=True)

    pickle_dumper(city_object,osm_out_path)



    return city_object



if __name__ == '__main__':
    city_filename = 'city_osm_test.p'
    city_filename_output = 'city_osm_test_for_TEASER.p'

    this_path = os.path.dirname(os.path.abspath(__file__))

    osm_in_path = os.path.join(this_path, 'input', city_filename)
    osm_out_path = os.path.join(this_path, 'output', city_filename_output)


    #  Execute Example City and return the edited pyCity Object
    run_example_city(osm_in_path, osm_out_path)