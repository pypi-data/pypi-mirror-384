from datetime import datetime
import os
import numpy as np
import pandas as pd
from PySimultan2.data_model import DataModel
from PySimultan2.multi_values import *
from PySimultan2.utils import get_or_create_taxonomy_entry
from PySimultan2.object_mapper import PythonMapper
from PySimultan2.taxonomy_maps import TaxonomyMap, Content

from SIMULTAN.Utils import IntIndex3D
from SIMULTAN.Data.SimMath import SimPoint3D

import resources

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 importlib_resources.
    import importlib_resources as pkg_resources


with pkg_resources.path(resources, 'test_multi_value_field_project.simultan') as r_path:
    project_path = str(r_path)

data_model = DataModel.create_new_project(project_path=project_path,
                                          user_name='admin',
                                          password='admin')


def test_value_field_creation():
    numpy_array = np.arange(1000, dtype=float).reshape(10, 10, 10)
    field = numpy_to_simultan_multi_value_field_3d(numpy_array, 'test_field')
    array = simultan_multi_value_field_3d_to_numpy(field)

    assert np.allclose(numpy_array, array)


def test_pandas_value_field_creation():
    df = pd.DataFrame(np.arange(24, dtype=float).reshape(6, 4),
                      columns=list("ABCD"))
    field = pandas_to_simultan_multi_value_big_table(df, 'test_field')
    loaded_df = simultan_multi_value_big_table_to_pandas(field)

    assert np.allclose(df.values, loaded_df.values)


def test_parameter_creation():
    tax_entry = get_or_create_taxonomy_entry(name='test_slot', key='test_slot', data_model=data_model)
    numpy_array = np.random.rand(10, 10, 10)
    parameter = create_field_parameter(name='test_parameter',
                                       value=numpy_array,
                                       slot=tax_entry,
                                       data_model=data_model)
    assert np.allclose(numpy_array, simultan_multi_value_field_3d_to_numpy(parameter.ValueSource.Field))

# data_model.data[0].Parameters[0].ValueSource.Field.GetValue(SimPoint3D(0, 0, 0))


def test_typed_data_model():

    mapper = PythonMapper()
    data = data_model.get_typed_data(mapper)
    assert data[0]._parameters


def test_set_parameter_to_value_field():

    # create a new component
    mapper = PythonMapper()

    class TestComponent(object):
        def __init__(self, *args, **kwargs):
            self.numpy_value = kwargs.get('numpy_value')
            self.pandas_value = kwargs.get('pandas_value')

    content0 = Content(text_or_key='numpy_value',  # text or key of the content/parameter/property
                       property_name='numpy_value',  # name of the generated property
                       type=np.ndarray,  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='numpy_value to test')

    content1 = Content(text_or_key='pandas_value',  # text or key of the content/parameter/property
                       property_name='pandas_value',  # name of the generated property
                       type=np.ndarray,  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='pandas_value to test')

    test_component_map = TaxonomyMap(taxonomy_name='Test',
                                     taxonomy_key='Test',
                                     taxonomy_entry_name='TestComponent',
                                     taxonomy_entry_key='TestComponent',
                                     content=[content0, content1],
                                     )

    mapper.register(test_component_map.taxonomy_entry_key, TestComponent, taxonomy_map=test_component_map)
    mapped_test_component_cls = mapper.get_mapped_class(test_component_map.taxonomy_entry_key)

    df = pd.DataFrame(np.random.rand(6, 4),
                      columns=list("ABCD"))

    test_component = mapped_test_component_cls(name='test_component',
                                               numpy_value=np.random.rand(10, 10, 10),
                                               pandas_value=df)

    test_component.numpy_value = np.arange(1000, dtype=float).reshape(10, 10, 10)
    test_component.pandas_value = pd.DataFrame(np.arange(24, dtype=float).reshape(6, 4),
                                               columns=list("ABCD"))

    data_model.save()


if __name__ == '__main__':
    test_value_field_creation()
    test_pandas_value_field_creation()
    test_parameter_creation()
    test_set_parameter_to_value_field()
    test_typed_data_model()


data_model.cleanup()
print('Test passed')
