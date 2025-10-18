''' opencos.tools.questa - Used by opencos.eda commands with --tool=questa

Also a base class for tools.modelsim_ase.
'''

# pylint: disable=R0801 # (setting similar, but not identical, self.defines key/value pairs)

# TODO(drew): fix these pylint eventually:
# pylint: disable=too-many-branches

import os
import re
import shutil

from opencos import util
from opencos.eda_base import Tool
from opencos.commands import CommandSim, CommandFList

class ToolQuesta(Tool):
    '''Base class for CommandSimQuesta, collects version information about qrun'''

    _TOOL = 'questa'
    _EXE = 'qrun'

    starter_edition = False # Aka, modelsim_ase
    use_vopt = shutil.which('vopt') # vopt exists in qrun/vsim framework, and we'll use it.
    sim_exe = '' # vsim or qrun
    sim_exe_base_path = ''
    questa_major = None
    questa_minor = None

    def __init__(self, config: dict):
        super().__init__(config=config)
        self.args['part'] = 'xcu200-fsgd2104-2-e'

    def get_versions(self) -> str:
        if self._VERSION:
            return self._VERSION
        path = shutil.which(self._EXE)
        if not path:
            self.error(f"{self._EXE} not in path, need to setup",
                       "(i.e. source /opt/intelFPGA_pro/23.4/settings64.sh")
            util.debug(f"{path=}")
            if self._EXE.endswith('qrun') and \
               any(x in path for x in ('modelsim_ase', 'questa_fse')):
                util.warning(f"{self._EXE=} Questa path is for starter edition",
                             "(modelsim_ase, questa_fse), consider using --tool=modelsim_ase",
                             "or --tool=questa_fse")
        else:
            self.sim_exe = path
            self.sim_exe_base_path, _ = os.path.split(path)

        if self._EXE.endswith('vsim'):
            self.starter_edition = True

        m = re.search(r'(\d+)\.(\d+)', path)
        if m:
            self.questa_major = int(m.group(1))
            self.questa_minor = int(m.group(2))
            self._VERSION = str(self.questa_major) + '.' + str(self.questa_minor)
        else:
            self.error("Questa path doesn't specificy version, expecting (d+.d+)")
        return self._VERSION

    def set_tool_defines(self):
        # Will only be called from an object which also inherits from CommandDesign,
        # i.e. has self.defines
        self.defines['OC_TOOL_QUESTA'] = None
        self.defines[f'OC_TOOL_QUESTA_{self.questa_major:d}_{self.questa_minor:d}'] = None

