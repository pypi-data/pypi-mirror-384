from PySimultan2.data_model import DataModel

project_path = r'resources/U5.simultan'

data_model = DataModel(project_path=project_path)

# data_model.data.Items[3].Components[0].Component.Slots[0].Target.Key

of_solids = data_model.find_components_with_taxonomy(taxonomy='of_solid')
of_volumes = data_model.find_components_with_taxonomy(taxonomy='of_volume')

# list(list(surface_mesh_setups)[0].Parameters)[0].get_NameTaxonomyEntry().TextOrKey
# list(list(surface_mesh_setups)[0].Parameters)[0].NameTaxonomyEntry

ref = data_model.get_associated_geometry(list(of_volumes)[0])

c = data_model.get_referenced_components(ref[0])

# fc_geometry = list(data_model.models)[2].Geometry.GeometryFromId(367)
# component = data_model.exch.GetComponents(fc_geometry)

[list(data_model.exch.GetComponents(x)) for x in list(list(data_model.models.values())[2].Geometry.Volumes)]

print('ok')
