import hashlib
import json

from copy import copy
from weakref import WeakSet
from functools import lru_cache
from . import utils
from numpy import ndarray
from pandas import DataFrame
import colorlog
from typing import Union, Optional, Any

logger = colorlog.getLogger('PySimultan')

from SIMULTAN.Data.Taxonomy import SimTaxonomyEntry, SimTaxonomyEntryReference, SimTaxonomy
from SIMULTAN.Data.Components import (ComponentWalker, SimComponent, SimBoolParameter, SimDoubleParameter,
                                      SimEnumParameter, SimIntegerParameter, SimStringParameter, ComponentMapping,
                                      SimSlot, ComponentMapping)
from SIMULTAN.Data.Assets import ResourceEntry, ResourceFileEntry, ContainedResourceFileEntry, Asset
from SIMULTAN.Data import SimId

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .data_model import DataModel
    from .object_mapper import PythonMapper
    from .geometry.geometry_base import ExtendedBaseGeometry

from .geometry.utils import create_python_geometry

from . import config


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, SimultanObject):
            return obj.to_json()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class classproperty(object):

    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


class MetaMock(type):
    def __call__(cls: 'SimultanObject', *args, **kwargs) -> 'SimultanObject':
        """
        Metaclass to implement object initialization either with wrapped_obj or keywords.

        If a wrapped_obj is defined, create new SimultanObject which wraps a SIMULTAN component (wrapped_obj).

        If no 'wrapped_obj' is defined, a new SimComponent is created with the content defined in the template and the
        values are set to the values defined in kwargs.
        """

        obj = cls.__new__(cls, *args, **kwargs)

        wrapped_obj = kwargs.get('wrapped_obj', None)
        if wrapped_obj is None:

            data_model = kwargs.get('data_model', None)
            if data_model is None:
                if config.get_default_data_model() is not None:
                    logger.warning(
                        f'No data model provided. Using default data model: {config.get_default_data_model().id}')
                    data_model = config.get_default_data_model()
                    kwargs['data_model'] = data_model
                else:
                    raise TypeError((f'Error creating new instance of class {cls.__name__}:\n'
                                     f'Any data model was defined. Tried to use default data model but there are multiple datamodels.\n'
                                     f'Define the data model to use with the key: data_model'))

            wrapped_obj = cls.create_simultan_component(*args, **kwargs)

            init_dict = kwargs.copy()
            init_dict['data_model_id'] = data_model.id
            init_dict['object_mapper'] = cls._object_mapper
            init_dict['data_model'] = data_model
            init_dict['wrapped_obj'] = wrapped_obj

            obj.__init__(*args, **init_dict)

            # for key, value in kwargs.items():
            #     if key in ['data_model', 'wrapped_obj', 'object_mapper']:
            #         continue
            #     setattr(obj, key, value)

        else:
            obj.__init__(*args, **kwargs)
        return obj


