# Python Lib Modules
import os
import re
import sys
from datetime import datetime, timedelta
import time
import logging
import json
# Community Modules
import requests
import requests_cache
# SMOREs Internal Imports
from smores.utility.errors import smores_error
from smores.utility.Authenticate import Authenticate
from requests import Session
import smores.utility.util as util

APIlog = logging.getLogger(__name__)


class SMORESapi:
    import smores.utility.util as util
    cache_base = util.get_util_base('cache')
    expire_after = timedelta(hours=48)
    e_class = '#A'
    e_subclass = 'x000'

    def __init__(self):
        self.api_url = ''
        self.api_name = ''
        self.api_short = ''
        self.cache = None
        self.endpoints = {}
        self.e_subclass = SMORESapi.e_subclass
        self.def_wait = 100  # in milliseconds
        self.last_call = None

    def get_endpoint(self, api_call):
        try:
            return self.endpoints[api_call]
        except KeyError:
            smores_error(self.get_e('2', c_ovrd=SMORESapi.e_subclass), [api_call, self.api_name], logger=APIlog)
            return False

    def call_api(self, call_type, val, c_opt=None):
        if self.last_call is None or ((datetime.today() - self.last_call).total_seconds() * 1000) > self.def_wait:
            pass
        else:
            time.sleep(self.def_wait)
            self.last_call = datetime.today()

        payload = {}
        endpoint = self.get_endpoint(call_type)
        api_call = self.api_url + endpoint['base']

        if endpoint:
            api_call = re.sub(r'\*CODE\*', str(val), api_call)

            for _pl, _p in endpoint['payload'].items():
                if type(_p) is list:
                    if _pl == 'regex':
                        for i in range(len(_p)):
                            _re = re.compile('\*' + str(_p[i]) + '\*')
                            api_call = re.sub(_re, str(c_opt[_p[i]]), api_call)
                    else:
                        if _p[1] == 'PRIMARY':
                            _pl_val = val
                        elif c_opt is not None and _p[1] in c_opt:
                            _pl_val = c_opt[_p[1]]
                        else:
                            smores_error(self.get_e('4', c_ovrd=SMORESapi.e_subclass), [self.api_short, _pl],
                                         logger=APIlog)
                            return False
                        payload[_pl] = _p[0] + str(_pl_val)
                else:
                    if _p == 'PRIMARY':
                        _pl_val = val
                    elif c_opt is not None and type(c_opt) is str:
                        _pl_val = c_opt
                    elif c_opt is not None and type(c_opt) is dict:
                        _pl_val = c_opt[_pl]
                    elif _p is not None:
                        _pl_val = _p
                    else:
                        smores_error(self.get_e('4', c_ovrd=SMORESapi.e_subclass), [self.api_short, _pl], logger=APIlog)
                        return False
                    payload[_pl] = str(_pl_val)

        else:
            smores_error(self.get_e('2'), [api_call, self.api_name], logger=APIlog)
            return False

        try:
            payload_str = "&".join("%s=%s" % (k, v) for k, v in payload.items())
            response = requests.get(api_call, params=payload_str)
            response.raise_for_status()
            if response.from_cache:
                APIlog.info('API Results from cache: %s', response.url)
            response.encoding = 'utf-8'
            try:
                json_data = response.json()
            except ValueError:
                json_data = json.load(response.text)
            return True, json_data, response.url
        except (requests.ConnectionError, requests.Timeout) as e:
            smores_error(self.get_e('1', c_ovrd=SMORESapi.e_subclass), [api_call, self.api_name, e], logger=APIlog)
            return False, api_call, None
        except requests.exceptions.HTTPError as e:
            smores_error(self.get_e('3', c_ovrd=SMORESapi.e_subclass), [api_call, self.api_name, e], logger=APIlog)
            return False, api_call, None

    def get_e(self, e, c_ovrd=None):
        if c_ovrd is not None:
            return '{0}{1}.{2}'.format(SMORESapi.e_class, c_ovrd, e)
        else:
            return '{0}{1}.{2}'.format(SMORESapi.e_class, self.e_subclass, e)


