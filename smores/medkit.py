import logging
from smores import medication as m
from smores import fhir_templates as tmpl
from smores import medicationdictionary as md
from smores.errors import smores_error
import rxnorm.rxnorm as rxnorm
import csv
from pathlib import Path
from multiprocessing import Process, Manager, cpu_count, Queue, Value
import queue
from multiprocessing.pool import Pool
from threading import Thread, activeCount
import time
import itertools
import os
import math
import sys
import mmap
import ntpath
from tqdm import tqdm, trange

smoresLog = logging.getLogger(__name__)


def show_prog(q, total, unit):
    prog = tqdm(total=total, desc="Progress", unit=unit)
    while 1:
        try:
            to_add = q.get(timeout=1)
            prog.n += to_add
            prog.update(0)
            if prog.n >= total:
                break
        except:
            continue


def add_meds(q, src):
    med_dict = md.get_med_dict_by_src(src)
    while True:
        try:
            item = q.get()
            if item == 'KILL_PROC' and item is not None:
                break
            else:
                item = q.get()
                med_dict.add_med_with_id(item[0], item[1])
        except:
            continue


def process_line(medkit, work_q, prog_q, curr_thd, track_q, out_q, id=0, delim=','):
    smoresLog = logging.getLogger(__name__ + '.' + str(id))
    head = medkit.headers
    md = medkit.file_name
    i_local_key = head['LOCAL_ID']
    i_code_key = head['CODE']
    i_code_type_key = head['CODE_TYPE']
    i_name_key = head['NAME']
    delimiter = delim
    trackers = {'records': 0, 'dups': 0, 'errors': []}
    i_last = None
    while True:
        item = work_q.get()
        line_no, _line = item
        if _line is not None and line_no > 0:
            line = _line.split(delimiter)
            smoresLog.debug("Current IDs in Threads: {0}".format(curr_thd))
            local_id = line[i_local_key]
            # Need to prevent multi processing of the same Local Id Across threads
            if local_id not in curr_thd and local_id != i_last:
                curr_thd.append(local_id)
                if m.med_exists(local_id, md):
                    # print('Dup')
                    temp_med = m.get_med_by_id(local_id, md)
                    trackers['dups'] += 1
                else:
                    temp_med = m.Medication(md, local_id)
                    trackers['records'] += 1
                    i_last = local_id

                if len(line[i_code_key]) != 0:
                    if line[i_code_type_key].upper() in ['RXCUI', 'RXNORM']:
                        smoresLog.debug('Code Type Check: RXCUI')
                        rxcui = rxnorm.get_rxcui(line[i_code_key])
                        if rxcui.valid:
                            temp_med.add_cui(rxcui, 'RXNORM')
                            smoresLog.debug('RXCUI:' + rxcui.cui)
                        else:
                            _error = smores_error('#Ax000.1')
                            smoresLog.error(str(_error) + ' ' + str(line[i_code_key]) + '\n')
                            trackers['errors'].append(line[i_code_key])

                    elif line[i_code_type_key].upper() == 'NDC':
                        smoresLog.debug('Code Type Check: NDC')
                        # TODO Do Stuff for NDC Code Inputs
                        pass
                else:
                    _error = smores_error('#Ax000.3')
                    smoresLog.error(str(_error) + ' ' + str(line[i_local_key]) + '\n')
                    trackers['errors'].append(line[i_code_key])

                if len(line[i_name_key]) > 0:
                    smoresLog.debug('Name Check')
                    temp_med.set_name(line[i_name_key])
                prog_q.put(1)
                out_q.put([temp_med, local_id])
                work_q.task_done()
                curr_thd.remove(local_id)
            else:
                smoresLog.warning('Stacked Rows Found, re-queue {0}'.format(item))
                work_q.task_done()
                work_q.put(item)
        else:
            break
    track_q.put(trackers)
    return


