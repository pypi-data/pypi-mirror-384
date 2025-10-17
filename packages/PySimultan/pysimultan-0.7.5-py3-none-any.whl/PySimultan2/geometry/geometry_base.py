import numpy as np

from numpy import array
from typing import Union, Optional
from weakref import WeakSet, WeakValueDictionary

from System import Array
from System.Collections.Generic import IEnumerable

from SIMULTAN.Data.Components import SimComponent, SimInstanceType

from SIMULTAN.Data.Geometry import (Layer, Vertex, Edge, PEdge, Face, Volume, EdgeLoop, OperationPermission,
                                    GeometryModelOperationPermissions, GeometryOperationPermissions,
                                    LayerOperationPermissions, GeometryModelData, GeometricOrientation,
                                    BaseEdgeContainer)

from SIMULTAN.Data.Geometry import FaceAlgorithms

from SIMULTAN.Data.Geometry import GeometryModel as NetGeometryModel

# from SIMULTAN.Utils import IDispatcherTimerFactory

from SIMULTAN.Data.SimMath import SimPoint3D

from SIMULTAN.Data.Geometry import FaceAlgorithms
from SIMULTAN.Data.Geometry import EdgeAlgorithms
from SIMULTAN.Data.Geometry import VolumeAlgorithms


# from ..utils import create_mapped_python_object, create_python_object
# from ..files import create_asset_from_file, FileInfo, create_asset_from_string
from .. import config
from .. import logger

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..simultan_object import SimultanObject
    from ..data_model import DataModel


class MetaMock(type):
    def __call__(cls, *args, **kwargs):
        wrapped_object = kwargs.get('wrapped_object', None)
        if wrapped_object is not None and hasattr(wrapped_object, 'Id'):
            obj = cls._cls_instances.get(wrapped_object.Id, None)
            if obj is not None:
                return obj

        obj = cls.__new__(cls)
        if wrapped_object is None:
            wrapped_object = obj.create_simultan_instance(*args, **kwargs)
        kwargs['wrapped_object'] = wrapped_object
        obj.__init__(*args, **kwargs)
        if hasattr(wrapped_object, 'Id'):
            cls._cls_instances[wrapped_object.Id] = obj
        return obj


class BaseGeometry(object, metaclass=MetaMock):

    associate_instance_type = getattr(SimInstanceType, 'None')

    def __init__(self, *args, **kwargs):
        self._wrapped_object: Union[Vertex, Edge, Face, Volume, EdgeLoop, Layer] = kwargs.get('wrapped_object', None)
        self._geometry_model: Optional[GeometryModel] = kwargs.get('geometry_model', None)
        self._object_mapper = kwargs.get('object_mapper', config.get_default_mapper())
        self._data_model = kwargs.get('data_model', None)

    @property
    def id(self):
        return self._wrapped_object.Id

    @property
    def components(self):
        return self.get_components()

    def get_components(self) -> list[Union[SimComponent, 'SimultanObject']]:
        if self._object_mapper is None:
            return list(self._geometry_model.Exchange.GetComponents(self._wrapped_object))
        else:
            return [self._object_mapper.create_python_object(x,
                                                             data_model=self._data_model) for x in list(
                self._geometry_model.Exchange.GetComponents(self._wrapped_object))]

    def associate(self, component: Union[SimComponent, 'SimultanObject']):
        wrapped_obj = component if isinstance(component, SimComponent) else component._wrapped_obj
        wrapped_obj.InstanceType = self.associate_instance_type
        self._geometry_model.Exchange.Associate(wrapped_obj, self._wrapped_object)

    def disassociate(self, component: Union[SimComponent, 'SimultanObject']):
        wrapped_obj = component if isinstance(component, SimComponent) else component._wrapped_obj
        self._geometry_model.Exchange.Disassociate(wrapped_obj, self._wrapped_object)


class classproperty(object):

    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


class SimultanLayer(BaseGeometry):

    _cls_instances = WeakValueDictionary()  # weak set with all created objects

    @classmethod
    def create_simultan_instance(cls, *args, **kwargs) -> 'SimultanLayer':
        """
        Create a new SimultanLayer instance and add to the fc_geometry model
        :keyword geometry_model: GeometryModel
        :keyword name: str
        :return: SimultanLayer
        """

        layer = Layer(kwargs.get('geometry_model').GeometryModelData,
                          kwargs.get('name', 'Layer'))
        geometry_model: GeometryModel = kwargs.get('geometry_model')
        geometry_model.add_layer(layer)
        return layer

    def __init__(self, *args, **kwargs):
        super(SimultanLayer, self).__init__(*args, **kwargs)

    @property
    def color(self):
        return self._wrapped_object.Color


