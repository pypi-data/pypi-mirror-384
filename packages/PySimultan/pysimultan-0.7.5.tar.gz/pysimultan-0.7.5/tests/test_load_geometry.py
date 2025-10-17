from PySimultan2.data_model import DataModel

from PySimultan2.tests import resources
from PySimultan2.geometry.geometry_base import (GeometryModel, SimultanLayer, SimultanVertex, SimultanEdge,
                                                    SimultanEdgeLoop, SimultanFace, SimultanVolume)

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 importlib_resources.
    import importlib_resources as pkg_resources


with pkg_resources.path(resources, 'U5.simultan') as r_path:
    project_path = str(r_path)

data_model = DataModel(project_path=project_path,
                       user_name='admin',
                       password='admin')

geo_model = GeometryModel(wrapped_object=data_model.models[list(data_model.models.keys())[-1]],
                          data_model=data_model)
faces = geo_model.faces

# new_geo_model = GeometryModel(filename='new_geo.simgeo')


def test_create_layer():

    layer = SimultanLayer(geometry_model=geo_model,
                          data_model=data_model,
                          name='new_layer')

    assert isinstance(layer, SimultanLayer)

    return layer


def create_vertex(layer, x, y, z, name):
    new_vertex = SimultanVertex(geometry_model=geo_model,
                                x=x,
                                y=y,
                                z=z,
                                data_model=data_model,
                                name=name,
                                layer=layer)
    assert isinstance(new_vertex, SimultanVertex)
    return new_vertex


def create_edge(layer, vertices, name):
    new_edge = SimultanEdge(geometry_model=geo_model,
                            data_model=data_model,
                            name=name,
                            layer=layer,
                            vertices=vertices)
    assert isinstance(new_edge, SimultanEdge)
    return new_edge


def create_edge_loop(layer, edges, name):
    new_edge_loop = SimultanEdgeLoop(geometry_model=geo_model,
                                     data_model=data_model,
                                     name=name,
                                     layer=layer,
                                     edges=edges)
    assert isinstance(new_edge_loop, SimultanEdgeLoop)
    return new_edge_loop


def create_face(layer, edge_loop, name):
    new_face = SimultanFace(geometry_model=geo_model,
                            data_model=data_model,
                            name=name,
                            layer=layer,
                            edge_loop=edge_loop)
    assert isinstance(new_face, SimultanFace)
    return new_face


def test_create_cube(layer):
    # create a cube
    vertex_pos = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
                  (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]

    vertices = []
    for i, pos in enumerate(vertex_pos):
        vertices.append(create_vertex(layer, *pos, 'new_vertex_{}'.format(i)))

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
        edges.append(create_edge(layer, edge_vertices, 'new_edge_{}'.format(i)))

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
        edge_loops.append(create_edge_loop(layer, edge_loop_edge, 'new_edge_loop_{}'.format(i)))

    # create faces
    faces = []
    for i, edge_loop in enumerate(edge_loops):
        faces.append(create_face(layer, edge_loop, 'new_face_{}'.format(i)))

    # create a volume
    volume = SimultanVolume(geometry_model=geo_model,
                            data_model=data_model,
                            name='new_volume',
                            layer=layer,
                            faces=faces)

    assert isinstance(volume, SimultanVolume)


if __name__ == '__main__':
    layer = test_create_layer()
    test_create_cube(layer)
    data_model.save()
    data_model.cleanup()
    print('All tests passed!')
