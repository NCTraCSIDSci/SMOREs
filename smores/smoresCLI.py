import cmd
import logging
import timeit
import smores.processes as smores
from smores.utility.errors import smores_error
from smores.utility.util import validate_id, resolve_target_path
import smores.utility.util as util

try:
    import sys

    if sys.platform == 'win32':
        from colorama import init

        init()
    from termcolor import colored
except ImportError:
    colored = None

smoresLog = logging.getLogger(__name__)
_OPTIONS_RXNSTATUS = util.OPTIONS_RXNSTATUS


def console_colorize(string, color):
    if colored:
        return colored(string, color)
    else:
        return string


def simple_input(question:str, values:list, index:bool = False):
    _vals = [str(val).upper() for val in values]
    _display_vals = ['[' + str(i) + '] ' + str(values[i]).upper() for i in range(len(values))] if index else _vals
    while True:
        _input = input(console_colorize(question, 'blue') + ' ' + str(_display_vals) + ' : ').upper().strip()
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


class smoresCLI(cmd.Cmd):

    def __init__(self, _meta):
        cmd.Cmd.__init__(self)
        self.__version__ = _meta['version']
        self.__grant__ = _meta['grant']
        self.intro = console_colorize(
            'Welcome to the CAMP-FHIR Synergistic Medication Organizer for RxNorm and Extras!', 'green') \
                     + '\n' + 'Release ' + console_colorize(self.__version__, 'yellow') + ' \n ' \
                                                                                          'Development of this tool is supported by ' + self.__grant__ + ' \n\n ' \
                                                                                                                                                         'Type ' + console_colorize(
            'help', 'red') + ' or ' + console_colorize('?', 'red') + ' to list commands.\n '
        self.inputs = {'loaded': False, 'files': {}, 'count': 0}
        self.prompt = console_colorize('>', 'yellow')
        self.errors = {}
        self.files = self.inputs['files']
        self.cmds = ['rxn_ing', 'rxn_status', 'rxn_lookup', 'rxn_remap', 'rxn_history']
        self.output_cmds = ['fhir', 'csv']
        self.client_run_function = smores.get_run_call

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
            valid_2, _ = self.validate_args(args, 'default')  # Validated will provide the valid ID Type
            valid_1 = args[0] if valid_2 and validate_id(args[0],
                                                         valid_2) else False
            # Ensures the input id is a valid id of the specified type

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
                valid_1 = simple_input("Please choose a command from the list to see errors: ", _current_err)

        elif cmd_call in ['csv', 'remap', 'fhir', 'json']:
            # Format: [File] [Output]
            if not self.inputs['loaded']:
                print("No Files Loaded!\nYou Must load a file containing local medications first")
            else:
                _file_opts = list(self.inputs['files'].keys()) + ['All']
                _dict_opts = list(smores.get_dict_sources()) + ['All']
                _file_or_dict = None

                if cmd_call in ['csv', 'json']:
                    if len(args) == 0:
                        _file_or_dict = simple_input("Do you want results for a File or a constructed Dictionary?",
                                                     ['File', 'Dictionary', 'exit'], True)
                    elif args[0] not in _file_opts and args[0] not in _dict_opts:
                        print('That option was not recognized as a valid source.')
                        _file_or_dict = simple_input("Do you want results for a File or a constructed Dictionary?",
                                                     ['File', 'Dictionary', 'exit'], True)
                    else:
                        valid_1 = args[0]

                    if _file_or_dict.upper() == 'FILE':
                        valid_1 = 'FILE|' + simple_input("Please choose a loaded file", _file_opts, True)
                    elif _file_or_dict.upper() == 'DICTIONARY':
                        valid_1 = 'DICT|' + simple_input("Please choose a code dictionary to output", _dict_opts, True)
                    elif _file_or_dict.upper() == 'EXIT':
                        return None
                else:
                    valid_1 = simple_input("Please choose a loaded file", _file_opts, True)

                if cmd_call in ['csv', 'json', 'fhir']:
                    if len(args) == 2 and len(args[1]) > 0:
                        valid_2 = args[1]
                    else:
                        valid_2 = input("Please provide an output file name:").strip()

                    if len(valid_2) > 0:
                        if "." in valid_2:
                            valid_2, ext = valid_2.split(".")
                    else:
                        valid_2 = ''
                        print('Empty file name provided, using default.')
                else:
                    valid_2 = args[0]
        elif cmd_call == 'file':
            re_use = False
            if self.inputs['loaded'] and len(in_args) == 0:
                print("The following file(s) have already been loaded: \n" + str(self.inputs['files']))
                _load_more = simple_input("Would you like to load an additional file?", ['Y', 'N', 'exit'])
                if _load_more == 'Y':
                    pass
                elif _load_more == 'N':
                    _re_use = simple_input("Would you like to re-use a loaded file?", ['Y', 'N', 'exit'])
                    if _re_use == 'Y':
                        re_use = True
                    else:
                        return False, None
                else:
                    return False, None

            if in_args is not None and len(in_args) > 0:
                valid_1 = in_args
            else:
                valid_1 = input("Please enter the name of the file to load: ") if not re_use else simple_input(
                    'Select the file to be used: ', list(self.inputs['files'].keys()), index=True)

            while True:
                if valid_1 in self.inputs['files']:
                    if not re_use:
                        print("It looks like you've already loaded that file. Please try a different file.")
                        valid_1, valid_2 = input("Please enter the name of the file to load: ")
                    else:
                        break
                elif len(valid_1) == 0:
                    smores_error('#Cx001.7', logger=smoresLog)
                    valid_1, valid_2 = input("Please enter the name of the file to load: ")
                else:
                    break

            if not resolve_target_path(valid_1):
                valid_1, valid_2 = self.validate_args('', 'file')

            elif '.smr' in valid_1:
                if len(self.inputs['files']) > 0:
                    print(
                        'It looks like you are trying to load a session, this will replace the current session and '
                        'all previous work.')
                    _save = simple_input('Do you want to save the current session first?', ['Y', 'N', 'EXIT'])
                    if _save == 'Y':
                        smores.save_session(self.__version__)
                    elif _save == 'EXIT':
                        return False, None
                valid_2 = 'session'
            else:
                valid_2 = 'file'

        smoresLog.debug('Args: {0}, Validated as: {1}'.format(valid_1, valid_2))
        return valid_1, valid_2

    def get_untouched(self, cmd: str = None, force: bool = False):
        """
        Get loaded files that have NOT been used in console command
        :param cmd: Console command issued
        :param force: Force return of all options regardless if ran or not
        :return: list of files
        """
        _r = []
        if cmd is not None:
            for _f, _d in self.inputs['files'].items():
                if not _d[cmd] or force:
                    _r.append(_f)
        else:
            for _f in self.inputs['files'].keys():
                _r.append(_f)
        return _r

    def set_touched(self, file: str, cmd_call: str):
        if file.upper() == 'ALL':
            for _f, _d in self.inputs['files'].items():
                _d[cmd_call] = True
        else:
            print(self.inputs['files'])
            self.inputs['files'][file][cmd_call] = True

    def run_id_call(self, func, cmd_call: str, in_type: str, in_id: str = None):
        if in_type == 'LOCAL' and self.inputs['loaded']:
            if len(self.inputs['files']) > 1:
                file_src = simple_input("Please choose a loaded file ", self.inputs['files'], True)
            else:
                file_src = self.inputs['files'][0]
            _r = func(client_cmd=cmd_call, file=file_src)
        else:
            _r = func(client_cmd=cmd_call, med_id=in_id, med_id_type=in_type)
        return _r

    def run_file_call(self, func, cmd_call: str, file: str = None):
        if file is None:
            file_msg = "Run {0} on all loaded files?".format(cmd_call)
            _run = simple_input(file_msg, ['Y', 'N', 'exit'])
        else:
            _run = 'Y'

        if _run == 'Y':
            _avail = self.get_untouched(cmd_call)
            if len(_avail) == 0:
                print('It looks like you''ve already ran this command for all available files.')
                while True:
                    _run_x = simple_input("Do you want to re-run any/all files?", ['Y', 'N', 'exit'])
                    if _run_x in ['Y', 'N', 'exit']:
                        break
                    else:
                        print('Invalid Option, Please Try Again')
                        continue
                if _run_x == 'Y':
                    _avail = self.get_untouched(cmd_call, True)
                else:
                    return

            if len(_avail) == 1 and file is None:
                file = 'ALL'
            elif file is None:
                _avail.append('ALL')
                _avail.append('exit')
                file = simple_input("Please choose a file to run, or run all:", _avail)

            if file.upper() == 'EXIT':
                return None
            else:
                return func(client_cmd=cmd_call, file=file)

        elif _run == 'N':
            print("Enter '? " + cmd_call + "' for options in running this command")
            return

        elif _run == 'exit':
            return

        else:
            print('Invalid Option')

    def run_cmd(self, arg, cmd_call: str):
        run_func = self.client_run_function()
        if len(arg) > 0:
            validated_cui, cui_type = self.validate_args(arg, cmd_call)  #
            if validated_cui is not None:
                id_result = self.run_id_call(run_func, cui_type, validated_cui, cmd_call)
            else:
                id_result = None

            if id_result is not None:
                print('Command Completed: {0}\nResults for {1} {2}'.format(cmd_call, cui_type, validated_cui))
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
            count_ran, errors, file = self.run_file_call(run_func, cmd_call)
            if count_ran is not None:
                self.set_touched(file, cmd_call)
                print('Command {0} Completed for {1} medications'.format(cmd_call, count_ran))
                return errors

        else:
            print("No Files Loaded!\nYou Must load a file containing local medications first "
                  "or specifiy a specific ID to check")

    def update_errors(self, cmd_call: str, errors: list):
        if cmd_call not in self.errors.keys():
            self.errors[cmd_call] = errors
        else:
            self.errors[cmd_call] += errors
        print_e = console_colorize('{0}'.format(len(errors)), 'red') + " Invalid Code's encountered.\nType '" \
                  + console_colorize('errors {0}'.format(cmd_call), 'red') + "' to see a list of CUI/Code errors\n"
        print(print_e)

    def is_output_cmd(self, output_call: str):
        return True if output_call in self.output_cmds else False

    def do_load(self, arg):
        print('Load')
        """Read in a designated file containing information on local medications
Syntax: load [file_name]
    - [file_name] is optional at entry but will be required.
    Files by default are expected to reside in this programs '/input' folder. If located under
    a different path, it must be fully specified"""
        load_type = None

        def _do_session_load(session: str):
            loaded = smores.load_session(session, self.__version__)
            if len(loaded) > 0:
                self.inputs['loaded'] = True
                self.inputs['files'] = {file: {} for file in loaded}
                for _f in self.inputs['files']:
                    self.inputs['files'][_f] = {_c: False for _c in self.cmds}
                print('Session {0} Load Complete'.format(session))
                print('Note: All SMOREs commands have been reset')
            else:
                print('Failed to Load Files from Session')

        def _do_file_load(file: str):
            tic = timeit.default_timer()
            success, result = smores.load_file(file)
            if success:
                self.inputs['loaded'] = True
                self.inputs['files'][file] = {_c: False for _c in self.cmds}
                self.inputs['count'] += result['records']
                toc = timeit.default_timer()
                elapsed = str(round(toc - tic, 2))
                print('\nElapsed Time: ' + str(elapsed) + ' seconds')
                print("\nSuccess! {0} New Medication(s) Successfully Loaded from File".format(result['records']))
                if result['dups'] > 0:
                    print("{0} Duplicate Local ID's were found. New Information "
                          "was added to previous record.".format(str(result['dups'])))
                return result['errors']
            else:
                if result is not None:
                    smores_error(result, console_p=True)
                else:
                    print('Something went wrong...')
                return

        print("* Note: All input files must reside in the 'input' folder of this program "
              "or contain a fully specified file path (e.g. 'C:\\Users\\Bob\\Desktop\\my_file.csv')")

        if type(arg) is list:
            _file = arg[0]
            if len(arg) == 2:
                load_type = arg[1]
        elif type(arg) is str and len(arg.strip()) > 0:
            _file = arg
        else:
            _file = ''

        if load_type:
            target = _file
        else:
            target, load_type = self.validate_args(_file, 'file')

        if target:
            if load_type == 'file':
                return _do_file_load(target)
            elif load_type == 'session':
                return _do_session_load(target)
            else:
                return
        else:
            return

    def do_workflow(self, arg=None):
        """Define a sequence of commands to be ran """

        def add_steps_to_workflow(curr_flow):
            while True:
                cmd_call = simple_input('Please choose a command to add to the workflow.', cmds, True)
                if cmd_call not in ['DONE', 'EXIT']:
                    if self.is_output_cmd(cmd_call):
                        curr_flow.add_output(cmd_call)
                    else:
                        curr_flow.add_step(cmd_call)
                    cmds.pop(cmds.index(cmd_call))
                elif cmd_call == 'DONE':
                    break
                else:
                    return
            return curr_flow.has_steps()

        def confirm_workflow(curr_flow):
            checks = [('START', 'Start workflow?'), ('ADD', 'Do you want to add more steps?'),
                      ('RESTART', 'Do you want to start over?')]
            curr_flow.draw_steps()
            for check in checks:
                _continue = simple_input(check[1], ['Y', 'N', 'EXIT'])
                if _continue == 'Y':
                    return check[0]
                if _continue == 'EXIT':
                    return 'EXIT'
            return 'INVALID'

        print('Preparing Workflow Wizard...')
        options = sorted(self.cmds + self.output_cmds)
        from smores.workflow import Workflow
        workflow = Workflow(self)
        target, load_type = self.validate_args('', 'file')
        if target:
            _l = True if target in self.inputs['files'].keys() else False
            workflow.add_target(target, load_type, _l)
            print('Please choose the commands you would like to add to the workflow.'
                  '\nCommands will be executed in the order in which they are added.'
                  '\n\nPlease note that some commands have dependencies that must be satisfied. An overview of '
                  'command dependencies is available on the main SMOREs wiki on Github')
            print('\nAvailable Commands for WorkFlow')
            cmds = []
            for i, _o in enumerate(options):
                print('{1}'.format(i, _o))
                cmds.append(_o)
            cmds.append('DONE')
            steps_added = add_steps_to_workflow(workflow)
            while steps_added:
                _run = confirm_workflow(workflow)
                if _run == 'START':
                    break
                elif _run == 'ADD':
                    _ = add_steps_to_workflow(workflow)
                elif _run == 'RESTART':
                    self.do_workflow('')
                else:
                    return
            workflow.run()
            print('Workflow has completed.')
            return

        else:
            print('Workflows currently have to be setup without the file already being loaded.')
            return

    def do_load_count(self, arg=None):
        print(self.inputs['count'])

    def do_rxn_status(self, arg):
        """Look up the active status of RXCUI's from a medication file.
        REQUIRES A FILE TO BE LOADED OR A SPECIFIC RXCUI TO BE PROVIDED"""

        cmd_call = 'rxn_status'
        return self.run_cmd(arg, cmd_call)

    def do_rxn_ingredients(self, arg):
        """Look up the ingredients for a medication through RxNorm
        REQUIRES A FILE TO BE LOADED OR A SPECIFIC RXCUI TO BE PROVIDED"""
        cmd_call = 'rxn_ing'
        return self.run_cmd(arg, cmd_call)

    def do_rxn_lookup(self, arg):
        """Look up current RxNorm CUI for any loaded medication by a linked CUI.
        Will NOT perform name matches which is currently a WiP for a future release."""
        cmd_call = 'rxn_lookup'
        return self.run_cmd(arg, cmd_call)

    def do_rxn_remap(self, arg):
        """Look up the remapped RxCUIs for a medication through RxNorm
        REQUIRES A FILE TO BE LOADED"""
        cmd_call = 'rxn_remap'
        return self.run_cmd(arg, cmd_call)

    def do_rxn_history(self, arg):
        """Looks for any history information for historical CUI's.
        Note: Only supports Retired or Alien  RxCUI"""
        print('RXN History currently only supports obtaining RxNorm History for Retired or Alien RxCUI')
        cmd_call = 'rxn_history'
        return self.run_cmd(arg, cmd_call)

    def do_fhir(self, arg):
        """Converts information pertaining to a medication into FHIR STU3 JSON Format"""
        file, output_file = self.validate_args(arg, 'fhir')
        if file is not None:
            smores.run_med_to_json(file=file, out_file=output_file)
        else:
            print("Enter '? fhir' for options in running this command")
            return

    do_json = do_fhir
    # Simply re-direct 'json' for now
    # TODO Make 'json' a separate output option that is not in FHIR format (ie for dictionaries)
    # """Converts information pertaining to a medication into FHIR STU3 JSON Format.
    # Performs the same actions as executing the 'fhir' command"""

    def do_csv(self, arg):
        target, output_file = self.validate_args(arg, 'csv')
        t_type, file = target.split('|')
        if file is not None:
            params = {}
            csv_constructor = {}
            if t_type == 'FILE':
                cmd_call = self.client_run_function('csv_FILE')
                print('Default output is : LOCAL_ID | LOCAL_NAME | SOURCE | CUI | CUI_TYPE')
                # TODO Add in customization of CSV structure
                params['default'] = 'Y'
                # params['default'] = simple_input("Do you want to save the default output data?", ['Y', 'N'])
                # params['details'] = simple_input("Do you want to save details to medications/codes
                # (e.g. NDC, ingredients, term type, status)?", ['Y', 'N'])
                # params['details'] = simple_input(
                #     "Do you want to save code dictionaries from cache? (e.g. NDC, RXNORM)",
                #     ['Y', 'N'])
                if params['default'] == 'Y':
                    csv_constructor['default'] = ''
            elif t_type == 'DICT':
                cmd_call = self.client_run_function('csv_DICT')
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

    def do_exit(self, arg=None):
        print('Until next time...')
        return True

    def emptyline(self):
        """Do nothing on an empty input line"""
        pass

    def postcmd(self, stop, line):
        split_line = line.split(' ')
        if type(stop) is list and len(stop) > 0:
            self.update_errors(split_line[0], stop)
