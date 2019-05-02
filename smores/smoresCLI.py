import cmd
import logging
import timeit
import smores.processes as smores
from smores.utility.errors import smores_error
from smores.utility.util import validate_id
import smores.utility.util as util

smoresLog = logging.getLogger(__name__)

_OPTIONS_RXNSTATUS = util.OPTIONS_RXNSTATUS


class smoresCLI(cmd.Cmd):

    def __init__(self, _meta):
        cmd.Cmd.__init__(self)
        self.__version__ =  _meta['version']
        self.__grant__ = _meta['grant']
        self.intro = 'Welcome to the CAMP-FHIR Synergistic Medication Organizer for RxNorm and Extras! \n' \
            'Release ' + self.__version__ + ' \n ' \
            'Development of this tool is supported by ' + self.__grant__ + ' \n\n ' \
            'Type help or ? to list commands.\n '
        self.inputs = {'loaded': False, 'files': {}, 'count': 0}
        self.prompt = '>'
        self.use_rawinput = True
        self.errors = {}
        self.files = self.inputs['files']
        self.cmds = ['rxn_ing','rxn_status','fhir','csv','rxn_lookup','rxn_remap','rxn_history']

    @staticmethod
    def simple_input(question, values, index=False):
        _vals = [str(val).upper() for val in values]
        _display_vals = ['[' + str(i) + '] ' + str(values[i]).upper() for i in range(len(values))] if index else _vals
        while True:
            _input = input(question + str(_display_vals) + ' : ').upper().strip()
            if _input in _vals:
                _index = _vals.index(_input)
                return values[_index]
            elif _input.isnumeric() and int(_input) < len(_vals):
                return values[int(_input)]
            elif _input == 'EXIT':
                return 'exit'
            else:
                print('Invalid Option, Please Try Again')
                continue

    def validate_id_type(self, id_type):
        global _OPTIONS_RXNSTATUS
        if len(id_type) > 0:
            if id_type == 'LOCAL' and not self.inputs['loaded']:
                print("No Files Loaded!\nYou Must load a file containing local medications first")
                valid_type = 'EXIT'
            elif id_type in _OPTIONS_RXNSTATUS:
                valid_type = True
            elif id_type.upper() == 'EXIT':
                valid_type = None
            else:
                valid_type = False
            return valid_type
        else:
            return False

    def validate_args(self, in_args, cmd_call):
        valid_1, valid_2 = None, None

        if len(in_args) > 0 and type(in_args) is not list:
            args = in_args.split()
            valid_1 = args[0]
        elif type(in_args) is list and len(in_args) > 0:
            args = in_args
            valid_1 = args[0]
        else:
            args = []

        if cmd_call in ['default']:
            while True:
                if len(args) == 2:
                    input_type = args[1].upper()
                else:
                    input_type = input("What type of id is '{0}'?  [LOCAL/RXCUI/NDC/SNOMED]".format(args[0])).upper()

                valid_type = self.validate_id_type(input_type)
                if isinstance(valid_type, str) or valid_type is None:
                    return None
                elif valid_type:
                    break
                elif not valid_type:
                    print('Invalid Option, Please Try Again')
                    continue
            valid_1 = input_type

        elif cmd_call == 'rxn_ing':
            valid_2, _ = self.validate_args(args, 'default')
            valid_1 = args[0]
        elif cmd_call == 'rxn_status':
            valid_2, _ = self.validate_args(args, 'default')
            valid_1 = args[0]
        elif cmd_call == 'rxn_remap':
            valid_2, _ = self.validate_args(args, 'default')
            valid_1 = args[0]
        elif cmd_call == 'rxn_lookup':
            valid_2, _ = self.validate_args(args, 'default') # Validated will provide the valid ID Type
            valid_1 = args[0] if valid_2 and validate_id(args[0], valid_2) else False # Ensures the input id is a valid id of the specified type

        elif cmd_call == 'errors':
            _current_err = list(self.errors.keys())
            if len(args) > 1:
                smores_error('#Cx001.7', console_p=True)
                return
            elif len(args) == 1 and args[0].lower() in _current_err:
                valid_1 = args[0]
            elif len(args) == 1:
                print('There are currently no errors logged for that command.')
                return
            else:
                valid_1 = self.simple_input("Please choose a command from the list to see errors: ", _current_err)

        elif cmd_call in ['csv', 'remap', 'fhir', 'json']:
            # Format: [File] [Output]
            if not self.inputs['loaded']:
                print("No Files Loaded!\nYou Must load a file containing local medications first")
                return
            else:
                _file_opts = list(self.inputs['files'].keys()) + ['All']
                _dict_opts = list(smores.get_dict_sources()) + ['All']
                _file_or_dict = None

                if cmd_call in ['csv', 'json']:
                    if len(args) == 0:
                        _file_or_dict = self.simple_input("Do you want results for a File or a constructed Dictionary?",
                                                          ['File', 'Dictionary', 'exit'], True)
                    elif args[0] not in _file_opts and args[0] not in _dict_opts:
                        print('That option was not recognized as a valid source.')
                        _file_or_dict = self.simple_input("Do you want results for a File or a constructed Dictionary?",
                                                          ['File', 'Dictionary', 'exit'], True)
                    else:
                        valid_1 = args[0]

                    if _file_or_dict.upper() == 'FILE':
                        valid_1 = 'FILE|' + self.simple_input("Please choose a loaded file", _file_opts, True)
                    elif _file_or_dict.upper() == 'DICTIONARY':
                        valid_1 = 'DICT|' + self.simple_input("Please choose a code dictionary to output", _dict_opts, True)
                    elif _file_or_dict.upper() == 'EXIT':
                        return
                else:
                    valid_1 = self.simple_input("Please choose a loaded file", _file_opts, True)

                if cmd_call in ['csv', 'json', 'fhir']:
                    if len(args) == 2 and len(args[1]) > 0:
                        valid_2 = args[1]
                    else:
                        valid_2 = input("Please provide an output file name: ").strip()

                    if len(valid_2) > 0:
                        if "." in valid_2:
                            valid_2, ext = valid_2.split(".")
                    else:
                        valid_2 = ''
                        print('Empty file name provided, using default.')
                else:
                    valid_2 = args[0]

        smoresLog.debug('Args: {0}, Validated as: {1}'.format(valid_1, valid_2))
        return valid_1, valid_2

    def get_untouched(self, cmd:str=None, force:bool=False):
        '''
        Get loaded files that have NOT been used in console command
        :param cmd: Console command issued
        :param force: Force return of all options regardless if ran or not
        :return: list of files
        '''
        _r = []
        if cmd is not None:
            for _f, _d in self.inputs['files'].items():
                if not _d[cmd] or force:
                    _r.append(_f)
        else:
            for _f in self.inputs['files'].keys():
                _r.append(_f)
        return _r

    def set_touched(self, file:str, cmd:str):
        if file.upper() == 'ALL':
            for _f, _d in self.inputs['files'].items():
                _d[cmd] = True
        else:
            print(self.inputs['files'])
            self.inputs['files'][file][cmd] = True

    def run_id_call(self, func, cmd:str, in_type:str, in_id:str=None):
        if in_type == 'LOCAL' and self.inputs['loaded']:
            if len(self.inputs['files']) > 1:
                file_src = self.simple_input("Please choose a loaded file ", self.inputs['files'], True)
            else:
                file_src = self.inputs['files'][0]
            _r = func(client_cmd=cmd, file=file_src)
        else:
            _r = func(client_cmd=cmd, med_id=in_id, med_id_type=in_type)
        return _r

    def run_file_call(self, func, cmd:str):
        file_msg = "Run {0} on all loaded files?".format(cmd)
        _run = self.simple_input(file_msg, ['Y', 'N', 'exit'])

        if _run == 'Y':
            _avail = self.get_untouched(cmd)
            if len(_avail) == 0:
                print('It looks like you''ve already ran this command for all available files.')
                while True:
                    _run_x = self.simple_input("Do you want to re-run any/all files?", ['Y', 'N', 'exit'])
                    if _run_x in ['Y', 'N', 'exit']:
                        break
                    else:
                        print('Invalid Option, Please Try Again')
                        continue
                if _run_x == 'Y':
                    _avail = self.get_untouched(cmd, True)
                else:
                    return

            if len(_avail) == 1:
                file = 'ALL'
            else:
                _avail.append('ALL')
                _avail.append('exit')
                file = self.simple_input("Please choose a file to run, or run all:", _avail)

            if file.upper() == 'EXIT':
                return None
            else:
                return func(client_cmd=cmd, file=file)

        elif _run == 'N':
            print("Enter '? rxn_status' for options in running this command")
            return

        elif _run == 'exit':
            return

        else:
            print('Invalid Option')

    def run_cmd(self, arg, cmd_call):
        cmd_func = smores.run_client_cmd
        if len(arg) > 0:
            validated_cui, cui_type = self.validate_args(arg, cmd_call) #
            if validated_cui is not None:
                id_result = self.run_id_call(cmd_func, cui_type, validated_cui, cmd_call)
            else:
                id_result = None

            if id_result is not None:
                print('Command Completed: {0}\nResults for {1} {2}'.format(cmd_call,cui_type,validated_cui))
                if type(id_result) is dict:
                    if 'print' in id_result.keys():
                        for rx_c, rx_res in id_result['print'].items():
                            if rx_c == validated_cui:
                                print(' {0}'.format(rx_res))
                            else:
                                print(' {0} : {1}'.format(rx_c, rx_res))
                    else:
                        for rx_k, rx_val in id_result.items():
                            if rx_k == validated_cui:
                                print(rx_val)
                            else:
                                print('{0} : {1}'.format(rx_k, rx_val))
                else:
                    print('Result: {0}'.format(id_result))
            else:
                smores_error('#Cx004.3')

        elif self.inputs['loaded']:
            count_ran, errors, file = self.run_file_call(cmd_func, cmd_call)

            if count_ran is None:
                return
            else:
                self.set_touched(file, cmd_call)
                print('Command {0} Completed for {1} medications'.format(cmd_call,count_ran))

            if len(errors) > 0 and len(errors[0]) > 0:
                self.update_errors(cmd_call, errors)
        else:
            print("No Files Loaded!\nYou Must load a file containing local medications first "
                  "or specifiy a specific ID to check")

    def update_errors(self, cmd, errors:list):
        print("{0} Invalid Code's encountered.\nType 'errors {1}' to see a list of CUI/Code errors\n".format(len(errors), cmd))
        if cmd not in self.errors.keys():
            self.errors[cmd] = errors
        else:
            self.errors[cmd] += errors

    def do_exit(self, arg=None):
        print('Until next time...')
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
            elif '.smr' in _file_input:
                if len(self.inputs['files']) > 0:
                    print('It looks like you are trying to load a session, this will replace all previous work.')
                    _save = self.simple_input('Do you want to save the current session first?',['Y','N','EXIT'])
                    if _save == 'Y':
                        smores.save_session(self.__version__)
                    elif _save == 'EXIT':
                        return
                loaded = smores.load_session(_file_input, self.__version__)
                if len(loaded) > 0:
                    self.inputs['loaded'] = True
                    self.inputs['files'] = {file: {} for file in loaded}
                    for _file in self.inputs['files']:
                        self.inputs['files'][_file] = {_c: False for _c in self.cmds}
                    print('Session {0} Load Complete'.format(_file_input))
                    print('Note: All SMOREs commands have been reset')
                else:
                    print('Failed to Load Files from Session')
            else:
                tic = timeit.default_timer()
                success, result = smores.load_file(_file_input)
                if success:
                    self.inputs['loaded'] = True
                    self.inputs['files'][_file_input] = {_c : False for _c in self.cmds}
                    self.inputs['count'] += result['records']
                    toc = timeit.default_timer()
                    elapsed = str(round(toc - tic, 2))
                    print('\nElapsed Time: ' + str(elapsed) + ' seconds')
                    print("\nSuccess! {0} New Medication(s) Successfully Loaded from File".format(result['records']))
                    if result['dups'] > 0:
                        print("{0} Duplicate Local ID's were found. New Information "
                              "was added to previous record.".format(str(result['dups'])))
                    if len(result['errors']) > 0:
                        self.update_errors('load', result['errors'])
                    return
                else:
                    if result is not None:
                        smores_error(result, console_p=True)
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
            elif _load_more in ('N', '', 'exit'):
                print("Returning to Starting Point")
                return
            else:
                print("Unknown Entry")
                self.do_load()
        else:
            _do_load(_file)

    def do_workflow(self):
        """Define a sequence of commands to be ran """
        options = sorted(self.cmds)
        print('Preparing Workflow Wizard...')
        _file = input('Please provide a file name:')


        print('Available Commands for WorkFlow')
        for i, _o in enumerate(options):
            print('{0}) {1}'.format(i, _o))

    def do_load_count(self, arg):
        print(self.inputs['count'])
        return

    def do_rxn_status(self, arg):
        """Look up the active status of RXCUI's from a medication file.
        REQUIRES A FILE TO BE LOADED OR A SPECIFIC RXCUI TO BE PROVIDED"""

        cmd_call = 'rxn_status'
        self.run_cmd(arg, cmd_call)

    def do_rxn_ingredients(self, arg):
        """Look up the ingredients for a medication through RxNorm
        REQUIRES A FILE TO BE LOADED OR A SPECIFIC RXCUI TO BE PROVIDED"""
        cmd_call = 'rxn_ing'
        self.run_cmd(arg, cmd_call)

    def do_rxn_lookup(self, arg):
        """Look up current RxNorm CUI for any loaded medication by a linked CUI.
        Will NOT perform name matches which is currently a WiP for a future release."""
        cmd_call = 'rxn_lookup'
        self.run_cmd(arg, cmd_call)

    def do_rxn_remap(self, arg):
        """Look up the remapped RxCUIs for a medication through RxNorm
        REQUIRES A FILE TO BE LOADED"""
        cmd_call = 'rxn_remap'
        self.run_cmd(arg, cmd_call)

    def do_rxn_history(self, arg):
        """Looks for any history information for historical CUI's.
        Note: Only supports Retired or Alien  RxCUI"""
        print('RXN History currently only supports obtaining RxNorm History for Retired or Alien RxCUI')
        cmd_call = 'rxn_history'
        self.run_cmd(arg, cmd_call)

    def do_fhir(self, arg):
        """Converts information pertaining to a medication into FHIR STU3 JSON Format"""
        file, output_file = self.validate_args(arg, 'fhir')
        if file is not None:
            smores.run_med_to_json(file=file, out_file=output_file)
        else:
            print("Enter '? jsonify' for options in running this command")
            return

    def do_json(self, arg):
        """Converts information pertaining to a medication into FHIR STU3 JSON Format.
        Performs the same actions as executing the 'fhir' command"""
        #TODO Make 'json' a separate output option that is not in FHIR format (ie for dictionaries)
        self.do_fhir(arg) # Simply re-direct for now, just provide two different paths

    def do_csv(self, arg):
        target, output_file = self.validate_args(arg, 'csv')
        t_type, file = target.split('|')
        if file is not None:
            params = {}
            csv_constructor = {}
            if t_type == 'FILE':
                cmd_call = smores.run_med_to_csv
                print('Default output is : LOCAL_ID | LOCAL_NAME | SOURCE | CUI | CUI_TYPE')
                #TODO Add in customization of CSV structure
                params['default'] = 'Y'
                # params['default'] = self.simple_input("Do you want to save the default output data?", ['Y', 'N'])
                # params['details'] = self.simple_input("Do you want to save details to medications/codes (e.g. NDC, ingredients, term type, status)?", ['Y', 'N'])
                # params['details'] = self.simple_input(
                #     "Do you want to save code dictionaries from cache? (e.g. NDC, RXNORM)",
                #     ['Y', 'N'])
                if params['default'] == 'Y':
                    csv_constructor['default'] = ''
            elif t_type == 'DICT':
                cmd_call = smores.run_dict_to_csv
                print('Default output is : CUI | CUI Name | CUI Type | Term Type (If applicable)')
                params['default'] = 'Y'
                # TODO Add in customization of CSV structure
                if params['default'] == 'Y':
                    csv_constructor['default'] = ''
            cmd_call(file, out_file=output_file, params=csv_constructor)
        else:
            print('Error in preparing CSV')
    def do_save(self, arg):
        """Save the current session for use later on. All existing imports and results from commands will be saved.
        Cached queries to API's will not be saved as these results should be rebuilt every 48 hours due to code set fluctuations."""
        smores.save_session(self.__version__)

    def do_errors(self, arg):
        if len(self.errors) == 0:
            print("There are currently no errors to display.")
        else:
            error_code, _ = self.validate_args(arg, 'errors')
            if error_code is not None:
                _e = self.errors[error_code]
                print('Errors Encountered for "{0}" : \n{1}\n\n'.format(error_code, _e))

    def do_test(self, arg):
        testFile = 'testFile2.csv'
        if arg == 'ing1':
            smoresLog.info('Running Ingredients Test 1...')
            smoresLog.info('1) Loading testFile.csv')
            self.do_load(testFile)
            smoresLog.info('2) Getting All Ingredients')
            self.do_rxn_ingredients('')
        elif arg == 'ing2':
            smoresLog.info('Running Ingredients Test 2...')
            smoresLog.info('1) Loading testFile.csv')
            self.do_load(testFile)
            smoresLog.info('2) Getting Ingredients Of Local Med: 1234')
            self.do_rxn_ingredients('1234 LOCAL')
        elif arg == 'ing3':
            smoresLog.info('Running Ingredients Test 3...')
            smoresLog.info('Testing RxNav Individual Call')
            # 353605, CHLORPHENIRAMINE-PHENYLEPHRINE-DM 4 MG-10 MG-12.5MG/5 ML ORAL LIQUID
            self.do_rxn_ingredients('8164 RXCUI')
        elif arg == 'status':
            self.do_load(testFile)
            self.do_rxn_status('')

        elif arg == 'fhir':
            smoresLog.info('Running FHIR Output Test...')
            self.do_load('CDWH.csv')
            # self.do_fhir('', test=True)
            smores.run_rxn_history('ALL', '')
            smores.run_rxn_ingredients()
            smores.run_med_to_json(file='OPIOID_TS_MED_DICT.csv')

        elif arg == 'ld':
            smoresLog.info('Running Load Test...')
            self.do_load(testFile)

        elif arg == 'csv':
            smoresLog.info('Running Load Test...')
            self.do_load(testFile)
            success, errors = smores.run_rxn_status('testFile2.csv')

        elif arg == 'remap':
            smoresLog.info('Running Load Test...')
            self.do_load(testFile)
            smores.run_remap('ALL', '')
            smores.run_rxn_ingredients()

        elif arg == 'unc':
            _file = 'CDWH_Q2_2019_for_SMOREs.csv'
            # self.do_load('unc_rxnorm_epic_small.csv')
            self.do_load(_file)
            # self.do_save('')
            # smores.run_client_cmd(client_cmd='rxn_lookup', file=_file)
            self.do_save('')
            smores.run_client_cmd(client_cmd='rxn_remap', file=_file)
            self.do_save('')
            smores.run_client_cmd(client_cmd='rxn_history', file=_file)
            self.do_save('')
            smores.run_client_cmd(client_cmd='rxn_ing', file=_file)
            self.do_save('')
            smores.run_med_to_csv(_file, params={})
            smores.run_dict_to_csv('RXNORM', params={})
            #
            # _file = 'claims_ndc.csv'
            # # self.do_load('unc_rxnorm_epic_small.csv')
            # self.do_load(_file)
            # smores.run_rxn_lookup(file=_file)
            # smores.run_rxn_ingredients(file=_file)
            # smores.run_med_to_json(file=_file)

        elif arg == 'hist':
            _file = 'unc_rxnorm_epic_small.csv'
            self.do_load(_file)
            self.do_cui_history('')
            # success, errors = smores.run_rxn_ingredients()
            # if success:
            #     print('Successfully completed ingredient search')
            #     self.set_touched('All', 'rxn_ingredients')
            # smores.run_med_to_csv(['All',''], None)
            # smores.run_med_to_csv(['All', ''], None, 'RXNORM')
    def emptyline(self):
        """Do nothing on an empty input line"""
        pass