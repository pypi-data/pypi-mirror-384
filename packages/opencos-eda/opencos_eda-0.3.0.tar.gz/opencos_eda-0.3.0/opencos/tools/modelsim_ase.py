''' opencos.tools.modelsim_ase - Used by opencos.eda for sim/elab commands w/ --tool=modelsim_ase.

Contains classes for ToolModelsimAse, CommandSimModelsimAse, CommandElabModelsimAse.

Note that this is for 32-bit Modelsim Student Edition. Consider using --tool=questa_fse instead.
'''

# pylint: disable=R0801 # (duplicate code in derived classes, such as if-condition return.)

import os

from opencos import util
from opencos.commands import sim, CommandSim
from opencos.tools.questa import ToolQuesta
from opencos.utils.str_helpers import sanitize_defines_for_sh

class ToolModelsimAse(ToolQuesta):
    '''ToolModelsimAse used by opencos.eda for --tool=modelsim_ase'''

    _TOOL = 'modelsim_ase' # otherwise it's 'questa' from base class.
    _EXE = 'vsim'
    use_vopt = False

class CommandSimModelsimAse(CommandSim, ToolModelsimAse):
    '''CommandSimModelsimAse is a command handler for: eda sim --tool=modelsim_ase'''

    def __init__(self, config: dict):
        CommandSim.__init__(self, config=config)
        ToolModelsimAse.__init__(self, config=self.config)
        self.shell_command = os.path.join(self.sim_exe_base_path, 'vsim')
        self.starter_edition = True
        self.args.update({
            'tool': self._TOOL, # override
            'gui': False,
            'vopt': self.use_vopt,
        })
        self.args_help.update({
            'vopt': (
                'Boolean to enable/disable use of vopt step prior to vsim step'
                ' Note that vopt args can be controlled with --elab-args=<value1>'
                ' --elab-args=<value2> ...'
            )
        })

    def set_tool_defines(self):
        # Update any defines from config.tools.modelsim_ase:
        self.defines.update(
            self.tool_config.get(
                'defines',
                # defaults, if not set:
                {'OC_ASSERT_PROPERTY_NOT_SUPPORTED': 1,
                 'OC_TOOL_MODELSIM_ASE': 1}
            )
        )

    def run_in_batch_mode(self) -> bool:
        '''Returns bool if we should run in batch mode (-c) from command line'''
        # TODO(drew): make CommandSimQuesta a parent and inherit this method instead.
        if self.args['test-mode']:
            return True
        if self.args['gui']:
            return False
        return True

    # We do override do_it() to avoid using CommandSimQuesta.do_it()
    def do_it(self):
        CommandSim.do_it(self)
        #    self.compile()   # runs if stop-before-compile is False, stop-after-compile is True
        #    self.elaborate() # runs if stop-before-compile is False, stop-after-compile is False,
        #                       stop-after-elaborate is True
        #    self.simulate()  # runs if stop-* are all False (run the whole thing)


    def prepare_compile(self):
        self.set_tool_defines()
        self.write_vlog_dot_f()
        self.write_vsim_dot_do(dot_do_to_write='all')

        vsim_command_lists = self.get_compile_command_lists()
        util.write_shell_command_file(
            dirpath=self.args['work-dir'],
            filename='compile_only.sh',
            command_lists=vsim_command_lists
        )

        vsim_command_lists = self.get_elaborate_command_lists()
        util.write_shell_command_file(
            dirpath=self.args['work-dir'],
            filename='compile_elaborate_only.sh',
            command_lists=vsim_command_lists
        )

        # Write simulate.sh and all.sh to work-dir:
        vsim_command_lists = self.get_simulate_command_lists()
        self.write_sh_scripts_to_work_dir(
            compile_lists=[], elaborate_lists=[], simulate_lists=vsim_command_lists
        )

    def compile(self):
        if self.args['stop-before-compile']:
            # don't run anything, save everyting we've already run in _prep_compile()
            return
        if self.args['stop-after-compile']:
            vsim_command_lists = self.get_compile_command_lists()
            self.run_commands_check_logs(vsim_command_lists, log_filename='sim.log',
                                         must_strings=['Errors: 0'], use_must_strings=False)

    def elaborate(self):
        if self.args['stop-before-compile']:
            return
        if self.args['stop-after-compile']:
            return
        if self.args['stop-after-elaborate']:
        # only run this if we stop after elaborate (simulate run it all)
            vsim_command_lists = self.get_elaborate_command_lists()
            self.run_commands_check_logs(vsim_command_lists, log_filename='sim.log')

    def simulate(self):
        if self.args['stop-before-compile'] or self.args['stop-after-compile'] or \
           self.args['stop-after-elaborate']:
            # don't run this if we're stopping before/after compile/elab
            return
        vsim_command_lists = self.get_simulate_command_lists()
        self.run_commands_check_logs(vsim_command_lists, log_filename='sim.log')

    def get_compile_command_lists(self, **kwargs) -> list:
        # This will also set up a compile.
        vsim_command_list = [
            self.sim_exe,
            '-c' if self.run_in_batch_mode() else '',
            '-do', 'vsim_vlogonly.do', '-logfile', 'sim.log',
        ]
        return [vsim_command_list]

    def get_elaborate_command_lists(self, **kwargs) -> list:
        # This will also set up a compile, for vlog + vsim (0 time)
        vsim_command_list = [
            self.sim_exe,
            '-c' if self.run_in_batch_mode() else '',
            '-do', 'vsim_lintonly.do', '-logfile', 'sim.log',
        ]
        return [vsim_command_list]

    def get_simulate_command_lists(self, **kwargs) -> list:
    # This will also set up a compile, for vlog + vsim (with run -a)
        vsim_command_list = [
            self.sim_exe,
            '-c' if self.run_in_batch_mode() else '',
            '-do', 'vsim.do', '-logfile', 'sim.log',
        ]
        return [vsim_command_list]

    def get_post_simulate_command_lists(self, **kwargs) -> list:
        return []

    def write_vlog_dot_f(self, filename='vlog.f') -> None:
        '''Returns none, creates filename (str) for a vlog.f'''
        vlog_dot_f_lines = []

        # Add compile args from config.tool.modelsim_ase:
        vlog_dot_f_lines += self.tool_config.get(
            'compile-args',
            '-sv -svinputport=net -lint').split()
        # Add waivers from config.tool.modelsim_ase:
        for waiver in self.tool_config.get(
                'compile-waivers',
                [ #defaults:
                    '2275', # 2275 - Existing package 'foo_pkg' will be overwritten.
                ]) + self.args['compile-waivers']:
            vlog_dot_f_lines += ['-suppress', str(waiver)]

        if self.args['gui'] or self.args['waves']:
            vlog_dot_f_lines += self.tool_config.get('compile-waves-args', '').split()

        vlog_dot_f_fname = filename
        vlog_dot_f_fpath = os.path.join(self.args['work-dir'], vlog_dot_f_fname)

        for value in self.incdirs:
            vlog_dot_f_lines += [ f"+incdir+{value}" ]

        for k,v in self.defines.items():
            if v is None:
                vlog_dot_f_lines += [ f'+define+{k}' ]
            else:

                # if the value v is a double-quoted string, such as v='"hi"', the
                # entire +define+NAME="hi" needs to wrapped in double quotes with the
                # value v double-quotes escaped: "+define+NAME=\"hi\""
                if isinstance(v, str) and v.startswith('"') and v.endswith('"'):
                    str_v = v.replace('"', '\\"')
                    vlog_dot_f_lines += [ f'"+define+{k}={str_v}"' ]
                else:
                    # Generally we should only support int and str python types passed as
                    # +define+{k}={v}, but also for SystemVerilog plusargs
                    vlog_dot_f_lines += [ f'+define+{k}={sanitize_defines_for_sh(v)}' ]


        vlog_dot_f_lines += self.args['compile-args']

        vlog_dot_f_lines += [
            '-source',
            ] + list(self.files_sv) + list(self.files_v)

        if not self.files_sv and not self.files_v:
            if not self.args['stop-before-compile']:
                self.error(f'{self.target=} {self.files_sv=} and {self.files_v=} are empty,',
                           'cannot create a valid vlog.f')

        with open(vlog_dot_f_fpath, 'w', encoding='utf-8') as f:
            f.writelines(line + "\n" for line in vlog_dot_f_lines)

    def vopt_handle_parameters(self) -> (str, list):
        '''Returns str for vopt or voptargs, and list of vopt tcl

        Note this is used for self.use_vopt = True or False.
        '''

        voptargs_str = ''
        vopt_do_lines = []

        # Note that if self.use_vopt=True, we have to do some workarounds for how
        # some questa-like tools behave for: tcl/.do + vopt arg processing
        # This affects string based parameters that have spaces (vopt treats spaces unique args,
        # vsim does not). Since we'd like to keep the vopt/vsim split into separate steps, we can
        # work around this by setting tcl varaibles for each parameter.
        if self.parameters:
            if not self.use_vopt:
                voptargs_str += ' ' + ' '.join(self.process_parameters_get_list(arg_prefix='-G'))
            else:
                for k,v in self.parameters.items():
                    s = sim.parameters_dict_get_command_list(params={k: v}, arg_prefix='')[0]
                    # At this point, s should be a str in form {k}={v}
                    if not s or '=' not in s:
                        continue
                    if ' ' in s:
                        # Instead of:
                        #   vopt -GMyParam="hi bye"
                        # we'll do:
                        #   set PARAMETERS(MyParam) "hi bye"
                        #  vopt -GMyParam=$PARAMETERS(MyParam)
                        s = s.replace(f'{k}=', f'set PARAMETERS({k}) ')
                        vopt_do_lines.append(s)
                        voptargs_str += f' -G{k}=$PARAMETERS({k}) '
                    else:
                        voptargs_str += f' -G{s} '

        return voptargs_str, vopt_do_lines


    def write_vsim_dot_do( # pylint: disable=too-many-locals
            self, dot_do_to_write: list
    ) -> None:
        '''Writes files(s) based on dot_do_to_write(list of str)

        list arg values can be empty (all) or have items 'all', 'sim', 'lint', 'vlog'.'''

        vsim_dot_do_fpath = os.path.join(self.args['work-dir'], 'vsim.do')
        vsim_lintonly_dot_do_fpath = os.path.join(self.args['work-dir'], 'vsim_lintonly.do')
        vsim_vlogonly_dot_do_fpath = os.path.join(self.args['work-dir'], 'vsim_vlogonly.do')

        sim_plusargs_str = self._get_sim_plusargs_str()
        vsim_suppress_list_str = self._get_vsim_suppress_list_str()
        vsim_ext_args = ' '.join(self.args.get('sim-args', []))

        voptargs_str = self.tool_config.get('elab-args', '')
        voptargs_str += ' '.join(self.args.get('elab-args', []))
        if self.args['gui'] or self.args['waves']:
            voptargs_str += ' ' + self.tool_config.get('simulate-waves-args', '+acc')
            util.artifacts.add_extension(
                search_paths=self.args['work-dir'], file_extension='wlf',
                typ='waveform', description='Modelsim/Questa Waveform WLF (Wave Log Format) file'
            )

        # TODO(drew): support self.args['sim_libary'] (1 lists)
        vlog_do_lines = []
        vsim_do_lines = []

        # parameters, use helper method to get voptargs_str and vopt_do_lines
        more_voptargs_str, vopt_do_lines = self.vopt_handle_parameters()
        voptargs_str += more_voptargs_str


        vopt_one_liner = ""
        if self.use_vopt:
            vopt_one_liner = (
                f"vopt {voptargs_str} work.{self.args['top']} -o opt__{self.args['top']}"
            )
            vopt_one_liner = vopt_one_liner.replace('\n', ' ') # needs to be a one-liner
            # vopt doesn't need -voptargs=(value) like vsim does, simply use (value).
            vopt_one_liner = vopt_one_liner.replace('-voptargs=', '')

            vsim_one_liner = "vsim -onfinish stop" \
                + f" -sv_seed {self.args['seed']} {sim_plusargs_str} {vsim_suppress_list_str}" \
                + f" {vsim_ext_args} opt__{self.args['top']}"
        else:
            # vopt doesn't exist, use single vsim call after vlog call:
            vsim_one_liner = "vsim -onfinish stop" \
                + f" -sv_seed {self.args['seed']} {sim_plusargs_str} {vsim_suppress_list_str}" \
                + f" {voptargs_str} {vsim_ext_args} work.{self.args['top']}"


        vsim_one_liner = vsim_one_liner.replace('\n', ' ')

        vlog_do_lines += [
            "if {[file exists work]} { vdel -all work; }",
            "vlib work;",
            "quietly set qc 30;",
            "if {[catch {vlog -f vlog.f} result]} {",
            "    echo \"Caught $result \";",
            "    if {[batch_mode]} {",
            "        quit -f -code 20;",
            "    }",
            "}",
        ]

        if self.use_vopt:
            vopt_do_lines += [
                "if {[catch { " + vopt_one_liner + " } result] } {",
                "    echo \"Caught $result\";",
                "    if {[batch_mode]} {",
                "        quit -f -code 19;",
                "    }",
                "}",
            ]

        vsim_do_lines += [
            "if {[catch { " + vsim_one_liner + " } result] } {",
            "    echo \"Caught $result\";",
            "    if {[batch_mode]} {",
            "        quit -f -code 18;",
            "    }",
            "}",
        ]

        vsim_vlogonly_dot_do_lines = vlog_do_lines + [
            "if {[batch_mode]} {",
            "    quit -f -code 0;",
            "}",
        ]

        final_check_teststatus_do_lines = [
            "set TestStatus [coverage attribute -name SEED -name TESTSTATUS];",
            "if {[regexp \"TESTSTATUS += 0\" $TestStatus]} {",
            "    quietly set qc 0;",
            "} elseif {[regexp \"TESTSTATUS += 1\" $TestStatus]} {",
            "    quietly set qc 0;",
            "} else {",
            "    quietly set qc 2;",
            "}",
            "if {[batch_mode]} {",
            "    quit -f -code $qc;",
            "}",
        ]

        # final vlog/vopt/vsim lint-only .do command (want to make sure it can completely
        # build for 'elab' style eda job), runs for 0ns, logs nothing for a waveform, quits
        vsim_lintonly_dot_do_lines = vlog_do_lines + vopt_do_lines + vsim_do_lines \
            + final_check_teststatus_do_lines

        # final vlog/opt/vsim full simulation .do command.
        vsim_dot_do_lines = vlog_do_lines + vopt_do_lines + vsim_do_lines + [
            "onbreak { resume; };",
            "catch {log -r *};",
            "run -a;",
        ] + final_check_teststatus_do_lines

        write_all = len(dot_do_to_write) == 0 or 'all' in dot_do_to_write
        if write_all or 'sim' in dot_do_to_write:
            with open(vsim_dot_do_fpath, 'w', encoding='utf-8') as f:
                f.writelines(line + "\n" for line in vsim_dot_do_lines)

        if write_all or 'lint' in dot_do_to_write:
            with open(vsim_lintonly_dot_do_fpath, 'w', encoding='utf-8') as f:
                f.writelines(line + "\n" for line in vsim_lintonly_dot_do_lines)

        if write_all or 'vlog' in dot_do_to_write:
            with open(vsim_vlogonly_dot_do_fpath, 'w', encoding='utf-8') as f:
                f.writelines(line + "\n" for line in vsim_vlogonly_dot_do_lines)


    def _get_sim_plusargs_str(self) -> str:
        sim_plusargs = []

        assert isinstance(self.args["sim-plusargs"], list), \
            f'{self.target=} {type(self.args["sim-plusargs"])=} but must be list'

        for x in self.args['sim-plusargs']:
            # For vsim we need to add a +key=value if the + is missing
            if x[0] != '+':
                x = f'+{x}'
            sim_plusargs.append(x)

        return ' '.join(sim_plusargs)


    def _get_vsim_suppress_list_str(self) -> str:
        vsim_suppress_list = []
        # Add waivers from config.tool.modelsim_ase:
        for waiver in self.tool_config.get(
                'simulate-waivers', [
                    #defaults:
                    '3009', # 3009: [TSCALE] - Module 'foo' does not have a timeunit/timeprecision
                            #       specification in effect, but other modules do.
                ]) + self.args['sim-waivers']:
            vsim_suppress_list += ['-suppress', str(waiver)]

        return ' '.join(vsim_suppress_list)


    def artifacts_add(self, name: str, typ: str, description: str) -> None:
        '''Override from Command.artifacts_add, so we can catch known file

        names to make their typ/description better, such as CommandSim using
        sim.log
        '''
        _, leafname = os.path.split(name)
        if leafname == 'sim.log':
            description = 'Modelsim/Questa Transcript log file'

        super().artifacts_add(name=name, typ=typ, description=description)


class CommandElabModelsimAse(CommandSimModelsimAse):
    '''CommandElabModelsimAse is a command handler for: eda elab --tool=modelsim_ase'''

    command_name = 'elab'

    def __init__(self, config:dict):
        super().__init__(config)
        self.args['stop-after-elaborate'] = True


class CommandLintModelsimAse(CommandSimModelsimAse):
    '''CommandLintModelsimAse is a command handler for: eda lint --tool=modelsim_ase'''

    command_name = 'lint'

    def __init__(self, config:dict):
        super().__init__(config)
        self.args['stop-after-compile'] = True
        self.args['stop-after-elaborate'] = True
