Input folder for city generator.

Important: Generator assumes that input within field "Annual thermal e demand in kWh" 
is final thermal energy demand value (e.g. gas or oil) for space heating.
(Domestic hot water profile can be generated, seperately) 
This value is converted within 
city generator to net thermal demand value (via eff_factor=0.85). If net thermal
energy demand should be used as input, set eff_factor = 1!


Explanations about input parameters:

    Columns:
    1:  id (int)
    2:  x in m (float)
    3:  y in m (float)
    4:  building_type (int, e.g. 0 for residential building)
    5:  net floor area in m2 (float)
    6:  Year of construction (int, optional)
    7:  Year of modernization (int, optional)
    8:  Annual (final) space heating energy demand in kWh (float, optional)
	(hot water profiles are generated, separately)
    9:  Annual electrical energy demand in kWh (float, optional)
    10: Usable pv roof area in m2 (float, optional)
    11: Number of apartments (int, optional)
    12: Total number of occupants (int, optional)
    13: Number of floors above the ground (int, optional)
    14: Average Height of floors (float, optional)
    15: If building has a central AHU or not (boolean, optional)
    16: Residential layout (int, optional, e.g. 0 for compact)
    17: Neighbour Buildings (int, optional); 0 - free standing; 1 - Double house; 2 - Row house;
    18: Type of attic (int, optional, e.g. 0 for flat roof); 1 - Roof, non heated; 2 - Roof, partially heated; 3- Roof, fully heated;
    19: Type of basement (int, optional, e.g. 1 for non heated basement 0 - No basement; 1 - basement, non heated; 2 - basement, partially heated; 3- basement, fully heated;
    20: Dormer (int, optional, 0: no dormer/ 1: dormer)
    21: Construction Type(heavy/light, optional) (0 - heavy; 1 - light)
    22: Method_3_nb (for usage of measured, weekly non-res. el. profile
    (optional) (0 to 4)
    23: Method_4_nb (for usage of measured, annual non-res. el. profile
    (optional) (0 - 2)

	method_3_type : str, optional
            Defines type of profile for method=3 (default: None)
            Options:
            0 - 'food_pro': Food production
            1 - 'metal': Metal company
            2 - 'rest': Restaurant (with large cooling load)
            3 - 'sports': Sports hall
            4 - 'repair': Repair / metal shop
        method_4_type : str, optional
            Defines type of profile for method=4 (default: None)
            0 - 'metal_1' : Metal company with smooth profile
            1 - 'metal_2' : Metal company with fluctuation in profile
            2 - 'warehouse' : Warehouse