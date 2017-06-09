# coding=utf-8
"""
Functions for usage of TEASER typebuildings with pycity_calc
"""

import os
import numpy as np
import warnings
import copy

import pycity.classes.Weather as Weather
import pycity.classes.demand.Occupancy as occ
import pycity.classes.demand.ElectricalDemand as eldem
import pycity.classes.demand.Apartment as Apartment
import pycity.classes.demand.SpaceHeating as spheat
import pycity.functions.changeResolution as chres

import pycity_calc.buildings.building as build_ex
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time

import pycity_calc.toolbox.user.user_air_exchange as usair

try:
    from teaser.project import Project
except:
    raise ImportError('Could not import TEASER package. Please check your '
                      'installation. TEASER can be found at: '
                      'https://github.com/RWTH-EBC/TEASER. '
                      'Installation is possible via pip. Alternatively, '
                      'you might have run into trouble with XML bindings in '
                      'TEASER. This can happen if you try to re-import TEASER '
                      'within an active Python console. Please close the '
                      'active Python console and open another one. Then '
                      'try again.')
try:
    import teaser.logic.simulation.VDI_6007.low_order_VDI as low_order_vdi
    import teaser.logic.simulation.VDI_6007.weather as vdiweather
    import teaser.logic.simulation.VDI_6007.equal_air_temperature as equ_air
except:
    msg = 'Could not import TEASER VDI 6007 core. You might be on the wrong' \
          ' branch. Look for issue297_vdi_core branch.'
    raise ImportError(msg)

def create_teaser_project(load_data=True, name=None, merge_windows=True):
    """
    Creates a new teaser Project and sets the calculation method to "vdi"

    Parameters
    ----------
    load_data : bool, optional
        Defines, if standard XML Typebuildings, UseCondisionts and Material
        Templates should be loaded (default: True)
    name : str, optional
        name of the TEASER Project (default: None)
    merge_windows : bool, optional
        Use calculation to merge window areas into walls within TEASER
        (default: True)

    Returns
    -------
    project : TEASER Project
        TEASER project
    """

    project = Project(load_data=load_data)

    if name is not None:
        project.name = name

    if merge_windows is True:
        project.merge_windows_calc = True

    return project


def create_teaser_typebld(project, BuildingExtended, name="example",
                          generate_Output=False, method_res='iwu',
                          usage_res='single_family_dwelling',
                          method_nonres='bmvbs', usage_nonres='office'):
    """
    Calls an extended building from pycity_calc and creates a TypeBuilding
    Residential from TEASER.
    Furthermore it can save the created TypeBuilding Residential as
    a .Mo-File to Output Folder.

    Parameters
    ----------
    project : TeaserProject Object
        the parent Project for the TypeBuilding to be created
    BuildingExtended : BuildingExtended Object
        the extended Building from pycity_calc form which the TypeBuilding is
        created
    name : str, optional
        name of the typebuilding (default: 'example')
    generate_Output : boolean, optional
        placeholder for Output generation, .Mo - File (default: False)
        True = create Output (save TEASER output structure)
        False = don't create Output
    method_res : str, optional
        Used residential archetype method, currenlty only 'iwu' or 'urbanrenet'
        are supported, 'tabula_de' to follow soon (default: 'iwu)
    usage_res : str, optional
        Main usage of the obtainend residential building, currently only
        'single_family_dwelling' is supported for iwu and 'est1a', 'est1b',
        'est2', 'est3', 'est4a', 'est4b', 'est5' 'est6', 'est7', 'est8a',
        'est8b' for urbanrenet (default: 'single_family_dwelling')
    method_nonres : str, optional
        Used archetype method, currenlty only 'bmvbs' is supported
        (default: 'bmvbs')
    usage_nonres : str, optional
        Main usage of the obtained building, currently only 'office',
        'institute', 'institute4', institute8' are supported
        (default: 'office')

    Returns
    -------
    (prj, type_bldg) : tuple
        prj: Teaser Project
            the created Project
        type_bldg: Teaser Type Building
            the created Typebuilding
    """

    #  Assert statements (general)
    assert BuildingExtended.build_year > 0
    assert BuildingExtended.build_type in [0, 1], 'Unknown building type.'
    assert BuildingExtended.nb_of_floors is not None and \
           BuildingExtended.nb_of_floors > 0
    assert BuildingExtended.height_of_floors is not None and \
           BuildingExtended.height_of_floors > 0
    assert BuildingExtended.net_floor_area is not None and \
           BuildingExtended.net_floor_area > 0
    if BuildingExtended.construction_type is not None:
        assert BuildingExtended.construction_type == "heavy" or \
               BuildingExtended.construction_type == "light"

    #  Assert statements (residential)
    if BuildingExtended.build_type == 0:
        if BuildingExtended.residential_layout is not None:
            assert 0 <= BuildingExtended.residential_layout <= 1
        if BuildingExtended.neighbour_buildings is not None:
            assert 0 <= BuildingExtended.neighbour_buildings <= 2
        if BuildingExtended.attic is not None:
            assert 0 <= BuildingExtended.attic <= 3
        if BuildingExtended.cellar is not None:
            assert 0 <= BuildingExtended.cellar <= 3
        if BuildingExtended.dormer is not None:
            assert BuildingExtended.dormer == 0 or BuildingExtended.dormer == 1

    #  Assert statements (Office)
    if BuildingExtended.build_type == 1:
        if BuildingExtended.office_layout is not None:
            assert 0 <= BuildingExtended.office_layout <= 3
        if BuildingExtended.window_layout is not None:
            assert 0 <= BuildingExtended.window_layout <= 3

    #  General parameters
    year_constr = BuildingExtended.build_year
    year_mod = BuildingExtended.mod_year
    number_of_floors = BuildingExtended.nb_of_floors
    height_of_floors = BuildingExtended.height_of_floors
    net_leased_area = BuildingExtended.net_floor_area
    construction_type = BuildingExtended.construction_type
    with_ahu = BuildingExtended.with_ahu

    if BuildingExtended.build_type == 0:
        residential_layout = BuildingExtended.residential_layout
        neighbour_buildings = BuildingExtended.neighbour_buildings
        attic = BuildingExtended.attic
        cellar = BuildingExtended.cellar
        dormer = BuildingExtended.dormer

    if BuildingExtended.build_type == 1:
        off_lay = BuildingExtended.office_layout
        win_lay = BuildingExtended.window_layout

    # create typeBuilding
    if BuildingExtended.build_type == 0:
        # creation of typeBuilding Residential

        nb_apart = BuildingExtended.get_number_of_apartments()

        type_bldg = \
            project.add_residential(
                method=method_res,
                usage=usage_res,
                name=name,
                year_of_construction=year_constr,
                number_of_floors=number_of_floors,
                height_of_floors=height_of_floors,
                net_leased_area=net_leased_area,
                with_ahu=with_ahu,
                residential_layout=residential_layout,
                neighbour_buildings=neighbour_buildings,
                attic=attic,
                cellar=cellar,
                dormer=dormer,
                construction_type=construction_type,
                number_of_apartments=nb_apart)

    if BuildingExtended.build_type == 1:
        #  Create office typeBuilding

        type_bldg = project.add_non_residential(
            method=method_nonres,
            usage=usage_nonres,
            name=name,
            year_of_construction=year_constr,
            number_of_floors=number_of_floors,
            height_of_floors=height_of_floors,
            net_leased_area=net_leased_area,
            with_ahu=with_ahu,
            office_layout=off_lay,
            window_layout=win_lay,
            construction_type=construction_type)

    # Do retrofiting (if year of modernization is defined)
    if year_mod is not None:
        assert year_mod > 0
        assert year_mod > year_constr
        print('Year of construction: ', year_constr)
        print('Going to retrofit building with modernization year:')
        print(year_mod)
        print()
        type_bldg.retrofit_building(year_of_retrofit=year_mod)

    if generate_Output:
        #  Generate and save output for Modelica (Records)
        path = os.path.dirname(os.path.abspath(__file__))
        path_root = path[:path.rfind("pycity_calc")]
        save_path = os.path.join(path_root, 'pycity_calc', 'toolbox',
                                 'teaser_usage', 'Output')

        try:
            # project.export_record("AixLib", save_path)
            project.export_aixlib(building_model="MultizoneEquipped",
                                  zone_model="ThermalZoneEquipped",
                                  corG=True,
                                  internal_id=None,
                                  path=save_path)
            project.save_project(project.name, save_path)
        except:
            warnings.warn('Could not save project!')

    return (project, type_bldg)


