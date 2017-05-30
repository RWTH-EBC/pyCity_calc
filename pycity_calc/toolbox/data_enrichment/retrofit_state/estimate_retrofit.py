"""
Script to estimate state of retrofit within city object instance.

Requires city object with existing net space heating load curves on
every building. Script calls TEASER VDI 6007 simulation core to
calculate space heating energy demand for different retrofit states
until simulated values is close to input value.
"""

import os
import copy
import warnings
import pickle
import numpy as np

import pycity.classes.demand.Occupancy as occ

import pycity_calc.toolbox.teaser_usage.teaser_use as teas_use


def estimate_build_retrofit(building, sh_ann_demand,
                            overwrite_sh=False,
                            list_retro_years=
                            [1977, 1982, 1995, 2002, 2009, 2014],
                            print_output=False, overwrite_mod=True,
                            t_set_heat=20, t_night=16):
    """
    Estimate retrofit state of single building instance, based on annual
    net thermal energy demand value on space heating instance.
    Add new year of retrofit (and/or new build_year) to building object
    instance.

    Important: Existing space heating load objects are ignored. Reference
    is sh_ann_demand input value!

    Parameters
    ----------
    building : object
        Building extended object instance of pycity_calc
    sh_ann_demand : float
        Annual space heating net energy demand in kWh
    overwrite_sh : bool, optional
        Defines, if space heating demand and load curve should be overwritten
        with generated VDI 6007 load curve (default: False)
    list_retro_years : list (of ints), optional
        List holding retrofit years, used for analysis
         (default: [1977, 1982, 1995, 2002, 2009, 2014]).
        Currently TEASER only supports retrofit years 1977 and higher.
    print_output : bool, optional
        Defines, if output should be printed out (default: False)
    overwrite_mod : bool, optional
        Decide, if existing years of modernization should be overwritten
        (default: True).
        If True: Overwrittes existing mod_year attributes.
        If False: If mod_year is not None, it is NOT overwritten
    t_set_heat : float, optional
        Heating set temperature in degree Celsius. If temperature drops below
        t_set_heat, model is going to be heated up. (default: 20)
    t_night : float, optional
        Night setback temperature in degree Celsius (default: 16)
    """

    for ap in building.apartments:
        if ap.occupancy is None:
            raise AssertionError('Requires occupancy within apartment!')

    assert sh_ann_demand >= 0

    # Check if year of construction is set
    #  If not, set default build_year of 1920
    if building.build_year is None:
        warnings.warn('No build_year found. Going to use 1920.')
        building.build_year = 1920

    # Sort list, in case it is unsorted
    list_retro_years.sort()

    #  Dummy value for space heat closest to reference value
    closest_vdi_sh = None
    #  Dummy value for closest retrofit year
    closest_r_year = None

    if building.mod_year is not None and overwrite_mod is False:
        msg = 'Building already has mod_year. Going to keep this value.'
        warnings.warn(msg)
    else:
        #  Loop over possible modernization years
        for retro_year in list_retro_years:

            #  Skip retro_years, which are older than year of construction
            if retro_year > building.build_year:

                if print_output:
                    print('Current year of retrofit: ', retro_year)

                #  Set retrofit year
                building.mod_year = retro_year

                #  Perfom VDI 6007 simulation of space heating load
                (temp_in, q_heat_cool, q_in_wall, q_out_wall) = teas_use. \
                    calc_th_load_build_vdi6007_ex_build(exbuild=building,
                                                        add_th_load=False,
                                                        array_vent_rate=None,
                                                        vent_factor=0.5,
                                                        t_set_heat=t_set_heat,
                                                        t_set_cool=70,
                                                        t_night=t_night,
                                                        alpha_rad=None,
                                                        project_name='project',
                                                        build_name='build_name',
                                                        heat_lim_val=10000000,
                                                        cool_lim_val=10000000)

                #  Extract heating, only
                heat_array = np.zeros(len(q_heat_cool))
                for i in range(len(q_heat_cool)):
                    if q_heat_cool[i] > 0:
                        heat_array[i] = q_heat_cool[i]
                    else:
                        heat_array[i] = 0

                timestep = building.environment.timer.timeDiscretization

                # Energy sum in kWh
                sh_dem_vdi = sum(heat_array) / (1000 * timestep/3600)

                if sh_dem_vdi < 0.1:
                    msg = 'Building thermal space heating demand of' \
                          ' ' + str(sh_dem_vdi) + ' is too low!'
                    warnings.warn(msg)

                if print_output:
                    print('Simulated space heating demand in kWh: ', sh_dem_vdi)
                    print('Difference to reference value:')
                    print(abs(sh_dem_vdi - sh_ann_demand))
                    print()

                #  Check if energy value is close to reference value
                if closest_vdi_sh is None:
                    closest_vdi_sh = sh_dem_vdi
                    closest_r_year = retro_year
                else:
                    if abs(sh_ann_demand - sh_dem_vdi) < abs(sh_ann_demand -
                                                                     closest_vdi_sh):
                        closest_vdi_sh = sh_dem_vdi
                        closest_r_year = retro_year

        # Set new retrofit year
        building.mod_year = closest_r_year

        if print_output:
            print('Best fitting last year of retrofit: ', closest_r_year)

    if overwrite_sh:
        #  Simulate new space heating load curve with current mod_year
        #  Perfom VDI 6007 simulation of space heating load
        teas_use.calc_th_load_build_vdi6007_ex_build(exbuild=building,
                                                     add_th_load=True,
                                                     array_vent_rate=None,
                                                     vent_factor=0.5,
                                                     t_set_heat=t_set_heat,
                                                     t_set_cool=70,
                                                     t_night=t_night,
                                                     alpha_rad=None,
                                                     project_name='project',
                                                     build_name='build_name',
                                                     heat_lim_val=10000000,
                                                     cool_lim_val=10000000)


