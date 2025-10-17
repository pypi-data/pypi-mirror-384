from src.PySimultan2.data_model import DataModel
from src.PySimultan2.utils import create_taxonomy, get_ot_create_taxonomy_entry

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 importlib_resources.
    import importlib_resources as pkg_resources


import PySimultan2.tests.readme_examples.resources as readme_examples

with pkg_resources.path(readme_examples, 'empty_project.simultan') as r_path:
    project_file = str(r_path)

data_model = DataModel(project_path=project_file)

taxonomy = create_taxonomy('test_name',
                           'test_key',
                           'test_description',
                           data_model=data_model)

taxonomy_entry = get_ot_create_taxonomy_entry('test_taxonomy_entry_name',
                                       'test_taxonomy_entry_key',
                                       'test_taxonomy_entry_description',
                                              sim_taxonomy=taxonomy)

data_model.save()
data_model.cleanup()
