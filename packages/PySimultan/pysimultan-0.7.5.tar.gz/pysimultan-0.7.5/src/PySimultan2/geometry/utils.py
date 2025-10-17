from typing import List, Type, Union, Optional
from numpy import array
from .. import config
from .geometry_base import (GeometryModel, SimultanLayer, SimultanVertex, SimultanEdge, SimultanEdgeLoop, SimultanFace,
                            SimultanVolume, BaseGeometry)

from SIMULTAN.Data.Geometry import (Layer, Vertex, Edge, PEdge, Face, Volume, EdgeLoop, OperationPermission,
                                    GeometryModelOperationPermissions, GeometryOperationPermissions,
                                    LayerOperationPermissions, GeometryModelData, GeometricOrientation,
                                    BaseEdgeContainer)

from SIMULTAN.Data.Geometry import GeometryModel as NetGeometryModel


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..default_types import ComponentList
    from ..simultan_object import SimultanObject
    from ..data_model import DataModel
    from ..object_mapper import PythonMapper


python_map_dict = {Layer: SimultanLayer,
                   Vertex: SimultanVertex,
                   Edge: SimultanEdge,
                   EdgeLoop: SimultanEdgeLoop,
                   Face: SimultanFace,
                   Volume: SimultanVolume}


def create_python_geometry(cls,
                           sim_geometry: Union[Layer, Vertex, Edge, Face, Volume, EdgeLoop],
                           data_model: 'DataModel',
                           python_mapper: 'PythonMapper',
                           geometry_model: Union[GeometryModel, NetGeometryModel] = None,
                           ) -> Union[SimultanLayer, SimultanVertex, SimultanEdge, SimultanEdgeLoop, SimultanFace, SimultanVolume]:

    if isinstance(geometry_model, NetGeometryModel):
        geometry_model = GeometryModel(wrapped_object=geometry_model,
                                       data_model=data_model,
                                       python_mapper=python_mapper)

    if type(sim_geometry) in python_map_dict:
        if cls is None:
            cls = python_map_dict.get(type(sim_geometry))
        return cls(wrapped_object=sim_geometry,
                   data_model=data_model,
                   geometry_model=geometry_model,
                   python_mapper=python_mapper)
    else:
        raise ValueError(f'Could not create python object for {sim_geometry}')


def create_cube(data_model,
                geo_model: GeometryModel,
                obj_mapper: Optional['PythonMapper'] = None,
                scale: Optional[float] = 1):

    if obj_mapper is None:
        obj_mapper = config.get_default_mapper()

    new_layer = obj_mapper.registered_geometry_classes[Layer](geometry_model=geo_model,
                                                              data_model=data_model,
                                                              name='new_layer')

    def create_vertex(layer, x, y, z, name, geo_model):
        new_vertex = obj_mapper.registered_geometry_classes[Vertex](geometry_model=geo_model,
                                                                    x=x,
                                                                    y=y,
                                                                    z=z,
                                                                    data_model=data_model,
                                                                    name=name,
                                                                    layer=layer)
        assert isinstance(new_vertex, SimultanVertex)
        return new_vertex

    def create_edge(layer, vertices, name, geo_model):
        new_edge = obj_mapper.registered_geometry_classes[Edge](geometry_model=geo_model,
                                                                data_model=data_model,
                                                                name=name,
                                                                layer=layer,
                                                                vertices=vertices)
        assert isinstance(new_edge, SimultanEdge)
        return new_edge

    def create_edge_loop(layer, edges, name, geo_model):
        new_edge_loop = obj_mapper.registered_geometry_classes[EdgeLoop](geometry_model=geo_model,
                                                                         data_model=data_model,
                                                                         name=name,
                                                                         layer=layer,
                                                                         edges=edges)
        assert isinstance(new_edge_loop, SimultanEdgeLoop)
        return new_edge_loop

    def create_face(layer, edge_loop, name, geo_model):
        new_face = obj_mapper.registered_geometry_classes[Face](geometry_model=geo_model,
                                                                data_model=data_model,
                                                                name=name,
                                                                layer=layer,
                                                                edge_loop=edge_loop)
        assert isinstance(new_face, SimultanFace)
        return new_face

    # create a cube
    vertex_pos = array([(0, 0, 0), (0.707, 0.707, 0), (0, 1.414, 0), (-0.707, 0.707, 0),
                        (0, 0, 1), (0.707, 0.707, 1), (0, 1.414, 1), (-0.707, 0.707, 1)]) * scale

    vertices = []
    for i, pos in enumerate(vertex_pos.tolist()):
        vertices.append(create_vertex(new_layer,
                                      *pos,
                                      'new_vertex_{}'.format(i),
                                      geo_model
                                      )
                        )

    edges_vertices = [(vertices[0], vertices[1]),
                      (vertices[1], vertices[2]),
                      (vertices[2], vertices[3]),
                      (vertices[3], vertices[0]),
                      (vertices[4], vertices[5]),
                      (vertices[5], vertices[6]),
                      (vertices[6], vertices[7]),
                      (vertices[7], vertices[4]),
                      (vertices[0], vertices[4]),
                      (vertices[1], vertices[5]),
                      (vertices[2], vertices[6]),
                      (vertices[3], vertices[7])
                      ]
    edges = []

    for i, edge_vertices in enumerate(edges_vertices):
        edges.append(create_edge(new_layer,
                                 edge_vertices,
                                 'new_edge_{}'.format(i),
                                 geo_model
                                 ))

    # create 6 edge loops as boundary for the cube
    edge_loop_edges = [
        # Front face loop
        [edges[0], edges[1], edges[2], edges[3]],
        # Back face loop
        [edges[4], edges[5], edges[6], edges[7]],
        # Top face loop
        [edges[1], edges[10], edges[5], edges[9]],
        # Bottom face loop
        [edges[3], edges[11], edges[7], edges[8]],
        # Left face loop
        [edges[0], edges[9], edges[4], edges[8]],
        # Right face loop
        [edges[2], edges[11], edges[6], edges[10]]
    ]

    edge_loops = []
    for i, edge_loop_edge in enumerate(edge_loop_edges):
        edge_loops.append(create_edge_loop(new_layer,
                                           edge_loop_edge,
                                           'new_edge_loop_{}'.format(i),
                                           geo_model),
                          )

    # create faces
    faces = []
    for i, edge_loop in enumerate(edge_loops):
        faces.append(create_face(new_layer,
                                 edge_loop,
                                 'new_face_{}'.format(i),
                                 geo_model
                                 )
                     )

    # create a volume

    volume = obj_mapper.registered_geometry_classes[Volume](geometry_model=geo_model,
                                                            data_model=data_model,
                                                            name='new_volume',
                                                            layer=new_layer,
                                                            faces=faces)

    return volume
