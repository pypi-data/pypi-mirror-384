''' opencos.tools.quartus - Used by opencos.eda commands with --tool=quartus

Contains classes for ToolQuartus, and command handlers for synth, build, flist.
Used for Intel FPGA synthesis, place & route, and bitstream generation.
'''

# pylint: disable=R0801 # (setting similar, but not identical, self.defines key/value pairs)

import os
import re
import shlex
import shutil
import subprocess

from pathlib import Path

from opencos import util, eda_base
from opencos.eda_base import Tool
from opencos.commands import (
    CommandSynth, CommandBuild, CommandFList, CommandProj, CommandUpload, CommandOpen
)
from opencos.utils.str_helpers import sanitize_defines_for_sh, strip_outer_quotes

class ToolQuartus(Tool):
    '''ToolQuartus used by opencos.eda for --tool=quartus'''

    _TOOL = 'quartus'
    _EXE = 'quartus_sh'

    quartus_year = None
    quartus_release = None
    quartus_base_path = ''
    quartus_exe = ''
    quartus_gui_exe = ''

    def __init__(self, config: dict):
        super().__init__(config=config)
        self.args.update({
            'part': 'A3CY135BM16AE6S',
            'family': 'Agilex 3',
        })
        self.args_help.update({
            'part': 'Device used for commands: synth, build.',
            'family': 'FPGA family for Quartus (e.g., Stratix IV, Arria 10, etc.)',
        })

    def get_versions(self) -> str:
        if self._VERSION:
            return self._VERSION

        path = shutil.which(self._EXE)
        if not path:
            self.error("Quartus not in path, need to install or add to $PATH",
                       f"(looked for '{self._EXE}')")
        else:
            self.quartus_exe = path
            self.quartus_base_path, _ = os.path.split(path)
        self.quartus_gui_exe = shutil.which('quartus') # vs quartus_sh



        # Get version based on install path name or by running quartus_sh --version
        util.debug(f"quartus path = {self.quartus_exe}")
        m = re.search(r'(\d+)\.(\d+)', self.quartus_exe)
        if m:
            version = m.group(1) + '.' + m.group(2)
            self._VERSION = version
        else:
            # Try to get version by running quartus_sh --version
            try:
                result = subprocess.run(
                    [self.quartus_exe, '--version'],
                    capture_output=True, text=True, timeout=10, check=False
                )
                version_match = re.search(r'Version (\d+\.\d+)', result.stdout)
                if version_match:
                    self._VERSION = version_match.group(1)
                else:
                    self.error("Could not determine Quartus version")
            except (
                subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError
            ):
                self.error("Could not determine Quartus version")

        if self._VERSION:
            numbers_list = self._VERSION.split('.')
            self.quartus_year = int(numbers_list[0])
            self.quartus_release = int(numbers_list[1])
        else:
            self.error(f"Quartus version not found, quartus path = {self.quartus_exe}")
        return self._VERSION

    def set_tool_defines(self) -> None:
        self.defines['OC_TOOL_QUARTUS'] = None
        def_year_release = f'OC_TOOL_QUARTUS_{self.quartus_year:02d}_{self.quartus_release:d}'
        self.defines[def_year_release] = None

        # Code can be conditional on Quartus versions
        versions = ['20.1', '21.1', '22.1', '23.1', '24.1', '25.1']

        def version_compare(v1, v2):
            v1_parts = [int(x) for x in v1.split('.')]
            v2_parts = [int(x) for x in v2.split('.')]
            l = max(len(v1_parts), len(v2_parts))
            v1_parts += [0] * (l - len(v1_parts))
            v2_parts += [0] * (l - len(v2_parts))
            return (v1_parts > v2_parts) - (v1_parts < v2_parts)

        for ver in versions:
            str_ver = ver.replace('.', '_')
            cmp = version_compare(self._VERSION, ver)
            if cmp <= 0:
                self.defines[f'OC_TOOL_QUARTUS_{str_ver}_OR_OLDER'] = None
            if cmp >= 0:
                self.defines[f'OC_TOOL_QUARTUS_{str_ver}_OR_NEWER'] = None

        util.debug(f"Setup tool defines: {self.defines}")


