#!/usr/bin/env python
# coding=utf-8
"""
Script to generate and dimension energy systems for city district, based
on csv/txt input table.

Requires city object (optionally, with networks) as input
"""

import os
import csv
import pickle
import pycity_base.classes.supply.BES as BES
import pycity_base.classes.supply.PV as PV
import pycity_calc.visualization.city_visual as citvis
import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc
import pycity_calc.toolbox.networks.network_ops as netop
import pycity_calc.energysystems.boiler as boil
import pycity_calc.energysystems.chp as chpsys
import pycity_calc.energysystems.thermalEnergyStorage as tes
import pycity_calc.energysystems.heatPumpSimple as hpsys
import pycity_calc.energysystems.electricalHeater as ehsys
import pycity_calc.energysystems.battery as batt
import pycity_calc.energysystems.Input.chp_asue_2015 as asue


def load_enersys_input_data(esys_path):
    """
    Load energy system input data from network_path (should point on
    csv/txt file, which is tab separated and holds information about
    planed energy systems (type and position))

    Parameters
    ----------
    esys_path : str
        Path to input file

    Returns
    -------
    list_data : list
        List (of tuples). Each tuple holds eneryg system data with following
        information: (node_id, type, method)
    """

    #  Generate empty data list
    list_data = []

    with open(esys_path, 'r') as file:
        next(file)  # Skip header

        reader = csv.reader(file, delimiter='\t')
        for node_id, type, method in reader:
            #  Generate data tuple
            tup_data = (int(node_id), int(type), float(method))

            #  Add tuple to data list
            list_data.append(tup_data)

    return list_data