def create_teaser_typecity(project, city, generate_Output=False,
                           addToCity=True, use_exist_tbuild=True):
    """
    Creates TypeBuildings as Teaser Objects from ExtendedBuildings on the
    nodes of the city object.
    Further the TypeBuildings are added to the city as an Object at the
    referring node.
    It returns the extended city.

    Parameters
    ----------
    project : Teaser Project Object
        Teaser Project Object
    citypyCity : Object
        PyCity City Object form which the TypeBuildings will be generated
    generate_Output : boolean, optional
        placeholder for Output generation, .Mo - File (default: False)
        True = create Output
        False = don't create Output
    addToCity : boolean, optional
        determines if the created typebuildings are added to the city object
        (default: True)
        True = add to city
        False = don't add to city
    use_exist_tbuild : bool, optional
        Defines, if existing typebuildings should be used (default: True).
        If set to True, uses existing typebuildings. If set to False,
        overwrites existing typebuildings.

    Returns
    -------
    city : Pycity City Object
        return the edited city object which now owns the created typeBuildings
         as attributes at
        city.node[i]['type_building']
    """

    #  Use buildings only
    list_build = []
    for n in city.nodes():
        if 'node_type' in city.node[n]:
            #  If node_type is building
            if city.node[n]['node_type'] == 'building':
                if 'entity' in city.node[n]:
                    #  If entity is of type building (not PV or wind farm)
                    if city.node[n]['entity']._kind == 'building':
                        if city.node[n]['entity'].build_type in [0, 1]:
                            list_build.append(n)

    for n in list_build:

        #  create Typebuildings
        type_building = \
            create_teaser_typebld(project=project,
                                  BuildingExtended=city.node[n]['entity'],
                                  name=str(n),
                                  generate_Output=generate_Output)[1]

        if addToCity:

            if use_exist_tbuild is False:
                city.node[n]['type_building'] = type_building
            else:
                if 'type_building' not in city.node[n]:
                    city.node[n]['type_building'] = type_building
                else:
                    #  Add found type_building to TEASER project
                    project.buildings.append(city.node[n]['type_building'])

    return city


def extract_build_data_dict(type_build, alphaowo=25, aowo=0.9, epso=0.1,
                            orientationswallshorizontal=[90, 90, 90, 90, 0],
                            temperatureground=283.15, imax=100):
    """
    Extract building data dictionary from TEASER type building for VDI 6007
    calcultion.

    Parameters
    ----------
    type_build : object
        Type building object instance of TEASER
    alphaowo
    aowo
    epso
    orientationswallshorizontal
    temperatureground
    imax

    Returns
    -------
    dict_data : dict
        Dictionary holding building data
    """

    #  Assumes one single zone for complete building (also multi-family)
    thermal_zone = type_build.thermal_zones[0]

    # Load constant house parameters
    if len(thermal_zone.inner_walls) != 0:
        withInnerwalls = True
    else:
        withInnerwalls = False

    list_window_areas = []
    list_sunblind = []
    for window in thermal_zone.windows:
        list_window_areas.append(window.area)
        list_sunblind.append(0.0)

        # Convert into house data dictionary
        #  #-------------------------------------------------------
        dict_data = {"R1i": thermal_zone.model_attr.r1_iw,
                     "C1i": thermal_zone.model_attr.c1_iw,
                     "Ai": thermal_zone.model_attr.area_iw,
                     "RRest": thermal_zone.model_attr.r_rest_ow,
                     "R1o": thermal_zone.model_attr.r1_ow,
                     "C1o": thermal_zone.model_attr.c1_ow,
                     "Ao": [thermal_zone.model_attr.area_ow],
                     "Aw": list_window_areas,
                     "At": list_window_areas,
                     "Vair": thermal_zone.volume,
                     "rhoair": thermal_zone.density_air,
                     "cair": thermal_zone.heat_capac_air,
                     "splitfac": thermal_zone.windows[0].a_conv,
                     "g": thermal_zone.model_attr.weighted_g_value,
                     "alphaiwi": thermal_zone.model_attr.alpha_comb_inner_iw,
                     "alphaowi": thermal_zone.model_attr.alpha_comb_inner_ow,
                     "alphaWall": thermal_zone.model_attr.alpha_comb_outer_ow * thermal_zone.model_attr.area_ow,
                     "alphaowo": alphaowo,
                     # TODO: Substitute with TEASER call (misc or outer walls)
                     "withInnerwalls": withInnerwalls,
                     "aowo": aowo,
                     "epso": epso,
                     "orientationswallshorizontal": [90, 90, 90, 90, 0],
                     "temperatureground": temperatureground,
                     "weightfactorswall": thermal_zone.model_attr.weightfactor_ow,
                     "weightfactorswindow": thermal_zone.model_attr.weightfactor_win,
                     "weightfactorground": thermal_zone.model_attr.weightfactor_ground,
                     "gsunblind": list_sunblind,
                     "Imax": imax,
                     "aExt": thermal_zone.model_attr.solar_absorp_ow,
                     # coefficient of absorption of exterior walls (outdoor)
                     "eExt": thermal_zone.model_attr.ir_emissivity_outer_ow,
                     # coefficient of emission of exterior walls (outdoor)
                     "wfWall": thermal_zone.model_attr.weightfactor_ow,
                     # weight factors of the walls
                     "wfWin": thermal_zone.model_attr.weightfactor_win,
                     # weight factors of the windows
                     "wfGro": thermal_zone.model_attr.weightfactor_ground,
                     # weight factor of the ground (0 if not considered)
                     "T_Gro": temperatureground,
                     "alpha_wall_out": thermal_zone.model_attr.alpha_conv_outer_ow,
                     "alpha_rad_wall": thermal_zone.model_attr.alpha_rad_outer_ow,
                     "withLongwave": False}

    return dict_data


