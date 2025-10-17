from PySimultan2.src.PySimultan2 import DataModel
from PySimultan2.src.PySimultan2 import PythonMapper
from PySimultan2.src.PySimultan2.taxonomy_maps import TaxonomyMap, Content
from PySimultan2.src.PySimultan2.simultan_object import SimultanObject

from PySimultan2.tests import resources

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 importlib_resources.
    import importlib_resources as pkg_resources


with pkg_resources.path(resources, 'test_parameter_reference_project.simultan') as r_path:
    project_path = str(r_path)

data_model = DataModel(project_path=project_path,
                       user_name='admin',
                       password='admin')


param_ref_component =  next((x for x in data_model.data if x.Name == 'ParamRefComponent'), None)
orig_component = next((x for x in data_model.data if x.Name == 'OrigComponent'), None)
param_ref_component.Parameters[0]
orig_component.Parameters[0]

def test_load_file_component():

    # create a new component
    mapper = PythonMapper()

    class TestComponent(object):
        def __init__(self, *args, **kwargs):
            self.file_content_1 = kwargs.get('file_content_1')
            self.file_content_2 = kwargs.get('file_content_2')

    content0 = Content(text_or_key='file_content_1',  # text or key of the content/parameter/property
                       property_name='file_content_1',  # name of the generated property
                       type='file',  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='file_value to test')

    content1 = Content(text_or_key='file_content_2',  # text or key of the content/parameter/property
                       property_name='file_content_2',  # name of the generated property
                       type='file',  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='file_value_2 to test')

    content2 = Content(text_or_key='param_1',  # text or key of the content/parameter/property
                       property_name='param_1',  # name of the generated property
                       type=None,  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='param_1 to test')

    content3 = Content(text_or_key='param_2',  # text or key of the content/parameter/property
                       property_name='param_2',  # name of the generated property
                       type=None,  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='param_2 to test')

    content4 = Content(text_or_key='sub_component',  # text or key of the content/parameter/property
                       property_name='sub_component',  # name of the generated property
                       type=None,  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='sub_component to test')

    content5 = Content(text_or_key='referenced_component',  # text or key of the content/parameter/property
                       property_name='referenced_component',  # name of the generated property
                       type=None,  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='referenced_component to test')

    test_component_map = TaxonomyMap(taxonomy_name='PySimultan',
                                     taxonomy_key='Test',
                                     taxonomy_entry_name='test_component',
                                     taxonomy_entry_key='test_component',
                                     content=[content0, content1, content2, content3, content4, content5],
                                     )

    mapper.register(test_component_map.taxonomy_entry_key, TestComponent, taxonomy_map=test_component_map)
    mapped_test_component_cls = mapper.get_mapped_class(test_component_map.taxonomy_entry_key)

    data = data_model.get_typed_data(mapper)
    assert type(data[0].file_content_1) is FileInfo
    assert data[0].param_2 == 10
    assert isinstance(data[0].sub_component, SimultanObject)

    print(data[0].file_content_1.content)


if __name__ == '__main__':
    print(data_model.data[0].ReferencedAssets[0].ResourceKey)
    print(data_model.data[0].ReferencedAssets[0].Resource)
    print(data_model.data[0].ReferencedAssets[0].Resource.Name)
    print(data_model.data[0].ReferencedAssets[0].Resource.File.FullPath)

    test_load_file_component()

data_model.cleanup()
print('Test passed')