def gen_esys_for_city(city, list_data, dhw_scale=False, tes_default=100,
                      buffer_factor=2, lhn_buffer=1.2):
    """
    Generate and dimensions energy systems within city district, based on
    user defined energy system types and method within txt input file.

    Parameters
    ----------
    city : object
        City object of pycity_calc
    list_data : list
        List (of tuples). Each tuple holds eneryg system data with following
        information: (node_id, type, method)
    dhw_scale : bool, optional
        Defines, if hot water thermal energy demand should be taken into
        account. (default: False)
        If True, only space heating power demand is taken into account.
    tes_default : float, optional
        Default value for smallest thermal storage size in kg
        (default: 100)
    buffer_factor : float, optional
        Factor for boiler/EH oversizing (default: 2)
    lhn_buffer : float, optional
        Factor for LHN connection oversizing (default: 1.2). Relevant to
        account for LHN losses in Boiler/CHP sytem dimensioning
    """

    #  Check if all node ids exist within city object
    for tup in list_data:
        assert tup[0] in city.nodelist_building, ('Node ' + str(tup[0]) +
                                                  ' is not within city')

    # Generate energy systems
    #  #---------------------------------------------------------------------
    for tup in list_data:

        node_id = tup[0]  # Id of node
        type = tup[1]  # Type of energy system
        method = tup[2]  # Method for generation of energy system

        print('Process node with id ', node_id)

        #  Check if building at node_id does not have BES, already
        if city.node[node_id]['entity'].hasBes is False:
            #  Generate BES, if not existent
            bes = BES.BES(environment=city.environment)
        else:
            bes = city.node[node_id]['entity'].bes

        # #-------------------------------------------------------------
        if type == 0:  # Boiler (+ TES)
            #  #-------------------------------------------------------------

            #  Check if chosen node_id building is connected via lhn to
            #  other buildings
            n_list = city.neighbors(node_id)

            #  TODO: Add function to allow adding boiler to lhn
            #  Check that no lhn connection exists
            #  (Currently, no dimensioning of lhn with boiler,
            #  exlusively, is allowed.
            if n_list != []:
                for nei in n_list:
                    if 'network_type' in city.edge[node_id][nei]:
                        if (city.edge[node_id][nei]['network_type']
                                == 'heating' or
                                    city.edge[node_id][nei]['network_type']
                                    == 'heating_and_deg'):
                            raise AssertionError('Building ' + str(node_id) +
                                                 ' should not be connected ' +
                                                 'to lhn!')
            # Pointer to building
            build = city.node[node_id]['entity']

            #  Size boiler with max. building th. power load
            if dhw_scale:

                if method == 1:
                    #  Size boiler according to total max. th. load (+ dhw)
                    boiler_th_power = dimfunc. \
                        get_max_power_of_building(build, with_dhw=True)

                elif method == 2:
                    #  Size boiler according to building load and average
                    #  dhw load
                    boiler_th_power = dimfunc. \
                        get_max_power_of_building(build, with_dhw=False)

                    #  Upscale to account for dhw demand
                    ann_dhw_demand = build.get_annual_dhw_demand()
                    ann_th_heat_demand = build.get_annual_space_heat_demand()

                    factor_rescale = (ann_dhw_demand + ann_th_heat_demand) / \
                                     ann_th_heat_demand

                    #  Rescale thermal power of boiler
                    boiler_th_power *= factor_rescale

            else:  # Size without hot water

                boiler_th_power = dimfunc. \
                    get_max_power_of_building(build, with_dhw=False)

            # Add boiler buffer factor
            boiler_th_power *= buffer_factor

            # Round results
            boiler_th_power = dimfunc.round_esys_size(boiler_th_power,
                                                      round_up=True)

            print('Chosen boiler size in kW:')
            print(boiler_th_power / 1000)

            #  Define empty entities list
            list_entities = []

            if method == 1:  # Only boiler

                boiler = boil.BoilerExtended(environment=city.environment,
                                             q_nominal=boiler_th_power,
                                             eta=0.85,
                                             lower_activation_limit=0)

                list_entities = [boiler]

            if method == 2:  # Boiler with thermal storage system

                boiler = boil.BoilerExtended(environment=city.environment,
                                             q_nominal=boiler_th_power,
                                             eta=0.85)

                #  Estimate tes size
                if dhw_scale:  # With dhw usage

                    #  Get max. thermal power (space heat and dhw)
                    max_th_total = dimfunc. \
                        get_max_power_of_building(build, with_dhw=True)

                    print('Max total power', max_th_total)

                    delta_th_power = max_th_total - boiler_th_power

                    if delta_th_power > 0:
                        #  Assuming that storage and boiler should be
                        #  able to cover max. peak load for 10 minutes
                        req_energy = delta_th_power * 10 * 60
                        #  Energy in Joule
                        tes_size = req_energy / (4182 * 80)
                        #  m = E/(c_p * delta_T)

                    else:
                        #  Default size
                        tes_size = tes_default

                else:  # Standard size
                    tes_size = tes_default

                # Round storage size up
                tes_size = dimfunc.storage_rounding(tes_size)

                print('Chosen storage size in liters:')
                print(tes_size)
                print()

                #  Generate storage system
                storage = tes. \
                    thermalEnergyStorageExtended(environment=city.environment,
                                                 t_init=20,
                                                 capacity=tes_size)

                list_entities = [boiler, storage]

            # Add devices to bes (type 0 - 2)
            bes.addMultipleDevices(list_entities)

        # #-------------------------------------------------------------
        elif type == 1:  # CHP + Boiler + TES
            #  #-------------------------------------------------------------

            #  Check if chosen node_id building is connected via lhn to
            #  other buildings
            n_list = city.neighbors(node_id)

            has_lhn_con = False

            if n_list != []:
                for nei in n_list:
                    if 'network_type' in city.edge[node_id][nei]:
                        if (city.edge[node_id][nei]['network_type']
                                == 'heating' or
                                    city.edge[node_id][nei]['network_type']
                                    == 'heating_and_deg'):
                            has_lhn_con = True
                            print('Found lhn connected to node ', node_id)

            # #------------------------------------
            if has_lhn_con:  # If lhn connection exists, find all buildings

                #  Get list of all nodes connected to this building
                list_lhn = \
                    netop.get_list_with_energy_net_con_node_ids(city,
                                                                network_type='heating',
                                                                search_node=node_id)

                list_build = []  # List of building entities
                #  Loop over list_lhn
                for n in list_lhn:
                    if 'node_type' in city.node[n]:
                        #  If node_type is building
                        if city.node[n]['node_type'] == 'building':
                            #  If entity is kind building
                            if city.node[n]['entity']._kind == 'building':
                                #  If node n holds building entity, add it.
                                list_build.append((n))

                print('List of building node ids, which are connected (LHN):')
                print(list_build)

                # sum up thermal energy demands
                th_dur_curve = dimfunc. \
                    get_ann_load_dur_curve(city_object=city,
                                           nodelist=list_build)

                #  Estimate pipe losses based on pipe length and diameter
                #  TODO: Add function to estimate max. pipe losses

                #  Account for hot water by upscaling factor
                if dhw_scale:
                    #  Upscale to account for dhw demand
                    ann_dhw_demand = city. \
                        get_annual_dhw_demand(nodelist=list_build)
                    ann_th_heat_demand = city. \
                        get_annual_space_heating_demand(nodelist=list_build)

                    factor_rescale = (ann_dhw_demand + ann_th_heat_demand) / \
                                     ann_th_heat_demand

                    #  Rescale th_dur_curve
                    th_dur_curve *= factor_rescale

                aggr_th_load_dur_curve = \
                    dimfunc.get_ann_load_dur_curve(city, with_dhw=dhw_scale,
                                                   nodelist=list_build)

            # #------------------------------------
            else:  # Only single building energy demand is relevant

                build_single = city.node[node_id]['entity']

                th_dur_curve = dimfunc. \
                    get_load_dur_curve_building(building=build_single)

                #  Account for hot water by upscaling factor
                if dhw_scale:
                    #  Upscale to account for dhw demand
                    ann_dhw_demand = build_single. \
                        get_annual_dhw_demand()
                    ann_th_heat_demand = build_single. \
                        get_annual_space_heat_demand()

                    factor_rescale = (ann_dhw_demand + ann_th_heat_demand) / \
                                     ann_th_heat_demand

                    #  Rescale th_dur_curve
                    th_dur_curve *= factor_rescale

                aggr_th_load_dur_curve = \
                        dimfunc.get_load_dur_curve_building(building=build_single,
                                                            with_dhw=dhw_scale)

            # CHP + Boiler + TES dimensioning
            #  #------------------------------------
            #  Use thermal load curve to dimension CHP with spec. method
            chp_th_power = dimfunc. \
                calc_chp_nom_th_power(th_power_curve=th_dur_curve,
                                      method=method,
                                      timestep=
                                      city.environment.timer.timeDiscretization)

            chp_el_th_ratio = asue.calc_asue_el_th_ratio(chp_th_power)
            chp_el_power = chp_el_th_ratio * chp_th_power

            #  Round results
            if has_lhn_con:
                chp_th_power = dimfunc.round_esys_size(
                    power=chp_th_power) * lhn_buffer
            else:
                chp_th_power = dimfunc.round_esys_size(power=chp_th_power)

            print('Chosen chp thermal power in kW:')
            print(chp_th_power / 1000)

            print('Chosen chp electrical power in kW:')
            print(chp_el_power / 1000)

            #  Size boiler to be able to fullfill maximal load
            boiler_th_power = dimfunc.get_max_p_of_power_curve(power_curve=
                                                               aggr_th_load_dur_curve)

            #  Round results
            if has_lhn_con:
                boiler_th_power = dimfunc.round_esys_size(boiler_th_power,
                                                          round_up=True) \
                                  * lhn_buffer
            else:
                boiler_th_power = dimfunc.round_esys_size(boiler_th_power,
                                                          round_up=True)

            #  Add boiler buffer factor
            boiler_th_power *= buffer_factor

            print('Chosen boiler size in kW:')
            print(boiler_th_power / 1000)

            #  TES sizing
            #  Storage should be capable of storing full chp thermal
            #  power for 6 hours (T_spread = 60 Kelvin)
            mass_tes = chp_th_power * 6 * 3600 / (4180 * 60)

            #  Round to realistic storage size
            mass_tes = dimfunc.storage_rounding(mass_tes)

            print('Chosen storage size in liters:')
            print(mass_tes)
            print()

            #  Generate energy systems and add them to bes
            #  #------------------------------------------
            boiler = boil.BoilerExtended(environment=city.environment,
                                         q_nominal=boiler_th_power,
                                         eta=0.85)

            chp = chpsys.ChpExtended(environment=city.environment,
                                     q_nominal=chp_th_power,
                                     p_nominal=chp_el_power)

            storage = tes. \
                thermalEnergyStorageExtended(environment=city.environment,
                                             t_init=20, capacity=mass_tes)

            list_entities = [boiler, chp, storage]

            # Add devices to bes (type 0 - 2)
            bes.addMultipleDevices(list_entities)

        # #-------------------------------------------------------------
        elif type == 2:  # HP + EH + TES
            #  #-------------------------------------------------------------

            #  Check if chosen node_id building is connected via lhn to
            #  other buildings
            n_list = city.neighbors(node_id)

            #  Check that no lhn connection exists
            if n_list != []:
                for nei in n_list:
                    if 'network_type' in city.edge[node_id][nei]:
                        if (city.edge[node_id][nei]['network_type']
                                == 'heating' or
                                    city.edge[node_id][nei]['network_type']
                                    == 'heating_and_deg'):
                            raise AssertionError('Building ' + str(node_id) +
                                                 ' should not be connected ' +
                                                 'to lhn (for heat pump)!')
            # Pointer to building
            build = city.node[node_id]['entity']

            hp_th_power = dimfunc. \
                get_max_power_of_building(build, with_dhw=False)

            #  Round values
            hp_th_power = dimfunc.round_esys_size(hp_th_power,
                                                  round_up=True)
            print('Chosen heat pump nominal th. power in kW:')
            print(hp_th_power / 1000)

            heatpump = hpsys.heatPumpSimple(environment=city.environment,
                                            q_nominal=hp_th_power)

            #  TODO: Size el. heater based on max. space heating and dhw power
            el_h_space_h_power = hp_th_power * buffer_factor

            if dhw_scale:
                #  Size el. heater according to max. dhw power of building
                dhw_power_curve = build.get_dhw_power_curve()
                max_dhw_power = \
                    dimfunc.get_max_p_of_power_curve(dhw_power_curve)

                el_h_space_h_power += max_dhw_power

            # Round values
            el_heat_power = dimfunc.round_esys_size(el_h_space_h_power,
                                                    round_up=True)
            print('Chosen el. heater nominal th. power in kW:')
            print(el_heat_power / 1000)

            el_heater = ehsys. \
                ElectricalHeaterExtended(environment=city.environment,
                                         q_nominal=el_heat_power)

            #  TES sizing
            #  Storage should be capable of storing full hp thermal
            #  power for 3 hour (T_spread = 30 Kelvin)
            mass_tes = hp_th_power * 3 * 3600 / (4180 * 30)

            #  Round to realistic storage size
            mass_tes = dimfunc.storage_rounding(mass_tes)

            print('Chosen storage size in liters:')
            print(mass_tes)
            print()

            storage = tes. \
                thermalEnergyStorageExtended(environment=city.environment,
                                             t_init=20, capacity=mass_tes)

            list_entities = [heatpump, el_heater, storage]

            # Add devices to bes (type 0 - 2)
            bes.addMultipleDevices(list_entities)

        # #-------------------------------------------------------------
        elif type == 3:  # PV
            #  #-------------------------------------------------------------
            # method --> Defines area of PV as float value

            pv = PV.PV(environment=city.environment, area=method,
                       eta=0.15)

            print('Add PV system with area in m2: ', method)

            # Add pv to bes
            bes.addDevice(pv)

        # #-------------------------------------------------------------
        elif type == 4:  # Battery
            #  #-------------------------------------------------------------
            #  method --> Defines capacity of battery as float value (kWh)

            battery = batt. \
                BatteryExtended(environment=city.environment,
                                soc_init_ratio=0, capacity_kwh=method)

            print('Add el. battery with capacity in kWh: ', method)

            # Add battery to bes
            bes.addDevice(battery)

        # #-------------------------------------------------------------
        else:
            raise ValueError('Type is unknown. Check list_data input!')

        # Add bes to building
        city.node[node_id]['entity'].addEntity(bes)
        print()


if __name__ == '__main__':
    #  Use dhw profile, too?
    dhw_usage = True

    #  Path to city pickle file
    city_filename = 'city_3_buildings_with_networks.p'
    this_path = os.path.dirname(os.path.abspath(__file__))
    city_path = os.path.join(this_path, 'input_esys_generator',
                             city_filename)

    #  Path to energy system input file (csv/txt; tab separated)
    esys_filename = 'city_3_building_enersys.txt'
    esys_path = os.path.join(this_path, 'input_esys_generator',
                             esys_filename)

    #  Path to save pickle city file with networks
    save_filename = 'city_3_building_enersys_enersys.p'
    save_path = os.path.join(this_path, 'output_esys_generator',
                             save_filename)

    #  Load city object
    city = pickle.load(open(city_path, mode='rb'))

    #  Load energy networks planing data
    list_data = load_enersys_input_data(esys_path)

    #  Generate energy systems
    gen_esys_for_city(city=city, list_data=list_data, dhw_scale=dhw_usage)

    #  Plot city
    citvis.plot_city_district(city=city, plot_lhn=True, plot_deg=True,
                              plot_street=True, plot_esys=True)

    #  Save city pickle file
    pickle.dump(city, open(save_path, mode='wb'))
