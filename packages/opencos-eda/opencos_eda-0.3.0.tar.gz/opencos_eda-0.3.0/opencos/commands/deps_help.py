'''opencos.commands.deps_help - command handler for: eda deps_help [args]

Note this command is handled differently than others (such as CommandSim),
it is generally run as simply

    > eda deps_help
    > eda deps_help --verbose
    > eda deps_help --help

uses no tools and will print a help text regarding DEPS markup files to stdout.
'''


import os

from opencos.eda_base import Command
from opencos import util


BASIC_DEPS_HELP = '''

--------------------------------------------------------------------

  What is a DEPS.yml file and why does `eda` use this?
  - DEPS.yml is a fancy filelist.
  - Used to organize a project into "targets", a tool can run on a "target".
  - Allows for more than just source files attached to a "target".
    -- incdirs, defines, and args can be applied to a "target".

--------------------------------------------------------------------

  Hello World example:

  The following example is a DEPS.yml file example for a SystemVerilog simulation of
  hello_world_tb.sv. DEPS.yml is, in short, a fancy filelist. We use them in the `eda`
  app to organize projects.

--- DEPS.yml: ---

hello-world:           # <-- this is a named target that will be run

  deps:                # <-- 'deps' is a list of SV, Verilog, VHDL files in compile order
    - hello_world_tb.sv

  top: hello_world_tb  # <-- For testbenches, it is good practice to specifiy the topmost
                       #     module using using 'top'. This is not necessary for design
                       #     files.


--- hello_world_tb.sv: ---

module hello_world_tb;

  initial begin
    #10ns;
    $display("%t %m: Hello World!", $realtime);
    $display("%t %m: Test finished", $realtime);
    $finish;
  end

endmodule : hello_world_tb

---


  hello-world:
    The target name in the DEPS.yml we named is hello-world. That is a valid target
    that `eda` can use. Such as:

       eda sim --tool=verilator hello-world


--------------------------------------------------------------------

   Beyond Hello World example:

   The following example is a DEPS.yml file for a more complex module simulation.
   It has two files in ./DEPS.yml and ./lib/DEPS.yml.

--- ./DEPS.yml: ---

my_fifo:                         # <-- this is a design
  incdirs: . lib                 # <-- 'incdirs' define the paths searched to find `include files
  defines:
    FIFO_DEBUG                   # add a basic define
    FIFO_IMPLEMENTATION=uram     # add a define with a value
  deps:            # <-- 'deps' is a list of SV, Verilog, VHDL files in compile order
    - my_fifo.sv                 # an SV file pulled in directly
    - lib/bin_to_gray            # a target, in a subdirectory that has it's own DEPS

my_fifo_test:                    # <-- this is a TEST
  top: my_fifo_test              # the top will default to whatever target is provided
                                 # by the user, so this could be optional
  deps:
    - my_fifo                    # the target that is defined above
    - my_fifo_tb.sv              # an SV file pulled in directly

my_fifo_stress_test:             # <-- this is another TEST
  top: my_fifo_test              # not optional because top is not "my_fifo_stress_test"
  defines:
    STRESS_TEST                  # configures my_fifo_test to be more stressful
  deps:
    - my_fifo_test               # aside from the define, this is same as "my_fifo_test"

--- lib/DEPS.yml: ---

lib_pkg:                         # <-- this is a package required by bin_to_gray below
  deps:
    - assert_pkg.sv              # an SV package pulled in directly, before it's needed below
    - lib_pkg.sv                 # an SV package pulled in directly

bin_to_gray:                     # <-- this is the target that was required by ../my_fifo
  deps:
    - lib_pkg                    # a target package, listed first as SV requires packages
                                 # to be read before the code that uses them
    - bin_to_gray.sv             # an SV module pulled in directly

--------------------------------------------------------------------
'''


