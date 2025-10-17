import resources
from src.PySimultan2.data_model import DataModel
from src.PySimultan2.object_mapper import PythonMapper
from src.PySimultan2.taxonomy_maps import TaxonomyMap, Content

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 importlib_resources.
    import importlib_resources as pkg_resources


with pkg_resources.path(resources, 'test_set_attr_property.simultan') as r_path:
    project_path = str(r_path)

data_model = DataModel.create_new_project(project_path=project_path,
                                          user_name='admin',
                                          password='admin')

mapper = PythonMapper()


class TestComponent(object):
    def __init__(self, *args, **kwargs):
        self.value = kwargs.get('value')
        self.value2 = kwargs.get('value2')


content0 = Content(text_or_key='value',  # text or key of the content/parameter/property
                   property_name='value',  # name of the generated property
                   type=None,  # type of the content/parameter/property
                   unit=None,  # unit of the content/parameter/property
                   documentation='value to test',
                   component_policy='subcomponent')

content1 = Content(text_or_key='value2',
                   property_name='value2',
                   type=None,
                   unit=None,
                   documentation='value2 to test',
                   component_policy='subcomponent',
                   ValueMin=100,
                   ValueMax=200)

test_component_map = TaxonomyMap(taxonomy_name='PySimultan',
                                 taxonomy_key='PySimultan',
                                 taxonomy_entry_name='TestComponent',
                                 taxonomy_entry_key='TestComponent',
                                 content=[content0, content1],
                                 )

mapper.register(test_component_map.taxonomy_entry_key, TestComponent, taxonomy_map=test_component_map)
cls1 = mapper.get_mapped_class(test_component_map.taxonomy_entry_key)

component = cls1(name='test_component',
                 value=78,
                 value2=350)

component.get_raw_attr('value')

component.set_attr_prop('value', 'ValueMin', 100)
component.set_attr_prop('value', 'ValueMax', 200)

data_model.save()
data_model.cleanup()
mapper.clear()


data_model = DataModel(project_path=project_path,
                       user_name='admin',
                       password='admin')


typed_data = mapper.get_typed_data(component_list=data_model.data, data_model=data_model)

pass
