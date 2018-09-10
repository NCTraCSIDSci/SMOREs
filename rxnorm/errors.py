import re
import logging
rxnormLog = logging.getLogger(__name__)


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


def rxnorm_error(error_id, supplement=None):
    error_class = get_class_re(error_id)
    error_subclass = get_subclass_re(error_id)
    error_descriptor = get_descriptor_re(error_id)
    try:
        error = rxnorm_errors[error_class][error_subclass][error_descriptor]
    except KeyError:
        error = rxnorm_errors['TBC']

    _message = error['message']
    if supplement is not None:
        _message = (_message+' : {0}' + '\n').format(supplement)
    if error['alert'] == 'warn':
        rxnormLog.warning(_message)
    elif error['alert'] == 'error':
        rxnormLog.error(_message)
    else:
        rxnormLog.info(_message)
    return error_id

rxnorm_errors = {
    'TBC': {'message': 'Error Not Yet Coded', 'alert': 'error'},
    'A':
        {
            'class': 'RxNav API Errors',
            '000':
                {
                    'sublcass': 'Generic API Call Errors',
                    '1': {'message': 'API Call Produced Unexpected Error', 'alert': 'error'},
                    '2': {'message': 'Unknown API Call Type', 'alert': 'error'}
                },
            '001':
                {
                    'subclass': 'RXCui Status Errors',
                    '1': {'message': 'API Error - Found a Status but Dead Ends', 'alert': 'info'},
                    '2': {'message': 'API Error - Couldn\'t Find a CUI Status', 'alert': 'warn'},
                    '3': {'message': 'API Error - An Error Occurred Obtaining Status', 'alert': 'warn'},
                    '4': {'message': 'API Error - An Invalid RxCUI Was Provided to the API', 'alert': 'error'}

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
                    '0': {'message': 'RxCUI is Not Valid', 'alert': 'warn'},
                    '1': {'message': 'RxCUI Is Not Present in RxCUI List', 'alert': 'warn'},
                    '2': {'message': 'Invalid Term Type Provided', 'alert': 'warn'},
                    '3': {'message': 'Invalid Status Provided', 'alert': 'warn'}
                },
            '002':
                {
                    'sublcass': 'RXCui Class "Get/Find" Errors',
                    '1': {'message': 'Unable to add ingredients to RXCui', 'alert': 'warn'}
                }
        }
}
