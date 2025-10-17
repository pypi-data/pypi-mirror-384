import inspect
import math
import os
from time import sleep

import PySimultan2.geometry
from PySimultan2 import PythonMapper, DataModel
from PySimultan2.taxonomy_maps import Content, TaxonomyMap
from PySimultan2.default_types import ComponentList

from PySimultan2.geometry.geometry_base import (GeometryModel)
from PySimultan2.geometry.utils import create_cube

from SIMULTAN import *
from SIMULTAN.Data import *
from SIMULTAN.Data.Geometry import *

project_dir = os.environ.get('PROJECT_DIR', '')
project_name = os.environ.get('PROJECT_NAME', 'ida_ice_structure.simultan')


def create_geometry_model(name='new_geometry_test', data_model=None):
    return GeometryModel(name=name,
                         data_model=data_model)



#####################################################################
# Create classes
#####################################################################

def create_contents():

    contents = {}

    contents['temperature_boundary_condition'] = Content(text_or_key='temperature_boundary_condition',
                                                         property_name='temperature_boundary_condition',
                                                         type=None,
                                                         unit='',
                                                         documentation='',
                                                         component_policy='reference')

    contents['construction'] = Content(text_or_key='Constructional_Element',
                                       property_name='construction',
                                       type=None,
                                       unit='',
                                       documentation='',
                                       component_policy='reference')

    contents['material'] = Content(text_or_key='material',
                                   property_name='material',
                                   type=None,
                                   unit='',
                                   documentation='',
                                   component_policy='reference')

    contents['thickness'] = Content(text_or_key='thickness',
                                    property_name='thickness',
                                    type=None,
                                    unit='',
                                    documentation='',
                                    component_policy='subcomponent',
                                    taxonomy_key='Building',
                                    taxonomy_name='Building')

    contents['thermal_conductivity'] = Content(text_or_key='thermal_conductivity',
                                               property_name='thermal_conductivity',
                                               type=float,
                                               unit='W/mK',
                                               documentation='',
                                               component_policy='subcomponent',
                                               taxonomy_name='Building',
                                               taxonomy_key='Building',
                                               )

    contents['specific_heat'] = Content(text_or_key='specific_heat',
                                        property_name='specific_heat',
                                        type=float,
                                        unit='J/kgK',
                                        documentation='',
                                        component_policy='subcomponent',
                                        taxonomy_name='Building',
                                        taxonomy_key='Building',
                                        )

    contents['density'] = Content(text_or_key='density',
                                  property_name='density',
                                  type=float,
                                  unit='kg/m3',
                                  documentation='',
                                  component_policy='subcomponent',
                                  taxonomy_name='Building',
                                  taxonomy_key='Building',
                                  )

    contents['alphaS'] = Content(text_or_key='alphaS',
                                 property_name='alphaS',
                                 type=float,
                                 unit='-',
                                 documentation='sound absorption coefficent',
                                 component_policy='subcomponent',
                                 ValueMin=0.0,
                                 ValueMax=1.0,
                                 taxonomy_name='Building',
                                 taxonomy_key='Building',
                                 )

    contents['alpha0'] = Content(text_or_key='alpha0',
                                 property_name='alpha0',
                                 type=float,
                                 unit='-',
                                 documentation='sound absorption coefficent',
                                 component_policy='subcomponent',
                                 ValueMin=0.0,
                                 ValueMax=1.0)

    contents['alphaN'] = Content(text_or_key='alphaN',
                                 property_name='alphaN',
                                 type=float,
                                 unit='-',
                                 documentation='sound absorption coefficent',
                                 component_policy='subcomponent',
                                 ValueMin=0.0,
                                 ValueMax=1.0)

    contents['r_se_cl'] = Content(text_or_key='r_se_cl',
                                  property_name='r_se_cl',
                                  type=float,
                                  unit='m2K/W',
                                  documentation='',
                                  component_policy='subcomponent')

    contents['r_si_cl'] = Content(text_or_key='r_si_cl',
                                  property_name='r_si_cl',
                                  type=float,
                                  unit='m2K/W',
                                  documentation='',
                                  component_policy='subcomponent')

    contents['temperature_cl'] = Content(text_or_key='temperature_cl',
                                         property_name='temperature_cl',
                                         type=None,
                                         unit='',
                                         documentation='',
                                         component_policy='reference')

    contents['RT'] = Content(text_or_key='RT_cl',
                             property_name='RT',
                             type=float,
                             unit='s',
                             documentation='reverberation time in s',
                             component_policy='subcomponent')


    contents['Aopt'] = Content(text_or_key='Aopt_cl',
                               property_name='Aopt',
                               type=float,
                               unit='m²',
                               documentation='equivalent absorption area in m²',
                               component_policy='subcomponent')

    contents['RTopt'] = Content(text_or_key='RTopt_cl',
                               property_name='RTopt',
                               type=float,
                               unit='s',
                               documentation='optimal reverberation time in s',
                               component_policy='subcomponent')

    return contents


