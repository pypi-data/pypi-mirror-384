from __future__ import annotations

import sys
import traceback
import functools
import numpy as np
import pandas as pd

from enum import Enum
from weakref import WeakSet
from typing import List as TypeList, Union, Optional, Type, Any, TYPE_CHECKING
from SIMULTAN.Data import SimId

from System import ArgumentException, NotSupportedException

from SIMULTAN.Data.Components import (ComponentWalker, SimComponent, SimBoolParameter, SimDoubleParameter,
                                      SimEnumParameter, SimIntegerParameter, SimStringParameter, ComponentMapping,
                                      SimSlot, SimComponentVisibility, SimChildComponentEntry, SimDefaultSlots,
                                      SimParameterOperations, SimComponentReference)
from SIMULTAN.Data.Taxonomy import SimTaxonomyEntry, SimTaxonomyEntryReference, SimTaxonomy
from SIMULTAN.Data.Components import SimDefaultSlotKeys
from SIMULTAN.Data.MultiValues import (SimMultiValueField3D, SimMultiValueField3DParameterSource, SimMultiValueBigTable,
                                       SimMultiValueBigTableHeader, SimMultiValueBigTableParameterSource)

from SIMULTAN.Data.Assets import (ResourceEntry, ResourceFileEntry, ContainedResourceFileEntry, Asset,
                                  LinkedResourceFileEntry, ResourceDirectoryEntry, DocumentAsset)
from SIMULTAN.Data.Geometry import Face, Edge, Vertex, Volume

from .multi_values import (simultan_multi_value_field_3d_to_numpy, set_parameter_to_value_field,
                           create_field_parameter, simultan_multi_value_big_table_to_pandas, SimultanPandasDataFrame)
from .files import FileInfo, remove_asset_from_component, add_asset_to_component, DirectoryInfo

if TYPE_CHECKING:
    from .default_types import ComponentList, ComponentDictionary
    from .simultan_object import SimultanObject
    from .data_model import DataModel
    from .object_mapper import PythonMapper
    from .taxonomy_maps import TaxonomyMap, Content


from . import logger
from . import config
from .simultan_object import SimultanObject


class UnresolvedObject(object):

    def __init__(self, wrapped_obj, cls, *args, **kwargs):
        self.wrapped_obj = wrapped_obj
        self.cls = cls

    def resolve(self):
        return self.cls._cls_instances_dict[self.wrapped_obj.Id]

    def __getattr__(self, item):
        return getattr(self.wrapped_obj, item)


class CircularReferenceResolver(object):

    def __init__(self, *args, **kwargs):
        self.unresolved_objects = dict()


circ_ref_resolver = CircularReferenceResolver()


def create_python_object(wrapped_obj: SimComponent,
                         cls: Type[SimultanObject],
                         *args,
                         **kwargs):
    """
    Create a new mapped python object from a wrapped object
    :param wrapped_obj: wrapped object to create the python object from
    :param cls: class of the python object
    :param args: additional arguments
    :param kwargs: additional keyword arguments
        :param data_model: DataModel
        :param object_mapper: PythonMapper

    :return: SimultanObject
    :return:
    """

    from .default_types import ComponentList, ComponentDictionary

    data_model = kwargs.get('data_model', None)

    if data_model is None:
        data_model = config.get_default_data_model()

    if wrapped_obj is None:
        return None
    else:

        if wrapped_obj.Id in circ_ref_resolver.unresolved_objects.keys():
            return circ_ref_resolver.unresolved_objects[wrapped_obj.Id]
        else:
            circ_ref_resolver.unresolved_objects[wrapped_obj.Id] = UnresolvedObject(wrapped_obj,
                                                                                    cls,
                                                                                    *args, **kwargs)

        # get existing object
        if wrapped_obj.Id in cls._cls_instances_dict.keys():
            return cls._cls_instances_dict[wrapped_obj.Id]

        if cls._taxonomy_map is not None:
            for content in cls._taxonomy_map.content:
                # logger.debug(f'Get property {content.text_or_key} from wrapped object {wrapped_obj.Name}')
                kwargs[content.text_or_key] = get_property(wrapped_obj=wrapped_obj,
                                                           text_or_key=content.text_or_key,
                                                           object_mapper=kwargs.get('object_mapper', None),
                                                           data_model=data_model
                                                           )

        kwargs['name'] = wrapped_obj.Name
        kwargs['__obj_init__'] = True

        obj = cls.__new__(cls)
        obj.__obj_init__ = True
        obj.__property_cache__ = dict()
        obj._wrapped_obj = wrapped_obj
        obj._data_model = data_model
        obj._object_mapper = kwargs.get('object_mapper', None)
        obj.component_policy = kwargs.get('component_policy', 'subcomponent')

        if isinstance(obj, ComponentList):
            obj.index = kwargs.get('index', 0)
        if isinstance(obj, ComponentDictionary):
            obj._dict = {}

        if "_cls_instances" not in cls.__dict__:
            cls._cls_instances = WeakSet()
        try:
            cls._cls_instances.add(obj)
        except Exception as e:
            logger.error(f'Error adding instance {obj} to _cls_instances: {e}')

        if hasattr(cls, '__load_init__'):
            obj.__load_init__(*args, **kwargs)
        #
        circ_ref_resolver.unresolved_objects.pop(wrapped_obj.Id)

        return obj


def create_taxonomy(name, key, description='', data_model=None) -> SimTaxonomy:
    """
    Create a new taxonomy
    :param name: name of the taxonomy
    :param key: key of the taxonomy
    :param description: description of the taxonomy
    :param data_model: data model; if not None, the taxonomy will be added to the data model
    :return: SimTaxonomy
    """
    new_taxonomy = SimTaxonomy(key, name, description, None)
    if data_model is not None:
        data_model.taxonomies.Add(new_taxonomy)
    return new_taxonomy


def get_or_create_taxonomy_entry(name: str,
                                 key: str,
                                 description='',
                                 sim_taxonomy: Optional[SimTaxonomy] = None,
                                 data_model: Optional[DataModel] = None,
                                 create=True) -> SimTaxonomyEntry:
    """
    Create a new taxonomy entry
    :param name: name of the taxonomy entry
    :param key: key of the taxonomy entry
    :param description: description of the taxonomy entry
    :param sim_taxonomy: sim taxonomy; if not None, the taxonomy entry will be added to the sim taxonomy
    :param data_model: data model; if not None, the taxonomy entry will be added to the data model
    :param create: if True, the taxonomy entry will be created if it does not exist
    :return: SimTaxonomyEntry
    """

    if data_model is not None:
        taxonomy_entries = data_model.get_taxonomy_entries()

        if key in taxonomy_entries.keys():
            return taxonomy_entries[key]
    if create:
        new_sim_taxonomy_entry = SimTaxonomyEntry(key, name, description, None)
        if sim_taxonomy is not None:
            sim_taxonomy.Entries.Add(new_sim_taxonomy_entry)
        return new_sim_taxonomy_entry


