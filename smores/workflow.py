from smores.smoresCLI import smoresCLI

class Workflow:
    def __init__(self, client:smoresCLI):
        self.client = client
        self.steps = []
        self.outputs = []
        self.dependencies = {}
        self.target = {'name': '', 'type': '', 'loaded': False}
        self.name = ''
        self.save = False
        self.valid_steps = client.cmds + client.output_cmds

    def add_target(self, target:str, type:str, is_loaded:bool):
        self.target['name'] = target
        self.target['type'] = type
        self.target['loaded'] = is_loaded

    def add_step(self, cmd):
        if cmd in self.valid_steps:
            if cmd in self.steps:
                pass
            else:
                self.steps.append(cmd)

    def add_output(self, cmd):
        if cmd in self.valid_steps:
            if cmd in self.outputs:
                pass
            else:
                self.outputs.append(cmd)
    # TODO Add customization options to outputs. Now defaults to outputting file only
    # def configure_output(self, cmd, params):
    #     try:
    #         self.outputs[self.outputs.index(cmd)] = params
    #         return True
    #     except KeyError:
    #         return False

    def has_steps(self):
        return True if len(self.steps) > 0 else False

    def draw_steps(self):
        for cmd in range(len(self.steps)):
            print('   {0}) {1}'.format(cmd, self.steps[cmd]))
        print('\n')

    def run(self):
        if not self.target['loaded']:
            self.client.do_load([self.target['name'], self.target['type']])
        else:
            print('File already loaded, skipping load step.')

        for cmd in self.steps:
            self.client.run_file_call(self.client.client_run_function(cmd), cmd, self.target['name'])

        for output in self.outputs:
            output_func = self.client.client_run_function(output)
            output_func(self.target['name'])








