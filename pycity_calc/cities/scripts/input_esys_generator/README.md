Possible energy system options for energy_sys_generator.py

Type	Method	Explanation
0	1	Boiler (full part load scale)
0	2	Boiler + TES
1	1	CHP + Boiler + TES (Max rectange method); Method checks if lhn exists 
1	2	CHP + Boiler + TES (Runtime method 5500 runtime); Method checks if lhn exists (fails, if CHP cannot reach required runtime!)
1	3	CHP + Boiler + TES (Nominal th. CHP power equal to max. thermal power)
1	4	CHP + Boiler + TES (Nominal th. CHP power as 1/5 share of max. thermal power)
2	1	HP (air/water) + EH + TES
2	2	HP (water/water) + EH + TES
3	area(float)	PV system
4	capacity(float)	Electric battery (capacity in kWh)