class ExtendedBaseGeometry(BaseGeometry):

    def __init__(self, *args, **kwargs):
        super(ExtendedBaseGeometry, self).__init__(*args, **kwargs)
        self.layer = kwargs.get('layer', None)

    @property
    def name(self):
        return self._wrapped_object.Name

    @name.setter
    def name(self, value: str):
        self._wrapped_object.Name = value

    @property
    def layer(self):
        cls = self._object_mapper.registered_geometry_classes[Layer]
        return cls(wrapped_object=self._wrapped_object.Layer,
                   geometry_model=self._geometry_model,
                   object_mapper=self._object_mapper,
                   data_model=self._data_model)

    @layer.setter
    def layer(self, value: Union[SimultanLayer, Layer]):
        if value is None:
            return

        if isinstance(value, SimultanLayer):
            new_layer = value._wrapped_object
        else:
            new_layer = value

        if self._wrapped_object.Layer.Id != new_layer.Id:
            self._wrapped_object.Layer = new_layer

    def add_to_model(self):
        self._wrapped_object.AddToModel()

    def remove_from_model(self):
        self._wrapped_object.RemoveFromModel()


class SimultanVertex(ExtendedBaseGeometry):

    associate_instance_type = SimInstanceType.AttributesPoint
    _cls_instances = WeakValueDictionary()  # weak set with all created objects

    @classmethod
    def create_simultan_instance(cls, *args, **kwargs):
        k_pos: Optional[tuple[float, float, float]] = kwargs.get('position', None)
        if k_pos is not None:
            position = SimPoint3D(k_pos[0], k_pos[1], k_pos[2])
        else:
            position = SimPoint3D(kwargs.get('x', 0), kwargs.get('y', 0), kwargs.get('z', 0))

        # layer
        layer = kwargs.get('layer', None)
        if layer is None:
            layer = kwargs.get('geometry_model').default_layer

        if isinstance(layer, SimultanLayer):
            layer = layer._wrapped_object

        wrapped_object = Vertex(layer, kwargs.get('name', 'vertex'), position)
        return wrapped_object

    def __init__(self, *args, **kwargs):
        super(SimultanVertex, self).__init__(*args, **kwargs)
        if self._wrapped_object is None:
            self.x = kwargs.get('x', 0)
            self.y = kwargs.get('y', 0)
            self.z = kwargs.get('z', 0)

    @property
    def x(self):
        return self._wrapped_object.Position.X

    @x.setter
    def x(self, value: float):
        self._wrapped_object.Position.X = value

    @property
    def y(self):
        return self._wrapped_object.Position.Y

    @y.setter
    def y(self, value: float):
        self._wrapped_object.Position.Y = value

    @property
    def z(self):
        return self._wrapped_object.Position.Z

    @z.setter
    def z(self, value: float):
        self._wrapped_object.Position.Z = value

    @property
    def position(self):
        return (self._wrapped_object.Position.X,
                self._wrapped_object.Position.Y,
                self._wrapped_object.Position.Z)

    @position.setter
    def position(self, value: tuple[float, float, float]):
        self._wrapped_object.Position.X = value[0]
        self._wrapped_object.Position.Y = value[1]
        self._wrapped_object.Position.Z = value[2]

    def __repr__(self):
        return f"SimultanVertex {self.id} ({self.x}, {self.y}, {self.z})"


