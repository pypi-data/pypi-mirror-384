from PySimultan2.data_model import DataModel



try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 importlib_resources.
    import importlib_resources as pkg_resources


import resources


with pkg_resources.path(resources, 'test_project.simultan') as r_path:
    project_path = str(r_path)


data_model = DataModel.create_new_project(project_path=project_path,
                                          user_name='admin',
                                          password='admin')

assert isinstance(data_model, DataModel)

data_model.cleanup()