def calc_th_load__build_vdi6007(type_build, temp_out, rad,
                                occ_profile, el_load, array_vent_rate=None,
                                vent_factor=0.5,
                                t_set_heat=20, t_set_cool=70, t_night=16,
                                timestep=3600, imax=100,
                                alpha_rad=None, heat_lim_val=10000000,
                                cool_lim_val=10000000):
    """
    Calculate thermal space heating load of building with TEASER, according
    to VDI 6007 standard.

    Currently only valid for single zone buildings!

    Parameters
    ----------
    type_build : object
        Type building object instance of TEASER
    temp_out : array-like
        Outdoor temperature in degree Celsius
    rad : array-like
        2d-array with solar radiation input on each external area in W/m2
    occ_profile : array-like
        Occupancy profile (number of persons within building at spec. timestep)
    el_load : array-like
        Electrical power curve in W
    array_vent_rate : array-like, optional
        Ventilation rate in 1/h (at outdoor temperature) (default: None).
        If set to None, used default value
        ((thermal_zone.volume * vent_factor / 3600)) --> 0.5 1/h
    vent_factor : float, optional
        Ventilation rate factor in 1/h (default: 0.5). Only used, if
        array_vent_rate is None (otherwise, array_vent_rate array is used)
    t_set_heat : float, optional
        Heating set temperature in degree Celsius. If temperature drops below
        t_set_heat, model is going to be heated up. (default: 20)
        (Related to constraints for res. buildings in DIN V 18599)
    t_set_cool : float, optional
        Cooling set temperature in degree Celsius. If temperature rises above
        t_set_cool, model is going to be cooled down. (default: 70)
    t_night : float, optional
        Night set back temperature in degree Celsius (default: 16)
        (Related to constraints for res. buildings in DIN V 18599)
    timestep : float, optional
        Timestep of calculation in seconds (default: 3600)
    imax : float, optional
        Maximal irradiation (default: 100)
    alpha_rad : array-like, optional
        Radiative heat transfer coef. between inner and outer walls in W/m2K
        (default: None). If set to None, uses default value
        (np.zeros(timesteps) + 5).
    heat_lim_val : float, optional
        Upper limit for heater power (default: 10.000.000 W)
    cool_lim_val : float, optional
        Upper limit for cooler power (default: 10.000.000 W). Here, positive
        value is used. Within VDI 6007 core in TEASER, values is negated.

    Returns
    -------
    res_tuple : tuple
        Result tuple with 4 entries
        (temp_in, q_heat_cool, q_in_wall, q_out_wall)
        temp_in : array-like
            Indoor air temperature in degree Celsius
        q_heat_cool : array-like
            Heating or cooling power in W (+ heating / - cooling)
        q_in_wall : array-like
            Heat flow through inner wall in W
        q_out_wall : array-like
            Heat flow through outer wall in W
    """

    if timestep != 3600:
        msg = 'Currently, VDI 6007 Python simulation core only supports ' \
              'timestep of 3600 seconds.'
        raise AssertionError(msg)

    if max(temp_out) >= 70:
        warnings.warn('Temperature inputs seems to be too high. '
                      'Please check your input. It has to be in degree Celsius'
                      ', not in Kelvin!')
    if t_night >= 30:
        warnings.warn('t_night inputs seems to be too high. '
                      'Please check your input. It has to be in degree Celsius'
                      ', not in Kelvin!')
    if t_set_heat >= 30:
        warnings.warn('t_set_heat inputs seems to be too high. '
                      'Please check your input. It has to be in degree Celsius'
                      ', not in Kelvin!')

    timesteps = 365 * 24 * 60 * 60 / timestep

    if len(occ_profile) != timesteps:
        warnings.warn('Occupancy profile has different timestep. '
                      'Going to be converted.')

        org_res = 365 * 24 * 3600 / len(occ_profile)

        occ_profile = chres.changeResolution(occ_profile,
                                             oldResolution=org_res,
                                             newResolution=timestep)

    if len(el_load) != timesteps:
        warnings.warn('El. load profile has different timestep. '
                      'Going to be converted.')

        org_res = 365 * 24 * 3600 / len(el_load)

        el_load = chres.changeResolution(el_load,
                                         oldResolution=org_res,
                                         newResolution=timestep)

    # Extract house data
    houseData = extract_build_data_dict(type_build=type_build)

    #  Convert outdoor temperature from degree Celsius to Kelvin
    temp_out_copy = copy.copy(temp_out)
    temp_out_copy += 273.15

    #  Calculate equivalent air temperature
    #  ####################################################################
    # equal_air_temp = temp_out_copy + 0.5

    t_black_sky = np.zeros(int(timesteps)) + 273.15

    #  Activate sunblinds
    sunblind_in = np.zeros_like(rad)
    sunblind_in[rad > imax] = 0.85

    equal_air_temp = equ_air.equal_air_temp(HSol=rad,
                                            TBlaSky=t_black_sky,
                                            TDryBul=temp_out_copy,
                                            sunblind=sunblind_in,
                                            params=houseData)

    #  Calculate inner loads
    #  ####################################################################

    #  Calculate human sensible heat with occupancy profile
    q_heat_person = occ_profile * 70
    #  70 W per person (DIN V 18599 Blatt 10)

    #  Sum up with el. load thermal power input
    q_ig = q_heat_person + el_load

    # q_ig = np.zeros(int(timesteps)) + 200

    if array_vent_rate is None:
        array_vent_rate_abs = np.zeros(int(timesteps)) + \
                              (type_build.thermal_zones[
                                   0].volume * vent_factor / 3600)
    else:
        #  Convert 1/h (related to total air volume) to m3/s
        array_vent_rate_abs = \
            type_build.thermal_zones[0].volume / 3600 * array_vent_rate

    if alpha_rad is None:
        # Radiative heat transfer coef. between inner and outer walls in W/m2K
        alphaRad = np.zeros(int(timesteps)) + 5

    # Fix parameters
    source_igRad = np.zeros(int(timesteps))
    krad = 1

    t_set_heat_day = \
        np.array([t_night, t_night, t_night, t_night, t_night, t_night,
                  t_set_heat, t_set_heat, t_set_heat,
                  t_set_heat, t_set_heat, t_set_heat, t_set_heat, t_set_heat,
                  t_set_heat, t_set_heat, t_set_heat, t_set_heat, t_set_heat,
                  t_set_heat, t_set_heat, t_set_heat, t_set_heat, t_night]) \
        + 273.15

    array_t_set_heat = np.tile(t_set_heat_day, 365)

    #  Dummy value for initial temperature for VDI 6007 core
    temp_init = t_set_heat + 0.1 + 273.15

    # Set cooling schedule (in Kelvin)
    array_t_set_cooling = np.zeros(int(timesteps)) + t_set_cool + 273.15

    if heat_lim_val is None:
        heat_lim_val = 10000000
    if cool_lim_val is None:
        cool_lim_val = 10000000

    heater_limit = np.zeros((int(timesteps), 3)) + heat_lim_val
    cooler_limit = np.zeros((int(timesteps), 3)) - cool_lim_val

    temp_in_k, q_heat_cool, q_in_wall, q_out_wall = \
        low_order_vdi.reducedOrderModelVDI(houseData=houseData,
                                           weatherTemperature=temp_out_copy,
                                           solarRad_in=rad,
                                           equalAirTemp=equal_air_temp,
                                           alphaRad=alphaRad,
                                           ventRate=array_vent_rate_abs,
                                           Q_ig=q_ig,
                                           source_igRad=source_igRad,
                                           krad=krad,
                                           heater_order=np.array([1, 2, 3]),
                                           cooler_order=np.array([1, 2, 3]),
                                           heater_limit=heater_limit,
                                           cooler_limit=cooler_limit,
                                           t_set_heating=array_t_set_heat,
                                           t_set_cooling=array_t_set_cooling,
                                           T_air_init=temp_init,
                                           T_iw_init=temp_init,
                                           T_ow_init=temp_init)

    #  Convert Kelvin to degree Celsius
    temp_in = temp_in_k - 273.15

    return (temp_in, q_heat_cool, q_in_wall, q_out_wall)


