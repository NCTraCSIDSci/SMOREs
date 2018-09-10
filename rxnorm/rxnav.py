import requests
import logging
from rxnorm.errors import rxnorm_error
rxnavLog = logging.getLogger(__name__)

_api_url = 'https://rxnav.nlm.nih.gov/REST/'
def_wait = .300

def call_rxnav_api(call_type, rxcui, c_opt=''):
    payload = {}
    endpoint = '/'
    if call_type == 'STATUS':
        endpoint = 'rxcui/'+rxcui+'/status.json'
    elif call_type == 'ING':
        endpoint = 'rxcui/'+rxcui+'/related.json'
        payload['tty'] = r'IN+MIN'
    elif call_type == 'HISTORY':
        params = ''
    elif call_type == 'PROPERTY':
        endpoint = 'rxcui/'+rxcui+'/property.json'
        payload['propName'] = c_opt

    # TODO Write a call to get an RxNorm CUI for an input NDC
    # elif call_type =="NDC_2_RXC":

    else:
        _error = rxnorm_error('#Ax001.2')
        rxnavLog.error(str(_error) + '\n' + call_type + '\n')
        return False, _error, None
    api_call = _api_url + endpoint


    try:
        payload_str = "&".join("%s=%s" % (k, v) for k, v in payload.items())
        response = requests.get(api_call, params=payload_str)
        response.raise_for_status()
        rxnavLog.debug(response.url)
        return True, response.json(), response.url

    except (requests.ConnectionError, requests.Timeout):
        _error = rxnorm_error('#Ax001.1')
        rxnavLog.error(str(_error) + '\n' + api_call + '\n')
        return False, _error, api_call


def get_rxcui_status(rxcui, ret_detail=False) -> [bool, str]:
    success, response, api_url = call_rxnav_api('STATUS', rxcui)
    tty, name = '', ''
    if success:
        rxnavLog.debug('Good Response from API.')
        cui_status = str(response['rxcuiStatus']['status'])
        if ret_detail and 'minConceptGroup' in response['rxcuiStatus']:
            json_detail = response['rxcuiStatus']['minConceptGroup']['minConcept'][0]
            rxnavLog.debug(json_detail)
            tty = str(json_detail['tty']) if 'tty' in json_detail.keys() else 'UNK'
            name = str(json_detail['name']) if 'name' in json_detail.keys() else 'UNK'

        if cui_status in['Remapped', 'Quantified', 'Active', 'Obsolete'] and 'minConceptGroup' not in response['rxcuiStatus']:
            rxnorm_error('#Ax001.1', api_url)
            if ret_detail:
                return False, '#Ax001.1', None, None
            else:
                return False, '#Ax001.1'

        elif len(cui_status) == 0 or cui_status.upper() == 'UNKNOWN':
            rxnorm_error('#Ax001.4', api_url)
            if ret_detail:
                return False, '#Ax001.4', None, None
            else:
                return False, '#Ax001.4'
        else:
            if ret_detail:
                return True, cui_status, tty, name
            else:
                return True, cui_status
    else:
        rxnorm_error('#Ax000.1', api_url)
        return False, None


def validate_rxcui(rxcui, details=False):
    """ Simple check to see if an input code is an actual valid RXCUI
        Uses the "STATUS" API so we can repurpose the results and not make another call later.
        @details : Specifics if additional information or than the RxNorm status should be returned"""
    # print(get_rxcui_status(rxcui, details))
    return get_rxcui_status(rxcui, details)


def get_rxcui_ingredients(rxcui):
    success, response, api_url = call_rxnav_api('ING', rxcui)
    if success:
        rxnavLog.debug('Good Response from API.')
        json_list = response['relatedGroup']['conceptGroup']
        ing_list = {}

        for tty_group in json_list:
            if 'conceptProperties' in tty_group:
                temp_ings = []
                for ingredient in tty_group['conceptProperties']:
                    temp_ings.append(ingredient)
                if len(temp_ings) > 0:
                    ing_list[tty_group['tty']] = temp_ings
                rxnavLog.debug(ing_list)
        return True, ing_list
    else:
        rxnorm_error('#Ax002.1', api_url)
        return False, None