def create_str_sim_slot(slot_name: str,
                        slot_extension: Union[str, int, float],
                        data_model: DataModel = None):
    return SimSlot(SimTaxonomyEntry(slot_name), str(slot_extension))


def create_component(name: Union[str, None] = None,
                     data_model: Union[DataModel, None] = None,
                     **kwargs) -> SimComponent:
    """
    Create a new Simultan component
    :param data_model: DataModel
    :param name: Name of the component; string
    :param kwargs: dictionary; set the components value of the key entry to to key value; Example: {'Visibility': 0,
    'IsAutomaticallyGenerated': True}
    :return: SimComponent
    """
    new_comp = SimComponent()

    slot = kwargs.get('slot', None)

    if name is not None:
        new_comp.Name = name

    # set the components value of the key entry to key value
    for key, value in kwargs.items():
        if key == 'Visibility':
            if value:
                new_comp.Visibility = SimComponentVisibility.AlwaysVisible
            else:
                new_comp.Visibility = SimComponentVisibility.Hidden
        else:
            setattr(new_comp, key, value)

    if slot is None:
        slot = SimTaxonomyEntryReference(SimDefaultSlotKeys.GetDefaultSlot(data_model.project_data_manager.Taxonomies,
                                                                           SimDefaultSlotKeys.Undefined))
    elif isinstance(slot, SimTaxonomyEntry):
        slot = SimTaxonomyEntryReference(slot)

    elif isinstance(slot, SimTaxonomyEntryReference):
        pass

    new_comp.Slots.InsertItem(0, slot)

    return new_comp


def get_default_slot(default_type: Union[SimTaxonomyEntryReference, SimTaxonomyEntry, str]) -> SimTaxonomyEntryReference:
    """
    Get the default slot of the project
    :param default_type:
    :return:
    """

    default_taxonomy_entry = SimDefaultSlotKeys.GetDefaultSlot(config.get_default_data_model().project_data_manager.Taxonomies,
                                                               SimDefaultSlotKeys.Undefined)

    if default_type is SimTaxonomyEntryReference:
        return SimTaxonomyEntryReference(default_taxonomy_entry)
    elif default_type is SimTaxonomyEntry:
        return default_taxonomy_entry


def create_sim_double_parameter(**kwargs) -> SimDoubleParameter:
    """
    Creates a new SIMULTAN double parameter
    :param name:    Name of the parameter
    :param unit:    Unit of the parameter
    :param value:   Value of the parameter
    :param slot:    SimTaxonomyEntry or SimTaxonomyEntryReference
    :param min_value:   If None, the value is not limited
    :param max_value:   If None, the value is not limited
    :param allowed_operations:  SimParameterOperations
    :return: SimDoubleParameter
    """

    init_dict = ['slot', 'unit', 'value', 'min_value', 'ValueMin', 'max_value', 'ValueMax', 'allowed_operations']

    args = [x for x in [kwargs.get(key, None) for key in init_dict] if x is not None]

    if 'allowed_operations' not in kwargs.keys():
        args.append(SimParameterOperations(0).All)

    return SimDoubleParameter(*args)


def create_sim_integer_parameter(**kwargs) -> SimIntegerParameter:
    """
    Creates a new SIMULTAN integer parameter
    :param name:    Name of the parameter
    :param unit:    Unit of the parameter
    :param value:   Value of the parameter
    :param slot:    SimTaxonomyEntry or SimTaxonomyEntryReference
    :param min_value:   If None, the value is not limited
    :param max_value:   If None, the value is not limited
    :param allowed_operations:  SimParameterOperations
    :return:
    """

    kwargs['value'] = int(kwargs['value'])
    init_dict = ['slot', 'unit', 'value', 'min_value', 'max_value', 'allowed_operations']

    args = [x for x in [kwargs.get(key, None) for key in init_dict] if x is not None]
    args.append(SimParameterOperations(0).All)

    return SimIntegerParameter(*args)


def create_sim_string_parameter(**kwargs) -> SimStringParameter:
    """
    Creates a new SIMULTAN string parameter
    :param name:    Name of the parameter
    :param value:   Value of the parameter
    :param slot:    SimTaxonomyEntry or SimTaxonomyEntryReference
    :param allowed_operations:  SimParameterOperations
    :return:
    """

    try:
        init_dict = ['slot', 'value']

        args = [x for x in [kwargs.get(key, None) for key in init_dict] if x is not None]
        args.append(SimParameterOperations(0).All)

        return SimStringParameter(*args)
    except Exception as e:
        logger.error(f'Error creating string parameter: {e}\n{traceback.format_exc()}')
        raise e


def create_sim_bool_parameter(**kwargs) -> SimBoolParameter:
    """
    Creates a new SIMULTAN bool parameter
    :param name:    Name of the parameter
    :param value:   Value of the parameter
    :param slot:    SimTaxonomyEntry or SimTaxonomyEntryReference
    :param allowed_operations:  SimParameterOperations
    :return:
    """

    init_dict = ['slot', 'value']

    args = [x for x in [kwargs.get(key, None) for key in init_dict] if x is not None]
    args.append(SimParameterOperations(0).All)

    return SimBoolParameter(*args)


def create_parameter(value: Union[int, float, str, SimTaxonomyEntry] = 0,
                     name: str = None,
                     parameter_type: Union[int, float, str, Enum] = None,
                     taxonomy_entry: SimTaxonomyEntry = None,
                     **kwargs) -> Union[SimDoubleParameter, SimIntegerParameter, SimStringParameter, SimEnumParameter]:
    """
    Creates a new SIMULTAN parameter

    - either parameter_type or value must be set, if parameter_type is not set, parameter_type
      is set automatically by the type of value
    - if name and taxonomy_entry_or_string is not set, the default slot is used.
    - If name is set, the slot is taxonomy_entry_or_string -> string
    - if taxonomy_entry_or_string is set, the slot is taxonomy_entry_or_string -> SimTaxonomyEntryReference

    :param name: Parameter name, string
    :param value: Value of the parameter; int or float
    :param parameter_type: Parameter type, int, float, string or enum
    :param taxonomy_entry: Taxonomy entry or string
    :return: SimParameter
    """

    if taxonomy_entry is None and name is None:
        taxonomy_entry = get_default_slot(SimTaxonomyEntry)

    if parameter_type is None:
        if type(value) in (float, np.float64, np.float32):
            parameter_type = float
        elif type(value) in (int, np.int64, np.int32):
            parameter_type = int
        elif type(value) is str:
            parameter_type = str
        elif type(value) is SimTaxonomyEntry:
            parameter_type = Enum
        elif type(value) is bool:
            parameter_type = bool
        else:
            raise ValueError(f'Parameter type {type(value)} not supported.')

    if parameter_type == float:
        if isinstance(value, (str, int)):
            value = float(value)

        return create_sim_double_parameter(name=name,
                                           value=value,
                                           slot=taxonomy_entry,
                                           unit=kwargs.pop('unit', ''),
                                           **kwargs)
    elif parameter_type == int:
        if isinstance(value, (str, float)):
            value = int(value)

        return create_sim_integer_parameter(name=name,
                                            value=value,
                                            slot=taxonomy_entry,
                                            unit=kwargs.pop('unit', ''),
                                            **kwargs)
    elif parameter_type == str:
        if isinstance(value, (int, float)):
            value = str(value)

        return create_sim_string_parameter(name=name,
                                           value=value,
                                           slot=taxonomy_entry,
                                           **kwargs)
    elif parameter_type == bool:
        return create_sim_bool_parameter(name=name,
                                         value=value,
                                         slot=taxonomy_entry,
                                         **kwargs)
    elif parameter_type == SimTaxonomyEntry:
        raise NotImplementedError('Parameter for Enum not implemented yet.')
    else:
        raise ValueError(f'Parameter type {parameter_type} not supported.')