class SimultanEdge(ExtendedBaseGeometry):

    associate_instance_type = SimInstanceType.AttributesEdge
    _cls_instances = WeakValueDictionary()  # weak set with all created objects

    @classmethod
    def create_simultan_instance(cls, *args, **kwargs):
        # layer
        layer = kwargs.get('layer', None)
        if layer is None:
            layer = kwargs.get('geometry_model').default_layer

        if isinstance(layer, SimultanLayer):
            layer = layer._wrapped_object

        vertices = [x if isinstance(x, Vertex) else x._wrapped_object for x in kwargs.get('vertices', [])]

        wrapped_object = Edge(layer,
                              kwargs.get('name', 'vertex'),
                              IEnumerable[Vertex](Array[Vertex](vertices)))
        return wrapped_object

    def __init__(self, *args, **kwargs):
        super(SimultanEdge, self).__init__(*args, **kwargs)

    @property
    def length(self):
        return EdgeAlgorithms.Length(self._wrapped_object)

    @property
    def vertices(self):
        cls = self._object_mapper.registered_geometry_classes[Vertex]
        return [cls(wrapped_object=x,
                    geometry_model=self._geometry_model,
                    object_mapper=self._object_mapper,
                    data_model=self._data_model) for x in self._wrapped_object.Vertices]

    @property
    def vertex_0(self):
        cls = self._object_mapper.registered_geometry_classes[Vertex]
        return cls(wrapped_object=self._wrapped_object.Vertices[0],
                   geometry_model=self._geometry_model,
                   object_mapper=self._object_mapper,
                   data_model=self._data_model)

    @property
    def vertex_1(self):
        cls = self._object_mapper.registered_geometry_classes[Vertex]
        return cls(wrapped_object=self._wrapped_object.Vertices[1],
                   geometry_model=self._geometry_model,
                   object_mapper=self._object_mapper,
                   data_model=self._data_model)

    def __repr__(self):
        return f"SimultanEdge {self.id} ({self.vertex_0.id}, {self.vertex_1.id})"


class SimultanPEdge(ExtendedBaseGeometry):

    _cls_instances = WeakValueDictionary()  # weak set with all created objects

    @classmethod
    def create_simultan_instance(cls, *args, **kwargs):

        layer = kwargs.get('layer', None)
        if layer is None:
            layer = kwargs.get('geometry_model').default_layer
        if isinstance(layer, SimultanLayer):
            layer = layer._wrapped_object

        edge = kwargs.get('edge', None)
        edge = edge._wrapped_object if isinstance(edge, SimultanEdge) else edge

        free_id = kwargs.get('geometry_model').get_free_id()

        wrapped_object = PEdge(edge,
                               kwargs.get('geometric_orientation', GeometricOrientation.Undefined),
                               kwargs.get('base_edge_container', BaseEdgeContainer(free_id, layer))
                               )
        return wrapped_object

    @property
    def id(self):
        return self._wrapped_object.GetHashCode()

    def __init__(self, *args, **kwargs):
        super(SimultanPEdge, self).__init__(*args, **kwargs)

    @property
    def edges(self):
        return [SimultanEdge(wrapped_object=x,
                             geometry_model=self._geometry_model,
                             object_mapper=self._object_mapper,
                             data_model=self._data_model) for x in self._wrapped_object.Edges]


class SimultanEdgeLoop(ExtendedBaseGeometry):

    _cls_instances = WeakValueDictionary()  # weak set with all created objects

    @classmethod
    def create_simultan_instance(cls, *args, **kwargs):
        # layer
        layer = kwargs.get('layer', None)
        if layer is None:
            layer = kwargs.get('geometry_model').default_layer

        if isinstance(layer, SimultanLayer):
            layer = layer._wrapped_object

        edges = [x if isinstance(x, Edge) else x._wrapped_object for x in kwargs.get('edges', [])]

        wrapped_object = EdgeLoop(layer,
                                  kwargs.get('name', 'EdgeLoop'),
                                  IEnumerable[Edge](Array[Edge](edges))
                                  )
        return wrapped_object

    def __init__(self, *args, **kwargs):
        super(SimultanEdgeLoop, self).__init__(*args, **kwargs)

    @property
    def edges(self):
        cls = self._object_mapper.registered_geometry_classes[Edge]
        return [cls(wrapped_object=x.Edge,
                    geometry_model=self._geometry_model,
                    object_mapper=self._object_mapper,
                    data_model=self._data_model) for x in self._wrapped_object.Edges]

    @property
    def vertices(self) -> list[SimultanVertex]:
        vertices = []

        for edge in self.edges:
            vertices.append(edge.vertices[0])

        return vertices

    def __repr__(self):
        return f"SimultanEdgeLoop {self.id} ({[x.id for x in self.edges]})"