def estimate_city_retrofit(city, overwrite_sh=False, print_output=False,
                           overwrite_mod=True, t_set_heat=20,
                           skip_non_res=True):
    """
    Estimate last year of retrofit per building, based on annual thermal space
    heating demand per building. Requires city with buildings, apartments,
    and loads to perform VDI 6007 calculation per building.

    Parameters
    ----------
    city : object
        City object of pycity_calc
    overwrite_sh : bool, optional
        Defines, if space heating demand and load curve should be overwritten
        with generated VDI 6007 load curve (default: False)
    print_output : bool, optional
        Defines, if output should be printed out (default: False)
    overwrite_mod : bool, optional
        Decide, if existing years of modernization should be overwritten
        (default: True).
        If True: Overwrittes existing mod_year attributes.
        If False: If mod_year is not None, it is NOT overwritten
    t_set_heat : float, optional
        Heating set temperature in degree Celsius. If temperature drops below
        t_set_heat, model is going to be heated up. (default: 20)
    skip_non_res : float, optional
        Defines, if all non residential buildings should be skipped
        (default: True). If True, only processes residential buildings.
        If False, trys to process every other building type, which
        is usable within TEASER type building logic (e.g. office or institutes)

    Returns
    -------
    city_new : object
        Copy of input city object instance with adjusted building year and
        last year of retrofit.
    """

    #  Copy city object instance
    city_new = copy.deepcopy(city)

    #  Loop over buildings
    for n in city_new.nodes():
        #  If node holds attribute 'node_type'
        if 'node_type' in city_new.node[n]:
            #  If node_type is building
            if city_new.node[n]['node_type'] == 'building':
                #  If entity is kind building
                if city_new.node[n]['entity']._kind == 'building':
                    if (city_new.node[n]['entity'].build_type == 0 or
                        city_new.node[n]['entity'].build_type == 1):
                        if skip_non_res and \
                            city_new.node[n]['entity'].build_type != 0:
                            pass
                        else:
                            print('Processing building ', n)
                            print()

                            #  Check if apartments within building have
                            #  occupancy objects with profiles
                            if city_new.node[n]['entity'].hasApartments:
                                for app in city_new.node[n]['entity'].apartments:
                                    if app.occupancy is None or app.occupancy.occupancy is None:

                                        msg = 'Building ' + str(n) + ' has' \
                                              'no occupancy profile. Thus, ' \
                                              'it is going to be generated.'
                                        warnings.warn(msg)

                                        #  Generate occupancy profile
                                        occ_obj = occ.Occupancy(environment=city.environment,
                                            number_occupants=app.occupancy.number_occupants)

                                        #  Add occupancy to apartment
                                        app.addEntity(occ_obj)

                            sh_dem = city_new.node[n]['entity']. \
                                get_annual_space_heat_demand()

                            #  TODO: Add comparison based on net floor area
                            if sh_dem < 5000:
                                msg = 'Space heating demand of ' + str(sh_dem) + ' ' \
                                      'kWh seems to be very low (ID: ' + str(n) + ').'
                                warnings.warn(msg)

                            elif sh_dem > 50000:
                                msg = 'Space heating demand of ' + str(sh_dem) + ' ' \
                                      'kWh seems to be very high (ID: ' + str(n) + ').'
                                warnings.warn(msg)

                            #  Estimate and set new retrofit years on building
                            estimate_build_retrofit(building=city_new.node[n]['entity'],
                                                    sh_ann_demand=sh_dem,
                                                    overwrite_sh=overwrite_sh,
                                                    print_output=print_output,
                                                    overwrite_mod=overwrite_mod,
                                                    t_set_heat=t_set_heat)

                            print('Processing building ', n)
                            print()

    #  TODO: Add log-function to write retrofit years to file, if desired

    return city_new


