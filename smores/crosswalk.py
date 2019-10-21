import smores.api as api
import smores.medication as med
import smores.utility.util as util

def get_crosswalk(source, target):
    return CUICrosswalk.CROSSWALKS[source][target]

# Class to handle workflows for performing various crosswalks to other code sets.
# allows for the definition of a workflow of different processes to be executed
# CUICrosswalk('RXNORM','NDC')
class CUICrosswalk:
    CROSSWALKS = {}

    def __init__(self, init_type:str, target_type:str):
        self.start = init_type
        self.end = target_type
        self.workflow = []
        CUICrosswalk.add_crosswalk(self)
        self.config = None

    @staticmethod
    def add_crosswalk(cross):
        if cross.start not in CUICrosswalk.CROSSWALKS.keys():
            CUICrosswalk.CROSSWALKS[cross.start] = {}
        CUICrosswalk.CROSSWALKS[cross.start][cross.end] = cross

    def add_config(self, param, val):
        if self.config is None:
            self.config = {}
        self.config[param] = val

    def set_workflow(self, work:list):
        self.workflow = work

    def add_step(self, step, cont=''):
        """
        Add a step to the workflow for this crosswalk
        :param step:
        :param cont: A value returned from the process that triggers it to continue
        """
        _proc = {'func': step}
        if cont != '':
            _proc['continue'] = cont
        self.workflow.append(_proc)

    def run_crosswalk(self, input:str):
        """
        Run the processes in the defined workflow for this crosswalk
        :param input: code input for crosswalk
        :return:
        """

        if self.config is not None:
            _proc_data = self.config
            _proc_data['input'] = input
        else:
            _proc_data = input

        for _proc in self.workflow:
            _func = _proc['func']
            _proc_data = self.run_workflow_process(_func, _proc_data if _proc_data is not None else input)
            if 'continue' in _proc.keys():
                if _proc_data == _proc['continue']:
                    continue
                else:
                    break
        return _proc_data

    @staticmethod
    def run_workflow_process(process, input):
        try:
            if isinstance(process, CUICrosswalk):
                return process.run_crosswalk(input)
            else:
                return process(input)
                # Process needs to be some kind of api call that returns the form of BOOL, DICT
                # return result
        except:
            print('error')

# Create NDC to RxNorm Crosswalk
NDC_RXN = CUICrosswalk('NDC','RXNORM')
NDC_RXN1 = CUICrosswalk('NDC1','RXNORM1')
NDC_RXN1.add_step(med.NDC.api.get_ndc_rxnorm)
NDC_RXN2 = CUICrosswalk('NDC2','RXNORM2')
NDC_RXN2.add_step(med.NDC.api2.get_ndc_rxnorm)
NDC_RXN.add_step(NDC_RXN1, None)
NDC_RXN.add_step(NDC_RXN2)

# Create RxNorm to NDC Crosswalk
RXN_NDC = CUICrosswalk('RXNORM', 'NDC')
RXN_NDC1 = CUICrosswalk('RXN1', 'NDC1')
RXN_NDC1.add_step(med.NDC.api.get_rxnorm_ndc)
RXN_NDC2 = CUICrosswalk('RXN2', 'NDC2')
RXN_NDC2.add_step(med.NDC.api2.get_rxnorm_ndc)
RXN_NDC.add_step(RXN_NDC1, None)
RXN_NDC.add_step(RXN_NDC2)

# Create RxNorm to SNOMED Crosswalk
RXN_SNOMED = CUICrosswalk('RXNORM', 'SNOMEDCT_US')
RXN_SNOMED.add_step(med.UMLSCUI.api.get_crosswalk_cui)
RXN_SNOMED.add_config('src', 'RXNORM')
RXN_SNOMED.add_config('target_src', 'SNOMEDCT_US')