def add_sub_component(comp: SimComponent,
                      sub_comp: SimComponent,
                      slot_extension: Union[str, int, float],
                      slot: Union[str, SimTaxonomyEntry, SimTaxonomyEntryReference] = None):
    """
    Add a sub component to a component.

    :param comp: Component to add the subcomponent; ParameterStructure.Components.SimComponent
    :param sub_comp: Component to be added; ParameterStructure.Components.SimComponent
    :param slot: Target slot name or taxonomie of the subcomponent; If string, a new slot is created with the string as
    target;
    :param slot_extension: Target slot extension of the subcomponent;
    """

    if slot is not None:
        if isinstance(slot, str):
            slot = SimTaxonomyEntry(slot)
            slot = create_str_sim_slot(slot, slot_extension)
        elif isinstance(slot, SimTaxonomyEntry):
            slot = SimTaxonomyEntryReference(slot)
        if slot not in sub_comp.Slots:
            sub_comp.Slots.InsertItem(0, slot)

    if slot_extension is None:
        new_slot = comp.Components.FindAvailableSlot(slot.Target if isinstance(slot,
                                                                               SimTaxonomyEntryReference)
                                                     else slot, "{0}")
    else:
        new_slot = SimSlot(sub_comp.Slots[0].Target, str(slot_extension))

    entry = SimChildComponentEntry(new_slot, sub_comp)

    error = None
    new_slot_extension = 0

    if entry not in comp.Components.Items:
        try:
            comp.Components.InsertItem(len(comp.Components.Items), entry)
        except (ArgumentException, NotSupportedException) as e:
            error = e

            while error is not None and new_slot_extension < 100:
                try:
                    try:
                        slot_extension += 1
                        if slot_extension > 1000:
                            break
                    except Exception as e:
                        new_slot_extension += 1
                        slot_extension = slot_extension + f'_{new_slot_extension}'
                    new_slot = SimSlot(sub_comp.Slots[0].Target, str(slot_extension))
                    entry = SimChildComponentEntry(new_slot, sub_comp)
                    comp.Components.InsertItem(len(comp.Components.Items), entry)
                    error = None
                except (ArgumentException, NotSupportedException) as e:
                    error = e
            raise error
    return True


# def add_asset_to_component(comp: SimComponent,
#                            asset: Union[ResourceFileEntry, ContainedResourceFileEntry],
#                            content_id: str = '') -> Asset:
#     """
#     Add an asset to a component
#     :param comp: Component to add the asset; ParameterStructure.Components.SimComponent
#     :param asset: Asset to be added; ParameterStructure.Assets.ResourceFileEntry
#     :param content_id: Content id of the asset; string; E.g. '0' as the page of a pdf
#     :return:
#     """
#     return ComponentMapping.AddAsset(comp, asset, content_id)


def remove_sub_component(comp: Union[SimComponent, SimultanObject],
                         sub_comp: Union[SimComponent, SimultanObject],
                         index: int = None):
    """
    Remove a sub component from a component.
    :param comp: Component to remove the subcomponent; ParameterStructure.Components.SimComponent
    :type comp: Union[SimComponent, SimultanObject]
    :param sub_comp: Component to be removed; ParameterStructure.Components.SimComponent
    :type sub_comp: Union[SimComponent, SimultanObject]
    :param index: Index of the subcomponent to be removed; int
    """

    sub_comp_wrapped_obj = sub_comp if isinstance(sub_comp, SimComponent) else sub_comp._wrapped_obj
    component_wrapped_obj = comp if isinstance(comp, SimComponent) else comp._wrapped_obj

    if index is not None:
        component_wrapped_obj.Components.RemoveAt(index)
        # sub_comp.Id = SimId.Empty
        return

    for i, sub_comp_entry in enumerate(component_wrapped_obj.Components.Items):
        if sub_comp_entry.Component == sub_comp_wrapped_obj:
            component_wrapped_obj.Components.RemoveAt(i)
            # sub_comp.Id = SimId.Empty
            return

def create_resource_reference(component: Union[SimComponent, SimultanObject],
                              resource: ContainedResourceFileEntry) -> Asset:
    """
    Add a reference to a resource file to a component
    :param component: Component to which to add the resource reference, Union[SimComponent, SimultanObject]
    :type component: Union[SimComponent, SimultanObject]
    :param resource: ParameterStructure.Assets.ContainedResourceFileEntry
    :type resource: ContainedResourceFileEntry
    :return: Created asset
    :rtype: Asset
    """
    component_wrapped_obj = component if isinstance(component, SimComponent) else component._wrapped_obj
    return ComponentMapping.AddAsset(component_wrapped_obj, resource, '')


def add_referenced_component(component: Union[SimComponent, SimultanObject],
                             referenced_component: Union[SimComponent, SimultanObject],
                             slot_extension: Union[str, int, float],
                             slot: SimTaxonomyEntry = None):
    """
    Add a reference to a component to a component
    :param component: ParameterStructure.Components.SimComponent
    :param referenced_component: ParameterStructure.Components.SimComponent
    :param slot_extension: SLot extension of the referenced component
    :param slot: ParameterStructure.Slots.SimSlot
    :return:
    """

    referenced_wrapped_obj = referenced_component if isinstance(referenced_component,
                                                                SimComponent) else referenced_component._wrapped_obj

    component_wrapped_obj = component if isinstance(component, SimComponent) else component._wrapped_obj

    if slot is None:
        slot = referenced_wrapped_obj.Slots[0].Target

    if isinstance(slot, SimTaxonomyEntry):
        if slot not in [x.Target for x in referenced_wrapped_obj.Slots.Items]:
            index = referenced_wrapped_obj.Slots.Items.__len__()
            referenced_wrapped_obj.Slots.InsertItem(index, SimTaxonomyEntryReference(slot))
    elif isinstance(slot, SimTaxonomyEntryReference):
        if slot.Target not in [x.Target for x in referenced_wrapped_obj.Slots.Items]:
            index = referenced_wrapped_obj.Slots.Items.__len__()
            referenced_wrapped_obj.Slots.InsertItem(index, slot.SlotBase)

    if isinstance(slot, SimTaxonomyEntryReference):
        slot = slot.Target

    if slot_extension is None:
        new_slot = component_wrapped_obj.Components.FindAvailableSlot(slot, "{0}")
    else:
        new_slot = SimSlot(slot, str(slot_extension))

    if isinstance(referenced_component, SimComponent):
        ref = SimComponentReference(new_slot, referenced_wrapped_obj)
    else:
        ref = SimComponentReference(new_slot, referenced_wrapped_obj._wrapped_obj)
    component_wrapped_obj.ReferencedComponents.Add(ref)

    return