def load_file(input_file):

    def process_file(medkit, workers):
        _num_lines = medkit.file_lines-1
        manager = Manager()
        prog_q = manager.Queue()
        work_q = manager.Queue()
        current = manager.list()
        results = manager.Queue()
        dict_q = manager.Queue()

        pool = []
        with open(medkit.path, 'r') as file_handle:
            progress = Process(target=show_prog, args=(prog_q, _num_lines, ' Rows'))
            progress.start()
            med_process = Process(target=add_meds, args=(dict_q, medkit.file_name))
            med_process.start()

            for i in range(workers):
                _p = Thread(target=process_line, args=(medkit, work_q, prog_q, current, results, dict_q, i))
                _p.start()
                pool.append(_p)
                # time.sleep(.02)

            iters = itertools.chain(file_handle, (None,)*workers)
            for line in enumerate(iters):
                work_q.put(line)

            c_records = 0
            c_dup = 0
            errors = []

            time.sleep(1)
            for _p in pool:
                _p.join()

            while not results.empty():
                _r = results.get()
                c_records += _r['records']
                c_dup += _r['dups']
                errors += _r['errors']

            return pool, {'records': c_records, 'dups': c_dup, 'errors': errors}


    if ':\\' in input_file:
        input_file_path = Path(input_file).resolve()
    elif 'tests/' in input_file:
        input_file_path = Path("..", 'tests', input_file).resolve()
    else:
        input_file_path = Path("..", 'input', input_file).resolve()

    try:
        medkit = MedKit(input_file_path)
        _num_workers = math.ceil(cpu_count())
        pool, counters = process_file(medkit, _num_workers)
        medkit.set_record_count(counters['records'])
        print('Counters: {0}'.format(counters))
    except FileNotFoundError:
        smores_error('#Cx001.1')
        return False, "#Cx001.1"
    except PermissionError:
        smores_error('#Cx001.2')
        return False, '#Cx001.2'
    else:
        return True, counters
        # return True, {'records': record_counter, 'dups': dup_counter, 'errors': _error_codes}


def write_file(output_file=None, data=None, iter=None):
    if data is None:
        smores_error('#Cx001.5')
        return False, 'ERROR'

    else:
        smoresLog.debug('Preparing to write file...')
        _write_path = '../output/'
        if output_file is None:
            output_file = 'SMORES_output_'+time.strftime("%Y%m%d-%H%M%S")+'.txt'

        if iter is not None:
            output_file = str(iter) + '_' + output_file

        _write_file_name = _write_path + output_file

        try:
            if os.path.exists(_write_file_name):
                append_write = 'w'
            else:
                append_write = 'a'
            with open(_write_file_name, append_write) as open_file:
                open_file.write(data)
            open_file.close()
            return True

        except FileNotFoundError:
            smores_error('#Cx001.4', output_file)
            return False, "#Cx001.4"
        except PermissionError:
            smores_error('#Cx001.2', output_file)
            return False, '#Cx001.2'

def run_status(source, med_id=None):
    _run_md = md.get_med_dict_by_src(source)
    _count = 0
    _total = 1 if med_id is not None else _run_md.get_med_count()
    _error_codes = []
    progress = tqdm(total=_total)
    try:
        for key, med_o in _run_md.med_list.items():
            _status = get_status(med_o, source)
            if _status is None:
                _error_codes.append('Med:'+str(med_o.get_local_id))
                smores_error('#Bx001.3', 'RXC: [' + str(rxc) + ']')
            elif None in list(_status.values()):
                for rxc, status in _status.iteritems():
                    if status is None:
                        _error_codes.append(rxc)
                        smores_error('#Bx001.3', 'RXC: [' + str(rxc) + ']')
            _count += 1
            progress.update(1)
        if _count > 0:
            return True, {'errors': _error_codes} if len(_error_codes) > 0 else None

    except [ValueError, KeyError]:
        smores_error('#Cx004.2')
        return False, None


def get_status(med_id, source):
    smoresLog.debug('MED_ID: ' + str(med_id) + '  -  Source: ' + source)
    if source == 'RXNORM':
        rxcui = rxnorm.get_rxcui(med_id) if type(med_id) is not rxnorm.RxCUI else med_id
        if rxcui.valid:
            return rxcui.status
        else:
            return None
    elif source == 'LOCAL':
        rxc_status = {}
        med = m.get_med_by_id(med_id, source) if type(med_id) is not m.Medication else med_id
        rxc_s = med.get_cui_by_src('RXNORM')
        smoresLog.debug(rxc_s)
        for cui in rxc_s:
            rxcui = rxnorm.get_rxcui(cui)
            rxc_status[cui] = rxcui.get_status()
        return rxc_status
    else:
        return None


