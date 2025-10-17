import os
from PySimultan2.src.PySimultan2 import DataModel, TaxonomyMap, Content, PythonMapper
from PySimultan2.src.PySimultan2.files import FileInfo, DirectoryInfo


project_dir = os.environ.get('PROJECT_DIR', '/simultan_projects')
if not os.path.exists(project_dir):
    os.makedirs(project_dir)


def test_files_and_directory_creation():
    new_data_model = DataModel.create_new_project(project_path=os.path.join(project_dir, 'test_dir_files.simultan'),
                                                  user_name='admin',
                                                  password='admin')

    print(new_data_model.file_directories)


    new_directory_info = DirectoryInfo(path='directory_info_dir',
                                       data_model=new_data_model)


    new_directory_info = DirectoryInfo(path='not_existing_dir/directory_to_create',
                                       data_model=new_data_model)


    print(new_data_model.file_directories)

    print(new_directory_info.resource_entry)
    print(new_directory_info.parent)

    new_file1 = new_directory_info.add_file('test_add_file.txt', 'This is a test file')
    new_file2 = new_directory_info.add_file('test_add_file2.txt')

    sub_directory_info = new_directory_info.add_sub_directory('sub_dir')
    print(sub_directory_info.parent)

    print(new_directory_info.sub_directories)


    new_directory = new_data_model.create_resource_directory('test_dir')
    new_directory2 = new_data_model.create_resource_directory('test_dir2')
    new_directory4 = new_data_model.create_resource_directory('test_dir3')

    new_data_model.add_empty_resource(filename=os.path.join(new_directory.CurrentFullPath, 'test_empty_file.txt'))

    new_data_model.add_empty_resource(filename='test_empty_file2.txt',
                                      target_dir=new_directory)

    new_file_info0 = FileInfo.from_string(filename='test_file.txt',
                                          content='This is a test file',
                                          data_model=new_data_model)

    new_file_info = FileInfo.from_string(filename='test_file.txt',
                                         content='This is a test file',
                                         target_dir=new_directory,
                                         data_model=new_data_model)

    new_file_info2 = FileInfo.from_string(filename='test_file2.txt',
                                         content='This is a test file 2',
                                         target_dir=new_directory2.current_full_path,
                                         data_model=new_data_model)

    # create just a file in the directory
    with open(os.path.join(new_directory2.current_full_path, 'not_contained_test_file3.txt'), 'w') as f:
        f.write('This is a test file 3')


    new_data_model.save()
    new_data_model.cleanup()


def create_mapper():
    mapper = PythonMapper()

    class TestComponent(object):
        def __init__(self, *args, **kwargs):
            self.file = kwargs.get('file')
            self.directory = kwargs.get('directory')
            self.param_1 = kwargs.get('param_1')
            self.param_2 = kwargs.get('param_2')

    content0 = Content(text_or_key='file',  # text or key of the content/parameter/property
                       property_name='file',  # name of the generated property
                       type='file',  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='file_value to test')

    content1 = Content(text_or_key='directory',  # text or key of the content/parameter/property
                       property_name='directory',  # name of the generated property
                       type='file',  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='file_value_2 to test')

    content2 = Content(text_or_key='param_1',  # text or key of the content/parameter/property
                       property_name='param_1',  # name of the generated property
                       type=None,  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='param_1 to test')

    content3 = Content(text_or_key='param_2',  # text or key of the content/parameter/property
                       property_name='param_2',  # name of the generated property
                       type=None,  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='param_2 to test')

    test_component_map = TaxonomyMap(taxonomy_name='PySimultan',
                                     taxonomy_key='Test',
                                     taxonomy_entry_name='test_component',
                                     taxonomy_entry_key='test_component',
                                     content=[content0, content1, content2, content3],
                                     )

    mapper.register(test_component_map.taxonomy_entry_key, TestComponent, taxonomy_map=test_component_map)

    return mapper


def test_component_with_directory():

    new_data_model = DataModel.create_new_project(project_path=os.path.join(project_dir, 'test_dir_component.simultan'),
                                                  user_name='admin',
                                                  password='admin')

    mapper = create_mapper()
    mapped_test_component_cls = mapper.get_mapped_class('test_component')

    new_component = mapped_test_component_cls(file=FileInfo.from_string(filename='test_file.txt',
                                                                                    content='This is a test file',
                                                                                    data_model=new_data_model),
                                                directory=DirectoryInfo(path='test_dir',
                                                                        data_model=new_data_model),
                                                param_1='param_1_value',
                                                param_2=2)

    print(new_component.directory)

    new_data_model.save()
    new_data_model.cleanup()
    mapper.clear()


def test_load_component_with_directory():
    new_data_model = DataModel(project_path=os.path.join(project_dir, 'test_dir_component.simultan'))

    mapper = create_mapper()
    typed_data = new_data_model.get_typed_data(mapper=mapper)
    mapped_test_component_cls = mapper.get_mapped_class('test_component')

    assert isinstance(mapped_test_component_cls.cls_instances[0].directory,  DirectoryInfo)

    new_data_model.cleanup()
    mapper.clear()


def test_complex_file_and_directory_info():
    pass


if __name__ == '__main__':
    test_files_and_directory_creation()
    test_complex_file_and_directory_info()
    test_component_with_directory()
    test_load_component_with_directory()
