from jinja2 import Environment, FileSystemLoader, exceptions
import smores.medication as m
import rxnorm.rxnorm as rxnorm
import logging
import math
import json
from tqdm import tqdm, trange
smoresLog = logging.getLogger('smores')

def load_template(template):
    try:
        template_loader = FileSystemLoader('../smores/templates')
        env = Environment(loader=template_loader)
        if template == 'MEDICATION':
            smoresLog.debug('Template Found: Medication')
            return env.get_template('MedicationRequest.txt')
        elif template == 'CODEABLE_CONCEPT':
            smoresLog.debug('Template Found: codeableConcept')
            return env.get_template('codeableConcept.txt')
        elif template == 'BUNDLE':
            smoresLog.debug('Template Found: bundle')
            return env.get_template('fhirBundle.txt')
        else:
            smoresLog.error('ERROR : Template "'+str(template)+'" is Not Available')
            print('ERROR : Template "'+str(template)+'" is Not Available')
            return None
    except exceptions.TemplateNotFound:
        smoresLog.error('')
        print('Template Folder could not be found')
        return None



def build_template(t_type, object, local_coding=[False, None]):
    if t_type == 'MEDICATION':
        return build_med_template(object, local_coding)


def build_med_template(medication, local_coding=[False, None]):
    if type(medication) is m.Medication:
        med = medication
    else:
        med = m.get_med_by_id(medication, 'LOCAL')
    d = {}
    rxcui_scd = med.get_rxcui_by_tty(['SCD', 'SBD', 'SCDC', 'SBDC'])
    rxcui_ing = med.get_rxcui_by_tty(['IN', 'MIN', 'PIN'])
    # snomed = med.get_snomed_ct()
    # ndc = med.get_ndc()

    d['med_id'] = med.local_id
    temp_coding = []
    if len(rxcui_scd) > 0:
        for cui in rxcui_scd:
            # codeableConcept = {'system': None, 'code': None, 'display': None}
            this_codeableConcept = {}
            rxcui = rxnorm.get_rxcui(cui)
            this_codeableConcept['display'] = json.dumps(rxcui.get_property('name'))
            this_codeableConcept['system'] = json.dumps('http://www.nlm.nih.gov/research/umls/rxnorm')
            this_codeableConcept['code'] = json.dumps(rxcui.cui)
            temp_coding.append(this_codeableConcept)


    # if len(snomed) > 0:
    # TODO: Add in SNOMED coding print

    # if len(ndc) > 0:
    # TODO: Add in NDC coding print

    if local_coding[0] and local_coding[1] is not None:
        FHIRcodeableConcept = load_template('CODEABLE_CONCEPT')
        if FHIRcodeableConcept is not None:
            this_codeableConcept = {}
            this_codeableConcept['display'] = json.dumps(med.get_name())
            this_codeableConcept['system'] = json.dumps(local_coding[1])
            this_codeableConcept['code'] = json.dumps(med.get_local_id())
            temp_coding.append(this_codeableConcept)

    if len(temp_coding) > 0:
        FHIRcodeableConcept = load_template('CODEABLE_CONCEPT')
        if FHIRcodeableConcept is not None:
            d['coding'] = FHIRcodeableConcept.render(coding=temp_coding)

    if len(rxcui_ing) > 0:
        d['ingredient'] = [{'itemCodeableConcept': {}}]
        # print(d['ingredient'])
        temp_coding = []
        ing_FHIRcodeableConcept = load_template('CODEABLE_CONCEPT')
        if ing_FHIRcodeableConcept is not None:
            for cui in rxcui_ing:
                # codeableConcept = {'system': None, 'code': None, 'display': None}
                this_codeableConcept = {}
                rxcui = rxnorm.get_rxcui(cui)
                this_codeableConcept['display'] = json.dumps(rxcui.get_property('name'))
                this_codeableConcept['system'] = json.dumps('http://www.nlm.nih.gov/research/umls/rxnorm')
                this_codeableConcept['code'] = json.dumps(rxcui.cui)
                temp_coding.append(this_codeableConcept)
            smoresLog.debug(temp_coding)
            d['ingredient'][0]['itemCodeableConcept'] = ing_FHIRcodeableConcept.render(coding=temp_coding)
    FHIRMedicationRequest = load_template('MEDICATION')
    if FHIRMedicationRequest is not None:
        output = FHIRMedicationRequest.render(med=d)
    else:
        output = None
    return output


def build_bundle(b_type, objects, local_coding=[False, None], _limit=0):
    """ @in_file is an existing "temporary" file that contains objects that need to be constructed into a FHIR Bundle"""
    smoresLog.debug(objects)
    if type(objects) is not list:
        smoresLog.error('Values for Bundle is Not Valid!')
    else:
        FHIRbundle = load_template('BUNDLE')
        entries = []
        _max = len(objects)
        if FHIRbundle is not None:
            if _limit is not None and _limit > 0:
                _iterations = int(math.ceil(len(objects) / _limit))
                _current = 0
                smoresLog.debug('Iterations to Run: ' + str(_iterations))
                try:
                    for i in trange(0, _iterations):
                        smoresLog.debug('Iteration: ' + str(i+1))
                        _iter_max = _current + _limit if _current + _limit < _max else _max
                        _temp_entry = []
                        _start = _current
                        smoresLog.debug('Object Set: ' + str(objects[_start:_iter_max]))
                        progress=tqdm(total=(_iter_max - _current))
                        for obj in objects[_start:_iter_max]:
                            resource = build_template(b_type, obj, local_coding)
                            _temp_entry.append(resource)
                            _current += 1
                            progress.update(1)
                        entries = entries + _temp_entry

                except (KeyError,ValueError,RuntimeError,OSError) as err:
                    print('Error During Bundle Processing: {0}, '
                          '\nBundle is incomplete after ' + str(_current) + ' items processed.').format(err)
                    return FHIRbundle.render(entry=entries)

            else:
                progress = tqdm(total=_max)
                for obj in objects:
                    resource = build_template(b_type, obj, local_coding)
                    entries.append(resource)
                    progress.update(1)
                return FHIRbundle.render(entry=entries)


