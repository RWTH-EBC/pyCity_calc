#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 04 15:26:30 2016

@author: Nadine
"""

import pycity_calc.cities.city as City
import pycity_calc.extern_el_grid.Transformer as Transformer
import pycity_calc.data.El_grid.RealisticData as data
import numpy as np
from pypower.api import runpf, ppoption

import shapely.geometry.point as point

import pycity_calc.visualization.city_visual as visual
import networkx as nx
import os
import sys
import matplotlib.pyplot as plt
import pypower.idx_bus as idx_bus
import pypower.idx_brch as idx_brch
import pypower.idx_gen as idx_gen
import matplotlib.animation as ani

'''
IMPORTANT: if the argument 'save=True' in the function 'power_flow_calculation' the package pypower has to be adjusted:
           function 'savecase.py' -> line 101 -> change from 'fd = open(fname, "wb")' to 'fd = open(fname, "w")'
'''

class PowerGrid(object):
    """
    creates a power grid based on a suitable Kerber network for a defined set of buildings and provides functions for
    load flow calculations and evaluations
    """

    def __init__(self, building_list, environment, grid_type="ruraloverhead1"):
        """
        Parameters
        ----------
        building_list: list
            list of buildings of the district
        environment: environment
            object of class environment of pyCity
        gridtype: str
            type of the electrical grid: "ruraloverhead1", "ruraloverhead2", "ruralcable1", "ruralcable2",
                                         "village", "suburbcable1", "suburbcable2"

        References:
        -----------
        Dissertation:
            Georg Kerber - "Aufnahmefähigkeit von Niederspannungsverteilnetzen für die Einspeisung aus
                            Photovoltaikkleinanlagen"
        Bachelor Thesis:
            Dominik Mildt - "Modeling of Demand Response Concepts under Power Flow Constraints"

        """

        self._kind = "power_grid"
        self.environment = environment
        self.building_list = building_list
        self.grid_type = grid_type
        self.number_of_buildings = len(building_list)
        #   calculates number of busses according to the number of buildings
        if grid_type == "ruraloverhead1" or grid_type == "ruraloverhead2":
            self.numberofbusses = self.number_of_buildings + 2
        else:
            self.numberofbusses = 2 * self.number_of_buildings + 2
        # matrix of all connections between busses; line length in [km]
        self.line_lengths = np.ones((self.numberofbusses, self.numberofbusses))
        #   matrix of busses; column: buss, row: characteristics of the bus
        self.bus = np.zeros((self.numberofbusses, 13))
        #   matrix of generators; here: first dimension is one as there is just one transformer
        self.gen = np.zeros((1, 21))
        #   matrix of current lines
        self.branch = []
        #  list of transformers
        self.transformers = []
        #   medium voltage [kV]
        self.medium_voltage = 20
        #   power reference value [MVA]
        self.baseMVA = 10.0
        #   node_numbers (city district) and busses (power flow calculation)
        self.node_number_at_bus = np.zeros(self.numberofbusses)
        #   number of time steps in power flow calculation
        self.nb_time_steps_pf_calculation = None
        #   index of building list and node number e.g. : {0: 1001, 1:1002, 2:1003}
        self.index_building_list_node_number = {}

        #   create object city district
        self.city_district = City.City(self.environment)

    def create_reference_grid(self):
        """
        generation of a power grid for a predefined building list and grid type according to 'Kerber networks'
        """

        # creates the transformer at the medium voltage/low voltage connection
        self.create_slack_transformer()

        #   generation of network busses without considering specific electrical demands of entities (e.g. buildings)
        self.create_standard_busses()

        #   generation of electrical lines between busses regarding the different line lengths
        #   changes the parameter self.line_length
        self.create_lines()

        #   generation of branch data for pypower
        #   create branch for every self.line_length and add transformer
        self.create_branch()

    def create_city_district(self, network_id='power_grid', plot=False):
        """
        generation of a city district based on the reference grid

        Parameters
        ----------
        network_id: string, optional
            name of the network
        plot: boolean, optional
            to display the network
        """
        #   create reference grid
        self.create_reference_grid()
        #   add an electricity network to city_district
        self.city_district.add_network(network_type='electricity', network_id=network_id)
        #   distance between feeders; has to be bigger than 0.033 [km]
        distance_feeders = 0.1
        #   line length is 0.0, for drawing the network
        length_transformer = 0.05

        #   add first and second bus to city district
        # ------------------------------------------------------------------------------
        #   create transformer
        #   add network node
        self.node_number_at_bus[0] = self.city_district.add_network_node(network_type='electricity',
                                                                         network_id=network_id,
                                                                         position=point.Point(0, distance_feeders))

        #   add network node
        node_number = self.node_number_at_bus[0]
        new_point = point.Point(self.city_district.node[node_number]['position'].x+length_transformer, distance_feeders)
        self.node_number_at_bus[1] = self.city_district.add_network_node(network_type='electricity',
                                                                         network_id=network_id,
                                                                         position=new_point)

        #   add transformer
        self.city_district.add_edge(self.node_number_at_bus[0], self.node_number_at_bus[1], network_type='transformer')

        # ------------------------------------------------------------------------------
        #   set nodes and edges
        if self.grid_type == "ruraloverhead1" or self.grid_type == "ruraloverhead2":
            #   first building of the list
            next_building = 0
            #   to create the different lines of the radiation network
            factor = 0

            # ------------------------------------------------------------------------------
            #   create first node at every line of the radiation network
            for n in range(self.numberofbusses):
                if self.line_lengths[1][n] > 0:
                    node_number = self.node_number_at_bus[1]
                    #   position of the next node
                    pos_x = self.city_district.node[node_number]['position'].x + self.line_lengths[1][n]
                    new_point = point.Point(pos_x,
                                            self.city_district.node[node_number]['position'].y -
                                            self.city_district.node[node_number]['position'].y * factor)
                    #   add entity
                    self.node_number_at_bus[n] = self.city_district.addEntity(entity=self.building_list[next_building],
                                                                              position=new_point)
                    #   self.node_number_at_bus[end] is node number of new entity
                    self.index_building_list_node_number[next_building] = self.node_number_at_bus[n]

                    #   add edge
                    self.city_district.add_edge(node_number,
                                                self.node_number_at_bus[n],
                                                network_type='electricity')
                    factor += 1

            # ------------------------------------------------------------------------------
            for start in range(2, self.numberofbusses):
                for end in range(2, self.numberofbusses):
                    if self.line_lengths[start][end] > 0:
                        node_number = self.node_number_at_bus[start]
                        #   position of node 'end' depending on position of node 'start'
                        pos_x = self.city_district.node[node_number]['position'].x + self.line_lengths[start][end]
                        new_point = point.Point(pos_x, self.city_district.node[node_number]['position'].y)
                        #   add entity
                        self.node_number_at_bus[end] = \
                            self.city_district.addEntity(entity=self.building_list[next_building],
                                                         position=new_point)
                        #   self.node_number_at_bus[end] is node number of new entity
                        self.index_building_list_node_number[next_building] = self.node_number_at_bus[end]

                        #   add edge
                        self.city_district.add_edge(node_number,
                                                    self.node_number_at_bus[end],
                                                    network_type='electricity')
                        next_building += 1
        else:
            #   first building of the list
            next_building = 0
            #   to create the different lines of the radiation network
            factor = 0

            # ------------------------------------------------------------------------------
            #   create first node at every feeder of the radiation network
            for n in range(self.numberofbusses):
                if self.line_lengths[1][n] > 0:
                    node_number = self.node_number_at_bus[1]
                    #   position of the next node
                    pos_x = self.city_district.node[node_number]['position'].x + self.line_lengths[1][n]
                    new_point = point.Point(pos_x,
                                            self.city_district.node[node_number]['position'].y -
                                            self.city_district.node[node_number]['position'].y * factor)
                    #   add network node
                    self.node_number_at_bus[n] = self.city_district.add_network_node(network_type='electricity',
                                                                                     network_id=network_id,
                                                                                     position=new_point)
                    #   add edge
                    self.city_district.add_edge(node_number,
                                                self.node_number_at_bus[n],
                                                network_type='electricity')
                    factor += 1

            # ------------------------------------------------------------------------------
            for start in range(2, self.numberofbusses):
                for end in range(2, self.numberofbusses):
                    if self.line_lengths[start][end] > 0:
                        node_number = self.node_number_at_bus[start]
                        #   busses with even bus numbers are network nodes
                        #   busses with add bus numbers are entities
                        if end % 2 != 0:
                            #   position of node 'end' depending on position of node 'start'
                            pos_y = self.city_district.node[node_number]['position'].y - self.line_lengths[start][end]
                            new_point = point.Point(self.city_district.node[node_number]['position'].x, pos_y)
                            #   add entity
                            self.node_number_at_bus[end] = \
                                self.city_district.addEntity(entity=self.building_list[next_building],
                                                             position=new_point)
                            #   self.node_number_at_bus[end] is node number of new entity
                            self.index_building_list_node_number[next_building] = self.node_number_at_bus[end]

                            #   add edge
                            self.city_district.add_edge(node_number,
                                                        self.node_number_at_bus[end],
                                                        network_type='electricity')
                            next_building += 1
                        else:
                            #   position of node 'end' depending on position of node 'start'
                            pos_x = self.city_district.node[node_number]['position'].x + self.line_lengths[start][end]
                            new_point = point.Point(pos_x,
                                                    self.city_district.node[node_number]['position'].y)
                            #   add network node
                            self.node_number_at_bus[end] = \
                                self.city_district.add_network_node(network_type='electricity',
                                                                    network_id=network_id,
                                                                    position=new_point)
                            #   add edge
                            self.city_district.add_edge(node_number,
                                                        self.node_number_at_bus[end],
                                                        network_type='electricity')

        #   if plot is True, display network
        if plot:
            visual.plot_city_district(self.city_district, plot_elec_labels=True, plot_deg=True)

    def power_flow_calculation(self, start=0, end=None, save=False):
        """
        power flow calculation of a specific period
        returns the status of the network (voltage, angel, loads at each node)

        Parameters
        ----------
        start: int
            number of first time step of the considered time horizon
        end: int
            number of last time step of the considered time horizon
        save: boolean, optional
            if true, save results

        Returns
        -------
        results: array
            1.dimension: time step
            2.dimension: results of the power flow calculation of pypower
                         [0] - results: consists of 'bus', 'gen', 'branch'
                         [1] - success: indicates if the power flow calculation was successful (1) or not (0)
            -> output of runpf() are described in the pdf document 'results_pf'
        """
        #   default parameter of total number of time steps (end-start) is one year
        if end is None:
            end = self.environment.timer.timestepsTotal-1

        #   check if start and end are valid arguments
        assert start < self.environment.timer.timestepsTotal
        assert end <= self.environment.timer.timestepsTotal
        assert start <= end

        #   number of time steps
        self.nb_time_steps_pf_calculation = end-start+1

        #   loop over all time steps
        results = np.zeros(self.nb_time_steps_pf_calculation, dtype=object)
        for time_step in range(start, end+1):
            #   update real power demand of building busses
            for curr_bus in range(len(self.node_number_at_bus)):
                node_number = self.node_number_at_bus[curr_bus]
                if node_number in self.city_district.node:
                    #   'node_type' == 'building' can be a 'building', 'pv' or 'windenergyconverter'
                    if self.city_district.node[node_number]['node_type'] == 'building':
                        #   check if node is a building
                        if self.city_district.node[node_number]['entity']._kind == 'building':
                            building = self.city_district.node[node_number]['entity']
                            #   value of 'get_electric_power_curve()' are in Watt; W/10^6=MW
                            #  TODO: Extend function to get 'building' residual load
                            power_curve = building.get_electric_power_curve()
                            #  TODO: If reactive power is required, use curr_bus index 3
                            self.bus[curr_bus][2] = power_curve[time_step]/(10**6)
            #   input file for load flow calculation according to example 'case9' of pyPower
            ppc = {"version": '2', "baseMVA": self.baseMVA, "bus": np.array(self.bus), "gen": np.array(self.gen),
                   "branch": np.array(self.branch)}

            #   additional options
            ppopt = ppoption()
            #   controls printing of results: -1 - individual flags control what prints,
            #                                  0 - don't print anything (overrides individual flags),
            #                                  1 - print everything (overrides individual flags)
            ppopt['OUT_ALL'] = 0
            #   amount of progress info printed: 0 - print no progress info,
            #                                    1 - print a little progress info,
            #                                    2 - print a lot of progress info,
            #                                    3 - print all progress info
            ppopt['VERBOSE'] = 0

            #   check if results should be saved
            if save:
                #   save power flow calculation results by using a function of pyPower
                path_pycity_calc = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                path_directory = path_pycity_calc + '\extern_el_grid\\results\\results_power_flow\\'
                if not os.path.exists(path_directory):
                    #   create directory
                    os.makedirs(path_directory)
                path = path_directory + 'time_step_'+ str(time_step)
                #   run power flow calculation and save results
                results[time_step-start] = runpf(ppc, ppopt, solvedcase=path)
            else:
                #   run power flow calculation
                results[time_step-start] = runpf(ppc, ppopt)

        return results

    def power_flow_evaluation(self, results):
        """
        generates a new city district with node attributes 'voltage' 'current' 'power'

        Parameters
        ----------
        results: array
            1.dimension: time step
            2.dimension: results of the power flow calculation of pypower
                         [0] - results: which consists of 'bus', 'gen', 'branch'
                         [1] - success: which indicates if the power flow calculation was successful (1) or not (0)
            -> output of runpf() are described in the pdf document 'results_pf'

        Returns
        -------
        res_city_district: pycity_calc.cities.City
            city district with additional attributes
            nodes: 'voltage' in [kV],
                   'max voltage' in [kV],
                   'min voltage' in [kV],
                   'real power demand' in [kW]
            edges -> branch: 'current' in [kA],
                             'max current' in [kA]
            edges -> transformer: 'apparent power' in [MVA],
                                  'max apparent power' in [MVA]

        """
        # ------------------------------------------------------------------------------
        #   add arrays for dictionary keys
        #   copy city_district for evaluation results
        res_city_district = self.city_district.copy()

        #   voltage
        for curr_bus in self.bus:
            #   get corresponding node_number
            node_number = self.node_number_at_bus[curr_bus[idx_bus.BUS_I]-1]
            #   add dictionary key 'voltage' with an array to every node
            res_city_district.add_node(node_number,
                                       voltage=np.zeros(len(results)))
            #   add dictionary key 'min_voltage' with an array to every node
            res_city_district.add_node(node_number,
                                       min_voltage=np.zeros(len(results)))
            #   add dictionary key 'max_voltage' with an array to every node
            res_city_district.add_node(node_number,
                                       max_voltage=np.zeros(len(results)))
            #   add dictionary key 'power_demand' with an array to every node
            res_city_district.add_node(node_number,
                                       real_power_demand=np.zeros(len(results)))

        #   current
        for curr_brch in self.branch:
            if curr_brch[idx_brch.TAP] == 0 :
                #   get corresponding node_number
                start_number = self.node_number_at_bus[curr_brch[idx_brch.F_BUS]-1]
                end_number = self.node_number_at_bus[curr_brch[idx_brch.T_BUS]-1]
                #   add dictionary key 'current' with an array to every node
                res_city_district.add_edge(start_number, end_number, current=np.zeros(len(results)))
                #   add dictionary key 'max_current' with an array to every node
                res_city_district.add_edge(start_number, end_number, max_current=np.zeros(len(results)))

        #   workload at transformer
        for curr_brch in self.branch:
            if curr_brch[idx_brch.TAP] != 0 :
                #   get corresponding node_number
                start_number = self.node_number_at_bus[curr_brch[idx_brch.F_BUS]-1]
                end_number = self.node_number_at_bus[curr_brch[idx_brch.T_BUS]-1]
                #   add dictionary key 'power' with an array to every node
                res_city_district.add_edge(start_number, end_number, power=np.zeros(len(results)))
                #   add dictionary key 'max_power' with an array to every node
                res_city_district.add_edge(start_number, end_number, max_power=np.zeros(len(results)))

        # ------------------------------------------------------------------------------
        #  power flow evaluation
        for time_step in range(len(results)):
            #    check if power flow calculation was successful
            if results[time_step][1] == 1:
                #   results_evaluation := voltage, losses, current, gen_real_power, gen_reactive_power
                res_city_district = self.evaluation_time_step(results[time_step][0], res_city_district, time_step)
            else:
                print('power flow calculation at time step ' + str(time_step) + ' was not successful!')

        return res_city_district

    def evaluation_time_step(self, results, res_city_district, time_step):
        """
        power flow evaluation of a single time step

        Parameter
        ---------
        results: dict
            bus, branch and gen data of the network
        res_city_district: pycity_calc.cities.City
            city district with the additional attributes:
            nodes: 'voltage' in [kV],
                   'max voltage' in [kV],
                   'min voltage' in [kV],
                   'real power demand' in [kW]
            edges -> branch: 'current' in [kA],
                             'max current' in [kA]
            edges -> transformer: 'apparent power' in [MVA],
                                  'max apparent power' in [MVA]
        time_step: int
            current time step
        """

        #   convert to internal indexing
        bus_results = results["bus"]
        branch_results = results["branch"]

        #   add voltage at every bus
        for curr_bus in bus_results:
            node_number = self.node_number_at_bus[curr_bus[idx_bus.BUS_I]-1]
            if node_number in self.city_district.node:
                #   voltage in [kV]
                res_city_district.node[node_number]['voltage'][time_step] = curr_bus[idx_bus.VM]*curr_bus[idx_bus.BASE_KV]
                #   min voltage in [kV]
                res_city_district.node[node_number]['min_voltage'][time_step] = curr_bus[idx_bus.VMIN]*curr_bus[idx_bus.BASE_KV]
                #   max voltage in [kV]
                res_city_district.node[node_number]['max_voltage'][time_step] = curr_bus[idx_bus.VMAX]*curr_bus[idx_bus.BASE_KV]
                #   real power demand in [kW]
                res_city_district.node[node_number]['real_power_demand'][time_step] = curr_bus[idx_bus.PD]*(10**3)

        #   add current at every electrical line
        for curr_brch in branch_results:
            #   check if branch is an electrical line
            if curr_brch[idx_brch.TAP] == 0:
                #   calculate apparent power
                apparent_power = abs(curr_brch[idx_brch.PF]+1j*curr_brch[idx_brch.QF])
                for curr_bus in bus_results:
                    if curr_brch[idx_brch.F_BUS] == curr_bus[idx_bus.BUS_I]:
                        f_bus_voltage = curr_bus[idx_bus.VM]
                        f_bus_base_kv = curr_bus[idx_bus.BASE_KV]
                #   calculate current at electrical line
                current_branch = apparent_power/(np.sqrt(3)*f_bus_voltage*f_bus_base_kv)
                #   save results in edge
                start_number = self.node_number_at_bus[curr_brch[idx_brch.F_BUS]-1]
                end_number = self.node_number_at_bus[curr_brch[idx_brch.T_BUS]-1]
                #   current in [kA]
                res_city_district.edge[start_number][end_number]['current'][time_step] = current_branch
                res_city_district.edge[start_number][end_number]['max_current'][time_step] = curr_brch[idx_brch.RATE_A]/(np.sqrt(3)*curr_bus[idx_bus.BASE_KV])

        #   add apparent power to transformer
        for curr_brch in branch_results:
            #   check if branch is a transformer
            if curr_brch[idx_brch.TAP] != 0:
                #   calculate apparent power
                apparent_power = abs(curr_brch[idx_brch.PF]+1j*curr_brch[idx_brch.QF])
                #   save results in edge
                start_number = self.node_number_at_bus[curr_brch[idx_brch.F_BUS]-1]
                end_number = self.node_number_at_bus[curr_brch[idx_brch.T_BUS]-1]
                #   power in [MVA]
                res_city_district.edge[start_number][end_number]['power'][time_step] = apparent_power
                res_city_district.edge[start_number][end_number]['max_power'][time_step] = curr_brch[idx_brch.RATE_A]

        return res_city_district

    def check_off_limit_conditions(self, res_city_district, fname='off_limt_conditions'):
        """
        check results for off-limit conditions and save results

        Parameters
        ----------
        res_city_district: pycity_calc.cities.City
            city district with the additional attributes:
            nodes: 'voltage' in [kV],
                   'max voltage' in [kV],
                   'min voltage' in [kV],
                   'real power demand' in [kW]
            edges -> branch: 'current' in [kA],
                             'max current' in [kA]
            edges -> transformer: 'apparent power' in [MVA],
                                  'max apparent power' in [MVA]
        fname: string, optional
            name of the file
        """

        #   get path
        path_pycity_calc = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        path_results = str(path_pycity_calc) + '\\extern_el_grid\\results\\'
        #   check if directory exists
        if not os.path.exists(path_results):
            #   create directory
            os.makedirs(path_results)
        path_directory = path_results + '\\' + fname + '.txt'
        #   open file
        fd = open(path_directory, 'w')

        for time_step in range(self.nb_time_steps_pf_calculation):
            #   flag for off-limit conditions
            off_limit = False

            #   time step
            fd.write('================================================================================\n')
            fd.write('time step: ')
            fd.write('%6d\n' % time_step)

            #   voltage deviation
            fd.write('node number           voltage [kV]        min voltage [kV]       max voltage [kV]\n')
            off_limit_v = False
            for curr_bus in self.bus:
                node_number = self.node_number_at_bus[curr_bus[idx_bus.BUS_I]-1]
                voltage = res_city_district.node[node_number]['voltage'][time_step]
                max_voltage = curr_bus[idx_bus.VMAX]*curr_bus[idx_bus.BASE_KV]
                min_voltage = curr_bus[idx_bus.VMIN]*curr_bus[idx_bus.BASE_KV]
                if voltage > max_voltage or voltage < min_voltage:
                    off_limit = True
                    off_limit_v = True
                    fd.write('%8d%22.4f%20.4f%22.4f\n' %
                             (node_number, voltage, min_voltage, max_voltage))
            if not off_limit_v:
                fd.write('%6s%22s%20s%20s\n' %
                         ('-', '-', '-', '-'))
            #   current
            fd.write('from node             to node             current [kA]           max current [kA]\n')
            off_limit_c = False
            for curr_branch in self.branch:
                #   check if branch is an electrical line
                if curr_branch[idx_brch.TAP] == 0:
                    f_node = self.node_number_at_bus[curr_branch[idx_brch.F_BUS]-1]
                    t_node = self.node_number_at_bus[curr_branch[idx_brch.T_BUS]-1]
                    current_branch = res_city_district.edge[f_node][t_node]['current'][time_step]
                    for curr_bus in self.bus:
                        if curr_branch[idx_brch.F_BUS] == curr_bus[idx_bus.BUS_I]:
                            current_max = curr_branch[idx_brch.RATE_A]/(np.sqrt(3)*curr_bus[idx_bus.BASE_KV])
                    if current_branch > current_max:
                        off_limit = True
                        off_limit_c = True
                        fd.write('%8d%20d%22.4f%22.4f\n' %
                                 (f_node, t_node, current_branch, current_max))
            if not off_limit_c:
                fd.write('%6s%22s%20s%20s\n' %
                         ('-', '-', '-', '-'))

            #   transformer
            fd.write('from node             to node             apparent power [MVA]   max apparent power [MVA]\n')
            off_limit_t = False
            for curr_brch in self.branch:
                #   check if branch is a transformer
                if curr_brch[idx_brch.TAP] != 0:
                    f_node = self.node_number_at_bus[curr_brch[idx_brch.F_BUS]-1]
                    t_node = self.node_number_at_bus[curr_brch[idx_brch.T_BUS]-1]
                    power = res_city_district.edge[f_node][t_node]['power'][time_step]
                    if power > curr_brch[idx_brch.RATE_A]:
                        off_limit = True
                        off_limit_t = True
                        fd.write('%8d%20d%22.4f%22.4f\n' %
                                 (f_node, t_node, power, curr_branch[idx_brch.RATE_A]))
            if not off_limit_t:
                fd.write('%6s%22s%20s%20s\n' %
                         ('-', '-', '-', '-'))

        #   check if there are any off-limit conditions
        if not off_limit:
            print('no off-limit conditions')

    def create_standard_busses(self):
        """
        generation of network busses without considering specific electrical demands of entities (e.g. buildings)
        buildings are modelled as PQ-busses
        the ref bus has to be a gen bus that is in service (see bustypes.py)
        """

        #   index of the next bus
        static_bus_index = 1

        # ------------------------------------------------------------------------------
        #   creation of the slack bus at medium voltage at static_bus_index 1
        #   primary winding of the transformer

        #   bus index (BUS_I); here: 1
        self.bus[0][0] = static_bus_index
        #   bus type (BUS_TYPE): 1 = PQ, 2 = PV, 3 = ref, 4 = isolated
        self.bus[0][1] = 3.0
        #   real power demand at bus (PD), initialized to 0
        self.bus[0][2] = 0.0
        #   reactive power demand at bus (QD), initialized to 0
        self.bus[0][3] = 0.0
        #   shunt conductance (GS)
        self.bus[0][4] = 0.0
        #   shunt susceptance (BS)
        self.bus[0][5] = 0.0
        #   area of the bus (BUS_AREA)
        self.bus[0][6] = 1.0
        #   voltage magnitude at bus (VM) in p.u.
        self.bus[0][7] = 1.0
        #   voltage angle at bus (VA) in degrees
        self.bus[0][8] = 0.0
        #   base voltage (BASE_KV in kV)
        self.bus[0][9] = self.medium_voltage
        #   bus loss zone (ZONE)
        self.bus[0][10] = 1.0
        #   bus maximum voltage magnitude (VMAX) in p.u.
        self.bus[0][11] = 1.06
        #   bus minimum voltage magnitude (VMIN) in p.u.
        self.bus[0][12] = 0.98

        #   bus index of generator (GEN_BUS); here: 1
        self.gen[0][0] = static_bus_index
        #   real power output (PG) in MW
        self.gen[0][1] = 0.0
        #   reactive power output (QG) in MVAr
        self.gen[0][2] = 0.0
        #   maximum reactive power output (QMAX) in MVAr; here: unknown
        self.gen[0][3] = 0.0
        #   minimum reactive power output (QMIN) in MVAr; here: unknown
        self.gen[0][4] = 0.0
        #   voltage magnitude setpoint (VG) in p.u.
        self.gen[0][5] = 1.0
        #   total MVA base of machine (MBASE)
        self.gen[0][6] = self.baseMVA
        #   status of the machine (GEN_STATUS); 1 = in service, 0 = out of service
        self.gen[0][7] = 1.0
        #   maximum real power output (PMAX); here: unknown
        self.gen[0][8] = 0.0
        #   minimum real power output (PMIN); here: unknown
        self.gen[0][9] = 0.0

        # ------------------------------------------------------------------------------
        static_bus_index += 1

        #   creation of the bus bar bus at static_bus_index := 2
        #   secondary winding of the transformer

        #   bus index (BUS_I); here: 2
        self.bus[1][0] = static_bus_index
        #   bus type (BUS_TYPE): 1 = PQ, 2 = PV, 3 = ref, 4 = isolated
        self.bus[1][1] = 1.0
        #   real power demand at bus (PD), initialized to 0
        self.bus[1][2] = 0.0
        #   reactive power demand at bus (QD), initialized to 0
        self.bus[1][3] = 0.0
        #   shunt conductance (GS)
        self.bus[1][4] = 0.0
        #   shunt susceptance (BS)
        self.bus[1][5] = 0.0
        #   area of the bus (BUS_AREA)
        self.bus[1][6] = 1.0
        #   voltage magnitude at bus (VM) in p.u.
        self.bus[1][7] = 1.0
        #   voltage angle at bus (VA) in degrees
        self.bus[1][8] = -self.transformers[0].getShift()
        #   bus loss zone (ZONE)
        self.bus[1][9] = 0.400
        #   bus loss zone (ZONE)
        self.bus[1][10] = 1.0
        #   bus maximum voltage magnitude (VMAX) in p.u.
        self.bus[1][11] = 1.1
        #   bus minimum voltage magnitude (VMIN) in p.u.
        self.bus[1][12] = 0.9

        # ----------------------------------------------------------------------
        static_bus_index += 1

        #   generation of the other busses
        #   busses 1 and 2 are already created

        for counter in range((self.numberofbusses - 2)):
            i = counter + 2

            #   busindex (BUS_I)
            self.bus[i][0] = static_bus_index

            #   bustype (BUS_TYPE), PQ node
            self.bus[i][1] = 1.0

            #   real power demand at bus (PD), initialized to 0
            self.bus[i][2] = 0.0

            #   reactive power demand at bus (QD), initialized to 0
            self.bus[i][3] = 0.0

            #   shunt conductance (GS)
            self.bus[i][4] = 0.0

            #   shunt susceptance (BS)
            self.bus[i][5] = 0.0

            #   area of the bus (BUS_AREA)
            self.bus[i][6] = 1.0

            #   voltage magnitude at bus (VM) in p.u.
            self.bus[i][7] = 1.0

            #   voltage angle at bus (VA) in degrees
            self.bus[i][8] = -self.transformers[0].getShift()

            #   base voltage (BASE_KV in kV)
            self.bus[i][9] = 0.400

            #   bus loss zone (ZONE)
            self.bus[i][10] = 1.0

            #   bus maximum voltage magnitude (VMAX) in p.u.
            self.bus[i][11] = 1.1

            #   bus minimum voltage magnitude (VMIN) in p.u.
            self.bus[i][12] = 0.9

            #   increment to the current bus index
            static_bus_index += 1

    def create_slack_transformer(self):
        """
        Creates a transformer for the the connection of the medium voltage grid to the low voltage grid
        """

        #   select type of transformer according to the grid type
        if self.grid_type == "ruraloverhead1":
            transformer_type = "DIN42500(Oil) 160kVA " + str(self.medium_voltage) + "kV"

        elif self.grid_type == "ruraloverhead2":
            transformer_type = "DIN42500(Oil) 100kVA " + str(self.medium_voltage) + "kV"

        elif self.grid_type == "ruralcable1":
            transformer_type = "DIN42500(Oil) 100kVA " + str(self.medium_voltage) + "kV"

        elif self.grid_type == "ruralcable2":
            transformer_type = "DIN42500(Oil) 160kVA " + str(self.medium_voltage) + "kV"

        elif self.grid_type == "village":
            transformer_type = "DIN42500(Oil) 400kVA " + str(self.medium_voltage) + "kV"

        elif self.grid_type == "suburbcable1":
            transformer_type = "DIN42500(Oil) 630kVA " + str(self.medium_voltage) + "kV"

        elif self.grid_type == "suburbcable2":
            transformer_type = "DIN42500(Oil) 630kVA " + str(self.medium_voltage) + "kV"

        try:
            #   create transformer object
            transformer = Transformer.Transformer("Gridtransformer", transformer_type, 1, 2)
            #   add transformer to the list of transformers
            self.transformers.append(transformer)
        except UnboundLocalError:
            print('grid type ' + self.grid_type + ' is not a valid argument for grid_type.')
            sys.exit()

    def create_lines(self):
        """
        generation of electrical lines between busses regarding the different line lengths
        changes the parameter self.line_length
        """
        #   sets all values to -1, which means there is no connection
        self.line_lengths = np.negative(self.line_lengths)

        #   medium/low voltage connection; transformer will be added later
        self.line_lengths[0][1] = 0.0

        # ----------------------------------------------------------------------
        #   create electrical lines depending on the grid type
        if self.grid_type == "ruraloverhead1":
            self.create_overhead_line(1, self.number_of_buildings, 0.021)
            return

        elif self.grid_type == "ruraloverhead2":
            self.create_overhead_line(1, min([2, self.number_of_buildings]), 0.081)
            if self.number_of_buildings > 2:
                curr_building = 3
                while self.number_of_buildings - curr_building + 1 > 5:
                    self.create_overhead_line(curr_building, 6, 0.038)
                    curr_building += 6

                if self.number_of_buildings - curr_building + 1 > 0:
                    self.create_overhead_line(curr_building, self.number_of_buildings - curr_building + 1, 0.038)
            return

        elif self.grid_type == "ruralcable1":
            self.create_tie_line(1, min([2, self.number_of_buildings]), 0.175, 0.018, 0.033)
            if self.number_of_buildings > 2:
                curr_building = 3
                while self.number_of_buildings - curr_building + 1 > 5:
                    self.create_tie_line(curr_building, 6, 0.082, 0.018, 0.033)
                    curr_building += 6

                if self.number_of_buildings - curr_building + 1 > 0:
                    self.create_tie_line(curr_building,
                                         self.number_of_buildings - curr_building + 1,
                                         0.082,
                                         0.018,
                                         0.033)

        elif self.grid_type == "ruralcable2":
            self.create_tie_line(1, min([2, self.number_of_buildings]), 0.175, 0.018, 0.033)
            if self.number_of_buildings > 2:
                curr_building = 3
                while self.number_of_buildings - curr_building + 1 > 11:
                    self.create_tie_line(curr_building, 12, 0.053, 0.018, 0.033)
                    curr_building += 12

                if self.number_of_buildings - curr_building + 1 > 0:
                    self.create_tie_line(curr_building,
                                         self.number_of_buildings - curr_building + 1,
                                         0.053,
                                         0.018,
                                         0.033)

        elif self.grid_type == "village":
            curr_building = 1
            if self.number_of_buildings - curr_building + 1 > 8:
                self.create_tie_line(curr_building, 9, 0.040, 0.015, 0.031)
                curr_building += 9
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.040, 0.015, 0.031)
                return

            if self.number_of_buildings - curr_building + 1 > 9:
                self.create_tie_line(curr_building, 9, 0.040, 0.015, 0.031)
                curr_building += 9
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.040, 0.015, 0.031)
                return

            if self.number_of_buildings - curr_building + 1 > 15:
                self.create_tie_line(curr_building, 16, 0.029, 0.015, 0.031)
                curr_building += 16
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.029, 0.015, 0.031)
                return

            if self.number_of_buildings - curr_building + 1 > 11:
                self.create_tie_line(curr_building, 12, 0.032, 0.015, 0.031)
                curr_building += 12
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.032, 0.015, 0.031)
                return

            if self.number_of_buildings - curr_building + 1 > 6:
                self.create_tie_line(curr_building, 7, 0.043, 0.015, 0.031)
                curr_building += 7
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.043, 0.015, 0.031)
                return

            if self.number_of_buildings - curr_building + 1 > 3:
                self.create_tie_line(curr_building, 4, 0.064, 0.015, 0.031)
                curr_building += 4
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.064, 0.015, 0.031)
                return

            while self.number_of_buildings - curr_building + 1 > 8:
                self.create_tie_line(curr_building, 9, 0.040, 0.015, 0.031)
                curr_building += 9

            if self.number_of_buildings - curr_building + 1 > 0:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.040, 0.015, 0.031)

        elif self.grid_type == "suburbcable1":

            curr_building = 1
            if self.number_of_buildings - curr_building + 1 > 13:
                self.create_tie_line(curr_building, 14, 0.021, 0.11)
                curr_building += 14
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.021, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 13:
                self.create_tie_line(curr_building, 14, 0.021, 0.11)
                curr_building += 14
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.021, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 13:
                self.create_tie_line(curr_building, 14, 0.021, 0.11)
                curr_building += 14
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.021, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 18:
                self.create_tie_line(curr_building, 19, 0.017, 0.11)
                curr_building += 19
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.017, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 18:
                self.create_tie_line(curr_building, 19, 0.017, 0.11)
                curr_building += 19
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.017, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 9:
                self.create_tie_line(curr_building, 10, 0.025, 0.11)
                curr_building += 10
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.025, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 9:
                self.create_tie_line(curr_building, 10, 0.025, 0.11)
                curr_building += 10
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.025, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 9:
                self.create_tie_line(curr_building, 10, 0.025, 0.11)
                curr_building += 10
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.025, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 31:
                self.create_tie_line(curr_building, 32, 0.011, 0.11)
                curr_building += 32
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.011, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 3:
                self.create_tie_line(curr_building, 4, 0.060, 0.11)
                curr_building += 4
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.060, 0.11)
                return

            while self.number_of_buildings - curr_building + 1 > 13:
                self.create_tie_line(curr_building, 14, 0.021, 0.11)
                curr_building += 14

            if self.number_of_buildings - curr_building + 1 > 0:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.021, 0.11)

        elif self.grid_type == "suburbcable2":

            curr_building = 1
            if self.number_of_buildings - curr_building + 1 > 14:
                self.create_tie_line(curr_building, 15, 0.023, 0.11)
                curr_building += 15
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.023, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 14:
                self.create_tie_line(curr_building, 15, 0.023, 0.11)
                curr_building += 15
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.023, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 14:
                self.create_tie_line(curr_building, 15, 0.023, 0.11)
                curr_building += 15
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.023, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 19:
                self.create_tie_line(curr_building, 20, 0.020, 0.11)
                curr_building += 20
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.020, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 19:
                self.create_tie_line(curr_building, 20, 0.020, 0.11)
                curr_building += 20
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.020, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 10:
                self.create_tie_line(curr_building, 11, 0.026, 0.11)
                curr_building += 11
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.026, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 10:
                self.create_tie_line(curr_building, 11, 0.026, 0.11)
                curr_building += 11
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.026, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 31:
                self.create_tie_line(curr_building, 32, 0.014, 0.11)
                curr_building += 32
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.014, 0.11)
                return

            if self.number_of_buildings - curr_building + 1 > 4:
                self.create_tie_line(curr_building, 5, 0.050, 0.11)
                curr_building += 5
            else:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.050, 0.11)
                return

            while self.number_of_buildings - curr_building + 1 > 14:
                self.create_tie_line(curr_building, 15, 0.023, 0.11)
                curr_building += 15

            if self.number_of_buildings - curr_building + 1 > 0:
                self.create_tie_line(curr_building, self.number_of_buildings - curr_building + 1, 0.023, 0.11)

    def create_overhead_line(self, start_building, number_of_buildings, main_length):
        """
        Creates a single overhead tie line connected to the bus bar with a given number of nodes and a
        constant line length
        Creates one line for a radial overhead network
        """
        curr_bus = start_building + 1
        if number_of_buildings > 0:
            self.line_lengths[1][curr_bus] = main_length
            if number_of_buildings > 1:
                for i in range(number_of_buildings - 1):
                    curr_bus += 1
                    self.line_lengths[curr_bus - 1][curr_bus] = main_length

    def create_tie_line(self, start_building, number_of_buildings, main_length, closure=0.0, cable=0.0):
        """
        Creates a single cable tie line connected to the bus bar with a given number of nodes and a constant line length
        Creates one line for a radial cable network.
        """

        curr_bus = start_building * 2
        if number_of_buildings > 0:
            self.line_lengths[1][curr_bus] = main_length
            self.line_lengths[curr_bus][curr_bus + 1] = closure
            if number_of_buildings > 1:
                for i in range((number_of_buildings - 1)):
                    curr_bus += 2
                    #   mainline
                    self.line_lengths[curr_bus - 2][curr_bus] = main_length
                    if cable != 0:
                        if (i % 2) == 0:
                            #   cable connection to household (0 for overhead lines)
                            self.line_lengths[curr_bus][curr_bus + 1] = cable
                        else:
                            self.line_lengths[curr_bus][curr_bus + 1] = closure
                    else:
                        #   closure connection to household (0 for overhead lines)
                        self.line_lengths[curr_bus][curr_bus + 1] = closure

    def create_branch(self):
        """
        Function that creates the branch data table needed for pypower calculation
        Creates the branch data for a network with set line_lengths and grid transformer, based on the grid type and 
        using examplified technical cable data.
        """
        
        # creating the connection between medium and low voltage grid
        counter = 0
        maintype = None
        contype1 = None
        contype2 = None

        # chooses cable types from provided grid equipment data
        if self.grid_type == "ruraloverhead1":
            maintype = "NFA2X 4X70"

        elif self.grid_type == "ruraloverhead2":
            maintype = "NFA2X 4X70"

        elif self.grid_type == "ruralcable1":
            maintype = "NAYY 4X150"
            contype1 = "NAYY 4X50"
            contype2 = "NAYY 4X50"

        elif self.grid_type == "ruralcable2":
            maintype = "NAYY 4X150"
            contype1 = "NAYY 4X50"
            contype2 = "NAYY 4X50"

        elif self.grid_type == "village":
            maintype = "NAYY 4X150"
            contype1 = "NAYY 4X50"
            contype2 = "NAYY 4X50"

        elif self.grid_type == "suburbcable1":
            maintype = "NAYY 4X150"
            contype1 = "NAYY 4X50"
            contype2 = "NAYY 4X35"

        elif self.grid_type == "suburbcable2":
            maintype = "NAYY 4X185"
            contype1 = "NAYY 4X50"
            contype2 = "NAYY 4X35"

        else:
            print('Invalid grid type in create_branch!')
            sys.exit()

        # Loop for adding branch data based on line_lengths
        # refImpedence = self.baseMVA/(0.400*0.400)
        for i in range(self.numberofbusses):
            for j in range(i + 1, self.numberofbusses):
                if self.line_lengths[i][j] > -1:
                    temp_branch = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    #   bus number and bus index are not the same number -> bus number := bus index +1
                    temp_branch[0] = i + 1
                    #   bus number and bus index are not the same number -> bus number := bus index +1
                    temp_branch[1] = j + 1
                    temp_branch[10] = 1
                    temp_branch[11] = -360
                    temp_branch[12] = 360

                    ref_Impedence = (self.bus[i+1][9] * self.bus[i+1][9]) / self.baseMVA

                    #   Every pair of directly neighbouring busses (except medium/lowvoltage connection)
                    #   represents a house connection
                    houseconnection = False

                    if i != 1:
                        if j != 1:
                            if abs(i - j) == 1:
                                houseconnection = True

                    if houseconnection:
                        if (contype1 == None):
                            currentconnection = maintype
                        elif (counter % 2 == 0):
                            currentconnection = contype1
                        else:
                            currentconnection = contype2

                        temp_branch[2] = data.cabledata[currentconnection]["RperKm"] * \
                                         self.line_lengths[i][j] / ref_Impedence
                        temp_branch[3] = data.cabledata[currentconnection]["XperKm"] * \
                                         self.line_lengths[i][j] / ref_Impedence
                        temp_branch[4] = data.cabledata[currentconnection]["BperKm"] * \
                                         self.line_lengths[i][j] * ref_Impedence
                        temp_branch[5] = data.cabledata[currentconnection]["MVA_A"]
                        temp_branch[6] = data.cabledata[currentconnection]["MVA_B"]
                        temp_branch[7] = data.cabledata[currentconnection]["MVA_C"]
                    else:
                        temp_branch[2] = data.cabledata[maintype]["RperKm"] * self.line_lengths[i][j] / ref_Impedence
                        temp_branch[3] = data.cabledata[maintype]["XperKm"] * self.line_lengths[i][j] / ref_Impedence
                        temp_branch[4] = data.cabledata[maintype]["BperKm"] * self.line_lengths[i][j] * ref_Impedence
                        temp_branch[5] = data.cabledata[maintype]["MVA_A"]
                        temp_branch[6] = data.cabledata[maintype]["MVA_B"]
                        temp_branch[7] = data.cabledata[maintype]["MVA_C"]

                    self.branch.append(temp_branch)

        # loop for adding transformers
        for t in range(len(self.transformers)):
            for b in range(len(self.branch)):

                if self.branch[b][0] == self.transformers[t].getBusf() and \
                                self.branch[b][1] == self.transformers[t].getBust():
                    ref_impedence = (self.bus[(self.transformers[t].getBusf()) - 1][9] *
                                    self.bus[(self.transformers[t].getBusf()) - 1][9]) / self.baseMVA
                    #   self.transformers[t].getMVA() := Sn
                    self.branch[b][5] = self.transformers[t].getMVA()
                    #   self.transformers[t].getMVA() := Sn
                    self.branch[b][6] = self.transformers[t].getMVA()
                    #   self.transformers[t].getMVA() := Sn
                    self.branch[b][7] = self.transformers[t].getMVA()
                    self.branch[b][8] = self.transformers[t].getTap()
                    self.branch[b][9] = self.transformers[t].getShift()
                    self.branch[b][2] += (self.transformers[t].getResistance() / ref_impedence)
                    self.branch[b][3] += (self.transformers[t].getInductance() / ref_impedence)

    def power_flow_animation(self, res_city_district, interval=1000):
        """
        animation of off-limit conditions over all time steps in the given city district

        Parameters
        ----------
        res_city_district: pycity_calc.cities.City
            city district
        interval: int, optional
            time period before the next picture appears in milliseconds
        """

        #   total number of times used in power flow calculation
        #   array of integer
        time_steps = np.arange(self.nb_time_steps_pf_calculation)

        #   set up the figure; plot city district
        fig = visual.plot_city_district(res_city_district,  plot_elec_labels=True, plot_deg=True, show_plot=False)
        #   returns dictionary with node ids as keys and position tuples (x, y) as values
        pos = visual.get_pos_for_plotting(res_city_district)

        #   maximize figure
        mng = plt.get_current_fig_manager()
        mng.window.state('zoomed')

        #   set position of text box on upper left corner
        axes = fig.get_axes()[0]
        x_min_axes = axes.get_xlim()[0]
        y_max_axes = axes.get_ylim()[1]
        text = plt.text(x_min_axes+0.01, y_max_axes-0.02, '', color='black', fontsize=15)

        #   this function will be called once before the first frame
        #   objects generated in the init function cannot be changed or removed later on
        def init():
            #   dummy object
            dummy = plt.plot(0, 0, markersize=0)
            return dummy

        #   makes an animation by repeatedly calling this function every 'interval' milliseconds
        def update(time_step):
            #   set text with time step
            text.set_text('time step: '+str(time_step))

            #   voltage deviation
            voltage_building = []
            voltage_network_node = []
            for node_number in res_city_district.node:
                vol = res_city_district.node[node_number]['voltage'][time_step]
                max_vol = res_city_district.node[node_number]['max_voltage'][time_step]
                min_vol = res_city_district.node[node_number]['min_voltage'][time_step]
                if vol > max_vol or vol < min_vol:
                    if res_city_district.node[node_number]['node_type'] == 'building':
                        voltage_building.append(node_number)
                    if res_city_district.node[node_number]['node_type'] == 'network_electricity':
                        voltage_network_node.append(node_number)
            scat_building = nx.draw_networkx_nodes(res_city_district,
                                                   pos=pos,
                                                   nodelist=voltage_building,
                                                   node_color='r',
                                                   node_shape='s',
                                                   alpha=0.5)
            scat_network_nodes = nx.draw_networkx_nodes(res_city_district,
                                                        pos=pos,
                                                        nodelist=voltage_network_node,
                                                        node_size=100,
                                                        width=2,
                                                        node_color='r',
                                                        alpha=0.5)

            #   current
            current = []
            for ed in res_city_district.edges():
                #   ed is tuple e.g. (1002, 1003)
                edge = res_city_district.edge[ed[0]][ed[1]]
                if edge['network_type'] == 'electricity':
                    cur = edge['current'][time_step]
                    max_cur = edge['max_current'][time_step]
                    if cur >= max_cur:
                        current.append(ed)
            scat_current = nx.draw_networkx_edges(res_city_district,
                                                  pos=pos,
                                                  edgelist=current,
                                                  width=2,
                                                  edge_color='r')

            #   transformer
            transformer = []
            for ed in res_city_district.edges():
                #   ed is tuple e.g. (1002, 1003)
                edge = res_city_district.edge[ed[0]][ed[1]]
                if edge['network_type'] == 'transformer':
                    power = edge['power'][time_step]
                    max_power = edge['max_power'][time_step]
                    if power > max_power:
                        transformer.append(ed)
            scat_power = nx.draw_networkx_edges(res_city_district,
                                                pos=pos,
                                                edgelist=transformer,
                                                style='dotted',
                                                width=3,
                                                edge_color='r')

            #   create output list
            return_list = []
            return_list.append(text)
            if scat_building is not None:
                return_list.append(scat_building)
            if scat_network_nodes is not None:
                return_list.append(scat_network_nodes)
            if scat_current is not None:
                return_list.append(scat_current)
            if scat_power is not None:
                return_list.append(scat_power)

            return return_list

        animation = ani.FuncAnimation(fig=fig, func=update, frames=time_steps, init_func=init, interval=interval, blit=True)

        plt.show()