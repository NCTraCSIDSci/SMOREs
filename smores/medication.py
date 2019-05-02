# Python Library Imports
import itertools
import logging
# SMOREs Internal Imports
import smores.medicationdictionary as md
from smores.api import openFDA, RXNAV, RXNDC, openFDADevice
from smores.utility.errors import smores_error
import smores.utility.util as util

smoresLog = logging.getLogger(__name__)

def get_FHIR_codesets(sys):
    return util.FHIR_CODESET_SYSTEMS

def get_RXNORM_tty_dict():
    return util.RXNORM_TTY_SUPPORT_DICT

def get_med_master_dict(src):
    return md.get_med_dict_by_src(src)


def get_med_by_id(med_id, src):
    smoresLog.debug('{0} : {1}'.format(med_id, src))
    smoresLog.debug('Med ID List: {0}'.format(Medication.med_id_list))
    if type(src) is md.MedicationDictionary:
        master_dict = get_med_master_dict(src)
        med = master_dict.get_med_by_id(med_id)
    elif src in Medication.med_id_list.keys():
        med = Medication.med_id_list[src][med_id]
    else:
        dict = md.get_med_dict_by_src(src)
        med = dict.get_med_by_id(med_id)
    return med


def med_exists(med_id, src):
    if type(src) is md.MedicationDictionary:
        return src.check_list_by_id(med_id)
    else:
        return True if med_id in Medication.med_id_list[src].keys() else False



def get_rxcui(cui, valid=None, idType=None):
    """Check to see if an RxCUI already exists.
        If Not, create a new RxCUI Object
        @input : string - Suspected RxCUI
        @output : RxCUI.Object """
    rxcui_dict = md.get_med_dict_by_src('RXNORM')
    smoresLog.debug(cui)
    smoresLog.debug('RxNorm Med List Keys: %s', str(rxcui_dict.med_list.keys()))
    # Process input list of cuis, recursive call
    if isinstance(cui, list):
        return_rxc = {'rxcui' : get_rxcui(_c, valid, idType) for _c in cui}
        return return_rxc
    # Process individual rxcui input
    else:
        if str(cui) in rxcui_dict.med_list.keys():
            smoresLog.debug('Key Already Exists: %s', str(cui))
            return rxcui_dict.med_list[cui]
        elif idType is not None:
            success, result = RXNAV().get_rxcui_by_id(cui, idType=idType)
            if success:
                if type(result) == list:
                    return_rxc = [get_rxcui(rxc) for rxc in result]
                else:
                    return_rxc = get_rxcui(result)
                return return_rxc
        else:
            return RxCUI(cui, valid)


def getValidTypes():
    return RXNAV.RXNAV_VALID_IDS


class Medication:
    id_count = itertools.count()
    med_id_list = {'GENERIC': {}}
    api = None

    def __init__(self, input_key: str):
        self.sys_id = int(next(Medication.id_count))
        self.cui = input_key
        self.dictionaries = {}
        self.name = None
        self.medClass = 'SYSTEM'

    def add_cui(self, cui, src):
        if not isinstance(cui, Medication) and not issubclass(type(cui), Medication):
            med_obj = Medication(cui)
        else:
            med_obj = cui
            cui = med_obj.cui

        if not self.has_dict(src):
            self.add_dict(src)

        self.get_dict(src).add_med_with_id(med_obj, cui)

    def isNameSet(self):
        return True if self.name is not None and len(self.name) > 0 else False

    # Medication Naming Functions
    def set_name(self, in_name):
        if len(in_name) > 0 and self.name is None:
            self.name = in_name
        elif in_name != self.name:
            if isinstance(self.name, list):
                self.name.append(in_name)
            else:
                _t = [self.name, in_name]
                self.name = _t
        elif in_name == self.name:
            pass
        else:
            self.name = "#Mx002.2"
            smores_error('#Mx002.2')

    def get_name(self):
        return self.name[0] if type(self.name) is list else self.name

    def has_dict(self, src, id=None):
        _r = True
        if src not in self.dictionaries.keys():
            smoresLog.debug('Adding To This Medication''s Dictionary List - Source: {0} ...'.format(src))
            _r = False
        elif id is not None and id not in self.dictionaries[src].keys():
            _r = False
        return _r

    def add_dict(self, src, id):
        self.dictionaries[src] = md.MedicationDictionary(src, id)

    def get_dict(self, src=None, id=None):
        if src is not None:
            smoresLog.debug('Looking for Dictionary {0} on Med {1}'.format(src, id))
            smoresLog.debug('[{0}] - '.format(self.sys_id, self.dictionaries))
            if self.has_dict(src, id):
                return self.dictionaries[src] if id is None else self.dictionaries[src][id]
            else:
                return None
        else:
            smoresLog.debug('Looking up all dictionaries...')
            return list(self.dictionaries.keys())

    # Medication Property Functions
    def get_property(self, prop):
        attr = getattr(self, prop, None)
        if attr is None:
            smores_error('#Mx002.1')
        return attr

    def add_details(self, details:dict):
        for det, val in details.items():
            if hasattr(self, det):
                setattr(self, det, value=val)

    def get_print_base(self):
        _print = {
            'id': self.sys_id,
            'name': self.get_name(),
            'source': str(type(self))
        }
        return _print

    def print_formats(self, p_type=None, p_mod=None, p_base=True):
        if p_type == 'simple' or p_type is None or p_base:
            _print = self.get_print_base()
        else:
            _print = {}

        return _print


