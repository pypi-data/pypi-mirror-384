"""
This module contains classes and functions to handle files and directories.
"""
from __future__ import annotations
from datetime import datetime
import glob

import contextlib
import os
import io
import re
import shutil
import tempfile
from typing import List, Union, Optional
import shutil
import zipfile
from pathlib import Path
# from System.IO import FileInfo  # public FileInfo (string fileName);

from SIMULTAN.Data.Assets import ResourceEntry, ResourceFileEntry, ContainedResourceFileEntry, Asset, ResourceDirectoryEntry
from SIMULTAN.Data.Taxonomy import SimTaxonomyEntry, SimTaxonomyEntryReference, SimTaxonomy
from SIMULTAN.Data.Components import SimComponent, ComponentMapping

from System.IO import DirectoryInfo as SystemDirectoryInfo
from System.IO import FileInfo as SystemFileInfo

# from .config import default_data_model

from . import config, logger

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .data_model import DataModel
    from .simultan_object import SimultanObject


@contextlib.contextmanager
def cd(newdir, cleanup=lambda: True):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)
        cleanup()


@contextlib.contextmanager
def tempdir():
    dir_path = tempfile.mkdtemp()

    def cleanup():
        shutil.rmtree(dir_path)

    with cd(dir_path, cleanup):
        yield dir_path


def add_tag_to_resource(resource: Union[ResourceFileEntry, ContainedResourceFileEntry, ResourceDirectoryEntry],
                        tag: Union[SimTaxonomyEntry, SimTaxonomyEntryReference]):
    """
    Add a tag to an asset.

    :param resource: The resource to add the tag to.
    :param tag: The tag to add to the asset.
    :return: None
    """
    if isinstance(tag, SimTaxonomyEntry):
        tag = SimTaxonomyEntryReference(tag)

    if tag not in resource.Tags:
        resource.Tags.Add(tag)


def add_asset_to_component(comp: [SimComponent, SimultanObject],
                           asset: Union[ResourceFileEntry, ContainedResourceFileEntry, ResourceDirectoryEntry],
                           content_id: str = '',
                           tag: SimTaxonomyEntry = None) -> Asset:
    """
    Add an asset to a component with a content id.
    :param comp: Component to add the asset; ParameterStructure.Components.SimComponent
    :param asset: Asset to be added; ParameterStructure.Assets.ResourceFileEntry
    :param content_id: Content id of the asset; string; E.g. '0' as the page of a pdf
    :param tag: Tag to be added to the asset.
    :return:
    """
    wrapped_obj = comp if isinstance(comp, SimComponent) else comp._wrapped_obj

    if tag is not None:
        try:
            add_tag_to_resource(asset, tag)
        except Exception as e:
            logger.error(f'Error adding tag to asset {asset}: {e} ')
            raise e

    try:
        return ComponentMapping.AddAsset(wrapped_obj, asset, content_id)
    except Exception as e:
        logger.error(f'Error adding asset {asset} to component: {e}')
        raise e


def remove_asset_from_component(comp: Union[SimComponent, SimultanObject],
                                asset: Asset) -> None:
    """
    Remove an asset from a component with a content id.
    :param comp: Component to remove the asset from; ParameterStructure.Components.SimComponent
    :param asset:
    :return:
    """
    wrapped_obj = comp if isinstance(comp, SimComponent) else comp._wrapped_obj
    return ComponentMapping.RemoveAsset(wrapped_obj, asset)


