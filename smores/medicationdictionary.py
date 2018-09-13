import logging
smoresLog = logging.getLogger(__name__)
src_list = {}

def get_med_dict_by_src(src):
    """ Returns a MedicationDictionary with a Source = @src - Always returns MASTER"""
    med_dict_list = MedicationDictionary.src_list
    smoresLog.debug('Source Requested: {0} , Current List: {1}'.format(src, med_dict_list))
    if src not in med_dict_list.keys():
        _md = MedicationDictionary(src)
    else:
        _md = med_dict_list[src]['MASTER']
    return _md


def get_available_med_dict():
    return MedicationDictionary.src_list

def get_obj_by_src(obj_id, src):
    return get_med_dict_by_src(src).get_med_by_id(obj_id)

def get_src_list():
    global src_list
    return src_list

class MedicationDictionary:
    """ Constructs a Dictionary for Various Medication Types.
    Can include pointers to either Medication.class or RxCUI.class Objects
    Will only contain pointers of a single object type"""

    src_list = get_src_list()

    def __init__(self,  dict_src='', dict_id=None, link=None):
        if dict_src != '':
            self.source = dict_src
            if dict_id is not None:
                MedicationDictionary.src_list[dict_src][dict_id] = self
            else:
                MedicationDictionary.src_list[dict_src] = {'MASTER': self}
                smoresLog.debug(MedicationDictionary.src_list)
        if link is not None:
            self.link = link
            MedicationDictionary.src_list[dict_src]['LINK'] = link
        else:
            self.link = None
        self.local_ids_avail = False
        self.rxcui_avail = False
        self.rxcui_status_avail = False
        self.ing_avail = False
        self.rxcui_matches_avail = False
        self.ndc_avail = False
        self.primary_key = ''
        # Object that contains the med id's as Keys and pointers to their medication object
        self.med_list = {}
        self.description = ''

    def add_med_with_id(self, in_med, id_check):
        """Add a Medication to a MedicationDictionary
            @in_med : A Medication or RxCUI object
            @id_check : The desired id of the Medication object to check.
                    This parameter depends on what ID (RXCUI, NDC, LOCAL) is the basis of the MedicationDictionary to
                    prevent duplicate entries"""
        smoresLog.debug("Performing ID Check... " + str(id_check))
        smoresLog.debug(id_check)
        if type(id_check) is not str:
            id_check = str(id_check)
        if not self.check_list_by_id(id_check):
            smoresLog.debug("Medication not found, adding to dictionary")
            self.med_list[id_check] = in_med
            return True
        else:
            smoresLog.debug("Medication already found, preventing duplicate entries.")
            return False

    def set_description(self, in_desc):
        self.description = in_desc

    def check_list_by_id(self, med_id):
        if med_id not in self.med_list:
            return False
        else:
            return True

    def has_records(self):
        if self.get_med_count() > 0:
            return True
        else:
            return False

    def set_input(self, input_src):
        self.primary_key = input_src.upper()
        if self.primary_key == 'RXCUI':
            self.rxcui_avail = True
        elif self.primary_key == 'LOCAL':
            self.local_ids_avail = True
        elif self.primary_key == 'NDC':
            self.ndc_avail = True
        else:
            self.primary_key = 'SYS'

    def get_med_by_id(self, med_id):
        return self.med_list[med_id]

    def get_med_by_property(self, prop, prop_val):
        mod_list = []
        smoresLog.debug(prop + ':' + str(prop_val))
        smoresLog.debug(self.med_list)
        for med_id, med in self.med_list.items():
            if type(prop_val) is list:
                if med.get_property(prop) in prop_val:
                    mod_list.append(med_id)
            else:
                if med.get_property(prop) == prop_val:
                    mod_list.append(med_id)
        return mod_list

    def get_dict_source(self):
        return self.source

    def get_med_count(self):
        return int(len(self.med_list))

    def get_avail_print_type(self):
        print_options = []
        if self.rxcui_status_avail:
            print_options.append(['STATUS', 'Current RXNorm Status of Input RxNorm Codes'])
        if self.ing_avail:
            print_options.append(['ING', 'Ingredients and Multi Ingredients for Provided Medications'])
        if self.rxcui_matches_avail:
            print_options.append(['MATCH', 'RxNorm Matches Obtained for Provided Medication Names'])

        return print_options

    def get_print_headers(self, p_type, p_scope='FULL'):
        return_headers = [self.primary_key.lower()]
        smoresLog.debug('Getting Print Headers...' + p_type)
        if self.local_ids_avail:
            return_headers.append('local_id')

        if p_type == 'STATUS' and self.rxcui_status_avail:
            return_headers.append('rxcui_status')
            if p_scope == 'FULL':
                return_headers.append('tty')
                return_headers.append('new_rxcui')

        elif p_type == 'ING' and self.ing_avail:
            if self.primary_key != 'RXCUI':
                return_headers.append('parent_rxcui')
            return_headers.append('ing_rxcui')
            return_headers.append('ing_tty')

        elif p_type == 'MATCH' and self.rxcui_matches_avail:
            return_headers.append('match_rxcui')
            if p_scope == 'FULL':
                return_headers.append('match_tty')
                return_headers.append('match_name')
                return_headers.append('confidence')

        return return_headers

    def get_med_list(self, modifier=None):
        if modifier is not None:
            mod_list = []
            for prop, value in modifier.items():
                for cui, med in self.med_list.items:
                    if med.get_property(prop) == value:
                        mod_list.append(cui)
            return mod_list
        else:
            return list(self.med_list.keys())
