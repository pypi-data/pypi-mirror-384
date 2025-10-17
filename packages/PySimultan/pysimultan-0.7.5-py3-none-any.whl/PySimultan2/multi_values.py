from __future__ import annotations
from typing import Union
from itertools import product

import numpy as np
import pandas as pd
from SIMULTAN.Data.Components import SimDoubleParameter, SimParameterOperations
from SIMULTAN.Data.MultiValues import (SimMultiValueField3D, SimMultiValueField3DParameterSource, SimMultiValueBigTable,
                                       SimMultiValueBigTableHeader, SimMultiValueBigTableParameterSource)
from SIMULTAN.Data.Taxonomy import SimTaxonomyEntry
from System import Array, Double, Object, Boolean, String
from System.Collections.Generic import List as NetList
from System.Collections.Generic import ICollection as NetICollection
from pandas import DataFrame

import System


class SimultanPandasDataFrame(pd.DataFrame):
    # temporary properties

    # normal properties
    _metadata = ["SimultanField"]

    @property
    def _constructor(self):
        return SimultanPandasDataFrame



def numpy_to_simultan_multi_value_field_3d(array: np.ndarray,
                                           name: str = 'UnnamedField',
                                           x_axis: list = None,
                                           y_axis: list = None,
                                           z_axis: list = None,
                                           unit_x: str = '',
                                           unit_y: str = '',
                                           unit_z: str = '',
                                           can_interpolate: bool = True) -> SimMultiValueField3D:
    """
    Convert a numpy array to a SimMultiValueField3D object. The x, y, and z axes can be provided as lists.
    If not provided, the axes will be generated based on the shape of the input array.
    :param array: The input numpy array
    :param name: The name of the field, default is 'UnnamedField'
    :param x_axis: The x-axis of the field, default is None
    :param y_axis: The y-axis of the field, default is None
    :param z_axis: The z-axis of the field, default is None
    :param unit_x: The unit of the x-axis, default is ''
    :param unit_y: The unit of the y-axis, default is ''
    :param unit_z: The unit of the z-axis, default is ''
    :param can_interpolate: If True, the field can be interpolated. Default is True.
    data_model = None
    :return:
    """
    if not isinstance(array, np.ndarray):
        raise ValueError('The input array must be a numpy array.')

    if array.ndim < 3:
        if array.ndim == 1:
            array = np.expand_dims(array, axis=(1, 2))
        elif array.ndim == 2:
            array = np.expand_dims(array, axis=2)
        else:
            raise ValueError('The input array must be at least 2-dimensional.')

    if x_axis is None:
        x_axis = NetList[Double](Array[Double](list(range(array.astype(float).shape[0]))))

    if y_axis is None:
        y_axis = NetList[Double](Array[Double](list(range(array.astype(float).shape[1]))))

    if z_axis is None:
        z_axis = NetList[Double](Array[Double](list(range(array.astype(float).shape[2]))))

    data = NetList[Double](Array[Double](array.astype(float).flatten(order='F')))

    field = SimMultiValueField3D(name, x_axis, unit_x, y_axis, unit_y, z_axis, unit_z, data, can_interpolate)

    return field


def pandas_to_simultan_multi_value_big_table(df: pd.DataFrame,
                                             name: str = 'UnnamedField',
                                             unit_columns: str = '',
                                             unit_rows: str = '',
                                             column_headers: SimMultiValueBigTableHeader = None,
                                             row_headers: SimMultiValueBigTableHeader = None) -> SimMultiValueBigTable:
    """
    Convert a pandas DataFrame to a SimMultiValueField3D object. The x, y, and z axes can be provided as lists. If not
    provided, the axes will be generated based on the shape of the input DataFrame.
    :param df:
    :param name:
    :param unit_columns: The unit of the columns
    :param unit_rows: The unit of the rows
    :param column_headers: The column headers
    :param row_headers: The row headers
    :return: SimMultiValueBigTable
    """

    if not isinstance(df, DataFrame):
        raise ValueError('The input df must be a pandas DataFrame.')

    if column_headers is None:
        column_headers = NetICollection[SimMultiValueBigTableHeader](
            Array[SimMultiValueBigTableHeader]([SimMultiValueBigTableHeader(str(x), '') for x in df.columns]))

    if row_headers is None:
        row_headers = NetICollection[SimMultiValueBigTableHeader](
            Array[SimMultiValueBigTableHeader]([SimMultiValueBigTableHeader(str(x), '') for x in df.index]))

    #
    data = NetList[NetList[Double]]()
    for i in range(len(df.index)):
        data.Add(NetList[Double](Array[Double](df.values[i].astype(float))))

    field = SimMultiValueBigTable(name,
                                  unit_columns,
                                  unit_rows,
                                  column_headers,
                                  row_headers,
                                  data,
                                  True)
    return field