def run_ingredients(source, med_id=None):
    _run_md = md.get_med_dict_by_src(source)
    _count = 0
    _error_codes = []
    _total = 1 if med_id is not None else _run_md.get_med_count()
    _static_list = _run_md.med_list.copy()
    smoresLog.debug(_static_list)
    progress = tqdm(total=_total)
    try:
        for key, med_o in _static_list.items():
            smoresLog.debug('Load ingredients for Med: ' + str(key))
            _loaded = load_ingredients(med_o, source, ret_count=True)
            smoresLog.debug(str(key) + ' Medication loaded ' + str(_loaded) + ' ingredients.')
            _count += 1 if _loaded is not None else 0
            if _loaded is None:
                _error_codes.append(key)
                smores_error('#Bx002.1')
            progress.update(1)
        print('\nTotal Ingredients Processed: '+str(_total))
        if len(_error_codes) != 0:
            smores_error('#Kx002.2', len(_error_codes))
            return True, {'errors': _error_codes}
        else:
            return True, None

    except [ValueError, KeyError]:
        smores_error('#Cx004.1')
        return False, None


def load_ingredients(med_id, source, print_ing=False, ret_count=False):
    _obj = None
    if source == 'RXNORM':
        rxcui = rxnorm.get_rxcui(med_id) if type(med_id) is not rxnorm.RxCUI else med_id
        if rxcui.valid:
            _obj = rxcui
        else:
            smores_error('#Ax000.1')
    elif source == 'LOCAL':
        _obj = m.get_med_by_id(med_id, source) if type(med_id) is not m.Medication else med_id
    try:
        logging.debug(_obj)
        if _obj.find_ingredients():
            if print_ing:
                return _obj
            else:
                return _obj.get_ingredients(count=ret_count)
        else:
            smores_error('#Cx004.3')
    except AttributeError:
        smores_error('#Cx001.4')

def get_ingredients(med_id, source):
    med_ing = load_ingredients(med_id, source, True)
    return format_to_print(med_ing, 'ing') if med_ing is not None and type(med_ing) is not int else med_ing


def run_med_to_json(source, med_id=None, to_write=[False, None], print_local=[False, None], incr=500):
    _run_md = md.get_med_dict_by_src(source)
    logging.debug('Returned Medication Dictionary: \n   {0}'.format(_run_md))
    _total = 1 if med_id is not None else _run_md.get_med_count()
    _bundle = True if _total > 1 else False
    _output = to_write[0]
    _base_file = to_write[1]
    _increment = incr

    def get_bundle_json():
        _count = 0
        _iters = int(math.ceil(_total/_increment))
        _med_list = list(_run_md.med_list.values())
        if _iters > 1:
            print('Medications will be saved across {0} files.'.format(_iters))
            for i in trange(_iters, desc='File Number'):
                list_end = _count + _increment if (_count + _increment) < _total else _total
                bundle = tmpl.build_bundle('MEDICATION', _med_list[_count:list_end], print_local, incr=None)
                write_file(output_file=_base_file, iter=i+1, data=bundle)
                _count += _increment

        else:
            bundle = tmpl.build_bundle('MEDICATION', _med_list, print_local)
            write_file(output_file=_base_file, data=bundle)

    def get_single_json(object):
        return tmpl.build_med_template(object, print_local)


    if _bundle and _output:
        get_bundle_json()
    elif _bundle:
        _count = 0
        progress = tqdm(total=_total)
        progress.set_description("")
        logging.debug("Current Med Dict 'med_list': \n   {0}".format(_run_md.med_list))
        for key, med_o in _run_md.med_list.items():
            med_o.add_json(get_single_json(med_o))
            _count += 1
            progress.update(1)
    elif med_id is not None:
        med_o = m.get_med_by_id(med_id, source)
        med_o.add_json(get_single_json(med_o))

    else:
        smores_error('#Kx001.2')