def calc_th_load_build_vdi6007_ex_build(exbuild, add_th_load=False,
                                        array_vent_rate=None,
                                        vent_factor=0.5,
                                        t_set_heat=20,
                                        t_set_cool=70,
                                        t_night=16,
                                        alpha_rad=None,
                                        project_name='project',
                                        build_name='build_name',
                                        heat_lim_val=10000000,
                                        cool_lim_val=10000000):
    """
    Calculates thermal space heating load of building object of PyCity_Calc
    according to VDI 6007 within TEASER.

    Currently only valid for single zone buildings!
    Moreover, geneates new TEASER project for every call!

    Parameters
    ----------
    exbuild : object
        BuildingExtended object instance of PyCity_Calc. Should hold all
        necessary parameters for TEASER type building generation as input.
        Moreover, should hold occupancy and el. load profile (to calculate
        internal gains within VDI 6007 core).
    add_th_load : bool, optional
        Defines, if thermal load curve should be added as thermal demand
        object to building instance (default: False).
    array_vent_rate : array-like, optional
        Ventilation rate in 1/h (at outdoor temperature) (default: None).
        If set to None, used default value
        ((thermal_zone.volume * vent_factor / 3600)) --> 0.5 1/h
    vent_factor : float, optional
        Ventilation rate factor in 1/h (default: 0.5). Only used, if
        array_vent_rate is None (otherwise, array_vent_rate array is used)
    t_set_heat : float, optional
        Heating set temperature in degree Celsius. If temperature drops below
        t_set_heat, model is going to be heated up. (default: 21)
    t_set_cool : float, optional
        Cooling set temperature in degree Celsius. If temperature rises above
        t_set_cool, model is going to be cooled down. (default: 70)
    t_night : float, optional
        Night set back temperature in degree Celsius (default: 16)
    alpha_rad : array-like, optional
        Radiative heat transfer coef. between inner and outer walls in W/m2K
        (default: None). If set to None, uses default value
        (np.zeros(timesteps) + 5).
    project_name : str, optional
        Name of TEASER project (default: 'project')
    build_name : str, optional
        Name of TEASER typebuilding (default: 'build_name')
    heat_lim_val : float, optional
        Upper limit for heater power (default: 10.000.000 W)
    cool_lim_val : float, optional
        Upper limit for cooler power (default: 10.000.000 W). Here, positive
        value is used. Within VDI 6007 core in TEASER, values is negated.

    Returns
    -------
    res_tuple : tuple
        Result tuple with 4 entries
        (temp_in, q_heat_cool, q_in_wall, q_out_wall)
        temp_in : array-like
            Indoor air temperature in degree Celsius
        q_heat_cool : array-like
            Heating or cooling power in W (+ heating / - cooling)
        q_in_wall : array-like
            Heat flow through inner wall in W
        q_out_wall : array-like
            Heat flow through outer wall in W
    """

    #  Check, if extended building object holds necessary attributes and
    #  objects
    assert exbuild.hasApartments is True, 'Building object has no apartment!'

    for apartment in exbuild.apartments:
        assert apartment.occupancy is not None, 'Apartment has no occupants!'

    # Pointer to timestep
    timestep_org = exbuild.environment.timer.timeDiscretization

    #  Number of timesteps per year
    nb_timesteps = 365 * 24 * 3600 / timestep_org

    #  #  Create TEASER weather
    #  #####################################################################

    #  TODO: Add function for calculation
    beta = [90.0, 0.0, 90.0, 0.0, 90.0, 90.0]
    gamma = [0.0, 0.0, -180.0, 0.0, -90.0, 90.0]

    #  Generate TEASER weather object
    teaser_weather = vdiweather.Weather(
        beta=beta, gamma=gamma,
        altitude=exbuild.environment.weather.altitude,
        location=exbuild.environment.location,
        timestep=timestep_org,
        do_sun_rad=False)
    # do_sun_rad=True)

    # Add weather data out of pycity weather object of TEASER
    teaser_weather.temp = exbuild.environment.weather.tAmbient
    teaser_weather.sun_dir = exbuild.environment.weather.qDirect
    teaser_weather.sun_diff = exbuild.environment.weather.qDiffuse
    teaser_weather.rad_sky = exbuild.environment.weather.rad_sky
    teaser_weather.rad_earth = exbuild.environment.weather.rad_earth

    #  Re-calculate sun radiation values
    teaser_weather.calc_sun_rad(timestep=timestep_org, nb_timesteps=nb_timesteps)

    if timestep_org != 3600:
        #  Currently, VDI 6007 core can only handle 3600 seconds timestep.
        msg = 'Timestep is not equal to 3600 seconds. Thus, input profiles' \
              ' are going to be changed to 3600 seconds timestep to perform' \
              ' VDI 6007 simulation. Going to be re-converted after thermal ' \
              'simulation.'
        warnings.warn(msg)
    #  Set timestep to 3600 seconds
    timestep = 3600

    #  Outdoor temperature pointer
    t_out = teaser_weather.temp[:]
    t_out = chres.changeResolution(t_out, oldResolution=timestep_org,
                                   newResolution=timestep)

    #  Get radiation values
    rad = np.transpose(teaser_weather.sun_rad)[:]

    if timestep_org != 3600:
        #  Convert all 6 radiation directions with new timestep
        new_rad = np.zeros((8760, len(rad[0])))
        for i in range(len(rad[0])):
            new_rd = chres.changeResolution(copy.copy(rad[:,i]),
                                            oldResolution=timestep_org,
                                            newResolution=timestep)
            new_rad[:,i] = new_rd
        use_rad = new_rad
    else:
        use_rad = rad

    #  #  Create TEASER project and type building
    #  #####################################################################

    #  Create TEASER project
    teas_proj = create_teaser_project(name=project_name)

    #  Create TEASER typebuilding
    (teas_proj, type_b) = \
        create_teaser_typebld(project=teas_proj,
                              BuildingExtended=exbuild,
                              name=build_name,
                              generate_Output=False)

    #  Extract occupancy profile
    occ_profile = exbuild.get_occupancy_profile()[:]

    if len(occ_profile) != nb_timesteps:
        #  Change resolution to timestep of environment
        org_res = 365 * 24 * 3600 / len(occ_profile)

        occ_profile = chres.changeResolution(occ_profile,
                                             oldResolution=org_res,
                                             newResolution=timestep)

    # Extract electrical load
    el_load = exbuild.get_electric_power_curve()[:]

    if len(el_load) != nb_timesteps:
        #  Change resolution to timestep of environment
        org_res = 365 * 24 * 3600 / len(el_load)

        el_load = chres.changeResolution(el_load,
                                         oldResolution=org_res,
                                         newResolution=timestep)

    #  Convert array_vent_rate
    array_vent_rate_res = array_vent_rate[:]
    if timestep != timestep_org:
        array_vent_rate_res = chres.changeResolution(array_vent_rate_res,
                                                 oldResolution=timestep_org,
                                                 newResolution=timestep)

    #  Perform VDI 6007 thermal simulation
    (temp_in, q_heat_cool, q_in_wall, q_out_wall) = \
        calc_th_load__build_vdi6007(type_build=type_b, temp_out=t_out,
                                    rad=use_rad,
                                    occ_profile=occ_profile,
                                    el_load=el_load,
                                    array_vent_rate=array_vent_rate_res,
                                    vent_factor=vent_factor,
                                    t_set_heat=t_set_heat,
                                    t_set_cool=t_set_cool,
                                    t_night=t_night,
                                    timestep=timestep,
                                    alpha_rad=alpha_rad,
                                    heat_lim_val=heat_lim_val,
                                    cool_lim_val=cool_lim_val)

    #  Reconvert from timestep to timestep_org
    temp_in = chres.changeResolution(temp_in, oldResolution=timestep,
                                     newResolution=timestep_org)
    q_heat_cool = chres.changeResolution(q_heat_cool,
                                         oldResolution=timestep,
                                         newResolution=timestep_org)
    q_in_wall = chres.changeResolution(q_in_wall,
                                       oldResolution=timestep,
                                       newResolution=timestep_org)
    q_out_wall = chres.changeResolution(q_out_wall,
                                        oldResolution=timestep,
                                        newResolution=timestep_org)
    #  Reset timestep to timestep_org
    #timestep = timestep_org

    if add_th_load:
        #  Add th. load curve to apartment(s)
        nb_apartments = len(exbuild.apartments)

        #  Extract heating and cooling curve
        q_heat = np.zeros(len(q_heat_cool))
        q_cool = np.zeros(len(q_heat_cool))
        for i in range(len(q_heat_cool)):
            if q_heat_cool[i] > 0:
                q_heat[i] = q_heat_cool[i]
            elif q_heat_cool[i] < 0:
                q_cool[i] = q_heat_cool[i]

        curr_th_load = q_heat / nb_apartments

        timestep = exbuild.environment.timer.timeDiscretization

        # Energy sum in kWh
        sh_dem_vdi = sum(curr_th_load) / (1000 * timestep / 3600)

        if sh_dem_vdi < 0.1:
            msg = 'Building thermal space heating demand of' \
                  ' ' + str(sh_dem_vdi) + ' is too low!'
            warnings.warn(msg)

        for apartment in exbuild.apartments:
            #  Generate space heating object instance
            space_heating = \
                spheat.SpaceHeating(environment=exbuild.environment, method=0,
                                    loadcurve=curr_th_load)

            #  Add space heating to current apartment
            apartment.addEntity(space_heating)

    return (temp_in, q_heat_cool, q_in_wall, q_out_wall)


