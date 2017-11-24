'''
# Example dictionary containing information on power excess and shortage for the current timestep
# {key:[Qsum,Qchp_nom,Qchp_min,Qboiler_nom,Qboiler_min,Q_tes_in,Q_tes_out]}

dict_Qlhn={'1001': {'Qsum':[10,10],'Qchp_nom':[8,8],'Qchp_min':[5,5],'Qboiler_nom':[2,2],'Qboiler_min':[1,1]},
                '1002': {'Qsum':[4,4],'Qchp_nom':[2,2],'Qchp_min':[2,2],'Qboiler_nom':[2,2],'Qboiler_min':[1,1]},
                '1003': {'Qsum':[6,6],'Qchp_nom':[3,3],'Qchp_min':[2,2],'Qboiler_nom':[3,3],'Qboiler_min':[1,1]},
                '1004': {'Qsum':[-15,-8],'Qchp_nom':[0,0],'Qchp_min':[0,0],'Qboiler_nom':[0,0],'Qboiler_min':[0,0]},
                '1005': {'Qsum':[-15,0],'Qchp_nom':[0,0],'Qchp_min':[0,0],'Qboiler_nom':[0,0],'Qboiler_min':[0,0]},
                '1006': {'Qsum':[10,10],'Q_CHP':[5,0],'Qchp_min':[1,0],'Qboiler_nom':[5,0],'Qboiler_min':[1,0]}
print(dict_Qlhn.keys())
time=[0,1]
'''
'''
This script determines which buildings supply their thermal excess to the LHN in order to cover the demand of other buildings
connected to the LHN which cannot supply their demand by their own energy Systems.
Qsum is the total amount of energy which can be supplied or must be taken from the LHN. Qsum>0 means supply, Qsum<0 means demand.

input:
dict_Qlhn: dictionary containing information about excess and shortage of each building over time, excess is also divided up in excess
                per energysystem
                dict_Qlhn={'nodenumber':{'Q_sum':[t1,t2,t3,...],'Qchp_nom':[t1,t2,t3,...],'Qchp_min':[t1,t2,t3,...],'Qboiler_nom':[t1,t2,t3,...],'Qboiler_min':[t1,t2,t3,...]}}
sortingmethod:  'str': 'COSTS' or 'CO2'. Sort supply priotity in accordance to costs or CO2 emissions [CHP first, then boiler, then EH]
time:           'list': List containing all the timesteps
LHN_supply_method: 'str', method to set the sequence of activated energy system
                        'flexible'=Use CHP first, then Boiler
                        'static'  =Use CHP+Boiler
subcity_building_nodes: 'list', list containing all buildingnode interconnected to a subcity
'''

import pycity_calc.toolbox.networks.network_ops as netop
import pycity_calc.toolbox.dimensioning.dim_networks as dim_net
import pycity_calc.simulation.energy_balance_optimization.energy_balance_building as EB2
#import pycity_calc.simulation.energy_balance_optimization.Complex_city_gen as CCG
import pycity_calc.simulation.energy_balance_optimization.test_city as testcity
import matplotlib.pyplot as plt#
import numpy as np
import pickle
import pycity_calc.cities.city as cit

# define invalid Individual Error.
class invalidind2(Exception):
    pass