def remove_referenced_component(component: Union[SimComponent, SimultanObject],
                                referenced_component: Union[SimComponent, SimultanObject]):
    """
    Remove a reference to a component from a component
    :param component: ParameterStructure.Components.SimComponent
    :param referenced_component: ParameterStructure.Components.SimComponent
    :return:
    """

    referenced_wrapped_obj = referenced_component if isinstance(referenced_component,
                                                                SimComponent) else referenced_component._wrapped_obj

    component_wrapped_obj = component if isinstance(component, SimComponent) else component._wrapped_obj

    for i, ref_comp in enumerate(component.ReferencedComponents.Items):
        if ref_comp.Target == referenced_wrapped_obj:
            component_wrapped_obj.ReferencedComponents.RemoveAt(i)
            return




def find_components_with_taxonomy(component_list: list[SimComponent], key, first=False) -> set[SimComponent]:

    components = set()

    for component in component_list:

        try:
            for slot_item in component.Slots.Items:
                if slot_item.Target.Key == key:
                    if first:
                        return component
                    components.add(component)

            components.update(find_components_with_taxonomy([x.Component for x in component.Components], key, first))
        except Exception as e:
            print(e)

    return components


def get_component_geometry(data_model, geometry_model, component) -> tuple[list[Vertex], list[Edge], list[Face], list[Volume]]:
    """
    Get the fc_geometry of a component from a fc_geometry model
    :param data_model:
    :param geometry_model:
    :param component:
    :return:
    """

    points = list()
    pot_points = geometry_model.Geometry.Vertices
    for point in pot_points:
        if component in list(data_model.exch.GetComponents(point)):
            points.append(point)

    edges = list()
    pot_edges = geometry_model.Geometry.Edges
    for edge in pot_edges:
        if component in list(data_model.exch.GetComponents(edge)):
            edges.append(edge)

    faces = list()
    pot_faces = geometry_model.Geometry.Faces
    for face in pot_faces:
        if component in list(data_model.exch.GetComponents(face)):
            faces.append(face)

    volumes = list()
    pot_volumes = geometry_model.Geometry.Volumes
    for volume in pot_volumes:
        if component in list(data_model.exch.GetComponents(volume)):
            volumes.append(volume)

    return points, edges, faces, volumes


def create_simultan_component_for_taxonomy(cls: Type[SimultanObject],
                                           *args,
                                           **kwargs) -> SimComponent:
    """
    Create a new Simultan component for a taxonomy
    :param cls:
    :param args:
    :param kwargs: add_to_data_model: if True, the component is added to the data model
    :return:
    """

    data_model = kwargs.get('data_model', None)
    if data_model is None:
        data_model = config.get_default_data_model()

    # simultan_taxonomy = cls._taxonomy_map.get_or_create_simultan_taxonomy(data_model=data_model)
    # tayonomy_entry = cls._taxonomy_map.get_or_create_simultan_taxonomy_entry(data_model=data_model)
    slot = cls._taxonomy_map.get_slot(data_model=data_model)

    new_component = create_component(data_model=data_model,
                                     slot=slot)

    add_to_data_model = kwargs.get('add_to_data_model', True)

    if add_to_data_model:
        data_model.add_component(new_component)

    return new_component


def get_component_taxonomy_entry(component, taxonomy: str):

    obj = None

    # search in subcomponents
    for sub_comp in component.Components:
        if sub_comp.Slot.get_SlotBase().Target.Key == taxonomy:
            return sub_comp.Component

    # search in referenced components
    for comp in component.ReferencedComponents:
        if comp.Slot.SlotBase.Target.Key == taxonomy:
            return comp.Target

    # search in parameters
    for param in component.Parameters:
        if param.NameTaxonomyEntry.TextOrKey == taxonomy:
            return param

    for referenced_asset in component.ReferencedAssets:
        if referenced_asset.Resource is None:
            return None
        resource_taxonomy_keys = [x.Target.Key for x in referenced_asset.Resource.Tags]
        if taxonomy in resource_taxonomy_keys:
            return referenced_asset.Resource


    if obj is None:
        return None


def sort_slots(slots, check_same_slot=False) -> list[SimSlot]:

    if slots.__len__() == 0:
        return slots

    if check_same_slot:
        if not all(slots[0].SlotBase == x.SlotBase for x in slots):
            raise TypeError(f'List elements do not have same slot')

    slot_extensions = [x.SlotExtension for x in slots]
    return slot_extensions


def get_property(prop_name: Optional[str] = None,
                 text_or_key: Optional[str] = None,
                 component=None,
                 wrapped_obj=None,
                 object_mapper=None,
                 data_model=None) -> Any:

    if prop_name is None and text_or_key is None:
        raise ValueError('Either prop_name or text_or_key must be set.')
    if prop_name is not None:
        content = component._taxonomy_map.get_content_by_property_name(prop_name)
        text_or_key = content.text_or_key

    if component is not None:
        obj = get_component_taxonomy_entry(component._wrapped_obj, text_or_key)
        if data_model is None:
            data_model = component._data_model
        object_mapper = component._object_mapper
    else:
        if data_model is None:
            data_model = config.get_default_data_model()
        obj = get_component_taxonomy_entry(wrapped_obj,
                                           text_or_key)

    return get_obj_value(obj, data_model=data_model, object_mapper=object_mapper)


def get_parameter_value(obj, data_model=None, object_mapper=None):
    return obj.Value


def get_sim_component_value(obj: SimComponent,
                            object_mapper: PythonMapper,
                            data_model: DataModel) -> SimComponent:
    return object_mapper.create_python_object(obj, data_model=data_model)


def get_sim_double_parameter_value(obj: SimDoubleParameter,
                                   *args,
                                   **kwargs) -> Union[int, float, pd.DataFrame, np.ndarray]:
    if obj.ValueSource is not None:
        if isinstance(obj.ValueSource, SimMultiValueField3DParameterSource):
            return simultan_multi_value_field_3d_to_numpy(obj.ValueSource.Field)
        elif isinstance(obj.ValueSource, SimMultiValueBigTableParameterSource):
            return simultan_multi_value_big_table_to_pandas(obj.ValueSource.Table)
        else:
            raise ValueError(f'Value source {obj.ValueSource} not supported.')
    return obj.Value


def get_resource_entry_value(obj: ResourceEntry,
                             data_model: DataModel = None,
                             object_mapper: PythonMapper = None) -> Union[FileInfo, DirectoryInfo]:
    if isinstance(obj, (ResourceFileEntry, ContainedResourceFileEntry, LinkedResourceFileEntry)):

        if obj.Name == '__dir_helper_file__':
            return DirectoryInfo(file_path=obj.Parent.CurrentFullPath,
                                 resource_entry=obj.Parent,
                                 helper_file=obj,
                                 data_model=data_model)

        return FileInfo(file_path=obj.File.FullPath,
                        resource_entry=obj,
                        data_model=data_model)
    elif isinstance(obj, ResourceDirectoryEntry):
        return DirectoryInfo(file_path=obj.CurrentFullPath,
                             resource_entry=obj,
                             data_model=data_model)


