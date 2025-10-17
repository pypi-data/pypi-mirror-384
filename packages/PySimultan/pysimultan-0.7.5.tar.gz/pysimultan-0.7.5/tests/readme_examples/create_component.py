from src.PySimultan2 import DataModel
from src.PySimultan2.utils import add_sub_component

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 importlib_resources.
    import importlib_resources as pkg_resources


import PySimultan2.tests.readme_examples.resources as readme_examples

with pkg_resources.path(readme_examples, 'create_component_example.simultan') as r_path:
    project_path = str(r_path)

data_model = DataModel.create_new_project(project_path=project_path,
                                          user_name='admin',
                                          password='admin')

# create a new component
new_comp = data_model.create_component(name='Example7 Test Component',
                                       Visibility=1,
                                       IsAutomaticallyGenerated=False)


# create a new component which is going to be the sub component
sub_component = data_model.create_component(name='Example7 New Sub Component',
                                            Visibility=1,
                                            IsAutomaticallyGenerated=False)

# add the sub_component as sub component to new_comp
add_sub_component(new_comp, sub_component, "Undefined Slot", 15)

data_model.save()
data_model.cleanup()
