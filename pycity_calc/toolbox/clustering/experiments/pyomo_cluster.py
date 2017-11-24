#!/usr/bin/env python
# coding=utf-8
"""
Clustering buildings by position via optimization problem, modeled within
pyomoe, solved with gurobi
"""

import os
import pickle

import pycity_calc.visualization.city_visual as citvis
import pycity_calc.toolbox.networks.network_ops as netop

import pyomo.environ as pyo
import pyomo.opt as pyopt


def run_min_clust_dist(city, max_nb_b, max_b_dist):
    """
    Runs building position clustering via pyomo optimization

    Parameters
    ----------
    city : object
        City object of pycity_calc
    max_nb_b : int
        Maximum number of building nodes per cluster
    max_b_dist : float
        Maximal allowed distance between buildings per cluster

    Returns
    -------
    results : object
        Results object of solved pyomo model
    """

    list_x_pos = []
    list_y_pos = []
    #  Extract position lists
    for n in city.nodelist_building:
        list_x_pos.append(city.nodes[n]['position'].x)
        list_y_pos.append(city.nodes[n]['position'].y)

    # #  Calculate distance values
    # matrix_d = []
    # for n in city.nodelist_building:
    #     list_2 = []
    #     for m in city.nodelist_building:
    #         p1 = city.nodes[n]['position']
    #         p2 = city.nodes[m]['position']
    #         dist = netop.calc_point_distance(point_1=p1, point_2=p2)
    #         list_2.append(dist)
    #     matrix_d.append(list_2)

    #  Fixme: Instead of dist. precalc. calc distances within constraints
    dist_input = {}
    for i in range(len(city.nodelist_building)):
        b1 = city.nodelist_building[i]
        for j in range(len(city.nodelist_building)):
            b2 = city.nodelist_building[j]
            p1 = city.nodes[b1]['position']
            p2 = city.nodes[b2]['position']
            dist_input[b1, b2] = netop.calc_point_distance(point_1=p1,
                                                           point_2=p2)

    #  Create solver (gurobi)
    sol = pyopt.SolverFactory('gurobi')

    #  Init model
    model = pyo.ConcreteModel()

    #  General parameters
    #  #-------------------------------------------------
    #  Maximal allowed inter building distance
    model.d_max = pyo.Param(within=pyo.NonNegativeReals, initialize=max_b_dist)
    #  Maximal allowed number of buildings per cluster
    model.nb_b_max = pyo.Param(within=pyo.NonNegativeIntegers,
                               initialize=max_nb_b)
    #  Total number of buildings
    model.nb_b_total = pyo.Param(within=pyo.NonNegativeIntegers,
                                 initialize=len(city.nodelist_building))

    #  Sets
    #  #-------------------------------------------------
    #  Building node id set
    model.B = pyo.Set(domain=pyo.NonNegativeIntegers,
                      initialize=city.nodelist_building)

    #  TODO: Define as indexed var?
    #  Cluster id set
    model.Clust = pyo.Set(domain=pyo.NonNegativeIntegers)

    #  Set dependent parameters
    #  #-------------------------------------------------
    #  x-Positions (might be negative)
    model.x_pos = pyo.Param(model.B, initialize=list_x_pos)
    #  y-Positions (might be negative)
    model.y_pos = pyo.Param(model.B, initialize=list_y_pos)

    #  Distance value
    model.dist = pyo.Param(model.B, model.B, within=pyo.NonNegativeReals,
                           initialize=dist_input)

    #  Set dependent variables
    #  #-------------------------------------------------
    # #  Number of clusters
    # model.n_cl = pyo.Var(domain=pyo.NonNegativeIntegers)
    #  Decision variable (dependent on building id and cluster id)
    model.x = pyo.Var(model.B, model.Clust, domain=pyo.Binary)

    model.nb_clusters = pyo.Var(domain=pyo.NonNegativeIntegers)

    #  Objective function (minimize number of clusters)
    #  #-------------------------------------------------
    def ObjRule(model):
        return model.nb_clusters
    model.objective = pyo.Objective(rule=ObjRule)

    #  Constraints
    #  #-------------------------------------------------

    #  Keep inter cluster building distance below or equal to max value
    #  d_b_b <= d_max (for b unequals b)
    # model.c1 = pyo.Constraint(expr = model.dist[])
    model.d_max_constraint = pyo.ConstraintList()
    #  Loop over clusters
    for c in model.Clust:
        #  Loop over buildings once
        for b1 in model.B:
            #  Second building loop
            for b2 in model.B:
                model.d_max_constraint.add(
                    model.dist[b1][b2] * model.x[b1][c] * model.x[b2][c]
                    <= model.d_max)

    #  Keep sum of buidlings per cluster below or equal to max value
    #  n <= n_max
    model.n_max_constraint = pyo.ConstraintList()
    #  Loop over clusters
    for c in model.Clust:
        #  Sum of decision variables should be smaller or equal to max
        #  building number
        model.n_max_constraint.add(
            sum(model.x[b][c]) <= model.nb_b_max for b in model.B)

    #  d unequal 0 (i != j)?

    #  Check that every building can only be selected once
    #  for b in model.B for c in model.C --> x <= 1
    model.b_max_constraint = pyo.ConstraintList()
    #  Loop over buildings
    for b in model.B:
        model.b_max_constraint.add(
            sum(model.x[b][c]) <= 1 for c in model.Clust)

    #  Check that all buildings have been selected
    model.all_buildings = pyo.Constraint(
        expr=sum(model.x[b][c] ==
                 model.nb_b_total for b in model.B for c in model.Clust))

    #  Fixme: Add constraint (dependency model.nb_clusters to rest)

    #  Solve model
    #  #-------------------------------------------------
    results = sol.solve(model)

    return results

if __name__ == '__main__':

    #  Max. number of buildings per cluster
    max_nb_b = 2

    #  Max inter building distance
    max_b_dist = 40

    #  Name of city object file
    city_file = 'city_3_buildings.p'

    #  Generate path to city object file
    this_path = os.path.dirname(os.path.abspath(__file__))
    clust_path = os.path.dirname(this_path)
    city_file_path = os.path.join(clust_path, 'test_city_object', city_file)

    #  Load city object
    city = pickle.load(open(city_file_path, mode='rb'))

    print(city)
    print(city.nodelist_building)
    print(city.nodes(data=True))

    #  Plot city district
    plot_cit = False
    if plot_cit:
        citvis.plot_city_district(city=city)

    #  Run clustering
    run_min_clust_dist(city=city, max_nb_b=max_nb_b, max_b_dist=max_b_dist)