class CommandSimQuesta(CommandSim, ToolQuesta):
    '''Command handler for: eda sim --tool=questa.'''

    def __init__(self, config:dict):
        CommandSim.__init__(self, config)
        ToolQuesta.__init__(self, config=self.config)
        # add args specific to this simulator
        self.args.update({
            'gui': False,
            'tcl-file': 'sim.tcl',
            'work-lib': 'work',
        })
        self.args_help.update({
            'gui': 'Run Questa in GUI mode',
            'tcl-file': 'name of TCL file to be created for Questa simulation',
            'work-lib': 'Questa work library name',
        })

        self.shell_command = self.sim_exe # set by ToolQuesta.get_versions(self)
        self.vlog_commands = []
        self.vopt_commands = []
        self.vsim_commands = []

    def set_tool_defines(self):
        ToolQuesta.set_tool_defines(self)

    # We do not override CommandSim.do_it(), CommandSim.check_logs_for_errors(...)

    def prepare_compile(self):
        self.set_tool_defines()
        self.vlog_commands = self.get_compile_command_lists()
        self.vopt_commands = self.get_elaborate_command_lists()
        self.vsim_commands = self.get_simulate_command_lists()
        self.write_sh_scripts_to_work_dir(
            compile_lists=self.vlog_commands,
            elaborate_lists=self.vopt_commands,
            simulate_lists=self.vsim_commands
        )

    def compile(self):
        if self.args['stop-before-compile']:
            return
        self.run_commands_check_logs(
            self.vlog_commands, check_logs=True, log_filename='vlog.log'
        )

    def elaborate(self):
        if self.args['stop-before-compile'] or self.args['stop-after-compile']:
            return
        self.run_commands_check_logs(
            self.vopt_commands, check_logs=True, log_filename='vopt.log'
        )

    def simulate(self):
        if self.args['stop-before-compile'] or self.args['stop-after-compile'] or \
           self.args['stop-after-elaborate']:
            return
        self.run_commands_check_logs(
            self.vsim_commands, check_logs=True, log_filename='vsim.log'
        )

    def get_compile_command_lists(self, **kwargs) -> list:
        self.set_tool_defines()
        ret = []

        # Create work library
        vlib_cmd = [os.path.join(self.sim_exe_base_path, 'vlib'), self.args['work-lib']]
        ret.append(vlib_cmd)

        # Map work library
        vmap_cmd = [os.path.join(self.sim_exe_base_path, 'vmap'), 'work', self.args['work-lib']]
        ret.append(vmap_cmd)

        # Compile files
        if self.files_v or self.files_sv:
            vlog_cmd = [os.path.join(self.sim_exe_base_path, 'vlog'), '-64', '-sv']

            # Add include directories
            for incdir in self.incdirs:
                vlog_cmd += [f'+incdir+{incdir}']

            # Add defines
            for key, value in self.defines.items():
                if value is None:
                    vlog_cmd += [f'+define+{key}']
                else:
                    vlog_cmd += [f'+define+{key}={value}']

            # Add suppression flags
            vlog_cmd += [
                '-svinputport=net',
                '-suppress', 'vlog-2275',
                '-suppress', 'vlog-2583',
            ]

            # Add source files
            vlog_cmd += self.files_v + self.files_sv

            ret.append(vlog_cmd)

        # Compile VHDL files if any
        if self.files_vhd:
            vcom_cmd = [os.path.join(self.sim_exe_base_path, 'vcom'), '-64']
            vcom_cmd += self.files_vhd
            ret.append(vcom_cmd)

        return ret

    def get_elaborate_command_lists(self, **kwargs) -> list:
        if self.args['stop-after-compile']:
            return []

        vopt_cmd = [os.path.join(self.sim_exe_base_path, 'vopt'), '-64']

        # Add optimization flags
        vopt_cmd += [
            '-suppress', 'vopt-13159',
            '-suppress', 'vopt-2685',
            '-note', 'vopt-2718',
        ]

        if self.args['gui'] or self.args['waves']:
            vopt_cmd += ['+acc']

        # Add top module and output
        vopt_cmd += [self.args['top'], '-o', 'opt_design']

        return [vopt_cmd]

    def get_simulate_command_lists(self, **kwargs) -> list:
        # Create TCL file
        tcl_name = os.path.abspath(os.path.join(self.args['work-dir'], self.args['tcl-file']))

        if self.args['waves']:
            util.artifacts.add_extension(
                search_paths=self.args['work-dir'], file_extension='wlf',
                typ='waveform', description='Questa Waveform WLF file'
            )

        with open(tcl_name, 'w', encoding='utf-8') as fo:
            if self.args['waves']:
                if self.args['waves-start']:
                    print(f"run {self.args['waves-start']} ns", file=fo)
                print("add wave -r /*", file=fo)
            print("run -all", file=fo)
            if self.run_in_batch_mode():
                print("quit", file=fo)

        # Create vsim command
        vsim_cmd = [os.path.join(self.sim_exe_base_path, 'vsim'), '-64']

        if not self.run_in_batch_mode():
            vsim_cmd += ['-gui']
        else:
            vsim_cmd += ['-c']

        if util.args['verbose']:
            vsim_cmd += ['-verbose']

        # Add simulation arguments
        vsim_cmd += ['-do', tcl_name, 'opt_design']

        return [vsim_cmd]

    def get_post_simulate_command_lists(self, **kwargs) -> list:
        return []

    def run_in_batch_mode(self) -> bool:
        '''Returns bool if we should run in batch mode (-c) from command line'''
        if self.args['test-mode']:
            return True
        if self.args['gui']:
            return False
        return True

    def artifacts_add(self, name: str, typ: str, description: str) -> None:
        '''Override from Command.artifacts_add for better descriptions'''
        _, leafname = os.path.split(name)
        if leafname == 'vsim.log':
            description = 'Questa simulation step (3/3) log from stdout/stderr'
        elif leafname == 'vopt.log':
            description = 'Questa elaboration step (2/3) log from stdout/stderr'
        elif leafname == 'vlog.log':
            description = 'Questa compile step (1/3) log from stdout/stderr'

        super().artifacts_add(name=name, typ=typ, description=description)


class CommandFListQuesta(CommandFList, ToolQuesta):
    '''CommandFListQuesta is a command handler for: eda flist --tool=questa'''

    def __init__(self, config: dict):
        CommandFList.__init__(self, config=config)
        ToolQuesta.__init__(self, config=self.config)


class CommandElabQuesta(CommandSimQuesta):
    '''Command handler for: eda elab --tool=questa'''

    command_name = 'elab'

    def __init__(self, config:dict):
        CommandSimQuesta.__init__(self, config)
        # add args specific to this simulator
        self.args['stop-after-elaborate'] = True


class CommandLintQuesta(CommandSimQuesta):
    '''Command handler for: eda lint --tool=questa'''

    command_name = 'lint'

    def __init__(self, config:dict):
        CommandSimQuesta.__init__(self, config)
        # add args specific to this simulator
        self.args['stop-after-compile'] = True
        self.args['stop-after-elaborate'] = True
