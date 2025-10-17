import os

project_dir = os.environ.get('PROJECT_DIR', '/simultan_projects')
if not os.path.exists(project_dir):
    os.makedirs(project_dir)

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 importlib_resources.
    import importlib_resources as pkg_resources

from PySimultan2.taxonomy_maps import Content, TaxonomyMap
from PySimultan2 import PythonMapper
from PySimultan2 import DataModel


mapper = PythonMapper(module='test_default_component')

class A:

    def __init__(self,
                 name: str = 'A',
                 param_a: int = 0,
                 param_b: float = 0.0,
                 param_c: str = 'test_str',
                 *args, **kwargs):

        self.name = name
        self.param_a = param_a
        self.param_b = param_b
        self.param_c = param_c


# define content

param_a_content = Content(text_or_key='param_a',
                          property_name='param_a',
                          type=None,
                          unit='',
                          documentation='',
                          component_policy='subcomponent')

param_b_content = Content(text_or_key='param_b',
                          property_name='param_b',
                          type=None,
                          unit='',
                          documentation='',
                          component_policy='subcomponent')

param_c_content = Content(name='This is the Name of the Content C',
                          text_or_key='param_c',
                          property_name='param_c',
                          type=None,
                          unit='',
                          documentation='',
                          component_policy='subcomponent')

# define taxonomy maps
a_map = TaxonomyMap(taxonomy_name='test_default_component',
                    taxonomy_key='test_default_component',
                    taxonomy_entry_name='A',
                    taxonomy_entry_key='A',
                    content=[param_a_content,
                             param_b_content,
                             param_c_content]
                    )

# register taxonomy maps
mapper.register(a_map.taxonomy_entry_key,
                A,
                taxonomy_map=a_map,
                re_register=True)


mapper.default_components.append(A(name='default_A',
                                   param_a=5,
                                   param_b=8.0,
                                   param_c='default_str'))


data_model = DataModel.create_new_project(project_path=os.path.join(project_dir, 'test_default_component.simultan'),
                                          user_name='admin',
                                          password='admin')

typed_data = data_model.get_typed_data(mapper=mapper,
                                       create_all=True)
MappedAClass = mapper.get_mapped_class('A')


assert MappedAClass.cls_instances[0].name == 'default_A'

data_model.save()
mapper.clear()

data_model = DataModel(project_path=os.path.join(project_dir, 'test_default_component.simultan'),
                          user_name='admin',
                       password='admin')
typed_data = data_model.get_typed_data(mapper=mapper,
                                       create_all=True)
MappedAClass = mapper.get_mapped_class('A')


assert MappedAClass.cls_instances[0].name == 'default_A'
