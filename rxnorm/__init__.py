import logging.config
import logging.handlers
from pathlib import Path
import sys
import os
import yaml

_prj = Path.cwd().parents[0]
sys.path.append(os.path.join(str(_prj), '..'))
_config = _prj.joinpath('smores','config')
_metapath = _config.joinpath('_metadata.py')
_logpath = _prj.joinpath('smores','logs')
_logconfig = _config.joinpath('logging.yaml')
if _logconfig.exists():
    with open(_logconfig, 'rt') as f:
        config = yaml.load(f.read())
    logging.config.dictConfig(config)