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



Table of build_types
------------------------------------
type_id	type_name	Spec. combustible final energy demand in kWh/m2*a	Spec. el. demand in kWh/m2*a	SLP_th_type	SLP_el_type
0	Residential building (generation possible via TEASER)
1	Office building (generation possible via TEASER)
2	Bauhauptgewerbe	22.96	53.74	3	1
3	Ausbaugewerbe	28.66	76.7	3	1
4	Banken, Versicherung	49.69	136.98	7	2
5	Oeffentl. Einrichtungen	40.07	139.63	7	1
6	Org. ohne Erwerbszweck	50.23	255.21	7	1
7	Kleine Bueros	5.6	184.05	7	1
8	Sonst. Dienstleistungen	75.86	174.72	13	1
9	Metall	55.44	69.41	3	1
10	KFZ	26.31	79.88	3	1
11	Holz	37.88	86.35	3	1
12	Papier	92.18	131.76	4	2
13	Einzelhandel Lebensmittel	145.58	143.67	5	5
14	Einzelhandel Non-food	32.71	68.34	5	5
15	Großhandel Lebensmittel	48.43	61.82	5	5
16	Grosshandel Non-food	38.79	71.15	5	5
17	Grund-/Hauptschule	102.08	10.04	7	1
18	Behindertenschule	92.73	23.17	7	1
19	Realschule/Gymnasium	168.49	18.71	7	1
20	Berufsschule	97.39	67.12	7	1
21	Hochschule	160.12	60.31	7	1
22	Hotels	172.9	118.44	8	1
23	Gaststaetten	259.75	124.03	9	1
24	Heim	122.81	34.64	7	1
25	Baeckerei	403.95	205.55	10	6
26	Fleischerei	182.95	79.2	5	5
27	Waescherei	471.59	283.9	11	1
28	Ueberwiegend Ackerbau	1136.17	227.75	12	8
29	Mischbetriebe 10 - 49 GVE	710.87	179.19	12	8
30	Mischbetriebe 50 - 100 GVE	196.32	67.86	12	8
31	Viehhaltung > 100 GVE	251.41	124.09	12	9
32	Gartenbau	2688	232	12	10
33	Krankenhaus	192.13	101.64	8	1
34	Bibliotheksgebaeude	80	55	7	1
35	Gefaengnisse	260	60	7	1
36	Kino	80	115	6	7
37	Theater, Oper	155	60	6	7
38	Jugendhaeuser, Gemeindehaeuser	150	30	7	1
39	Sporthalle	170	50	7	1
40	Mehrzweckhalle	345	55	7	1
41	Schwimmhalle	550	150	8	1
42	Sportheim, Vereinsheim	115	25	8	1
43	Fitnessstudio	140	170	7	1
44	Bahnhof < 5000m2	170	45	9	1
45	Bahnhof >= 5000m2	165	140	5	1
