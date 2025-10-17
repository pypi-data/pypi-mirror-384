from typing import Any
import numpy as np
import pandas as pd
import inspect
import enum

from .utils import (SimComponent, SimDoubleParameter, SimIntegerParameter, SimStringParameter,
                    SimBoolParameter, SimEnumParameter, SimMultiValueField3D, SimMultiValueBigTable, FileInfo, DirectoryInfo,
                    set_property_to_sim_component, set_property_to_parameter, set_property_to_value_field,
                    set_property_to_file_info, set_property_to_list, set_property_to_dict, set_property_to_directory_info)

from .simultan_object import SimultanObject, MetaMock

from .default_types import ComponentList, ComponentDictionary
from .multi_values import SimultanPandasDataFrame

from SIMULTAN.Data.Components import (ComponentWalker, SimComponent, SimBoolParameter, SimDoubleParameter,
                                      SimEnumParameter, SimIntegerParameter, SimStringParameter, ComponentMapping,
                                      SimSlot, SimComponentVisibility, SimChildComponentEntry, SimDefaultSlots,
                                      SimParameterOperations, SimComponentReference)


class TypeSetterFcnLookupDict(object):
    lookup_dict = {None: lambda x: None,
                   SimComponent: set_property_to_sim_component,
                   SimultanObject: set_property_to_sim_component,
                   SimDoubleParameter: set_property_to_parameter,
                   SimIntegerParameter: set_property_to_parameter,
                   SimStringParameter: set_property_to_parameter,
                   SimBoolParameter: set_property_to_parameter,
                   SimEnumParameter: set_property_to_parameter,
                   SimMultiValueField3D: set_property_to_value_field,
                   SimMultiValueBigTable: set_property_to_value_field,
                   int: set_property_to_parameter,
                   np.int32: set_property_to_parameter,
                   np.int64: set_property_to_parameter,
                   float: set_property_to_parameter,
                   np.float32: set_property_to_parameter,
                   np.float64: set_property_to_parameter,
                   str: set_property_to_parameter,
                   bool: set_property_to_parameter,
                   FileInfo: set_property_to_file_info,
                   DirectoryInfo: set_property_to_directory_info,
                   list: set_property_to_list,
                   tuple: set_property_to_list,
                   set: set_property_to_list,
                   dict: set_property_to_dict,
                   enum.Enum: set_property_to_parameter,
                   enum.IntEnum: set_property_to_parameter,
                   enum.EnumType: set_property_to_parameter,
                   ComponentDictionary: set_property_to_sim_component,
                   ComponentList: set_property_to_list,
                   np.ndarray: set_property_to_value_field,
                   pd.DataFrame: set_property_to_value_field,
                   SimultanPandasDataFrame: set_property_to_value_field}

    def __getitem__(self, item: type):
        bases = [item, *inspect.getmro(type(item))]

        if SimultanObject in bases or MetaMock in bases:
            return set_property_to_sim_component
        else:
            for base in bases:
                if base in self.lookup_dict:
                    return self.lookup_dict[base]
        return None

    def get(self,
            item: Any,
            default='_____'):

        val = self.__getitem__(type(item))
        if val is None:
            if default == '_____':
                raise KeyError(f'No setter function found for type {type(item)}')
            return default
        else:
            return val


type_setter_fcn_lookup_dict = TypeSetterFcnLookupDict()
