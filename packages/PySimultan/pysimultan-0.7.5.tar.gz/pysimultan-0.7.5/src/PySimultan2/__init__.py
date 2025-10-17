import os
import sys
import colorlog
from ruamel.yaml import YAML, add_representer

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .data_model import DataModel
    from .object_mapper import PythonMapper

def setup_logging():
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )

    handler.setFormatter(formatter)

    logger = colorlog.getLogger('PySimultan')
    logger.addHandler(handler)

    return logger


def setup():
    import colorlog
    try:
        import importlib.resources as pkg_resources
    except ImportError:
        # Try backported to PY<37 importlib_resources.
        import importlib_resources as pkg_resources

    from . import resources
    sys.path.append(str(pkg_resources.files(resources)))

    logger = colorlog.getLogger('PySimultan')
    logger.setLevel('DEBUG')

    dll_path = os.environ.get('SIMULTAN_SDK_DIR', None)
    if dll_path is None:
        with pkg_resources.path(resources, 'SIMULTAN.dll') as r_path:
            dll_path = str(r_path)
    sys.path.append(dll_path)

    from pythonnet import load
    from pythonnet import clr_loader, set_runtime
    list(clr_loader.find_runtimes())
    load('coreclr')
    import clr
    try:
        clr.AddReference('SIMULTAN')
    except Exception as e:
        test = clr.AddReference(
            os.path.join(dll_path, 'SIMULTAN.dll') if not dll_path.endswith('SIMULTAN.dll') else dll_path)
    clr.AddReference("System.Security.Cryptography")
    # clr.AddReference(os.path.join(dll_path, 'SIMULTAN'))

    from SIMULTAN.Data.Components import SimComponent

    continue_on_error = True

    def represent_none(self, _):
        return self.represent_scalar('tag:yaml.org,2002:null', '')

    add_representer(type(None), represent_none)
    yaml = YAML()
    yaml.default_flow_style = None
    yaml.preserve_quotes = True
    yaml.allow_unicode = True

    return yaml


logger = setup_logging()
yaml = setup()


class Config:
    def __init__(self):
        self._default_data_model = None
        self._default_mapper = None
        self.logger = logger

    def get_default_data_model(self, *args, **kwargs) -> 'DataModel':
        return self._default_data_model

    def get_default_mapper(self, *args, **kwargs) -> 'PythonMapper':
        return self._default_mapper

    def set_default_data_model(self, data_model: 'DataModel'):
        self.logger.debug(f'set_default_data_model: {id(data_model)}')
        self._default_data_model = data_model

    def set_default_mapper(self, mapper: 'PythonMapper'):
        self.logger.debug(f'set_default_mapper: {id(mapper)}')
        self._default_mapper = mapper


config = Config()

from .data_model import DataModel
from .files import FileInfo
from .object_mapper import PythonMapper
from .taxonomy_maps import Content, TaxonomyMap
