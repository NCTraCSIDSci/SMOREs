# Python Lib Modules
import time, os, math, csv, re, logging
from pathlib import Path
from datetime import datetime
import json
# Community Modules
import pandas as pd
from tqdm import tqdm, trange
# SMOREs Internal Imports
import smores.medication as m
from smores import medicationdictionary as md
from smores.medkit import MedKit
from smores.utility.errors import smores_error
from typing import Union
import smores.utility.util as util
from smores.crosswalk import get_crosswalk

smoresLog = logging.getLogger(__name__)

def line_read (medkit, input, last_id=None, skip1=True):
    _n, line = input
    if _n == 0 and skip1:
        return False, False, None, None
    else:
        try:
            config_i_keys = util.read_config_value('INFILE_KEYS')
            i_local_key = config_i_keys['local_id_col_id']
            i_code_key = config_i_keys['code_col_id']
            i_code_type_key = config_i_keys['code_type_col_id']
            i_name_key = config_i_keys['local_name_col_id']
            i_code_name = config_i_keys['code_name_col_id']
        except KeyError as e:
            print(e)
            return None, "#Cx001.6", None, None

        is_dup = False
        has_err = {}
        cui_type = None
        local_id = line[i_local_key]
        if local_id == last_id or m.med_exists(local_id, medkit.file_name):
            temp_med = m.get_med_by_id(local_id, medkit.file_name)
            is_dup = True
        else:
            temp_med = m.LocalMed(input_key=local_id, source=medkit.file_name)

        if len(line[i_code_key]) != 0:
            cui_type = line[i_code_type_key].upper()
            cui_type = 'RXNORM' if cui_type == 'RXCUI' else cui_type # Prevent automatic fail incase RXCUI instead of RXNORM
            if util.validate_id(line[i_code_key], cui_type):
                # Support for inclusion of local name for local code id's
                if cui_type == 'LOCAL' and not temp_med.isNameSet():
                    temp_med.set_name(line[i_code_name])

                elif cui_type in util.OPTIONS_CUI_TYPES:
                    if i_code_name in line.keys() and len(line[i_code_name]) > 0:
                        _e = temp_med.add_cui(line[i_code_key], cui_type, line[i_code_name])
                    else:
                        _e = temp_med.add_cui(line[i_code_key], cui_type)
                    if _e > 0:
                        smores_error('#Ax000.1', line[i_local_key])
                        has_err[line[i_code_key]] = "#Ax000.1"

        else:
            smores_error('#Ax000.3', line[i_local_key])
            has_err[line[i_code_key]] = "#Ax000.3"

        if i_name_key in line.keys() and len(line[i_name_key]) > 0:
            clean_rx = r'\\["n]'
            temp_med.set_name(re.sub(clean_rx, '', line[i_name_key]))

        return local_id, is_dup, has_err, cui_type


def load_file(input_file:str):
    def process_file(curr_medkit):
        try:
            c_records = 0
            c_dup = 0
            errors = []
            _last = None
            with open(curr_medkit.path, 'r') as file_handle:
                reader = csv.DictReader(file_handle, delimiter=",", skipinitialspace=True)

                for line in tqdm(enumerate(reader), total=curr_medkit.file_lines, desc="Progress", unit=' rows'):
                    _med, _dup, _err, _type = line_read(curr_medkit, line, _last, False)
                    if _med is None:
                        smores_error(_err)
                    elif not _med:
                        pass
                    else:
                        if not _dup:
                            curr_medkit.add_med(_med, _type)
                            c_records += 1
                            _last = _med
                        if _dup:
                            c_dup += 1
                        if len(_err) > 0:
                            errors.append(_err)

        except FileNotFoundError:
            return False, "#Cx001.1"
        except PermissionError:
            return False, "#Cx001.2"
        except BaseException as e:
            print(e)
            return False, None
        else:
            time.sleep(.01) # Clean exit of tqdm
            return {'records': c_records, 'dups': c_dup, 'errors': errors, 'file': curr_medkit.file_name}

    if ':\\' in input_file:
        input_file_path = Path(input_file).resolve()
    elif 'tests/' in input_file:
        input_file_path = Path("..", 'tests', input_file).resolve()
    else:
        input_file_path = Path("..", 'input', input_file).resolve()

    try:
        if input_file_path.exists():
            medkit = MedKit(input_file_path)
            file_stat = process_file(medkit)
            medkit.set_record_count(file_stat['records'])
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        return False, "#Cx001.1"
    except PermissionError:
        return False, '#Cx001.2'
    except OSError:
        raise OSError('#Cx001.6')
    except BaseException as e:
        print(e)
        return False, None
    else:
        return True, file_stat


