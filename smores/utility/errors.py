import re
import logging
smoresLog = logging.getLogger(__name__)


def get_class_re(id):
    pattern = r'(?<=^#)[A-Z]{1}'
    r = re.compile(pattern)
    try:
        return r.search(id).group()
    except AttributeError:
        return None

def get_subclass_re(id):
    pattern = r'(?<=x)(\d{1,3})'
    r = re.compile(pattern)
    try:
        return r.search(id).group()
    except AttributeError:
        return None


def get_descriptor_re(id):
    pattern = r'(?<=\.)(\d{1,})'
    r = re.compile(pattern)
    try:
        return r.search(id).group()
    except AttributeError:
        return None


def smores_error(error_id, supplement=None, console_p=False, logger=None):
    error_class = get_class_re(error_id)
    error_subclass = get_subclass_re(error_id)
    error_descriptor = get_descriptor_re(error_id)
    logFile = logger if logger is not None else smoresLog

    try:
        error = smores_errors[error_class][error_subclass][error_descriptor]
    except KeyError:
        error = smores_errors['TBC']

    _message = error['message']
    if supplement is not None:
        _message = (_message + ' : \n {0}').format(supplement)

    if error['alert'] == 'warn':
        logFile.warning(_message)
    elif error['alert'] == 'error':
        logFile.error(error_id + ' ' + _message)
    else:
        logFile.info(_message)

    if console_p:
        print('\n'+_message)
    return error_id

"""
    SMOREs Errors follow a consistent format for tracing:
    Example : #Cx001.2
    #C: represents the Class of error / the system involved. Always a character prefixed by '#'
        - #C = Command Interface Errors
    x001: sub section of that class, or grouping of errors related to a specific functionality. Always a 3 digit value prefixed by 'x'
        - x001 = File Handling Errors
    .2: The specific error that has been triggered. Always an integer prefixed by '.'
        - .2 = Permission Denied
"""
smores_errors = {
    'TBC': {'message': 'Error Not Yet Coded', 'alert': 'error'},
    'A': { 'class': 'API Errors',
        '000': {'subclass': 'Generic Errors',
            '1': {'message': 'API Call Produced Unexpected Error', 'alert': 'error'},
            '2': {'message': 'Invalid API Call Type', 'alert': 'error'},
            '3': {'message': 'API Produced 404 Error', 'alert': 'error'},
            '4': {'message': 'KeyError: Invalid value for Payload Parameter', 'alert': 'error'}
         },
        '001': { 'subclass': 'RXNav API Errors',
            '1': {'message': 'RXNav API Call Failed', 'alert': 'error'},
            '2': {'message': 'Incomplete Results Received from API', 'alert': 'error'},
            '3': {'message': 'Failed to Find RxCUI Status', 'alert': 'error'},
            '4': {'message': 'Invalid RxCUI Provided to API', 'alert': 'error'},
            '5': {'message': 'RxCUI is Retired', 'alert': 'info'},
            '6': {'message': 'RxCUI Status Has Dead End', 'alert': 'info'},
            '7': {'message': 'RxCUI Has Been Quantified', 'alert': 'info'},
            '8': {'message': 'RxCUI Has Been Remapped', 'alert': 'info'},
            '9': {'message': 'Invalid idType provided to API', 'alert': 'error'},
            '10': {'message': 'KeyError: Invalid value for Payload Parameter', 'alert': 'error'}
        },
        '002': { 'subclass': 'openFDA API Errors',
            '1': {'message': 'openFDA API Call Failed', 'alert': 'error'},
            '2': {'message': 'Incomplete Results Received from API', 'alert': 'error'}
        }
    },
    'C': { 'class': 'Command Interface Errors',
        '000': { 'subclass': 'Generic Console Errors',
            '1': {'message': '', 'alert': ''}
        },
        '001': { 'subclass': 'File Handling Errors',
            '1': {'message': 'Input File Could Not Be Found', 'alert': 'critical'},
            '2': {'message': 'Permission Denied When Accessing File.\nMake Sure File Is Not Already Open', 'alert': 'error'},
            '3': {'message': 'Output File/Path Could Not Be Found', 'alert': 'error'},
            '4': {'message': 'No Data Provided. File Write Failed.', 'alert': 'error'},
            '5': {'message': 'OSError - Connection to data appears to have been interrupted', 'alert': 'critical'},
            '6': {'message': 'KeyError - A required column value is missing '
                             'from the configuration file or is not properly formatted', 'alert': 'critical'}
        },
        '002': { 'subclass': 'Command Run Errors',
            '1': {'message': 'Error in Obtaining Results for Command', 'alert': 'error'}
        },
        '003': { 'subclass': 'Command Validation',
            '1': {'message': 'Invalid Parameter Provided', 'alert': 'error'},
            '2': {'message': 'Too Many Parameters Provided', 'alert': 'error'}
        }
    },
    'M': { 'class': 'Medication Class Errors',
        '000': { 'subclass': 'Generic Medication Errors',
            '1': {'message': 'Medication does not have an available CUI', 'alert': 'info'},
            '2': {'message': 'Invalid CUI attempted to be added to Medication', 'alert': 'warn'},
            '3': {'message': 'Medication Property is Not Defined', 'alert': 'warn'},
            '4': {'message': 'Invalid Name: No Value Provided', 'alert': 'error'},
            '5': {'message': 'Invalid ID: No Value Provided', 'alert': 'error'}
        },
        '001': { 'subclass': 'LocalMedication Specific Errors',
            '1': {'message': '', 'alert': ''}
        },
            '002': { 'subclass': 'RXCUI Specific Errors',
                '1': {'message': 'Invalid RxCUI Encountered', 'alert': 'error'},
                '2': {'message': 'RxCUI Is Not Present in RxCUI List', 'alert': 'warn'},
                '3': {'message': 'Invalid Term Type Provided', 'alert': 'warn'},
                '4': {'message': 'Invalid Status Provided', 'alert': 'warn'},
                '5': {'message': 'Unable to add ingredients to RXCUI', 'alert': 'warn'}
        },
        '003': { 'subclass': 'NDC Specific Errors',
            '1': {'message': 'Invalid NDC Encountered', 'alert': 'error'}
        }
    },
    'K': { 'class': 'MedKit Class Errors',
        '000': {'subclass': 'Generic MedKit Errors',
            '1': {'message': 'MedKit of the Name Does Not Exist', 'alert': 'error'}
        },
        '001': {'subclass': 'Processing Errors',
            '1': {'message': 'Invalid Object Type', 'alert': 'error'},
            '2': {'message': 'Invalid Input Parameter', 'alert': 'error'}
        }
    }
}
