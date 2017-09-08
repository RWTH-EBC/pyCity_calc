#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script exports buildings of city object into vDistrict

"""
from __future__ import division

import os
import pickle
import datetime
import pytz
from shapely.geometry import Polygon
import pandas as pd

import pycity_calc.cities.scripts.city_generator.city_generator as citgen

from vdistrict.citydb.models import BuildingEnergy
from vdistrict.citydb.models import CityObject
from vdistrict.citydb.models import ObjectClass
from vdistrict.citydb.models import UsageZone
from vdistrict.citydb.models import ThermalZone
from vdistrict.citydb.models import ThermalBoundary
from vdistrict.citydb.models import ThermalOpening
from vdistrict.citydb.models import Construction
from vdistrict.citydb.models import Layer
from vdistrict.citydb.models import LayerComponent
from vdistrict.citydb.models import SolidMaterial
from vdistrict.citydb.models import SurfaceGeometry
from vdistrict.citydb.models import ThematicSurface
from vdistrict.citydb.models import EnergyConversionSystem
from vdistrict.citydb.models import HeatExchanger
from vdistrict.citydb.models import IrregularTimeSeries
from vdistrict.citydb.models import MappingBWZK
from vdistrict.citydb.models import MappingDIN

from vdistrict.citydb.models import Node
from vdistrict.citydb.models import Pipe
from vdistrict.citydb.models import ProtectiveElement
from vdistrict.citydb.models import Edge

from vdistrict.citydb.models import Scenario

from django.contrib.gis.geos import GEOSGeometry
import math
import pickle
from django.db import IntegrityError

try:
    import vdistrict as vd
except:
    msg = 'Could not import vDistrict, which can be found at: ' \
          'https://git.rwth-aachen.de/EBC/Team_UES/living-roadmap/vDistrict '
    raise ImportError(msg)


def export_city_to_vdistrict(city):
    """

    Parameters
    ----------
    city

    Returns
    -------

    Annotations
    -----------
    CityGML parameter reference:
    http://en.wiki.quality.sig3d.org/index.php/Modeling_Guide_for_3D_Objects_-_Part_2:_Modeling_of_Buildings_(LoD1,_LoD2,_LoD3)#Building_.28bldg:Building.29
    """
    #  Get building entity list
    list_build_ids = city.get_list_build_entity_node_ids()

    #  Loop over buildings
    for n in list_build_ids:
        #  Building pointer
        build = city.node[n]['entity']

        #  Generate new vDistrict building
        vbuild = vd.modules.energy.buildingphysics.buildingenergy.BuildingEnergy()

        #  City id (foreign key)
        vbuild.id = None

        #  Building unique id
        vbuild.gml_id = n

        #  Get information about usage (as string, based on build_type int)
        build_info = citgen.conv_build_type_nb_to_name(build.build_type)

        #  Class
        #  http://www.sig3d.org/codelists/Handbuch-SIG3D/building/2.0/CL-V1.0/_AbstractBuilding_class.xml
        vbuild.class_field = build_info

        vbuild.class_codespace = 'pyCity_calc description'

        vbuild.function = None  # bldg_cf.function
        vbuild.function_codespace = "BWZK"

        #  Year of construction
        if build.mod_year is not None:
            assert build.mod_year >= 1800
            vbuild.year_of_construction = datetime.date(
                build.mod_year, 1, 1)
        else:
            vbuild.year_of_construction = datetime.date(
                build.build_year, 1, 1)

        # bldg_vd.year_of_construction = datetime.date(
        #     bldg_cf.year_of_construction, 1, 1)

        #  Measured_heigh
        if build.height_of_floors is not None and build.nb_of_floors is not None:
            vbuild.measured_height = build.height_of_floors * build.nb_of_floors

        vbuild.measured_height_unit = "urn:adv:uom:m"

        if build.nb_of_floors is not None:
            vbuild.storeys_above_ground = build.nb_of_floors

        if build.height_of_floors is not None:
            vbuild.storey_heights_above_ground = build.height_of_floors

        if build.net_floor_area is not None:
            vbuild.floor_area = build.net_floor_area

        #  Fixme: Add corresponding geographic refs
        # vbuild.surface_geometry.polygon = Polygon(
        #     bldg_cf.surface_geometry.polygon)
        # vbuild.reference_point = GEOSGeometry(
        #     str(bldg_cf.surface_geometry.polygon.centroid), srid=25832)

        vbuild.save()

        # city_object_vd = _generate_city_object(
        #     gmlid=bldg_cf.name,
        #     classname='Building',
        #     description=bldg_cf.description)

        # bldg_vd.id = city_object_vd
        # bldg_vd.name = city_object_vd.gmlid
        # bldg_vd.building_parent =
        # bldg_vd.building_root =
        #bldg_vd.class_field = bldg_cf.description
        # bldg_vd.class_codespace = "FZJ description of building"
        # bldg_vd.function = bldg_cf.function
        # bldg_vd.function_codespace = "BWZK"
        # bldg_vd.year_of_construction = datetime.date(
        #     bldg_cf.year_of_construction, 1, 1)
        # bldg_vd.measured_height = bldg_cf.measured_height
        # bldg_vd.measured_height_unit = "urn:adv:uom:m"
        # bldg_vd.storeys_above_ground = bldg_cf.storeys_above_ground
        # bldg_vd.storeys_below_ground = bldg_cf.storeys_below_ground
        # bldg_vd.floor_area = bldg_cf.net_floor_area
        # bldg_cf.surface_geometry.polygon = Polygon(
        #     bldg_cf.surface_geometry.polygon)
        # bldg_vd.reference_point = GEOSGeometry(
        #     str(bldg_cf.surface_geometry.polygon.centroid), srid=25832)

        # bldg_vd.save()

        # city_object_thematic_vd = _generate_city_object(
        #     gmlid="surface" + bldg_vd.id.gmlid,
        #     classname='BuildingGroundSurface')
        # them_vd = ThematicSurface()
        # them_vd.id = city_object_thematic_vd
        # them_vd.objectclass = city_object_thematic_vd.objectclass
        # them_vd.building = bldg_vd
        #
        # them_vd.save()

        # geom_vd = SurfaceGeometry()
        # geom_vd.gmlid = bldg_vd.id.gmlid
        # geom_vd.geometry = GEOSGeometry(
        #     str(bldg_cf.surface_geometry.geometry), srid=25832)
        #
        # geom_vd.cityobject = city_object_thematic_vd
        # geom_vd.save()
        #
        # them_vd.lod2_multi_surface
        # them_vd.save()
        # bldg_vd.lod2_solid = geom_vd

        return vbuild

"""
    Parameters
    ----------
    cityobject : cityobject Python object
        the default value is None

    main_building : building Python object
        if the instance is a subbuilding you should hand over the
        main_building as a building python object.
        the default value is None

    Attributes
    ----------

    Attributes of building SQL table

    id_building : int
        this is the individual id from SQL building table
    name : str
        if the class is instantiated based on something different then SQL
        data base, the name can be specified. The setter tries to handle the
        given name, thus it fits the requirements of the data base (e.g.
        replacing whitespaces) the default value is None
    building_parent_id : int
        SQL id for parent building, if this building is a subbuilding
    building_root_id : int
        SQL id for root building. This is a quite important attribute as it
        allows the trace back to the original building.
    description : str
        the description contains building description and additional
        information if data was transferred from old DB
    function : str
        the function contains a string with  the germen BWZK of the building.
        (Bauwerkszuordnungskatalog)
    year_of_construction : int
        the year of construction of the building
    measured_height : float [m]
        the measured total height of the building
    storeys_above_ground : int
        number of storeys of the building that are above ground level
    storeys_below_ground : int
        number of storeys of the building that are below ground level (celler)
    lod2_geometry_id : int
        SQL id for foreign key relationship to surface_geometry table in SQL

    Attributes of building_campus SQL table

    id_building_campus : int
        this is the individual id from SQL building_campus table
    number_campus_building : str
        this is the building name (duplicate of building.name)
    campus_building_parent_id : int
        SQL ID to main building in building_campus.
    owner : str
        this is the owner of the building (typically FZJ or JEN)
    id_campus : int
        this is the individual id for foreign key relationship to campus SQL
        table (typically this is 7 for FZJ)
    is_physical_building: bool
        this indicates if the building is a physical building or just a
        container for subbuildings. There is always one container for
        subbuilding that is not physical, all subbuildings are physical.
    is_subbuilding : bool
        this indicates if the building is a subbuilding or not. Kind of
        duplicate but can be helpful if theortically the subbuilding has
        subbuildings

    Attributes of building_energy SQL table

    id_building_energy : int
        this is the individual id from SQL building_energy table
    number_bldg_energy : int
        this is the building name (duplicate of building.name)
    net_floor_area : float [m2]
        this is the total used net floor area of the building (all storeys)
    id_parent : int
        SQL id of parent (not sure why we need this, implemented because of
        insert)

    Attributes of DBCampusAPI

    sub_buildings : list
        a list containing all subbuildings (Building python objects)
    usage_zones : list
        a list containing all usage zones (UsageZone python objects)
    surface_components : list
        a list containing all surface components (SurfaceComponent
        python objects)
    surface_geometry : SurfaceGeometry python object
        foreign key relationship to surface_geometry, represented by python
        object
    select_success : bool
        Boolean of the select_id function was successful or not
    sensors : list
        a list containing all sensors in this building (Sensor python object)
    energy_systems : list
        a list containing all energy systems of this building (
        EnergyConversionSystem python object)
    building_res : BuildingRes object
        BuildingRes object that contains simulation data
    sim_data : list
        a list containing all sensors that are connected to simulation data
        from data base

