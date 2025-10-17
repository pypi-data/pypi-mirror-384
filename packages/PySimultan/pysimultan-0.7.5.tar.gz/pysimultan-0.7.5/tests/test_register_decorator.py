from PySimultan2.taxonomy_maps import TaxonomyMap, Content
from PySimultan2.object_mapper import register
from PySimultan2 import PythonMapper


content_a = Content(text_or_key='a',
                    property_name='a',
                    type=None,
                    unit=None,
                    documentation='Property a',)

content_b = Content(text_or_key='b',
                    property_name='b',
                    type=None,
                    unit=None,
                    documentation='Property a',)

test_map = TaxonomyMap(taxonomy_name='Test',
                       taxonomy_key='Test',
                       taxonomy_entry_name='TestClass',
                       taxonomy_entry_key='TestClass',
                       content=[content_a, content_b],
                       )

@register(test_map.taxonomy_entry_key, taxonomy_map=test_map, re_register=True, module='test_mapper')
class TestClass(object):

    def __init__(self, *args, **kwargs):
        self.a = kwargs.get('a', 1)
        self.b = kwargs.get('b', 2)

    def add(self):
        return self.a + self.b

    def __repr__(self):
        return f'TestClass(a={self.a}, b={self.b})'



mapped_test_cls = PythonMapper.mappers['test_mapper'].get_mapped_class('TestClass')
print(mapped_test_cls)