def simultan_multi_value_big_table_to_pandas(field: SimMultiValueBigTable) -> pd.DataFrame:
    """
    Convert a SimMultiValueBigTable object to a pandas DataFrame.
    :param field:
    :return:
    """
    if not isinstance(field, SimMultiValueBigTable):
        raise ValueError('The input field must be a SimMultiValueBigTable object.')

    data = np.ndarray((field.RowHeaders.Count, field.ColumnHeaders.Count))
    for i in range(field.RowHeaders.Count):
        data[i, :] = list(field.GetRow(i))

    df = SimultanPandasDataFrame(data, columns=[x.Name for x in field.ColumnHeaders], index=[x.Name for x in field.RowHeaders])
    df.SimultanField = {'id': field.Id, 'name': field.Name}

    return df


def simultan_multi_value_field_3d_to_numpy(field: SimMultiValueField3D,
                                           assert_ordered=False,
                                           squeeze: bool = True) -> np.ndarray:
    """
    Convert a SimMultiValueField3D object to a numpy array.
    :param field:
    :param assert_ordered: If True, the function will check if the field is ordered. Default is True.
    :return:
    """
    if not isinstance(field, SimMultiValueField3D):
        raise ValueError('The input field must be a SimMultiValueField3D object.')

    if assert_ordered:
        data = [x.Value for x in field.Field]
        x_axis = list(field.XAxis)
        y_axis = list(field.YAxis)
        z_axis = list(field.ZAxis)
        array = np.array(data).reshape(len(x_axis), len(y_axis), len(z_axis))
    else:
        array = np.empty((len(field.XAxis), len(field.YAxis), len(field.ZAxis)))
        for comb in product(range(len(field.XAxis)), range(len(field.YAxis)), range(len(field.ZAxis)), repeat=1):
            array[comb[0], comb[1], comb[2]] = field[comb[0], comb[1], comb[2]]

    if squeeze:
        return np.squeeze(array)
    else:
        return array


def add_field_to_data_model(field: SimMultiValueField3D, data_model: 'SimultanObject') -> SimMultiValueField3D:
    """
    Add a SimMultiValueField3D object to a data model.
    :param field: The SimMultiValueField3D object
    :param data_model: The data model
    :return: SimMultiValueField3D
    """
    if not isinstance(field, SimMultiValueField3D):
        raise ValueError('The input field must be a SimMultiValueField3D object.')

    if data_model is None:
        raise ValueError('The data model must not be None.')
    data_model.add_field(field)


def set_parameter_to_value_field(parameter: SimDoubleParameter,
                                 value: Union[SimMultiValueField3D, np.ndarray, DataFrame],
                                 field_name: str = None,
                                 x_ax_val: float = None,
                                 y_ax_val: float = None,
                                 z_ax_val: float = None,
                                 data_model=None) -> SimDoubleParameter:
    """
    Set the value of a field parameter to a SimMultiValueField3D object. The value can be a SimMultiValueField3D object,
    a numpy array, or a DataFrame.
    :param parameter: The field parameter
    :param value: The value of the parameter (SimMultiValueField3D, numpy array, or DataFrame)
    :param field_name: The name of the field, default is None
    :param x_ax_val: The value on the X-Axis (NOT the index/position)
    :param y_ax_val: The value on the Y-Axis (NOT the index/position)
    :param z_ax_val: The value on the Z-Axis (NOT the index/position)
    :param data_model: The data model, default is None. If data_model is not None, the SimMultiValueField3D will be
    added to the data model (if SimMultiValueField3D is created).
    :return: SimDoubleParameter
    """

    _ = x_ax_val

    def default_value_source(val_field: SimMultiValueField3D,
                             x_ax: float = None,
                             y_ax: float = None,
                             z_ax: float = None):
        x_ax = x_ax if x_ax is not None else val_field.XAxis[0]
        y_ax = y_ax if y_ax is not None else val_field.YAxis[0]
        z_ax = z_ax if z_ax is not None else val_field.ZAxis[0]
        return SimMultiValueField3DParameterSource(val_field, x_ax, y_ax, z_ax)

    if not isinstance(parameter, SimDoubleParameter):
        raise ValueError('The input parameter must be a SimDoubleParameter object.')

    if isinstance(value, SimMultiValueField3D):
        # source = value
        source = default_value_source(value, x_ax_val, y_ax_val, z_ax_val)
    elif isinstance(value, np.ndarray):
        value_field = numpy_to_simultan_multi_value_field_3d(value,
                                                             name=field_name if field_name is not None else str(
                                                                 parameter.Id) + '_field')
        if data_model is not None:
            data_model.add_field(value_field)

        # x_ax_val = x_ax_val if x_ax_val is not None else value_field.XAxis[0]
        # y_ax_val = y_ax_val if y_ax_val is not None else value_field.YAxis[0]
        # z_ax_val = z_ax_val if z_ax_val is not None else value_field.ZAxis[0]
        #
        # source = SimMultiValueField3DParameterSource(value_field, x_ax_val, y_ax_val, z_ax_val)
        source = default_value_source(value_field, x_ax_val, y_ax_val, z_ax_val)
    elif isinstance(value, SimultanPandasDataFrame):
        field = next(x for x in data_model.value_fields if x.Id.Equals(value.SimultanField['id']))  # check if field is in data model
        value_field = pandas_to_simultan_multi_value_big_table(value,
                                                               name=field_name if field_name is not None else str(
                                                               parameter.Id) + '_field')
        field.ReplaceData(value_field)
        source = SimMultiValueBigTableParameterSource(field, 0, 0)

    elif isinstance(value, pd.DataFrame):
        value.__class__ = SimultanPandasDataFrame  # change class to add temporary properties
        value_field = pandas_to_simultan_multi_value_big_table(value,
                                                               name=field_name if field_name is not None else str(
                                                                   parameter.Id) + '_field')
        if data_model is not None:
            data_model.add_field(value_field)

        source = SimMultiValueBigTableParameterSource(value_field, 0, 0)
        value.SimultanField = {'id': value_field.Id, 'name': value_field.Name}

    else:
        raise ValueError('The value of the field parameter must be a numpy array or a DataFrame.')

    parameter.set_ValueSource(source)
    return parameter


