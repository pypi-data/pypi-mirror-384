from PySimultan2.src.PySimultan2 import DataModel, create_component
from PySimultan2.src.PySimultan2.utils import add_sub_component
from PySimultan2.src.PySimultan2.utils import create_taxonomy, get_ot_create_taxonomy_entry, create_parameter


try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 importlib_resources.
    import importlib_resources as pkg_resources


import PySimultan2.tests.readme_examples.resources as readme_examples

with pkg_resources.path(readme_examples, 'empty_project.simultan') as r_path:
    project_file = str(r_path)

data_model = DataModel(project_path=project_file)

# create a new taxonomy
taxonomy = create_taxonomy('test_name',
                           'test_key',
                           'test_description',
                           data_model=data_model)

# create a new taxonomy entry
taxonomy_entry = get_ot_create_taxonomy_entry('test_taxonomy_entry_name',
                                       'test_taxonomy_entry_key',
                                       'test_taxonomy_entry_description',
                                              sim_taxonomy=taxonomy)

# create a new component
new_comp = create_component(data_model=data_model,
                            name='Example7 Test Component',
                            Visibility=1,
                            IsAutomaticallyGenerated=False,
                            slot=taxonomy_entry)

# add parameters to the component
new_param = create_parameter(name='Example7 Test Parameter',
                             value=1.025)

new_param2 = create_parameter(name='Example int Parameter',
                              parameter_type=int,
                              value=45)

new_slot_param = create_parameter(value='test string value',
                                  taxonomy_entry=taxonomy_entry)

new_comp.Parameters.Add(new_param)
new_comp.Parameters.Add(new_param2)
new_comp.Parameters.Add(new_slot_param)

# add the component to the data model:
data_model.add_component(new_comp)


# create a second new taxonomy entry
taxonomy_entry2 = get_ot_create_taxonomy_entry('test_taxonomy_entry_name2',
                                        'test_taxonomy_entry_key2',
                                        'test_taxonomy_entry_description2',
                                               sim_taxonomy=taxonomy)


# create a new component which is going to be the sub component
sub_component = create_component(name='Example7 New Sub Component',
                                 Visibility=1,
                                 IsAutomaticallyGenerated=False,
                                 slot=taxonomy_entry2,
                                 data_model=data_model)

# add the sub_component as sub component to new_comp
add_sub_component(new_comp, sub_component, slot_extension=15)

data_model.save()
data_model.cleanup()