class CommandSynthQuartus(CommandSynth, ToolQuartus):
    '''CommandSynthQuartus is a command handler for: eda synth --tool=quartus'''

    def __init__(self, config: dict):
        CommandSynth.__init__(self, config)
        ToolQuartus.__init__(self, config=self.config)
        # add args specific to this tool
        self.args.update({
            'gui': False,
            'tcl-file': "synth.tcl",
            'sdc': "",
            'qsf': "",
        })
        self.args_help.update({
            'gui': 'Run Quartus in GUI mode',
            'tcl-file': 'name of TCL file to be created for Quartus',
            'sdc': 'SDC constraints file',
            'qsf': 'Quartus Settings File (.qsf)',
        })

    def do_it(self) -> None:
        CommandSynth.do_it(self)

        if self.is_export_enabled():
            return

        # create TCL
        tcl_file = os.path.abspath(
            os.path.join(self.args['work-dir'], self.args['tcl-file'])
        )

        self.write_tcl_file(tcl_file=tcl_file)

        # execute Quartus synthesis
        command_list_gui = [self.quartus_gui_exe, '-t', tcl_file]
        command_list = [
            self.quartus_exe, '-t', tcl_file
        ]
        if not util.args['verbose']:
            command_list.append('-q')

        # Add artifact tracking
        util.artifacts.add_extension(
            search_paths=self.args['work-dir'], file_extension='qpf',
            typ='tcl', description='Quartus Project File'
        )
        util.artifacts.add_extension(
            search_paths=self.args['work-dir'], file_extension='qsf',
            typ='tcl', description='Quartus Settings File'
        )
        util.artifacts.add_extension(
            search_paths=self.args['work-dir'], file_extension='rpt',
            typ='text', description='Quartus Synthesis Report'
        )

        if self.args['gui'] and self.quartus_gui_exe:
            self.exec(self.args['work-dir'], command_list_gui)
        else:
            self.exec(self.args['work-dir'], command_list)


        saved_qpf_filename = self.args["top"] + '.qpf'
        if not os.path.isfile(os.path.join(self.args['work-dir'], saved_qpf_filename)):
            self.error('Saved project file does not exist:',
                       os.path.join(self.args['work-dir'], saved_qpf_filename))

        util.info(f"Synthesis done, results are in: {self.args['work-dir']}")

        # Note: in GUI mode, if you ran: quaruts -t build.tcl, it will exit on completion,
        # so we'll re-open the project.
        if self.args['gui'] and self.quartus_gui_exe:
            self.exec(
                work_dir=self.args['work-dir'],
                command_list=[self.quartus_gui_exe, saved_qpf_filename]
            )

    def write_tcl_file(self, tcl_file: str) -> None:  # pylint: disable=too-many-locals,too-many-branches
        '''Writes synthesis capable Quartus tcl file to filepath 'tcl_file'.'''

        top = self.args['top']
        part = self.args['part']
        family = self.args['family']

        tcl_lines = [
            "# Quartus Synthesis Script",
            "load_package flow",
            f"project_new {top} -overwrite",
            f"set_global_assignment -name FAMILY \"{family}\"",
            f"set_global_assignment -name DEVICE {part}",
            f"set_global_assignment -name TOP_LEVEL_ENTITY {top}",
        ]

        # Add source files (convert to relative paths and use forward slashes)
        # Note that default of self.args['all-sv'] is False so we should have added
        # all files to self.files_sv instead of files_v:
        for f in self.files_v:
            rel_path = os.path.relpath(f, self.args['work-dir']).replace('\\', '/')
            tcl_lines.append(f"set_global_assignment -name VERILOG_FILE \"{rel_path}\"")
        for f in self.files_sv:
            rel_path = os.path.relpath(f, self.args['work-dir']).replace('\\', '/')
            tcl_lines.append(f"set_global_assignment -name SYSTEMVERILOG_FILE \"{rel_path}\"")
        for f in self.files_vhd:
            rel_path = os.path.relpath(f, self.args['work-dir']).replace('\\', '/')
            tcl_lines.append(f"set_global_assignment -name VHDL_FILE \"{rel_path}\"")

        # Add include directories - Quartus needs the base directory where "lib/" can be found
        for incdir in self.incdirs:
            tcl_lines.append(f"set_global_assignment -name SEARCH_PATH \"{incdir}\"")

        # Parameters -->  set_parameter -name <Parameter_Name> <Value>
        for k,v in self.parameters.items():
            if not isinstance(v, (int, str)):
                util.warning(f'parameter {k} has value: {v}, parameters must be int/string types')
            if isinstance(v, int):
                tcl_lines.append(f"set_parameter -name {k} {v}")
            else:
                v = strip_outer_quotes(v.strip('\n'))
                v = '"' + v + '"'
                tcl_lines.append(f"set_parameter -name {k} {sanitize_defines_for_sh(v)}")


        # Add all include directories as user libraries for better include resolution
        for incdir in self.incdirs:
            if os.path.exists(incdir):
                tcl_lines.append(
                    f"set_global_assignment -name USER_LIBRARIES \"{incdir}\""
                )

        # Add defines
        for key, value in self.defines.items():
            if value is None:
                tcl_lines.append(f"set_global_assignment -name VERILOG_MACRO \"{key}\"")
            else:
                tcl_lines.append(f"set_global_assignment -name VERILOG_MACRO \"{key}={value}\"")

        # Add constraints
        default_sdc = False
        sdc_files = []
        if self.args['sdc']:
            sdc_files = [os.path.abspath(self.args['sdc'])]
        elif self.files_sdc:
            # Use files from DEPS target or command line.
            sdc_files = self.files_sdc
        else:
            default_sdc = True
            sdc_file = self.args['top'] + '.sdc'
            sdc_files = [sdc_file]

        for f in sdc_files:
            for attr in ('SDC_FILE', 'SYN_SDC_FILE', 'RTL_SDC_FILE'):
                tcl_lines.extend([
                    f"set_global_assignment -name {attr} \"{f}\""
                ])
        tcl_lines.append("set_global_assignment -name SYNTH_TIMING_DRIVEN_SYNTHESIS ON")

        if default_sdc:
            self.write_default_sdc(sdc_file=os.path.join(self.args['work-dir'], sdc_file))

        tcl_lines += [
            "# Run synthesis",
            'flng::run_flow_command -flow "compile" -end "dni_synthesis"',
            'flng::run_flow_command -flow "compile" -end "sta_early" -resume',
        ]

        with open(tcl_file, 'w', encoding='utf-8') as ftcl:
            ftcl.write('\n'.join(tcl_lines))


    def write_default_sdc(self, sdc_file: str) -> None:
        '''Writes a default SDC file to filepath 'sdc_file'.'''

        sdc_lines = []
        util.info("Creating default constraints: clock:",
                  f"{self.args['clock-name']}, {self.args['clock-ns']} (ns),")

        clock_name = self.args['clock-name']
        period = self.args['clock-ns']

        sdc_lines += [
            ("create_clock -name {" + clock_name + "} -period {" + str(period) + "} [get_ports "
             "{" + clock_name + "}]")
        ]

        with open( sdc_file, 'w', encoding='utf-8' ) as fsdc:
            fsdc.write('\n'.join(sdc_lines))