class openFDA(SMORESapi):
    # TODO Need to Add Function to Check if Device NDC
    requests_cache.install_cache(str(SMORESapi.cache_base.joinpath('openfda_cache').absolute()),
                                 backend='sqlite',
                                 expire_after=SMORESapi.expire_after)

    def __init__(self, delay=300, api_key=None):
        super(openFDA, self).__init__()

        self.api_url = 'https://api.fda.gov/drug/'
        self.def_wait = delay
        self.api_name = 'openFDA - US Food and Drug Administration API'
        self.api_short = 'openFDA API'
        self.cache = None
        self.e_subclass = 'x002'
        self.api_key = api_key if api_key != 'NONE' and api_key is not None else None
        self.endpoints = {
            'PACK_STATUS': {
                'base': 'ndc.json',
                'payload': {
                    'search': ['packaging.package_ndc:', 'PRIMARY']
                }
            },
            'PRODUCT': {
                'base': 'ndc.json',
                'payload': {
                    'search': ['product_ndc:', 'PRIMARY']
                }
            },
            'RXN_LOOKUP': {
                'base': 'ndc.json',
                'payload': {
                    'search': ['openfda.rxcui:', 'PRIMARY']
                }
            }
        }
        if self.api_key is not None:
            for endpoint in self.endpoints.values():
                if 'api_key' not in endpoint['payload'].keys():
                    endpoint['payload']['api_key'] = self.api_key

    def get_ndc_base(self, ndc):
        """
        Returns base information on a provided NDC code from the openFDA API
        :param ndc: str of valid NDC format
        :return: NONE or dict{ndc, name, status}
        """
        success, response, api_url = self.call_api('PACK_STATUS', ndc)
        _r, package_ndc, generic, brand, dose, form = (None for i in range(6))
        if success and 'error' not in response.keys():
            results = response['results'][0]
            if len(results['packaging']) > 1:
                for _ndc in results['packaging']:
                    if _ndc['package_ndc'] == ndc:
                        package_ndc = _ndc['package_ndc']
                if package_ndc is None:
                    package_ndc = results['product_ndc']
            else:
                package_ndc = results['packaging'][0]['package_ndc']
            _ndc = self.process_ndc(results)
            _r = {'ndc': package_ndc, 'name': _ndc['name'], 'status': _ndc['status']}
        else:
            smores_error(self.get_e('1'), api_url, logger=APIlog)
        return _r

    def get_ndc_rxnorm(self, ndc):
        success, response, api_url = self.call_api('PACK_STATUS', ndc)
        _r = None
        if success and 'error' not in response.keys():
            results = response['results'][0]
            try:
                _r = results['openfda']['rxcui']
            except KeyError:
                _r = None
                smores_error(self.get_e('2'), api_url, logger=APIlog)
        else:
            smores_error(self.get_e('1'), api_url, logger=APIlog)

        return _r

    def get_rxnorm_ndc(self, rxcui):
        """
        Lookup all corresponding NDC's for a provided RXCUI
        :param rxcui: Input RXCUI
        :return: list of NDC codes
        """
        success, response, api_url = self.call_api('RXN_LOOKUP', rxcui)
        _r = None
        if success and 'error' not in response.keys():
            results = response['results'][0]
            ndc_list = self.process_ndc(results)
            try:
                _r2 = ndc_list['packaging']
                _r = []
                for _ndc in _r2:
                    __r = _ndc['package_ndc']
                    _r.append(__r)
            except KeyError:
                smores_error(self.get_e('2'), api_url, logger=APIlog)
                return None
            else:
                return _r
        else:
            smores_error(self.get_e('1'), api_url, logger=APIlog)

    def get_ndc_product(self, ndc):
        success, response, api_url = self.call_api('PRODUCT', ndc)
        if success and 'error' not in response.keys():
            results = response['results'][0]
            _r = self.process_ndc(results)
        else:
            smores_error(self.get_e('1'), api_url, logger=APIlog)
        return _r

    def get_ndc_by_rxcui(self, rxcui):
        """
        DEPRECATED
        Lookup all corresponding NDC's for a provided RXCUI
        :param rxcui:
        :return: List of dict of NDC's with NDC base
        """
        success, response, api_url = self.call_api('CROSSWALK', rxcui)
        if success and 'error' not in response.keys():
            results = response['results']
            ndc_list = []
            for result in results:
                _r = self.process_ndc(result)
                if _r is not None:
                    ndc_list.append(_r)
            return ndc_list

    def process_ndc(self, ndc_data):
        try:
            _r_keys = ndc_data.keys()
            if len(_r_keys) == 0:
                return None
            _r, product_ndc, package_ndc, generic, brand, dose, form, unii = (None for i in range(8))

            product_ndc = ndc_data['product_ndc'] if 'product_ndc' in _r_keys else False
            generic = ndc_data['generic_name'] if 'generic_name' in _r_keys else False
            brand = ndc_data['brand_name'] if 'brand_name' in _r_keys else False
            _dose = [ing['strength'] for ing in
                     ndc_data['active_ingredients']] if 'active_ingredients' in _r_keys else False
            form = ndc_data['dosage_form']
            dose = '(' + '|'.join(_d for _d in _dose) + ')' if _dose else ''
            unii = ndc_data['openfda']['unii']
            package_ndc = ndc_data['packaging'] if 'packaging' in _r_keys else False
            if generic and brand:
                _base = generic + ' [' + brand + ']'
            elif generic:
                _base = generic
            elif brand:
                _base = brand
            else:
                _base = ''
            full_name = ' '.join([_base, dose, form]).upper()
            _list_expire = datetime.strptime(ndc_data[
                                                 'listing_expiration_date' if 'listing_expiration_date' in _r_keys else 'marketing_end_date'],
                                             '%Y%m%d')
            _d = datetime.today()
            status = 'valid' if _list_expire > _d else 'expired'
            _r = {'ndc': product_ndc, 'name': full_name, 'status': status, 'unii': unii}
            if package_ndc:
                _r['packaging'] = package_ndc
        except KeyError:
            _r = None
            smores_error(self.get_e('2'), '', logger=APIlog)
        else:
            return _r

    def validate(self, ndc):
        return True if self.get_ndc_base(ndc) is not None else False


