from typing import Optional, Type, TYPE_CHECKING, Union, Any, Dict, List
from copy import copy
from collections import UserList
from colorlog import getLogger
from weakref import WeakSet

from . import config
from .utils import create_python_object, add_properties
from .default_types import ComponentList, component_list_map, ComponentDictionary, component_dict_map

from .simultan_object import SimultanObject
from .geometry.utils import create_python_geometry

from SIMULTAN.Data.Geometry import (Layer, Vertex, Edge, PEdge, Face, Volume, EdgeLoop)
from SIMULTAN.Data.Components import SimComponent
from SIMULTAN.Data import SimId
from .geometry.geometry_base import (SimultanLayer, SimultanVertex, SimultanEdge, SimultanEdgeLoop, SimultanFace,
                                     SimultanVolume)

from .taxonomy_maps import TaxonomyMap, Content

if TYPE_CHECKING:
    from .data_model import DataModel

logger = getLogger('PySimultan')

default_registered_classes = {'ComponentList': ComponentList,
                              'ComponentDict': ComponentDictionary}
default_mapped_classes = {}
default_taxonomy_maps = {'ComponentList': component_list_map,
                         'ComponentDict': component_dict_map}


class PythonMapper(object):

    mappers = {}

    def __new__(cls, *args, **kwargs):
        instance = super(PythonMapper, cls).__new__(cls)
        config.set_default_mapper(instance)

        if kwargs.get('add_to_mappers', True):
            initial_module_name = kwargs.get('module', 'unknown_module')
            module_name = initial_module_name
            i = 0
            while module_name in cls.mappers.keys():
                module_name = f'{initial_module_name}_{i}'
                i+=1
            cls.mappers[module_name] = instance

        return instance

    def __init__(self, *args, **kwargs):

        self._mapped_classes = {}

        self.name = kwargs.get('name', 'PythonMapper')
        self._module = kwargs.get('module', 'unknown_module')
        self.submodules = kwargs.get('submodules', {})

        self.registered_classes: dict[str: SimultanObject] = copy(default_registered_classes)  # dict with all registered classes: {taxonomy: class}

        self.undefined_registered_classes: dict[str: SimultanObject] = {}  # dict with all registered classes: {taxonomy: class}

        self.mapped_classes = copy(default_mapped_classes)  # dict with all mapped classes: {taxonomy: class}
        self.taxonomy_maps = copy(default_taxonomy_maps)  # dict with all taxonomie maps: {taxonomy: taxonomie_map}

        self.registered_geometry_classes = {Layer: SimultanLayer,
                                            Vertex: SimultanVertex,
                                            Edge: SimultanEdge,
                                            Face: SimultanFace,
                                            Volume: SimultanVolume,
                                            EdgeLoop: SimultanEdgeLoop}

        self.re_register = False
        self.load_undefined = False

        self.default_components: List[Any] = []

    @property
    def module(self):
        return self._module

    @module.setter
    def module(self, value):
        if self._module != value:
            del self.mappers[self._module]

        self._module = value
        self.mappers[value] = self

    @property
    def mapped_classes(self):
        if len(self.registered_classes) > len(self._mapped_classes):
            for taxonomy in self.registered_classes.keys():
                if self._mapped_classes.get(taxonomy, None) is None:
                    self.create_mapped_class(taxonomy, self.registered_classes[taxonomy])

        return self._mapped_classes

    @mapped_classes.setter
    def mapped_classes(self, value):
        self._mapped_classes = value

    def register(self,
                 taxonomy: str,
                 cls: Type[Any],
                 taxonomy_map: TaxonomyMap,
                 re_register: bool = True,
                 update_in_other_mappers: bool = False):

        # print(f'Registering {taxonomy} with {cls} {hash(cls)}')

        if not (self.re_register or re_register) and taxonomy in self.registered_classes.keys():
            return

        if taxonomy in self.mapped_classes.keys():
            try:
                del self.mapped_classes[taxonomy]
            except KeyError:
                pass

        if taxonomy_map is None:
            taxonomy_map = TaxonomyMap(taxonomy_name='PySimultan',
                                       taxonomy_key='PySimultan',
                                       taxonomy_entry_name=taxonomy,
                                       taxonomy_entry_key=taxonomy)

        self.registered_classes[taxonomy] = cls
        self.taxonomy_maps[taxonomy] = taxonomy_map

        if update_in_other_mappers:
            self.update_from_other_mappers()

        return self.get_mapped_class(taxonomy)

    def update_from_other_mappers(self):
        for mapper in self.mappers.values():
            if mapper is not self:
                for cls, taxonomy in mapper.registered_classes.items():
                    if cls in self.registered_classes.values():
                        key = list(filter(lambda x: mapper.registered_classes[x] == cls,
                                          mapper.registered_classes)
                                   )[0]
                        mapper.registered_classes[key] = cls

    def update_from_submodules(self):
        for submodule in self.submodules.values():
            self.registered_classes.update(submodule.registered_classes)
            self.taxonomy_maps.update(submodule.taxonomy_maps)
            self.registered_geometry_classes.update(submodule.registered_geometry_classes)

    def create_mapped_class(self,
                            taxonomy: str,
                            cls: Any):

        if any([issubclass(cls, x) for x in (SimultanObject, UserList)]):
            bases = (cls,)
        else:
            bases = (SimultanObject,) + (cls,)

        def new_init(self, *args, **kwargs):
            for base in self.__class__.__bases__:
                base.__init__(self, *args, **kwargs)

        new_class_dict = {'__init__': new_init,
                          '__name__': cls.__name__,
                          '_taxonomy': taxonomy,
                          '_cls_instances': WeakSet(),
                          '_taxonomy_map': self.taxonomy_maps.get(taxonomy, None),
                          '_base': bases,
                          '_original_cls': cls,
                          '_object_mapper': self}

        new_class_dict.update(self.get_properties(taxonomy))
        new_class = type(cls.__name__, bases, new_class_dict)

        self._mapped_classes[taxonomy] = new_class

        return new_class

    def get_mapped_class(self, taxonomy) -> Type[SimultanObject]:
        if self.mapped_classes.get(taxonomy, None) is None:
            self.create_mapped_class(taxonomy, self.registered_classes[taxonomy])

        return self.mapped_classes.get(taxonomy, None)

    def get_typed_data(self,
                       data_model: 'DataModel' = None,
                       component_list: List[SimComponent] = None,
                       create_all: bool = False):

        typed_data = []

        if component_list is None:
            component_list = list(data_model.data.Items)

        if data_model is None:
            data_model = config.get_default_data_model()

        if create_all:
            new_component_list = set()

            def get_subcomponents(sim_component: Union[SimComponent, SimultanObject]):
                new_subcomponents = set()
                if isinstance(sim_component, SimultanObject):
                    sim_component = sim_component._wrapped_obj

                if sim_component in new_component_list:
                    return
                else:
                    new_component_list.add(sim_component)

                if sim_component is None:
                    return []

                for sub_component in sim_component.Components.Items:
                    if sub_component is None:
                        continue
                    new_subcomponents.add(sub_component.Component)
                for ref_component in sim_component.ReferencedComponents.Items:
                    if ref_component is None:
                        continue
                    new_subcomponents.add(ref_component.Target)

                for new_subcomponent in new_subcomponents:
                    get_subcomponents(new_subcomponent)

                new_component_list.update(new_subcomponents)

            for component in component_list:
                if component is None:
                    continue
                get_subcomponents(component)
            component_list = list(new_component_list)

        for component in component_list:
            typed_object = self.create_python_object(component, data_model=data_model)
            if typed_object is not None:
                typed_data.append(typed_object)

        if create_all:
            self.create_default_components(data_model)

        return typed_data

    def create_default_components(self, data_model: 'DataModel'):
        for instance in self.default_components:
            key = list(filter(lambda x: self.registered_classes[x] == type(instance),
                              self.registered_classes)
                       )[0]
            cls = self.get_mapped_class(key)
            if not cls.cls_instances:
                self.create_mapped_python_object(obj=instance,
                                                 data_model=data_model)
            else:
                # check if default instance is already in data model
                if not any([x.name == instance.name for x in cls.cls_instances]):
                    self.create_mapped_python_object(obj=instance,
                                                     data_model=data_model)

    def create_python_geometry_object(self,
                                      component: Union[Layer, Vertex, Edge, PEdge, Face, Volume, EdgeLoop],
                                      data_model: 'DataModel' = None,
                                      *args,
                                      **kwargs):

        if component is None:
            return None

        if data_model is None:
            logger.warning(f'No data model provided. Using default data model: {config.get_default_data_model().id}.')
            data_model = config.get_default_data_model()

        if isinstance(component, (Layer, Vertex, Edge, PEdge, Face, Volume, EdgeLoop)):
            if isinstance(component, Layer):
                geometry_model = component.Model.Model
            else:
                geometry_model = component.Layer.Model.Model
            cls = self.registered_geometry_classes[type(component)]
            return create_python_geometry(cls, component, data_model, self, geometry_model)
        else:
            self.create_python_object(component, data_model, *args, **kwargs)

    def get_mapped_class_from_component(self,
                                        component: Union[SimComponent, Layer, Vertex, Edge, PEdge, Face, Volume, EdgeLoop],
                                        data_model: Optional['DataModel'] = None,
                                        *args,
                                        **kwargs) -> Optional[Type[SimultanObject]]:
        if component is None:
            return None

        if data_model is None:
            logger.warning(f'No data model provided. Using default data model: {config.get_default_data_model().id}.')
            data_model = config.get_default_data_model()

        if isinstance(component,
                      (Layer, Vertex, Edge, PEdge, Face, Volume, EdgeLoop)
                      ):
            self.create_python_geometry_object(component,
                                               data_model,
                                               *args,
                                               **kwargs)

        c_slots = [x.Target.Key for x in component.Slots.Items]
        c_slot = list(set(c_slots) & set(self.registered_classes.keys()))
        if len(c_slot) == 0:
            if c_slots[0] not in self.registered_classes.keys() and self.load_undefined:

                def new_init(self, *args, **kwargs):
                    """
                    Init method for undefined classes
                    :param self:
                    :param args:
                    :param kwargs:
                    :return:
                    """
                    pass

                new_cls = type(c_slots[0],
                               (object,),
                               {'__init__': new_init}
                               )

                self.register(c_slots[0], new_cls)
                c_slot = [c_slots[0]]
                self.undefined_registered_classes[c_slot[0]] = new_cls
                # self.create_mapped_class(c_slot[0], self.registered_classes[c_slot[0]])
            elif c_slots[0] not in self.registered_classes.keys() and not self.load_undefined:
                logger.debug(f'Component {component} has no registered taxonomy: {c_slots}')
                return
        elif len(c_slot) > 1:
            num_superclasses = [len(self.registered_classes[x].__mro__) for x in c_slot]
            c_slot = [c_slot[num_superclasses.index(max(num_superclasses))]]

        if c_slot[0] not in self.mapped_classes.keys():
            self.create_mapped_class(c_slot[0], self.registered_classes[c_slot[0]])

        cls = self.mapped_classes[c_slot[0]]

        return cls

    # @lru_cache(maxsize=500)
    def create_python_object(self, component, cls=None, data_model=None, *args, **kwargs) -> Optional[SimultanObject]:

        if cls is None:
            cls = self.get_mapped_class_from_component(component,
                                                       data_model,
                                                       *args, **kwargs)

        if cls is None:
            return None

        if component is not None and component.Id in cls._cls_instances_dict.keys():
            return cls._cls_instances_dict[component.Id]
        else:
            return create_python_object(component,
                                        cls,
                                        object_mapper=self,
                                        data_model=data_model,
                                        *args,
                                        **kwargs)

    def create_mapped_python_object(self,
                                    obj: Any,
                                    data_model=None,
                                    add_to_data_model=True,
                                    *args,
                                    **kwargs) -> Optional[SimultanObject]:

        from .utils import create_mapped_python_object
        return create_mapped_python_object(obj,
                                           object_mapper=self,
                                           data_model=data_model,
                                           add_to_data_model=add_to_data_model,
                                           *args,
                                           **kwargs)

    def get_typed_data_with_taxonomy(self, taxonomy: str, data_model=None, first=False):

        tax_components = data_model.find_components_with_taxonomy(taxonomy=taxonomy, first=first)
        return self.get_typed_data(component_list=tax_components)

    def get_properties(self, taxonomy):

        prop_dict = {}
        taxonomy_map = self.taxonomy_maps.get(taxonomy, None)

        if taxonomy_map is None:
            return prop_dict

        for prop in taxonomy_map.content:

            prop_dict[prop.property_name] = add_properties(prop_name=prop.property_name,
                                                           text_or_key=prop.text_or_key,
                                                           content=prop,
                                                           taxonomy_map=taxonomy_map,
                                                           taxonomy=taxonomy)

        return prop_dict

    def clear(self, remove_from_default=False):
        for cls in self.registered_classes.values():
            cls._cls_instances = set()

        for cls in self.mapped_classes.values():
            cls._cls_instances = set()
            cls.__property_cache__ = {}

        if remove_from_default and config.get_default_mapper() is self:
            config.set_default_mapper(None)

    def create_sim_component(self,
                             obj,
                             data_model: 'DataModel'):
        from . utils import create_mapped_python_object
        new_val = create_mapped_python_object(obj, self, data_model)
        return new_val

    def copy(self,
             *args,
             **kwargs) -> 'PythonMapper':

        orig_new_module_name = kwargs.get('module', self.module)
        new_module_name = orig_new_module_name
        i = 0
        while new_module_name in self.mappers.keys():
            new_module_name = f'copy_{i}_of_{new_module_name}'
            i+=1

        new_mapper = PythonMapper(add_to_mappers=kwargs.get('add_to_mappers', True),
                                  module=new_module_name)
        new_mapper.registered_classes = self.registered_classes
        new_mapper.taxonomy_maps = self.taxonomy_maps
        new_mapper.registered_geometry_classes = self.registered_geometry_classes
        new_mapper.load_undefined = self.load_undefined
        new_mapper.default_components = self.default_components

        return new_mapper

    def __add__(self, other: 'PythonMapper') -> 'PythonMapper':
        # new_mapper = self.copy(add_to_mappers=True)
        self.submodules[other.module] = other
        self.submodules.update(other.submodules)
        self.registered_classes.update(other.registered_classes)
        self.taxonomy_maps.update(other.taxonomy_maps)
        self.registered_geometry_classes.update(other.registered_geometry_classes)
        self.default_components.extend(other.default_components)
        return self

    def get_mapped_class_for_python_type(self, python_type: type) -> Optional[Type[SimultanObject]]:
        try:
            key = list(filter(lambda x: self.registered_classes[x] == python_type,
                              self.registered_classes)
                       )[0]
            mapped_cls = self.get_mapped_class(key)
            return mapped_cls
        except IndexError:
            return None

    def get_mapped_object_by_id(self,
                                component_id: Union[SimId, int],
                                data_model: 'DataModel',
                                search_subcomponents: bool = True) -> Optional[SimultanObject]:

        component = data_model.get_component_by_id(component_id, search_subcomponents=search_subcomponents)
        if component is None:
            logger.error(f'Component with id {id} not found in the data model')
            return None
        typed_object = self.create_python_object(component, data_model=data_model)
        return typed_object

    def __repr__(self):
        return f'PythonMapper(module={self.module}, {len(self.registered_classes)} registered classes)'


if config.get_default_mapper() is None:
    config.set_default_mapper(PythonMapper(module='default'))


def register(taxonomy: str,
             taxonomy_map: TaxonomyMap,
             re_register=True,
             module: str = 'unknown_module') -> Any:

    if module not in PythonMapper.mappers.keys():
        PythonMapper(module=module)

    mapper = PythonMapper.mappers[module]

    def decorator(cls):
        mapper.register(taxonomy,
                        cls,
                        re_register=re_register,
                        taxonomy_map=taxonomy_map)
        return cls

    return decorator
