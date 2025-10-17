from PySimultan2.taxonomy_maps import TaxonomyMap, Content


def test_create_taxonomie_map(filename):

    content0 = Content(text_or_key='of_geometry',         # text or key of the content/parameter/property
                       property_name='of_geometry',       # name of the generated property
                       type=None,                         # type of the content/parameter/property
                       unit=None,                         # unit of the content/parameter/property
                       documentation='Component or reference which represents the case fc_geometry')

    content1 = Content(text_or_key='meshing',  # text or key of the content/parameter/property
                       property_name='meshing',  # name of the generated property
                       type=None,  # type of the content/parameter/property
                       unit=None,  # unit of the content/parameter/property
                       documentation='Component or reference which represents the meshing')

    of_solid_map = TaxonomyMap(taxonomie_name='of_case',
                               taxonomie_key='of_case',
                               content=[content0, content1],
                               )

    of_solid_map.write(filename=filename)


def load_taxonomie_map(filename):
    return TaxonomyMap.from_yaml_file(filename=filename)


if __name__ == '__main__':
    test_create_taxonomie_map(filename='of_solid_map.yaml')
    load_taxonomie_map(filename='of_solid_map.yaml')
    pass