type_convert_dict = {SimComponent: get_sim_component_value,
                     SimDoubleParameter: get_sim_double_parameter_value,
                     SimIntegerParameter: get_parameter_value,
                     SimStringParameter: get_parameter_value,
                     SimBoolParameter: get_parameter_value,
                     SimEnumParameter: get_parameter_value,
                     ResourceEntry: get_resource_entry_value,
                     ResourceFileEntry: get_resource_entry_value,
                     ResourceDirectoryEntry: get_resource_entry_value,
                     ContainedResourceFileEntry: get_resource_entry_value,
                     LinkedResourceFileEntry: get_resource_entry_value
                     }


def get_obj_value(obj: Union[SimComponent, SimDoubleParameter, SimIntegerParameter, SimStringParameter,
                             SimBoolParameter, SimEnumParameter, ResourceEntry, ResourceFileEntry, ContainedResourceFileEntry,
                             ResourceDirectoryEntry, None],
                  data_model: DataModel,
                  object_mapper: PythonMapper) -> Union[SimultanObject, int, float, str, FileInfo, None, pd.DataFrame,
                                                        np.ndarray]:

    if obj is None:
        return
    elif isinstance(obj, SimultanObject):
        return obj
    elif isinstance(obj, (int, float, str)):
        return obj
    elif type(obj) in type_convert_dict.keys():
        return type_convert_dict[type(obj)](obj, data_model=data_model, object_mapper=object_mapper)
    else:
        logger.warning(f'Object type {type(obj)} not supported.')
        return obj

    #
    # if obj is None:
    #     return None
    # elif isinstance(obj, SimComponent):
    #     return object_mapper.create_python_object(obj, data_model=data_model)
    # elif isinstance(obj, SimDoubleParameter):
    #     if obj.ValueSource is not None:
    #         if isinstance(obj.ValueSource, SimMultiValueField3DParameterSource):
    #             return simultan_multi_value_field_3d_to_numpy(obj.ValueSource.Field)
    #         elif isinstance(obj.ValueSource, SimMultiValueBigTableParameterSource):
    #             return simultan_multi_value_big_table_to_pandas(obj.ValueSource.Table)
    #         else:
    #             raise ValueError(f'Value source {obj.ValueSource} not supported.')
    #     return obj.Value
    # elif isinstance(obj, SimIntegerParameter):
    #     return obj.Value
    # elif isinstance(obj, SimStringParameter):
    #     return obj.Value
    # elif isinstance(obj, SimBoolParameter):
    #     return obj.Value
    # elif isinstance(obj, SimEnumParameter):
    #     return obj.Value
    # elif isinstance(obj, ResourceEntry):
    #     return FileInfo(file_path=obj.File.FullPath,
    #                     resource_entry=obj,
    #                     data_model=data_model)
    # else:
    #     return obj


def get_param_indices(wrapped_obj: SimComponent,
                      taxonomy_entry: SimTaxonomyEntry) -> tuple[int, int, int, int]:
    """
    Get the indices of a taxonomy entry in a component
    :param wrapped_obj:
    :param taxonomy_entry:
    :return: Index of the component, index of the referenced component, index of the parameter,
    index of the referenced asset
    """

    parameter_idx = next((i for i, x in enumerate(wrapped_obj.Parameters.Items) if
                          x.NameTaxonomyEntry.TextOrKey == taxonomy_entry.Key), None)

    component_idx = next((i for i, x in enumerate(wrapped_obj.Components.Items) if
                          x.Slot.SlotBase.Target.Key == taxonomy_entry.Key), None)

    ref_component_idx = next((i for i, x in enumerate(wrapped_obj.ReferencedComponents.Items) if
                              x.Slot.SlotBase.Target.Key == taxonomy_entry.Key), None)

    ref_asset_idx = next((i for i, x in enumerate(wrapped_obj.ReferencedAssets.Items) if taxonomy_entry.Key in
                          [y.Target.Key for y in x.Resource.Tags]), None)

    return component_idx, ref_component_idx, parameter_idx, ref_asset_idx


def create_component_list(values,
                          name=None,
                          data_model: Union[DataModel, None] = None,
                          additional_slots: Union[TypeList[SimSlot], TypeList[SimTaxonomyEntryReference]] = None,
                          object_mapper: Union[PythonMapper, None] = None,
                          add_to_data_model: bool = True) -> ComponentList:
    """
    Create a new component list
    :param values: values of the component list
    :param name: name of the component list
    :param data_model: data model to use
    :param additional_slots: additional slots to use
    :param object_mapper: object mapper to use
    :param add_to_data_model: if True, the component list is added to the data model
    :return: ComponentList
    """
    from .default_types import ComponentList

    new_component_list = ComponentList.create_from_values(data_model=data_model,
                                                          values=values,
                                                          object_mapper=object_mapper,
                                                          add_to_data_model=add_to_data_model)
    new_component_list._wrapped_obj.Name = name

    if additional_slots is not None:
        for i, slot in enumerate(additional_slots):
            if isinstance(slot, SimTaxonomyEntryReference):
                new_component_list.add_taxonomy_entry_reference(slot, index=i)
            elif isinstance(slot, SimSlot):
                new_component_list.add_taxonomy_entry_reference(slot.SlotBase, index=i)
            elif isinstance(slot, SimTaxonomyEntry):
                new_component_list.add_taxonomy_entry_reference(SimTaxonomyEntryReference(slot), index=i)

    return new_component_list


def create_component_dict(values,
                          name=None,
                          data_model: Union[DataModel, None] = None,
                          additional_slots: Union[TypeList[SimSlot], TypeList[SimTaxonomyEntryReference]] = None,
                          object_mapper: Union[PythonMapper, None] = None,
                          add_to_data_model: bool = True):
    from .default_types import ComponentDictionary
    new_component_dict = ComponentDictionary.create_from_values(data_model=data_model,
                                                                values=values,
                                                                object_mapper=object_mapper,
                                                                add_to_data_model=add_to_data_model)
    new_component_dict._wrapped_obj.Name = name

    if additional_slots is not None:
        for i, slot in enumerate(additional_slots):
            if isinstance(slot, SimTaxonomyEntryReference):
                new_component_dict.add_taxonomy_entry_reference(slot, index=i)
            elif isinstance(slot, SimSlot):
                new_component_dict.add_taxonomy_entry_reference(slot.SlotBase, index=i)
            elif isinstance(slot, SimTaxonomyEntry):
                new_component_dict.add_taxonomy_entry_reference(SimTaxonomyEntryReference(slot), index=i)

    return new_component_dict


param_type_lookup_dict = {str: SimStringParameter,
                          int: SimIntegerParameter,
                          float: SimDoubleParameter,
                          bool: SimBoolParameter}