def create_asset_from_string(filename: str,
                             content: str,
                             data_model: DataModel,
                             target_dir: Optional[Union[DirectoryInfo, ResourceDirectoryEntry, str]] = None,
                             tag: Optional[Union[SimTaxonomyEntry, SimTaxonomyEntryReference]] = None) -> ResourceFileEntry:
    """
    Create a new asset from a string. The asset is added to the data model.
    :param filename: Name of the file to be created. E.g. 'new_file.txt'
    :param content:  Content of the file. E.g. 'This is the content of the file.'
    :param data_model:  Data model to add the asset to.
    :param target_dir: Target directory to add the asset to.
    :param tag: Tag to be added to the asset.
    :return: ResourceFileEntry
    """

    # check if file already exists
    if target_dir is not None:
        if isinstance(target_dir, DirectoryInfo):
            target_dir = target_dir.full_path


    with tempdir() as dirpath:
        filepath = os.path.join(dirpath, filename)
        with open(filepath, 'w') as f:
            f.write(content)

        if target_dir is not None:
            if isinstance(target_dir, DirectoryInfo):
                target_dir = target_dir.full_path

            resource = data_model.add_resource(filepath,
                                               target_dir=target_dir)
        else:
            resource = data_model.add_resource(filepath)

    if tag is not None:
        add_tag_to_resource(resource,
                            tag)

    return resource


def create_asset_from_str_io(filename: str,
                             content: io.StringIO,
                             data_model: DataModel,
                             target_dir: Optional[Union[DirectoryInfo, ResourceDirectoryEntry, str]] = None,
                             tag: Union[SimTaxonomyEntry, SimTaxonomyEntryReference] = None) -> ResourceFileEntry:
    """
    Create a new asset from a string io. The asset is added to the data model.
    :param filename: Name of the file to be created. E.g. 'new_file.txt'
    :param content:  Content of the file. E.g. 'This is the content of the file.'
    :param data_model:  Data model to add the asset to.
    :param target_dir: Target directory to add the asset to.
    :param tag: Tag to be added to the asset.
    :return: ResourceFileEntry
    """
    with tempdir() as dirpath:
        filepath = os.path.join(dirpath, filename)
        with open(filepath, 'w') as f:
            f.write(content.getvalue())

        resource = data_model.add_resource(filepath,
                                           target_dir=target_dir)

    if tag is not None:
        add_tag_to_resource(resource, tag)

    return resource


def create_asset_from_file(file_info: FileInfo,
                           data_model: DataModel,
                           tag: Union[SimTaxonomyEntry, SimTaxonomyEntryReference] = None) -> Union[
                           ResourceFileEntry, ContainedResourceFileEntry]:
    """
    Create a new asset from a file. The asset is added to the data model.
    :param file_info: FileInfo object of the file to be added.
    :param data_model:  Data model to add the asset to.
    :param tag: Tag to be added to the asset.
    :return: ResourceFileEntry
    """
    resource = data_model.add_resource(file_info.file_path)

    if tag is not None:
        add_tag_to_resource(resource, tag)

    return resource


def add_directory(data_model: DataModel,
                  directory: str,
                  parent_directory: Optional[Union[DirectoryInfo, ResourceDirectoryEntry, str]] = None,
                  tag: Union[SimTaxonomyEntry, SimTaxonomyEntryReference] = None) -> ResourceDirectoryEntry:

    """
    Add a directory to the data model.
    :param data_model:
    :param target_dir:
    :param tag:
    :return:
    """

    # create the directory
    resource_directory_entry = data_model.create_resource_directory(parent_directory=parent_directory)

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        resource = data_model.add_resource(file_path)
        if tag is not None:
            add_tag_to_resource(resource, tag)





class MetaMock(type):

    @property
    def cls_instances(cls) -> list['SimultanObject']:
        try:
            return list(cls._cls_instances)
        except Exception as e:
            logger.error(f'Error getting cls_instances: {e}')
            return []

    def __call__(cls, *args, **kwargs):
        resource_entry = kwargs.get('resource_entry', None)
        if resource_entry is not None and hasattr(resource_entry, 'Key'):
            obj = cls._cls_instances.get(resource_entry.Key, None)
            if obj is not None:
                return obj

        obj = cls.__new__(cls)
        obj.__init__(*args, **kwargs)
        if obj.resource_entry is not None:
            cls._cls_instances[obj.resource_entry.Key] = obj
        return obj


