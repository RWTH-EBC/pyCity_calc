from __future__ import division
__author__ = 'jsc-nle'

import pycity_calc.extern_el_grid.PowerGrid as grid
import pycity_calc.data.El_grid.RealisticData as data
from pycity_calc.test.pycity_calc_fixtures import fixture_building, \
    fixture_environment, fixture_city, fixture_apartment, fixture_th_demand, \
    fixture_el_demand

class Test_PowerGrid(object):
    """
    Test class for PowerGrid
    """
    def test_PowerGrid_init(self, fixture_environment, fixture_building):
        """
        test method to check method for creating power grids
        """
        #   create building list
        test_building_list = [fixture_building, fixture_building, fixture_building]
        #   create power grid
        test_PowerGrid = grid.PowerGrid(test_building_list, fixture_environment)

        assert test_PowerGrid.grid_type == "ruraloverhead1"
        assert test_PowerGrid.medium_voltage == 20
        assert test_PowerGrid.number_of_buildings == len(test_building_list)

    def test_create_reference_grid(self, fixture_environment, fixture_building):
        """
        test method to check method for creating reference grids
        """
        #   create building list
        test_building_list = [fixture_building,fixture_building, fixture_building]
        #   create power grid
        test_grid = grid.PowerGrid(building_list=test_building_list,
                                   environment=fixture_environment,
                                   grid_type="ruraloverhead1")
        #   create refrence grid
        test_grid.create_reference_grid()

        #   test create_slack_transformer()
        assert len(test_grid.transformers) > 0

        #   test create_standard_busses()
        for bus_number in range(len(test_grid.bus)):
            if bus_number > 0:
                #   bus type (BUS_TYPE)
                assert test_grid.bus[bus_number][1] == 1.0
                #   voltage magnitude at bus (VM) in p.u.
                assert test_grid.bus[bus_number][7] == 1.0
                #   base voltage (BASE_KV in kV)
                assert test_grid.bus[bus_number][9] == 0.400

        #   test create_lines()
        assert test_grid.line_lengths[0][1] == 0.0
        for bus in range(2,len(test_grid.line_lengths)):
            assert test_grid.line_lengths[bus-1][bus] == 0.021

        #   test create_branch()
        for bus in range(2,len(test_grid.line_lengths)):
            test_ref_impedance = (test_grid.bus[bus-1][9] * test_grid.bus[bus-1][9]) / test_grid.baseMVA
            assert test_grid.branch[bus-1][2] == data.cabledata["NFA2X 4X70"]["RperKm"] * \
                                                         test_grid.line_lengths[bus-1][bus] / test_ref_impedance

    def test_create_city_district(self, fixture_environment, fixture_building):
        """
        test method to check method for creating city districts
        """
        #   create building list
        test_building_list = [fixture_building, fixture_building, fixture_building]
        #   create power grid
        test_grid = grid.PowerGrid(building_list=test_building_list,
                                   environment=fixture_environment,
                                   grid_type="ruraloverhead1")
        #   create city district
        test_grid.create_city_district()

        assert len(test_grid.city_district.nodelist_building) == len(test_building_list)
        assert len(test_grid.city_district.node) == test_grid.numberofbusses

    # def test_power_flow_calculation(self, fixture_environment, fixture_building):
    #     """
    #     test method to check method for power flow calculations
    #     """
    #     test_start = 4
    #     test_end = 20
    #     #   create building list
    #     test_building_list = [fixture_building, fixture_building, fixture_building]
    #     #   create power grid
    #     test_grid = grid.PowerGrid(building_list=test_building_list,
    #                                environment=fixture_environment,
    #                                grid_type="ruraloverhead1")
    #     #   create city district
    #     test_grid.create_city_district()
    #     #   run power flow calculation
    #     test_results = test_grid.power_flow_calculation(start=test_start, end=test_end, save=False)
    #
    #     assert len(test_results) == (test_end-test_start+1)
    #
    # def test_power_flow_evaluation(self, fixture_environment, fixture_building):
    #     """
    #     test method to check method for power flow evaluations
    #     """
    #     test_start = 4
    #     test_end = 20
    #     #   create building list
    #     test_building_list = [fixture_building, fixture_building, fixture_building]
    #     #   create power grid
    #     test_grid = grid.PowerGrid(building_list=test_building_list,
    #                                environment=fixture_environment,
    #                                grid_type="ruraloverhead1")
    #     #   create city district
    #     test_grid.create_city_district()
    #     #   run power flow calculation
    #     test_results = test_grid.power_flow_calculation(start=test_start, end=test_end, save=False)
    #     #   run power flow evaluation
    #     test_res_city_district = test_grid.power_flow_evaluation(test_results)
    #
    #     for n in test_res_city_district.node:
    #         if test_res_city_district.nodes[n]['node_type'] == 'building':
    #             if test_res_city_district.nodes[n]['entity']._kind == 'building':
    #                 assert (test_res_city_district.nodes[n]['real_power_demand'][0]*10**3)\
    #                    == test_res_city_district.nodes[n]['entity'].get_electric_power_curve()[test_start]
    #
    #     assert test_res_city_district.nodes[1001]['voltage'][0] == test_grid.medium_voltage
    #
    #
    #