def create_mapped_python_object(value: Any,
                                object_mapper: PythonMapper,
                                data_model: DataModel,
                                add_to_data_model=True) -> SimultanObject:
    """
    Create a mapped python object from a python object and add it to the data model or as subcomponent to a parent
    :param value: python object to map
    :param object_mapper: object mapper to use
    :param data_model: data model to use
    :param add_to_data_model: if True, the object is added to the data model
    :return: mapped python object
    """

    if object_mapper is None:
        object_mapper = config.get_default_mapper()

    # logger.debug(f'Creating mapped python object for {value}.')
    if type(value) in object_mapper.registered_classes.values():
        key = list(filter(lambda x: object_mapper.registered_classes[x] == type(value),
                          object_mapper.registered_classes)
                   )[0]
        mapped_cls = object_mapper.get_mapped_class(key)
        new_val = mapped_cls(**value.__dict__,
                             data_model=data_model,
                             object_mapper=object_mapper,
                             add_to_data_model=add_to_data_model)
        # logger.debug(f'Created mapped python object {new_val} for {value}.')
        return new_val
    elif isinstance(value, dict):
        from .default_types import ComponentDictionary
        new_val = ComponentDictionary.create_from_values(data_model=data_model,
                                                         values=value,
                                                         object_mapper=object_mapper,
                                                         add_to_data_model=add_to_data_model)
        return new_val
    elif isinstance(value, (list, set, tuple)):
        from .default_types import ComponentList
        new_val = ComponentList.create_from_values(data_model=data_model,
                                                   values=value,
                                                   object_mapper=object_mapper,
                                                   add_to_data_model=add_to_data_model)
        return new_val
    elif isinstance(value, UnresolvedObject):
        return value.resolve()
    else:
        sub_classes = [issubclass(x, value.__class__) for x in object_mapper.registered_classes.values()]
        if sum(sub_classes) == 1:
            key = list(object_mapper.registered_classes.keys())[sub_classes.index(True)]
            mapped_cls = object_mapper.get_mapped_class(key)
            new_val = mapped_cls(**value.__dict__,
                                 data_model=data_model,
                                 object_mapper=object_mapper,
                                 add_to_data_model=add_to_data_model)
            return new_val

        raise TypeError(f'Error creating mapped python object for {value}.')


def remove_prop_from_sim_component(component: SimComponent,
                                   component_idx: int = None,
                                   ref_component_idx: int = None,
                                   parameter_idx: int = None,
                                   ref_asset_idx: int = None,
                                   keep: list[str] = None):

    if keep is None:
        keep = []

    if component_idx is not None and 'component_idx' not in keep:
        component.Components.RemoveItem(component_idx)
        component_idx = None
    if ref_component_idx is not None and 'ref_component_idx'not in keep:
        component.ReferencedComponents.RemoveItem(ref_component_idx)
        ref_component_idx = None
    if parameter_idx is not None and 'parameter_idx' not in keep:
        component.Parameters.RemoveItem(parameter_idx)
        parameter_idx = None

    if ref_asset_idx is not None and 'ref_asset_idx' not in keep:
        asset = component.ReferencedAssets.Items[ref_asset_idx]
        remove_asset_from_component(component, asset)


def set_property_to_list(value: Union[list, tuple, set, ComponentList],
                         component: SimultanObject,
                         prop_name: str,
                         taxonomy_entry: SimTaxonomyEntry,
                         slot_extension: Union[str, int, float],
                         component_idx: int = None,
                         ref_component_idx: int = None,
                         parameter_idx: int = None,
                         ref_asset_idx: int = None,
                         content: Content = None):

    from .default_types import ComponentList

    remove_prop_from_sim_component(component=component,
                                   component_idx=component_idx,
                                   ref_component_idx=ref_component_idx,
                                   parameter_idx=parameter_idx,
                                   ref_asset_idx=ref_asset_idx,
                                   keep=['component_idx', 'ref_component_idx'])

    if isinstance(value, ComponentList):
        if component_idx is not None:
            if value._wrapped_obj.Id.Equals(component._wrapped_obj.Components.Items[component_idx].Component.Id):
                return
            else:
                component._wrapped_obj.Components.RemoveItem(component_idx)
                component_idx = None
        if ref_component_idx is not None:
            if value._wrapped_obj.Id.Equals(
                    component._wrapped_obj.ReferencedComponents.Items[ref_component_idx].Target.Id):
                return

    if component_idx is not None:
        component = component._wrapped_obj.Components.Items[component_idx].Component

        if 'ComponentList' in [x.Target.Key for x in component.Slots]:
            if not hasattr(component, '_object_mapper'):
                mapper = config.get_default_mapper()
                component._object_mapper = mapper
            else:
                mapper = component._object_mapper

            if not hasattr(component, '_data_model'):
                data_model = config.get_default_data_model()
                component._data_model = data_model
            else:
                data_model = component._data_model

            component_list = mapper.create_python_object(component, data_model=data_model)
            component_list.clear()
            component_list.extend(value)
            return component_list
        else:
            component._data_model.remove_subcomponent(component)
            component._wrapped_obj.Components.RemoveItem(component_idx)
        component_idx = None
    if ref_component_idx is not None:
        # component._data_model.remove_referenced_component(component, ref_component_idx)
        component._wrapped_obj.ReferencedComponents.RemoveItem(ref_component_idx)
        ref_component_idx = None

    slot = SimTaxonomyEntryReference(taxonomy_entry)

    new_component_list = create_component_list(values=value,
                                               name=prop_name,
                                               additional_slots=[slot],
                                               data_model=component._data_model,
                                               object_mapper=component._object_mapper,
                                               add_to_data_model=True)

    component.add_subcomponent(new_component_list,
                               slot_extension=slot_extension,
                               slot=slot)


def set_property_to_sim_component(value: Union[SimComponent, SimultanObject, list, tuple, set, ComponentList],
                                  component: SimultanObject,
                                  prop_name: str,
                                  taxonomy_entry: SimTaxonomyEntry,
                                  slot_extension: Union[str, int, float],
                                  component_idx: int = None,
                                  ref_component_idx: int = None,
                                  parameter_idx: int = None,
                                  ref_asset_idx: int = None,
                                  content: Content = None) -> None:

    wrapped_obj = value if isinstance(value, SimComponent) else value._wrapped_obj
    remove_prop_from_sim_component(component=component,
                                   component_idx=component_idx,
                                   ref_component_idx=ref_component_idx,
                                   parameter_idx=parameter_idx,
                                   ref_asset_idx=ref_asset_idx,
                                   keep=['component_idx', 'ref_component_idx'])

    if component_idx is not None:
        if wrapped_obj.Id.Equals(component._wrapped_obj.Components.Items[component_idx].Component.Id):
            return
        else:
            component._wrapped_obj.Components.RemoveItem(component_idx)
    if ref_component_idx is not None:
        if component._wrapped_obj.ReferencedComponents.Items[ref_component_idx].Target is None:
            component._wrapped_obj.ReferencedComponents.RemoveItem(ref_component_idx)
        elif wrapped_obj.Id.Equals(component._wrapped_obj.ReferencedComponents.Items[ref_component_idx].Target.Id):
            return
        else:
            component._wrapped_obj.ReferencedComponents.RemoveItem(ref_component_idx)

    if content.component_policy in (None, 'reference') or wrapped_obj.Parent is not None:
        component.add_referenced_component(value,
                                           slot_extension=slot_extension,
                                           slot=taxonomy_entry)
    elif content.component_policy == 'subcomponent':
        component.add_subcomponent(value,
                                   slot_extension=slot_extension,
                                   slot=taxonomy_entry)


