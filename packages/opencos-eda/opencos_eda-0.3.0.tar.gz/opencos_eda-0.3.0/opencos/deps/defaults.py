''' opencos.deps.defaults -- pymodule for defaults referenced by other modules here'''


DEPS_FILE_EXTS = set([
    '.yml', '.yaml', '.toml', '.json',
    # Treat no extension DEPS as YAML.
    ''
])

ROOT_TABLE_KEYS_NOT_TARGETS = set([
    "DEFAULTS",
    "METADATA",
])

KNOWN_EDA_COMMANDS = set([
    "sim",
    "elab",
    "synth",
    "flist",
    "proj",
    "multi",
    "tools-multi",
    "sweep",
    "build",
    "waves",
    "upload",
    "open",
    "export",
])

SUPPORTED_TARGET_TABLE_KEYS = set([
    'args',
    'defines',
    'parameters',
    'incdirs',
    'top',
    'deps',
    'reqs',
    'multi',
    'tags',
    'commands'] + list(KNOWN_EDA_COMMANDS))

SUPPORTED_DEP_KEYS_BY_TYPE = {
    dict: set(['commands']),
    str: set(['*']),
}

SUPPORTED_TAG_KEYS = set([
    'with-tools',
    'with-commands',
    'with-args',
    'args',
    'deps',
    'reqs',
    'defines',
    'parameters',
    'incdirs',
    'replace-config-tools',
    'additive-config-tools',
])

COMMAND_ATTRIBUTES = {
    # with default values
    'run-from-work-dir': True,
    'filepath-subst-target-dir': True,

    'run-after-tool': False,   # default is to run before any tool compile step.
    'dirpath-subst-target-dir': False,
    'var-subst-args': False,
    'var-subst-os-env': False,
    'tee': None,
}

SUPPORTED_COMMAND_KEYS = set([
    'shell',
    'peakrdl',
    'work-dir-add-srcs', 'work-dir-add-sources'
])
for key in COMMAND_ATTRIBUTES:
    SUPPORTED_COMMAND_KEYS.add(key)