def write_file(output_file=None, data=None, iter:int=0, ext:str=None):
    _default = 'SMORES_output_'+time.strftime("%Y%m%d-%H%M%S")
    if data is None:
        smores_error('#Cx001.5')
        return False, 'ERROR'

    else:
        _write_path = '../output/'
        _ext = 'txt' if ext is None else ext
        if output_file is None or len(output_file) == 0:
            _base = _default
        else:
            if "." in output_file:
                _base, _ext = output_file.split(".")
                if 'SMORES_DEFAULT' in _base:
                    _base = output_file[:output_file.index('-')] + _default if '-' in output_file else _default
            else:
                _base = output_file

        if iter > 0:
            _base = _base + "_" + str(iter)
        _write_file_name = _write_path + _base + "." + _ext
        try:
            if os.path.exists(_write_file_name):
                append_write = 'w'
            else:
                append_write = 'a'

            _head_wr = True
            if _ext in ['csv', 'txt']:
                for row in tqdm(data, total=len(data), unit='rows',
                                desc='Writing To File {0} '.format(_write_file_name), position=iter):
                    has_list = False
                    for _v in list(row.values()):
                        if type(_v) is list:
                            has_list = True
                            break
                        elif type(_v) is dict:
                            for _v2 in list(_v.values()):
                                if type(_v2) is list:
                                    has_list = True
                                    break
                    if has_list:
                        _df = pd.DataFrame.from_dict(row)
                    else:
                        _df = pd.DataFrame(row, index=[0])
                    _df.to_csv(_write_file_name, mode=append_write, header=_head_wr, index=False)
                    if _head_wr and _ext != 'json':
                        _head_wr = False
                    append_write = 'a'
            else:
                with open(_write_file_name, append_write) as open_file:
                    open_file.write(json.dumps(data, ensure_ascii=False) if type(data) is dict else str(data))
                open_file.close()

            return True

        except FileNotFoundError:
            smores_error('#Cx001.4', output_file)
            return False, "#Cx001.4"
        except PermissionError:
            smores_error('#Cx001.2', output_file)
            return False, '#Cx001.2'


def process_event(src:Union[MedKit, str], func, display:str, event_restrict=None, args=None):
    '''

    :param src:
    :param func:
    :param event_restrict: Must be a function call
    :return:
    '''
    _count = 0
    _num_valid = 0
    _error_codes = []
    if event_restrict is not None:
        try:
            med_val_list = event_restrict().values()
        except TypeError:
            return False, None
    else:
        _md = src.m_dict if type(src) is MedKit else md.get_med_dict_by_src(src)
        med_val_list = list(_md.med_list.values())

    results = {}
    pbar = tqdm(total=len(med_val_list), desc=display + ' Processing', position=0)
    for _val in med_val_list:
        _v, _res = func(_val) if args is None else func(_val, args)
        if _v:
            _num_valid += 1
            results[_val.cui] = _res
        pbar.update(1)
    #pbar.close()

    #pbar = tqdm(total=_num_valid, desc='Finalizing Results', position=0)
    pbar.set_description('Finalizing Results')
    pbar.refresh()
    for med_id, _ans in results.items():
        if _ans is None:
            _error_codes.append('Med:' + str(med_id))
            smores_error('#Bx001.3', 'Med:' + str(med_id))
        elif type(_ans) is dict:
            for _cui, _cui_ans in _ans.items():
                if _cui_ans is None:
                    _error_codes.append(_cui)
                    smores_error('#Bx001.3', 'RXC: [' + str(_cui) + ']')
        else:
            pass
        _count += 1
        #pbar.update(1)
    pbar.set_description('Complete')
    pbar.close()
    time.sleep(.01)
    if _count > 0:
        return _count, _error_codes
    else:
        smores_error('#Cx004.2')
        return False, None


