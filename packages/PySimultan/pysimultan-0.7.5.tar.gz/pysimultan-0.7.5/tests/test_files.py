import os

from PySimultan2.data_model import DataModel
from PySimultan2.files import add_asset_to_component, create_asset_from_string
from PySimultan2 import FileInfo

from PySimultan2.object_mapper import PythonMapper
from PySimultan2.taxonomy_maps import TaxonomyMap, Content

import resources

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 importlib_resources.
    import importlib_resources as pkg_resources


with pkg_resources.path(resources, 'test_file_project.simultan') as r_path:
    project_path = str(r_path)

data_model = DataModel.create_new_project(project_path=project_path,
                                          user_name='admin',
                                          password='admin')


def test_create_resource():
    taxonomy = data_model.get_or_create_taxonomy('TestTagTaxonomy')
    tag = data_model.get_or_create_taxonomy_entry('TestTag', 'TestTag', sim_taxonomy=taxonomy)
    # create a new file:
    with pkg_resources.path(resources, 'new_test_file.txt') as r_path:
        with open(str(r_path), 'w') as f:
            f.write('This is the content of the file.')
        resource = data_model.add_resource(str(r_path),
                                           tag=tag)

    return resource


def test_create_resource_from_string():
    # create a new file from string:
    taxonomy = data_model.get_or_create_taxonomy('TestTagTaxonomy')
    tag = data_model.get_or_create_taxonomy_entry('TestTag2', 'TestTag2', sim_taxonomy=taxonomy)
    resource = create_asset_from_string('new_test_file_from_str.txt',
                                        'This is the content of the file.',
                                        data_model=data_model,
                                        tag=tag)

    return resource


def test_add_resource_to_component(resource):
    # create a new component:
    component = data_model.create_new_component('TestComponent')
    add_asset_to_component(component, resource)


def test_set_file():

    # create a new component
    mapper = PythonMapper()

    class TestComponent(object):
        def __init__(self, *args, **kwargs):
            self.file_value = kwargs.get('file_value')
            self.file_value_2 = kwargs.get('file_value_2')

    content0 = Content(text_or_key='file_value',  # text or key of the content/parameter/property
                       property_name='file_value',  # name of the generated property
                       type='file',  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='file_value to test')

    content1 = Content(text_or_key='file_value_2',  # text or key of the content/parameter/property
                       property_name='file_value_2',  # name of the generated property
                       type='file',  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='file_value_2 to test')

    test_component_map = TaxonomyMap(taxonomy_name='Test',
                                     taxonomy_key='Test',
                                     taxonomy_entry_name='TestComponent',
                                     taxonomy_entry_key='TestComponent',
                                     content=[content0, content1],
                                     )

    mapper.register(test_component_map.taxonomy_entry_key, TestComponent, taxonomy_map=test_component_map)
    mapped_test_component_cls = mapper.get_mapped_class(test_component_map.taxonomy_entry_key)

    with pkg_resources.path(resources, 'new_test_file2.txt') as r_path:
        with open(str(r_path), 'w') as f:
            f.write('This is the content of the file 2.')

        file_info = FileInfo(file_path=r_path)

    test_component = mapped_test_component_cls(name='test_component',
                                               file_value_2=file_info)

    return mapper


def test_add_resource_in_directory(mapper):

    file_path = os.path.join(str(data_model.project.ProjectUnpackFolder), 'already_exising.txt')

    with open(file_path, 'w') as f:
        f.write('This is the content of the already existing file.')

    file_info = FileInfo(file_path=file_path)
    mapped_test_component_cls = mapper.get_mapped_class('TestComponent')
    test_component = mapped_test_component_cls(name='test_component 2',
                                               file_value_2=file_info)

def test_add_resource_file():
    file_path = os.path.join(str(data_model.project.ProjectUnpackFolder), 'already_exising_2.txt')

    with open(file_path, 'w') as f:
        f.write('This is the content of the already existing file 2.')

    file = data_model.add_resource_file(file_path)
    file = data_model.add_resource(file_path)
    print(file)

    file_path = os.path.join(str(data_model.project.ProjectUnpackFolder), 'already_exising_3.txt')

    with open(file_path, 'w') as f:
        f.write('This is the content of the already existing file 3.')

    file_info = FileInfo.from_existing_file(file_path=file_path,
                                            data_model=data_model)

    mapped_test_component_cls = mapper.get_mapped_class('TestComponent')
    test_component3 = mapped_test_component_cls(name='test_component 3',
                                               file_value_2=file_info)


if __name__ == '__main__':
    new_resource = test_create_resource()
    test_create_resource_from_string()
    test_add_resource_to_component(new_resource)
    mapper = test_set_file()
    test_add_resource_in_directory(mapper)
    test_add_resource_file()
    data_model.save()

data_model.cleanup()
print('Test passed')
