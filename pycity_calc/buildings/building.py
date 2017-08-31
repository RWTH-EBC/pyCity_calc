# coding=utf-8
"""
Extended building class (inheritance from building class of pycity).
BuildingExtended holds further attributes, which are necessary for
TEASER usage.
"""
from __future__ import division
from __future__ import division
from __future__ import division
import warnings
import numpy as np

import pycity_base.classes.Building as build
import pycity_calc.toolbox.unit_conversion as unitcon


class BuildingExtended(build.Building):
    """
    BuildingExtended class (inheritance from building class of pycity)
    """
    def __init__(self, environment, build_year=None, mod_year=None,
                 build_type=None, roof_usabl_pv_area=None, net_floor_area=None,
                 ground_area=None, height_of_floors=None,
                 nb_of_floors=None, neighbour_buildings=None,
                 residential_layout=None, attic=None, cellar=None,
                 construction_type=None, dormer=None, with_ahu=None,
                 office_layout=None, window_layout=None,
                 retrofit_state = None):
        """
        Constructor of extended building. Inheritance from PyCity Building
        object.

        Parameters
        ----------
        environment : Environment object
            Environment object of PyCity
        build_year : int, optional
            Year of construction of building (default: None)
        mod_year :  int, optional
            Last year of modernization / retrofit (default: None)
        build_type : int, optional
            Number of building type (default: None)
            (0 - residential, 1 - office, others - non-res)
        roof_usabl_pv_area : float, optional
            Usable area for pv system (default: None)
        net_floor_area : float, optional
            Total net leased area of building in m^2 (default: None)
        ground_area : float, optional
            Building ground floor area in m^2 (default: None)
        height_of_floors : int, optional
            Average height of single floor in m (default: None)
        nb_of_floors : int, optional
            Building number of floors (default: None)
        neighbour_buildings : int, optional
            Integer to define way of interconnection to other houses
            (default: None)
            0: no neighbour (stand alone)
            1: one neighbour (semi-detached house)
            2: two neighbours (row house)
        residential_layout : int, optional
            type of floor plan (default = None)
            0: compact
            1: elongated/complex
        attic : int, optional
            type of attic (default = None)
            0: flat roof
            1: non heated attic
            2: partly heated attic
            3: heated attic
        cellar : int, optional
            type of cellar (default = None)
            0: no cellar
            1: non heated cellar
            2: partly heated cellar
            3: heated cellar
        construction_type : str, optional
            construction type (default = None)
            heavy: heavy construction
            light: light construction
        dormer : str, optional
            construction type (default = None)
            0: no dormer
            1: dormer
        with_ahu : bool, optional
            Defines, if building holds air handling unit (AHU)
            (default: False)
        office_layout : int, optional
            type of floor plan (for offices) (default: None)
            Options:
            0: use default values
            1: elongated 1 floor
            2: elongated 2 floors
            3: compact
        window_layout : int, optinoal
            type of window layout (for offices) (default: None)
            Options:
            0: use default values
            1: punctuated facade
            2: banner facade
            3: full glazing
        retrofit_state: int, optional
            Defines the state of retrofit
            0: mainly retrofitted
            1: slightly retrofitted
            2: not retrofitted

        Examples
        --------
        >>> import pycity_base.classes.Timer as time
        >>> import pycity_base.classes.Weather as weath
        >>> import pycity_base.classes.Prices as price
        >>> import pycity_base.classes.Environment as env
        >>> timer = time.Timer()
        >>> weather = weath.Weather(timer)
        >>> prices = price.Prices()
        >>> environment = env.Environment(timer, weather, prices)
        >>> extended_building = BuildingExtended(environment)
        """

        #  Initialize superclass
        super(BuildingExtended, self).__init__(environment)

        #  Set initial parameters
        self.build_year = build_year
        self.mod_year = mod_year
        self.build_type = build_type
        self.roof_usabl_pv_area = roof_usabl_pv_area
        self.net_floor_area = net_floor_area
        self.ground_area = ground_area
        self.height_of_floors = height_of_floors
        self.nb_of_floors = nb_of_floors
        self.neighbour_buildings = neighbour_buildings
        self.residential_layout = residential_layout
        self.attic = attic
        self.cellar = cellar
        self.construction_type = construction_type
        self.dormer = dormer
        self.with_ahu = with_ahu
        self.office_layout = office_layout
        self.window_layout = window_layout
        self.retrofit_state = retrofit_state

    def get_annual_space_heat_demand(self):
        """
        Returns annual space heating demand in kWh/a

        Returns
        -------
        ann_heat_demand : float
            Annual space heating demand
        """

        power_curve = self.get_space_heating_power_curve()

        energy_curve = power_curve * self.environment.timer.timeDiscretization

        #  Sum in Ws
        annual_demand = np.sum(energy_curve)

        #  Convert Ws to kWh
        ann_heat_demand = unitcon.con_joule_to_kwh(annual_demand)

        return ann_heat_demand

    def get_annual_el_demand(self):
        """
        Returns annual electrical demand in kWh/a

        Returns
        -------
        ann_el_demand : float
            Annual space heating demand
        """

        power_curve = self.get_electric_power_curve()

        energy_curve = power_curve * self.environment.timer.timeDiscretization

        #  Sum in Ws
        annual_demand = np.sum(energy_curve)

        #  Convert Ws to kWh
        ann_el_demand = unitcon.con_joule_to_kwh(annual_demand)

        return ann_el_demand

    def get_annual_dhw_demand(self):
        """
        Returns annual hot water energy demand in kWh/a

        Returns
        -------
        ann_dhw_demand : float
            Annual hot water energy demand
        """

        power_curve = self.get_dhw_power_curve()

        energy_curve = power_curve * self.environment.timer.timeDiscretization

        #  Sum in Ws
        annual_demand = np.sum(energy_curve)

        #  Convert Ws to kWh
        ann_dhw_demand = unitcon.con_joule_to_kwh(annual_demand)

        return ann_dhw_demand

    def get_build_total_height(self):
        """
        Returns building total height value, if it is defined. Otherwise,
        returns None

        Returns
        -------
        height : float
            Building height in meters
        """

        if (self.height_of_floors is not None and
                    self.nb_of_floors is not None):
            return self.height_of_floors * self.nb_of_floors
        else:
            return None