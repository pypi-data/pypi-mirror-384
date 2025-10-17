from PySimultan2.src.PySimultan2.data_model import DataModel
from PySimultan2.src.PySimultan2.object_mapper import PythonMapper
from PySimultan2.src.PySimultan2.taxonomy_maps import TaxonomyMap, Content

import resources

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 importlib_resources.
    import importlib_resources as pkg_resources


with pkg_resources.path(resources, 'test_set_dictionary.simultan') as r_path:
    project_path = str(r_path)


data_model = DataModel.create_new_project(project_path=project_path,
                                          user_name='admin',
                                          password='admin')

mapper = PythonMapper()


def map_classes():
    class TestComponent(object):
        def __init__(self, *args, **kwargs):
            self.mapped_property = kwargs.get('mapped_property')
            self.value2 = kwargs.get('value2')

    content0 = Content(text_or_key='value',  # text or key of the content/parameter/property
                       property_name='mapped_property',  # name of the generated property
                       type=None,  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='mapped_property to test',
                       component_policy='subcomponent')

    content1 = Content(text_or_key='value2',  # text or key of the content/parameter/property
                       property_name='value2',  # name of the generated property
                       type=None,  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='value2',
                       component_policy='reference')

    test_component_map = TaxonomyMap(taxonomy_name='PySimultan',
                                     taxonomy_key='PySimultan',
                                     taxonomy_entry_name='TestComponent',
                                     taxonomy_entry_key='TestComponent',
                                     content=[content0, content1],
                                     )

    mapper.register(test_component_map.taxonomy_entry_key, TestComponent, taxonomy_map=test_component_map)
    cls1 = mapper.get_mapped_class(test_component_map.taxonomy_entry_key)

    test_component_map_2 = TaxonomyMap(taxonomy_name='PySimultan',
                                       taxonomy_key='PySimultan',
                                       taxonomy_entry_name='TestComponent2',
                                       taxonomy_entry_key='TestComponent2',
                                       content=[content0],
                                       )

    mapper.register(test_component_map_2.taxonomy_entry_key, TestComponent, taxonomy_map=test_component_map_2)
    cls2 = mapper.get_mapped_class(test_component_map_2.taxonomy_entry_key)

    return cls1, cls2


mapped_cls_1, mapped_cls_2 = map_classes()
component = mapped_cls_1(name='test_component',
                         mapped_property=None)


def test_set_dictionary_param(component):

    other_component = mapped_cls_2(name='other_component',
                                   mapped_property=None)
    other_component_2 = mapped_cls_2(name='other_component_2',
                                     mapped_property=None)
    other_component_3 = mapped_cls_2(name='other_component_3',
                                     mapped_property=None)
    other_component_4 = mapped_cls_2(name='other_component_4',
                                     mapped_property=None)

    new_test = mapped_cls_1(name='test_component_2',
                            mapped_property={'val_a': 1,
                                             'val_b': 2.0,
                                             'val_c': 'test',
                                             'val_d': True,
                                             'val_e': [other_component, other_component_2, other_component_3],
                                             'val_f': {'a': other_component_2, 'b': other_component_3},
                                             'val_g': None,
                                             'val_h': other_component,
                                             'val_i': other_component_4,
                                             })

    test_dict = {'val_a': 1,
                 'val_b': 2.0,
                 'val_c': 'test',
                 'val_d': True,
                 'val_e': [other_component, other_component_2, other_component_3],
                 'val_f': {'a': other_component_2, 'b': other_component_3},
                 'val_g': None,
                 'val_h': other_component,
                 'val_i': 5,
                 'val_j': new_test
                 }

    component.mapped_property = test_dict
    component.mapped_property['val_a'] = 222

    assert component.mapped_property['val_j'].mapped_property['val_a'] == 1
    component.mapped_property['val_j'].mapped_property._generate_internal_dict()

    component.mapped_property['val_i'] = other_component_4

    print(component.mapped_property)


def load_data_model(data_model: DataModel):
    data_model = DataModel(project_path=project_path,
                           user_name='admin',
                           password='admin')
    typed_data = data_model.get_typed_data(mapper=mapper,
                                           create_all=True)

    TestComponent = mapper.get_mapped_class('TestComponent')
    test_component = TestComponent.cls_instances[0]

    TestComponent2 = mapper.get_mapped_class('TestComponent2')
    other_component = next(x for x in TestComponent2.cls_instances if x.name == 'other_component')
    other_component_2 = next(x for x in TestComponent2.cls_instances if x.name == 'other_component_2')
    other_component_3 = next(x for x in TestComponent2.cls_instances if x.name == 'other_component_3')
    other_component_4 = next(x for x in TestComponent2.cls_instances if x.name == 'other_component_4')

    assert test_component.mapped_property['val_a'] == 222
    assert test_component.mapped_property['val_b'] == 2.0
    assert test_component.mapped_property['val_c'] == 'test'
    assert test_component.mapped_property['val_d'] is True
    assert test_component.mapped_property['val_g'] is None
    assert test_component.mapped_property['val_h'] == other_component
    assert len(test_component.mapped_property['val_e']) == 3
    assert test_component.mapped_property['val_e'][0] == other_component
    assert test_component.mapped_property['val_e'][1] == other_component_2
    assert test_component.mapped_property['val_e'][2] == other_component_3
    assert test_component.mapped_property['val_f']['a'] == other_component_2
    assert test_component.mapped_property['val_f']['b'] == other_component_3
    assert test_component.mapped_property['val_i'] == other_component_4

    return data_model


if __name__ == '__main__':
    test_set_dictionary_param(component)
    data_model.save()
    mapper.clear()
    data_model.cleanup()
    data_model = DataModel(project_path=project_path,
                           user_name='admin',
                           password='admin')
    load_data_model(data_model)


data_model.cleanup()
print('Test passed')