def get_run_call(client_cmd:str='default', opt:str=None):
    client_cmds = {
        'default': run_client_cmd,
        'csv': run_med_to_csv,
        'csv_FILE': run_med_to_csv,
        'csv_DICT': run_dict_to_csv,
        'fhir': run_med_to_json
    }
    try:
        _cmd = client_cmds[client_cmd] if opt is None else client_cmds[client_cmd][opt]
    except KeyError:
        return client_cmds['default']
    else:
        return _cmd


def run_client_cmd(client_cmd:str, med_id:str=None, med_id_type:str=None, file:str=None, args=None):
    """

    :param client_cmd:
    :param med_id:
    :param med_id_type:
    :param file:
    :param opts:
    :return:
    """
    client_cmds = {'rxn_status': {'func': get_rxn_status, 'display': 'RxNorm Status', 'restrict': None},
                   'rxn_ing': {'func': get_rxn_ingredients, 'display': 'RxNorm Ingredients', 'restrict': None},
                   'rxn_lookup': {'func': get_rxn_lookup, 'display': 'RxNorm Lookup', 'restrict': None},
                   'rxn_remap': {'func': get_rxn_remap, 'display': 'Remapped RxNorm', 'restrict': None},
                   'rxn_history': {'func': get_rxn_history,
                                   'display': 'Retired RxNorm History',
                                   'restrict': m.RxCUI.get_historical_list},
                   'code_lookup': {'func': get_code_lookup, 'display': 'Code Lookup', 'restrict': None}
                   # 'rxn_search': get_rxn_search
                   }
    try:
        this_cmd = client_cmds[client_cmd]['func']
        this_display = client_cmds[client_cmd]['display']
        this_restriction = client_cmds[client_cmd]['restrict']
        this_cmd_requires = client_cmds[client_cmd]['requires'] if 'requires' in client_cmds[client_cmd].keys() else None
    except KeyError:
        smores_error('TBD', client_cmd)
        return

    if file is not None:
        # If a command has a requirement in order to process without complete failure, check that it has passed
        if this_cmd_requires:
            pass_requires, error = get_cmd_requirements(client_cmd, [file, args])
            if not pass_requires:
                print('Command {0} does not meet the requirements needed to execute the command'.format(client_cmd))
                if error is not None:
                    print('   Requirements: {0} \n'.format(error))
                return 0, [], file
        success_count, errors = 0, []
        if file == 'ALL':
            medkits = MedKit.get_medkit()
            num_kits = len(medkits)
            if num_kits > 1:
                kits_prog = tqdm(total=num_kits, unit='Files')
            for id, kit in medkits.items():
                _c, _e = process_event(kit, this_cmd, this_display, this_restriction, args)
                success_count += _c
                if _e is not None and len(_e) > 0:
                    errors = errors + _e if type(_e) is list else errors.append(_e)
                if num_kits > 1:
                    kits_prog.update(1)

        else:
            #elif MedKit.src_is_medkit(file):
            medkit = MedKit.get_medkit(file) if not isinstance(file, MedKit) and MedKit.src_is_medkit(file)else file
            success_count, errors = process_event(medkit, this_cmd, this_display, this_restriction, args)

        return success_count, errors, file

    elif med_id is not None and med_id_type is not None:
        med = m.get_med_by_id(med_id, med_id_type)
        success, error = this_cmd(med_id=med)
        return success, error, med_id

    else:
        smores_error('TBD', client_cmd)
        return 0, [], med_id


