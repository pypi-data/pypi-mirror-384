from PySimultan2.data_model import DataModel

from PySimultan2.tests import resources

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 importlib_resources.
    import importlib_resources as pkg_resources


with pkg_resources.path(resources, 'test_multi_value_big_table_load.simultan') as r_path:
    project_path = str(r_path)

data_model = DataModel(project_path=project_path,
                       user_name='admin',
                       password='admin')
