from PySimultan2.data_model import DataModel
from PySimultan2.utils import create_taxonomy, get_ot_create_taxonomy_entry

project_path = r'resources/U5.simultan'

data_model = DataModel(project_path=project_path)

taxonomy = create_taxonomy('test_name', 'test_key', data_model=data_model)

taxonomy_entry = get_ot_create_taxonomy_entry('test_taxonomy_entry_name', 'test_taxonomy_entry_key', sim_taxonomy=taxonomy)

data_model.save()
data_model.cleanup()

print('done')