def set_property_to_file_info(value: FileInfo,
                              component: SimultanObject,
                              prop_name: str,
                              taxonomy_entry: SimTaxonomyEntry,
                              slot_extension: Union[str, int, float],
                              component_idx: int = None,
                              ref_component_idx: int = None,
                              parameter_idx: int = None,
                              ref_asset_idx: int = None,
                              content: Content = None) -> None:

    remove_prop_from_sim_component(component=component,
                                   component_idx=component_idx,
                                   ref_component_idx=ref_component_idx,
                                   parameter_idx=parameter_idx,
                                   ref_asset_idx=ref_asset_idx,
                                   keep=['ref_asset_idx'])

    value.data_model = component._data_model

    if ref_asset_idx is not None:
        asset = component._wrapped_obj.ReferencedAssets.Items[ref_asset_idx]

        if hasattr(value, 'resource_entry'):
            if asset.Resource.Key == value.resource_entry.Key:
                return
        elif asset.Resource.CurrentFullPath == str(value.file_path):
            return

        remove_asset_from_component(component._wrapped_obj, asset)
        ref_asset_idx = None

    add_asset_to_component(component._wrapped_obj,
                           value.resource_entry,
                           '0',
                           tag=taxonomy_entry)


def set_property_to_directory_info(value: DirectoryInfo,
                                   component: SimultanObject,
                                   prop_name: str,
                                   taxonomy_entry: SimTaxonomyEntry,
                                   slot_extension: Union[str, int, float],
                                   component_idx: int = None,
                                   ref_component_idx: int = None,
                                   parameter_idx: int = None,
                                   ref_asset_idx: int = None,
                                   content: Content = None) -> None:

    remove_prop_from_sim_component(component=component,
                                   component_idx=component_idx,
                                   ref_component_idx=ref_component_idx,
                                   parameter_idx=parameter_idx,
                                   ref_asset_idx=ref_asset_idx,
                                   keep=['ref_asset_idx'])

    value.data_model = component._data_model

    if ref_asset_idx is not None:
        asset = component._wrapped_obj.ReferencedAssets.Items[ref_asset_idx]

        if hasattr(value, 'resource_entry'):
            if asset.Resource.Key == value.resource_entry.Key:
                return
        elif asset.Resource.CurrentFullPath == str(value.file_path):
            return

        remove_asset_from_component(component._wrapped_obj, asset)
        ref_asset_idx = None

    add_asset_to_component(component._wrapped_obj,
                           value.helper_file.resource_entry,
                           '0',
                           tag=taxonomy_entry)


def set_property_to_parameter(value: Union[int, float, str, Enum, bool],
                              component: SimultanObject,
                              prop_name: str,
                              taxonomy_entry: SimTaxonomyEntry,
                              slot_extension: Union[str, int, float],
                              component_idx: int = None,
                              ref_component_idx: int = None,
                              parameter_idx: int = None,
                              ref_asset_idx: int = None,
                              content: Content = None) -> None:

    remove_prop_from_sim_component(component=component,
                                   component_idx=component_idx,
                                   ref_component_idx=ref_component_idx,
                                   parameter_idx=parameter_idx,
                                   ref_asset_idx=ref_asset_idx,
                                   keep=['parameter_idx'])

    wrapped_obj = component._wrapped_obj

    if isinstance(value, Enum):
        value = value.value

    if parameter_idx is not None:
        existing_parameter_type = type(wrapped_obj.Parameters.Items[parameter_idx])

        new_param_type = content.type if content.type is not None else param_type_lookup_dict[type(value)]

        if new_param_type is not existing_parameter_type:
            wrapped_obj.Parameters.RemoveItem(parameter_idx)
            parameter_idx = None
        else:
            if wrapped_obj.Parameters.Items[parameter_idx].Value == value:
                return
            else:
                wrapped_obj.Parameters.Items[parameter_idx].set_Value(value)
                return

    if parameter_idx is None:
        param = create_parameter(value=value,
                                 name=prop_name,
                                 unit=content.unit if content.unit is not None else '',
                                 taxonomy_entry=taxonomy_entry,
                                 parameter_type=content.type)
        for key, value in content.additional_attributes.items():
            if hasattr(param, key):
                setattr(param, key, value)
        wrapped_obj.Parameters.Add(param)
    elif parameter_idx is not None:
        wrapped_obj.Parameters.Items[parameter_idx].set_Value(value)


def set_property_to_value_field(value: Union[np.ndarray, pd.DataFrame],
                                component: SimultanObject,
                                prop_name: str,
                                taxonomy_entry: SimTaxonomyEntry,
                                slot_extension: Union[str, int, float],
                                component_idx: int = None,
                                ref_component_idx: int = None,
                                parameter_idx: int = None,
                                ref_asset_idx: int = None,
                                content: Content = None
                                ) -> None:

    remove_prop_from_sim_component(component=component,
                                   component_idx=component_idx,
                                   ref_component_idx=ref_component_idx,
                                   parameter_idx=parameter_idx,
                                   ref_asset_idx=ref_asset_idx,
                                   keep=['parameter_idx'])

    wrapped_obj = component._wrapped_obj

    if parameter_idx is not None:
        existing_parameter_type = type(wrapped_obj.Parameters.Items[parameter_idx])

        if existing_parameter_type is not SimDoubleParameter:
            wrapped_obj.Parameters.RemoveItem(parameter_idx)
            parameter_idx = None
        else:
            value_source = wrapped_obj.Parameters.Items[parameter_idx].ValueSource

            if isinstance(value_source, SimMultiValueField3DParameterSource):
                value_field = wrapped_obj.Parameters.Items[parameter_idx].ValueSource.Field
            elif isinstance(value_source, SimMultiValueBigTableParameterSource):
                value_field = wrapped_obj.Parameters.Items[parameter_idx].ValueSource.Table
            else:
                raise ValueError(f'Value source {value_source} not supported.')

            component._data_model.remove_field(value_field)
            set_parameter_to_value_field(wrapped_obj.Parameters.Items[parameter_idx],
                                         value,
                                         field_name=str(component.id) + '_' + prop_name,
                                         data_model=component._data_model)

    if parameter_idx is None:

        param = create_field_parameter(field_name=str(component.id) + '_' + prop_name,
                                       value=value,
                                       slot=taxonomy_entry,
                                       data_model=component._data_model)
        wrapped_obj.Parameters.Add(param)


