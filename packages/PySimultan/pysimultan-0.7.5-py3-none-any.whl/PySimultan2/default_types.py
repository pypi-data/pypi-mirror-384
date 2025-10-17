from __future__ import annotations

from collections.abc import Iterable
import numpy as np
import colorlog
from typing import Union, List, Type, Set, Tuple, Any, Optional

from .geometry.geometry_base import classproperty
from .utils import (sort_slots, create_simultan_component_for_taxonomy, create_mapped_python_object,
                    set_property_to_sim_component, set_property_to_parameter, set_property_to_file_info,
                    set_property_to_list, set_property_to_value_field, set_property_to_unknown_type,
                    remove_prop_from_sim_component, get_param_indices, set_property_to_dict, get_obj_value,
                    get_component_taxonomy_entry)
from .simultan_object import SimultanObject
from .taxonomy_maps import TaxonomyMap, Content

from SIMULTAN.Data.Components import (ComponentWalker, SimComponent, SimBoolParameter, SimDoubleParameter,
                                      SimEnumParameter, SimIntegerParameter, SimStringParameter, ComponentMapping,
                                      SimSlot, SimComponentVisibility, SimChildComponentEntry, SimDefaultSlots,
                                      SimParameterOperations, SimComponentReference)

from SIMULTAN.Data.Assets import DocumentAsset

from .files import FileInfo

from . import config

logger = colorlog.getLogger('PySimultan')


