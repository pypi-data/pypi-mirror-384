import os

from PySimultan2.data_model import DataModel
from PySimultan2.object_mapper import PythonMapper
from PySimultan2.taxonomy_maps import TaxonomyMap, Content

# from bson.objectid import ObjectId


dir_path = os.path.dirname(os.path.realpath(__file__))

project_path = 'resources/U5.simultan'
data_model = DataModel(project_path=project_path,
                       user_name='admin',
                       password='admin')


def create_of_volume_taxonomie_map(filename=None):

    content0 = Content(text_or_key='surface_mesh_setup',         # text or key of the content/parameter/property
                       property_name='surface_mesh_setup',       # name of the generated property
                       type=None,                                # type of the content/parameter/property
                       unit=None,                                # unit of the content/parameter/property
                       documentation='Component or reference which represents the surface_mesh_setup')

    content1 = Content(text_or_key='material',  # text or key of the content/parameter/property
                       property_name='material',  # name of the generated property
                       type=None,  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='Component or reference which represents the material of the volume')

    of_volume = TaxonomyMap(taxonomie_name='of_volume',
                            taxonomie_key='of_volume',
                            content=[content0, content1],
                            )

    if filename is not None:
        of_volume.write(filename=filename)
    return of_volume


def create_material_taxonomie_map(filename=None):

    content0 = Content(text_or_key='density',         # text or key of the content/parameter/property
                       property_name='density',       # name of the generated property
                       type=None,                                # type of the content/parameter/property
                       unit=None,                                # unit of the content/parameter/property
                       documentation='Component or reference which represents Density')

    content1 = Content(text_or_key='state',  # text or key of the content/parameter/property
                       property_name='state',  # name of the generated property
                       type=None,  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='Component or reference which represents the material state')

    material = TaxonomyMap(taxonomie_name='material',
                           taxonomie_key='material',
                           content=[content0, content1],
                           )

    if filename is not None:
        material.write(filename=filename)
    return material


class Undefined(object):

    def __init__(self, *args, **kwargs):
        pass


host = 'mongodb://root:example@localhost:27017/?authMechanism=DEFAULT'

of_volume_map = create_of_volume_taxonomie_map(filename='of_volume_map.yaml')
material_map = create_material_taxonomie_map(filename='material_map.yaml')

mapper = PythonMapper()
mapper.register('of_volume', OFVolume, taxonomie_map=of_volume_map)
mapper.register('material', OFMaterial, taxonomie_map=material_map)
mapper.register('undefined', Undefined)
of_volumes = data_model.find_components_with_taxonomy(taxonomy='of_volume')

py_of_volumes = mapper.get_typed_data(component_list=of_volumes)


save_data_model_in_mongodb(host,
                           data_model=data_model,
                           db='of_api_test_db')

print([x.surface_mesh_setup for x in py_of_volumes])
print(py_of_volumes[0].material.state)

[save_in_mongodb(x, host, db='of_api_test_db') for x in py_of_volumes]

typed_data = data_model.get_typed_data(mapper)

typed_data[1].get_subcomponents()

data_model.cleanup()

components = list(load_from_mongodb(host))
print(components[6].instances[0].placements[0].geometry.faces[2].boundary.edges[0].vertices[0])
drop_mongodb(host)

print('ok')
