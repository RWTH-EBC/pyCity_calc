'''
Plot energy_balance results.
'''

import matplotlib.pyplot as plt
import pickle

def plot_all_results(city_object,dict_supply,t_start,t_stop):
    #############################
    # Plot Heat fluxes and demand
    #############################
    placement=1
    nodes = sorted(city_object.get_list_build_entity_node_ids())
    for node in nodes:
        ax = plt.subplot(len(city_object.get_list_build_entity_node_ids()),1,placement) #create as much subplots as there are buildings
        placement=placement+1
        if city_object.node[node]['entity'].bes.hasBoiler == True:
            plt.plot(city_object.node[node]['entity'].bes.boiler.totalQOutput[t_start:t_stop], label='boiler')
            if str(node) in dict_supply:
                plt.plot(dict_supply[str(node)]['Qboiler_nom'][t_start:t_stop], label = 'LHN_boiler_supply')
        if city_object.node[node]['entity'].bes.hasChp == True:
            plt.plot(city_object.node[node]['entity'].bes.chp.totalQOutput[t_start:t_stop], label='chp')
            if str(node) in dict_supply:
                plt.plot(dict_supply[str(node)]['Qchp_nom'][t_start:t_stop], label = 'LHN_chp_supply')
        if city_object.node[node]['entity'].bes.hasTes == True:
            plt.plot(city_object.node[node]['entity'].bes.tes.array_q_discharge[t_start:t_stop], label='tes_out')
            plt.plot(city_object.node[node]['entity'].bes.tes.array_q_charge[t_start:t_stop], label='tes_in')
        if city_object.node[node]['entity'].bes.hasElectricalHeater == True:
            plt.plot(city_object.node[node]['entity'].bes.electricalHeater.totalQOutput[t_start:t_stop], label='EH')
        if city_object.node[node]['entity'].bes.hasHeatpump== True:
            plt.plot(city_object.node[node]['entity'].bes.heatpump.totalQOutput[t_start:t_stop], label='HP')

        plt.plot(city_object.node[node]['entity'].get_space_heating_power_curve()[t_start:t_stop]+city_object.node[node]['entity'].get_dhw_power_curve()[t_start:t_stop], label='demand')

        plt.legend(loc='upper center', shadow=True, fancybox=True)

        ax.get_legend()
        #plt.rc('text', usetex=True)
        #font = {'family': 'serif', 'size': 24}
        #plt.rc('font', **font)

        #plt.xlabel('Time in hours')
        #plt.ylabel('Thermal load in kW')
        #plt.grid()
        #plt.tight_layout()
    plt.show()

    ############################
    # Plot Inputpower and demand
    ############################
    placement=1

    nodes = sorted(city_object.get_list_build_entity_node_ids())
    for node in nodes:
        ax = plt.subplot(len(city_object.get_list_build_entity_node_ids()),1,placement) #create as much subplots as there are buildings
        placement=placement+1
        if city_object.node[node]['entity'].bes.hasBoiler == True:
            plt.plot(city_object.node[node]['entity'].bes.boiler.array_fuel_power[t_start:t_stop], label='boilerfuelin')
            if str(node) in dict_supply:
                plt.plot(dict_supply[str(node)]['Qboiler_nom'][t_start:t_stop], label = 'LHN_boiler_supply')
        if city_object.node[node]['entity'].bes.hasChp == True:
            plt.plot(city_object.node[node]['entity'].bes.chp.array_fuel_power[t_start:t_stop], label='chpfuelin')
            if str(node) in dict_supply:
                plt.plot(dict_supply[str(node)]['Qchp_nom'][t_start:t_stop], label = 'LHN_chp_supply')
        if city_object.node[node]['entity'].bes.hasTes == True:
            plt.plot(city_object.node[node]['entity'].bes.tes.array_q_discharge[t_start:t_stop], label='tes_out')
            plt.plot(city_object.node[node]['entity'].bes.tes.array_q_charge[t_start:t_stop], label='tes_in')
        if city_object.node[node]['entity'].bes.hasElectricalHeater == True:
            plt.plot(city_object.node[node]['entity'].bes.electricalHeater.totalPConsumption[t_start:t_stop], label='EHpowerin')
        if city_object.node[node]['entity'].bes.hasHeatpump== True:
            plt.plot(city_object.node[node]['entity'].bes.heatpump.array_el_power_in[t_start:t_stop], label='HPpowerin')

        plt.plot(city_object.node[node]['entity'].get_space_heating_power_curve()[t_start:t_stop]+city_object.node[node]['entity'].get_dhw_power_curve()[t_start:t_stop], label='demand')

        plt.legend(loc='upper center', shadow=True, fancybox=True)

        ax.get_legend()
            #plt.rc('text', usetex=True)
            #font = {'family': 'serif', 'size': 24}
            #plt.rc('font', **font)

            #plt.xlabel('Time in hours')
            #plt.ylabel('Thermal load in kW')
            #plt.grid()
            #plt.tight_layout()
    plt.show()
    ###########################
    # Plot Storage temperatures
    ###########################
    placement=1
    nodes = sorted(city_object.get_list_build_entity_node_ids())
    for node in nodes:
        ax = plt.subplot(len(city_object.get_list_build_entity_node_ids()),1,placement) #create as much subplots as there are buildings
        placement=placement+1
        if city_object.node[node]['entity'].bes.hasTes == True:
            plt.plot(city_object.node[node]['entity'].bes.tes.array_temp_storage[t_start:t_stop], label='T_tes')
            plt.plot([city_object.node[node]['entity'].bes.tes.t_min]*(t_stop-t_start), label='T_tes_min')
            plt.plot([city_object.node[node]['entity'].bes.tes.tMax]*(t_stop-t_start), label='T_tes_max')
        #plt.plot(city_object.node[node]['entity'].apartments[0].demandSpaceheating.loadcurve[t_start:t_stop], label='demand')

        plt.legend(loc='upper center', shadow=True, fancybox=True)

        ax.get_legend()
            #plt.rc('text', usetex=True)
            #font = {'family': 'serif', 'size': 24}
            #plt.rc('font', **font)

            #plt.xlabel('Time in hours')
            #plt.ylabel('Thermal load in kW')
            #plt.grid()
            #plt.tight_layout()
    plt.show()

    ###########################
    # Plot Electric demands and Supply
    ###########################
    placement=1
    nodes = sorted(city_object.get_list_build_entity_node_ids())
    for node in nodes:
        ax = plt.subplot(len(city_object.get_list_build_entity_node_ids()),1,placement) #create as much subplots as there are buildings
        placement=placement+1
        plt.plot(city_object.node[node]['entity'].get_electric_power_curve()[t_start:t_stop], label='demand',color='green')
        if city_object.node[node]['entity'].bes.hasChp == True:
            plt.plot(city_object.node[node]['entity'].bes.chp.totalPOutput[t_start:t_stop], label='chp_supply',color='blue')
            plt.plot(city_object.node[node]['chp_sold'][t_start:t_stop], label='chp_sold',color='cyan')
            plt.plot(city_object.node[node]['chp_used_self'][t_start:t_stop], label='chp_used_self',color='darkslateblue')
        if city_object.node[node]['entity'].bes.hasPv == True:
            plt.plot(city_object.node[node]['entity'].bes.pv.getPower()[t_start:t_stop], label='pv_supply',color='red')
            plt.plot(city_object.node[node]['pv_sold'][t_start:t_stop], label='pv_sold',color='brown')
            plt.plot(city_object.node[node]['pv_used_self'][t_start:t_stop], label='pv_used_self',color='lightsalmon')
        if city_object.node[node]['entity'].bes.hasBattery == True:
            plt.plot(city_object.node[node]['batt_load'][t_start:t_stop], label='batt_load',color='black')
            plt.plot(city_object.node[node]['batt_unload'][t_start:t_stop], label='batt_unload',color='grey')
        #if city_object.node[node]['entity'].bes.hasHeatpump == True:
        #    plt.plot(city_object.node[node]['electricity_heatpump'][t_start:t_stop], label='demand_hp',color='purple')


        plt.legend(loc='upper center', shadow=True, fancybox=True)

        ax.get_legend()
            #plt.rc('text', usetex=True)
            #font = {'family': 'serif', 'size': 24}
            #plt.rc('font', **font)

            #plt.xlabel('Time in hours')
            #plt.ylabel('Thermal load in kW')
            #plt.grid()
            #plt.tight_layout()
    plt.show()


    ###########################
    # Plot SOC of Battery
    ###########################
    if city_object.node[node]['entity'].bes.hasBattery == True:
        placement = 1
        nodes = sorted(city_object.get_list_build_entity_node_ids())
        for node in nodes:
            ax = plt.subplot(len(city_object.get_list_build_entity_node_ids()), 1,
                             placement)  # create as much subplots as there are buildings
            placement = placement + 1

            plt.plot(city_object.node[node]['entity'].bes.battery.totalSoc[t_start:t_stop], label='SOC')
            plt.plot([city_object.node[node]['entity'].bes.battery.capacity] * (t_stop - t_start), label='SOC_max')
            plt.plot([0] * (t_stop - t_start), label='SOC_min')

            plt.legend(loc='upper center', shadow=True, fancybox=True)

            ax.get_legend()
            # plt.rc('text', usetex=True)
            # font = {'family': 'serif', 'size': 24}
            # plt.rc('font', **font)

            # plt.xlabel('Time in hours')
            # plt.ylabel('Thermal load in kW')
            # plt.grid()
            # plt.tight_layout()
        plt.show()


if __name__ == '__main__':
    with open('all_results.pkl', 'rb') as input:
        city_object = pickle.load(input)
        dict_supply = pickle.load(input)
    plot_all_results(city_object,dict_supply,t_start=0,t_stop=200)