# Determine which Buildings are chosen to cover the demand of the LHN
def city_energy_balance(City_Object, dict_Qlhn, sortingmethod='CO2', LHN_supply_method = "flexible", subcity_building_nodes=None):
    ################
    #calc lhn losses

    #create empty grapg
    lhn_graph = cit.City(environment=City_Object.environment)
    #get list of lhn connected nodes
    lhn_con_nodes = netop.get_list_with_energy_net_con_node_ids(City_Object,search_node=subcity_building_nodes[0], network_type='heating')


    list_n_lhn = []
    #  Add building nodes of nodelist to lhn_graph
    for n in lhn_con_nodes:
        if 'node_type' in City_Object.nodes[n]:
            if City_Object.nodes[n]['node_type'] == 'heating' or City_Object.nodes[n]['node_type'] == 'building':
                curr_pos = City_Object.nodes[n]['position']
                #  Add nodes to city_copy
                lhn_graph.add_node(n, position=curr_pos, node_type='heating')
                list_n_lhn.append(n)

    #  Add all edges of type heating to lhn_graph
    for u, v in City_Object.edges():
        if u in lhn_con_nodes and v in lhn_con_nodes:
            if 'network_type' in City_Object.edges[u, v]:
                if City_Object.edges[u, v]['network_type'] == 'heating' or City_Object.edges[u, v]['network_type'] == 'heating_and_deg':
                    #  Add street edge to street_graph
                    lhn_graph.add_edge(u, v, network_type='heating')
                    temp_vl = City_Object.edges[u, v]['temp_vl']
                    temp_rl = City_Object.edges[u, v]['temp_rl']
                    d_i = City_Object.edges[u, v]['d_i']
                    #TODO: find better way to get temp and di

    #Add nodelist street
    lhn_graph.nodelist_street = list_n_lhn
    #add weights to edges
    netop.add_weights_to_edges(lhn_graph)
    #calc total length of LHN network
    length = netop.sum_up_weights_of_edges(lhn_graph, network_type='heating')
    #print('LHN networklength in m:', length)

    # calc total power losses
    u_pipe = dim_net.estimate_u_value(d_i)
    temp_environment = City_Object.environment.temp_ground
    Q_dot_loss = dim_net.calc_pipe_power_loss(length, u_pipe, temp_vl, temp_rl, temp_environment)
    #print('LHN losses in W:', Q_dot_loss)
    ################
    # save number of timesteps
    timesteps=City_Object.environment.timer.timestepsTotal

    # Create dict to store results
    dict_supply={}
    for node in dict_Qlhn.keys():
        dict_supply.update({node: {'Qchp_nom': np.zeros(timesteps), 'Qboiler_nom': np.zeros(timesteps)}})

    # usefull for debugging. All print statements are stored to .txt file
    #import sys
    #filename = open("results.txt", 'w')
    #sys.stdout = filename

    # Loop over all timesteps
    for t in range(timesteps):
        ####print("############timestep", t, "###############")
        # Check if the demand can be covered by the supply
        Qsum_total = 0 # initialization
        demand_at_timestep = False
        for Qsum_i in dict_Qlhn.items():
            Qsum_total = Qsum_total+Qsum_i[1]['Qsum'][t]  # sum all Qsum
            if Qsum_i[1]['Qsum'][t] < 0:
                demand_at_timestep = True
        #only if there is a demand add the lhn losses
        if demand_at_timestep:
            Qsum_total = Qsum_total - Q_dot_loss
            #TODO might want to add a factor

        #####if Qsum_total >= 0:
        #####    print('enough supply\nQsum_total:', Qsum_total)
        if Qsum_total < -0.001:
            print('not enough supply\nQsum_total:', Qsum_total)
            raise invalidind2 # raise the invalid Individual Error


        # Create dictionaries containing only suppliers or only demanders
        supplier_nodes_CHP_B = {}   # initialization
        supplier_nodes_boiler = {}  # initialization
        consumer_nodes = {}         # initialization
        for Qsum_i in dict_Qlhn.items():       # loop over all building nodes
            if Qsum_i[1]['Qsum'][t] > 0:            # Qsum>0->supply
                subdict_CHP_B = {}
                subdict_boiler = {}
                if Qsum_i[1]['Qchp_nom'][t] > 0:       # Supply from CHP and Boiler
                    for subitem in Qsum_i[1].items():
                        subdict_CHP_B.update({subitem[0]: subitem[1][t]})
                    supplier_nodes_CHP_B.update({Qsum_i[0]: subdict_CHP_B})
                elif Qsum_i[1]['Qchp_nom'][t] == 0 and Qsum_i[1]['Qeh_nom'][t] == 0:    # Supply from boiler
                    for subitem in Qsum_i[1].items():
                        subdict_boiler.update({subitem[0]: subitem[1][t]})
                    supplier_nodes_boiler.update({Qsum_i[0]: subdict_boiler})

            elif Qsum_i[1]['Qsum'][t] < 0:          # Qsum<0->demand
                subdict = {}
                for subitem in Qsum_i[1].items():
                    subdict.update({subitem[0]: subitem[1][t]})
                consumer_nodes.update({Qsum_i[0]: subdict})
        supplier_nodes = {**supplier_nodes_CHP_B,**supplier_nodes_boiler}  # merge to a general supply dict

        #print("supplier_nodes with CHP and B:", supplier_nodes_CHP_B.keys())
        #print("supplier_nodes with EH:", supplier_nodes_EH.keys())
        ####print("supplier_nodes:", supplier_nodes)
        ####print("consumer_nodes:", consumer_nodes)

        # Create a list which only contains building nodes('str'), sorted according to a sortingmethod('COSTS', 'CO2')
        list_supplier_priority_CHP_B = []   # initialization
        list_supplier_priority_boiler = []  # initialization
        list_supplier_priority = []         # initialization
        if sortingmethod == 'CO2':
            list_supplier_CHP_B_priority_temp = sorted(supplier_nodes_CHP_B.items(), key=lambda x: x[1]['Qchp_nom'], reverse=True) #return a list, with items sorted by Qchp_nom
            for item in list_supplier_CHP_B_priority_temp:
                list_supplier_priority_CHP_B.append(item[0])
            list_supplier_boiler_priority_temp = sorted(supplier_nodes_boiler.items(), key=lambda x: x[1]['Qboiler_nom'], reverse=True)  # return a list, with items sorted by boiler_nom
            for item in list_supplier_boiler_priority_temp:
                list_supplier_priority_boiler.append(item[0])

            list_supplier_priority=list_supplier_priority_CHP_B+list_supplier_priority_boiler
        elif sortingmethod == 'COSTS':
            list_supplier_priority = []
            # TODO: implement, maybe a second dict_energysource_prices is needed

        ####print("list_provider_priority:", list_supplier_priority)

        # From the supply priority list define buildings that actual supply.
        # Also calculate the actual amount to be supplied by each building

        # calculate total demand
        Q_demand = 0     # initialization
        for Qsum_i in consumer_nodes.items():
            Q_demand = Q_demand+abs(Qsum_i[1]['Qsum'])

        # if the LHN is used the thermal losses are added to demand
        # this method neglects the cooling and reheating process of the lhn.
        if Q_demand > 0:
            Q_demand = Q_demand + Q_dot_loss
            #TODO: good way??
            #TODO might want to add a factor

        ####print('demand: ',Q_demand)

        Q_supply_sum = 0        # initialization
        Q_supply_sum_min = 0    # initialization

        # determine suppliers: First CHP, then Boiler, then EH
        if LHN_supply_method == 'flexible':
            supply = True         # as long as supply is true, the supply is not covered by the buildings selected so far
            CHP_partload = False  # boolean to enter the "minimize the remainder by CHP partload" loop
            B_partload = False    # boolean to enter the "minimize the remainder by B partload" loop
            #EH_partload = False   # boolean to enter the "minimize the remainder by EH partload" loop

            # go through suppliers list, determine which supplier
            # has to actually supply. Stop when enough supply summed up
            # to cover the demand

            ##############################
            # try to cover demand with CHP
            ##############################

            # sum up maximum CHP supply building by building
            for node in list_supplier_priority:
                if Q_supply_sum < Q_demand:
                    Q_supply_max = supplier_nodes[node]['Qchp_nom']
                    Q_supply_sum = Q_supply_sum+Q_supply_max
                    Q_supply_min = supplier_nodes[node]['Qchp_min']
                    Q_supply_sum_min = Q_supply_sum_min+Q_supply_min
                    dict_supply[node]['Qchp_nom'][t] = supplier_nodes[node]['Qchp_nom']
                    # If all demand can be covered by the CHP
                    if Q_supply_sum >= Q_demand:
                        supply = False              # demand is covered, no more suppliers are necessary
                        CHP_partload = True         # enter the partload loop to fit supply to demand
                        break

            # try to exactly fit supply to demand:
            #   reduce supply by switching last selected supplier's CHP to partload to reduce remainder
            if CHP_partload:
                if Q_supply_sum != Q_demand:    # only enter when demand is not exactly met
                    remainder = Q_supply_sum-Q_demand   # Energy that would be wasted if all system ran in nominal condition
                    possible_reduction = supplier_nodes[node]['Qchp_nom']-supplier_nodes[node]['Qchp_min']    # possible reduction by switching to min_load
                    ####print('remainder:', remainder)
                    ####print('possible_reduction: ',possible_reduction, 'at node:', node)

                    if remainder < possible_reduction:
                        dict_supply[node]['Qchp_nom'][t] = possible_reduction-remainder+supplier_nodes[node]['Qchp_min']
                        ####print('last suppliers Q_CHP in partload')
                    if remainder >= possible_reduction:
                        dict_supply[node]['Qchp_nom'][t] = supplier_nodes[node]['Qchp_nom'] - remainder
                        ####print('last suppliers Q_CHP in min_load')

            ############################################
            # try to cover remaining  demand with Boiler
            ############################################

            if supply:
                # sum up maximum boiler supply building by building
                for node in list_supplier_priority:
                    if Q_supply_sum < Q_demand:
                        Q_supply_max = supplier_nodes[node]['Qboiler_nom']
                        Q_supply_sum = Q_supply_sum+Q_supply_max
                        Q_supply_min = supplier_nodes[node]['Qboiler_min']
                        Q_supply_sum_min = Q_supply_sum_min+Q_supply_min
                        dict_supply[node]['Qboiler_nom'][t] = supplier_nodes[node]['Qboiler_nom']
                        # If all demand can be covered by including boilers
                        if Q_supply_sum >= Q_demand:
                            supply = False      # demand is covered, no more suppliers are necessary
                            B_partload = True   # enter the partload loop to fit supply to demand
                            break


            # try to exactly fit supply to demand:
            #   reduce supply by switching last selected supplier's Boiler to partload to reduce remainder
            if B_partload:
                if Q_supply_sum != Q_demand:    # only enter when demand is not exactly met
                    remainder = Q_supply_sum-Q_demand   # Energy that would be wasted if all system ran in nominal condition
                    possible_reduction = supplier_nodes[node]['Qboiler_nom']-supplier_nodes[node]['Qboiler_min']    # possible reduction by switching to min_load
                    ####print('remainder:', remainder)
                    ####print('possible_reduction: ',possible_reduction, 'at node:', node)

                    if remainder < possible_reduction:
                        dict_supply[node]['Qboiler_nom'][t] = possible_reduction-remainder+supplier_nodes[node]['Qboiler_min']
                        ####print('last suppliers B in partload')
                    if remainder >= possible_reduction:
                        dict_supply[node]['Qboiler_nom'][t] = supplier_nodes[node]['Qboiler_nom'] - remainder
                        ####print('last suppliers B in min_load')


            #assert supply == False, ("Demand cannot be covered by LHN")
            '''
            #######################################
            # try to cover remaining demand with EH
            #######################################

            if supply:
                # sum up maximum EH supply building by building
                for node in list_supplier_priority:
                    Q_supply = supplier_nodes[node]['Qeh_nom']
                    Q_supply_sum = Q_supply_sum+Q_supply
                    # Q_supply_min = supplier_nodes[node]['Q_EH_min']
                    # Q_supply_sum_min = Q_supply_sum_min+Q_supply_min
                    dict_supply[node]['Qeh_nom'][t] = supplier_nodes[node]['Qeh_nom']
                    # If all demand can be covered by the EH
                    if Q_supply_sum >= Q_demand:
                        # EH_partload = True
                        break
            '''
            '''
            # try to exactly fit supply to demand:
            #   reduce supply by switching last selected supplier's EH to partload to reduce remainder
            if EH_partload:
                if Q_supply_sum != Q_demand:
                    remainder = Q_supply_sum-Q_demand   # Energy that would be wasted if all system ran in nominal condition
                    possible_reduction = supplier_nodes[node]['Qeh_nom']-supplier_nodes[node]['Q_EH_min']    # possible reduction by switching to min_load
                    print('remainder:', remainder)
                    print('possible_reduction: ',possible_reduction, 'at node:', node)

                    if remainder<possible_reduction:
                        dict_supply[node]['Qeh_nom'][t] = remainder
                        print('last suppliers EH in partload')
                    if remainder>=possible_reduction:
                        dict_supply[node]['Qeh_nom'][t] = supplier_nodes_EH[node]['Q_EH_min']
                        print('last suppliers EH in min_load')
            '''
            ####for node in dict_supply.keys():
                ####print('QCHP',node,': ', dict_supply[node]['Qchp_nom'][t], '\n',
                      ####'Qboiler',node,': ', dict_supply[node]['Qboiler_nom'][t])


        elif LHN_supply_method == 'static':
            #do something
            A=1
            #TODO: implement: CHP and Boiler always operate together


    ####for key in dict_supply.keys():
        ####print("dict_supply_Qboiler:",key,"\n",dict_supply[key]['Qboiler_nom'],'\n')
        ####print("dict_supply_Qchp:",key,"\n",dict_supply[key]['Qchp_nom'],'\n')
        #print("dict_supply_t:\n",dict_supply['1001'],'\n',dict_supply['1002'],'\n',dict_supply['1003'],'\n',dict_supply['1004'],'\n',dict_supply['1005'],'\n',dict_supply['1006'],'\n')
        #print("###########################\n timestep", t, " done \n###########################")


    #def add_LHN_results_to_city_object(dict_supply, City_Object, timesteps):
    for node in dict_supply.keys(): # loop over all buildings with LHN
        Bes = City_Object.nodes[int(node)]['entity'].bes # get Bes from City_Object
        for t in range(timesteps): #timesteps
            if dict_supply[node]['Qboiler_nom'][t] != 0:
                # Add the LHN supply amount to the current stored value
                boiler_supply=dict_supply[str(node)]['Qboiler_nom'][t]+City_Object.nodes[int(node)]['heat_demand_for_boiler'][t]
                if boiler_supply<Bes.boiler.qNominal*Bes.boiler.lowerActivationLimit:
                    #if the needed amount is below LAL run in LAL and waste rest of the energy
                    boiler_supply=Bes.boiler.qNominal*Bes.boiler.lowerActivationLimit
                power_boiler, power_boiler_in = Bes.boiler.calc_boiler_all_results(boiler_supply, t)
            if dict_supply[node]['Qchp_nom'][t] != 0:
                # Add the LHN supply amount to the current stored value
                chp_supply=dict_supply[str(node)]['Qchp_nom'][t]+City_Object.nodes[int(node)]['heat_demand_for_chp'][t]
                boiler_supply = dict_supply[str(node)]['Qboiler_nom'][t] + City_Object.nodes[int(node)]['heat_demand_for_boiler'][t]
                if chp_supply<Bes.chp.qNominal*Bes.chp.lowerActivationLimit:
                    #if the needed amount is below CHP LAL try to shift demand to boiler
                    if chp_supply + boiler_supply <= Bes.boiler.qNominal and chp_supply + boiler_supply > Bes.boiler.qNominal*Bes.boiler.lowerActivationLimit:
                        #  boiler can supply chp_supply in addtion to his load
                        boiler_supply += chp_supply
                        chp_supply = 0
                        power_boiler, power_boiler_in = Bes.boiler.calc_boiler_all_results(boiler_supply, t)
                    elif chp_supply + boiler_supply <= Bes.boiler.qNominal*Bes.boiler.lowerActivationLimit:
                        # if boiler load + chp_supply are below boiler LAL, run boiler at LAL
                        boiler_supply = Bes.boiler.qNominal*Bes.boiler.lowerActivationLimit
                        chp_supply = 0
                        power_boiler, power_boiler_in = Bes.boiler.calc_boiler_all_results(boiler_supply, t)
                    else:
                        # boiler can not cover the additional load, CHP must run at partload
                        chp_supply=Bes.chp.qNominal*Bes.chp.lowerActivationLimit
                (power_thermal_chp, power_electrical_chp, fuel_power_in_chp)=Bes.chp.th_op_calc_all_results(chp_supply, t)


        if Bes.hasChp and Bes.hasBoiler:
            City_Object.nodes[int(node)]['fuel demand'] = Bes.chp.array_fuel_power+Bes.boiler.array_fuel_power
            City_Object.nodes[int(node)]['power_el_chp'] = Bes.chp.totalPOutput
        elif Bes.hasChp == False and Bes.hasBoiler:
            City_Object.nodes[int(node)]['fuel demand'] = Bes.boiler.array_fuel_power



    return City_Object, dict_supply




