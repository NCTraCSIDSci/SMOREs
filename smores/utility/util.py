# Python Lib Imports
import collections , ntpath
from pathlib import Path
import sys, os
import re
from smores.utility.errors import smores_error

OPTIONS_RXNSTATUS = ['LOCAL', 'RXCUI', 'NDC', 'SNOMED','CPT']
RXNORM_TTY_SUPPORT_DICT = {'SBD': {'name': 'Semantic Branded Drug'},
    'SCD': {'name': 'Semantic Clinical Drug'},
    'IN': {'name': 'Ingredient'},
    'MIN': {'name': 'Multi-Ingredient'},
    'PIN': {'name': 'Precise Ingredient'},
    'BN': {'name': 'Branded Name'},
    'SBDC': {'name': 'Semantic Branded Drug Component'},
    'SCDC': {'name': 'Semantic Clinical Drug Component'},
    'DF': {'name': 'Dose Form'},
    'SCDF': {'name': ''},
    'SBDF': {'name': ''},
    'GPCK': {'name': ''},
    'BPCK': {'name': ''}
}

FHIR_CODESET_SYSTEMS = {
    'RXNORM': 'http://www.nlm.nih.gov/research/umls/rxnorm',
    'NDC': 'http://hl7.org/fhir/sid/ndc',
    'SNOMEDCT_US': 'http://snomed.info/sct'
}

UMLS_VALID_SRCS = {
    'MED-RT': 'Medication Reference Terminology',
    'NDFRT': 'National Drug File - Reference Terminology',
    'RXNORM': 'RXNORM',
    'SNOMEDCT_US': 'US Edition of SNOMED CT',
    'CPT': 'Current Procedural Terminology',
    'HCPCS': 'Healthcare Common Procedure Coding System'
}

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten_dict(v, parent_key=new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_filename(path):
    if type(path) is Path:
        return path.name
    else:
        head, tail = ntpath.split(path)
        # file, ext = os.path.splitext(tail or ntpath.basename(head))
        return tail


def validate_id(id, id_type):
    re_dict = {'NDC': r'(\d{4}\-\d{4}\-\d{2}|\d{5}\-\d{3}\-\d{2})|(\d{5}\-\d{4}\-\d{1,2})|(\d{5}\-\*\d{3}-\d{2}|\d{11})',
               'CPT': r'(\d{4}[A-Z0-9]|[A-Z]{1}\d{4}',
               'RXCUI': None,
               'RXNORM': None,
               'SNOMED': None,
               'LOCAL': None}
    if re_dict[id_type] is not None:
        valid_id_check = True if re.match(re_dict[id_type], id) is not None else False
        if not valid_id_check:
            print('{0} is not a valid format of ID Type {1}'.format(id, id_type))
    else:
        # TODO Are there valid RegEx patterns for other ID types?
        valid_id_check = True if len(id) > 0 else False
    return valid_id_check


def resolve_target_path(target):
    if ':\\' in target:
        target_path = Path(target).resolve()
    elif 'tests/' in target:
        target_path = Path("..", 'tests', target).resolve()
    else:
        target_path = Path("..", 'input', target).resolve()

    try:
        if target_path.exists():
            return target_path
        else:
            raise FileNotFoundError

    except FileNotFoundError:
        smores_error("#Cx001.1")
        return False
    except PermissionError:
        smores_error('#Cx001.2')
        return False
    except OSError as e:
        smores_error('#Cx001.6', supplement=e, console_p=True)
        return False
    except BaseException as e:
        smores_error('#Cx001.6', supplement=e, console_p=True)
        return False, None

def get_util_base(type):
    i = 0
    _prj = Path.cwd()
    if 'smores' in _prj.parts:
        while True:
            head, tail = os.path.split(_prj)
            if(tail == 'smores'):
                _prj=Path.cwd()
                return _prj
            _par = _prj.parents[i]
            head, tail = os.path.split(_par)
            if tail == 'smores':
                _prj = _prj.parents[i+1]
                break
            else:
                i += 1
    elif _prj.name == 'scripts':
        _prj = _prj.parent

    sys.path.append(str(_prj))
    if type == 'config':
        return _prj.joinpath('smores', 'config')
    elif type == 'cache':
        return _prj.joinpath('smores', 'cache')
    else:
        return _prj


def get_version():
    from smores.smoresCLI import smoresCLI
    return smoresCLI.client_version


def get_api_key(API:str):
    config_keys = {
        'FDA': 'FDA_API_KEY',
        'UMLS': 'UMLS_API_KEY'
    }

    conf = read_config_value('API_KEY')
    key = conf[config_keys[API].lower()]
    validated_key = key if key.upper() != 'NONE' and len(key) > 1 else 'NONE'
    return validated_key


def read_config_value(setting):
    import configparser as cf
    config_path = get_util_base('config').joinpath('config.ini')
    config = cf.ConfigParser()
    try:
        config.read(config_path)

        if setting == 'INFILE_KEYS':
            index = 'INPUT_FILE'
        elif setting == 'OUTPUT_CONF':
            index = 'OUTPUT_FILE'
        elif setting == 'API_KEY':
            index = 'API_CONFIG'
        return {item.lower(): value for item, value in config[index].items()}
    except KeyError:
        smores_error('TBD')
        return None
    except FileNotFoundError:
        smores_error('#Cx001.1', console_p=True, supplement='config.ini')
        return None
    except PermissionError:
        smores_error('#Cx001.2', console_p=True, supplement='config.ini')
        return None

def harmonize_cui_status(in_status):
    return