class CommandBuildQuartus(CommandBuild, ToolQuartus):
    '''CommandBuildQuartus is a command handler for: eda build --tool=quartus'''

    def __init__(self, config: dict):
        CommandBuild.__init__(self, config)
        ToolQuartus.__init__(self, config=self.config)
        # add args specific to this tool
        self.args.update({
            'gui': False,
            'proj': False,
            'resynth': False,
            'reset': False,
            'add-tcl-files': [],
            'flow-tcl-files': [],
        })

    def do_it(self) -> None: # pylint: disable=too-many-branches,too-many-statements,too-many-locals
        # add defines for this job
        self.set_tool_defines()
        self.write_eda_config_and_args()

        # create FLIST
        flist_file = os.path.abspath(os.path.join(self.args['work-dir'], 'build.flist'))
        util.debug(f"CommandBuildQuartus: top={self.args['top']} target={self.target}",
                   f"design={self.args['design']}")

        command_list = [
            eda_base.get_eda_exec('flist'), 'flist',
            '--no-default-log',
            '--tool=' + self.args['tool'],
            '--force',
            '--out=' + flist_file,
            '--no-quote-define',
            '--no-quote-define-value',
            '--no-escape-define-value',
            '--equal-define',
            '--bracket-quote-path',
            # Enhanced prefixes for better Quartus integration
            '--prefix-incdir=' + shlex.quote("set_global_assignment -name SEARCH_PATH "),
            '--prefix-define=' + shlex.quote("set_global_assignment -name VERILOG_MACRO "),
            '--prefix-sv=' + shlex.quote("set_global_assignment -name SYSTEMVERILOG_FILE "),
            '--prefix-v=' + shlex.quote("set_global_assignment -name VERILOG_FILE "),
            '--prefix-vhd=' + shlex.quote("set_global_assignment -name VHDL_FILE "),
            '--emit-rel-path',  # Use relative paths for better portability
        ]

        # create an eda.flist_input.f that we'll pass to flist:
        with open(os.path.join(self.args['work-dir'], 'eda.flist_input.f'),
                  'w', encoding='utf-8') as f:

            # defines
            for key,value in self.defines.items():
                if value is None:
                    f.write(f"+define+{key}\n")
                else:
                    f.write(shlex.quote(f"+define+{key}={value}") + "\n")

            # incdirs:
            for incdir in self.incdirs:
                f.write(f'+incdir+{incdir}\n')

            # files:
            f.write('\n'.join(self.files_v + self.files_sv + self.files_vhd + ['']))


        command_list.append('--input-file=eda.flist_input.f')



        # Write out a .sh command for debug
        command_list = util.ShellCommandList(command_list, tee_fpath='run_eda_flist.log')
        util.write_shell_command_file(dirpath=self.args['work-dir'], filename='run_eda_flist.sh',
                                      command_lists=[command_list], line_breaks=True)

        self.exec(work_dir=self.args['work-dir'], command_list=command_list,
                  tee_fpath=command_list.tee_fpath)

        if self.args['job-name'] == "":
            self.args['job-name'] = self.args['design']
        project_dir = 'project.' + self.args['job-name']

        # Create a simple Quartus build TCL script
        build_tcl_file = os.path.abspath(os.path.join(self.args['work-dir'], 'build.tcl'))
        build_tcl_lines = [
            '# Quartus Build Script',
            '',
            f'set Top {self.args["top"]}'
            '',
            'load_package flow',
            f'project_new {self.args["design"]} -overwrite',
            f'set_global_assignment -name FAMILY \"{self.args["family"]}\"',
            f'set_global_assignment -name DEVICE {self.args["part"]}',
            'set_global_assignment -name TOP_LEVEL_ENTITY "$Top"',
            '',
            '# Source the flist file',
            'source build.flist',
            '',
        ]

        # If we have additinal TCL files via --add-tcl-files, then source those too:
        if self.args['add-tcl-files']:
            build_tcl_lines.append('')
            build_tcl_lines.append('# Source TCL files from --add-tcl-files args')
            for fname in self.args['add-tcl-files']:
                fname_abs = os.path.abspath(fname)
                if not os.path.isfile(fname_abs):
                    self.error(f'add-tcl-files: "{fname_abs}"; does not exist')
                build_tcl_lines.append(f'source {fname_abs}')
            build_tcl_lines.append('')

        # If we don't have any args for --flow-tcl-files, then use a default flow:
        if not self.args['flow-tcl-files']:
            build_tcl_lines.extend([
                '# Default flow for compile',
                'flng::run_flow_command -flow "compile"',
                ''
            ])
        else:
            build_tcl_lines.append('')
            build_tcl_lines.append('# Flow TCL files from --flow-tcl-files args')
            for fname in self.args['flow-tcl-files']:
                fname_abs = os.path.abspath(fname)
                if not os.path.isfile(fname_abs):
                    self.error(f'flow-tcl-files: "{fname_abs}"; does not exist')
                build_tcl_lines.append(f'source {fname_abs}')
            build_tcl_lines.append('')

        with open(build_tcl_file, 'w', encoding='utf-8') as ftcl:
            ftcl.write('\n'.join(build_tcl_lines))

        # launch Quartus build, from work-dir:
        command_list_gui = [self.quartus_gui_exe, '-t', 'build.tcl', project_dir]
        command_list = [self.quartus_exe, '-t', 'build.tcl', project_dir]
        saved_qpf_filename = self.args["design"] + '.qpf'
        if not util.args['verbose']:
            command_list.append('-q')

        # Write out a .sh command for debug
        command_list = util.ShellCommandList(command_list, tee_fpath=None)
        util.write_shell_command_file(dirpath=self.args['work-dir'], filename='run_quartus.sh',
                                      command_lists=[command_list], line_breaks=True)
        util.write_shell_command_file(dirpath=self.args['work-dir'], filename='run_quartus_gui.sh',
                                      command_lists=[
                                          command_list_gui,
                                          # reopen when done.
                                          [self.quartus_gui_exe, saved_qpf_filename],
                                      ], line_breaks=True)

        # Add artifact tracking for build
        artifacts_search_paths = [
            self.args['work-dir'],
            os.path.join(self.args['work-dir'], 'output_files'),
        ]

        util.artifacts.add_extension(
            search_paths=artifacts_search_paths, file_extension='sof',
            typ='bitstream', description='Quartus SRAM Object File (bitstream)'
        )
        util.artifacts.add_extension(
            search_paths=artifacts_search_paths, file_extension='pof',
            typ='bitstream', description='Quartus Programmer Object File'
        )
        util.artifacts.add_extension(
            search_paths=artifacts_search_paths, file_extension='rpt',
            typ='text', description='Quartus Timing, Fitter, or other report'
        )
        util.artifacts.add_extension(
            search_paths=artifacts_search_paths, file_extension='summary',
            typ='text', description='Quartus Timing, Fitter, or other summary'
        )

        if self.args['stop-before-compile']:
            util.info(f"--stop-before-compile set: scripts in : {self.args['work-dir']}")
            return


        if self.args['gui'] and self.quartus_gui_exe:
            self.exec(
                work_dir=self.args['work-dir'], command_list=command_list_gui
            )
        else:
            self.exec(
                work_dir=self.args['work-dir'], command_list=command_list,
                tee_fpath=command_list.tee_fpath
            )
        if not os.path.isfile(os.path.join(self.args['work-dir'], saved_qpf_filename)):
            self.error('Saved project file does not exist:',
                       os.path.join(self.args['work-dir'], saved_qpf_filename))

        util.info(f"Build done, results are in: {self.args['work-dir']}")

        # Note: in GUI mode, if you ran: quaruts -t build.tcl, it will exit on completion,
        # so we'll re-open the project.
        if self.args['gui'] and self.quartus_gui_exe:
            self.exec(
                work_dir=self.args['work-dir'],
                command_list=[self.quartus_gui_exe, saved_qpf_filename]
            )


