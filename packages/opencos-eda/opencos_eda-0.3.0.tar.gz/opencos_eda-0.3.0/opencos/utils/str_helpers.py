'''opencos.utils.str_helpers -- Various str helpers for printing, indenting'''

import fnmatch
import os
import re
import shlex
import textwrap

VALID_TARGET_INFO_STR = (
    "should start with a . or underscore/letter, rest should be"
    " ., alpha-numeric, dashes, or underscores."
)

def is_valid_target_name(s: str) -> bool:
    '''Returns True if str starts with . or underscore/letter, rest alphanum, dash, dot,

    or underscores. We allow '.' otherwise deps_file.py posts warnings about badly named
    targets for files that are missing.'''
    if not s or not (s[0].isalpha() or s[0] == '_' or s[0] == '.'):
        return False
    return s.replace('_', '').replace('-', '').replace('.', '').isalnum()

def strip_all_quotes(s: str) -> str:
    '''Returns str with all ' and " removed'''
    return s.replace("'", '').replace('"', '')


def strip_outer_quotes(s: str) -> str:
    '''Returns str with outer pairs of (' or ") removed

    Note this is done safely removing only outmost pairs of single quotes, or double
    quotes. This is used on bare CLI args that may have outer quotes from shlex.quote(arg).
    '''
    ret = str(s)
    while (ret.startswith("'") and ret.endswith("'")) or \
          (ret.startswith('"') and ret.endswith('"')):
        ret = ret[1:-1]
    return ret


def string_or_space(text: str, whitespace: bool = False) -> str:
    '''Returns str of either spaces (len(text)) or returns text.'''
    if whitespace:
        return " " * len(text)
    return text


def sanitize_defines_for_sh(value: object, shlex_quote: bool = False) -> str:
    '''Attempts to make a str for +define+key[=value] safer for using as a shell arg

    Need to sanitize this for shell in case someone sends a +define+foo+1'b0,
    which needs to be escaped as +define+foo+1\'b0, otherwise bash or sh will
    think this is an unterminated string.

    Optionally can use shlex.quote('+define+key=value') via shlex_quote=True
    '''
    if isinstance(value, str):
        value = value.replace("'", "\\" + "'")
    if shlex_quote:
        value = shlex.quote(value)
    return value


def sprint_time(time_value: int) -> str:
    '''Return pretty str for time'''
    s = int(time_value)
    txt = ""
    do_all = False
    # days
    if s >= (24 * 60 * 60): # greater than 24h, we show days
        d = int(s / (24 *60 *60))
        txt += f"{d}d:"
        s -= d * 24 * 60 * 60
        do_all = True
    # hours
    if do_all or s >= (60 *60):
        d = int(s / (60 * 60))
        txt += f"{d:2}:"
        s -= d * 60 * 60
        do_all = True
    # minutes
    d = int(s / 60)
    txt += f"{d:02}:"
    s -= d * 60
    # seconds
    txt += f"{s:02}"
    return txt


def indent_wrap_long_text(
        text: str, width: int = 80, initial_indent: int = 0, indent: int = 4
) -> str:
    """Returns str, wraps text to a specified width and indents subsequent lines."""
    wrapped_lines = textwrap.wrap(
        text, width=width,
        initial_indent=' ' * initial_indent,
        subsequent_indent=' ' * indent
    )
    return '\n'.join(wrapped_lines)


def dep_str2list(value: object) -> list:
    '''Helper for a markup \n or space separated string to be returned as a list'''
    if value is None:
        return []
    if isinstance(value, str):
        return re.split('\n+| +', value) # convert \n separated to list, also split on spaces
    return value


def fnmatch_or_re(pattern: str, string: str) -> bool:
    '''Returns True if pattern/string matches in re.match or fnmatch'''
    matches = []
    # fnmatch check, aka: ./*test
    matches.append(
        bool(fnmatch.fnmatch(name=string, pat=pattern))
    )
    # regex check, aka: ./.*test
    try:
        matches.append(
            bool(re.match(pattern=pattern, string=string))
        )
    except: # pylint: disable=bare-except
        # could have been an illegal/unsupported regex, so don't match.
        pass
    return any(matches)


def get_terminal_columns():
    """
    Retrieves the number of columns (width) of the terminal window.

    Returns:
        int: The number of columns in the terminal, or a default value (e.g., 80)
             if the terminal size cannot be determined.
    """
    try:
        size = os.get_terminal_size()
        return size.columns
    except OSError:
        # Handle cases where the terminal size cannot be determined (e.g., not in a TTY)
        return 80  # Default to 80 columns

    return 80 # else default to 80.


def pretty_list_columns_manual(data: list, num_columns: int = 4, auto_columns: bool = True) -> list:
    """Returns list, from list of str, organized into columns, manually aligning them."""

    ret_lines = []
    if not data:
        return ret_lines

    _spacing = 2

    # Calculate maximum width for each column
    max_lengths = [0] * num_columns
    max_item_len = 0
    for i, item in enumerate(data):
        col_index = i % num_columns
        max_lengths[col_index] = max(max_lengths[col_index], len(item))
        max_item_len = max(max_item_len, len(item))

    if auto_columns and num_columns > 1:
        window_cols = get_terminal_columns()
        max_line_len = 0
        for x in max_lengths:
            max_line_len += x + _spacing
        if max_line_len > window_cols:
            # subtract a column (already >= 2):
            ret_lines.extend(
                pretty_list_columns_manual(data=data, num_columns=num_columns-1, auto_columns=True)
            )
            return ret_lines
        if max_line_len + max_item_len + _spacing < window_cols:
            # add 1 more column if we're guaranteed to have room.
            ret_lines.extend(
                pretty_list_columns_manual(data=data, num_columns=num_columns+1, auto_columns=True)
            )
            return ret_lines
        # else continue

    # Print data in columns
    ret_lines.append('')
    for i, item in enumerate(data):
        col_index = i % num_columns
        ret_lines[-1] += str(item).ljust(max_lengths[col_index] + _spacing)
        if col_index == num_columns - 1 or i == len(data) - 1:
            ret_lines.append('')

    return ret_lines


def print_columns_manual(data: list, num_columns: int = 4, auto_columns: bool = True) -> None:
    """Prints a list of strings in columns, manually aligning them."""

    lines = pretty_list_columns_manual(
        data=data, num_columns=num_columns, auto_columns=auto_columns
    )
    print('\n'.join(lines))