def get_code_lookup(medObj:Union[m.Medication, m.NDC, m.RxCUI], target:str):
    """
    Performs a crosswalk of an input medication's cui to another codeset
    :param medObj: A Medication object or sub type to be crosswalked
    :param target: the target codeset to search for mappings to
    :return: True if results, False if None
    """
    source = medObj.get_property('source')
    crosswalk = get_crosswalk(source, target)
    cross_r = crosswalk.run_crosswalk(medObj.cui) # hold results from the lookup of target code set
    if cross_r is not None and len(cross_r) > 0:
        smoresLog.debug('Crosswalk Results for {0} to {1}'.format(medObj.cui, target))
        for _res in cross_r:
            medObj.add_linked_cui(_res, target)
            smoresLog.debug('{0}.{1}'.format(target, _res))
        return True, _res
    else:
        return False, None


def get_rxn_lookup(medObj:Union[m.Medication, m.LocalMed, m.NDC]):
    """
    DEPRECATED
    Lookup RxCUI for codes from a different source
    :param medObj:
    :return:
    """
    if isinstance(medObj, m.RxCUI):
        smores_error('TBD')
        return 0, []

    success_count, errors = 0, []
    non_rxc_dict = medObj.get_cui_all(omit=['PARENT', 'RXNORM'], inc_obj=True)
    _e = {}
    if len(non_rxc_dict) > 0:
        for src in non_rxc_dict:
            _src_e = []
            _src_s = 0
            for medC, medO in non_rxc_dict[src].items():
                rxc_l = medO.get_linked_cui('RXNORM')
                for _o in rxc_l:
                    if _o is None:
                        _src_e.append(medC)
                    else:
                        _src_s += 1
                        medObj.add_cui(_o)
            success_count += 1 if _src_s > 0 else 0
            if len(_src_e) > 0:
                _e[src] = _src_e
    if len(_e) > 0:
        errors = _e
    return success_count, errors


def get_rxn_status(medObj:Union[m.Medication, m.LocalMed, m.RxCUI], api:str='RXNAV'):
    '''
    :param med_id: A string representing a medication or a Medication object
    :param med_id_type: Value representing the type/source of the med_id
    :param api: API to call for the rxn_status - Default RXNAV (UMLS may be a secondary option in future)
    :return:
    '''
    # smoresLog.debug('MED_ID: {0} - Source: {1}'.format(med_id, med_id_type))
    if api == 'RXNAV':
        if isinstance(medObj, m.RxCUI):
            if medObj.valid:
                return True, {medObj.cui: medObj.status}
            else:
                return False, {medObj.cui: None}
        else:
            rx_md = medObj.get_dict('RXNORM')
            if rx_md is not None:
                rxc_l = rx_md.get_med_list(inc_obj=True)
                rxc_status = {}
                for cui, RxCUI in rxc_l.items():
                    rxc_status[cui] = RxCUI.get_status()
                return True, rxc_status
            else:
                return False, None
    else:
        smores_error('#Cx004.2', 'Unknown Target')
        return False, None


def get_rxn_ingredients(medObj:Union[m.Medication, m.LocalMed, m.RxCUI], api:str='RXNAV'):
    """
    Return the RxNorm ingredients for a given Medication Object
    :param medObj:
    :param api:
    :return: Valid Input (bool) ; type(Dict) , {RxCUI: Ingredient List}
    """
    if api == 'RXNAV':
        if isinstance(medObj, m.RxCUI):
            if medObj.valid:
                return {medObj.cui: medObj.get_ingredients()}
            else:
                return False, {medObj.cui: None}
        else:
            return True, {medObj.cui: medObj.get_ingredients()}
    else:
        smores_error('#Cx004.2', 'Unknown Target')
        return False, None