def create_field_parameter(value: Union[SimMultiValueField3D, np.ndarray, DataFrame],
                           name: str = 'unnamed parameter',
                           field_name: str = None,
                           unit: str = '',
                           slot: SimTaxonomyEntry = None,
                           min_value: float = None,
                           max_value: float = None,
                           allowed_operations: int = SimParameterOperations(0).All,
                           x_ax_val: float = None,
                           y_ax_val: float = None,
                           z_ax_val: float = None,
                           data_model=None
                           ) -> SimDoubleParameter:
    """
    Create a field parameter with a SimMultiValueField3D as value.  The value can be a SimMultiValueField3D object, a
    numpy array, or a DataFrame.
    :param value: The value of the parameter (SimMultiValueField3D, numpy array, or DataFrame)
    :param name: The name of the parameter, default is 'unnamed parameter'
    :param field_name: The name of the field, default is None
    :param unit: The unit of the parameter, default is ''
    :param slot: SimTaxonomyEntry
    :param min_value: The minimum value for the parameter, default is None
    :param max_value: The maximum value for the parameter, default is None
    :param allowed_operations: The allowed operations for the parameter (e.g. SimParameterOperations(0).All)
    :param x_ax_val: The value on the X-Axis (NOT the index/position)
    :param y_ax_val: The value on the Y-Axis (NOT the index/position)
    :param z_ax_val: The value on the Z-Axis (NOT the index/position)
    :param data_model: The data model, default is None. If data_model is not None, the SimMultiValueField3D will be
    added to the data model.
    :return: SimDoubleParameter
    """

    from .utils import create_sim_double_parameter

    param_init_dict = {'value': 0}

    for key in ['name', 'unit', 'slot', 'min_value', 'max_value', 'allowed_operations']:
        if locals()[key] is not None:
            param_init_dict[key] = locals()[key]

    param = create_sim_double_parameter(**param_init_dict)

    set_parameter_to_value_field(param,
                                 value,
                                 field_name=field_name,
                                 x_ax_val=x_ax_val,
                                 y_ax_val=y_ax_val,
                                 z_ax_val=z_ax_val,
                                 data_model=data_model
                                 )

    return param


def add_row(field: SimMultiValueField3D,
            dim: int = 0):

    array = simultan_multi_value_field_3d_to_numpy(field, squeeze=False)

    new_shape = list(array.shape)
    if new_shape.__len__() - 1 < dim:
        while new_shape.__len__() - 1 < dim:
            new_shape.append(1)
    new_shape[dim] += 1

    # data = NetList[Double](Array[Double](array.astype(float).flatten(order='F')))

    while field.XAxis.Count < new_shape[0]:
        field.XAxis.Add(field.XAxis.Count+1)
    while field.YAxis.Count < new_shape[1]:
        field.YAxis.Add(field.YAxis.Count+1)
    while field.ZAxis.Count < new_shape[2]:
        field.ZAxis.Add(field.ZAxis.Count+1)

    resized_array = np.resize(array, new_shape)

    for i, j, k in zip(range(new_shape[0]), range(new_shape[1]), range(new_shape[2])):
        field[i, j, k] = resized_array[i, j, k]

    return field


def resize(field: SimMultiValueField3D,
           new_shape: list[int]) -> SimMultiValueField3D:
    """
    Resize a SimMultiValueField3D object to a new shape.
    :param field: The SimMultiValueField3D object
    :param new_shape: The new shape of the field, e.g. [10, 20, 30]
    :return: SimMultiValueField3D
    """
    array = simultan_multi_value_field_3d_to_numpy(field, squeeze=False)
    resized_array = np.resize(array, new_shape)

    while field.XAxis.Count < resized_array.shape[0]:
        field.XAxis.Add(field.XAxis.Count+1)
    while field.YAxis.Count < resized_array.shape[1]:
        field.YAxis.Add(field.YAxis.Count+1)
    while field.ZAxis.Count < resized_array.shape[2]:
        field.ZAxis.Add(field.ZAxis.Count+1)

    for i, j, k in zip(range(new_shape[0]), range(new_shape[1]), range(new_shape[2])):
        field[i, j, k] = resized_array[i, j, k]

    return field