FULL_DEPS_HELP = '''

--------------------------------------------------------------------

   Full DEPS.yml schema:

```
DEFAULTS: # <table> defaults applied to ALL targets in this file, local targets ** override ** the defaults.

METADATA: # <table> unstructured data, any UPPERCASE first level key is not considered a target.

target-spec:

  args: # <array or | separated str>
    - --waves
    - --sim_plusargs="+info=500"

  defines: # <table>
    SOME_DEFINE: value
    SOME_DEFINE_NO_VALUE:   # we just leave this blank, or use nil (yaml's None)

  incdirs: # <array>
    - some/relative/path

  top: # <string>

  deps: # <array or | space separated string>
    - some_relative_target       # <string> aka, a target
    - some_file.sv               # <string> aka, a file
    - sv@some_file.txt           # <string> aka, ext@file where we'd like a file not ending in .sv to be
                                 # treated as a .sv file for tools.
                                 # Supported for sv@, v@, vhdl@, cpp@
    - commands:                  # <table> with key 'commands' for a <array>:  support for built-in commands
                                 # Note this cannot be confused for other targets or files.
      - shell: # <string>
        var-subst-args: # <bool> default false. If true, substitute vars in commands, such as {fpga}
                        # substituted from eda arg --fpga=SomeFpga, such that {fpga} becomes SomeFpga
        var-subst-os-env:  #<bool> default false. If true, substitute vars in commands using os.environ vars,
                           # such as {FPGA} could get substituted by env value for $FPGA
        tee: # <string> optional filename, otherwise shell commands write to {target-spec}__shell_0.log
        run-from-work-dir: #<bool> default true. If false, runs from the directory of this DEPS file.
        filepath-subst-target-dir: #<bool> default true. If false, disables shell file path
	                               substituion on this target's directory (this DEPS file dir).
        dirpath-subst-target-dir: #<bool> default false. If true, enables shell directory path
	                              substituion on this target's directory (this DEPS file dir).
      - shell: echo "Hello World!"
      - work-dir-add-sources: # <array or | space separated string>, this is how to add generated files
                              # to compile order list.
      - peakrdl:              # <string>     ## peakrdl command to generate CSRs

  reqs: # <array or | space separated string>
    - some_file.mem           # <string> aka, a non-source file required for this target.
                              # This file is checked for existence prior to invoking the tool involved, for example,
                              # in a simulation this would be done prior to a compile step.

  multi:
    ignore-this-target:  # <array of tables> eda commands to be ignored in `eda multi <command>` for this target only
                         # this is checked in the matching multi targets list, and is not inherited through dependencies.
      - commands: synth  # space separated strings
        tools: vivado    # space separated strings

      - commands: sim # omit tools, ignores 'sim' commands for all tools, for this target only, when this target
                      # is in the target list called by `eda multi`.

      - tools: vivado # omit commands, ignores all commands if tool is vivado, for this target only, when this target
                      # is in the target list called by `eda multi`.

    args: # <array> additional args added to all multi commands of this target.
          # Note that all args are POSIX with dashes, --sim-plusargs=value, etc.

  <eda-command>: # key is one of sim, flist, build, synth, etc.
                 # can be used instead of 'tags' to support different args or deps.
    disable-tools: # Note: not implemented yet.
    only-tools:    # Note: not implemented yet.
    args: # <array or | space separated string>
    deps: # <array or | space separated string> # Note: not implemented yet
    defines: ## <table>
    incdirs: ## <array>

  tags: # <table> this is the currently support tags features in a target.
    <tag-name>: # <string> key for table, can be anything, name is not used.
      with-tools: <array or | space separated string>
                  # If using one of these tools, apply these values.
                  # entries can be in the form: vivado, or vivado:2024.1
      with-commands: <array or | space separated string>
                  # apply if this was the `eda` command, such as: sim
      with-args: # <table> (optional) arg key/value pairs to match for this tag.
                 # this would be an alternative to running eda with --tags=value
                 # The existence of an argument with correct value would enable a tag.
                 # And example would be:
                 #   with-args:
                 #     waves: true
      args: <array or | space separated string> # args to be applied if this target is used, with a matching
                                          # tool in 'with-tools'.
      deps: <array or | space separated string, applied with tag>
      defines: <table, applied with tag>
      incdirs: <array, applied with tag>
      replace-config-tools: <table>  # spec matching eda_config_defaults.yml::tools.<tool> (replace merge strategy)
      additive-config-tools: <table> # spec matching eda_config_defaults.yml::tools.<tool> (additive merge strategy)


```
'''


class CommandDepsHelp:
    '''command handler for: eda deps-help'''

    command_name = 'deps-help'

    def __init__(self, config: dict):
        # We don't inherit opencos.eda_base.Command, so we have to set a few
        # member vars for Command.help to work.
        self.args = {}
        self.args_help = {}
        self.config = config
        self.status = 0

    def process_tokens( # pylint: disable=unused-argument
        self, tokens: list, process_all: bool = True,
        pwd: str = os.getcwd()
    ) -> list:
        '''This is effectively our 'run' method, entrypoint from opencos.eda.main'''

        print(BASIC_DEPS_HELP)
        if util.args['verbose'] or util.args['debug']:
            print()
            print(FULL_DEPS_HELP)

        return []

    def help(self, tokens: list) -> None:
        '''Since we don't inherit from opencos.eda_base.Command, need our own help
        method
        '''
        Command.help(self, tokens=tokens, no_targets=True)
        print()
        print(FULL_DEPS_HELP)