class LocalMed(Medication):
    api = None

    def __init__(self, input_key=None, source=None, name=None, parent_dict=None, is_generic=False):
        super(LocalMed, self).__init__(input_key)
        smoresLog.debug('Adding medication {0} from source {1}'.format(input_key, source))
        self.source = source
        self.id_links = {}
        self.parent_med_dict = md.get_med_dict_by_src(self.source) if parent_dict is None else parent_dict
        self.local_id = input_key if input_key is not None else self.sys_id
        self.dictionaries = {'PARENT': self.parent_med_dict}
        self.has_rxcui = False
        self.has_ingredients = None
        self.ing_checked = False
        self.json = None
        self.remap_checked = False
        self.has_remap = False

        if is_generic:
            Medication.med_id_list['GENERIC'][self.local_id] = self
        else:
            Medication.med_id_list[source][self.local_id] = self

    def remove(self):
        import gc
        self.dictionaries = None
        self.parent_med_dict = None
        self.id_links = None
        referrers = gc.get_referrers(self)
        for ref in referrers:
            del ref
        del self

    def add_cui(self, in_cui, cui_type=None, cui_name: str=None):
        smoresLog.debug('IN_CUI : ' + str(in_cui))
        smoresLog.debug('{0} Current Dictionaries: {1}'.format(self.local_id, self.dictionaries))
        invalid_cui = 0
        if type(in_cui) is list:
            smoresLog.debug('In CUI Type Check: LIST - Recursive Call')
            for nest_cui in in_cui:
                invalid_cui += self.add_cui(nest_cui, cui_type)
        elif type(in_cui) is dict:
            smoresLog.debug('In CUI Type Check: DICT - Recursive Call')
            for cui, obj in in_cui.items():
                invalid_cui += self.add_cui(obj, cui_type)
        elif isinstance(in_cui, RxCUI):
            smoresLog.debug('In CUI Type Check: RXCUI.Object')
            cui_type='RXNORM'
            if in_cui.check_ingredient():
                if not self.has_dict('ING'):
                    self.add_dict('ING', self.sys_id)
                cui_dict = self.get_dict(src='ING')
                self.has_ingredients = True
            else:
                if not self.has_dict(cui_type):
                    self.add_dict(cui_type, self.sys_id)
                cui_dict = self.get_dict(src=cui_type)
            cui_dict.add_med_with_id(in_cui, in_cui.cui)
            self.has_rxcui = True
            invalid_cui += 1 if not in_cui.valid else 0
        elif isinstance(in_cui, NDC):
            smoresLog.debug('In CUI Type Check: NDC.Object')
            if not self.has_dict('NDC'):
                self.add_dict('NDC', self.sys_id)
            cui_dict = self.get_dict('NDC')
            cui_dict.add_med_with_id(in_cui, in_cui.local_id)
            invalid_cui += 1 if not in_cui.valid else 0
        elif type(in_cui) is str and cui_type in ['RXNORM','RXCUI']:
            cui_type='RXNORM'
            smoresLog.debug('In CUI Type Check: RXNORM, RXCUI')
            rxcui_obj = get_rxcui(in_cui)
            if rxcui_obj.check_ingredient():
                if not self.has_dict('ING'):
                    self.add_dict('ING', self.sys_id)
                cui_dict = self.get_dict('ING')
                self.has_ingredients = True
            else:
                if not self.has_dict(cui_type):
                    self.add_dict(cui_type, self.sys_id)
                cui_dict = self.get_dict(cui_type)
            cui_dict.add_med_with_id(rxcui_obj, in_cui)
            self.has_rxcui = True
            invalid_cui += 1 if not rxcui_obj.valid else 0
        elif type(in_cui) is str and cui_type == 'NDC':
            smoresLog.debug('In CUI Type Check: Generic')
            if not self.has_dict('NDC'):
                self.add_dict('NDC', self.sys_id)
            cui_dict = self.get_dict('NDC')
            ndc_obj = NDC(in_cui)
            if cui_name is not None:
                ndc_obj.set_name(cui_name)
            cui_dict.add_med_with_id(ndc_obj, in_cui)
            invalid_cui += 1 if not ndc_obj.valid else 0
        else:
            smores_error('#Mx001.2')
        return invalid_cui

    def add_json(self, json):
        self.json = json

    def set_local_id(self, in_id):
        if len(in_id) > 0:
            self.local_id = in_id
        else:
            self.local_id = "#Mx002.3"
            smores_error('#Mx002.3')

    # Standard "_get" functions to return object values
    def get_local_id(self):
        return self.local_id

    def get_source(self):
        return self.source

    def get_json(self):
        return self.json

    def get_cui_by_src(self, c_type, mod=None, inc_obj=False):
        """Returns a list of RxCUI"""
        try:
            if type(c_type) is list:
                _cuis = {}
                for _c in c_type:
                    _cuis[_c] = self.get_dict(_c, mod).get_med_list(modifier=mod, inc_obj=inc_obj)
            else:
                _cuis = self.get_dict(c_type, mod).get_med_list(modifier=mod, inc_obj=inc_obj)
        except AttributeError:
            return {} if inc_obj else []
        else:
            return _cuis

    def get_cui_all(self, omit=[], inc_obj=False):
        src_list = self.get_dict()
        _cuis = {}
        for src in src_list:
            if src not in omit:
                _cuis[src] = self.get_cui_by_src(c_type=src, inc_obj=inc_obj)
        return _cuis

    # Lookup specific term types of RxCUI's for a medication that have already been identified.
    # Will not perform a new API search
    # Returns
    def get_rxcui_by_tty(self, tty):
        return self.get_dict('RXNORM').get_med_by_property('tty', tty)

    def get_ingredients(self, obj_inc=False):

        if self.has_ingredients:
            logging.debug('{0} Has Ingredients'.format(self.local_id))
            dict = self.get_dict('ING')

        elif 'RXNORM' in self.dictionaries.keys() and (self.has_ingredients is None or not self.ing_checked):
            if not self.has_dict('ING'):
                self.add_dict('ING', self.sys_id)
            dict = self.get_dict('ING')
            rxc_list = self.get_cui_by_src('RXNORM')
            for cui in rxc_list:
                _ing_temp = get_rxcui(cui).get_ingredients()
                if _ing_temp is not None:
                    self.has_ingredients = True if len(_ing_temp) > 0 else self.has_ingredients
                    for ing in _ing_temp:
                        _rxc = get_rxcui(ing)
                        dict.add_med_with_id(_rxc, _rxc.cui)

            if self.has_ingredients is None:
                self.has_ingredients = False

        if obj_inc and self.has_ingredients:
            ing_list = []
            for ing in dict.get_med_list():
                ing_list.append(get_rxcui(ing))
        elif self.has_ingredients:
            ing_list = dict.get_med_list()
        else:
            ing_list = None

        return ing_list

    def get_fhir(self):
        # TODO ERROR : This is loading everything for the first medication and not just what is associated with it
        default = self.print_formats('FHIR')
        FHIR_RESOURCE = {'resource': {'resourceType': 'Medication', 'id': default['id']}}
        # TODO parameterize the local code fhir value system
        codeable_concept = [{'code': self.local_id, 'display': self.get_name(), 'system':'https://unchealthcare.org/epic/medications'}]
        if 'cui' in default.keys():
            for cuiSrc, cuiList in default['cui'].items():
                system = get_FHIR_codesets(cuiSrc.upper())
                _cuiSet = []
                for cui in cuiList:
                    _c = get_med_by_id(cui, cuiSrc)
                    if _c.valid and _c.fhir_valid:
                        _cuiSet.append({'code': cui, 'system': system, 'display': _c.get_name()})
                codeable_concept = codeable_concept + _cuiSet
            FHIR_RESOURCE['resource']['code'] = {'coding': codeable_concept}

        if 'ing' in default.keys():
            codeable_concept = []
            if type(default['ing']) is dict:
                for cuiSrc, cuiList in default['ing'].items():
                    system = get_FHIR_codesets('RXNORM') # Only supporting RxNorm ingredients
                    _cuiSet = [{'code': cui, 'system': system, 'display': get_med_by_id(cui, cuiSrc).get_name()} for cui in cuiList]
                    codeable_concept = codeable_concept + _cuiSet
            else:
                for cui in default['ing']:
                    system = get_FHIR_codesets('RXNORM')  # Only supporting RxNorm ingredients
                    _cuiSet = {'code': cui, 'system': system, 'display': get_med_by_id(cui, 'RXNORM').get_name()}
                    codeable_concept.append(_cuiSet)

            FHIR_RESOURCE['resource']['ingredient'] = [{'itemCodeableConcept': [{'coding': codeable_concept}]}]
        return FHIR_RESOURCE

    def get_print_base(self):
        _print = {
            'id': self.get_local_id(),
            'name': self.get_name(),
            'source': self.get_source()
        }
        return _print

    def print_formats(self, p_type=None, p_mod=None, p_base=True):
        if p_type == 'simple' or p_type is None or p_base:
            _print = self.get_print_base()
        else:
            _print = {}

        if p_type == 'ing' or p_type == 'ingredients':
            _ing_temp = self.get_ingredients(obj_inc=True)
            _ing = [item.print_formats(p_base=True) for item in _ing_temp] if _ing_temp is not None else None
            smoresLog.debug(_ing)
            if _ing is not None and p_base:
                _print['ing'] = _ing
            elif _ing is not None and not p_base:
                _print = _ing

        elif p_type == 'cui':
            smoresLog.debug('Getting Cui Format...')
            if p_mod is not None:
                if 'src' in list(p_mod.keys()):
                    _cui = self.get_cui_by_src(p_mod['src'])
                elif 'omit_src' in list(p_mod.keys()):
                    _cui = self.get_cui_all(omit=p_mod['omit_src'])
            else:
                _cui = self.get_cui_all()

            if _cui is not None:
                _print = _cui

        elif p_type == 'complete':
            _ing_m = None if p_mod is None or 'ing' not in list(p_mod.keys()) else p_mod['ing']
            _cui_m = None if p_mod is None or 'cui' not in list(p_mod.keys()) else p_mod['cui']
            _ing = self.print_formats(p_type='ing', p_base=False, p_mod=_ing_m)
            _cui = self.print_formats(p_type='cui', p_base=False, p_mod=_cui_m)
            if 'ingredients' in list(_ing.keys()):
                _print['ingredients'] = _ing
            if 'cui' in list(_cui.keys()):
                _print['cui'] = _cui['cui']

        elif p_type in ['CSV']:
            from smores.utility.util import flatten_dict
            smoresLog.debug('p_mods : {0}'.format(p_mod))
            _print = self.print_formats(p_base=True)
            if isinstance(p_mod, dict):
                for mod_k, mod_v in p_mod.items():
                    smoresLog.debug('Current p_mod: {0} , {1}'.format(mod_k, mod_v))
                    _print[mod_k] = self.print_formats(mod_k, p_mod=mod_v, p_base=False)
                if 'ing' in _print.keys():
                    if len(_print['ing']) >= 0:
                        _ing2 = [item['cui'] for item in _print['ing'].copy()]
                        _print['cui'] = _print['cui'] + _ing2 if _ing2 is not None else _print['cui']
                    _print.pop('ing')
            _print = flatten_dict(_print)

        elif p_type == 'FHIR':
            _print = self.print_formats(p_base=True)
            _print['cui'] = self.print_formats('cui', p_mod={'omit_src': ['PARENT', 'ING']}, p_base=False)
            if self.has_ingredients:
                _ing = self.print_formats(p_type='ing', p_base=False)
                _print['ing'] = [item['cui'] for item in _ing['ing']] if _ing is not None else None

        smoresLog.debug('{0} : {1}'.format(p_type, _print))
        return _print


