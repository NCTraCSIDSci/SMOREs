# Python Lib Modules
import mmap, logging
# Community Modules
# SMOREs Internal Imports
from smores import medication as m
from smores import medicationdictionary as md
from smores.utility.errors import smores_error
import smores.utility.util as util


smoresLog = logging.getLogger(__name__)

class MedKit:
    '''

    '''
    med_kits = {}

    @staticmethod
    def src_is_medkit(src: str):
        if src in MedKit.med_kits.keys():
            return True
        elif src =='ALL' and len(MedKit.med_kits) > 0:
            return True
        else:
            return False

    @staticmethod
    def get_medkit(kit_name: str = None):
        '''
        Get function to return a MedKit object or lsit of MedKit objects for multi-processing
        :param kit_name:
        :return: List of all MedKits if :param kit_name is None,
                Single MedKit object of :param kit_name is not None
                Raise error if kit is not found
        '''
        if (kit_name is None or kit_name.upper() == 'ALL') and len(MedKit.med_kits) > 0:
            return MedKit.med_kits
        else:
            if kit_name in MedKit.med_kits.keys():
                return MedKit.med_kits[kit_name]
            else:
                smores_error('#Kx000.1')
                raise ValueError('Input Error - No MedKit of name {0} was found. Check File loads.'.format(kit_name))

    @staticmethod
    def load_session(kits:dict):
        _e = []
        medkits = MedKit.med_kits
        for kit, obj in medkits.items():
            medkits[kit] = None
            del obj
            MedKit.med_kits.pop(kit)
        MedKit.med_kits = {}
        for kit, obj in kits.items():
            if isinstance(obj, MedKit):
                MedKit.med_kits[kit] = obj
            else:
                _e.append(kit)
        m.Medication.med_id_list = {kit : obj.med_list for kit, obj in MedKit.med_kits.items()}
        return _e

    def __init__(self, in_file, file_delim=','):
        self.path = in_file
        self.file_name = util.get_filename(in_file)
        self.delim = file_delim
        self.file_lines = self.get_file_lines()
        self.c_records = 0
        self.records = {}
        self.headers = util.read_config_value('INFILE_KEYS')
        self.trackers = {}
        self.cui_types = []
        self.m_dict = md.MedicationDictionary(self.file_name, link=self)
        MedKit.med_kits[self.file_name] = self

        m.Medication.med_id_list[self.file_name] = {}
        self.med_list = m.Medication.med_id_list[self.file_name]

    def add_med(self, id, type):
        med = m.get_med_by_id(id, self.file_name)
        self.add_cui_type(type)
        smoresLog.debug("MedKit MedDictionary: {0}".format(self.m_dict))
        self.med_list[id] = med
        self.m_dict.add_med_with_id(med, id)

    def add_cui_type(self, cui_type):
        if cui_type not in self.cui_types:
            self.cui_types.append(cui_type)
            self.cui_types = sorted(self.cui_types)

    def get_cui_types(self):
        return self.cui_types

    def get_headers(self, delim=','):
        try:
            data = open(self.path, "r+").readline()
            keys = list(util.read_config_value('INFILE_KEYS').values())
            map = {}
            _d = data.split(delim)
            for key in keys:
                for i in range(len(_d)):
                    if _d[i].replace('\n', '') == key:
                        map[key] = i
            return map
        except FileNotFoundError:
            smores_error('#Cx001.1')
            return None
        except PermissionError:
            smores_error('#Cx001.2')
            return None

    def get_file_lines(self) -> int:
        try:
            smoresLog.debug('Getting Number of Lines in File...')
            fp = open(self.path, "r+")
            buf = mmap.mmap(fp.fileno(), 0)
            lines = 0
            while buf.readline():
                lines += 1
            smoresLog.info('File Size of {0} Lines Found...'.format(lines))
            return lines -1
        except FileNotFoundError:
            smores_error('#Cx001.1')
            return 0
        except PermissionError:
            smores_error('#Cx001.2')
            return 0

    def set_records(self, dict):
        self.records = dict
        return

    def get_records(self):
        return self.records

    def set_record_count(self, num):
        self.c_records = num
        return
    def get_record_count(self, num):
        return self.c_records