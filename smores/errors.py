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


def smores_error(error_id, supplement=None):
    error_class = get_class_re(error_id)
    error_subclass = get_subclass_re(error_id)
    error_descriptor = get_descriptor_re(error_id)
    try:
        error = smores_errors[error_class][error_subclass][error_descriptor]
    except KeyError:
        error = smores_errors['TBC']

    _message = error['message']
    if supplement is not None:
        _message = (_message + ' : {0}' + '\n').format(supplement)
    if error['alert'] == 'warn':
        smoresLog.warning(_message)
    elif error['alert'] == 'error':
        smoresLog.error(_message)
    else:
        smoresLog.info(_message)
    return error_id


smores_errors = {
    'TBC': {'message': 'Error Not Yet Coded', 'alert': 'error'},
    'C':
        {
            'class': 'Command Interface Errors',
            '001':
                {
                    'subclass': 'File Handling Errors',
                    '1': {'message': 'Input File Could Not Be Found', 'alert': 'error'},
                    '2': {'message': 'Permission Denied When Accessing File.\nMake Sure File Is Not Already Open',
                          'alert': 'error'},
                    '3': {'message': 'Invalid Status Provided', 'alert': 'error'},
                    '4': {'message': 'Output File/Path Could Not Be Found', 'alert': 'error'},
                    '5': {'message': 'No Data Was Provided. File Write Failed.', 'alert': 'error'},
                },
            '002':
                {
                    'sublcass': 'RXCui Class "Get/Find" Errors',
                    '1': {'message': 'Unable to add ingredients to RXCui', 'alert': 'warn'},
                },
            '003':
                {
                    'subclass': 'Medication Class "Get/Find" Errors'
                },
            '004':
                {
                    'subclass': 'Run Command Errors',
                    '1': {'message': 'Error In Obtaining Ingredients', 'alert': 'error'},
                    '2': {'message': 'Error in Obtaining Status', 'alert': 'error'},
                    '3': {'message': 'No Ingredients Found', 'alert': 'info'},
                    '4': {'message': 'An Invalid Object Was Provided', 'alert': 'error'}
                }
        },
    'A':
        {
            'class': 'File Input Read Errors',
            '000':
                {
                    'sublcass': 'Code Input Errors',
                    '1': {'message': 'Input RxCUI Rejected', 'alert': 'error'},
                    '2': {'message': 'Unknown API Call Type', 'alert': 'error'},
                    '3': {'message': 'Empty "CODE" Provided. Code not processed. Use "match" to attempt name '
                                     'matching to RXNORM', 'alert': 'info'}
                },
            '001':
                {
                    'subclass': 'RXCui Status Errors',
                    '1': {'message': 'API Error - Found a Status but Dead Ends', 'alert': 'warn'},
                    '2': {'message': 'API Error - Couldn\'t Find a CUI Status', 'alert': 'warn'},
                    '3': {'message': 'API Error - An Error Occurred Obtaining Status', 'alert': 'warn'}

                },
            '002':
                {
                    'subclass': 'RxCUI Ingredient Search Errors',
                    '1': {'message': 'API Error - An Error Occurred Obtaining Ingredients', 'alert': 'warn'}
                }

        },
    'B':
        {
            'class': 'RxNorm Class Errors',
            '001':
                {
                    'subclass': 'RXCui Class Set/Addition Errors',
                    '1': {'message': 'RxCUI Is Not Present in RxCUI List', 'alert': 'warn'},
                    '2': {'message': 'Invalid Term Type Provided', 'alert': 'warn'},
                    '3': {'message': 'Invalid Status Provided', 'alert': 'warn'}
                },
            '002':
                {
                    'sublcass': 'RXCui Class "Get/Find" Errors',
                    '1': {'message': 'Unable to add ingredients to RXCui', 'alert': 'warn'},
                    '2': {'message': 'Invalid RxCUI Encountered', 'alert': 'info'}
                }
        },
    'K':
        {
            'class': 'MedKit Processing Errors',
            '001':
                {
                    'subclass': 'General Processing',
                    '1': {'message': 'Invalid Object Type', 'alert': 'error'},
                    '2': {'message': 'Invalid Input Parameter', 'alert': 'error'}
                }
        },
    'M':
        {
            'class': 'Medication Class Errors',
            '001':
                {
                    'sublcass': 'Generic Errors',
                    '1': {'message': 'Medication does not have an available RxCui', 'alert': 'info'}
                },
            '002':
                {
                    'subclass': 'Definition Errors',
                    '1': {'message': 'Medication Property is Not Defined', 'alert': 'warn'},
                    '2': {'message': 'Invalid Name: No Value Provided', 'alert': 'error'},
                    '3': {'message': 'Invalid ID: No Value Provided', 'alert': 'error'},
                }
        }
}
