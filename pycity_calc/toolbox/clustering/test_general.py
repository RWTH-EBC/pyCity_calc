import matplotlib.pyplot as plt
import pycity.classes.CityDistrict as cd
import os
import pycity_calc.cities.scripts.complex_city_generator as cocity
import pycity_calc.toolbox.clustering.ba_clustering as bacl
import pycity_calc.toolbox.clustering.experiments.kmeans_lloyd as kl
import pickle
import numpy as np
import networkx as nx
# import sympy.geometry.point as point
import shapely.geometry.point as point


def run_tobi_clust(city):
    """
    Run clustering algorithms of T. Beckhoelter.

    Parameters
    ----------
    city : object
        City object of pycity_calc (should include street network)

    Returns
    -------
    result : dict
        Cluster dictionary (key: cluster number; value: list (of node ids))
    """

    #  Cluster by street
    # result = bacl.get_clusters_street(district=city, street_type='real_simple',
    #                                   n_max=6, side_street_max=50,
    #                                   node_mode='street')

    #  Cluster by demands
    result = bacl.get_clusters_demand(district=quarter, n_max=8, assignment='group_energetic',
                                     grouping_mode='street', recentering=True, show_demand=False)

    return result


if __name__ == '__main__':

    filename = 'wm_res_non_DH.p'
    script_dir = os.path.dirname(__file__)
    path_load = os.path.join(script_dir, 'test_city_object', filename)

    # load pickle
    quarter = pickle.load(open(path_load, mode='rb'))

    #  Execute clustering
    dict_res = run_tobi_clust(city=quarter)

    print('Results dictionary:')
    print(dict_res)
