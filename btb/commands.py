import contextlib
import os
import logging
from pathlib import Path
from subprocess import run as R
from subprocess import check_output

import sys

# Setup logging
LOG_FILEPATH = os.fspath((Path.cwd() / 'btb.log').absolute())
log = logging.getLogger('utility')


class LoggedRunError(Exception):
    pass


class StdErrPrintMonkeyPatch:
    from functools import partial
    info = partial(print, file=sys.stderr, flush=True)


def read_log():
    with open(LOG_FILEPATH, 'r', encoding='UTF-8') as rf:
        build_log = rf.read().splitlines()

    return build_log


@contextlib.contextmanager
def header_footer(header, footer, print_func, width=80):
    half = ('- ' * ((width - len(header)) // 4))
    print_func(half + header + half)
    yield
    half = ('- ' * ((width - len(footer)) // 4))
    print_func(half + footer + half)


def tail_log(logged, n):
    if len(logged) > 0:
        for line in logged[-n:]:
            yield line


def grep_errors(logged):
    if logged is not None and len(logged) > 0:
        for line in logged:
            or_conds = [
                'error' in line.lower(),
                'FAIL' in line,  # validation
            ]
            not_conds = [
                'export' in line,  # export definitions
                '-Werror' in line,  # Reduce compiler commands
                'ERROR' in line,  # build macros, don't want them
                line.strip().startswith('/'),  # Pace application calls
                line.startswith('[Info]'),
                line.startswith('[Warning]')
            ]

            if any(or_conds) and not any(not_conds):
                yield line


def print_cmd_errors(use_print=False):
    if use_print:
        grep = StdErrPrintMonkeyPatch()
    else:
        grep = log

    with header_footer('looking for lines with "error"', 'end of grepping errors ', grep.info):
        for line in grep_errors(read_log()):
            grep.info(line)


def print_cmd_tail(n=80):
    tail = logging.getLogger('tail')
    with header_footer('tailing log file ', 'end of tailing of the log file ', tail.info):
        for line in tail_log(read_log(), n):
            tail.info(line)


class LoggedCmd:
    """Wrapper for subprocess methods that log to a file and can be patched/mocked for testing."""

    @staticmethod
    def run(cmd_lst: list, cwd=None, exc=None, info_msg=None, to_stdout=False, raise_exc=True, **kwargs):
        """Helper for subprocess that logs to file the output of the command.
        Also defines a default working directory with Path.cwd()

        Note:
            This has to be a staticmethod so that it can be used outside of this file (imports)

        Args:
            cmd_lst: passed to subprocess.run
            cwd:        Current Working Directory - defines where the subprocess.run is executed
            exc:      Either a string for a message to print out if subprocess.run fails. None by default in which case prints
                        only the return code
                        or
                        An exception class (with or without a msg) which to raise instead of the LoggedRunError
            info_msg:   Message to print out when running the command (default None and no print out)
            to_stdout:  Log messages to stdout instead of collecting them with log handler (default False)
            raise_exc:  If exceptions occur, raise them (default True)

        Raises:
            LoggedRunException - Catch this explicitly to handle when subprocess.run retval != 0
        """
        if cwd is None:
            # By default we run the command in the current directory's context
            cwd = Path.cwd()

        if info_msg is not None:
            # log.info(info_msg)
            print(info_msg)

        # When using elevate, the logfile can be created in priviledged mode. This creates issues
        # in consecutive runs. More robust to just create a new file.
        if Path(LOG_FILEPATH).exists():
            Path(LOG_FILEPATH).unlink()

        res = None
        with open(LOG_FILEPATH, 'w') as lfh:
            log.debug(
                f'logged_run\n\tcwd:\t{str(cwd)}\n\tcmd:\t{pretty_string_cmd(cmd_lst)}\n\tkwargs:\t{repr(kwargs)}')
            try:
                cmd_lst = [str(e) for e in cmd_lst]  # py3.6.1 ~ Handles PathLike paths as first argument in the list
                if to_stdout:
                    res = R(cmd_lst, cwd=cwd, universal_newlines=True, encoding='UTF-8', **kwargs)
                else:
                    res = R(cmd_lst, cwd=cwd, stdout=lfh, stderr=lfh, universal_newlines=True, encoding='UTF-8',
                            **kwargs)
            except FileNotFoundError as e:
                log.error(
                    f'{__class__.__name__}.{sys._getframe().f_code.co_name}(...) raised [ {e.__class__.__name__}: {e} ]')

        # Custom exception handling
        if res is None or res.returncode != 0:
            print_cmd_tail(40)
            print_cmd_errors()
            if res is not None:
                log.error('return code: %s', res.returncode)

            if raise_exc:
                if exc is not None:
                    if isinstance(exc, str):
                        log.error(exc)
                        raise LoggedRunError
                    elif isinstance(exc, Exception):
                        raise exc

                # Fallback exception type
                raise LoggedRunError

        return res

    @staticmethod
    def check(cmd_lst: list, cwd=None, exc=None, info_msg=None, to_stdout=False, **kwargs):
        """Helper for subprocess that logs to file the output of the command.
        Also defines a default working directory with Path.cwd()

        Note:
            This has to be a staticmethod so that it can be used outside of this file (imports)

        Args:
            cmd_lst: passed to subprocess.run
            cwd:        Current Working Directory - defines where the subprocess.run is executed
            exc:      Either a string for a message to print out if subprocess.run fails. None by default in which case prints
                        only the return code
                        or
                        An exception class (with or without a msg) which to raise instead of the LoggedRunError

        Raises:
            LoggedRunException - Catch this explicitly to handle when subprocess.run retval != 0
        """
        if cwd is None:
            # By default we run the command in the current directory's context
            cwd = Path.cwd()

        if info_msg is not None:
            # log.info(info_msg)
            print(info_msg)

        # When using elevate, the logfile can be created in priviledged mode. This creates issues
        # in consecutive runs. More robust to just create a new file.
        if Path(LOG_FILEPATH).exists():
            Path(LOG_FILEPATH).unlink()

        res = None
        with open(LOG_FILEPATH, 'w') as lfh:
            log.debug(
                f'logged_run\n\tcwd:\t{str(cwd)}\n\tcmd:\t{pretty_string_cmd(cmd_lst)}\n\tkwargs:\t{repr(kwargs)}')
            try:
                cmd_lst = [str(e) for e in cmd_lst]  # py3.6.1 ~ Handles PathLike paths as first argument in the list
                res = check_output(cmd_lst, cwd=cwd, universal_newlines=True, encoding='UTF-8', **kwargs)
            except FileNotFoundError as e:
                log.error(
                    f'{__class__.__name__}.{sys._getframe().f_code.co_name}(...) raised [ {e.__class__.__name__}: {e} ]')
        return res

    @staticmethod
    def run_with_retry(cmd_lst: list, cwd=None, retries=1, **kwargs):
        try:
            LoggedCmd.run(cmd_lst, cwd, **kwargs)
        except LoggedRunError:
            if retries > 0:
                LoggedCmd.run_with_retry(cmd_lst, cwd, retries - 1, **kwargs)
            else:
                raise


def pretty_string_cmd(cmd_lst: list):
    """For pretty printing commands and their arguments - concatenate [keyword arg] pairs on the same line"""
    last_was_keyword = False
    lf_fmt = ' \\\n\t\t{}'
    cc_fmt = ' {}'
    new_args = [str(cmd_lst[0])]
    for cmd_arg in cmd_lst[1:]:
        cmd_arg = str(cmd_arg)
        if last_was_keyword and not cmd_arg.startswith('-'):
            last_was_keyword = last_was_secret = False
            narg = cc_fmt.format(cmd_arg)
        else:
            if cmd_arg.startswith('-'):
                last_was_keyword = True
            narg = lf_fmt.format(cmd_arg)
        # print trailing whitespace if arg mystically has one
        # narg = narg if not narg.endswith(' ') else f'{narg}\u2334'
        new_args.append(narg)

    return ''.join(new_args)