class SimultanObject(object, metaclass=MetaMock):

    _cls_instances = set()  # weak set with all created objects
    _create_all = False  # if true all properties are evaluated to create python objects when initialized
    _cls_instances_dict_cache = None
    __type_view__ = None      # ui view cls

    @classmethod
    def reset_cls(cls):
        cls._cls_instances = set()
        cls._cls_instances_dict_cache = None

    @classmethod
    def get_instance_by_id(cls, id: SimId) -> 'SimultanObject':
        return cls._cls_instances_dict.get(id, None)

    @classproperty
    def _cls_instances_dict(cls) -> dict[SimId, 'SimultanObject']:
        if cls._cls_instances_dict_cache is None:
            cls._cls_instances_dict_cache = dict(zip([x.id for x in cls._cls_instances], [x for x in cls._cls_instances]))

        elif len(cls._cls_instances) == 0:
            return {}
        elif len(cls._cls_instances) != len(cls._cls_instances_dict_cache):
            cls._cls_instances_dict_cache = dict(zip([x.id for x in cls._cls_instances], [x for x in cls._cls_instances]))
        return cls._cls_instances_dict_cache

    @classproperty
    def cls_instances(cls) -> list['SimultanObject']:
        try:
            return list(cls._cls_instances)
        except Exception as e:
            logger.error(f'Error getting cls_instances: {e}')
            return []

    @classproperty
    def super_classes(cls):
        superclasses = []
        for key, mcls in cls._object_mapper.mapped_classes.items():
            if mcls is cls:
                continue
            if set(cls._original_cls.__mro__) & set(mcls._original_cls.__mro__) - set([object]) and \
                    set(mcls._original_cls.__mro__) - set(cls._original_cls.__mro__) - set((SimultanObject,
                                                           object)):
                superclasses.append(mcls)
        return superclasses

    @classproperty
    def sub_classes(cls):
        subclasses = []
        for key, mcls in cls._object_mapper.mapped_classes.items():
            if mcls is cls:
                continue
            if set(cls._original_cls.__mro__) & set(mcls._original_cls.__mro__) - set([object]) and \
                    set(cls._original_cls.__mro__) - set(mcls._original_cls.__mro__) - set((SimultanObject,
                                                                                            object)):
                subclasses.append(mcls)
        return subclasses

    @classproperty
    def super_class_instances(cls) -> set['SimultanObject']:
        instances = set()
        _ = [instances.update(x.cls_instances) for x in cls.super_classes]
        return instances

    @classproperty
    def sub_class_instances(cls) -> set['SimultanObject']:
        instances = set()
        _ = [instances.update(x.cls_instances) for x in cls.sub_classes]
        return instances

    @classmethod
    def create_simultan_component(cls, *args, **kwargs) -> SimComponent:
        wrapped_obj = utils.create_simultan_component_for_taxonomy(cls, *args, **kwargs)
        wrapped_obj.Name = kwargs.get('name', 'UnnamedComponent')
        return wrapped_obj

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        if "_cls_instances" not in cls.__dict__:
            cls._cls_instances = set()
        try:
            cls._cls_instances.add(instance)
        except Exception as e:
            logger.error(f'Error adding instance {instance} to _cls_instances: {e}')

        return instance

    def __init__(self, *args, **kwargs):
        """
        Initialize the SimultanObject. This method is only called if the object is initialized the first time without a
        wrapped_obj. If a wrapped_obj is defined, the __new__ method is called and the object can be initialized with
        the __load_init__ method.

        :param args:
        :param kwargs:
        """

        self._wrapped_obj: Union[SimComponent, None] = kwargs.get('wrapped_obj', None)
        self.__obj_init__: bool = kwargs.get('__obj_init__', False)
        self._data_model: Union[DataModel, None] = kwargs.get('data_model', config.get_default_data_model())

        object_mapper = kwargs.get('object_mapper', None)
        if object_mapper is None:
            object_mapper = config.get_default_mapper()
        self._object_mapper: Union[PythonMapper, None] = object_mapper
        self.name: str = kwargs.get('name', '')

        self.__property_cache__ = {}
        self._slot = None

    def __getattribute__(self, attr) -> Any:

        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            wrapped = object.__getattribute__(self, '_wrapped_obj')
            if wrapped is not None:
                return object.__getattribute__(wrapped, attr)
            else:
                raise KeyError

    def __setattr__(self, attr, value) -> None:
        if hasattr(self, '_wrapped_obj'):
            if hasattr(self._wrapped_obj, attr) and (self._wrapped_obj is not None) and not self.__obj_init__:
                object.__setattr__(self._wrapped_obj, attr, value)
                return
        # object.__setattr__(self, attr, value)
        super().__setattr__(attr, value)

        # if hasattr(super(self.__class__), attr):
        #     super(self.__class__).__setattr__(attr, value)

    @property
    def id(self) -> SimId:
        if self._wrapped_obj is not None:
            return self._wrapped_obj.Id

    @property
    def id_str(self) -> str:
        return '_'.join((str(self.id.GlobalId), str(self.id.LocalId)))

    @property
    def taxonomy_keys(self) -> list[str]:
        if self._wrapped_obj is not None:
            return [x.Target.Key for x in self._wrapped_obj.Slots]

    @property
    def name(self) -> str:
        if self._wrapped_obj is not None:
            return self._wrapped_obj.Name

    @name.setter
    def name(self, value: str):
        if self._wrapped_obj is not None:
            self._wrapped_obj.Name = value

    @property
    def parent(self) -> 'SimultanObject':
        if not hasattr(self._wrapped_obj, 'Parent'):
            return None

        if self._wrapped_obj.Parent is not None:
            return self._object_mapper.create_python_object(self._wrapped_obj.Parent, data_model=self._data_model)
        else:
            return None

    @property
    def slots(self):
        if self._wrapped_obj is not None:
            return list(self._wrapped_obj.Slots.Items)

    @property
    def primary_slot(self):
        if self._wrapped_obj is not None:
            return self._wrapped_obj.Slots.Items[0]

    @property
    def referenced_by(self) -> set['SimultanObject']:
        return set([self._object_mapper.create_python_object(x.Target, data_model=self._data_model)
                    for x in self._wrapped_obj.ReferencedBy if
                    x.Target != self._wrapped_obj])

    @property
    def _parameters(self) -> dict[str, Union[str, int, float, bool, ndarray]]:
        return {x.NameTaxonomyEntry.get_TextOrKey(): utils.get_obj_value(x,
                                                                         data_model=self._data_model,
                                                                         object_mapper=self._object_mapper) for x in
                self._wrapped_obj.Parameters}

    @property
    def associated_geometry(self):
        ref_geometries = self._data_model.get_associated_geometry(self)

        return [create_python_geometry(None, geo, self._data_model, self._object_mapper, geo_model) for geo, geo_model in
                ref_geometries]

    def get_subcomponents(self) -> dict[[str, str], Union['SimultanObject', SimComponent]]:
        subcomponents = {}
        for comp in self._wrapped_obj.Components:
            subcomponents[(comp.Slot.SlotBase.Target.Key,
                           comp.Slot.SlotExtension)] = self._object_mapper.create_python_object(comp.Component,
                                                                                                data_model=self._data_model)
        return subcomponents

    def get_subcomponent_list(self) -> list[Union['SimultanObject', SimComponent]]:
        return list(self.get_subcomponents().values())

    def get_referenced_components(self) -> list['SimultanObject']:
        return [self._object_mapper.create_python_object(x, data_model=self._data_model)
                for x in self._wrapped_obj.ReferencedComponents]

    def add_taxonomy_entry_reference(self,
                                     taxonomy_entry_reference: SimTaxonomyEntryReference,
                                     index: int = None):
        if index is None:
            index = self._wrapped_obj.Slots.Items.__len__()
        self._wrapped_obj.Slots.InsertItem(index, taxonomy_entry_reference)

    def add_subcomponent(self, subcomponent: Union['SimultanObject', SimComponent],
                         slot: SimTaxonomyEntryReference = None,
                         slot_extension: str = None) -> 'SimultanObject':

        if isinstance(subcomponent, SimComponent):
            comp_to_add = subcomponent
        elif isinstance(subcomponent, SimultanObject):
            comp_to_add = subcomponent._wrapped_obj
        else:
            comp_to_add = utils.create_mapped_python_object(subcomponent,
                                                            object_mapper=self._object_mapper,
                                                            data_model=self._data_model,
                                                            add_to_data_model=True)

        utils.add_sub_component(self._wrapped_obj,
                                comp_to_add,
                                slot_extension,
                                slot)

        return comp_to_add

    def remove_subcomponent(self, subcomponent: Union['SimultanObject', SimComponent]):
        if isinstance(subcomponent, SimComponent):
            utils.remove_sub_component(self._wrapped_obj, subcomponent)
        elif isinstance(subcomponent, SimultanObject):
            utils.remove_sub_component(self._wrapped_obj, subcomponent._wrapped_obj)
        else:
            raise TypeError(f'Unknown type for subcomponent: {type(subcomponent)}')

    def add_referenced_component(self,
                                 referenced_component: Union['SimultanObject', SimComponent],
                                 slot: SimTaxonomyEntryReference = None,
                                 slot_extension: str = None):

        referenced_wrapped_obj = referenced_component if isinstance(referenced_component,
                                                                    SimComponent) else referenced_component._wrapped_obj

        # logger.debug(f'Adding referenced component {referenced_component} to {self}')
        utils.add_referenced_component(self._wrapped_obj,
                                       referenced_wrapped_obj,
                                       slot_extension,
                                       slot)

    def remove_referenced_component(self, referenced_component: 'SimultanObject'):

        if isinstance(referenced_component, SimComponent):
            utils.remove_referenced_component(self._wrapped_obj, referenced_component)
        elif isinstance(referenced_component, SimultanObject):
            utils.remove_referenced_component(self._wrapped_obj, referenced_component._wrapped_obj)


    def add_asset(self,
                  resource_file_entry: 'ResourceFileEntry',
                  _id_contained: str = '') -> Asset:

        return ComponentMapping.AddAsset(self, resource_file_entry, _id_contained)

    def __repr__(self):
        return f'{self.name}: ' + object.__repr__(self)

    def associate(self, other: 'ExtendedBaseGeometry'):
        """
        Associate this object with another object
        :param other: fc_geometry object to associate with
        :return: None
        """
        other.associate(self)

    def get_raw_attr(self, attr: Optional[str] = None, text_or_key: Optional[str] = None):
        if attr is not None:
            content = self._taxonomy_map.get_content_by_property_name(attr)
            if content is None:
                raise KeyError(f'No content found for attribute {attr}')

            return utils.get_component_taxonomy_entry(self._wrapped_obj, content.text_or_key)

        if text_or_key is not None:
            return utils.get_component_taxonomy_entry(self._wrapped_obj, text_or_key)

    def set_attr_prop(self, attr: str, prop: str, value):
        """
        Set attribute of the mapped property

        Example:

        class TestComponent(object):
            def __init__(self, *args, **kwargs):
                self.value = kwargs.get('value')

        content0 = Content(text_or_key='value',  # text or key of the content/parameter/property
                           property_name='value',  # name of the generated property
                           type=float,  # type of the content/parameter/property
                           unit=None,  # unit of the content/parameter/property
                           documentation='value to test',
                           component_policy='subcomponent')

        test_component_map = TaxonomyMap(taxonomy_name='PySimultan',
                                         taxonomy_key='PySimultan',
                                         taxonomy_entry_name='TestComponent',
                                         taxonomy_entry_key='TestComponent',
                                         content=[content0]
                                         )

        mapper.register(test_component_map.taxonomy_entry_key, TestComponent, taxonomy_map=test_component_map)
        cls1 = mapper.get_mapped_class(test_component_map.taxonomy_entry_key)

        test_component = cls1(name='test_component',
                                value=None)

        test_component.set_attr_prop('value', 'MinValue, 0)
        test_component.set_attr_prop('value', 'MaxValue, 1)

        :param attr:
        :param value:
        :return:
        """
        comp_prop = utils.get_component_taxonomy_entry(self._wrapped_obj, attr)
        if comp_prop is not None:
            setattr(comp_prop, prop, value)
        return comp_prop

    def copy(self,
             name: str = None):
        """
        Create a copy of the object including all properties. The properties are copied by reference.
        :return:
        """
        new_copy = self.__class__(name=name if name is not None else f'Copy of {self.name}',
                                  data_model=self._data_model,
                                  object_mapper=self._object_mapper)

        for content in self._taxonomy_map.content:
            setattr(new_copy, content.property_name, getattr(self, content.property_name))

        # new_copy.name = name if name is not None else f'Copy of {self.name}'

        if self.associated_geometry:
            for geo in self.associated_geometry:
                new_copy.associate(geo)

        return new_copy

    def remove_from_datamodel(self):
        self._data_model.remove_component(self)
        self.__class__.cls_instances.remove(self)

    def to_json(self) -> dict:

        from .default_types import ComponentList, ComponentDictionary

        obj_dict = {
            str(self.id): {'name': self.name},
            'taxonomies': self.taxonomy_keys,
                    }

        for content in self._taxonomy_map.content:
            val = getattr(self, content.property_name)

            if hasattr(val, 'json_ref'):
                obj_dict[content.text_or_key] = val.json_ref()
            elif isinstance(val, (list, ComponentList)):
                obj_dict[content.text_or_key] = [v.json_ref() if hasattr(v, 'json_ref') else v for v in val]
            elif isinstance(val, (dict, ComponentDictionary)):
                obj_dict[content.text_or_key] = {k: v.json_ref() if hasattr(v, 'json_ref') else v for k, v in val.items()}
            elif isinstance(val, ndarray):
                obj_dict[content.text_or_key] = val.tolist()
            elif isinstance(val, DataFrame):
                obj_dict[content.text_or_key] = val.to_dict()
            else:
                obj_dict[content.text_or_key] = val

        return obj_dict

    def json_ref(self):
        return {"$ref": {
            "$type": 'Component',
            "$taxonomies": self.taxonomy_keys,
            "$id": {'local_id': self.id.LocalId,
                    'global_id': str(self.id.GlobalId)
                    }
        }
        }

    # def to_json(self):
    #
    #     super().to_json(self)

        # return {str(self.id): {'name': self.name}}
