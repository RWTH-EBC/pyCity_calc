Options for energy network generator:

network_id: int
	Network id (e.g. 1)

nodelist: list (of ints)
	List holding building node ids, which should be connected with specific network
	
type: str
	String defining network type
	Options:
	- 'heating' : Local heating network (LHN)
	- 'heating_and_deg' : LHN and decentralized, electrical grid (DEG)
	- 'deg' : DEG, only
	
method: int
	Method to generate/dimension network 
	Options:
	- 1 : Use shortest, areal connection
	- 2 : Use street routing (pipes can only follow street routes)