class SimultanFace(ExtendedBaseGeometry):

    associate_instance_type = SimInstanceType.AttributesFace
    _cls_instances = WeakValueDictionary()  # weak set with all created objects

    @classmethod
    def create_simultan_instance(cls, *args, **kwargs):
        layer = kwargs.get('layer', None)
        if layer is None:
            layer = kwargs.get('geometry_model').default_layer
        if isinstance(layer, SimultanLayer):
            layer = layer._wrapped_object

        edge_loop = kwargs.get('edge_loop', kwargs.get('boundary', None))
        edge_loop = edge_loop if isinstance(edge_loop, EdgeLoop) else edge_loop._wrapped_object

        holes = [x if isinstance(x, EdgeLoop) else x._wrapped_object for x in kwargs.get('holes', [])]
        if len(holes) > 0:
            holes = IEnumerable[EdgeLoop](Array[EdgeLoop](holes))
        else:
            holes = None

        wrapped_object = Face(layer,
                              kwargs.get('name', 'Face'),
                              edge_loop,
                              kwargs.get('geometric_orientation', GeometricOrientation.Forward),
                              holes)

        return wrapped_object

    def __init__(self, *args, **kwargs):
        super(SimultanFace, self).__init__(*args, **kwargs)

    @property
    def area(self) -> tuple[np.ndarray, np.ndarray]:
        return FaceAlgorithms.Area(self._wrapped_object)

    @property
    def boundary(self):
        cls = self._object_mapper.registered_geometry_classes[EdgeLoop]
        return cls(wrapped_object=self._wrapped_object.Boundary,
                   geometry_model=self._geometry_model,
                   object_mapper=self._object_mapper,
                   data_model=self._data_model)

    @property
    def holes(self) -> list[SimultanEdgeLoop]:
        cls = self._object_mapper.registered_geometry_classes[EdgeLoop]
        return [cls(wrapped_object=x,
                    geometry_model=self._geometry_model,
                    object_mapper=self._object_mapper,
                    data_model=self._data_model) for x in self._wrapped_object.Holes]

    @property
    def orientation(self):
        return self._wrapped_object.Orientation

    @property
    def normal(self):
        return array([self._wrapped_object.Normal.X,
                      self._wrapped_object.Normal.Y,
                      self._wrapped_object.Normal.Z])

    @property
    def stl(self):
        return self.create_stl_str()

    @property
    def vertices(self) -> list[SimultanVertex]:
        vertices = self.boundary_vertices
        for hole in self.holes:
            vertices.append(hole.vertices[0])
        return vertices

    @property
    def boundary_vertices(self) -> list[SimultanVertex]:
        vertices = []
        for edge in self.boundary.edges:
            vertices.append(edge.vertices[0])
        return vertices

    def triangulate(self):
        triangulation =FaceAlgorithms.Triangulate(self._wrapped_object, GeometricOrientation.Forward)
        vertices = np.array([(x.X, x.Y, x.Z) for x in triangulation.Item1])
        triangles = np.array(triangulation.Item3).reshape(int(triangulation.Item3.Count / 3), 3)

        return vertices, triangles

    def get_orientation_to_volume(self, volume: 'SimultanVolume') -> Optional[GeometricOrientation]:

        p_face = next((x for x in volume._wrapped_object.Faces if x.Face.Id is self._wrapped_object.Id), None)

        if p_face is None or p_face.Orientation == GeometricOrientation.Undefined:
            return None

        mul_1 = 1 if self.orientation == GeometricOrientation.Forward else -1
        mul_2 = 1 if p_face.Orientation == GeometricOrientation.Forward else -1

        return GeometricOrientation.Forward if mul_1 * mul_2 == 1 else GeometricOrientation.Backward

    def __repr__(self):
        return f"SimultanFace {self.id} ({self.boundary.id}, {[x.id for x in self.holes]})"


class SimultanVolume(ExtendedBaseGeometry):

    associate_instance_type = SimInstanceType.Entity3D
    _cls_instances = WeakValueDictionary()  # weak set with all created objects

    @classmethod
    def create_simultan_instance(cls, *args, **kwargs):
        layer = kwargs.get('layer', None)
        if layer is None:
            layer = kwargs.get('geometry_model').default_layer

        if isinstance(layer, SimultanLayer):
            layer = layer._wrapped_object

        faces = IEnumerable[Face](
            Array[Face]([x if isinstance(x, Face) else x._wrapped_object for x in kwargs.get('faces', [])]))

        wrapped_object = Volume(layer,
                                kwargs.get('name', 'Face'),
                                faces,
                                )

        return wrapped_object

    def __init__(self, *args, **kwargs):
        super(SimultanVolume, self).__init__(*args, **kwargs)

    @property
    def faces(self):

        face_cls = self._object_mapper.registered_geometry_classes[Face]
        return [face_cls(wrapped_object=x.Face,
                         geometry_model=self._geometry_model,
                         object_mapper=self._object_mapper,
                         data_model=self._data_model) for x in self._wrapped_object.Faces]

    @property
    def vertices(self):
        vertices = set()

        for face in self.faces:
            vertices.update(face.vertices)

        return vertices

    @property
    def area_brutto_netto(self):
        return VolumeAlgorithms.AreaBruttoNetto(self._wrapped_object)

    @property
    def volume(self):
        return VolumeAlgorithms.Volume(self._wrapped_object)

    def __repr__(self):
        return f"SimultanVolume {self.id} ({[x.id for x in self.faces]})"


