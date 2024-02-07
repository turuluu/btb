from btb.commands import LoggedCmd, log
from pathlib import Path
import os
import stat
import copy
import pprint


def file_permissions(f):
    if f.exists():
        return stat.filemode(os.stat(f).st_mode)
    else:
        log.debug(f'Tried to check permissions for {f} - file not found')


#
# def get_filepath(filepattern):
#     """with a pattern, search recursively and get full/absolute path to the (first) file if found (otherwise None)"""
#     filepath = None
#     for p in c.cwd.rglob(filepattern):
#         filepath = p.absolute()
#         break
#     return filepath
#
#
# def has_file(filepattern, recursive=True):
#     """Searches for file or dir and returns True if it was found in the working directory"""
#     if recursive:
#         files = list(c.cwd.rglob(filepattern))
#     else:
#         files = list(c.cwd.glob(filepattern))
#     log.debug(f'found files: {repr(files)}')
#
#     return len(files) > 0
def format_locals(lcls):
    _locals = copy.deepcopy(lcls)

    return pprint.pformat(_locals, width=120)


def safe_copy(src: Path, dst: Path):
    """python's shutil.copytree and copyfile don't work on windows appropriately resulting
    in obscure permissions errors, rendering some artefacts broken
    so that they are not verified as wrapped after the copy process, etc. This doesn't
    happen with system level copy command thus it's the reasonable mitigation step

    On python reference docs ( https://docs.python.org/3/library/shutil.html ):
    > Even the higher-level file copying functions (shutil.copy(), shutil.copy2()) cannot copy all file metadata.
    """
    LoggedCmd.run(['cp', src, dst])


def safe_copytree(src: Path, dst: Path):
    """python's shutil.copytree and copyfile don't work on windows appropriately resulting
    in obscure permissions errors, rendering some artefacts broken
    so that they are not verified as wrapped after the copy process, etc. This doesn't
    happen with system level copy command thus it's the reasonable mitigation step

    On python reference docs ( https://docs.python.org/3/library/shutil.html ):
    > Even the higher-level file copying functions (shutil.copy(), shutil.copy2()) cannot copy all file metadata.
    """
    LoggedCmd.run(['cp', '-R', src, dst])


def safe_mkdir(p: Path, *, mode=0o755, **kwargs):
    """python's mkdir seems to not respect the mode it's given. This uses chmod via
    a shell command after creating the dir.

    mode and kwargs are passed to Path.mkdir(mode=0o755, parents=False, exist_ok=False)
    """
    p = p if isinstance(p, Path) else Path(p)
    p = p if p.is_absolute() else p.absolute()
    p.mkdir(mode=mode, **kwargs)
    log.debug('Created dir [ %s ]: %s', file_permissions(p), p)
    chmod(p, mode)


def chmod(p: Path, mode=0o755, recursive=True):
    p = p if isinstance(p, Path) else Path(p)
    p = p if p.is_absolute() else p.absolute()
    if recursive:
        LoggedCmd.run(['chmod', '-R', '{:o}'.format(mode), os.fspath(p)])
    else:
        LoggedCmd.run(['chmod', '{:o}'.format(mode), os.fspath(p)])

    log.debug('chmod validation: permissions are now [ %s ] for %s', file_permissions(p), p)


def mac_force_access_all(path, is_executable=False):
    p = Path(path)
    for file_dir in p.rglob('*'):
        if file_dir.is_dir() or is_executable:
            chmod(file_dir, 0o755, False)
        else:
            chmod(file_dir, 0o644, False)