# attributes of (sub)building
        self.name = None
        self.building_parent_id = None
        self.building_root_id = None
        self.description = None
        self.id_building = None
        self.function = None
        self.year_of_construction = None
        self.measured_height = None
        self.storeys_above_ground = 0
        self.storeys_below_ground = 0
        self.lod2_geometry_id = None

        # attributes of building_campus
        self.id_building_campus = None
        self.number_campus_building = self.name
        self.campus_building_parent_id = None
        self.owner = None
        self.id_campus = 7
        self.is_physical_building = None
        self.is_subbuilding = None

        # attributes of building_energy
        self.id_building_energy = None
        self.number_bldg_energy = self.name
        self.net_floor_area = None
        self.id_parent = None

        # attributes of DBCampusAPI
        self.cityobject = cityobject
        self.main_building = main_building
        self.sub_buildings = []
        self.usage_zones = []
        self.surface_components = []
        self.surface_geometry = None
        self.sensors = []
        self.energy_systems = []
        self.building_res = None
        self.sim_data = []
        self.select_success = False
"""


# #  Copy of campflow transfer data
# def building_data(bldg_cf):
#     """Transfer building data from CampFlow to vDistrict.
#
#     Semantic and geometric information transfer for buildings
#
#     Parameters
#     ----------
#     bldg_cf : CampFlow Building class
#         Building class of CampFlow
#
#     Returns
#     -------
#     bldg_vd : vDistrict Building class
#         Building class of vDistrict
#
#     """
#
#     city_object_vd = _generate_city_object(
#         gmlid=bldg_cf.name,
#         classname='Building',
#         description=bldg_cf.description)
#
#     bldg_vd = BuildingEnergy()
#     bldg_vd.id = city_object_vd
#     bldg_vd.name = city_object_vd.gmlid
#     # bldg_vd.building_parent =
#     # bldg_vd.building_root =
#     bldg_vd.class_field = bldg_cf.description
#     bldg_vd.class_codespace = "FZJ description of building"
#     bldg_vd.function = bldg_cf.function
#     bldg_vd.function_codespace = "BWZK"
#     bldg_vd.year_of_construction = datetime.date(
#         bldg_cf.year_of_construction, 1, 1)
#     bldg_vd.measured_height = bldg_cf.measured_height
#     bldg_vd.measured_height_unit = "urn:adv:uom:m"
#     bldg_vd.storeys_above_ground = bldg_cf.storeys_above_ground
#     bldg_vd.storeys_below_ground = bldg_cf.storeys_below_ground
#     bldg_vd.floor_area = bldg_cf.net_floor_area
#     bldg_cf.surface_geometry.polygon = Polygon(
#         bldg_cf.surface_geometry.polygon)
#     bldg_vd.reference_point = GEOSGeometry(
#         str(bldg_cf.surface_geometry.polygon.centroid), srid=25832)
#
#     bldg_vd.save()
#
#     city_object_thematic_vd = _generate_city_object(
#         gmlid="surface" + bldg_vd.id.gmlid,
#         classname='BuildingGroundSurface')
#     them_vd = ThematicSurface()
#     them_vd.id = city_object_thematic_vd
#     them_vd.objectclass = city_object_thematic_vd.objectclass
#     them_vd.building = bldg_vd
#
#     them_vd.save()
#
#     geom_vd = SurfaceGeometry()
#     geom_vd.gmlid = bldg_vd.id.gmlid
#     geom_vd.geometry = GEOSGeometry(
#         str(bldg_cf.surface_geometry.geometry), srid=25832)
#
#     geom_vd.cityobject = city_object_thematic_vd
#     geom_vd.save()
#
#     them_vd.lod2_multi_surface
#     them_vd.save()
#     bldg_vd.lod2_solid = geom_vd
#     bldg_vd.save()
#
#     return bldg_vd
#
# #  Copy of CampFlow
# def _generate_city_object(gmlid, classname, description=None):
#     """Generate a CityObject object.
#
#     This is a helper function to generate a CityObject ORM object.
#
#     Parameters
#     ----------
#     gmlid : str
#         Value of the gmlid.
#     classname : str
#         Classname of the code list of objectsclass table.
#     description : str
#         Decription of that instance
#
#     Returns
#     -------
#     city_object_vd : CityObject object
#         vDistrict CityObject instance.
#
#     """
#     city_object_vd = CityObject()
#     city_object_vd.gmlid = gmlid
#     city_object_vd.objectclass = ObjectClass.objects.get(classname=classname)
#     city_object_vd.name = classname + "_" + gmlid
#     city_object_vd.description = description
#     city_object_vd.creation_date = datetime.datetime.now(
#         pytz.timezone('Europe/Berlin'))
#     city_object_vd.last_modification_date = datetime.datetime.now(
#         pytz.timezone('Europe/Berlin'))
#     city_object_vd.updating_person = 'pre'
#     city_object_vd.reason_for_update = 'Transfer from CampFlow to vDistrict'
#     city_object_vd.save()
#
#     return city_object_vd


if __name__ == '__main__':
    this_path = os.path.dirname(os.path.abspath(__file__))

    city_f_name = 'city_3_buildings.pkl'

    city_path = os.path.join(this_path, 'input', city_f_name)

    city = pickle.load(open(city_path, mode='rb'))