class RXNAV(SMORESapi):
    RXNAV_VALID_IDS = ['AMPID', 'ANADA', 'ANDA', 'ATC', 'BLA', 'CVX', 'Drugbank', 'GCN_SEQNO', 'GFC', 'HCPCS',
                       'HIC_SEQN', 'MESH', 'MMSL_CODE', 'NADA', 'NDA', 'NDC', 'NUI', 'SNOMEDCT', 'SPL_SET_ID',
                       'UMLSCUI', 'UNII_CODE', 'USP', 'VUID']
    requests_cache.install_cache(str(SMORESapi.cache_base.joinpath('rxnav_cache').absolute()),
                                 backend='sqlite',
                                 expire_after=SMORESapi.expire_after)

    def __init__(self, delay=100):
        super(RXNAV, self).__init__()

        self.api_url = 'https://rxnav.nlm.nih.gov/REST/'
        self.def_wait = delay
        self.api_name = 'RxNav - NLM RxNorm API'
        self.api_short = 'RxNav API'
        self.e_subclass = 'x001'
        self.last_call = None
        self.endpoints = {
            'STATUS': {
                'base': 'rxcui/*CODE*/status.json',
                'payload': {}
            },
            'ING': {
                'base': 'rxcui/*CODE*/related.json',
                'payload': {'tty': r'IN+MIN'}
            },
            'HISTORY': {
                'base': 'rxcuihistory/concept.json',
                'payload': {'rxcui': 'PRIMARY'}
            },
            'PROPERTY': {
                'base': 'rxcui/*CODE*/property.json',
                'payload': {'propName': ''}
            },
            'ID_LOOKUP': {
                'base': 'rxcui.json',
                'payload': {'idtype': '', 'id': 'PRIMARY'}
            },
            'NDC_STATUS': {
                'base': 'ndcstatus.json',
                'payload': {'ndc': 'PRIMARY'}
            }
        }

    def get_cui_base(self, rxcui):
        success, response, api_url = self.call_api('STATUS', rxcui.cui)
        error_index = {'Remapped': '5', 'Quantified': '8', 'Active': '1', 'Obsolete': '6', 'Retired': '5', 'Alien': '5'}
        if success and response is not None:
            APIlog.debug('Good Response from API.')
            try:
                rxcui.set_status(str(response['rxcuiStatus']['status']))
                json_detail = response['rxcuiStatus']['minConceptGroup']['minConcept'][0]
                APIlog.debug(json_detail)
                rxcui.set_tty(str(json_detail['tty']) if 'tty' in json_detail.keys() else 'UNK')
                rxcui.set_name(str(json_detail['name']) if 'name' in json_detail.keys() else 'UNK')
            except KeyError or IndexError:
                smores_error(self.get_e('2'), api_url, logger=APIlog)
                return False
            else:
                return True
        else:
            smores_error(self.get_e('1'), api_url, logger=APIlog)
            return None

    def get_cui_status(self, rxcui) -> [bool, str]:
        success, response, api_url = self.call_api('STATUS', rxcui)
        e_index = {'remapped': '5', 'quantified': '7', 'active': '6', 'obsolete': '5', 'retired': '5', 'alien': '4',
                   'non-rxnorm': '4', 'never%20active': '4', 'unknown': '4'}
        if success and response is not None:
            APIlog.debug('Good Response from API.')
            _r, cui_status = False, None
            try:
                cui_status = str(response['rxcuiStatus']['status']).upper()

                if cui_status.upper() in ['REMAPPED', 'QUANTIFIED', 'ACTIVE', 'OBSOLETE', 'RETIRED'] \
                        and 'minConceptGroup' not in response['rxcuiStatus']:
                    smores_error(self.get_e(e_index[cui_status.lower()]), rxcui, logger=APIlog)
                    _r = True

                elif cui_status.upper() in ['ALIEN', 'NON-RXNORM', ' NEVER%20ACTIVE']:
                    smores_error(self.get_e(e_index[cui_status.lower()]), rxcui, logger=APIlog)
                    _r = False

                elif len(cui_status) == 0 or cui_status.upper() == 'UNKNOWN':
                    smores_error(self.get_e(e_index[cui_status.lower()]), rxcui, logger=APIlog)
                    _r = False
                else:
                    _r = True

            except KeyError or IndexError:
                smores_error(self.get_e(e_index[cui_status.lower()] if cui_status is not None else '4' ), api_url, logger=APIlog)
                return False, None
            else:
                return _r, cui_status
        else:
            smores_error(self.get_e('1'), api_url, logger=APIlog)
            return False, None

    def validate(self, rxcui):
        """ Simple check to see if an input code is an actual valid RXCUI
            Uses the "STATUS" API so we can repurpose the results and not make another call later.
            @details : Specifics if additional information or than the RxNorm status should be returned"""
        valid, _ = self.get_cui_status(rxcui)
        return valid

    def get_rxcui_ingredients(self, rxcui):
        success, response, api_url = self.call_api('ING', rxcui)
        if success:
            APIlog.debug('Good Response from API.')
            json_list = response['relatedGroup']['conceptGroup']
            ing_list = {}

            for tty_group in json_list:
                if 'conceptProperties' in tty_group:
                    temp_ings = []
                    for ingredient in tty_group['conceptProperties']:
                        temp_ings.append(ingredient)
                    if len(temp_ings) > 0:
                        ing_list[tty_group['tty']] = temp_ings
                    APIlog.debug(ing_list)
            return ing_list
        else:
            smores_error(self.get_e('1'), api_url, logger=APIlog)
            return None

    def get_remap_cuis(self, rxcui):
        success, response, api_url = self.call_api('STATUS', rxcui)
        remapped = []
        if success and response is not None:
            APIlog.debug('Good Response from API.')
            try:
                json_detail = response['rxcuiStatus']['minConceptGroup']['minConcept']
                remapped = [index['rxcui'] for index in json_detail]
            except KeyError:
                pass
        else:
            smores_error(self.get_e('1'), api_url, logger=APIlog)
        return remapped

    def get_historical_info(self, rxcui, target='rxcuiConcept'):
        success, response, api_url = self.call_api('HISTORY', rxcui)
        if success and response is not None:
            APIlog.debug('Good Response from API.')
            if target not in response['rxcuiHistoryConcept'].keys():
                smores_error('#Ax000.1', api_url, logger=APIlog)
                return False
            elif response['rxcuiHistoryConcept']['rxcuiConcept'] == 'Not Found':
                smores_error('#Ax003.2', api_url, logger=APIlog)
                return False
            else:
                json_detail = response['rxcuiHistoryConcept'][target]
                APIlog.debug(json_detail)
                return json_detail
        else:
            smores_error(self.get_e('1'), api_url, logger=APIlog)
            return False

    def get_rxcui_by_id(self, id, idType):
        VALID_ID_TYPES = RXNAV.RXNAV_VALID_IDS
        api_success, api_results = False, None
        if idType.upper() in VALID_ID_TYPES:
            alt_src_r = None
            # If it's an NDC code, try the NDC API first
            if idType.upper() == 'NDC':
                alt_src_r = openFDA().get_ndc_rxnorm(id)

            _clean_id = id.copy()
            if idType == 'NDC' and len(_clean_id) < 11:
                _zeroes = 11 - len(_clean_id)
                for i in range(_zeroes):
                    _clean_id = '0' + _clean_id
            api_success, response, api_url = self.call_api('ID_LOOKUP', _clean_id, idType)
            if api_success and response is not None:
                APIlog.info('Good Response from API : %s', api_url)
                json_detail = []
                # idGroup -- idType, id
                # rxnormId -- Array[#]
                try:
                    json_detail = response['idGroup']['rxnormId']
                    APIlog.debug(json_detail)
                except KeyError or IndexError:
                    smores_error(self.get_e('10'), api_url, logger=APIlog)
                finally:
                    if alt_src_r is not None:
                        api_results = json_detail + list(set(alt_src_r) - set(json_detail))
                        api_success = True
                        APIlog.info('%s : Combined multiple API results for RxCUI\'s', '{0}.{1}'.format(id, idType))
                    else:
                        api_results = json_detail
                return api_success, api_results
            else:
                smores_error(self.get_e('1'), api_url, logger=APIlog)
        else:
            smores_error(self.get_e('9'), 'idType:{0}'.format(idType), logger=APIlog)
            return False, None