def run_med_to_csv(source, med_id=None, to_write=None, print_local=[False, None], incr=500):
    _run_md = md.get_med_dict_by_src(source)
    _total = 1 if med_id is not None else _run_md.get_med_count()
    _bundle = True if _total > 1 else False
    _base_file = to_write
    _increment = incr
    print_headers = ['id', 'name', 'rxcui', 'tty']

    def get_rows(object):
        if type(object) is rxnorm.RxCUI or type(object) is m.Medication:
            return format_to_print(object, f_type='CSV', f_mod={'cui': ['RXNORM']})

        else:
            smores_error('TBC')

    if _bundle:
        _count = 0
        progress = tqdm(total=_total)
        progress.set_description("")
        smoresLog.debug("Current Med Dict 'med_list': \n   {0}".format(_run_md.med_list))
        _iters = int(math.ceil(_total / _increment))
        if _iters > 1:
            print('Medications will be saved across {0} files.'.format(_iters))
            _items = _run_md.med_list
            _med_list = list(_run_md.med_list.values())
            for i in trange(_iters, desc='File Number'):
                list_end = _count + _increment if (_count + _increment) < _total else _total
                bundle = format_to_print(_med_list[_count:list_end], 'CSV')
                # for key in _med_list[_count:list_end]:
                #     bundle.append(get_rows(_items[key]))
                #     progress.update(1)
                print(bundle)
                # write_file(output_file=_base_file, iter=i + 1, data=bundle)
                _count += _increment
        else:
            bundle = []
            for key, med_o in _run_md.med_list.items():
                bundle.append(get_rows(med_o))
                progress.update(1)
            print(bundle)
            # write_file(output_file=_base_file, data=bundle)
    else:
        print('Nothing')
    # TODO Write To CSV needs to be completed. 100% necessary for i2b2 Updates
    # This can probably mimic the structure of run_med_to_json in defining bundle printing
    # across multiple files and repurpose the "write_file" function
    # TODO Need to identify how to add in or utilize the existing print_formats for RXCUI and MEDICATION objects
    # Copy from old RxNormMapper?


def format_to_print(object, f_type=None, f_mod=None):
    _formatted = []
    # try:
    if type(object) is list:
        for item in object:
            _formatted.append(format_to_print(item, f_type))
    elif type(object) is dict:
        for key, value in object.items():
            _formatted.append(format_to_print(value, f_type))
    elif type(object) is str:
        _formatted.append(object)
    else:
        _formatted.append(object.print_formats(p_type=f_type, p_mod=f_mod))
    return _formatted
    # except TypeError:
    #     smores_error('#Kx001.1', str(type(object)))
    # except AttributeError:
    #     smores_error('#Kx001.1')

def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    Git Home: https://gist.github.com/aubricus/f91fb55dc6ba5557fbab06119420dd6a
    """

    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()

class MedKit:
    med_kits = {}

    def __init__(self, in_file, file_delim=','):
        self.path = in_file
        self.file_name = self.get_filename(in_file)
        self.delim = file_delim
        # self.input_q = queue.Queue()
        self.file_lines = self.get_file_lines()
        self.c_records = 0
        self.records = {}
        self.headers = self.get_headers(file_delim)
        self.trackers = {}
        self.m_dict = md.MedicationDictionary(self.file_name, link=self)
        MedKit.med_kits[self.path] = self
        self.prog_q = None

        m.Medication.med_id_list[self.file_name] = {}

    def get_filename(self, path):
        if type(path) is Path:
            return path.name
        else:
            head, tail = ntpath.split(path)
            file, ext = os.path.splitext(tail or ntpath.basename(head))
            return file

    def get_headers(self, delim=','):
        try:
            data = open(self.path, "r+").readline()
            keys = ['LOCAL_ID', 'CODE', 'CODE_TYPE', 'NAME']
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
            return lines
        except FileNotFoundError:
            smores_error('#Cx001.1')
            return None
        except PermissionError:
            smores_error('#Cx001.2')
            return None

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