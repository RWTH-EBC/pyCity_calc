
import os

import teaser.project as proj



if __name__ == '__main__':

    this_path = os.path.dirname(os.path.abspath(__file__))

    filename = 'LoD2_295_5628_1_NW.gml'

    # load_path = os.path.join(this_path, 'input_osm', 'Diss_Quartiere',
    #                          '3d-gm_lod2_05334002_Aachen_EPSG5555_CityGML',
    #                          filename)
    abs_path = r'T:\jsc\city_gml_aachen\3d-gm_lod2_05334002_Aachen_EPSG5555_CityGML'

    load_path = os.path.join(abs_path, filename)

    project = proj.Project()

    project.load_citygml(path=load_path)

    print(project.buildings)