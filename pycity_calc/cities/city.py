# coding=utf-8
"""
Pycity_calc city class (as inheritance from citydistrict class of pycity)
"""
from __future__ import division

try:
    import pycity_base
except:  # pragma: no cover
    ImportError('Package pycity_base is not found. Please install pycity first.' +
                'https://github.com/RWTH-EBC/pyCity')

import pycity_base.classes.CityDistrict as citydist


class City(citydist.CityDistrict):
    """
    City class of PyCity calculator.
    """
    def __init__(self, environment=None):
        """
        City class. Inheritance from PyCity CityDistrict object
        (which is based on networkx graph)

        Parameter
        ---------
        environment: Environment object, optional
            Environment object of PyCity (default: None)

        Example
        -------
        >>> import pycity_base.classes.Timer as time
        >>> import pycity_base.classes.Weather as weath
        >>> import pycity_base.classes.Prices as price
        >>> import pycity_base.classes.Environment as env
        >>> timer = time.Timer()
        >>> weather = weath.Weather(timer)
        >>> prices = price.Prices()
        >>> environment = env.Environment(timer, weather, prices)
        >>> city = City(environment)
        """

        # Initialize City with inheritance from pycity citydistrict object
        super(City, self).__init__(environment)

    def add_extended_building(self, extended_building, position, name=None):
        """
        Add extended building object into city.

        Parameters
        ----------
        extended_building : object
            BuildingExtended object of PyCity
        position : shapely.geometry.Point object
            New node's position
        name : str, optional
            Name of entity (default: None)

        Returns
        -------
        node_number : int
            Number of node
        """

        if self.environment is None:  # pragma: no cover
            self.environment = extended_building.environment  # pragma: no cover

        node_number = self.addEntity(entity=extended_building,
                                     position=position, name=name,
                                     is_supply_electricity=False)

        return node_number

    def get_annual_space_heating_demand(self, nodelist=None):
        """
        Returns annual space heating demand of all buildings within city

        Parameters
        ----------
        nodelist : list (of ints), optional
            Defines which nodes should be used to return annual space
            heating demand in kWh (default: None).
            If nodelist is None, all nodes with building entities will
            be used.

        Returns
        -------
        ann_heat_demand : float
            Annual space heating demand in kWh
        """

        ann_heat_demand = 0

        if nodelist is None:
            use_nodes = self
        else:
            for n in nodelist:
                assert n in self.nodes(), ('Node ' + str(n) + 'is not '
                                           'within city object!')
            use_nodes = nodelist

        #  Loop over all nodes
        for n in use_nodes:
            #  If node holds attribute 'node_type'
            if 'node_type' in self.node[n]:
                #  If node_type is building
                if self.node[n]['node_type'] == 'building':
                    #  If entity is kind building
                    if self.node[n]['entity']._kind == 'building':
                        ann_heat_demand += self.node[n]['entity'].\
                            get_annual_space_heat_demand()

        return ann_heat_demand

    def get_annual_el_demand(self, nodelist=None):
        """
        Returns annual electrical demand of all buildings within city

        Parameters
        ----------
        nodelist : list (of ints), optional
            Defines which nodes should be used to return annual electricity
            demand in kWh (default: None).
            If nodelist is None, all nodes with building entities will
            be used.

        Returns
        -------
        ann_el_demand : float
            Annual electrical demand in kWh
        """

        if nodelist is None:
            use_nodes = self
        else:
            for n in nodelist:
                assert n in self.nodes(), ('Node ' + str(n) + 'is not '
                                           'within city object!')
            use_nodes = nodelist

        ann_el_demand = 0

        #  Loop over all nodes
        for n in use_nodes:
            #  If node holds attribute 'node_type'
            if 'node_type' in self.node[n]:
                #  If node_type is building
                if self.node[n]['node_type'] == 'building':
                    #  If entity is kind building
                    if self.node[n]['entity']._kind == 'building':
                        ann_el_demand += self.node[n]['entity'].\
                            get_annual_el_demand()

        return ann_el_demand

    def get_annual_dhw_demand(self, nodelist=None):
        """
        Returns annual hot water energy demand of all buildings within city

        Parameters
        ----------
        nodelist : list (of ints), optional
            Defines which nodes should be used to return annual hot water
            heating demand in kWh (default: None).
            If nodelist is None, all nodes with building entities will
            be used.

        Returns
        -------
        ann_dhw_demand : float
            Annual  hot water energy demand in kWh
        """

        if nodelist is None:
            use_nodes = self
        else:
            for n in nodelist:
                assert n in self.nodes(), ('Node ' + str(n) + 'is not '
                                           'within city object!')
            use_nodes = nodelist

        ann_dhw_demand = 0

        #  Loop over all nodes
        for n in use_nodes:
            #  If node holds attribute 'node_type'
            if 'node_type' in self.node[n]:
                #  If node_type is building
                if self.node[n]['node_type'] == 'building':
                    #  If entity is kind building
                    if self.node[n]['entity']._kind == 'building':
                        ann_dhw_demand += self.node[n]['entity'].\
                            get_annual_dhw_demand()

        return ann_dhw_demand

    def get_total_annual_th_demand(self, nodelist=None):
        """
        Returns annual space heating and hot water energy demand
        of all buildings within city

        Parameters
        ----------
        nodelist : list (of ints), optional
            Defines which nodes should be used to return annual thermal
            demand in kWh (default: None).
            If nodelist is None, all nodes with building entities will
            be used.

        Returns
        -------
        total_th_demand : float
            Annual space heatin and hot water energy demand in kWh
        """

        total_th_demand = self.get_annual_space_heating_demand(nodelist=
                                                               nodelist) \
                          + self.get_annual_dhw_demand(nodelist=nodelist)

        return total_th_demand