if __name__ == '__main__':
    city_object=testcity.run_city_generator(list_types=['HP','CHP','CHP','HP','CHP','CHP'],year = 2010,
                timestep = 3600,
                livingArea=[120,130,140,120,130,140],
                b_Space_heat_demand=True,
                specificDemandSH=[100,110,120,100,110,120],
                annualDemandel=[3000, 3000, 3000,3000, 3000, 3000],
                profileType=['H0','H0','H0','H0','H0','H0'],
                methodel=[1,1,1,1,1,1],
                b_domestic_hot_water=False,
                b_el_demand=True,
                roof_usabl_pv_area=[30, 30, 30,30, 30, 30],
                boiler_q_nominal=[3000, 5500, 6000,3000, 5500, 6000],
                boiler_eta=[0.9, 0.9, 0.9,0.9, 0.9, 0.9],
                boiler_lal=[0.5, 0.5, 0.5,0.5, 0.5, 0.5],
                tes_capacity=[700, 700, 700,700, 700, 700],
                tes_k_loss=[0, 0, 0,0,0,0],
                tes_t_max=[95, 95, 95,95, 95, 95],
                eh_q_nominal=[4000, 4000, 4000,4000, 4000, 4000],
                hp_q_nominal=[7000, 7000, 7000,7000, 7000, 7000],
                hp_lal=[0.5, 0.5, 0.5,0.5, 0.5, 0.5],
                chp_p_nominal=[1500, 2000, 2000,1500, 2000, 2000],
                chp_q_nominal=[4000, 5000, 5000,4000, 5000, 5000],
                chp_eta_total=[0.9, 0.9, 0.9,0.9, 0.9, 0.9],
                chp_lal=[0.5, 0.5, 0.5,0.5, 0.5, 0.5],
                PVarea=[30,0,0,30,0,0],
                bat_capacity=[100000,0,0,100000,0,0],
                list_etaCharge=[0.96, 0.96, 0.96,0.96, 0.96, 0.96],
                list_etaDischarge=[0.95, 0.95, 0.95,0.95, 0.95, 0.95]
                )
    Calculator=EB2.calculator(city_object)
    dict_bes_data=Calculator.assembler()
    ####print('Dict city data', dict_bes_data)
    for i in range(len(dict_bes_data)):
        city_object, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data,i)

    #save all results
    with open('all_results.pkl', 'wb') as output:
        pickle.dump(city_object, output, pickle.HIGHEST_PROTOCOL)
        pickle.dump(dict_supply, output, pickle.HIGHEST_PROTOCOL)
    ####print('line just for Breakpoint')