class ComponentList(SimultanObject):

    _create_all = False     # if true all properties are evaluated to create python objects when initialized
    _taxonomy = 'ComponentList'

    @classproperty
    def _original_class(cls) -> Type[ComponentList]:
        return cls

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.component_policy = kwargs.get('component_policy', 'subcomponent')  # component add policy of the content/parameter/property, 'reference' or 'subcomponent'
        self.index = 0

        if args:
            self.append(args)

    @classmethod
    def create_from_values(cls,
                           values: Union[List[SimultanObject], Set[SimultanObject], Tuple[SimultanObject]],
                           data_model=None,
                           object_mapper=None,
                           *args,
                           **kwargs,
                           ):

        # logger.debug(f'Creating new component list from values {values}')

        wrapped_obj = create_simultan_component_for_taxonomy(cls,
                                                             data_model=data_model,
                                                             object_mapper=object_mapper,
                                                             add_to_data_model=kwargs.get('add_to_data_model', True))

        new_component_list = cls(wrapped_obj=wrapped_obj,
                                 data_model_id=data_model.id,
                                 object_mapper=object_mapper,
                                 data_model=data_model,
                                 )

        wrapped_obj.Name = kwargs.get('name', 'UnnamedComponentList')

        new_component_list.append(values)

        # for i, value in enumerate(values):
        #     if isinstance(value, SimultanObject):
        #         try:
        #             new_component_list.add_referenced_component(value._wrapped_obj,
        #                                                         slot_extension=str(i),
        #                                                         slot=value.slot)
        #         except Exception as e:
        #             logger.error(f'Could not add component {value} to list {new_component_list}:\n{e}')
        #     else:
        #         new_val = create_mapped_python_object(value,
        #                                               data_model=data_model,
        #                                               object_mapper=object_mapper,
        #                                               add_to_data_model=True)
        #
        #         taxonomy = data_model.get_or_create_taxonomy(taxonomy_name=new_val._taxonomy_map.taxonomy_name,
        #                                                      taxonomy_key=new_val._taxonomy_map.taxonomy_key)
        #
        #         taxonomy_entry = data_model.get_or_create_taxonomy_entry(name=new_val._taxonomy_map.taxonomy_entry_name,
        #                                                                  key=new_val._taxonomy_map.taxonomy_entry_key,
        #                                                                  sim_taxonomy=taxonomy)
        #
        #         new_component_list.add_subcomponent(new_val._wrapped_obj,
        #                                             slot_extension=str(i),
        #                                             slot=taxonomy_entry)

        # logger.debug(f'Created new component list {new_component_list.id} from values {new_component_list}')

        return new_component_list

    @property
    def components(self):
        return [x.Component for x in self._wrapped_obj.Components.Items]

    @property
    def ref_components(self):
        return [x.Target for x in self._wrapped_obj.ReferencedComponents.Items if x.Target is not None]

    @property
    def data(self) -> List[SimultanObject]:
        try:
            if self._wrapped_obj is None:
                return
            components = self.components
            ref_components = self.ref_components
            all_components = [*components, *ref_components]

            slots = [*[x.Slot for x in self._wrapped_obj.Components.Items],
                     *[x.Slot for x in self._wrapped_obj.ReferencedComponents.Items if x.Target is not None]]

            try:
                indices = sort_slots(slots)
                return [self._object_mapper.create_python_object(x, data_model=self._data_model) for x in
                        [all_components[i] for i in np.argsort(indices)]]
            except TypeError as e:
                logger.warning(f'Could not sort list {all_components}:\n{e}')
                return [self._object_mapper.create_python_object(x, data_model=self._data_model) for x in all_components]
        except Exception as e:
            logger.error(f'Could not get data from list {self}:\n{e}')
            return []

    def discard(self,
                value: SimultanObject,
                update_slots: bool = True):

        components = self.components
        subcomponents = self.ref_components

        if value._wrapped_obj in components:
            index = components.index(value._wrapped_obj)
            self._data_model.add_component(value._wrapped_obj)
            self._wrapped_obj.Components.RemoveAt(index)
        elif value._wrapped_obj in subcomponents:
            index = subcomponents.index(value._wrapped_obj)
            self.remove_referenced_component(value._wrapped_obj)
        else:
            raise ValueError(f'Component {value} not in list {self}')
        if update_slots:
            self._update_slot_extensions(index)

    def insert(self, index: int, value: Any):
        for i, component in enumerate(self.data[index:]):
            if component._wrapped_obj in self.components:
                slot, c_entry = next(
                    (x.Slot, x) for x in self._wrapped_obj.Components.Items if x.Component == component._wrapped_obj)
            elif component._wrapped_obj in self.ref_components:
                slot, c_entry = next((x.Slot, x) for x in self._wrapped_obj.ReferencedComponents.Items if
                                     x.Target == component._wrapped_obj)
            c_entry.set_Slot(SimSlot(slot.SlotBase, str(i + index + 1)))

        self._set_value(value, index)
        print(f'Inserted {value} at index {index}')

        if self.data[index] is not value:
            raise ValueError(f'Could not insert {value} at index {index}')

    def append(self, values: Union[SimultanObject, List]):

        return_val = []

        as_list = True
        if not isinstance(values, Iterable):
            as_list = False
            values = [values]

        for i, value in enumerate(values, start=len(self.data)):
            return_val.append(self._set_value(value, i))

        if not as_list:
            return return_val[0]
        return return_val

    def _update_slot_extensions(self, index: int):

        # update slot extension of all elements > index
        for i, component in enumerate(self.data):
            if i > index-1:
                if component._wrapped_obj in self.components:
                    slot, c_entry = next((x.Slot, x) for x in self._wrapped_obj.Components.Items if x.Component == component._wrapped_obj)
                elif component._wrapped_obj in self.ref_components:
                    slot, c_entry = next((x.Slot, x) for x in self._wrapped_obj.ReferencedComponents.Items if x.Target == component._wrapped_obj)
                else:
                    raise ValueError(f'Component {component} not in list {self}')
                c_entry.set_Slot(SimSlot(slot.SlotBase, str(i)))

    def _set_value(self, value, i):

        if isinstance(value, FileInfo):
            raise ValueError(f'FileInfos cannot be added to ComponentLists')

        if isinstance(value, SimultanObject):
            slot = value._wrapped_obj.Slots.Items[0]

            if self.component_policy == 'subcomponent' and value._wrapped_obj.Parent is None:
                if value in self.components:
                    self.add_referenced_component(value._wrapped_obj,
                                                  slot_extension=str(i),
                                                  slot=slot)
                else:
                    self.add_subcomponent(value._wrapped_obj,
                                          slot_extension=str(i),
                                          slot=slot)
            else:
                self.add_referenced_component(value._wrapped_obj,
                                              slot_extension=str(i),
                                              slot=slot)

            return value

        else:
            new_val = create_mapped_python_object(value,
                                                  data_model=self._data_model,
                                                  object_mapper=self._object_mapper,
                                                  add_to_data_model=True)

            taxonomy = self._data_model.get_or_create_taxonomy(taxonomy_name=new_val._taxonomy_map.taxonomy_name,
                                                               taxonomy_key=new_val._taxonomy_map.taxonomy_key)

            taxonomy_entry = self._data_model.get_or_create_taxonomy_entry(name=new_val._taxonomy_map.taxonomy_entry_name,
                                                                           key=new_val._taxonomy_map.taxonomy_entry_key,
                                                                           sim_taxonomy=taxonomy)

            if new_val._wrapped_obj.Parent is None:
                self.add_subcomponent(new_val._wrapped_obj,
                                      slot_extension=str(i),
                                      slot=taxonomy_entry)
            else:
                self.add_referenced_component(new_val._wrapped_obj,
                                              slot_extension=str(i),
                                              slot=taxonomy_entry)

            return new_val

    def __setitem__(self, i, value):
        if isinstance(i, slice):
            for j, val in enumerate(value):
                self.__setitem__(i.start + j, val)
        else:
            if i < 0:
                i += len(self.data)

            if i >= len(self.data):
                self.append([value])
            else:
                if self.data[i] is value:
                    return
                self.discard(self.data[i])
                self.insert(i, value)

        if self.data[i] is not value:
            raise ValueError(f'Could not insert {value} at index {i}')

    def extend(self, values: List):
        return self.append(values)

    def remove(self, value: SimultanObject):
        self.discard(value)

    def add(self, value: Union[SimultanObject, List[SimultanObject]]):
        if value not in self.data:
            self.append(value)

    def move_item(self, item: SimultanObject, new_index: int):
        if item not in self.data:
            raise ValueError(f'Item {item} not in list {self}')
        old_index = self.data.index(item)

        if new_index < 0:
            new_index += len(self.data)

        if new_index == old_index:
            return

        new_data = self.data.copy()
        new_data.pop(old_index)
        new_data.insert(new_index, item)

        for i, item in enumerate(new_data):
            if item._wrapped_obj in self.components:
                slot, c_entry = next(
                    (x.Slot, x) for x in self._wrapped_obj.Components.Items if x.Component == item._wrapped_obj)
            elif item._wrapped_obj in self.ref_components:
                slot = next(
                    x.Slot for x in self._wrapped_obj.ReferencedComponents.Items if x.Target == item._wrapped_obj)
            else:
                raise ValueError(f'Component {item} not in list {self}')
            c_entry.set_Slot(SimSlot(slot.SlotBase, str(i)))

    def __getitem__(self, i):
        if isinstance(i, slice):
            if self._object_mapper is None:
                return self.__class__(self.data[i])
            return [self._object_mapper.create_python_object(x, data_model=self._data_model)
                    for x in self.__class__(self.data[i])]
        else:
            if self._object_mapper is None:
                return self.data[i]
            return self._object_mapper.create_python_object(self.data[i], data_model=self._data_model)

    def __delitem__(self, i):
        if isinstance(i, slice):
            for j in range(i.start, i.stop):
                self.discard(self.data[j])
        else:
            self.discard(self.data[i])

    def __repr__(self):
        return f'List {self.name}: ' + repr(list(self.data))

    def __iter__(self):
        return iter([self._object_mapper.create_python_object(x, data_model=self._data_model) for x in self.data])

    def __next__(self):
        try:
            result = self.__getitem__(self.index)
        except IndexError:
            raise StopIteration
        self.index += 1
        return result

    def __len__(self):
        return self.data.__len__()

    @property
    def parent(self):
        if not hasattr(self._wrapped_obj, 'Parent'):
            return None

        if self._wrapped_obj.Parent is not None:
            return self._object_mapper.create_python_object(self._wrapped_obj.Parent, data_model=self._data_model)
        else:
            return None

    @property
    def referenced_by(self):
        return set([self._object_mapper.create_python_object(x.Target, data_model=self._data_model) for x in self._wrapped_obj.ReferencedBy if
                    x.Target != self._wrapped_obj])

    def clear(self):
        self._wrapped_obj.Components.Clear()
        self._wrapped_obj.ReferencedComponents.Clear()

    def to_json(self) -> dict[Any: Any]:

        return_val = [None] * len(self.data)

        for i, val in enumerate(self.data):

            if hasattr(val, 'json_ref'):
                return_val[i] = val.json_ref()
            elif isinstance(val, list):
                return_val[i] = [v.json_ref() if hasattr(v, 'json_ref') else v for v in val]
            elif isinstance(val, dict):
                return_val[i] = {k: v.json_ref() if hasattr(v, 'json_ref') else v for k, v in val.items()}
            elif isinstance(val, np.ndarray):
                return_val[i] = val.tolist()
            else:
                return_val[i] = val

        return {
            str(self.id): {
                'name': self.name,
                'taxonomies': self.taxonomy_keys,
                'items': return_val
            }
        }

    def json_ref(self):
        return {"$ref": {
            "$type": 'ComponentList',
            "$taxonomies": self.taxonomy_keys,
            "$id": {'local_id': self.id.LocalId,
                    'global_id': str(self.id.GlobalId)
                    },
            "length": len(self)
        }
        }

