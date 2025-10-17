import numpy as np
import pandas as pd

from PySimultan2.data_model import DataModel
from PySimultan2 import FileInfo

from PySimultan2.object_mapper import PythonMapper
from PySimultan2.taxonomy_maps import TaxonomyMap, Content

import resources

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 importlib_resources.
    import importlib_resources as pkg_resources


with pkg_resources.path(resources, 'test_set_value_project.simultan') as r_path:
    project_path = str(r_path)

data_model = DataModel.create_new_project(project_path=project_path,
                                          user_name='admin',
                                          password='admin')

mapper = PythonMapper()


def map_classes():
    class TestComponent(object):
        def __init__(self, *args, **kwargs):
            self.value = kwargs.get('mapped_property')

    content0 = Content(text_or_key='value',  # text or key of the content/parameter/property
                       property_name='mapped_property',  # name of the generated property
                       type=None,  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='mapped_property to test',
                       component_policy='subcomponent')

    content1 = Content(text_or_key='value2',  # text or key of the content/parameter/property
                       property_name='value2',  # name of the generated property
                       type=None,  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='value2',
                       component_policy='reference')

    test_component_map = TaxonomyMap(taxonomy_name='PySimultan',
                                     taxonomy_key='PySimultan',
                                     taxonomy_entry_name='TestComponent',
                                     taxonomy_entry_key='TestComponent',
                                     content=[content0, content1],
                                     )

    mapper.register(test_component_map.taxonomy_entry_key, TestComponent, taxonomy_map=test_component_map)
    cls1 = mapper.get_mapped_class(test_component_map.taxonomy_entry_key)

    test_component_map_2 = TaxonomyMap(taxonomy_name='PySimultan',
                                       taxonomy_key='PySimultan',
                                       taxonomy_entry_name='TestComponent2',
                                       taxonomy_entry_key='TestComponent2',
                                       content=[content0],
                                       )

    mapper.register(test_component_map_2.taxonomy_entry_key, TestComponent, taxonomy_map=test_component_map_2)
    cls2 = mapper.get_mapped_class(test_component_map_2.taxonomy_entry_key)

    return cls1, cls2


mapped_cls_1, mapped_cls_2 = map_classes()
component = mapped_cls_1(name='test_component',
                         value=None)


def test_set_parameter(test_component):
    test_component.mapped_property = 'test_value'
    assert test_component.mapped_property == 'test_value'

    test_component.mapped_property = 1
    assert test_component.mapped_property == 1

    test_component.mapped_property = 1.0
    assert test_component.mapped_property == 1.0

    test_component.mapped_property = True
    assert test_component.mapped_property


def test_set_set_file(test_component):

    with pkg_resources.path(resources, 'new_test_file_1.txt') as r_path:
        with open(str(r_path), 'w') as f:
            f.write('This is the content of the file 1.')

        file_info_1 = FileInfo(file_path=r_path)

    with pkg_resources.path(resources, 'new_test_file_2.txt') as r_path:
        with open(str(r_path), 'w') as f:
            f.write('This is the content of the file 2.')

        file_info_2 = FileInfo(file_path=r_path)

    test_component.mapped_property = file_info_1
    assert test_component.mapped_property.content == 'This is the content of the file 1.'

    test_component.mapped_property = file_info_2
    assert test_component.mapped_property.content == 'This is the content of the file 2.'


def test_set_value_field(test_component):

    df = pd.DataFrame(np.random.rand(6, 4),
                      columns=list("ABCD"))

    numpy_value = np.arange(1000, dtype=float).reshape(10, 10, 10)

    test_component.mapped_property = numpy_value
    assert np.array_equal(test_component.mapped_property, numpy_value)

    test_component.mapped_property = df
    assert np.array_equal(test_component.mapped_property.values, df.values)

    df['A'] = df['A'] * 2

    test_component.value2 = df
    assert np.array_equal(test_component.value2.values, df.values)
    assert np.array_equal(test_component.mapped_property.values, df.values)


def set_referenced_component(test_component):
    referenced_component = mapped_cls_2(name='referenced_component',
                                        value=None)
    test_component.mapped_property = referenced_component
    assert test_component.mapped_property._wrapped_obj.Id.Equals(referenced_component.Id)


def test_set_dictionary_param(test_component):
    test_dict = {'val_a': 1,
                 'val_b': 2.0,
                 'val_c': 'test'}
    test_component.mapped_property = test_dict
    test_component.mapped_property['val_a'] = 222

    assert test_component.mapped_property['val_a'] == 222


def set_new_component(test_component):
    new_component = data_model.create_new_component('SubComponent',
                                                    add_to_project=False)
    test_component.mapped_property = new_component
    assert test_component.mapped_property._wrapped_obj.Id.Equals(new_component.Id)


if __name__ == '__main__':
    test_set_parameter(component)
    test_set_dictionary_param(component)
    test_set_set_file(component)
    test_set_value_field(component)
    set_referenced_component(component)
    # set_new_component(component)
    data_model.save()

data_model.cleanup()
print('Test passed')
