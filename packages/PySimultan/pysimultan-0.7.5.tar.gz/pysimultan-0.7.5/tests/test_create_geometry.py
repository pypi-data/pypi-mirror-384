from PySimultan2.src.PySimultan2.data_model import DataModel

from PySimultan2.tests import resources
from PySimultan2.src.PySimultan2.geometry.geometry_base import (GeometryModel, SimultanLayer, SimultanVertex,
                                                                SimultanEdge, SimultanEdgeLoop, SimultanFace,
                                                                SimultanVolume)

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 importlib_resources.
    import importlib_resources as pkg_resources


with pkg_resources.path(resources, 'new_geometry_test.simultan') as r_path:
    project_path = str(r_path)


data_model = DataModel.create_new_project(project_path=project_path,
                                          user_name='admin',
                                          password='admin')


def create_geometry_model(name='new_geometry_test'):
    return GeometryModel(name=name,
                         data_model=data_model)


def test_create_layer(geo_model):
    new_layer = SimultanLayer(geometry_model=geo_model,
                              data_model=data_model,
                              name='new_layer')

    assert isinstance(new_layer, SimultanLayer)

    return new_layer


def create_vertex(layer, x, y, z, name, geo_model):
    new_vertex = SimultanVertex(geometry_model=geo_model,
                                x=x,
                                y=y,
                                z=z,
                                data_model=data_model,
                                name=name,
                                layer=layer)
    assert isinstance(new_vertex, SimultanVertex)
    return new_vertex


def create_edge(layer, vertices, name, geo_model):
    new_edge = SimultanEdge(geometry_model=geo_model,
                            data_model=data_model,
                            name=name,
                            layer=layer,
                            vertices=vertices)
    assert isinstance(new_edge, SimultanEdge)
    return new_edge


def create_edge_loop(layer, edges, name, geo_model):
    new_edge_loop = SimultanEdgeLoop(geometry_model=geo_model,
                                     data_model=data_model,
                                     name=name,
                                     layer=layer,
                                     edges=edges)
    assert isinstance(new_edge_loop, SimultanEdgeLoop)
    return new_edge_loop


def create_face(layer, edge_loop, name, geo_model):
    new_face = SimultanFace(geometry_model=geo_model,
                            data_model=data_model,
                            name=name,
                            layer=layer,
                            edge_loop=edge_loop)
    assert isinstance(new_face, SimultanFace)
    return new_face


def test_create_cube(layer, geo_model):
    # create a cube
    vertex_pos = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
                  (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]

    vertices = []
    for i, pos in enumerate(vertex_pos):
        vertices.append(create_vertex(layer,
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
        edges.append(create_edge(layer,
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
        edge_loops.append(create_edge_loop(layer,
                                           edge_loop_edge,
                                           'new_edge_loop_{}'.format(i),
                                           geo_model),
                          )

    # create faces
    faces = []
    for i, edge_loop in enumerate(edge_loops):
        faces.append(create_face(layer,
                                 edge_loop,
                                 'new_face_{}'.format(i),
                                 geo_model
                                 )
                     )

    # create a volume
    volume = SimultanVolume(geometry_model=geo_model,
                            data_model=data_model,
                            name='new_volume',
                            layer=layer,
                            faces=faces)

    assert isinstance(volume, SimultanVolume)


if __name__ == '__main__':
    geo_model = create_geometry_model(name='new_geometry_test')
    layer = test_create_layer(geo_model)
    test_create_cube(layer, geo_model)
    data_model.save()
    data_model.cleanup()
    print('All tests passed!')