def set_property_to_unknown_type(value,
                                 component: SimultanObject,
                                 prop_name: str,
                                 *args, **kwargs):
    from .default_types import ComponentList, ComponentDictionary

    new_val = create_mapped_python_object(value, component._object_mapper, component._data_model)
    if isinstance(component, ComponentDictionary):
        component[prop_name] = new_val
    else:
        setattr(component, prop_name, new_val)


def set_property_to_dict(value: dict,
                         component: SimultanObject,
                         prop_name: str,
                         taxonomy_entry: SimTaxonomyEntry,
                         slot_extension: Union[str, int, float],
                         component_idx: int = None,
                         ref_component_idx: int = None,
                         parameter_idx: int = None,
                         ref_asset_idx: int = None,
                         content: Content = None):

    from .default_types import ComponentDictionary

    remove_prop_from_sim_component(component=component,
                                   component_idx=component_idx,
                                   ref_component_idx=ref_component_idx,
                                   parameter_idx=parameter_idx,
                                   ref_asset_idx=ref_asset_idx,
                                   keep=['component_idx', 'ref_component_idx'])

    if isinstance(value, ComponentDictionary):
        if component_idx is not None:
            if value._wrapped_obj.Id.Equals(component._wrapped_obj.Components.Items[component_idx].Component.Id):
                return
            else:
                component._wrapped_obj.Components.RemoveItem(component_idx)
                component_idx = None
        if ref_component_idx is not None:
            if value._wrapped_obj.Id.Equals(
                    component._wrapped_obj.ReferencedComponents.Items[ref_component_idx].Target.Id):
                return

    if component_idx is not None:
        sub_component = component._wrapped_obj.Components.Items[component_idx].Component

        if 'ComponentDictionary' in [x.Target.Key for x in component.Slots]:
            if not hasattr(component, '_object_mapper'):
                mapper = config.get_default_mapper()
                component._object_mapper = mapper
            else:
                mapper = component._object_mapper

            if not hasattr(component, '_data_model'):
                data_model = config.get_default_data_model()
                component._data_model = data_model
            else:
                data_model = component._data_model

            component_dict = mapper.create_python_object(component, data_model=data_model)
            component_dict.clear()
            component_dict.update(value)
            return component_dict
        else:
            component._wrapped_obj.Components.RemoveItem(component_idx)
        component_idx = None
    if ref_component_idx is not None:
        # component._data_model.remove_referenced_component(component, ref_component_idx)
        component._wrapped_obj.ReferencedComponents.RemoveItem(ref_component_idx)
        ref_component_idx = None

    slot = SimTaxonomyEntryReference(taxonomy_entry)

    new_component_dict = create_component_dict(values=value,
                                               name=prop_name,
                                               additional_slots=[slot],
                                               data_model=component._data_model,
                                               object_mapper=component._object_mapper,
                                               add_to_data_model=True)

    component.add_subcomponent(new_component_dict,
                               slot_extension=slot_extension,
                               slot=slot)

def add_properties(prop_name: str,
                   text_or_key: str,
                   content: Content,
                   taxonomy: str,
                   taxonomy_map: 'TaxonomyMap') -> property:

    """
    create property for a class
    :param prop_name: name of the property (str)
    :param text_or_key: text or key of the taxonomy entry (str)
    :param content: content of the property (Content)
    :param prop_name: name of the synonym (str)
    :param taxonomy: taxonomy to use (str)
    :param syn_name: name of the synonym (str)
    :param taxonomy_map: taxonomy map to use (TaxonomyMap)
    :return: property
    """

    from .default_types import ComponentList, ComponentDictionary

    class Empty:
        pass

    def getx(self):

        cache_value = self.__property_cache__.get(content.text_or_key, Empty)
        if isinstance(cache_value, SimultanPandasDataFrame):
            cache_value = Empty

        if cache_value is not Empty:
            return cache_value

        val = get_property(component=self,
                           text_or_key=content.text_or_key,
                           object_mapper=self._object_mapper)

        self.__property_cache__[content.text_or_key] = val
        return val

    getx.__taxonomy__ = taxonomy
    content = taxonomy_map.get_content_by_property_name(prop_name)

    def setx(self, value: Union[int, float, str, tuple, set, SimComponent, SimultanObject]):

        # logger.debug(f'Setting property {prop_name} to {value}.')

        self.__property_cache__.pop(content.text_or_key, None)

        slot_extension = content.slot_extension

        if slot_extension is None:
            slot_extension = 0

        taxonomy_entry = content.get_taxonomie_entry(self._data_model)

        component_idx, ref_component_idx, parameter_idx, ref_asset_idx = get_param_indices(self._wrapped_obj,
                                                                                           taxonomy_entry)

        fcn_arg_list = [value,
                        self,
                        prop_name,
                        taxonomy_entry,
                        slot_extension,
                        component_idx,
                        ref_component_idx,
                        parameter_idx,
                        ref_asset_idx,
                        content]

        if value is None:
            remove_prop_from_sim_component(component=self._wrapped_obj,
                                           component_idx=component_idx,
                                           ref_component_idx=ref_component_idx,
                                           parameter_idx=parameter_idx,
                                           keep=[])
            return

        if isinstance(value, UnresolvedObject):
            return

        from .type_setter_lookup import type_setter_fcn_lookup_dict

        setter_fcn = type_setter_fcn_lookup_dict.get(value, set_property_to_unknown_type)

        setter_fcn(*fcn_arg_list)

    setx.__taxonomy__ = taxonomy

    def delx(self):

        sim_taxonomy = self._data_model.get_or_create_taxonomy(taxonomy_name=taxonomy_map.taxonomy_name,
                                                               taxonomy_key=taxonomy_map.taxonomy_key)
        taxonomy_entry = self._data_model.get_or_create_taxonomy_entry(key=content.text_or_key,
                                                                       name=content.property_name,
                                                                       sim_taxonomy=sim_taxonomy)
        component_idx, ref_component_idx, parameter_idx, ref_asset_idx = get_param_indices(self._wrapped_obj,
                                                                                           taxonomy_entry)

        remove_prop_from_sim_component(component=self,
                                       component_idx=component_idx,
                                       ref_component_idx=ref_component_idx,
                                       parameter_idx=parameter_idx,
                                       ref_asset_idx=ref_asset_idx)

    delx.__taxonomy__ = taxonomy

    return property(getx, setx, delx, "automatic created property")


def uncache(exclude):
    """Remove package modules from cache except excluded ones.
    On next import they will be reloaded.

    Args:
        exclude (iter<str>): Sequence of module paths.
    """
    pkgs = []
    for mod in exclude:
        pkg = mod.split('.', 1)[0]
        pkgs.append(pkg)

    to_uncache = []
    for mod in sys.modules:
        if mod in exclude:
            continue

        if mod in pkgs:
            to_uncache.append(mod)
            continue

        for pkg in pkgs:
            if mod.startswith(pkg + '.'):
                to_uncache.append(mod)
                break

    for mod in to_uncache:
        del sys.modules[mod]