class DirectoryInfoMetaMock(type):

    @property
    def cls_instances(cls) -> list['SimultanObject']:
        try:
            return list(cls._cls_instances)
        except Exception as e:
            logger.error(f'Error getting cls_instances: {e}')
            return []

    def __call__(cls, *args, **kwargs):
        resource_entry: Optional[ResourceDirectoryEntry] = kwargs.get('resource_entry', None)
        if resource_entry is not None and hasattr(resource_entry, 'Key'):
            obj = cls._cls_instances.get(resource_entry.Key, None)
            if obj is not None:
                return obj

        obj = cls.__new__(cls)
        obj.__init__(*args, **kwargs)
        if obj.resource_entry is not None:
            cls._cls_instances[obj.resource_entry.Key] = obj
        return obj


class FileInfo(object, metaclass=MetaMock):

    _cls_instances = {}
    _taxonomy = 'FileInfo'

    @classmethod
    def from_string(cls,
                    filename: str,
                    content: str,
                    target_dir: Optional[Union[DirectoryInfo, ResourceDirectoryEntry, str]] = None,
                    *args,
                    **kwargs,
                    ) -> FileInfo:
        """
        Create a file info object from a string.
        :param filename: Name of the file to be created. E.g. 'new_file.txt'
        :param content:  Content of the file. E.g. 'This is the content of the file.'
        :param target_dir: Target directory to add the asset to.
        :param args:
        :param kwargs:
        :return: FileInfo
        """

        data_model = kwargs.get('data_model', config.get_default_data_model())

        if target_dir is not None:
            if isinstance(target_dir, DirectoryInfo):
                full_path = os.path.join(target_dir.full_path, filename)
            elif isinstance(target_dir, ResourceDirectoryEntry):
                full_path = os.path.join(target_dir.CurrentFullPath, filename)
            elif isinstance(target_dir, str):
                full_path = os.path.join(target_dir, filename)
            else:
                raise ValueError(f'Unsupported target_dir format')
        else:
            if not filename.startswith(str(data_model.project.ProjectUnpackFolder)):
                full_path = os.path.join(str(data_model.project.ProjectUnpackFolder), filename)
            else:
                full_path = filename

        if os.path.isfile(full_path):
            # check if resource entry exists
            resource = data_model.get_resource(full_path)
            if resource is None:
                resource = create_asset_from_string(filename,
                                                    content,
                                                    target_dir=target_dir,
                                                    *args,
                                                    **kwargs)
        else:
            resource = create_asset_from_string(filename,
                                                content,
                                                target_dir=target_dir,
                                                *args,
                                                **kwargs)

        file_info = cls(resource_entry=resource,
                        data_model=data_model)
        file_info.write_content(content)
        return file_info

    @classmethod
    def from_existing_file(cls,
                           file_path: str,
                           *args,
                           **kwargs) -> FileInfo:

        data_model = kwargs.get('data_model', config.get_default_data_model())
        resource = data_model.add_resource_file(file_path)

        return cls(resource_entry=resource,
                   *args,
                   **kwargs)


    def __init__(self, file_path=None, *args, **kwargs):
        """
        Custom file info object to be used with the with statement. This object is used to open a file and close it
        automatically.
        Example:

        file_path = 'path/to/file.txt'
        file_info = FileInfo(file_path, 'r')

        with file_info as f:
            print(f.read())

        :param file_path:
        :param args:
        :param kwargs:
        """
        # do custom stuff here
        self.deleted = False
        self._resource_entry: Union[ResourceFileEntry, ContainedResourceFileEntry, None] = None

        if file_path is not None:
            self.file_path: str = file_path
        else:
            self.file_path = kwargs.get('resource_entry').File.FullPath

        self.data_model: Union[DataModel, None] = kwargs.get('data_model', None)
        self.resource_entry = kwargs.get('resource_entry', None)

        self.encoding = kwargs.get('encoding', 'utf-8')

        self.args = args
        self.kwargs = kwargs

    @property
    def parent(self):
        return self.resource_entry.Parent

    @property
    def key(self) -> int:
        try:
            return self.resource_entry.Key
        except Exception as e:
            return None

    @property
    def directory(self) -> DirectoryInfo:
        return DirectoryInfo(resource_entry=self.resource_entry.Parent,
                             data_model=self.data_model)

    @property
    def resource_entry(self) -> Union[ResourceFileEntry, ContainedResourceFileEntry, None]:
        if self._resource_entry is None and not self.deleted:
            if self.data_model is None:
                logger.warning(f'No data model provided. Using default data model: {config.get_default_data_model().id}.')
                self.data_model = config.get_default_data_model()
            if self.data_model is not None:
                self.resource_entry = self.data_model.add_resource(self.file_path)
                self.file_path = self.resource_entry.File.FullPath
        return self._resource_entry

    @resource_entry.setter
    def resource_entry(self, value):

        if value is not None:
            self._cls_instances[value.Key] = self
        else:
            del self._cls_instances[self._resource_entry.Key]
        self._resource_entry = value

    @property
    def file_size(self) -> Optional[int]:
        try:
            return os.path.getsize(self.file_path)
        except FileNotFoundError:
            raise FileNotFoundError(f'File not found: {self.file_path}')
        except Exception as e:
            raise e

    @property
    def last_modified(self) -> datetime:
        return datetime.fromtimestamp(os.path.getmtime(self.file_path))

    @resource_entry.setter
    def resource_entry(self, value):
        self._resource_entry = value

    @property
    def filename(self) -> str:
        return self.resource_entry.File.Name

    @property
    def name(self) -> str:
        return os.path.basename(self.file_path)

    @name.setter
    def name(self, value: str):
        os.rename(self.file_path, os.path.join(os.path.dirname(self.file_path), value))
        self.file_path = os.path.join(os.path.dirname(self.file_path), value)

    @property
    def full_path(self) -> str:
        return os.path.abspath(self.file_path)

    @property
    def size(self) -> int:
        return os.path.getsize(self.file_path)

    @property
    def is_zip(self) -> bool:
        return self.file_path.endswith('.zip')

    @property
    def files(self) -> List[str]:
        if self.is_zip:
            with zipfile.ZipFile(self.file_path, 'r') as z:
                return z.namelist()
        else:
            return []

    @property
    def exists(self) -> bool:
        return os.path.exists(self.file_path)

    @property
    def content(self) -> str:
        return self.get_content(encoding=self.encoding)

    @content.setter
    def content(self, value: str):
        self.write_content(value)

    def __enter__(self):
        self.file_obj = open(self.file_path, *self.args, **self.kwargs)
        return self.file_obj

    def __exit__(self, *args):
        self.file_obj.close()

    def __repr__(self):
        if not self.deleted:
            return f'FileInfo({self.file_path})'
        else:
            return f'FileInfo({self.file_path}) (deleted)'

    def move(self, new_directory_path: Union[str, DirectoryInfo]) -> FileInfo:

        if isinstance(new_directory_path, str):
            new_directory_path = DirectoryInfo.from_existing_directory(new_directory_path,
                                                                       data_model=self.data_model)

        # check if file can be moved
        try:
            self.resource_entry.ChangeLocation(SystemDirectoryInfo(new_directory_path.full_path),
                                                   '1',
                                                   True)
        except Exception as e:
            logger.error(f'Error moving file: {e}')
            raise e

    def get_content(self, encoding='utf-8') -> Optional[Union[str, dict[str, str]]]:
        """
        Get the content of the file.
        :param encoding: Encoding of the file.
        :return: File content
        """
        if self.exists:
            if self.file_path.endswith('.zip'):
                content = {}
                with zipfile.ZipFile(self.file_path, 'r') as z:
                    for file in z.namelist():
                        content[file] = z.read(file).decode(encoding)
                return content
            else:
                with open(self.file_path, 'r', encoding=encoding) as f:
                    return f.read()
        else:
            return

    def copy(self,
             new_file_path: Union[str, DirectoryInfo]) -> FileInfo:
        """
        Copy the file to a new location.
        :param new_file_path: New file path.
        :return: FileInfo
        """
        if isinstance(new_file_path, DirectoryInfo):
            new_file_path = os.path.join(new_file_path.full_path, self.filename)

        shutil.copy(self.full_path, new_file_path)
        return FileInfo.from_existing_file(file_path=new_file_path,
                                           data_model=self.data_model)

    def write_content(self, content: str, encoding='utf-8') -> None:
        """
        Write content to the file.
        :param content: Content to be written to the file.
        :param encoding: Encoding of the file.
        :return: None
        """
        with open(self.file_path, 'w', encoding=encoding) as f:
            f.write(content)

    def append_content(self, content: str, encoding='utf-8') -> None:
        """
        Append content to the file.
        :param content: Content to be appended to the file.
        :param encoding: Encoding of the file.
        :return: None
        """
        with open(self.file_path, 'a', encoding=encoding) as f:
            f.write(content)

    def delete(self) -> None:
        """
        Delete the file.
        :return: None
        """
        if self.resource_entry is not None:
            if self.resource_entry.Key in self._cls_instances:
                del self._cls_instances[self.resource_entry.Key]
            self.data_model.delete_resource(self.resource_entry)

        try:
            os.remove(self.file_path)
        except FileNotFoundError:
            pass
        self.deleted = True

    def to_json(self) -> dict:

        obj_dict = {
            'key': self.key,
            'name': self.name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'last_modified': self.last_modified,
            'encoding': self.encoding,
            'is_zip': self.is_zip,
        }

        return obj_dict

    def json_ref(self):
        return {"$ref": {
            "$type": 'FileInfo',
            "$key": str(self.key)
        }
        }


