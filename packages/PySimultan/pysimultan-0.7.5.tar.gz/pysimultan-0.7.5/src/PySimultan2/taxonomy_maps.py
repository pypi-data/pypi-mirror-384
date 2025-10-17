import io
from functools import cache
from ruamel.yaml import YAML, yaml_object, add_representer
from . import yaml

from typing import TYPE_CHECKING, Optional, Union, Literal, Any, Dict

if TYPE_CHECKING:
    from .data_model import DataModel

from SIMULTAN.Data.Taxonomy import SimTaxonomyEntryReference, SimTaxonomyEntry, SimTaxonomyEntryReference, SimTaxonomy


@yaml_object(yaml)
class Content(object):

    yaml_tag = u'!Content'

    def __init__(self,
                 text_or_key: str,
                 name: Optional[str] = None,
                 property_name: Optional[str] = None,
                 slot_extension: Optional[str] = None,
                 type: Optional[Any] = None,
                 unit: Optional[str] = None,
                 documentation: Optional[str] = None,
                 component_policy: Optional[Literal['reference', 'subcomponent']] = 'subcomponent',
                 *args,
                 **kwargs):
        """
        Define a content/parameter/property of a taxonomy entry in the taxonomy map.

        :param args:
        :Keyword Arguments
            * *name* (``str``) -- name of the Taxonomy Entry in SIMULTAN
            * *text_or_key* (``str``) -- text or key of the content/parameter/property
            * *property_name* (``str``) -- name of the generated property
            * *slot_extension* (``str``) -- slot extension of the content/parameter/property
            * *type* (``str``) -- type of the content/parameter/property
            * *unit* (``str``) -- unit of the content/parameter/property
            * *documentation* (``str``) -- documentation of the content/parameter/property
            * *component_policy* (``str``) -- component add policy of the content/parameter/property, 'reference' or 'subcomponent'
        """

        self.name: str = name if name is not None else text_or_key # name of the Taxonomy Entry in SIMULTAN
        self.text_or_key: str = text_or_key          # text or key of the content/parameter/property
        self.property_name: str = property_name if property_name is not None else text_or_key  # name of the generated property in the python class
        self.slot_extension: str = slot_extension    # slot extension of the content/parameter/property
        self.type: Optional[Any] = type                        # type of the content/parameter/property
        self.unit: Optional[str] = unit                       # unit of the content/parameter/property
        self.documentation: Optional[str] = documentation       # documentation of the content/parameter/property
        self.component_policy: Literal['reference', 'subcomponent'] = component_policy  # component add policy of the content/parameter/property, 'reference' or 'subcomponent'

        self._taxonomies = {}
        self._taxonomy_entries = {}
        self._taxonomy_map: Optional['TaxonomyMap'] = kwargs.get('taxonomy_map', None)

        self.taxonomy_key: Optional[SimTaxonomy] = kwargs.get('taxonomy_key')

        add_kwargs = kwargs.copy()
        _ = [add_kwargs.pop(key, None) for key in ['taxonomy_name', 'taxonomy_key', 'taxonomy_entry_name',
                                                   'taxonomy_entry_key', 'content', 'documentation', 'python_mapper',
                                                   'mapped_class', 'unit', 'type', 'component_policy',
                                                   'text_or_key', 'property_name', 'slot_extension']]

        self.additional_attributes: dict[Any, Any] = add_kwargs

        self.taxonomy_key: Optional[SimTaxonomy]  = kwargs.get('taxonomy_key')
        self.taxonomy_name: str = kwargs.get('taxonomy_name')


    def get_taxonomie_entry(self, data_model: 'DataModel'):
        if self._taxonomy_entries.get(data_model, None) is None:

            if self.taxonomy_key is None:
                taxonomy = self._taxonomy_map.get_or_create_simultan_taxonomy(data_model=data_model, create=True)
            else:
                taxonomy = data_model.get_or_create_taxonomy(taxonomy_name=self.taxonomy_name,
                                                             taxonomy_key=self.taxonomy_key,
                                                             create=True)

            self._taxonomy_entries[data_model] = data_model.get_or_create_taxonomy_entry(name=self.name,
                                                                                         key=self.text_or_key,
                                                                                         description=self.documentation,
                                                                                         sim_taxonomy=taxonomy)
        return self._taxonomy_entries[data_model]

    def __repr__(self):
        return (f"Content({self.name}, {self.text_or_key}, "
                f"{self.property_name}, {self.slot_extension}, "
                f"{self.type}, {self.unit}, "
                f"{self.documentation}, {self.component_policy})")


