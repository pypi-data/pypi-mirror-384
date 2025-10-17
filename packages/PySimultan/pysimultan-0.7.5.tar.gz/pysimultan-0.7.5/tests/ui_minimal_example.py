from PySimultan2.py_simultan_ui.main_ui import run_ui
from PySimultan2.py_simultan_ui.core import mapper
from PySimultan2.taxonomy_maps import TaxonomyMap, Content
from PySimultan2.py_simultan_ui.core.method_mapper import method_mapper


class TestClass(object):

    def __init__(self, *args, **kwargs):
        self.param_1 = kwargs.get('param_1', 1)
        self.param_2 = kwargs.get('param_2', 2)
        self.c = kwargs.get('c', None)

    def test_method(self):
        self.c = self.param_1 + self.param_2


c_param_1 = Content(text_or_key='param_1',
                    property_name='param_1',
                    type=None,
                    unit='',
                    documentation='param_1')

c_param_2 = Content(text_or_key='param_2',
                    property_name='param_2',
                    type=None,
                    unit='',
                    documentation='param_2')
#
c_c = Content(text_or_key='c',
              property_name='c',
              type=None,
              unit='',
              documentation='c')


cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                      taxonomy_key='PySimultan',
                      taxonomy_entry_name='TestClass',
                      taxonomy_entry_key='TestClass',
                      content=[c_param_1, c_param_2, c_c],
                      )

mapper.register(cls_map.taxonomy_entry_key, TestClass, taxonomy_map=cls_map)
mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)


method_mapper.register_method(cls=mapped_cls,
                              name='test_method',
                              method=mapped_cls.test_method,
                              args=[],
                              kwargs={})


run_ui()