def calc_and_add_vdi_6007_loads_to_city(city,
                                        air_vent_mode,
                                        vent_factor=0.5,
                                        t_set_heat=20,
                                        t_set_cool=70,
                                        t_night=16,
                                        alpha_rad=None,
                                        project_name='project',
                                        heat_lim_val=10000000,
                                        cool_lim_val=10000000,
                                        use_exist_tbuild=False,
                                        requ_profiles=True):
    """
    Calculates and adds vdi 6007 space heating loads for every building
    within city object. Uses attributes of extended building to generate
    new TEASER typebuildings.
    Functions does NOT search for existing type buildings on nodes!
    If they exist, and use_exist_tbuild is False,
    they are going to be overwritten!

    Buildings should hold occupancy and electrical load profiles!

    Parameters
    ----------
    city : object
        City object of PyCity_Calc
    air_vent_mode : int
        Defines method to generation air exchange rate for VDI 6007 simulation
        Options:
        0 : Use constant value (vent_factor in 1/h)
        1 : Use deterministic, temperature-dependent profile
        2 : Use stochastic, user-dependent profile
    vent_factor : float, optional
        Ventilation rate factor in 1/h (default: 0.5). Only used, if
        air_vent_mode is 0
    t_set_heat : float, optional
        Heating set temperature in degree Celsius. If temperature drops below
        t_set_heat, model is going to be heated up. (default: 20)
        (Related to constraints for res. buildings in DIN V 18599)
    t_set_cool : float, optional
        Cooling set temperature in degree Celsius. If temperature rises above
        t_set_cool, model is going to be cooled down. (default: 70)
    t_night : float, optional
        Night set back temperature in degree Celsius (default: 16)
        (Related to constraints for res. buildings in DIN V 18599)
    alpha_rad : array-like, optional
        Radiative heat transfer coef. between inner and outer walls in W/m2K
        (default: None). If set to None, uses default value
        (np.zeros(timesteps) + 5).
    project_name : str, optional
        Name of TEASER project (default: 'project')
    heat_lim_val : float, optional
        Upper limit for heater power (default: 10.000.000 W)
    cool_lim_val : float, optional
        Upper limit for cooler power (default: 10.000.000 W). Here, positive
        value is used. Within VDI 6007 core in TEASER, values is negated.
    use_exist_tbuild : bool, optional
        Defines, if existing typebuildings should be used (default: False).
        If set to True, uses existing typebuildings. If set to False,
        overwrites existing typebuildings.
    requ_profiles : bool, optional
        Defines, if function demands occupancy and electrical load profiles
        for VDI usage (default: True).
        If set to True: Requires profile on every building
        If set to False: Set user profile and el. load profiles to zero
    """

    #  Pointer to timestep
    timestep_org = city.environment.timer.timeDiscretization

    #  Number of timesteps per year
    nb_timesteps = 365 * 24 * 3600 / timestep_org

    #  Geneate new teaser project
    teaser_project = create_teaser_project(name=project_name)

    #  TODO: TEASER project
    #  If type_building exists, append list .buildings
    #  If not, generate type_building
    #  Prob. calc_all_buildings

    #  Create typebuilding and add it to every building node
    create_teaser_typecity(teaser_project, city=city, generate_Output=False,
                           addToCity=True, use_exist_tbuild=use_exist_tbuild)

    #  Search for buildings (res. and office), only
    list_build = []
    for n in city.nodes():
        if 'node_type' in city.node[n]:
            #  If node_type is building
            if city.node[n]['node_type'] == 'building':
                if 'entity' in city.node[n]:
                    #  If entity is of type building (not PV or wind farm)
                    if city.node[n]['entity']._kind == 'building':
                        if city.node[n]['entity'].build_type in [0, 1]:
                            list_build.append(n)

    # #  Create TEASER weather
    #  #####################################################################

    #  TODO: Add function for calculation
    beta = [90.0, 0.0, 90.0, 0.0, 90.0, 90.0]
    gamma = [0.0, 0.0, -180.0, 0.0, -90.0, 90.0]

    #  Generate TEASER weather object
    teaser_weather = vdiweather.Weather(
        beta=beta, gamma=gamma,
        altitude=city.environment.weather.altitude,
        location=city.environment.location,
        timestep=city.environment.timer.timeDiscretization,
        do_sun_rad=False)
    # do_sun_rad=True)

    # Add weather data out of pycity weather object of TEASER
    teaser_weather.temp = city.environment.weather.tAmbient
    teaser_weather.sun_dir = city.environment.weather.qDirect
    teaser_weather.sun_diff = city.environment.weather.qDiffuse
    teaser_weather.rad_sky = city.environment.weather.rad_sky
    teaser_weather.rad_earth = city.environment.weather.rad_earth

    #  Re-calculate sun radiation values
    teaser_weather.calc_sun_rad(timestep=timestep_org,
                                nb_timesteps=nb_timesteps)

    if timestep_org != 3600:
        #  Currently, VDI 6007 core can only handle 3600 seconds timestep.
        msg = 'Timestep is not equal to 3600 seconds. Thus, input profiles' \
              ' are going to be changed to 3600 seconds timestep to perform' \
              ' VDI 6007 simulation. Going to be re-converted after thermal ' \
              'simulation.'
        warnings.warn(msg)
    #  Set timestep to 3600 seconds
    timestep = 3600

    #  Outdoor temperature pointer
    t_out = teaser_weather.temp[:]
    t_out = chres.changeResolution(t_out, oldResolution=(365 * 24 * 3600 / len(t_out)),
                                   newResolution=timestep)

    #  Get radiation values
    rad = np.transpose(teaser_weather.sun_rad)[:]

    if timestep_org != 3600:
        #  Convert all 6 radiation directions with new timestep
        new_rad = np.zeros((8760, len(rad[0])))
        for i in range(len(rad[0])):
            new_rd = chres.changeResolution(copy.copy(rad[:, i]),
                                            oldResolution=(365 * 24 * 3600 / len(rad)),
                                            newResolution=timestep)
            new_rad[:, i] = new_rd
        use_rad = new_rad
    else:
        use_rad = rad

    #  Perform VDI 6007 simulation for every building
    #  #####################################################################
    for n in list_build:

        print('Process (VDI 6007 calculation) building node with id: ', n)

        #  Check that building type is residential or office
        assert city.node[n]['entity'].build_type in [0, 1]

        curr_build = city.node[n]['entity']
        curr_type_b = city.node[n]['type_building']

        # #  Generate ventilation rate (window opening etc.)
        #  ##################################################################

        #  Get infiltration rate
        if curr_build.mod_year is None:
            year = curr_build.build_year
        else:
            year = curr_build.mod_year
        inf_rate = usair.get_inf_rate(year)

        if air_vent_mode == 0 or requ_profiles is False:  # Use constant value
            array_vent = None  # If array_vent is None, use constant
            print('Use constant air exchange rate.')
            # default value

        elif air_vent_mode == 1:  # Use deterministic, temp-dependent profile

            print('Generate deterministic, dynamic air exchange rate.')

            #  Generate dummy array
            array_vent = np.zeros(len(t_out))

            #  Loop over all apartments
            for ap in curr_build.apartments:

                if requ_profiles:
                    #  Extract occupancy profile
                    occ_profile = ap.get_occupancy_profile()[:]
                else:
                    #  Create dummy occupancy profile with single
                    occ_profile = np.ones(len(t_out))

                if len(occ_profile) != (365 * 24 * 3600 / timestep):
                    #  Change resolution to timestep of environment
                    org_res = 365 * 24 * 3600 / len(occ_profile)

                    occ_profile = chres.changeResolution(occ_profile,
                                                         oldResolution=org_res,
                                                         newResolution=timestep)

                #  Sum up air exchange rates of all apartments
                array_vent += \
                    usair.gen_det_air_ex_rate_temp_dependend(occ_profile=
                                                             occ_profile,
                                                             temp_profile=
                                                             t_out,
                                                             inf_rate=0)

            #  Finally, add infiltration rate of building
            array_vent += inf_rate

            #  Divide by apartment number (because of normalizing
			#  air exchange to total building volume)
            array_vent /= len(curr_build.apartments)

        elif air_vent_mode == 2:

            print('Generate stochastic air exchange rate.')

            #  Generate dummy array
            array_vent = np.zeros(len(t_out))

            #  Loop over all apartments
            for ap in curr_build.apartments:

                if requ_profiles:
                    #  Extract occupancy profile
                    occ_profile = ap.get_occupancy_profile()[:]
                else:
                    #  Create dummy occupancy profile with single
                    occ_profile = np.ones(len(t_out))

                if len(occ_profile) != (365 * 24 * 3600 / timestep):
                    #  Change resolution to timestep of environment
                    org_res = 365 * 24 * 3600 / len(occ_profile)

                    occ_profile = chres.changeResolution(occ_profile,
                                                         oldResolution=org_res,
                                                         newResolution=timestep)

                #  Sum up air exchange rate profiles
                #  Get ventilation rate (in 1/h, related to building air volume)
                array_vent += \
                    usair.gen_user_air_ex_rate(
                        occ_profile=occ_profile,
                        temp_profile=t_out,
                        b_type='res',
                        inf_rate=0)

            #  Finally, add infiltration rate of building
            array_vent += inf_rate

            #  Divide by apartment number (because of normalizing
			#  air exchange to total building volume)
            array_vent /= len(curr_build.apartments)

        if air_vent_mode == 1 or air_vent_mode == 2:
            print('Mean air exchange rate of building for one year in 1/h:')
            print(np.mean(array_vent))
            print('Minimal air exchange rate in 1/h: ', min(array_vent))
            print('Maximal air exchange rate in 1/h: ', max(array_vent))
            print()

        # #  Get building occupancy and el. load profile
        #  ##################################################################

        #  Get overall occupancy profile of building
        occupancy_profile = curr_build.get_occupancy_profile()[:]
        org_res = 365 * 24 * 3600 / len(occupancy_profile)

        occupancy_profile = chres.changeResolution(occupancy_profile,
                                                   oldResolution=org_res,
                                                   newResolution=timestep)

        if requ_profiles:
            # Extract electrical load
            el_load = curr_build.get_electric_power_curve()[:]
        else:
            #  Generate dummy el. load profile with zeros
            el_load = np.zeros(len(t_out))

        if len(el_load) != (365 * 24 * 3600 / timestep):
            #  Change resolution to timestep of environment
            res_el = 365 * 24 * 3600 / len(el_load)

            el_load = chres.changeResolution(el_load,
                                             oldResolution=res_el,
                                             newResolution=timestep)

        # #  Perform VDI 6007 simulation
        #  ##################################################################

        # Do simulation
        (temp_in, q_heat_cool, q_in_wall, q_out_wall) = \
            calc_th_load__build_vdi6007(type_build=curr_type_b,
                                        temp_out=t_out, rad=use_rad,
                                        occ_profile=occupancy_profile,
                                        el_load=el_load,
                                        array_vent_rate=array_vent,
                                        vent_factor=vent_factor,
                                        t_set_heat=t_set_heat,
                                        t_set_cool=t_set_cool,
                                        t_night=t_night,
                                        timestep=timestep,
                                        alpha_rad=alpha_rad,
                                        heat_lim_val=heat_lim_val,
                                        cool_lim_val=cool_lim_val)

        #  Reconvert results to original timestep
        #  ##################################################################
        temp_in = chres.changeResolution(temp_in, oldResolution=timestep,
                                         newResolution=timestep_org)
        q_heat_cool = chres.changeResolution(q_heat_cool,
                                             oldResolution=timestep,
                                             newResolution=timestep_org)
        q_in_wall = chres.changeResolution(q_in_wall,
                                           oldResolution=timestep,
                                           newResolution=timestep_org)
        q_out_wall = chres.changeResolution(q_out_wall,
                                            oldResolution=timestep,
                                            newResolution=timestep_org)

        # #  Add space heating power curves to apartments
        #  ##################################################################

        #  Add load to building object
        nb_apartments = len(curr_build.apartments)

        #  Extract heating and cooling curve
        q_heat = np.zeros(len(q_heat_cool))
        q_cool = np.zeros(len(q_heat_cool))
        for i in range(len(q_heat_cool)):
            if q_heat_cool[i] > 0:
                q_heat[i] = q_heat_cool[i]
            elif q_heat_cool[i] < 0:
                q_cool[i] = q_heat_cool[i]

        curr_th_load = q_heat / nb_apartments

        print('Max. space heating thermal power in Watt'
              ', according to VDI 6007 simulation: ', max(q_heat))

        for apartment in curr_build.apartments:
            #  Generate space heating object instance
            space_heating = \
                spheat.SpaceHeating(environment=curr_build.environment,
                                    method=0,
                                    loadcurve=curr_th_load)

            #  Add space heating object to current apartment
            apartment.addEntity(space_heating)

        print('Finished VDI calculation for building node with id: ', n)