def create_classes_and_map():

    mapper = PythonMapper(module='ida_ice_structure')


    class Construction_Assignement_List(ComponentList):
        pass


    class ConstructionAssignment:

        def __init__(self,
                     name,
                     temperature_boundary_condition,
                     construction,
                     *args,
                     **kwargs
                     ):
            self.name = name
            self.temperature_boundary_condition = temperature_boundary_condition
            self.construction = construction


    class Construction(ComponentList):
        """
        Class representing a construction as a list of layers
        """
        def __init__(self,
                     name,
                     r_se_cl: float = None,
                     r_si_cl: float = None,
                     alpha0: float = None,
                     alphaN: float = None,
                     *args,
                     **kwargs
                     ):
            super().__init__(*args, **kwargs)
            self.name = name
            self.r_se_cl = r_se_cl
            self.r_si_cl = r_si_cl
            self.alpha0 = alpha0
            self.alphaN = alphaN


    class Layer:

        def __init__(self,
                     name,
                     material,
                     thickness,
                     *args,
                     **kwargs
                     ):
            self.name = name
            self.material = material
            self.thickness = thickness


    class Material:

        def __init__(self,
                     name,
                     density: float,
                     specific_heat: float,
                     thermal_conductivity: float,
                     alphaS: float = None,
                     *args,
                     **kwargs
                     ):
            self.name = name
            self.density = density
            self.specific_heat = specific_heat
            self.thermal_conductivity = thermal_conductivity
            self.alphaS = alphaS


    class TemperatureBoundaryCondition:

        def __init__(self,
                    name: str,
                    temperature_cl: float,
                    *args,
                    **kwargs
                    ):
            self.name = name
            self.temperature_cl = temperature_cl


    class Room_Cl:

        def __init__(self,
                    name: str,
                    RT: float = None,
                    RTopt: float = None,
                    Aopt: float = None,
                    *args,
                    **kwargs
                    ):
            self.name = name
            self.RT = RT
            self.RTopt = RTopt
            self.Aopt = Aopt

        def calculate_RT(self):
            try:
                volume=self.associated_geometry[0].volume
                self.RTopt=0.5+0.05*math.log(volume)  # EN 12354
                self.Aopt=0.163*volume/self.RTopt

                print(self.name)
                EquivArea=0
                anzfaces=len(self.associated_geometry[0].faces)
                for face in self.associated_geometry[0].faces:
                    alphaS=0.0
                    if len(face.components)>0 :
                        construction=face.components[0].construction
                        orient1=face.orientation

                        PVolumeTest=self.associated_geometry[0]._wrapped_object
                        PFace = next((PF for PF in  PVolumeTest.Faces if PF.Face == face._wrapped_object), None)
                        orient2=PFace.Orientation

                        print(construction.name," Orientierung", orient1,orient2)


                        if orient2 == orient2.Forward:
                            if construction.alpha0 is not None:

                                if construction.alpha0>0 and construction.alpha0<1:
                                    alphaS=construction.alpha0
                                else:
                                    construction.alpha0=99.0
                                    construction.data[0].material.alphaS=99.0
                                    alphaS=-1
                            else:
                                construction.alpha0=99.0
                                alphaS=-1


                            print("Erste Schichte",alphaS)
                        else:
                            if construction.alphaN is not None:
                                if construction.alphaN>0 and construction.alphaN<1:
                                    alphaS = construction.alphaN
                                else:
                                    construction.alphaN=99.0
                                    construction.data[len(construction.data)-1].material.alphaS=99.0

                                    alphaS=-1

                            else:
                                construction.alphaN=99.0
                                construction.data[len(construction.data)-1].material.alphaS=99.0
                                alphaS=-1

                            print("Letzte Schichte",alphaS)
                        for layer in construction.data:
                            if layer is not None:
                                print(layer.name)
                            else:
                                print("ERROR Layer ist None")

                    if alphaS is not None: EquivArea += face.area*alphaS



                if EquivArea>0:
                    RT= 0.163*volume / EquivArea
                else:
                    RT=-1.0

                self.RT = RT
            except Exception as e:
                raise e

            return RT



    contents = create_contents()

    construction_assignment_list_map = TaxonomyMap(taxonomy_name='Building',
                                                   taxonomy_key='Building',
                                                   taxonomy_entry_name='Constructional Assignment List',
                                                   taxonomy_entry_key='Constructional_Assignment_List',
                                                   content=[]
                                                   )

    mapper.register(taxonomy=construction_assignment_list_map.taxonomy_entry_key,
                    cls=Construction_Assignement_List,
                    taxonomy_map=construction_assignment_list_map)


    construction_map = TaxonomyMap(taxonomy_name='Building',
                                   taxonomy_key='Building',
                                   taxonomy_entry_name='Constructional Element',
                                   taxonomy_entry_key='Constructional_Element',
                                   content=[contents['r_se_cl'],
                                            contents['r_si_cl'],
                                            contents['alpha0'],
                                            contents['alphaN'],
                                            ]
                                   )


    mapper.register(taxonomy=construction_map.taxonomy_entry_key,
                    cls=Construction,
                    taxonomy_map=construction_map)

    construction_assignment_map = TaxonomyMap(taxonomy_name='Building',
                                              taxonomy_key='Building',
                                              taxonomy_entry_name='Constructional Assignment',
                                              taxonomy_entry_key='Constructional_Assignment',
                                              content=[contents['temperature_boundary_condition'],
                                                       contents['construction']
                                                       ]
                                              )

    mapper.register(taxonomy=construction_assignment_map.taxonomy_entry_key,
                    cls=ConstructionAssignment,
                    taxonomy_map=construction_assignment_map)

    layer_map = TaxonomyMap(taxonomy_name='Reserved Slots',
                            taxonomy_key='resslot',
                            taxonomy_entry_name='Layer',
                            taxonomy_entry_key='layer',
                            content=[contents['material'],
                                     contents['thickness']
                                     ]
                            )

    mapper.register(taxonomy=layer_map.taxonomy_entry_key,
                    cls=Layer,
                    taxonomy_map=layer_map)


    material_map = TaxonomyMap(taxonomy_name='Reserved Slots',
                                 taxonomy_key='resslot',
                                 taxonomy_entry_name='Material',
                                 taxonomy_entry_key='material',
                                 content=[contents['density'],
                                         contents['specific_heat'],
                                         contents['thermal_conductivity'],
                                         contents['alphaS'],
                                         ]
                                 )

    mapper.register(taxonomy=material_map.taxonomy_entry_key,
                    cls=Material,
                    taxonomy_map=material_map)

    temperature_boundary_condition_map = TaxonomyMap(taxonomy_name='PySimultan_RoomAku',
                                                     taxonomy_key='PySimultan_RoomAku',
                                                     taxonomy_entry_name='TemperatureBoundaryCondition_name',
                                                     taxonomy_entry_key='TemperatureBoundaryCondition_key',
                                                     content=[
                                                         contents['temperature_cl']
                                                     ]
                                                     )

    mapper.register(taxonomy=temperature_boundary_condition_map.taxonomy_entry_key,
                    cls=TemperatureBoundaryCondition,
                    taxonomy_map=temperature_boundary_condition_map)

    room_map = TaxonomyMap(taxonomy_name='PySimultan_RoomAku',
                           taxonomy_key='PySimultan_RoomAku',
                           taxonomy_entry_name='Room_tax_name',
                           taxonomy_entry_key='Room_tax_key',
                           content=[
                                    contents['RT'],
                                    contents['RTopt'],
                                    contents['Aopt']
                                   ]
                           )

    mapper.register(taxonomy=room_map.taxonomy_entry_key,
                    cls=Room_Cl,
                    taxonomy_map=room_map)

    return mapper