class NDC(Medication):
    api = openFDA(api_key=util.get_api_key('FDA'))
    api2 = RXNDC()
    api3 = openFDADevice(api_key=util.get_api_key('FDA'))

    def __init__(self, input_key:str, valid=None):
        super(NDC, self).__init__(input_key)

        if valid is None:
            if NDC.api.validate(self.cui):
                ndc_base = NDC.api.get_ndc_base(self.cui)
                self.api = NDC.api
            elif NDC.api2.validate:
                ndc_base = NDC.api2.get_cui_base(self.cui)
                self.api = NDC.api2 if ndc_base is not None else self.api
            elif NDC.api3.validate:
                self.valid = False
            else:
                ndc_base = NDC.api.get_ndc_product(self.cui)

            if ndc_base is not None:
                self.valid = True
                self.name = ndc_base['name']
                self.status = ndc_base['status']
            else:
                self.valid = False

        self.parent_med_dict = md.get_med_dict_by_src('NDC')
        self.parent_med_dict.add_med_with_id(self, self.cui)
        self.fhir_valid = True

    def get_linked_cui(self, cui_type:str):
        linked = []
        if self.has_dict(cui_type.upper()):
            linked = self.get_dict(cui_type.upper()).get_med_list(inc_obj=True)
        elif cui_type == 'RXNORM':
            rxc_l = self.api.get_ndc_rxnorm(self.cui)
            if rxc_l:
                self.add_dict('RXNORM', self.sys_id)
                rxc_dict = self.get_dict('RXNORM')
                for rxcui in rxc_l:
                    _rxc = get_rxcui(rxcui)
                    rxc_dict.add_med_with_id(_rxc, rxcui)
                    linked.append(_rxc)
        return linked