class CommandFListQuartus(CommandFList, ToolQuartus):
    '''CommandFListQuartus is a command handler for: eda flist --tool=quartus'''

    def __init__(self, config: dict):
        CommandFList.__init__(self, config=config)
        ToolQuartus.__init__(self, config=self.config)
        self.args.update({
            'emit-parameter': False
        })


class CommandProjQuartus(CommandProj, ToolQuartus):
    '''CommandProjQuartus is a command handler for: eda proj --tool=quartus'''

    def __init__(self, config: dict):
        CommandProj.__init__(self, config)
        ToolQuartus.__init__(self, config=self.config)
        # add args specific to this tool
        self.args.update({
            'gui': True,
            'tcl-file': "proj.tcl",
        })
        self.args_help.update({
            'gui': 'Open Quartus in GUI mode (always True for proj)',
            'tcl-file': 'name of TCL file to be created for Quartus project',
        })

    def do_it(self):
        # add defines for this job
        self.set_tool_defines()
        self.write_eda_config_and_args()

        # create TCL
        tcl_file = os.path.abspath(os.path.join(self.args['work-dir'], self.args['tcl-file']))

        part = self.args['part']
        family = self.args['family']
        top = self.args['top']

        tcl_lines = [
            "# Quartus Project Creation Script",
            "load_package flow",
            f"project_new {top}_proj -overwrite",
            f"set_global_assignment -name FAMILY \"{family}\"",
            f"set_global_assignment -name DEVICE {part}",
            f"set_global_assignment -name TOP_LEVEL_ENTITY {top}",
        ]

        # Add source files
        for f in self.files_v:
            rel_path = os.path.relpath(f, self.args['work-dir']).replace('\\', '/')
            tcl_lines.append(f"set_global_assignment -name VERILOG_FILE \"{rel_path}\"")
        for f in self.files_sv:
            rel_path = os.path.relpath(f, self.args['work-dir']).replace('\\', '/')
            tcl_lines.append(f"set_global_assignment -name SYSTEMVERILOG_FILE \"{rel_path}\"")
        for f in self.files_vhd:
            rel_path = os.path.relpath(f, self.args['work-dir']).replace('\\', '/')
            tcl_lines.append(f"set_global_assignment -name VHDL_FILE \"{rel_path}\"")

        # Add include directories
        for incdir in self.incdirs:
            tcl_lines.append(f"set_global_assignment -name SEARCH_PATH \"{incdir}\"")

        # Add defines
        for key, value in self.defines.items():
            if value is None:
                tcl_lines.append(f"set_global_assignment -name VERILOG_MACRO \"{key}\"")
            else:
                tcl_lines.append(f"set_global_assignment -name VERILOG_MACRO \"{key}={value}\"")

        # Add constraints if available
        if self.files_sdc:
            for sdc_file in self.files_sdc:
                tcl_lines.append(f"set_global_assignment -name SDC_FILE \"{sdc_file}\"")

        tcl_lines += [
            "project_close",
            f"project_open {top}_proj"
        ]

        with open(tcl_file, 'w', encoding='utf-8') as ftcl:
            ftcl.write('\n'.join(tcl_lines))

        # execute Quartus in GUI mode
        command_list = [
            self.quartus_exe, '-t', tcl_file
        ]
        if not util.args['verbose']:
            command_list.append('-q')

        self.exec(self.args['work-dir'], command_list)
        util.info(f"Project created and opened in: {self.args['work-dir']}")


