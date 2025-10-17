Version 0.6.2 (28.03.2024)
- Added extended functionality to ComponentDictionary
- Bugfixing

Version 0.6.1 (24.02.2024)
- Bugfixes in default_types and File/Directory handling

Version 0.6.0.7 (16.02.2024)
- Fixed Asset creation and deletion bugs

Version 0.6.0.3 (23.01.2024)
- Added sub_classes and super_classes to SimultanObject

Version 0.6.0.2 (16.01.2024)
- Added __delitem__ method to default_types.ComponentList

Version 0.6.0.1 (15.01.2024)
- Updated SIMULTAN Version to 0.7.6
- Fixed bugs in default_types.ComponentList

Version 0.5.9.7 (09.01.2024)
- Added default component support to Mapper: if a default component is not present in the datamodel, it is automatically added
- Fixed content naming bug: Content.name is now used for the name of the TaxonomyEntry in SIMULTAN
- Added typing for better code completion

Version 0.5.9.4 (31.12.2024)
- Fixed bug in DirectoryInfo where __dir__helper_file__ was not found if already existing

Version 0.5.7 (11.12.2024)
- Added get_orientation_to_volume method to SimultanFace which returns the orientation of the face to the volume

Version 0.5.3 (01.12.2024)
- Added support for directories (Assets and FileInfo)

Version 0.5.1 (25.11.2024)

- setting re-register default in Mapper to True
- added uncache method to utils for monkey patching