def add_kfw_retrofit_to_city(city, material=None, thickness=None):
    """
    Add additional insulation to all buildings in city

    Parameters
    ----------
    city : object
        City object of pycity_calc
    material : string, optional
            Type of material, that is used for insulation (default: None)
            If set to None, EPS035 is used
    thickness : float, optional
        Thickness of insulation layer (default: None) in m
    """

    for n in city.nodes():

        if 'node_type' in city.node[n]:
            if city.node[n]['node_type'] == 'building':

                if 'entity' in city.node[n]:

                    if city.node[n]['entity']._kind == 'building':

                        #  Only residential or office (for TEASER typebuild)
                        if city.node[n]['entity'].build_type in [0, 1]:

                            curr_typeb = city.node[n]['type_building']

                            for zone in curr_typeb.thermal_zones:

                                for wall_count in zone.outer_walls:
                                    wall_count. \
                                        insulate_wall(material=material,
                                                      thickness=thickness)

                                for roof_count in zone.rooftops:
                                    roof_count. \
                                        insulate_wall(material=material,
                                                      thickness=thickness)

                                for ground_count in zone.ground_floors:
                                    ground_count. \
                                        insulate_wall(material=material,
                                                      thickness=thickness)

    curr_typeb.parent.calc_all_buildings()