class CommandUploadQuartus(CommandUpload, ToolQuartus):
    '''CommandUploadQuartus is a command handler for: eda upload --tool=quartus'''

    def __init__(self, config: dict):
        CommandUpload.__init__(self, config)
        ToolQuartus.__init__(self, config=self.config)
        # add args specific to this tool
        self.args.update({
            'sof-file': "",
            'cable': "1",
            'device': "1",
            'list-cables': False,
            'list-devices': False,
            'list-sof-files': False,
            'tcl-file': "upload.tcl",
            'log-file': "upload.log",
        })
        self.args_help.update({
            'sof-file': 'SOF file to upload (auto-detected if not specified)',
            'cable': 'Cable number to use for programming',
            'device': 'Device number on the cable',
            'list-cables': 'List available programming cables',
            'list-devices': 'List available devices on cable',
            'list-sof-files': 'List available SOF files',
            'tcl-file': 'name of TCL file to be created for upload',
            'log-file': 'log file for upload operation',
        })

    def do_it(self):  # pylint: disable=too-many-branches,too-many-statements,too-many-locals
        # add defines for this job
        self.set_tool_defines()
        self.write_eda_config_and_args()

        sof_file = None
        if self.args['sof-file']:
            if os.path.isfile(self.args['sof-file']):
                sof_file = self.args['sof-file']
            else:
                self.error(f"Specified SOF file does not exist: {self.args['sof-file']}")

        # Auto-discover SOF file if not specified
        if not sof_file and not self.args['list-cables'] and not self.args['list-devices']:
            sof_files = []
            util.debug(f"Looking for SOF files in {os.path.abspath('.')}")
            for root, _, files in os.walk("."):
                for f in files:
                    if f.endswith(".sof"):
                        fullpath = os.path.abspath(os.path.join(root, f))
                        sof_files.append(fullpath)
                        util.info(f"Found SOF file: {fullpath}")

            if len(sof_files) == 1:
                sof_file = sof_files[0]
            elif len(sof_files) > 1:
                if self.args['list-sof-files']:
                    util.info("Multiple SOF files found:")
                    for sf in sof_files:
                        util.info(f"  {sf}")
                    return
                self.error("Multiple SOF files found, please specify --sof-file")
            elif not sof_files:
                if self.args['list-sof-files']:
                    util.info("No SOF files found")
                    return
                self.error("No SOF files found")

        # Generate TCL script
        script_file = Path(self.args['tcl-file'])

        try:
            with script_file.open("w", encoding="utf-8") as fout:
                fout.write('load_package quartus_pgm\n')

                if self.args['list-cables']:
                    fout.write('foreach cable [get_hardware_names] {\n')
                    fout.write('    puts "Cable: $cable"\n')
                    fout.write('}\n')

                if self.args['list-devices']:
                    cable_idx = int(self.args["cable"]) - 1
                    fout.write(f'set cable [lindex [get_hardware_names] {cable_idx}]\n')
                    fout.write('foreach device [get_device_names -hardware_name $cable] {\n')
                    fout.write('    puts "Device: $device"\n')
                    fout.write('}\n')

                if sof_file:
                    cable_idx2 = int(self.args["cable"]) - 1
                    device_idx = int(self.args["device"]) - 1
                    fout.write(f'set cable [lindex [get_hardware_names] {cable_idx2}]\n')
                    device_cmd = (
                        f'set device [lindex [get_device_names -hardware_name $cable] {device_idx}]'
                    )
                    fout.write(device_cmd)
                    fout.write('set_global_assignment -name USE_CONFIGURATION_DEVICE OFF\n')
                    fout.write('execute_flow -compile\n')
                    fout.write(f'quartus_pgm -c $cable -m jtag -o "p;{sof_file}@$device"\n')

        except Exception as exc:
            self.error(f"Cannot create {script_file}: {exc}")

        if sof_file:
            util.info(f"Programming with SOF file: {sof_file}")
        else:
            util.info("Listing cables/devices only")

        # Execute Quartus programmer
        command_list = [
            self.quartus_exe, '-t', str(script_file)
        ]
        if not util.args['verbose']:
            command_list.append('-q')

        self.exec(self.args['work-dir'], command_list)
        util.info("Upload operation completed")