class DirectoryInfo(object, metaclass=DirectoryInfoMetaMock):

    _cls_instances = {}
    _taxonomy = 'DirectoryInfo'

    @classmethod
    def get_by_key(cls, key: int) -> Optional[DirectoryInfo]:
        return cls._cls_instances.get(key, None)

    @classmethod
    def from_existing_directory(cls,
                                directory_path: str,
                                add_files: bool = True,
                                add_sub_directories: bool = True,
                                *args,
                                **kwargs) -> DirectoryInfo:
        """
        Create a directory info object from an existing directory.
        :param directory_path: the path to the directory
        :param add_files:
        :param add_sub_directories:
        :param args:
        :param kwargs:
        :return:
        """

        data_model = kwargs.get('data_model', config.get_default_data_model())

        if not directory_path.startswith(str(data_model.project.ProjectUnpackFolder)):
            directory_path = os.path.join(str(data_model.project.ProjectUnpackFolder), directory_path)

        res = data_model.project_data_manager.AssetManager.CreateResourceDirIn(os.path.basename(directory_path),
                                                     SystemDirectoryInfo(os.path.dirname(directory_path)),
                                                     '')

        resource = data_model.project_data_manager.AssetManager.GetResource(res.Item1)

        directory_info = cls(resource_entry=resource,
                             *args,
                             **kwargs)


        if add_files:
            directory_info.add_all_contained_files()

            # for file in os.listdir(directory_path):
            #     file_path = os.path.join(directory_path, file)
            #     data_model.add_resource_file(file_path, target_dir=resource)

        if add_sub_directories:
            directory_info.add_all_contained_directories()

            # for sub_dir in os.listdir(directory_path):
            #     sub_dir_path = os.path.join(directory_path, sub_dir)
            #     data_model.add_resource_directory(sub_dir_path, parent_directory=resource)

        return directory_info

    @classmethod
    def from_existing_directory_copy(cls,
                                     directory_path: str,
                                     destination_path: str,
                                     add_files: bool = True,
                                     add_sub_directories: bool = True,
                                     *args,
                                     **kwargs) -> DirectoryInfo:

        """
        Create a directory info object from an existing directory which is copied to a directory in the project.
        :param directory_path:
        :param destination_path: the path to the directory (in the project)
        :param add_files:
        :param add_sub_directories:
        :param args:
        :param kwargs:
        :return:
        """

        shutil.copytree(directory_path, destination_path)
        return cls.from_existing_directory(destination_path,
                                             add_files=add_files,
                                             add_sub_directories=add_sub_directories,
                                             *args,
                                             **kwargs)

    def __init__(self,
                 path: Optional[str] = None,
                 helper_file: Optional[FileInfo] = None,
                 resource_entry: Optional[ResourceDirectoryEntry] = None,
                 *args,
                 **kwargs):

        self.deleted = False

        self._resource_entry: Optional[ResourceDirectoryEntry] = None
        self._helper_file: Optional[FileInfo] = None
        self.data_model: Optional[DataModel] = kwargs.get('data_model', None)
        self.path: str = path

        self.resource_entry = resource_entry
        self.helper_file = helper_file

    @property
    def tags(self) -> List[SimTaxonomyEntry]:
        return list(self.resource_entry.Tags)

    @property
    def full_path(self) -> str:
        return self.resource_entry.CurrentFullPath

    @property
    def relative_path(self) -> str:
        return self.resource_entry.CurrentRelativePath

    @property
    def helper_file(self) -> Optional[FileInfo]:
        if (self._helper_file is None or not isinstance(self._helper_file, FileInfo)) and not self.deleted:
            self._helper_file = self.add_file('__dir_helper_file__')

        return self._helper_file

    @helper_file.setter
    def helper_file(self, value):
        self._helper_file = value

    @property
    def resource_entry(self) -> Optional[ResourceDirectoryEntry]:
        if self._resource_entry is None and not self.deleted:
            if self.data_model is None:
                logger.warning(
                    f'No data model provided. Using default data model: {config.get_default_data_model().id}.')
                self.data_model = config.get_default_data_model()
            if self.data_model is not None:
                self.resource_entry = self.data_model.create_resource_directory(self.path)
                self._cls_instances[self.resource_entry.Key] = self
                self.path = self.resource_entry.CurrentFullPath
        return self._resource_entry

    @resource_entry.setter
    def resource_entry(self, value):

        orig_value = self._resource_entry
        self._resource_entry = value

        if self._resource_entry is None:
            if orig_value is not None:
                del self._cls_instances[orig_value.Key]
            return

        if self.key is not None:
            if value is not None:
                self._cls_instances[value.Key] = self
            else:
                del self._cls_instances[self._resource_entry.Key]
            self._resource_entry = value

    @property
    def parent(self) -> Optional[ResourceDirectoryEntry]:
        if self.resource_entry.Parent is not None:
            if self.resource_entry.Parent.Key in self._cls_instances:
                return self.get_by_key(self.resource_entry.Parent.Key)
            return DirectoryInfo(resource_entry=self.resource_entry.Parent)
        else:
            return self.resource_entry.Parent

    @property
    def sub_directories(self) -> List[DirectoryInfo]:
        return [DirectoryInfo(resource_entry=entry,
                              data_model=self.data_model) for entry in self.resource_entry.Children if isinstance(entry, ResourceDirectoryEntry)]

    @property
    def files(self) -> List[FileInfo]:
        return [FileInfo(resource_entry=entry,
                         data_model=self.data_model) for entry in self.resource_entry.Children if isinstance(entry,
                                                                                                             (
                                                                                                             ResourceFileEntry,
                                                                                                             ContainedResourceFileEntry)
                                                                                                             ) and entry.Name != '__dir_helper_file__'
                ]

    @property
    def key(self) -> Optional[int]:
        if self.resource_entry is not None:
            return self.resource_entry.Key
        else:
            return None

    def add_sub_directory(self, dirname: str) -> DirectoryInfo:

        existing = next((x for x in self.sub_directories if x.resource_entry.current_relative_path == dirname), None)
        if existing is not None:
            return existing

        return DirectoryInfo(path=os.path.join(self.resource_entry.current_relative_path, dirname),
                             data_model=self.data_model)

    def get_sub_directory(self,
                          dirname: str,
                          create=False) -> Optional[DirectoryInfo]:
        """
        Get a sub directory by name.
        :param dirname: directory name, relative to self.relative_path
        :param create:
        :return:
        """

        logger.debug(f'Getting sub directory in {self.relative_path}: {dirname}')
        res = next((x for x in self.sub_directories if x.resource_entry.Name == dirname), None)
        if not res and create:
            logger.debug(f'Creating sub directory in {self.relative_path}: {dirname}')
            res = self.add_sub_directory(dirname)

        return res

    def file_exists(self, filename: str) -> bool:
        return any(x for x in self.files if x.resource_entry.Name == filename)

    def get_file(self, filename: str) -> Optional[FileInfo]:
        resource = next((x for x in self.files if x.resource_entry.Name == filename), None)
        return resource

    def add_file(self,
                 filename: str,
                 content: Optional[str] = None) -> FileInfo:

        if Path(self.full_path).joinpath(filename).exists():
            return FileInfo.from_existing_file(str(Path(self.full_path).joinpath(filename)), data_model=self.data_model)


        if self.resource_entry.Children:
            file = self.get_file(filename)
            if file is not None:
                return file

        if content is not None:
            return FileInfo.from_string(filename=filename,
                                        content=content,
                                        target_dir=self.resource_entry,
                                        data_model=self.data_model)
        else:
            new_resource = self.data_model.add_empty_resource(filename=os.path.join(self.full_path, filename))
            return FileInfo(resource_entry=new_resource,
                            data_model=self.data_model)

    def add_all_contained_files(self):
        for file in os.listdir(self.full_path):
            full_filename = os.path.join(self.full_path, file)
            if Path(full_filename).is_file():

                if full_filename in (x.current_full_path for x in self.resource_entry.Children):
                    continue
                else:
                    logger.info(f'Adding file: {full_filename} to resources')
                    FileInfo.from_existing_file(full_filename, data_model=self.data_model)

    def add_all_contained_directories(self):
        for file in os.listdir(self.full_path):
            full_filename = os.path.join(self.full_path, file)
            if Path(full_filename).is_dir():
                if full_filename in (x.current_full_path for x in self.resource_entry.Children):
                    continue
                else:
                    logger.info(f'Adding directory: {full_filename} to resources')
                    DirectoryInfo.from_existing_directory(full_filename, data_model=self.data_model)

        for directory in self.sub_directories:
            directory.add_all_contained_files()
            directory.add_all_contained_directories()

    def add_tag(self, tag: SimTaxonomyEntry) -> None:
        add_tag_to_resource(self.resource_entry, tag)

    def delete(self):

        for file in self.files:
            file.delete()

        # delete helper file
        if self.helper_file is not None:
            self.helper_file.delete()

        if self.resource_entry is not None:
            if self.resource_entry.Key in self._cls_instances:
                del self._cls_instances[self.resource_entry.Key]
            self.data_model.delete_resource(self.resource_entry)

        shutil.rmtree(self.full_path)
        self.deleted = True

    def delete_files(self,
                     pattern: Optional[str] = None,
                     recursive: bool = False) -> None:
        """
        Delete files by pattern.
        :param pattern: Pattern to match files. Default is None. if None, all files are deleted.
        :param recursive: If True, delete files recursively.
        :return:
        """

        if pattern:
            matching = glob.glob(self.full_path + f'/{pattern}', recursive=recursive)

        for file in self.files:
            if pattern is None or file.file_path in matching:
                logger.debug(f'Deleting file: {file.filename}')
                file.delete()

        if recursive:
            for sub_dir in self.sub_directories:
                sub_dir.delete_files(pattern=pattern, recursive=recursive)

    def delete_subdirectories(self,
                              pattern: Optional[str] = None,
                                recursive: bool = False) -> None:

        """
        Delete subdirectories by pattern.
        :param pattern: Regex pattern to match subdirectories. Default is None. If None, all subdirectories are deleted.
        :param recursive: If True, delete subdirectories recursively.
        :return:
        """

        for sub_dir in self.sub_directories:
            if pattern is None or re.match(pattern, sub_dir.relative_path):
                logger.debug(f'Deleting subdirectory: {sub_dir.relative_path}')
                sub_dir.delete()

    def __repr__(self):
        if not self.deleted:
            return f'DirectoryInfo(key:{self.key}, hash: {hash(self)}; {self.full_path})'
        else:
            return f'(Deleted) DirectoryInfo(key:{self.key}, hash: {hash(self)}; {self.full_path}) (deleted)'
