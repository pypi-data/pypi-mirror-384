# pysimultan

[![PyPI - Version](https://img.shields.io/pypi/v/pysimultan.svg)](https://pypi.org/project/pysimultan)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pysimultan.svg)](https://pypi.org/project/pysimultan)

PySimultan is a Python library designed to facilitate the creation, manipulation, and management of SIMULTAN data models, taxonomies, and templates. It provides a structured way to define and interact with complex data structures, making it particularly useful for applications that require detailed data organization and templating.  
Key Features:
- Data Models: Create and manage data SIMULTAN models with ease.
- Taxonomies: Define and use taxonomies to categorize and structure data.
- File and Directory Management: Handle files and directories within the data models.
- Mapping of Python objects to SIMULTAN data models: Map Python objects to SIMULTAN data models for easy data creation and manipulation.
- Simple integration in existing Python projects: Easily integrate PySimultan into existing Python projects to enhance data management capabilities.


-----

## Table of Contents

- [Installation](#installation)
- [License](#license)
- [Usage](#usage)
- [Change Log](#change-log)

## Installation

```console
pip install PySimultan
```

## License

`PySimultan` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.


# Usage

### Data Models

Create a new data model:
```python
from PySimultan2 import DataModel

# Create a new data model
data_model = DataModel.create_new_project(project_path='my_project.simultan',
                                          user_name='admin',
                                          password='admin')
```

Load an existing data model:
```python
from PySimultan2 import DataModel

# Load an existing data model
data_model = DataModel(project_path='my_project.simultan',
                       user_name='admin',
                       password='admin')
```

save the data model:
```python
data_model.save()
```

close and cleanup the data model:
```python
data_model.cleanup()
```


### Mapping python to SIMULTAN

#### Create a mapped class:
```python
from PySimultan2 import DataModel, TaxonomyMap, Content, PythonMapper

mapper = PythonMapper()

class TestComponent(object):
    def __init__(self, *args, **kwargs):
        self.param_1 = kwargs.get('param_1')
        self.param_2 = kwargs.get('param_2')

content0 = Content(text_or_key='param_1',  # text or key of the content/parameter/property
                   property_name='param_1',  # name of the generated property
                   type=None,  # type of the content/parameter/property
                   unit=None,  # unit of the content/parameter/property
                   documentation='param_1 to test')

content1 = Content(text_or_key='param_2',  # text or key of the content/parameter/property
                   property_name='param_2',  # name of the generated property
                   type=None,  # type of the content/parameter/property
                   unit=None,  # unit of the content/parameter/property
                   documentation='param_2 to test')

test_component_map = TaxonomyMap(taxonomy_name='PySimultan',
                                 taxonomy_key='Test',
                                 taxonomy_entry_name='test_component',
                                 taxonomy_entry_key='test_component',
                                 content=[content0, content1],
                                 )

mapper.register(test_component_map.taxonomy_entry_key, TestComponent, taxonomy_map=test_component_map)
```

#### Create an instance of the mapped class:
```python
# get the mapped class
mapped_test_component_cls = mapper.get_mapped_class('test_component')

# create an instance of the mapped class
mapped_test_component = mapped_test_component_cls(param_1='value1', 
                                                  param_2='value2',
                                                  data_model=data_model)

# save the data_model
data_model.save()

# cleanup the data_model
data_model.cleanup()
```

#### Load an instance of the mapped class:
```python
# load the data_model
data_model = DataModel(project_path='my_project.simultan',
                       user_name='admin',
                       password='admin')
                       
# get the mapped class
mapped_test_component_cls = mapper.get_mapped_class('test_component')

# get the instances of the mapped class
instances = mapped_test_component_cls.cls_instaces

print(instances[0].param_1)
```


# Change Log
## [0.6.4] - 2025-06-06
Updated SIMULTAN version to 0.7.18

## [0.5.9.7] - 2025-01-09
- Added default component support to Mapper: if a default component is not present in the datamodel, it is automatically added
- Fixed content naming bug: Content.name is now used for the name of the TaxonomyEntry in SIMULTAN
- Added typing for better code completion

## [0.5.9.4] - 2024-12-31
- Fixed bug in DirectoryInfo where \_\_dir_helper_file__ was not found if already existing

## [0.5.8] - 2024-12-17
- Added FileInfo.from_existing_file method to create FileInfo object from existing file in ProjectUnpackFolder

## [0.5.7] - 2024-12-09
- Added support for different taxonomy for content
- Added support for numpy np.float32, np.float64 and np.int32, np.int64

## [0.4.20] - 2024-07-01
- Fixed Bug in nested dictionary creation

## [0.4.19] - 2024-07-01
- Refactored dictionaries 