class GeometryModel(object, metaclass=MetaMock):

    @classmethod
    def create_simultan_instance(cls, *args, **kwargs):

        data_model: DataModel = kwargs.get('data_model', config.get_default_data_model())
        name: str = kwargs.get('name', 'GeometryModel')

        new_geo_model, resource = data_model.create_new_geometry_model(name=name)
        data_model.project_data_manager.GeometryModels.AddGeometryModel(new_geo_model)
        data_model.models_dict[resource.Key] = new_geo_model
        data_model.save()

        return new_geo_model

    def __init__(self, *args, **kwargs):
        self._wrapped_object: NetGeometryModel = kwargs.get('wrapped_object', None)
        self._object_mapper = kwargs.get('object_mapper', config.get_default_mapper())
        self._data_model = kwargs.get('data_model', config.get_default_data_model())

    @property
    def name(self):
        return self._wrapped_object.Name

    @name.setter
    def name(self, value: str):
        self._wrapped_object.Name = value

    @property
    def key(self):
        if self.resource_file_entry is not None:
            return self.resource_file_entry.Key

    @property
    def layers(self):
        cls = self._object_mapper.registered_geometry_classes[Layer]
        return [cls(wrapped_object=x,
                    geometry_model=self,
                    object_mapper=self._object_mapper,
                    data_model=self._data_model) for x in list(self._wrapped_object.Geometry.Layers)]

    @property
    def default_layer(self):
        if self.layers:
            return self.layers[0]
        else:
            cls = self._object_mapper.registered_geometry_classes[Layer]
            cls(geometry_model=self,
                data_model=self._data_model,
                name='Default Layer')
        return self.layers[0]

    @property
    def vertices(self):
        cls = self._object_mapper.registered_geometry_classes[Vertex]
        return [cls(wrapped_object=x,
                    geometry_model=self,
                    object_mapper=self._object_mapper,
                    data_model=self._data_model) for x in self._wrapped_object.Geometry.Vertices]

    @property
    def edges(self):
        cls = self._object_mapper.registered_geometry_classes[Edge]
        return [cls(wrapped_object=x,
                    geometry_model=self,
                    object_mapper=self._object_mapper,
                    data_model=self._data_model) for x in self._wrapped_object.Geometry.Edges]

    @property
    def edge_loops(self):
        cls = self._object_mapper.registered_geometry_classes[EdgeLoop]
        return [cls(wrapped_object=x,
                    geometry_model=self,
                    object_mapper=self._object_mapper,
                    data_model=self._data_model) for x in self._wrapped_object.Geometry.EdgeLoops]

    @property
    def faces(self):
        cls = self._object_mapper.registered_geometry_classes[Face]
        return [cls(wrapped_object=x,
                    geometry_model=self,
                    object_mapper=self._object_mapper,
                    data_model=self._data_model) for x in self._wrapped_object.Geometry.Faces]

    @property
    def volumes(self):
        cls = self._object_mapper.registered_geometry_classes[Volume]
        return [cls(wrapped_object=x,
                    geometry_model=self,
                    object_mapper=self._object_mapper,
                    data_model=self._data_model) for x in self._wrapped_object.Geometry.Volumes]

    @property
    def resource_file_entry(self):
        return self._wrapped_object.File

    @property
    def geo_references(self):
        return self._wrapped_object.Geometry.GeoReferences

    @property
    def Exchange(self):
        return self._wrapped_object.Exchange

    @property
    def GeometryModelData(self):
        return self._wrapped_object.Geometry

    def add_layer(self, layer: Union[Layer, SimultanLayer]):
        if isinstance(layer, SimultanLayer):
            layer = layer._wrapped_object
        self._wrapped_object.Geometry.Layers.Add(layer)

    def get_geometry_by_id(self, geo_id):
        return self._wrapped_object.Geometry.GeometryFromId(geo_id)

    def get_layer_by_id(self, geo_id):
        return self._wrapped_object.Geometry.LayerFromId(geo_id)

    def get_free_id(self):
        return self._wrapped_object.Geometry.GetFreeId(True)
