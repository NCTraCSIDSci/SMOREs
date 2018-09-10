import cmd
import os
import logging
import timeit
from configparser import ConfigParser
import smores.medkit as smores
from smores.errors import smores_error

smoresLog = logging.getLogger(__name__)


def load_environment():
    logging.debug('Parsing config.ini and environmental variables')
    config = ConfigParser()
    config.read('config.ini')

    config['main']['input_file'] = os.getenv('input_file', config['main'].get('input_file'))

class smoresCLI(cmd.Cmd):
    _OPTIONS_RXNSTATUS = ['LOCAL', 'RXCUI', 'NDC', 'SNOMED']

    def __init__(self, _meta):
        cmd.Cmd.__init__(self)
        self.__version__ =  _meta['version']
        self.__grant__ = _meta['grant']
        # self.config = load_environment()
        self.intro = 'Welcome to the CAMP-FHIR Synergistic Medication Organizer for RxNorm and Extras! \n' \
            'Release ' + self.__version__ + ' \n ' \
            'Development of this tool is supported by ' + self.__grant__ + ' \n\n ' \
            'Type help or ? to list commands.\n '
        self.inputs = {'loaded': False, 'files': [], 'count': 0}
        self.prompt = '>'
        self.use_rawinput = True
        self.errors = {}

    def validate_args(self, args, cmd_call):
        validated = None
        if cmd_call in ['default']:
            while True:
                if len(args) == 2:
                    validated = args[1].upper()
                else:
                    validated = input("What type of id is '{0}'?  [LOCAL/RXCUI/NDC/SNOMED]".format(args[0])).upper()
                if len(validated) > 0:
                    if validated == 'LOCAL' and not self.inputs['loaded']:
                        print("No Files Loaded!\nYou Must load a file containing local medications first")
                        return
                    elif validated in self._OPTIONS_RXNSTATUS:
                        break
                    else:
                        print('Invalid Option, Please Try Again')
                        continue
        elif cmd_call == 'ndc':
            validated = self.validate_args(args, 'default')
        elif cmd_call == 'fhir':
            validated = self.validate_args(args, 'default')
        elif cmd_call == 'ing':
            validated = self.validate_args(args, 'default')
        elif cmd_call == 'rxn_status':
            validated = self.validate_args(args, 'default')
        elif cmd_call == 'errors':
            if len(args) > 1:
                print('Too many parameters entered. Please enter only one parameter.')
            else:
                _current_err = list(self.errors.keys())
                if args[0] in _current_err:
                    validated = args[0]
                else:
                    print('There are currently no errors logged for that command.')
        return validated

    def simple_input(self, question, values):
        list_vals = values
        while True:
            _input = input(question + str(list_vals)).upper().strip()
            if _input in list_vals:
                break
            else:
                print('Invalid Option, Please Try Again')
                continue

        return _input

    @staticmethod
    def do_exit(self, arg=None):
        print('Until next time...')
        self.close()
        return True

    def do_load(self, arg):
        print('Load')
        """Read in a designated file containing information on local medications
Syntax: load [file_name]
    - [file_name] is optional at entry but will be required.
    Files by default are expected to reside in this programs '/input' folder. If located under
    a different path, it must be fully specified"""
        if len(arg.strip()) > 0:
            _file = arg
        else:
            _file = None

        def _do_load(_input=None):
            print("* Note: All input files must reside in the 'input' folder of this program "
                  "or contain a fully specified file path")
            if _input is None:
                _file_input = input("Please enter the name of the file to load: ")
            else:
                _file_input = _input
            if _file_input in self.inputs['files']:
                print("It looks like you've already loaded that file. Please try a different file.")
            else:
                tic = timeit.default_timer()
                success, count = smores.load_file(_file_input)
                if success:
                    self.inputs['loaded'] = True
                    self.inputs['files'].append(_file_input)
                    self.inputs['count'] += count['records']
                    toc = timeit.default_timer()
                    elapsed = str(round(toc - tic, 2))
                    print('\nElapsed Time: ' + str(elapsed) + ' seconds')
                    print("\nSuccess! {0} New Medication(s) Successfully Loaded from File".format(count['records']))
                    if count['dups'] > 0:
                        print("{0} Duplicate Local ID's were found. New Information "
                              "was added to previous record.".format(str(count['dups'])))
                    if len(count['errors']) > 0:
                        print("{0} Invalid RxCUI's encountered in file. ".format(str(len(count['errors']))))
                        print("\nType 'errors load' to see a list of RxCUI errors or check logs for more information")
                        self.errors['load'] = count['errors']
                    return
                else:
                    print('Something went wrong...')
                    return

        if self.inputs['loaded']:
            print("The following file(s) have already been loaded: \n"+str(self.inputs['files']))
            _load_more = self.simple_input("Would you like to load an additional file?",  ['Y', 'N', 'exit'])
            if _file is not None:
                print('Current File to Be Loaded: '+_file)
            if _load_more == 'Y':
                _do_load(_file)
            elif _load_more in ('N', ''):
                print("Returning to Starting Point")
                return
            else:
                print("Unknown Entry")
                self.do_load()
        else:
            _do_load(_file)

    def do_load_count(self, arg):
        print(self.inputs['count'])
        return

    def do_rxn_status(self, arg):
        """Look up the active status of RXCUI's from a medication file.
                REQUIRES A FILE TO BE LOADED OR A SPECIFIC RXCUI TO BE PROVIDED"""
        if len(arg) > 0:
            args = arg.split()
            type_check = self.validate_args(args, 'rxn_status')
            if type_check is not None:
                if type_check == 'RXCUI':
                    print("Processing RxNorm Status of RxCUI: " + str(args[0]))
                    status = smores.get_status(args[0], 'RXNORM')
                    if status is not None:
                        print('RxCui : ' + str(args[0]) + '\nRxNorm Status : ' + status)
                elif type_check == 'LOCAL' and self.inputs['loaded']:
                    print("Processing RxNorm Status of Local Med: " + str(args[0]))
                    status = smores.get_status(args[0], 'LOCAL')
                    if status is not None and type(status) is dict:
                        for cui, rx_stat in status.items():
                            print('RxCUI : ' + cui + ' , Status: ' + rx_stat)

        elif self.inputs['loaded']:
            while True:
                _run = self.simple_input("Check status of all loaded Local Medications?",  ['Y', 'N', 'exit'])
                if _run in ['Y', 'N', 'exit']:
                    break
                else:
                    print('Invalid Option, Please Try Again')
                    continue

            if _run == 'Y':
                success, count = smores.run_status('LOCAL')
                if len(count['errors']) > 0:
                    print("{0} Invalid RxCUI's encountered. ".format(str(len(count['errors']))))
                    print("\nType 'errors load' to see a list of RxCUI errors")
                    self.errors['load'] = count['errors']
            elif _run == 'N':
                print("Enter '? rxn_status' for options in running this command")
            else:
                print('Invalid Option')
            # TODO Write run_status in smores to get the status of all Medications
        else:
            print("No Files Loaded!\nYou Must load a file containing local medications first "
                  "or specifiy a specific ID to check")


    def do_rxn_ingredients(self, arg):
        """Look up the ingredients for a medication through RxNorm
        REQUIRES A FILE TO BE LOADED OR A SPECIFIC RXCUI TO BE PROVIDED"""
        if len(arg) > 0:
            args = arg.split()
            type_check = self.validate_args(args, 'ing')
            if type_check is not None:
                if type_check == 'RXCUI':
                    print("Processing RxNorm Ingredients of RxCUI: " + str(arg))
                    ingredients = smores.get_ingredients(args[0], 'RXNORM')
                elif type_check == 'LOCAL' and self.inputs['loaded']:
                    print("Processing RxNorm Status of Local Med: " + str(args[0]))
                    ingredients = smores.get_ingredients(args[0], 'LOCAL')
                if ingredients is not None:
                    for rx_ing in ingredients:
                        print(rx_ing)
                else:
                    smores_error('#Cx004.3')
            else:
                print('Sorry that option isn\'t supported yet')

        elif self.inputs['loaded']:
            _run = self.simple_input("Get ingredients of all loaded Local Meds?", ['Y','N'])

            if _run == 'Y':
                smores.run_ingredients('LOCAL')
            elif _run == 'N':
                print("Enter '? rxn_ingredients' for options in running this command")
            else:
                print('Invalid Option')

        else:
            print(
                "No Files Loaded!\nYou Must load a file containing local "
                "medications first or specifiy an RxCUI to check")


    def do_fhir(self, arg, test=False):
        """Converts information pertaining to a medication into FHIR STU3 JSON Format"""
        if test:
            smores.run_med_to_json('LOCAL', None, [True, None], [True, 'fhir_test/'])
        else:
            input_src = None
            wr = [False, None]
            input_id = None
            local_print = []
            if len(arg) > 0:
                args = arg.split()
                type_check = self.validate_args(args, 'fhir')
                if type_check == 'RXCUI':
                    input_src = 'RXNORM'
                    _run = 'Y'
                    input_id = args[0]
                elif type_check == 'LOCAL' and self.inputs['loaded']:
                    input_src == 'LOCAL'
                    _run = 'Y'
                    input_id = args[0]
                else:
                    _run = 'N'
            elif self.inputs['loaded']:
                _run = self.simple_input('Get JSON of all loaded Local Meds?', ['Y', 'N'])
                input_src = 'LOCAL'
                _local = self.simple_input('Include local id\'s in coding block?', ['Y', 'N'])
                if _local.upper() == 'Y':
                    _local_uri = input('Please provide the system for local id\'s:')
                    id_print=[True, _local_uri]
            if _run == 'Y':
                _write_bool = self.simple_input('Do you want to write the output to a file?', ['Y', 'N'])
                _output = 'N'
                if _write_bool in ['Y']:
                    _output = input('Please provide a file name: ')
                    wr = [True, _output]

                if _output != 'EXIT':
                    smores.run_med_to_json(input_src, input_id, wr, id_print)
                else:
                    return
            elif _run == 'EXIT':
                return
            else:
                print("Enter '? jsonify' for options in running this command")
                return
    def do_json(self,arg):
        """Converts information pertaining to a medication into FHIR STU3 JSON Format.
        Performs the same actions as executing the 'fhir' command"""
        self.do_fhir(arg) # Simply re-direct for now, just provide two different paths

    def do_csv(self, arg):
        smores.run_med_to_csv('LOCAL')

    def do_errors(self, arg):
        if len(self.errors) == 0:
            print("There are currently no errors to display.")
        else:
            if len(arg) > 0:
                args = arg.split()
                type_check = self.validate_args(args, 'errors')
                if type_check is not None:
                    print(self.errors[type_check])


    def do_test(self, arg):
        if arg == 'ing1':
            smoresLog.info('Running Ingredients Test 1...')
            smoresLog.info('1) Loading testFile.csv')
            self.do_load('tests/testFile.csv')
            smoresLog.info('2) Getting All Ingredients')
            self.do_rxn_ingredients('')
        elif arg == 'ing2':
            smoresLog.info('Running Ingredients Test 2...')
            smoresLog.info('1) Loading testFile.csv')
            self.do_load('tests/testFile.csv')
            smoresLog.info('2) Getting Ingredients Of Local Med: 1234')
            self.do_rxn_ingredients('1234 LOCAL')
        elif arg == 'ing3':
            smoresLog.info('Running Ingredients Test 3...')
            smoresLog.info('Testing RxNav Individual Call')
            # 353605, CHLORPHENIRAMINE-PHENYLEPHRINE-DM 4 MG-10 MG-12.5MG/5 ML ORAL LIQUID
            self.do_rxn_ingredients('8164 RXCUI')
        elif arg == 'status':
            self.do_load('tests/testFile.csv')
            self.do_rxn_status('')
        elif arg == 'fhir':
            smoresLog.info('Running FHIR Output Test...')
            self.do_load('tests/testFile.csv')
            self.do_fhir('', test=True)
        elif arg == 'ld':
            smoresLog.info('Running Load Test...')
            self.do_load('testFile2.csv')

    def emptyline(self):
        """Do nothing on an empty input line"""
        pass