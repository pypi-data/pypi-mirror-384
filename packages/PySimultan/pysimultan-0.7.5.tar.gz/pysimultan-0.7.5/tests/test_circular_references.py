from PySimultan2.src.PySimultan2 import DataModel
from PySimultan2.src.PySimultan2 import PythonMapper
from PySimultan2.src.PySimultan2.taxonomy_maps import TaxonomyMap, Content

from PySimultan2.tests import resources

try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources

with pkg_resources.path(resources, 'new_geometry_test.simultan') as r_path:
    project_path = str(r_path)


def create_classes() -> tuple[dict[str, type], PythonMapper]:

    class Class1(object):
        def __init__(self, *args, **kwargs):
            self.temperature = kwargs.get('temperature', 125.15)
            self.obj_1 = kwargs.get('obj_1', None)
            self.attr_name_test = kwargs.get('attr_name_test', None)

    class Class2(object):
        def __init__(self, *args, **kwargs):
            self.temperature = kwargs.get('temperature', 225.15)
            self.obj_1 = kwargs.get('obj_1', None)

    class Class3(object):
        def __init__(self, *args, **kwargs):
            self.temperature = kwargs.get('temperature', 325.15)
            self.obj_1 = kwargs.get('obj_1', None)

    cls_dict = {'Class1': Class1,
                'Class2': Class2,
                'Class3': Class3,
                }

    return cls_dict


def create_mapped_classes(classes: dict[str, type]) -> dict[str, type]:
    mapper = PythonMapper()

    def create_contents() -> dict[str, Content]:
        contents = {}

        contents['temperature'] = Content(text_or_key='temperature',
                                                   property_name='temperature',
                                                   type=None,
                                                   unit='K',
                                                   documentation='temperature in K')

        contents['obj_1'] = Content(text_or_key='obj_1',
                                    property_name='obj_1',
                                    type=None,
                                    unit=None,
                                    documentation='obj_1')

        contents['obj_2'] = Content(text_or_key='obj_2',
                                    property_name='obj_2',
                                    type=None,
                                    unit=None,
                                    documentation='obj_2')

        contents['attr_name_test'] = Content(text_or_key='obj_3',
                                             property_name='attr_name_test',
                                             type=None,
                                             unit=None,
                                             documentation='obj_3/attr_name_test')

        return contents

    def create_mapped_cls_1(cls, contents: dict[str, Content]):
        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='Class1',
                              taxonomy_entry_key='Class1',
                              content=[contents['temperature'],
                                       contents['obj_1'],
                                       contents['attr_name_test'],
                                       ],
                              )

        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    def create_mapped_cls_2(cls, contents: dict[str, Content]):
        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='Class2',
                              taxonomy_entry_key='Class2',
                              content=[contents['temperature'],
                                       contents['obj_1']],
                              )

        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    def create_mapped_cls_3(cls, contents: dict[str, Content]):
        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='Class3',
                              taxonomy_entry_key='Class3',
                              content=[contents['temperature'],
                                       contents['obj_1']],
                              )

        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    tax_contents = create_contents()

    mapped_cls_1 = create_mapped_cls_1(classes['Class1'], tax_contents)
    mapped_cls_2 = create_mapped_cls_2(classes['Class2'], tax_contents)
    mapped_cls_3 = create_mapped_cls_3(classes['Class3'], tax_contents)

    mapped_cls_dict = {'Class1': mapped_cls_1,
                       'Class2': mapped_cls_2,
                       'Class3': mapped_cls_3}

    return mapped_cls_dict, mapper


def create_model():
    data_model = DataModel.create_new_project(project_path=project_path,
                                              user_name='admin',
                                              password='admin')
    classes = create_classes()
    mapped_classes, mapper = create_mapped_classes(classes)

    class_1 = mapped_classes['Class1']
    class_2 = mapped_classes['Class2']
    class_3 = mapped_classes['Class3']

    obj_1 = class_1(temperature=125.15,
                    attr_name_test=15)
    obj_2 = class_2(temperature=225.15, obj_1=obj_1)
    obj_3 = class_3(temperature=325.15, obj_1=obj_2)

    assert obj_1.attr_name_test == 15

    raw_attr = obj_1.get_raw_attr('attr_name_test')
    raw_attr.set_Value(25)

    assert obj_1.attr_name_test == 25

    obj_1.obj_1 = obj_2

    data_model.save()

    data_model.cleanup()
    mapper.clear()


def load_model():
    mapped_cls_dict, mapper = create_mapped_classes(create_classes())

    # create copy of the mapper to test mapper.copy
    mapper_copy = mapper.copy()
    data_model = DataModel(project_path=project_path,
                           user_name='admin',
                           password='admin')
    typed_data = data_model.get_typed_data(mapper=mapper_copy, create_all=True)
    class_1 = mapper.get_mapped_class('Class1')
    obj_1 = list(class_1._cls_instances_dict.values())[0]
    assert obj_1.obj_1.obj_1 is obj_1
    return typed_data


if __name__ == '__main__':
    create_model()
    typed_data = load_model()