verbose_output = False


@yaml_object(yaml)
class TaxonomyMap(object):

    yaml_tag = u'!TaxonomyMap'

    @classmethod
    def from_yaml_file(cls, filename):
        with open(filename, mode='r') as f:
            taxonomie_map = yaml.load(f)
        return taxonomie_map[0]

    def __init__(self,
                 taxonomy_key: str,
                 taxonomy_entry_key: str,
                 taxonomy_name: Optional[str] = None,
                 taxonomy_entry_name: Optional[str] = None,
                 content: Optional[list[Content]] = None,
                 documentation: Optional[str] = None,
                 *args,
                 **kwargs):

        self._content = []
        self._content_dict = {}
        self._parameter_taxonomy_entry_dict = {}

        self.taxonomy_key = taxonomy_key
        self.taxonomy_name = taxonomy_name if taxonomy_name is not None else taxonomy_key


        if self.taxonomy_key == taxonomy_entry_key:
            raise ValueError('taxonomy_key and taxonomy_entry_key must be different')

        self.taxonomy_entry_key = taxonomy_entry_key
        self.taxonomy_entry_name = taxonomy_entry_name if taxonomy_entry_name is not None else taxonomy_entry_key

        self.content = content if content is not None else []
        self.documentation = documentation

        self.python_mapper = kwargs.get('python_mapper', None)
        self.mapped_class = kwargs.get('mapped_class', None)

        self._taxonomies: Dict[DataModel, SimTaxonomy] = {}
        self._taxonomy_entries: Dict[DataModel, SimTaxonomyEntry] = {}

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value: list[Content]):
        self._content = value
        for content in self._content:
            content._taxonomy_map = self
        self._content_dict = {}

        self.get_content_by_property_name.cache_clear()
        self.get_content_by_text_or_key.cache_clear()

    @property
    def content_dict(self):
        if self._content_dict == {}:
            for content in self._content:
                self._content_dict[content.text_or_key] = content
        return self._content_dict

    @property
    def parameter_taxonomy_entry_dict(self):
        if not self._parameter_taxonomy_entry_dict:
            self._parameter_taxonomy_entry_dict = {content.property_name: content.text_or_key for content in self._content}
        return self._parameter_taxonomy_entry_dict

    def write(self, filename=None):
        if filename is not None:
            with open(filename, mode='w') as f:
                yaml.dump([self], f)
        else:
            f = io.StringIO()
            yaml.dump([self], f)
            return f.getvalue()

    def __getstate__(self):
        data = self.__dict__.copy()
        del data['python_mapper']
        del data['mapped_class']
        return data

    def add_content(self, content: Content):
        self._content.append(content)
        content._taxonomy_map = self
        self._content_dict = {}

    def get_or_create_simultan_taxonomy_entry(self,
                                              data_model: 'DataModel',
                                              create=True):

        if self._taxonomy_entries.get(data_model, None) is None:

            taxonomy_entries = data_model.get_taxonomy_entries(taxonomy=self.taxonomy_key)
            if self.taxonomy_entry_key in taxonomy_entries.keys():
                self._taxonomy_entries[data_model] = taxonomy_entries[self.taxonomy_entry_key]
            elif create:
                self._taxonomy_entries[data_model] = data_model.get_or_create_taxonomy_entry(
                    key=self.taxonomy_entry_key,
                    name=self.taxonomy_entry_name,
                    sim_taxonomy=self.get_or_create_simultan_taxonomy(data_model=data_model,
                                                                      create=create))
        return self._taxonomy_entries[data_model]

    def get_or_create_simultan_taxonomy(self,
                                        data_model: 'DataModel',
                                        create=True) -> SimTaxonomy:
        if self._taxonomies.get(data_model, None) is None:
            self._taxonomies[data_model] = data_model.get_or_create_taxonomy(
                taxonomy_name=self.taxonomy_name,
                taxonomy_key=self.taxonomy_key,
                description=self.documentation,
                create=create)

        return self._taxonomies[data_model]

    def get_slot(self, data_model: 'DataModel'):
        return SimTaxonomyEntryReference(self.get_or_create_simultan_taxonomy_entry(data_model=data_model,
                                                                                    create=True))

    @cache
    def get_content_by_property_name(self, property_name: str):
        return next((x for x in self.content if x.property_name == property_name), None)

    @cache
    def get_content_by_text_or_key(self, text_or_key: str):
        return next((x for x in self.content if x.text_or_key == text_or_key), None)
