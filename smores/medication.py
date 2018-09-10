import itertools
import logging
import smores.medicationdictionary as md
import rxnorm.rxnorm as rxnorm
from smores.errors import smores_error
import json

smoresLog = logging.getLogger(__name__)
_FHIR_JSON_KEYS = []


def get_med_master_dict(src):
    return md.get_med_dict_by_src(src)


def get_med_by_id(med_id, src):
    master_dict = get_med_master_dict(src)
    return master_dict.get_med_by_id(med_id)


def med_exists(med_id, src):
    if type(src) is md.MedicationDictionary:
        return src.check_list_by_id(med_id)
    else:
        master_dict = get_med_master_dict(src)
        smoresLog.debug('Master Dict: {0}'.format(master_dict))
        return master_dict.check_list_by_id(med_id)


def get_json_keys(json_type):
    if json_type == 'FHIR':
        return _FHIR_JSON_KEYS


class Medication:
    id_count = itertools.count()

    def __init__(self, source, input_key=None, is_rxcui=False, name=''):
        smoresLog.debug('Adding medication')
        self.sys_id = int(next(Medication.id_count))
        self.name = name
        self.source = source
        self.id_links = {}
        self.parent_med_dict = md.get_med_dict_by_src(self.source)
        self.local_id = input_key if input_key is not None else self.sys_id
        self.dictionaries = {}
        self.has_rxcui = False
        self.has_ingredients = None
        self.json = None
        if input_key is not None:
            self.add_cui(self, source)
        self.parent_med_dict.add_med_with_id(self, self.local_id)

    def add_cui(self, in_cui, cui_type):
        cui_dict = self.get_dict(cui_type)
        smoresLog.debug('IN_CUI : ' + str(in_cui))
        if type(in_cui) is list:
            smoresLog.debug('In CUI Type Check: LIST - Recursive Call')
            for nest_cui in in_cui:
                self.add_cui(nest_cui, cui_type)
        elif type(in_cui) is dict:
            smoresLog.debug('In CUI Type Check: DICT - Recursive Call')
            for cui, obj in in_cui.items():
                self.add_cui(obj, cui_type)
        elif type(in_cui) is rxnorm.RxCUI:
            smoresLog.debug('In CUI Type Check: RXCUI.Object')
            self.dictionaries[cui_type].add_med_with_id(in_cui, in_cui.cui)
            self.has_rxcui = True
        elif type(in_cui) is Medication:
            smoresLog.debug('In CUI Type Check: Medication.Object')
            cui_dict.add_med_with_id(in_cui, in_cui.local_id)
        elif type(in_cui) is str and cui_type in ['RXNORM', 'RXNAV', 'RXCUI']:
            smoresLog.debug('In CUI Type Check: RXNORM, RXNAV, RXCUI')
            rxcui_obj = rxnorm.get_rxcui(in_cui)
            cui_dict.add_med_with_id(rxcui_obj, in_cui)
            self.has_rxcui = True
        else:
            smoresLog.debug('In CUI Type Check: Generic')
            generic_med = Medication(cui_type, in_cui)
            cui_dict.add_med_with_id(generic_med, in_cui)

    def add_med_id(self, id, id_type):
        if len(id) > 0 and len(id_type) > 0:
            if id_type.upper() == 'LOCAL':
                self.set_local_id(id)
            else:
                self.add_cui(id, id_type)

    def add_json(self, json):
        self.json = json


    def add_dict(self, src, id=None):
        if src not in self.dictionaries.keys():
            smoresLog.debug('Adding To Medication Dictionary - Source: {0} ...'.format(src))
            self.dictionaries[src] = md.MedicationDictionary(src, id)
        return True

    def set_local_id(self, in_id):
        if len(in_id) > 0:
            self.local_id = in_id
        else:
            self.local_id = "#Mx002.3"
            smores_error('#Mx002.3')

    def set_name(self, in_name):
        if len(in_name) > 0:
            self.name = in_name
        else:
            self.name = "#Mx002.2"
            smores_error('#Mx002.2')

    # Standard "_get" functions to return object values
    def get_local_id(self):
        return self.local_id

    def get_name(self):
        return self.name

    def get_property(self, prop):
        attr = getattr(self, prop, None)
        if attr is None:
            smores_error('#Mx002.1')
        return attr

    def get_source(self):
        return self.source

    def get_json(self):
        return self.json

    def get_dict(self, src=None):
        if src is not None:
            if self.add_dict(src):
                return self.dictionaries[src]
            else:
                return None
        else:
            return list(self.dictionaries.keys())

    def get_cui_by_src(self, c_type, mod=None):
        """Returns a list of RxCUI"""
        if type(c_type) is list:
            _cuis = {}
            for _c in c_type:
                _cuis[_c] = self.get_dict(_c).get_med_list(mod)
        else:
            _cuis = self.get_dict(c_type).get_med_list(mod)
        return _cuis

    def get_cui_all(self, omit=[]):
        src_list = self.get_dict()
        _cuis = {}
        for src in src_list:
            if src not in omit:
                _cuis[src] = self.get_cui_by_src(src)
        return _cuis

    # RxNav / RxCui.Class specific functions
    def get_cui_status(self):
        return self.rxcui_status

    def get_rxcui_by_tty(self, tty):
        return self.get_dict('RXNORM').get_med_by_property('tty', tty)

    def find_ingredients(self, search='RXNORM'):
        if self.has_ingredients is None:
            smoresLog.debug('Medication.py : Finding ingredients')
            if search == 'RXNORM':
                rxc_s = self.get_cui_by_src('RXNORM').copy() # Prevent continuous recursive calls
                if len(rxc_s) > 0:
                    smoresLog.debug('RXC_S: {0}'.format(rxc_s))
                    for rxcui in rxc_s:
                        smoresLog.debug('Starting Ingredient Search for: {0}'.format(rxcui))
                        rxc_o = rxnorm.get_rxcui(rxcui)
                        # smoresLog.debug(rxnorm.get_rxcui(rxcui))
                        if rxc_o.find_ingredients():
                            smoresLog.debug('Ingredients Found, Adding to Dictionary')
                            self.add_cui(rxc_o.get_ingredients(), 'RXNORM')
                            self.has_ingredients = True
                else:
                    smores_error('#Mx001.1')
                    self.has_ingredients = False
            else:
                smores_error('TBC')  # TODO Encode Error
        return self.has_ingredients

    def get_ingredients(self, mod=['ALL'], count=False):
        if self.has_ingredients:
            logging.debug('{0} Has Ingredients'.format(self.local_id))
            if 'ALL' in mod or 'RXNORM' in mod:
                ings = self.get_rxcui_by_tty(['IN', 'MIN'])

            if count:
                return len(ings)
            else:
                _ing_temp = [rxnorm.get_rxcui(cui) for cui in ings]
                return _ing_temp
        else:
            return None

    def remap_rxcui (self, in_remaps):
        med_remap_dict = self.get_remap_med_dict()
        for remap in in_remaps:
            new_med = Medication('RXNAV')
            new_med.set_attributes(remap)
            med_remap_dict.add_med_with_id(new_med, new_med.get_rxcui())

    def print_formats(self, p_type=None, p_mod=None, p_base=True):
        if p_type == 'simple' or p_type is None or p_base:
            _print = {
                'id': self.get_local_id(),
                'name': self.get_name(),
                'source': self.get_source()
            }
        else:
            _print = {}

        if p_type == 'ing':
            _ing_temp = self.get_ingredients('RXNORM')
            _ing = [item.print_formats() for item in _ing_temp] if _ing_temp is not None else None
            if _ing is not None:
                _print['ingredients'] = _ing

        elif p_type == 'cui':
            if p_mod is not None and 'cui' in list(p_mod.keys()):
                _cui = self.get_cui_by_src(p_mod['cui'])
            else:
                _cui = self.get_cui_all()
            if _cui is not None:
                _print['cui'] = _cui

        elif p_type == 'complete':
            _ing = self.print_formats(p_type='ing', p_base=False, p_mod=p_mod)
            _cui = self.print_formats(p_type='cui', p_base=False, p_mod=p_mod)
            if 'ingredients' in list(_ing.keys()):
                _print['ingredients'] = _ing['ingredients']
            if 'cui' in list(_cui.keys()):
                _print['cui'] = _cui['cui']

        elif p_type == 'CSV':
            _print = self.print_formats('complete', p_mod=p_mod)
            if 'cui' in list(_print.keys()) and len(_print['cui']) > 0:
                _base = self.print_formats('simple')
                for src in _print['cui']:
                    for cui in src:
                        _obj = md.get_obj_by_src(cui, src)
                        _obj_print = _obj.print_formats('simple')
                        _flatten = _base

        return _print