class RXNDC(SMORESapi):
    requests_cache.install_cache(str(SMORESapi.cache_base.joinpath('rxndc_cache').absolute()),
                                 backend='sqlite',
                                 expire_after=SMORESapi.expire_after)

    def __init__(self, delay=100):
        super().__init__()

        self.api_url = 'https://rxnav.nlm.nih.gov/REST/'
        self.def_wait = delay
        self.api_name = 'RxNav - NLM RxNorm API for NDC Specific Lookups'
        self.api_short = 'RxNav API'
        self.e_subclass = 'x001'
        self.endpoints = {
            'NDC_STATUS': {
                'base': 'ndcstatus.json',
                'payload': {'ndc': 'PRIMARY'}
            },
            'NDC_LOOKUP': {
                'base': 'allhistoricalndcs.json',
                'payload': {'rxcui': 'PRIMARY'}
            }
        }

    def get_cui_base(self, ndc):
        if len(ndc) < 11:
            _zeroes = 11 - len(ndc)
            for i in range(_zeroes):
                ndc = '0' + ndc

        success, response, api_url = self.call_api('NDC_STATUS', ndc)
        e_class = ''
        _r, status, name = (None for i in range(3))
        if success and response is not None:
            APIlog.debug('Good Response from API.')
            try:
                json_detail = response['ndcStatus']
                APIlog.debug(json_detail)
                status = json_detail['status']
                name = str(json_detail['conceptName']) if 'conceptName' in json_detail.keys() else 'UNK'
                _r = {'status': status, 'name': name}
            except KeyError or IndexError:
                smores_error(self.get_e('1'), api_url, logger=APIlog)
                return False
            else:
                return _r
        else:
            smores_error(self.get_e('1'), api_url, logger=APIlog)
            return None

    def get_cui_status(self, ndc):
        # RXNAV API expects 11 digit NDC with no hyphens
        e_class = ''
        _r, ndc_status = None, None
        if len(ndc) < 11:
            _zeroes = 11 - len(ndc)
            for i in range(_zeroes):
                ndc = '0' + ndc
        success, response, api_url = self.call_api('NDC_STATUS', ndc)
        if success and response is not None:
            try:
                ndc_status = response['ndcStatus']['status']
                _r = True

            except KeyError or IndexError:
                smores_error(self.get_e('1'), api_url, logger=APIlog)
                return False, None
            else:
                return _r, ndc_status

    def get_ndc_rxnorm(self, ndc):
        if len(ndc) < 11:
            _zeroes = 11 - len(ndc)
            for i in range(_zeroes):
                ndc = '0' + ndc

        success, response, api_url = self.call_api('NDC_STATUS', ndc)
        e_class = ''
        _r, status, name = (None for i in range(3))
        if success and response is not None:
            APIlog.debug('Good Response from API.')
            try:
                json_detail = response['ndcStatus']
                APIlog.debug(json_detail)
                status = json_detail['status']
                name = str(json_detail['conceptName']) if 'conceptName' in json_detail.keys() else 'UNK'
                _r = [json_detail['rxcui']] if 'rxcui' in json_detail.keys() and response[
                    'ndcStatus'] != 'UNKNOWN' else []
                if 'ndcHistory' in json_detail.keys() and len(json_detail['ndcHistory']) > 0:
                    for _mapping in json_detail['ndcHistory']:
                        _actCui = _mapping['activeRxcui']
                        _origCui = _mapping['originalRxcui']
                        if len(_actCui) > 0 and _actCui not in _r:
                            _r.append(_actCui)
                        if len(_origCui) > 0 and _origCui not in _r:
                            _r.append(_origCui)
            except KeyError or IndexError:
                smores_error(self.get_e('1'), api_url, logger=APIlog)
                return False
            else:
                return _r
        else:
            smores_error(self.get_e('1'), api_url, logger=APIlog)
            return None

    def get_rxnorm_ndc(self, rxcui):
        success, response, api_url = self.call_api('NDC_LOOKUP', rxcui)
        e_class = ''
        _r, _ndcList = (None for i in range(2))
        if success and response is not None:
            APIlog.debug('Good Response from API.')
            try:
                json_detail = response['historicalNdcConcept']
                APIlog.debug(json_detail)
                _r = json_detail['historicalNdcConcept']['historicalNdcTime']
                _ndcList = []
                for set in _r:
                    for _ndc in set['ndcTime']:
                        _ndcList = _ndcList + _ndc['ndc']
                _r = _ndcList
            except KeyError or IndexError:
                smores_error(self.get_e('1'), api_url, logger=APIlog)
                return False
            else:
                return _r
        else:
            smores_error(self.get_e('1'), api_url, logger=APIlog)
            return None

    def validate(self, ndc):
        if len(ndc) < 11:
            _zeroes = 11 - len(ndc)
            for i in range(_zeroes):
                ndc = '0' + ndc
        response, status = RXNDC.get_cui_status(ndc)
        if response and status != 'UNKNOWN':
            return True
        else:
            return False