if __name__ == '__main__':

    overwrite_space_heat = True
    print_out = True  # Print output (intermediate results)
    overwrite_mod = True
    t_set_heat = 20

    skip_non_res = True  # Skip office buildings

    #  Define input path
    #  ############################################################
    this_path = os.path.dirname(os.path.abspath(__file__))

    src_path = os.path.dirname(os.path.dirname(os.path.dirname(this_path)))

    filename = 'rheinbaben_nord_mod_jsc.p'
    # filename = 'city_Rheinbaben_sued_mod_jsc.p'
    # filename = 'innenstadt_mod_jsc_temp.p'

    # city_path = os.path.join(this_path, 'input', filename)
    city_path = os.path.join(src_path, 'cities', 'scripts',
                             'output_complex_city_gen', filename)

    save_file = 'rheinbaben_nord_mod_jsc_estimate_retrofit_overwrite.p'
    # save_file = 'city_Rheinbaben_sued_mod_jsc_estimate_retrofit.p'
    # save_file = 'innenstadt_mod_jsc_temp_estimate_retrofit.p'

    save_path = os.path.join(this_path, 'output', save_file)

    #  ############################################################

    print('Run estimation of retrofit for: ', filename)

    #  Load city pickle file
    city = pickle.load(open(city_path, mode='rb'))

    #  Generate new city with retrofit years
    city_retro = estimate_city_retrofit(city=city,
                                        overwrite_sh=overwrite_space_heat,
                                        overwrite_mod=overwrite_mod,
                                        print_output=print_out,
                                        t_set_heat=t_set_heat,
                                        skip_non_res=skip_non_res)

    pickle.dump(city_retro, open(save_path, mode='wb'))

    print()
    #  Loop over buildings
    for n in city_retro.nodes():
        #  If node holds attribute 'node_type'
        if 'node_type' in city_retro.node[n]:
            #  If node_type is building
            if city_retro.node[n]['node_type'] == 'building':
                #  If entity is kind building
                if city_retro.node[n]['entity']._kind == 'building':

                    building = city_retro.node[n]['entity']
                    print('Mod year of building ' + str(n) + ':')
                    print(building.mod_year)