class RxCUI(Medication):
    rx_remap_avail = {}
    rx_hist_avail = {}
    api = RXNAV()

    TTY_DICT = util.RXNORM_TTY_SUPPORT_DICT

    @staticmethod
    def get_historical_list():
        return RxCUI.rx_hist_avail.copy()

    def __init__(self, input_key:str, valid=None):
        super(RxCUI, self).__init__(input_key)

        self.has_ingredients = None
        self.has_remaps = None
        self.has_hist = None
        self.dictionaries = {}

        if valid is None:
            self.valid, self.status, self.tty, self.name = (None for i in range(4))
            if RxCUI.api.validate(self.cui):
                RxCUI.api.get_cui_base(self)
                self.valid = True
            else:
                self.valid = False

            self.api = RxCUI.api
            self.parent_med_dict = md.get_med_dict_by_src('RXNORM')
            self.parent_med_dict.add_med_with_id(self, self.cui)

        if self.status is not None:
            if self.status not in ['ACTIVE','RETIRED','ALIEN','UNKNOWN']:
                RxCUI.rx_remap_avail[self.cui] = self
                self.has_remaps = True

            if self.status in ['ALIEN', 'UNKNOWN', 'RETIRED']:
                RxCUI.rx_hist_avail[self.cui] = self
                self.has_hist = True
                self.hist_checked = False

        if self.tty is not None:
            self.is_ingredient = self.check_ingredient()

        self.fhir_valid = True if self.tty not in ['BN', 'DF', 'SBDF', 'SCDF'] else False

    def set_tty(self, in_tty):
        if in_tty.upper() in RxCUI.TTY_DICT.keys():
            self.tty = in_tty.upper()
            self.is_ingredient = self.check_ingredient()
        else:
            _error = smores_error('#Bx001.2')
            smoresLog.error(str(_error) + '\n')

        self.fhir_valid = True if self.tty not in ['BN', 'DF', 'SBDF', 'SCDF'] else False

    def get_tty(self):
        return self.tty

    def set_status(self, in_status):
        if in_status is not None:
            self.status = in_status.upper()
        else:
            _error = smores_error('#Bx001.3')
            smoresLog.error(str(_error) + '\n')

    def get_status(self):
        if self.status is None:
            valid, status = self.api.get_cui_status(self.cui)
            if valid:
                self.set_status(status)
                return self.status
            else:
                _error = smores_error('#Bx001.3')
                smoresLog.warning(_error + '\n')
        else:
            if not self.valid:
                _error = smores_error('#Bx001.3')
                smoresLog.warning(_error + '\n')
                return None
            else:
                return self.status

    def get_active_cui(self):
        """Get the primary cui for this RxCUI object - Return the New cui if the original is no longer active"""
        if self.status == 'Active' or self.status == 'Retired':
            return self.cui
        elif self.valid and len(self.remap_cui) > 0:
            smoresLog.debug('Remaps: {0}'.format(self.remaps))
            return [cui.get_active_cui() for cui in self.remap]
        else:
            return self.cui

    def get_ingredients(self):
        if self.has_ingredients:
            return self.dictionaries['ING'].get_med_list()
        elif self.valid and self.has_ingredients is None:
            self.dictionaries['ING'] = md.MedicationDictionary(dict_src='RXNORM_ING', dict_id=self.cui)
            if self.has_hist:
                cui_list = self.api.get_historical_info(self.cui, 'bossConcept')
                if cui_list and 'baseRxcui' in cui_list[0].keys():
                    for i in cui_list:
                        _rxc = get_rxcui(i['baseRxcui'])
                        self.dictionaries['ING'].add_med_with_id(_rxc, _rxc.cui)
                    self.has_ingredients = True
                else:
                    self.has_ingredients = False
            else:
                cui_list = self.api.get_rxcui_ingredients(self.cui)
                if len(cui_list) > 0:
                    for tty, i in cui_list.items():
                        for cui in i:
                            _rxc = get_rxcui(cui['rxcui'])
                            self.dictionaries['ING'].add_med_with_id(_rxc, _rxc.cui)
                    self.has_ingredients = True
                else:
                    self.has_ingredients = False
            self.ing_checked = True
            return self.dictionaries['ING'].get_med_list()
        else:
            return None

    def check_ingredient(self):
        if self.tty in ['IN', 'MIN', 'PIN']:
            return True
        else:
            return False

    def get_linked_cui(self, cui_type:str):
        linked = []
        if cui_type == 'remap':
            if self.has_dict('REMAP'):
                linked = self.get_dict('REMAP').get_med_list(inc_obj=True)
            else:
                remaps = self.api.get_remap_cuis(self.cui)
                if remaps:
                    self.add_dict('REMAP', self.sys_id)
                    remap_d = self.get_dict('REMAP')
                    for cui in remaps:
                        _rxc = get_rxcui(cui)
                        remap_d.add_med_with_id(_rxc, cui)
                        linked.append(_rxc)
        elif cui_type == 'history':
            if self.has_hist and not self.hist_checked:
                history = self.api.get_historical_info(self.cui, 'rxcuiConcept')
                if history:
                    if 'str' in history.keys():
                        self.set_name(history['str'])
                    if 'tty' in history.keys():
                        self.set_tty(history['tty'])
        return linked

    # TODO Move to super()
    def set_property(self, prop, value):
        if hasattr(self, prop):
            self.__setattr__(prop, value)
        elif prop == 'str':
            # This is a translation of an API variance between calls
            self.__setattr__('name', value)
        else:
            raise Exception('"{0}" property does not exist on {1} Object!'.format)

    def check_tty(self, in_tty):
        format_tty = in_tty.upper()
        if format_tty in get_RXNORM_tty_dict():
            return [True, format_tty]
        else:
            error_ret = {'code': '#Mx001.1'}
            error_ret['msg'] = 'Invalid Term Type Provided (' + error_ret['code'] + ') | Invalid TTY: ' + in_tty
            return [False, error_ret]

    def get_print_base(self):
        _print = {
            'cui': self.cui,
            # 'act_cui': self.get_active_cui(),
            'tty': self.get_tty(),
            'name': self.get_name(),
            'status': self.get_status()
        }
        return _print

    # def print_formats(self, p_type=None, p_mod=None, p_base=True):
    #     smoresLog.debug('Getting print format..')
    #     if p_type == 'simple' or p_type is None or p_base:
    #         _print = self.get_print_base()
    #     else:
    #         _print = {}
    #
    #     if p_type == 'ing':
    #         _ing_temp = self.get_ingredients()
    #         _ing = [item.print_formats(p_base=True) for item in _ing_temp] if _ing_temp is not None else None
    #         smoresLog.debug(_ing)
    #
    #         if _ing is not None:
    #             _print['ingredients'] = _ing
    #             if 'id' in _print['ingredients'].keys():
    #                 _print['ingredients']['cui_ing'] = _print['ingredients']['cui']
    #                 _print['ingredients'].pop('cui', None)
    #
    #     elif p_type == 'complete':
    #         _print = self.print_formats()
    #         _ing = self.print_formats('ing')
    #
    #     elif p_type == 'cui':
    #         _print = self.cui
    #
    #     elif p_type == 'CSV':
    #         from smores.medkit import flatten_dict
    #         smoresLog.debug('p_mods : {0}'.format(p_mod))
    #         _print = self.print_formats(p_base=True)
    #         smoresLog.debug(_print)
    #         for mod_k, mod_v in p_mod.items():
    #             smoresLog.debug('Current p_mod: {0} , {1}'.format(mod_k, mod_v))
    #             _print[mod_k] = self.print_formats(mod_k, p_mod=mod_v, p_base=False)
    #         smoresLog.debug(_print)
    #         _print = flatten_dict(_print)
    #
    #     return _print