def get_rxn_remap(medObj:Union[m.Medication, m.LocalMed, m.RxCUI], api:str='RXNAV'):
    if api == 'RXNAV':
        if isinstance(medObj, m.RxCUI):
            if medObj.valid:
                return {medObj.cui: True}
            elif not medObj.has_remaps and medObj.has_remaps is not None:
                return {medObj.cui: medObj.get_linked_cui('remap')}
        else:
            rx_md = medObj.get_dict('RXNORM')
            if rx_md is not None:
                rxc_l = rx_md.get_med_list(inc_obj=True)
                rxc_remap = {}
                for cui, RxCUI in rxc_l.items():
                    if RxCUI.has_remaps:
                        rxc_remap[cui] = RxCUI.get_linked_cui('remap')
                for re_cui in rxc_remap.values():
                    medObj.add_cui(re_cui)
                return True, rxc_remap
            else:
                return False, None
    else:
        smores_error('#Cx004.2', 'Unknown Target')
        return False, None


def get_rxn_history(rxcObj:m.RxCUI, api:str='RXNAV'):
    '''
    Barebones - Runs history of all medications currently loaded
    # TODO Allow for specific targeting of med_ids
    :param med_id:
    :param med_id_type:
    :param file:
    :return:
    '''
    if api == 'RXNAV':
        success = rxcObj.get_linked_cui('history')
    if success:
        return True, success
    else:
        return False, None


def run_med_to_json(med_id=None, med_id_type:str=None, file:str=None,
                    out_file:str=None):
    '''

    :param med_id:
    :param med_id_type:
    :param file:
    :param out_file:
    :param incr:
    :return:
    '''
    smoresLog.debug('Preparing to generate FHIR JSON Files')

    def get_bundle_json(in_dict:md.MedicationDictionary, json_file:str):
        incr = int(util.read_config_value('OUTPUT_CONF')['file_size_max'])
        _total = in_dict.get_med_count()
        _iters = int(math.ceil(_total/incr)) if incr is not None else 1
        _med_list = list(in_dict.med_list.values())
        fhir_construct = {'resourceType': 'Bundle', 'date': datetime.today().strftime('%Y-%m-%d %H:%M:%S%z'), 'total':0, 'entry':[]}
        if _iters > 1:
            _count = 0
            print('Medications will be saved across {0} files.'.format(_iters))
            for i in trange(_iters, desc='File Number', position=0):
                bundle = fhir_construct.copy()
                list_end = _count + incr if (_count + incr) < _total else _total
                _b = [med.get_fhir() for med in _med_list[_count:list_end]]
                bundle['entry'] = _b
                bundle['total'] = list_end - _count
                write_file(output_file=json_file, iter=i+1, data=bundle, ext='json')
                _count += incr
        else:
            bundle = fhir_construct
            for med in _med_list:
                 bundle['entry'].append(med.get_fhir())
                 bundle['total'] += 1
            write_file(output_file=json_file, data=fhir_construct, ext='json')
        return

    def get_single_json(object:m.Medication):
        return object.get_fhir()

    if file is not None:
        kits = MedKit.get_medkit(file)
        if type(kits) is dict:
            i=1
            for file, kit in kits.items():
                _file, _ = process_filename(out_file=out_file, info_type=kit.file_name.split('.')[0])
                get_bundle_json(kit.m_dict, _file)
                i += 1
        else:
            _file, _ = process_filename(out_file=out_file, info_type=kits.file_name.split('.')[0])
            get_bundle_json(kits.m_dict, _file)

    elif med_id is not None and med_id_type is not None:
        med_o = m.get_med_by_id(med_id, file)
        med_o.add_json(get_single_json(med_o))
    else:
        smores_error('#Kx001.2')
    return