class openFDADevice(openFDA):
    def __init__(self, api_key=None):
        super(openFDA, self).__init__()
        # https://api.fda.gov/device/udi.json?search=identifiers.id:%2266004-6028-1%22
        self.api_url = 'https://api.fda.gov/device/'
        self.api_key = api_key if api_key.upper() != 'NONE' and api_key is not None else None
        self.endpoints = {
            'VALID': {
                'base': 'udi.json',
                'payload': {'search': 'identifiers.id:"*CODE*"'}
            }
        }
        self.def_wait = 1500 if self.api_key is None else 250
        if self.api_key is not None:
            for endpoint in self.endpoints.values():
                if 'api_key' not in endpoint['payload'].keys():
                    endpoint['payload']['api_key'] = self.api_key

    def get_ndc_base(self, ndc):
        """
        Returns base information on a provided NDC code from the openFDA API
        :param ndc: str of valid NDC format
        :return: NONE or dict{ndc, name, status}
        """
        success, response, api_url = self.call_api('PACK_STATUS', ndc)
        if success and 'error' not in response.keys():
            if len(response['results']) > 0:
                return True
            else:
                return False


class UMLS(SMORESapi):
    requests_cache.install_cache(str(SMORESapi.cache_base.joinpath('umls_cache').absolute()),
                                 backend='sqlite',
                                 expire_after=SMORESapi.expire_after)

    def __init__(self, apikey=None, authuser=None, authpwd=None):
        super(UMLS, self).__init__()
        self.api_url = 'https://uts-ws.nlm.nih.gov/rest/'
        self.auth_uri = 'https://utslogin.nlm.nih.gov/'
        self.auth_endpoints = {'apikey': 'cas/v1/api-key', 'user': 'cas/v1/tickets/'}
        self.auth_client = Authenticate(self.auth_uri, self.auth_endpoints, apikey, authuser, authpwd)
        self.st_service = 'http://umlsks.nlm.nih.gov'
        self.valid_codesets = util.UMLS_VALID_SRCS.keys()
        self.endpoints = {
            'STATUS': {
                'base': 'content/current/*SRC*/*CODE*',
                'payload': {'ticket': '', 'regex': ['SRC']}
            },
            'CROSSWALK': {
                'base': 'crosswalk/current/source/*SRC*/*CODE*',
                'payload': {'targetSource': '', 'ticket': '', 'regex': ['SRC']}
            },
            'CUI_LOOKUP': {
                'base': 'search/2019AA',
                'payload': {
                            'ticket': '', 'string': '', 'sabs':'', 'searchType': '', 'inputType': ''}
            }
        }

    def get_st(self):
        return self.auth_client.get_service_ticket(self.st_service)

    def get_umls_cui(self, cui, src:str='CUI', search_type:str='exact'):
        _opts = {'ticket': self.get_st(),
                 'string': cui,
                 'sabs': src,
                 'searchType': search_type,
                 'inputType': 'sourceUi'}
        success, response, api_url = self.call_api('CUI_LOOKUP', cui, _opts)
        if success and response is not None:
            try:
                umls_cui = [atomCluster['ui'] for atomCluster in response['result']['results']]
            except KeyError or IndexError:
                smores_error(self.get_e('1'), api_url, logger=APIlog)
                return False, None
            else:
                return True, umls_cui

    def get_cui_base(self, cui, src:str='CUI'):
        if src.upper() in self.valid_codesets or src == 'CUI':
            if src != 'CUI':
                src = 'source/'+src
            _opts = {'ticket': self.get_st(), 'SRC': src}
            success, response, api_url = self.call_api('STATUS', cui, _opts)
            if success and response is not None:
                try:
                    cui_base = {}
                    cui_base['status'] = 'ACTIVE' if not response['result']['obsolete'] else 'OBSOLETE'
                    cui_base['name'] = response['result']['name']
                except KeyError or IndexError:
                    smores_error(self.get_e('1'), api_url, logger=APIlog)
                    return False, None
                else:
                    return True, cui_base
            return success, response
        else:
            smores_error(self.get_e('4'), self.api_url, logger=APIlog)
            return False, None

    def get_cui_status(self, cui, src:str='CUI'):
        if src.upper() in self.valid_codesets or src == 'CUI':
            if src != 'CUI':
                src = 'source/'+src
            _opts = {'ticket': self.get_st(), 'SRC': src}
            success, response, api_url = self.call_api('STATUS', cui, _opts)
            if success and response is not None:
                try:
                    cui_status = 'ACTIVE' if not response['result']['obsolete'] else 'OBSOLETE'
                except KeyError or IndexError:
                    smores_error(self.get_e('1'), api_url, logger=APIlog)
                    return False, None
                else:
                    return True, cui_status
            return success, response
        else:
            smores_error(self.get_e('4'), self.api_url, logger=APIlog)
            return False, None

    def get_crosswalk_cui(self, cui, src, target_src):
        _opts = {'ticket': self.get_st(), 'SRC': src, 'targetSource': target_src}
        if src.upper() in self.valid_codesets and target_src.upper() in self.valid_codesets:
            success, response, api_url = self.call_api('CROSSWALK', cui, _opts)
            if success and response is not None:
                json.dump(response, indent=4)
                try:
                    cui_crosswalk = [{'ui': atomCluster['ui'],
                                      'name': atomCluster['name'],
                                      'status': 'ACTIVE' if not atomCluster['obsolete'] else 'OBSOLETE',
                                      'cui': self.get_umls_cui(atomCluster['ui'], atomCluster['rootSource'], 'exact'),
                                      } for atomCluster in response['result']]
                    _r = True
                except KeyError or IndexError:
                    smores_error(self.get_e('1'), api_url, logger=APIlog)
                    return False, None
                else:
                    return _r, cui_crosswalk

    def validate(self, cui, src:str='CUI'):
        response, status = self.get_cui_status(cui, src)
        if response and status is not None:
            return True
        else:
            return False