def create_model(project_name=None,mapper=None):

    if project_name is None:
        project_name = project_path

    data_model = DataModel.create_new_project(project_path=os.path.join(project_dir, project_name),
                                              user_name='admin',
                                              password='admin')

    MappedConstructionAssignmentList = mapper.get_mapped_class('Constructional_Assignment_List')
    MappedConstructionAssignment = mapper.get_mapped_class('Constructional_Assignment')
    MappedConstruction = mapper.get_mapped_class('Constructional_Element')
    MappedLayer = mapper.get_mapped_class('layer')
    MappedMaterial = mapper.get_mapped_class('material')
    MappedTemperatureBoundaryCondition = mapper.get_mapped_class('TemperatureBoundaryCondition_key')
    MappedRoom = mapper.get_mapped_class('Room_tax_key')

    concrete = MappedMaterial(name='concrete',
                              density=2600,
                              specific_heat=800,
                              thermal_conductivity=1.5)

    insulation = MappedMaterial(name='insulation',
                                density=150,
                                specific_heat=1500,
                                thermal_conductivity=0.03)

    plaster = MappedMaterial(name='plaster',
                             density=1200,
                             specific_heat=700,
                             thermal_conductivity=0.60)

    t_out_1 = MappedTemperatureBoundaryCondition(name='t_out_1',
                                                 temperature_cl=273.15)

    t_out_2 = MappedTemperatureBoundaryCondition(name='t_out_2',
                                                 temperature_cl=283.15)

    # wall1
    wall1 = MappedConstruction(name='wall1',
                               r_se_cl=0.04,
                               r_si_cl=0.13)
    wall1_layers = [
        MappedLayer(name='concrete_layer',
                    material=concrete,
                    thickness=0.2),
        MappedLayer(name='insulation_layer',
                    material=insulation,
                    thickness=0.1),
        MappedLayer(name='plaster_layer',
                    material=plaster,
                    thickness=0.04)
    ]
    wall1.extend(wall1_layers)

    wall2_layers = [
        MappedLayer(name='concrete_layer',
                    material=concrete,
                    thickness=0.15),
        MappedLayer(name='insulation_layer',
                    material=insulation,
                    thickness=0.2),
    ]

    wall2 = MappedConstruction(name='wall2',
                               r_se_cl=0.04,
                               r_si_cl=0.13)
    wall2.extend(wall2_layers)

    bauteilzuweisung = MappedConstructionAssignmentList(name='Bauteilzuweisung')

    con1_zuw = MappedConstructionAssignment(name='con1_zuw',
                                            temperature_boundary_condition=t_out_1,
                                            construction=wall1)

    con2_zuw = MappedConstructionAssignment(name='con2_zuw',
                                            temperature_boundary_condition=t_out_2,
                                            construction=wall1)

    bauteilzuweisung.extend([con1_zuw, con2_zuw])

    Room1 = MappedRoom(name='Room1',
                       RT=3.0)

    geo_model = create_geometry_model(name='new_geometry_test',
                                      data_model=data_model)

    cube = create_cube(data_model, geo_model, scale=10)

    Room1.associate(cube)
    Room1.calculate_RT()

    con1_zuw.associate(cube.faces[0])
    con2_zuw.associate(cube.faces[1])

    data_model.save()
    data_model.cleanup()



def test_loaded_model(project_name=None,mapper=None):

    if project_name is None:
        project_name = project_path

    data_model = DataModel(project_path=project_name,
                           user_name='admin',
                           password='admin')

    mapper.load_undefined = False
    #mapper.load_undefined = True

    typed_data = data_model.get_typed_data(mapper=mapper,
                                           create_all=True)



    zone_cls = mapper.get_mapped_class('Room_tax_key')

    for zone in zone_cls.cls_instances:
        print("************************************************")
        print(zone.name)

        RT = zone.calculate_RT()
        volume = zone.associated_geometry[0].volume
        print(zone.name,"  RT ",RT,"Volumen",volume)


    data_model.save()

    data_model.cleanup()
    mapper.clear()
    del data_model


if __name__ == '__main__':

    RoomAcu_mapper = create_classes_and_map()

    create_model(project_name="TestNEU3.simultan", mapper=RoomAcu_mapper)

    # sleep(1)
    # test_loaded_model(project_name="241217_DigiTwin_as.simultan", mapper=RoomAcu_mapper)

    # test_loaded_model(project_name="Testmodell.simultan", mapper=RoomAcu_mapper)
    # sleep(1)