def run_med_to_csv(file:str=None, out_file:str=None, params:dict=None):
    '''
    Only supports outputing bundles, not individual meds
    :param file: the target input file to be output to CSV, or ALL
    :param out_file: basename to be used for file outputs, can be None: default name will be used
    :param params: Customization parameters for the CSV output
        Possible Parameters: codes (codeset to output), ing (include ingredients)
    :param incr: Number of medications to be saved per file (not rows)
    :return:
    '''
    smoresLog.debug('Preparing to generate CSV')
    incr = int(util.read_config_value('OUTPUT_CONF')['file_size_max'])
    # csv_files = {}
    # csv_outputs = params.keys() if params is not None else ''
    # if 'detail' in csv_outputs:
    #     for _d in params['detail'].values():
    #         base_filename, ext = process_filename(_d['type'])
    #         csv_files[_d] = {'file': base_filename, 'ext': ext, 'detail': _d}

    if file is not None:
        kits = MedKit.get_medkit(file)
        if type(kits) is dict:
            i=1
            for file, kit in kits.items():
                _file, ext = process_filename(out_file=out_file, info_type=kit.file_name.split('.')[0])
                save_csv_bundle(kit.m_dict, _file, incr=incr, ext=ext, csv_detail=params)
                i += 1
        else:
            _file, ext = process_filename(out_file=out_file, info_type=kits.file_name.split('.')[0])
            save_csv_bundle(kits.m_dict, _file, incr=incr, ext=ext, csv_detail=params)

    else:
        smores_error('#Kx001.2')
    return


def run_dict_to_csv(src_dict:str, out_file:str=None, params=None):
    """
    Retrieves the corresponding MedicationDictionary for an input src and saves to CSV
    :param src_dict: Name of the src to be saved. Will identify the medication "bundle" to be saved
    :param out_file: output filename specified by the user. Def None results in default name generated
    :param params: Additional output parameters to be applied in building the csv
    :return: Function call to save the bundle of medications
    """
    incr = int(util.read_config_value('OUTPUT_CONF')['file_size_max'])
    dict_to_save = md.get_med_dict_by_src(src_dict)
    _file, ext = process_filename(out_file=out_file, info_type=src_dict)
    return save_csv_bundle(dict_to_save, _file, incr, params, ext=ext)


def save_csv_bundle(in_dict:md.MedicationDictionary, out_file:str, incr:int, csv_detail=None, **kwargs):
    """
    Takes an input MedicationDictionary object and retrieves the output print format for the included medication objects
    :param in_dict: Input MedicationDictionary to be saved
    :param out_file: output filename specified by the user. Def None results in default name generated
    :param incr: Number of medications to be included in each file. Prevent rows for a single medication from being
        spread across multiple files
    :param csv_detail: Additional specifications regarding the format of the output CSV
    :return:
    """
    _total = in_dict.get_med_count()
    _iters = int(math.ceil(_total / incr)) if incr is not None else 1
    _med_list = list(in_dict.med_list.values())
    if csv_detail['default']:
        # Default save format is to retrieve all cui's from the RxNorm code set
        _d = {'cui': {'src': 'RXNORM', 'ing': True}}
    else:
        csv_detail.pop('default', None)
        _d = {csv_detail.lower(): ''} if type(csv_detail) is not dict else csv_detail
        out_file = str(list(_d.keys())[0]) + '-' + out_file if len(_d.keys()) > 1 else out_file
    if _iters > 1:
        _count = 0
        print('Records will be saved across {0} files.'.format(_iters))
        with trange(_iters, position=0) as prog:
            prog.set_description('File Save Progress')
            for i in prog:
                list_end = _count + incr if (_count + incr) < _total else _total
                bundle = format_to_print(_med_list[_count:list_end], 'CSV', _d)
                write_file(output_file=out_file, iter=i+1, data=bundle, ext='csv')
                _count = list_end
    else:
        bundle = format_to_print(_med_list, 'CSV', _d)
        write_file(output_file=out_file, data=bundle, ext='csv')
    return