component_list_map = TaxonomyMap(taxonomy_name='PySimultan',
                                 taxonomy_key='PySimultan',
                                 taxonomy_entry_name='ComponentList',
                                 taxonomy_entry_key='ComponentList',
                                 )

ComponentList._taxonomy_map = component_list_map


class ComponentDictionary(SimultanObject):

    component_policy = 'subcomponent'  # component add policy of the content/parameter/property, 'reference'
    # or 'subcomponent'

    _taxonomy_map = TaxonomyMap(taxonomy_name='Dictionaries',
                                taxonomy_key='Dictionaries',
                                taxonomy_entry_name='ComponentDict',
                                taxonomy_entry_key='ComponentDict',
                                )

    _taxonomy = 'ComponentDict'

    @classproperty
    def _original_class(cls) -> Type[ComponentList]:
        return cls

    def __init__(self, *args, **kwargs):
        self._dict = {}
        super().__init__(*args, **kwargs)
        self.component_policy = kwargs.get('component_policy', 'subcomponent')  # component add policy of the content/parameter/property, 'reference' or 'subcomponent'
        self._generate_internal_dict()

    def __load_init__(self, *args, **kwargs):
        self._dict = {}
        self._generate_internal_dict()

    @classmethod
    def create_from_values(cls,
                           values: dict[str, Any],
                           data_model=None,
                           object_mapper=None,
                           *args,
                           **kwargs,
                           ):

        wrapped_obj = create_simultan_component_for_taxonomy(cls,
                                                             data_model=data_model,
                                                             object_mapper=object_mapper,
                                                             add_to_data_model=kwargs.get('add_to_data_model', True))

        new_component_dict = cls(wrapped_obj=wrapped_obj,
                                 data_model_id=data_model.id,
                                 object_mapper=object_mapper,
                                 data_model=data_model,
                                 )

        wrapped_obj.Name = kwargs.get('name', 'UnnamedComponentDict')

        for key, value in values.items():
            new_component_dict[key] = value

        new_component_dict._generate_internal_dict()

        return new_component_dict

    def __getitem__(self, key, *args, **kwargs):

        comp_dict = object.__getattribute__(self, '_dict')

        if (kwargs.get('check_dict', False) and comp_dict is not None and
                (key in comp_dict.keys() or '__dict_key__' + key in comp_dict.keys())):
            if key in comp_dict.keys():
                return comp_dict.get(key, None)
            else:
                return comp_dict.get('__dict_key__' + key, None)
        else:
            # data_model = config.default_data_model
            # obj = get_component_taxonomy_entry(self._wrapped_obj, key)
            # if obj is not None:
            # val = get_obj_value(obj, data_model=self._data_model, object_mapper=self._object_mapper)
            data_model = self._data_model
            object_mapper = self._object_mapper
            wrapped_obj = self._wrapped_obj

            if key in self._taxonomy_map.parameter_taxonomy_entry_dict.keys():
                text_or_key = self._taxonomy_map.parameter_taxonomy_entry_dict[key]
            else:
                content = Content(text_or_key=f'__dict_key__{key}',
                                  property_name=key,
                                  type=None,
                                  unit=None,
                                  documentation=f'Property {key} in ComponentDictionary',
                                  component_policy=self.component_policy)
                self._taxonomy_map.add_content(content)
                text_or_key = content.text_or_key

            try:
                components = list(wrapped_obj.Components.Items)
                val = next((get_obj_value(x.Component,
                                          data_model=data_model,
                                          object_mapper=object_mapper) for x in components if
                            x.Slot.SlotBase.Target.Key == text_or_key), None)
                if val is None:
                    ref_components = list(wrapped_obj.ReferencedComponents.Items)
                    val = next((get_obj_value(x.Target,
                                              data_model=data_model,
                                              object_mapper=object_mapper) for x in ref_components
                                if x.Slot.SlotBase.Target.Key == text_or_key), None)
                if val is None:
                    parameters = list(wrapped_obj.Parameters.Items)
                    val = next((get_obj_value(x,
                                              data_model=data_model,
                                              object_mapper=object_mapper) for x in parameters if
                                x.NameTaxonomyEntry.TextOrKey == text_or_key), None)

            except Exception as e:
                logger.error(f'Could not get value for key {key} ({text_or_key}) in {self}:\n{e}')
                raise ValueError(f'Could not get value for key {key} ({text_or_key}) in {self}:\n{e}')

            val = get_obj_value(val,
                                data_model=data_model,
                                object_mapper=object_mapper)

            if val is not None:
                if key.startswith('__dict_key__'):
                    key = key.replace('__dict_key__', '')
                self._dict[key] = val

        return self._dict.get(key, None)

    def __setitem__(self, key, value):

        # if key in self._dict:
        #     del self._dict[key]

        if key in self._taxonomy_map.content_dict.keys():
            content = self._taxonomy_map.content_dict[key]
        elif '__dict_key__' + key in self._taxonomy_map.content_dict.keys():
            content = self._taxonomy_map.content_dict['__dict_key__' + key]
        else:
            content = Content(text_or_key=f'__dict_key__{key}',
                              property_name=key,
                              type=None,
                              unit=None,
                              documentation=f'Property {key} in ComponentDictionary',
                              component_policy=self.component_policy)
            self._taxonomy_map.add_content(content)
        taxonomy_entry = content.get_taxonomie_entry(self._data_model)
        component_idx, ref_component_idx, parameter_idx, ref_asset_idx = get_param_indices(self._wrapped_obj,
                                                                                           taxonomy_entry)

        slot_extension = content.slot_extension

        if slot_extension is None:
            slot_extension = 0

        fcn_arg_list = [value,
                        self,
                        key,
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

        from .type_setter_lookup import type_setter_fcn_lookup_dict
        setter_fcn = type_setter_fcn_lookup_dict.get(value, set_property_to_unknown_type)

        setter_fcn(*fcn_arg_list)
        item = self.__getitem__(key, check_dict=False)

        if key.startswith('__dict_key__'):
            self._dict[key.replace('__dict_key__', '')] = item
        else:
            self._dict[key] = item

    def __delitem__(self, key):
        self[key] = None
        try:
            del self._dict[key]
        except KeyError:
            pass

    def items(self):
        if self._dict is None or not self._dict:
            self._generate_internal_dict()
        return self._dict.items()

    def keys(self):
        if not self._dict or not self._dict:
            self._generate_internal_dict()
        return self._dict.keys()

    def values(self):
        if not self._dict or not self._dict:
            self._generate_internal_dict()
        return self._dict.values()

    def _generate_internal_dict(self):
        comp_dict = {}

        for parameter in self._wrapped_obj.Parameters.Items:
            key = parameter.NameTaxonomyEntry.TextOrKey.replace('__dict_key__', '')
            comp_dict[key] = get_obj_value(parameter,
                                           data_model=self._data_model,
                                           object_mapper=self._object_mapper)
        for component in self._wrapped_obj.Components.Items:
            key = component.Slot.SlotBase.Target.Key.replace('__dict_key__', '')
            comp_dict[key] = get_obj_value(component.Component,
                                           data_model=self._data_model,
                                           object_mapper=self._object_mapper)
        for ref_component in self._wrapped_obj.ReferencedComponents.Items:
            key = ref_component.Slot.SlotBase.Target.Key.replace('__dict_key__', '')
            comp_dict[key] = get_obj_value(ref_component.Target,
                                           data_model=self._data_model,
                                           object_mapper=self._object_mapper)
        for ref_asset in self._wrapped_obj.ReferencedAssets.Items:
            for tag in ref_asset.Resource.Tags:
                key = tag.Target.Key.replace('__dict_key__', '')
                if isinstance(ref_asset, DocumentAsset):
                    comp_dict[key] = get_obj_value(ref_asset.Resource,
                                                   data_model=self._data_model,
                                                   object_mapper=self._object_mapper)
                else:
                    comp_dict[key] = get_obj_value(ref_asset.Target,
                                                   data_model=self._data_model,
                                                   object_mapper=self._object_mapper)

        object.__setattr__(self, '_dict', comp_dict)

    def clear(self):
        for key in self.keys():
            del self[key]

    def __repr__(self):
        if not self._dict:
            self._generate_internal_dict()
        return repr(self._dict)

    def __iter__(self):
        return self._dict.__iter__()

    def __next__(self):
        return self._dict.__next__()

    def __len__(self):
        return len(self._dict)

    def __contains__(self, key):
        return key in self._dict

    def get(self, key, default=None):
        return self._dict.get(key, default)

    def update(self, other):
        for key, value in other.items():
            self[key] = value

    def to_json(self) -> dict:

        return_value = {}

        for key, value in self.items():
            if isinstance(value, SimultanObject):
                return_value[key] = value.to_json()
            elif isinstance(value, list):
                return_value[key] = [v.json_ref() if hasattr(v, 'json_ref') else v for v in value]
            elif isinstance(value, dict):
                return_value[key] = {k: v.json_ref() if hasattr(v, 'json_ref') else v for k, v in value.items()}
            elif isinstance(value, np.ndarray):
                return_value[key] = value.tolist()
            else:
                return_value[key] = value

        return {
            str(self.id): {
                'name': self.name,
                'taxonomies': self.taxonomy_keys,
                'items': return_value
            }
        }

    def json_ref(self):
        return {"$ref": {
            "$type": 'ComponentDictionary',
            "$taxonomies": self.taxonomy_keys,
            "$id": {'local_id': self.id.LocalId,
                    'global_id': str(self.id.GlobalId)
                    },
            "length": len(self)
        }
        }

    def get_raw_attr(self, attr: Optional[str] = None, text_or_key: Optional[str] = None):
        if attr is not None:
            content = self._taxonomy_map.get_content_by_property_name(attr)
            if content is None:
                content = Content(text_or_key=f'__dict_key__{attr}',
                                  property_name=attr,
                                  type=None,
                                  unit=None,
                                  documentation=f'Property {attr} in ComponentDictionary',
                                  component_policy=self.component_policy)
                self._taxonomy_map.add_content(content)

            return get_component_taxonomy_entry(self._wrapped_obj, content.text_or_key)

        if text_or_key is not None:
            return get_component_taxonomy_entry(self._wrapped_obj, text_or_key)


component_dict_map = ComponentDictionary._taxonomy_map