if __name__ == '__main__':
    #  Example how to calculate thermal load according to VDI 6007 with
    #  TEASER type building

    #  Define simulation settings
    build_year = 1962  # Year of construction
    mod_year = 2014  # Year of retrofit

    el_demand = 3000  # Annual, el. demand in kWh

    t_set_heat = 20  # Heating set temperature in degree Celsius
    t_set_night = 16  # Night set back temperature in degree Celsius
    t_set_cool = 70  # Cooling set temperature in degree Celsius

    air_vent_mode = 1
    #  int; Define mode for air ventilation rate generation
    #  0 : Use constant value (vent_factor in 1/h)
    #  1 : Use deterministic, temperature-dependent profile
    #  2 : Use stochastic, user-dependent profile
    #  False: Use static ventilation rate value

    vent_factor = 0.5  # Constant. ventilation rate
    #  (only used, if use_dyn_vent_rate is False)

    #  #  Create PyCity_Calc environment
    #  #####################################################################

    #  Create extended environment of pycity_calc
    year = 2010
    timestep = 3600  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
    altitude = 55  # Altitude of Bottrop

    nb_timesteps = 365 * 24 * 3600 / timestep

    #  Generate timer object
    timer = time.TimerExtended(timestep=timestep, year=year)

    #  Generate weather object
    weather = Weather.Weather(timer, useTRY=True, location=location,
                              altitude=altitude)

    #  Generate market object
    market = mark.Market()

    #  Generate co2 emissions object
    co2em = co2.Emissions(year=year)

    #  Generate environment
    environment = env.EnvironmentExtended(timer, weather, prices=market,
                                          location=location, co2em=co2em)

    #  #  Create TEASER weather
    #  #####################################################################

    #  TODO: Add function for calculation
    beta = [90.0, 0.0, 90.0, 0.0, 90.0, 90.0]
    gamma = [0.0, 0.0, -180.0, 0.0, -90.0, 90.0]

    #  Generate TEASER weather object
    teaser_weather = \
        vdiweather.Weather(beta=beta, gamma=gamma,
                           altitude=environment.weather.altitude,
                           location=environment.location,
                           timestep=timestep,
                           do_sun_rad=False)
    # do_sun_rad=True)

    # Add weather data out of pycity weather object of TEASER
    teaser_weather.temp = environment.weather.tAmbient
    teaser_weather.sun_dir = environment.weather.qDirect
    teaser_weather.sun_diff = environment.weather.qDiffuse
    teaser_weather.rad_sky = environment.weather.rad_sky
    teaser_weather.rad_earth = environment.weather.rad_earth

    #  Re-calculate sun radiation values
    teaser_weather.calc_sun_rad(timestep=timestep, nb_timesteps=nb_timesteps)

    #  Outdoor temperature pointer
    t_out = teaser_weather.temp[:]

    #  Get radiation values
    rad = np.transpose(teaser_weather.sun_rad)

    #  #  Create occupancy profile
    #  #####################################################################

    num_occ = 3

    print('Calculate occupancy.\n')
    #  Generate occupancy profile
    occupancy_obj = occ.Occupancy(environment, number_occupants=num_occ)

    print('Finished occupancy calculation.\n')

    #  #  Generate ventilation rate (window opening etc.)
    #  #####################################################################

    #  Get infiltration rate
    if mod_year is None:
        year = build_year
    else:
        year = mod_year
    inf_rate = usair.get_inf_rate(year)

    if air_vent_mode == 0:  # Use constant value
        array_vent = None  # If array_vent is None, use default values

    elif air_vent_mode == 1:  # Use deterministic, temp-dependent profile
        array_vent = \
            usair.gen_det_air_ex_rate_temp_dependend(occ_profile=
                                                     occupancy_obj.occupancy,
                                                     temp_profile=
                                                     environment.weather.tAmbient,
                                                     inf_rate=inf_rate)


    elif air_vent_mode == 2:
        #  Get ventilation rate (in 1/h, related to building air volume)
        array_vent = \
            usair.gen_user_air_ex_rate(occ_profile=occupancy_obj.occupancy,
                                       temp_profile=environment.weather.tAmbient,
                                       b_type='res',
                                       inf_rate=inf_rate)

    # #  Create electrical load
    #  #####################################################################

    print('Calculate el. load.\n')

    #  # Generate stochastic, el. load profile
    # el_dem_stochastic = \
    #     eldem.ElectricalDemand(environment,
    #                            method=2,
    #                            annualDemand=el_demand,
    #                            do_normalization=True,
    #                            total_nb_occupants=num_occ,
    #                            randomizeAppliances=True,
    #                            lightConfiguration=10,
    #                            occupancy=occupancy_obj.occupancy[:])

    # #  Instead of stochastic profile, use SLP to be faster with calculation
    el_dem_stochastic = eldem.ElectricalDemand(environment,
                                               method=1,
                                               # Standard load profile
                                               profileType="H0",
                                               annualDemand=el_demand)
    #  #  Change resolution of el. load profile (necessary for SLP)
    old_res = 365 * 24 * 3600 / len(occupancy_obj.occupancy)
    new_res = 3600
    el_profile = \
        chres.changeResolution(el_dem_stochastic.loadcurve,
                               oldResolution=old_res,
                               newResolution=new_res)

    #  Pointer to el. load profile
    el_profile = el_dem_stochastic.loadcurve

    print('Finished el. load calculation.\n')

    # #  Change resolution of occupancy profile
    old_res = 365 * 24 * 3600 / len(occupancy_obj.occupancy)
    new_res = 3600
    occ_profile = \
        chres.changeResolution(occupancy_obj.occupancy,
                               oldResolution=old_res,
                               newResolution=new_res)

    #  #  Create apartment and building object
    #  #####################################################################

    #  Create apartment
    apartment = Apartment.Apartment(environment)

    #  Add demands to apartment
    apartment.addMultipleEntities([el_dem_stochastic, occupancy_obj])

    #  Create extended building object
    extended_building = build_ex.BuildingExtended(environment,
                                                  build_year=build_year,
                                                  mod_year=mod_year,
                                                  build_type=0,
                                                  roof_usabl_pv_area=30,
                                                  net_floor_area=200,
                                                  height_of_floors=2.8,
                                                  nb_of_floors=2,
                                                  neighbour_buildings=0,
                                                  residential_layout=0,
                                                  attic=1, cellar=1,
                                                  construction_type='heavy',
                                                  dormer=1)

    #  BuildingExtended holds further, optional input parameters,
    #  such as ground_area, nb_of_floors etc.

    #  Add apartment to extended building
    extended_building.addEntity(entity=apartment)

    #  #  Create TEASER project and type building
    #  #####################################################################

    #  Create TEASER project
    teas_proj = create_teaser_project(name='Demo_project')

    #  Create TEASER typebuilding
    (teas_proj, type_b) = \
        create_teaser_typebld(project=teas_proj,
                              BuildingExtended=extended_building,
                              name="example",
                              generate_Output=False)

    # #  Pointer to outdoor temperature
    # t_out = environment.weather.tAmbient
    #
    # #  Pointer to radiation
    # rad = environment.weather.qDirect + environment.weather.qDiffuse

    #  #  Perform simulation
    #  #####################################################################

    #  Perform VDI 6007 simulation
    (temp_in, q_heat_cool, q_in_wall, q_out_wall) = \
        calc_th_load__build_vdi6007(type_build=type_b, temp_out=t_out, rad=rad,
                                    occ_profile=occ_profile,
                                    vent_factor=vent_factor,
                                    el_load=el_profile,
                                    array_vent_rate=array_vent,
                                    t_set_heat=t_set_heat,
                                    t_set_cool=t_set_cool,
                                    timestep=timestep,
                                    alpha_rad=None,
                                    t_night=t_set_night)

    #  #  Results
    #  #####################################################################

    print('Indoor air temperature in degree Celsius:')
    print(temp_in)
    print()

    print('Heating(+) / cooling(-) load in Watt:')
    print(q_heat_cool)
    print()

    q_heat = np.zeros(len(q_heat_cool))
    q_cool = np.zeros(len(q_heat_cool))
    for i in range(len(q_heat_cool)):
        if q_heat_cool[i] > 0:
            q_heat[i] = q_heat_cool[i]
        elif q_heat_cool[i] < 0:
            q_cool[i] = q_heat_cool[i]

    print('Sum of heating energy in kWh:')
    print(sum(q_heat) / 1000)

    print('Sum of cooling energy in kWh:')
    print(-sum(q_cool) / 1000)

    import matplotlib.pyplot as plt

    fig = plt.figure()
    fig.add_subplot(411)
    plt.plot(environment.weather.tAmbient)
    plt.ylabel('Outdoor air\ntemperature in\ndegree Celsius')
    fig.add_subplot(412)
    plt.plot(rad)
    plt.ylabel('Sun radiation\non surface 0')
    fig.add_subplot(413)
    plt.plot(temp_in)
    plt.ylabel('Indoor air\ntemperature in\ndegree Celsius')
    fig.add_subplot(414)
    plt.plot(q_heat_cool / 1000)
    plt.ylabel('Heating/cooling\npower (+/-)\nin kW')
    plt.xlabel('Time in hours')
    plt.show()
    plt.close()


    # #  Calculate and save thermal load to extended building object instance
    # (temp_in, q_heat_cool, q_in_wall, q_out_wall) = \
    #     calc_th_load_build_vdi6007_ex_build(exbuild=extended_building,
    #                                         array_vent_rate=None,
    #                                         vent_factor=0.5,
    #                                         t_set_heat=21,
    #                                         t_set_cool=70,
    #                                         t_night=18,
    #                                         alpha_rad=None,
    #                                         project_name='project',
    #                                         build_name='build_name',
    #                                         add_th_load=True)
    #
    # print()
    # print(extended_building.get_annual_space_heat_demand())