class CommandOpenQuartus(CommandOpen, ToolQuartus):
    '''CommandOpenQuartus is a command handler for: eda open --tool=quartus'''

    def __init__(self, config: dict):
        CommandOpen.__init__(self, config)
        ToolQuartus.__init__(self, config=self.config)
        # add args specific to this tool
        self.args.update({
            'file': "",
            'gui': True,
        })
        self.args_help.update({
            'file': 'Quartus project file (.qpf) to open (auto-detected if not specified)',
            'gui': 'Open Quartus in GUI mode (always True for open)',
        })

    def do_it(self):
        if not self.args['file']:
            util.info("Searching for Quartus project...")
            found_file = False
            all_files = []
            for root, _, files in os.walk("."):
                for file in files:
                    if file.endswith(".qpf"):
                        found_file = os.path.abspath(os.path.join(root, file))
                        util.info(f"Found project: {found_file}")
                        all_files.append(found_file)
            self.args['file'] = found_file
            if len(all_files) > 1:
                all_files.sort(key=os.path.getmtime)
                self.args['file'] = all_files[-1]
                util.info(f"Choosing: {self.args['file']} (newest)")

        if not self.args['file']:
            self.error("Couldn't find a QPF Quartus project to open")

        projdir = os.path.dirname(self.args['file'])

        command_list = [
            self.quartus_exe, self.args['file']
        ]

        self.write_eda_config_and_args()
        self.exec(projdir, command_list)
        util.info(f"Opened Quartus project: {self.args['file']}")
