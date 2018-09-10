import logging
import rxnorm.rxnav as rxnav
import smores.medicationdictionary as md
from rxnorm.errors import rxnorm_error

rxnormLog = logging.getLogger(__name__)

_tty_dict = {
    'SBD': {'name': 'Semantic Branded Drug'},
    'SCD': {'name': 'Semantic Clinical Drug'},
    'IN': {'name': 'Ingredient'},
    'MIN': {'name': 'Multi-Ingredient'},
    'PIN': {'name': 'Precise Ingredient'},
    'BN': {'name': 'Branded Name'},
    'SBDC': {'name': 'Semantic Branded Drug Component'},
    'SCDC': {'name': 'Semantic Clinical Drug Component'},
}

def get_rxcui(rxcui, valid=False):
    """Check to see if an RxCUI already exists.
        If Not, create a new RxCUI Object
        @input : string - Suspected RxCUI
        @output : RxCUI.Object """
    rxcui_dict = md.get_med_dict_by_src('RXNORM')
    rxnormLog.debug(rxcui)
    rxnormLog.debug('RxNorm Med List Keys: %s', str(rxcui_dict.med_list.keys()))
    if str(rxcui) in rxcui_dict.med_list.keys():
        rxnormLog.debug('Key Already Exists: %s', str(rxcui))
        return rxcui_dict.med_list[rxcui]
    else:
        return RxCUI(rxcui)


class RxCUI:
    rx_master = {}

    def __init__(self, rxcui, tty=None, name=None, remap=[], valid=None):
        self.cui = rxcui
        self.remap_cui = remap
        self.ing_list = {}
        self.ing_checked = False

        if tty is None or name is None:
            self.valid, self.status, self.tty, self.name = rxnav.validate_rxcui(rxcui, True)
        else:
            if valid is None or not valid:
                self.valid, self.status = rxnav.validate_rxcui(rxcui)
            else:
                self.valid = valid
            self.tty = tty
            self.name = name
        if self.valid:
            md.get_med_dict_by_src('RXNORM').add_med_with_id(self, self.cui)
        else:

            self.tty = tty
            self.name = name

    def set_tty(self, in_tty):
        if in_tty.upper() in _tty_dict.keys():
            self.tty = in_tty.upper()
        else:
            _error = rxnorm_error('#Bx001.2')
            rxnormLog.error(str(_error) + '\n')

    def get_tty(self):
        return self.tty

    def get_name(self):
        return self.name

    def set_status(self, in_status):
        if in_status is not None:
            self.status = in_status.upper()
        else:
            _error = rxnorm_error('#Bx001.3')
            rxnormLog.error(str(_error) + '\n')

    def get_status(self):
        if self.status is None:
            valid, status = rxnav.get_rxcui_status(self.cui)
            if valid:
                self.set_status(status)
                return self.status
            else:
                _error = rxnorm_error('#Bx001.3')
                rxnormLog.warning(_error + '\n')
        else:
            if not self.valid:
                _error = rxnorm_error('#Bx001.3')
                rxnormLog.warning(_error + '\n')
                return None
            else:
                return self.status

    def get_active_cui(self):
        """Get the primary cui for this RxCUI object - Return the New cui if the original is no longer active"""
        if len(self.remap_cui) == 0:
            return self.cui
        else:
            # For now return just the first remap cui
            return self.remap_cui[0].get_active_cui()

    def add_ingredient(self, in_cui):
        if type(in_cui) is list:
            rxnormLog.debug('In_CUI is List : ' + str(in_cui))
            for cui in in_cui:
                self.add_ingredient(cui)

        elif type(in_cui) is dict:
            rxnormLog.debug('In_CUI is DICT : ' + str(in_cui))
            try:
                if 'rxcui' in in_cui.keys():
                    self.add_ingredient(in_cui['rxcui'])
            except KeyError:
                rxnorm_error('#Bx001.1')
                return

        else:
            rxnormLog.debug('In_CUI is String : ' + in_cui)
            rxcui = get_rxcui(str(in_cui))
            if rxcui.cui not in self.ing_list.keys():
                rxnormLog.debug('Ingredient Not Present, Adding...')
                self.ing_list[rxcui.cui] = rxcui
            else:
                rxnormLog.debug('Ingredient Already Present, Passing...')
        rxnormLog.debug('Ingredient List : ' + str(self.ing_list))
        return

    def find_ingredients(self):
        """ Returns a list of RxCUI Objects of TTY = [IN,MIN]"""
        if self.tty in ['IN', 'MIN']:
            return {self.cui: self}
        elif self.ing_checked:
            return self.ing_list
        else:
            ing_count = 0
            act_cui = self.get_active_cui()
            if type(act_cui) is list:
                rxnormLog.debug('Active CUI: Is List')
                for cui in act_cui:
                    rxcui_o = get_rxcui(cui)
                    success, cui_list = rxnav.get_rxcui_ingredients(rxcui_o.get_active_cui()) \
                        if rxcui_o.get_tty() not in ['IN', 'MIN'] else False, None

                    if success:
                        for key in cui_list.keys():
                            self.add_ingredient(cui_list[key])
                            ing_count += 1
            else:
                rxnormLog.debug('Active CUI: Not List')
                rxcui_o = get_rxcui(act_cui)
                success, cui_list = rxnav.get_rxcui_ingredients(rxcui_o.get_active_cui())
                if success:
                    for key in cui_list.keys():
                        self.add_ingredient(cui_list[key])
                        ing_count += 1
                else:
                    rxnorm_error('#Bx002.1')
            self.ing_checked = True
            if ing_count > 0:
                rxnormLog.debug('ING Count: %s', ing_count)
                return True
            else:
                return False

    def get_ingredients(self):
        if self.tty in ['IN', 'MIN']:
            return [self]
        elif self.ing_checked and len(self.ing_list) > 0:
            rxnormLog.debug('ING List: ' + str(self.ing_list))
            return self.ing_list
        elif not self.ing_checked:
            self.find_ingredients()
            return self.get_ingredients()
        else:
            return []

    def get_property(self, prop):
        if hasattr(self, prop):
            return getattr(self, prop)
        else:
            return None

    def check_tty(self, in_tty):
        format_tty = in_tty.upper()
        if format_tty in _tty_dict:
            return [True, format_tty]
        else:
            error_ret = {'code': '#Mx001.1'}
            error_ret['msg'] = 'Invalid Term Type Provided (' + error_ret['code'] + ') | Invalid TTY: ' + in_tty
            return [False, error_ret]

    def print_formats(self, p_type=None):
        rxnormLog.debug('Getting print format..')
        if p_type == 'simple' or p_type is None:
            _print = {
                'rxcui': self.get_active_cui(),
                'tty': self.get_tty(),
                'name': self.get_name()
            }

        elif p_type == 'ing':
            _print = self.print_formats()
            _ing = self.get_ingredients()
            logging.debug(_ing)
            _print['ingredients'] = [get_rxcui(rxcui).print_formats() for rxcui in _ing]

        elif p_type == 'complete':
            _print = self.print_formats()
            _ing = self.print_formats('ing')

        return _print
