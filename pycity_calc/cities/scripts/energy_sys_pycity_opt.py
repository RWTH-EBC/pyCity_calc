#!/usr/bin/env python
# coding=utf-8
"""
Script to postprocess pycity_opt results object. Resized chosen energy
system sized to be more realistic.
"""

# import os
# import pickle
#
# import pycity_base.classes.supply.BES as BES
# import pycity_base.classes.supply.PV as PV
#
# import pycity_calc.toolbox.networks.network_ops as netop
# import pycity_calc.toolbox.dimensioning.dim_networks as dimnet
# import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc
# import pycity_calc.visualization.city_visual as citvis
#
# import pycity_calc.energysystems.chp as chpsys
# import pycity_calc.energysystems.boiler as boil
# import pycity_calc.energysystems.heatPumpSimple as hpsys
# import pycity_calc.energysystems.electricalHeater as ehsys
# import pycity_calc.energysystems.thermalEnergyStorage as storage
# import pycity_calc.energysystems.battery as batt


# def gen_esys_city_with_pycity_opt_res(city, esopt_res, single_lhn_source=False,
#                                       dhw_usage=False,
#                                       use_street=False, boil_buffer=1.2,
#                                       pv_eta_default=0.15, boil_def_eta=0.85):
#     """
#     Generate energy system objects within city object, based on results of
#     pycity_opt ESOpt.py
#
#     Parameters
#     ----------
#     city : object
#         City object of pycity_calc (city without energy systems)
#     esopt_res : object
#         City object of pycity_calc (with results)
#     single_lhn_source : bool, optional
#         Defines, if lhn networks should only hvae single thermal source
#         or multiple sources (default: False)
#         True - Sum up all device powers and capacities and install system
#         within building of largest thermal energy demand
#     dhw_usage : bool, optional
#         Defines, if hot water should be taken into account
#         (default: False)
#     use_street : bool, optional
#         Defines, if heating networks should be routed along streets
#         (default: False)
#     boil_buffer : float, optional
#         Defines buffer factor for boiler (default: 1.2).
#         Used for overdimensioning
#     pv_eta_default : float, optional
#         Defines default value for efficiency of PV-modules (default: 0.15).
#         If set to None, uses original value of esopt.py results object
#     boil_def_eta : float, optional
#         Default value for boiler efficiency (default: 0.85)
#
#     Returns
#     -------
#     city : object
#         City object of pycity_calc (with energy systems)
#     """
#
#     #  TODO: Erase later
#     assert single_lhn_source is False, 'Single lhn source currently not supported!'
#
#
#     assert boil_buffer >= 1
#     assert pv_eta_default > 0
#     assert boil_def_eta > 0
#
#     #  Find all network types within esopt_res (heating, electricity,
#     #  lhn_and_electricity)
#     list_lhn_con = \
#         netop.get_list_with_energy_net_con_node_ids(city=esopt_res,
#                                                     network_type='heating')
#     list_deg_con = \
#         netop.get_list_with_energy_net_con_node_ids(city=esopt_res,
#                                                     network_type='electricity')
#
#     print('List of heating network connected building nodes:')
#     print(list_lhn_con)
#
#     print('List of deg connected nodes:')
#     print(list_deg_con)
#     print()
#
#     #  Install lhn and deg networks, first
#     #  #---------------------------------------------------------------------
#     #  Add networks to city (dimension heating networks according to dimfunc)
#     #  Add lhn networks, first
#     for list_h in list_lhn_con:
#         #  Dimension lhn system
#         dimnet.add_lhn_to_city(city=city, list_build_node_nb=list_h,
#                                network_type='heating')
#
#     # Add deg next (if heating edge already exists, change type
#     #  to heating_and_deg
#     for list_deg in list_deg_con:
#         #  Dimension deg
#         dimnet.add_deg_to_city(city=city, list_build_node_nb=list_deg)
#
#     # # Install single source devices within lhn networks
#     #  #---------------------------------------------------------------------
#     # Make decision, if lhn should only have single source or multiple sources
#     if single_lhn_source:  # Install single thermal sources within lhn
#
#         #  Loop over heating networks
#         for list_h in list_lhn_con:
#
#             found_multi_sources = False
#             source_count = 0
#             p_chp_el_nom = 0  # Dummy total chp el. power in W
#             p_chp_th_nom = 0  # Dummy total chp el. power in W
#             p_boil_th_nom = 0  # Dummy total boiler th. power in W
#             cap_tes_nom = 0  # Dummy total thermal storage capacity in kg
#
#             #  Loop over heating network nodes:
#             for n in list_h:
#                 # if 'node_type' in city.node[n]:
#                 #     if city.node[n]['node_type'] == 'building':
#                 if 'entity' in esopt_res.node[n]:
#                     if esopt_res.node[n]['entity']._kind == 'building':
#                         if esopt_res.node[n]['entity'].hasBes:
#
#                             #  If device is found, add power to total power
#                             if esopt_res.node[n]['entity'].bes.hasBoiler:
#                                 p_boil_th_nom += esopt_res.node[n]['entity'] \
#                                     .bes.boiler.qNominal
#                             if esopt_res.node[n]['entity'].bes.hasChp:
#                                 p_chp_el_nom += esopt_res.node[n]['entity'] \
#                                     .bes.chp.pNominal
#                                 p_chp_th_nom += esopt_res.node[n]['entity'] \
#                                     .bes.boiler.qNominal
#                             if esopt_res.node[n]['entity'].bes.hasTes:
#                                 cap_tes_nom += esopt_res.node[n]['entity'] \
#                                     .bes.tes.capacity
#
#                             source_count += 1
#
#                             if source_count >= 2:
#                                 found_multi_sources = True
#
#             if found_multi_sources:  # Add devices to building with highest
#                 #  thermal power
#
#                 #  Extract subcity
#                 subcity = netop.get_build_str_subgraph(city, nodelist=list_h)
#
#                 #  Find id of building with larges
#                 (id, th_p_max) = dimfunc.get_id_max_th_power(city=subcity,
#                                                              with_dhw=dhw_usage,
#                                                              find_max=True,
#                                                              return_value=True)
#
#                 #  Add bes to building (with node id 'id')
#                 # Instantiate BES
#                 bes = BES.BES(city.environment)
#
#                 if p_chp_el_nom > 0:
#                     #  Round power of chp
#                     p_chp_el_nom = dimfunc. \
#                         round_esys_size(p_chp_el_nom, round_up=True)
#                     p_chp_th_nom = dimfunc. \
#                         round_esys_size(p_chp_th_nom, round_up=True)
#
#                     #  Generate and add chp
#                     chp = chpsys.ChpExtended(environment=city.environment,
#                                              p_nominal=p_chp_el_nom,
#                                              q_nominal=p_chp_th_nom)
#
#                     #  Add to bes
#                     bes.addDevice(chp)
#
#                 if p_boil_th_nom > 0:
#                     #  Boiler buffer factor
#                     p_boil_th_nom *= boil_buffer
#
#                     #  Round power up
#                     p_boil_th_nom = dimfunc. \
#                         round_esys_size(p_boil_th_nom, round_up=True)
#
#                     #  Generate boiler object
#                     boiler = boil.BoilerExtended(environment=city.environment,
#                                                  q_nominal=p_boil_th_nom)
#
#                     #  Add boiler to bes
#                     bes.addDevice(boiler)
#
#                 if cap_tes_nom > 0:
#                     #  Round tes capacity
#                     cap_tes_nom = dimfunc.storage_rounding(cap_tes_nom)
#
#                     #  Generate tes object
#                     tes = storage. \
#                         thermalEnergyStorageExtended(
#                         environment=city.environment,
#                         capacity=cap_tes_nom,
#                         t_init=20, t_min=20)
#
#                     #  Add to bes
#                     bes.addDevice(tes)
#
#             else:  # Only found single source
#                 pass
#
#                 #  TODO: Add functions to single source adding
#
#                 #  Only install single thermal source within lhn network
#
#
#         #  Install further (thermal devices) in single buildings
#
#         #  Identify PV and battery systems in all buildings
#
#
#     # # Install multiple source devices within lhn networks
#     #  #---------------------------------------------------------------------
#     else:  # Install multiple heat sources in lhn (if found in results obj)
#
#         #  Check if node is of type building
#         for n in esopt_res.nodes():
#             #  Check if entity is of kind building
#             if 'entity' in esopt_res.node[n]:
#                 if esopt_res.node[n]['entity']._kind == 'building':
#                     if esopt_res.node[n]['entity'].hasBes:
#
#                         #  TODO: Check with which units parameters are handed over!
#
#                         found_boiler = False
#                         found_chp = False
#                         found_hp = False
#                         found_eh = False
#                         found_tes = False
#                         found_pv = False
#                         found_bat = False
#
#                         #  Search for boiler
#                         if esopt_res.node[n]['entity'].bes.hasBoiler:
#                             found_boiler = True
#                             cur_boil_th_nom = esopt_res.node[n]['entity'] \
#                                 .bes.boiler.qNominal  # in Watt
#
#                         #  Search for chp
#                         if esopt_res.node[n]['entity'].bes.hasChp:
#                             found_chp = True
#                             cur_chp_el_nom = esopt_res.node[n]['entity'] \
#                                 .bes.chp.pNominal
#                             cur_chp_th_nom = esopt_res.node[n]['entity'] \
#                                 .bes.boiler.qNominal
#
#                             #  in Watt
#
#                         #  Search for tes
#                         if esopt_res.node[n]['entity'].bes.hasTes:
#                             found_tes = True
#                             cur_cap_tes_nom = esopt_res.node[n]['entity'] \
#                                 .bes.tes.capacity
#
#                             #  in kG
#
#                         #  Search for heatpump
#                         if esopt_res.node[n]['entity'].bes.hasHeatpump:
#                             found_hp = True
#                             cur_hp_th_nom = esopt_res.node[n]['entity'] \
#                                 .bes.heatpump.qNominal
#                             #  Fixme: Figure out type of heatpump!
#
#                             #  in W
#
#                         #  Search for electrical heater
#                         if esopt_res.node[n]['entity'].bes.hasElectricalHeater:
#                             found_eh = True
#                             curr_eh_th_nom = esopt_res.node[n]['entity'] \
#                                 .bes.electricalHeater.qNominal
#
#                             #  in W
#
#                         #  Search for PV system
#                         if esopt_res.node[n]['entity'].bes.hasPv:
#                             found_pv = True
#                             curr_pv_area = esopt_res.node[n]['entity'] \
#                                 .bes.pv.area
#                             curr_pv_eta = esopt_res.node[n]['entity'] \
#                                 .bes.pv.eta
#
#                         # Search for battery system
#                         if esopt_res.node[n]['entity'].bes.hasBattery:
#                             found_pv = True
#                             curr_bat_cap = esopt_res.node[n]['entity'] \
#                                 .bes.battery.capacity
#                             curr_bat_socInit = esopt_res.node[n]['entity'] \
#                                 .bes.battery.capacity
#
#                             #  in Joule
#
#                         #  Resize and add energy systems to city object
#                         #  #-------------------------------------------------
#
#                         cur_b = city.node[n]['entity']  # Current building
#                         print('##############')
#                         print('Process building node with id ' + str(n))
#
#                         #  Add bes to current building
#                         bes = BES.BES(environment=city.environment)
#                         cur_b.addEntity(bes)
#                         cur_bes = city.node[n]['entity'].bes
#
#                         #  # Process boiler
#                         #  #---------------------------------------------------
#                         if found_boiler:
#
#                             #  Resize boiler
#                             if dhw_usage:
#                                 #  Upscale to account for dhw demand
#                                 ann_dhw_demand = cur_b.get_annual_dhw_demand()
#                                 ann_th_heat_demand = \
#                                     cur_b.get_annual_space_heat_demand()
#
#                                 factor_rescale = (ann_dhw_demand +
#                                                   ann_th_heat_demand) / \
#                                                  ann_th_heat_demand
#
#                                 #  Rescale boiler with dhw factor
#                                 cur_boil_th_nom *= factor_rescale
#
#                             # Add buffer factor
#                             cur_boil_th_nom *= boil_buffer
#
#                             #  Round boiler power up
#                             cur_boil_th_nom = \
#                                 dimfunc.round_esys_size(cur_boil_th_nom,
#                                                         round_up=True)
#
#                             #  Generate boiler object
#                             boiler = \
#                                 boil.BoilerExtended(
#                                     environment=city.environment,
#                                     q_nominal=cur_boil_th_nom,
#                                     eta=boil_def_eta)
#
#                             #  Add to building bes
#                             cur_bes.addDevice(boiler)
#
#                             print('Add boiler object with thermal power:')
#                             print(str(cur_boil_th_nom/1000) + ' kW')
#                             print('To building ' + str(n))
#
#                         # # Process chp
#                         #  #---------------------------------------------------
#                         if found_chp:
#
#                             if dhw_usage:
#                                 #  Upscale to account for dhw demand
#                                 ann_dhw_demand = cur_b.get_annual_dhw_demand()
#                                 ann_th_heat_demand = \
#                                     cur_b.get_annual_space_heat_demand()
#
#                                 factor_rescale = (ann_dhw_demand +
#                                                   ann_th_heat_demand) / \
#                                                  ann_th_heat_demand
#
#                                 #  Rescale chp with dhw factor
#                                 cur_chp_th_nom *= factor_rescale
#
#                             # Calculate el. power
#                             chp_el_th_ratio = \
#                                 dimfunc.calc_asue_el_th_ratio(cur_chp_th_nom)
#
#                             cur_chp_el_nom = chp_el_th_ratio * cur_chp_th_nom
#
#                             #  Round chp powers (round down)
#                             cur_chp_th_nom = \
#                                 dimfunc.round_esys_size(cur_chp_th_nom)
#                             cur_chp_el_nom = \
#                                 dimfunc.round_esys_size(cur_chp_el_nom)
#
#                             #  Generate chp object
#                             chp = chpsys.ChpExtended(environment=
#                                                      city.environment,
#                                                      q_nominal=cur_chp_th_nom,
#                                                      p_nominal=cur_chp_el_nom)
#
#                             #  Add to bes
#                             cur_bes.addDevice(chp)
#
#                             print('Add chp object with thermal power:')
#                             print(str(cur_chp_th_nom/1000) + ' kW')
#                             print('To building ' + str(n))
#
#                         # # Process hp
#                         #  #---------------------------------------------------
#                         if found_hp:
#
#                             #  Round values
#                             cur_hp_th_nom = \
#                                 dimfunc.round_esys_size(cur_hp_th_nom,
#                                                         round_up=True)
#
#                             #  Generate heatpump object
#                             heatpump = hpsys.heatPumpSimple(
#                                 environment=city.environment,
#                                 q_nominal=cur_hp_th_nom)
#
#                             #  Add heatpump to current bes
#                             cur_bes.addDevice(heatpump)
#
#                             print('Add heat pump object with thermal power:')
#                             print(str(cur_hp_th_nom/1000) + ' kW')
#                             print('To building ' + str(n))
#
#                         # # Process electrical heater
#                         #  #---------------------------------------------------
#                         if found_eh:
#
#                             if dhw_usage:
#                                 #  Upscale to account for dhw demand
#                                 ann_dhw_demand = cur_b.get_annual_dhw_demand()
#                                 ann_th_heat_demand = \
#                                     cur_b.get_annual_space_heat_demand()
#
#                                 factor_rescale = (ann_dhw_demand +
#                                                   ann_th_heat_demand) / \
#                                                  ann_th_heat_demand
#
#                                 #  Rescale chp with dhw factor
#                                 curr_eh_th_nom *= factor_rescale
#
#                             # Add electrical heater buffer (use boiler buffer)
#                             curr_eh_th_nom *= boil_buffer
#
#                             #  Round values
#                             curr_eh_th_nom = \
#                                 dimfunc.round_esys_size(curr_eh_th_nom,
#                                                         round_up=True)
#
#                             #  Generate electr. heater object
#                             el_heater = ehsys. \
#                                 ElectricalHeaterExtended(
#                                 environment=city.environment,
#                                 q_nominal=curr_eh_th_nom)
#
#                             #  Add to current bes
#                             cur_bes.addDevice(el_heater)
#
#                             print('Add el. heater object with thermal power:')
#                             print(str(el_heater/1000) + ' kW')
#                             print('To building ' + str(n))
#
#                         # # Process thermal energy storage (TES)
#                         #  #---------------------------------------------------
#                         if found_tes:
#
#                             if dhw_usage:
#                                 #  Upscale to account for dhw demand
#                                 ann_dhw_demand = cur_b.get_annual_dhw_demand()
#                                 ann_th_heat_demand = \
#                                     cur_b.get_annual_space_heat_demand()
#
#                                 factor_rescale = (ann_dhw_demand +
#                                                   ann_th_heat_demand) / \
#                                                  ann_th_heat_demand
#
#                                 #  Rescale chp with dhw factor
#                                 cur_cap_tes_nom *= factor_rescale
#
#                             #  Round to realistic storage size
#                             cur_cap_tes_nom = \
#                                 dimfunc.storage_rounding(cur_cap_tes_nom)
#
#                             tes = storage. \
#                                 thermalEnergyStorageExtended(
#                                 environment=city.environment,
#                                 t_init=20, capacity=cur_cap_tes_nom)
#
#                             #  Add tes to bes
#                             cur_bes.addDevice(tes)
#
#                             print('Add thermal storage with thermal capacity:')
#                             print(str(cur_cap_tes_nom) + ' kg')
#                             print('To building ' + str(n))
#
#                         # # Process PV
#                         #  #---------------------------------------------------
#                         if found_pv:
#
#                             assert curr_pv_eta <= 0.2
#
#                             #  Use user defined pv eta
#                             if pv_eta_default is not None:
#                                 assert pv_eta_default > 0
#                                 curr_pv_eta = pv_eta_default
#
#                             pv = PV.PV(environment=city.environment,
#                                        area=curr_pv_area,
#                                        eta=curr_pv_eta)
#
#                             #  Add PV to bes
#                             cur_bes.addDevice(pv)
#
#                             print('Add PV object with area:')
#                             print(str(curr_pv_area) + ' m2')
#                             print('To building ' + str(n))
#
#                         # # Process battery
#                         #  #---------------------------------------------------
#                         if found_bat:
#
#                             battery = batt. \
#                                 BatteryExtended(environment=city.environment,
#                                                 soc_init_ratio=0,
#                                                 capacity_kwh=curr_bat_cap/ (
#                                                 3600 * 1000))
#
#                             # Add battery to bes
#                             bes.addDevice(battery)
#
#                             print('Add battery object with capacity:')
#                             print(str(curr_bat_cap / (3600 * 1000)) + ' kWh')
#                             print('To building ' + str(n))
#
#     return city
#
#
# if __name__ == '__main__':
#     #  TODO: Loop over multiple result files (for cluster)
#
#     #  User input
#     #  #---------------------------------------------------------------------
#     #  Path to city pickle file (original city object without
#     #  energy systems and energy networks!)
#     city_filename = 'city_3_buildings.p'
#     this_path = os.path.dirname(os.path.abspath(__file__))
#     city_path = os.path.join(this_path,
#                              'input_esys_gen_pycity_opt',
#                              city_filename)
#
#     #  Path to pycity_opt results object
#     opt_filename = 'epsilon_12177_res.p'
#     opt_path = os.path.join(this_path, 'input_esys_gen_pycity_opt',
#                             opt_filename)
#
#     #  Path to save new city object (with re-dimensiong energy systems) to
#     output_name = 'city_complete.p'
#     output_path = os.path.join(this_path, 'output_esys_gen_pycity_opt',
#                                output_name)
#
#     #  Use single or multiple thermal sources within lhn network?
#     s_lhn = False
#     #  True - single source (converts multiple sources to single source,
#     #  if necessary)
#     #  False - Multiple sources possible
#
#     #  Account for hot water demands
#     dhw_usage = False
#
#     #  Route heating networks along streets
#     use_street = False
#
#     #  End of user input
#     #  #---------------------------------------------------------------------
#
#     #  Load city object
#     city = pickle.load(open(city_path, mode='rb'))
#
#     #  Load pycity_opt results object
#     res_obj = pickle.load(open(opt_path, mode='rb'))
#
#     #  Add resized energy system configs from optimization to city object
#     city = gen_esys_city_with_pycity_opt_res(city=city,
#                                              single_lhn_source=s_lhn,
#                                              esopt_res=res_obj,
#                                              dhw_usage=dhw_usage,
#                                              use_street=use_street)
#
#     #  Save city object as pickle file
#     pickle.dump(city, open(output_path, mode='wb'))
#
#     #  Visualization
#     citvis.plot_city_district(city=city, plot_lhn=True,
#                               plot_deg=True,
#                               plot_esys=True)