def save_session(SMOREs_version:str):
    import pickle
    print('Saving Session...')
    _write_path = Path('../output/')
    file_name, ext = process_filename(info_type='session', ext='smr')
    _file = file_name + '.' + ext
    output_path = _write_path.joinpath(_file)
    try:
        filehandler = open(output_path, 'wb')
        medKits = MedKit.get_medkit()
        medDicts = md.get_available_med_dict()
        session = {'MedKit': medKits, 'MedicationDictionary': medDicts, 'version': SMOREs_version, 'date': datetime.now()}
        pickle.dump(session, filehandler)
        if output_path.resolve() and output_path.stat().st_size > 0:
            print('Session Saved: {0}'.format(_file))
    except:
        print('UNKNOWN ERROR - save_session()')


def load_session(session:str, SMOREs_version:str):
    import pickle
    print('Loading Session...')
    _load_path = Path('../input/')
    input_file = _load_path.joinpath(session)
    filehandler = open(input_file, 'rb')
    try:
        session = pickle.load(filehandler)
        if session['version'] != SMOREs_version:
            print('\nWarning: Version of data loaded from previous session is not the same. Some functionality may not be supported.')
            print('Current: {0}\nLoaded: {1} \n'.format(SMOREs_version, session['version']))
        md_e = md.MedicationDictionary.load_session(session['MedicationDictionary'])
        mk_e = MedKit.load_session(session['MedKit'])
        if len(md_e) == 0 and len(mk_e) == 0:
            print('Success!')
        else:
            # TODO Smores Error Encode
            print('Errors encountered while loading session')
            if len(md_e) > 0:
                print('Medication Dictionaries with Errors: {0}'.format(md_e))
            if len(mk_e) > 0:
                print('Files with Errors: {0}'.format(mk_e))
        if 'date' in session.keys():
            print('\nSession Date: {0}'.format(session['date'].strftime("%Y-%m-%d %H:%M")))
        return list(MedKit.get_medkit().keys())
    except FileNotFoundError:
        smores_error('#Cx001.1')
        return None
    except PermissionError:
        smores_error('#Cx001.2')
        return None


def get_cmd_requirements(cmd:str, input:list):
    _file = input[0]
    _opts = input[1]
    if cmd == 'code_lookup':

        file_cui_types = get_file_cui_types(input)
        if file_cui_types is not None:
            if any(i in ['NDC'] for i in file_cui_types):
                return True, None
            else:
                return False, 'There are no valid CUI types that can be searched for rxnorm codes.'
        else:
            return None
    else:
        return True


def get_dict_sources(codes_only=False):
    md_keys = list(md.MedicationDictionary.get_src_list().keys())
    return md_keys if not codes_only else list(set(md_keys) & set(util.OPTIONS_CUI_TYPES))


def get_file_cui_types(_file:str):
    if MedKit.src_is_medkit(_file):
        _mks = MedKit.get_medkit(_file)
        if type(_mks) is dict:
            cui_types = []
            for _mk in _mks.values():
                for _ct in _mk.get_cui_types():
                    if _ct not in cui_types:
                        cui_types.append(_ct)
            return cui_types
        else:
            return _mks.get_cui_types()
    elif _file == 'ALL':
        _mks = MedKit.get_medkit()
    else:
        return None


def process_filename(out_file:str=None, info_type:str='default', ext:str='csv'):
    if out_file is None or out_file == '':
        affix = time.strftime("%Y%m%d-%H%M%S")
        base_file = 'SMORES_{0}_{1}'.format(info_type, affix)
    else:
        if "." in out_file:
            base_file, ext = out_file.split(".")
        else:
            base_file = out_file
    return base_file, ext


def format_to_print(object, f_type=None, f_mod=None):
    smoresLog.debug('IN_OBJ: {0}'.format(object))
    if type(object) is list:
        _formatted = []
        for item in object:
            _formatted.append(format_to_print(item, f_type, f_mod))
    elif type(object) is dict:
        _formatted = []
        for key, value in object.items():
            _formatted.append(format_to_print(value, f_type, f_mod))
    elif type(object) is str:
        _formatted = object
    else:
        _formatted = object.print_formats(p_type=f_type, p_mod=f_mod)
    smoresLog.debug(_formatted)
    return _formatted

