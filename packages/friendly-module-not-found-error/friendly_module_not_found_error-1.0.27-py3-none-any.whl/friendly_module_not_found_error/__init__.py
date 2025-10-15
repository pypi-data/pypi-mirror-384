import sys
import traceback
import importlib
import runpy

try:
    import idlelib.run

    _has_idlelib = True
except:
    _has_idlelib = False
from .traceback_change import (original_traceback_TracebackException_init,
                               original_TracebackException_format_exception_only,
                               new_init, new_format_exception_ony)
from .runpy_change import original_runpy_get_module_details, _get_module_details
from .idlelib_all_change import original_idlelib_run_print_exception, print_exception
from .importlib_change import original_find_and_load_unlocked, _find_and_load_unlocked
from .handle_path import scan_dir, find_in_path

major, minor = sys.version_info[:2]
importlib._bootstrap.BuiltinImporter.__find__ = staticmethod(
    lambda name=None: (
        sorted(sys.builtin_module_names) if not name else []
    )
)
original_sys_excepthook = sys.__excepthook__


def _excepthook(exc_type, exc_value, exc_tb):
    try:
        tb_exception = traceback.TracebackException(
            exc_type, exc_value, exc_tb, capture_locals=False
        )
        if minor < 13:
            for line in tb_exception.format():
                sys.stderr.write(line)
        else:
            for line in tb_exception.format(colorize=True):
                sys.stderr.write(line)
    except:
        traceback.print_exception(exc_type, exc_value, exc_tb, file=sys.stderr)


sys.excepthook = sys.__excepthook__ = _excepthook


def unchange(full_recovery=False):
    traceback.TracebackException.__init__ = original_traceback_TracebackException_init
    traceback.TracebackException.format_exception_only = original_TracebackException_format_exception_only
    runpy._get_module_details = original_runpy_get_module_details
    if _has_idlelib:
        idlelib.run.print_exception = original_idlelib_run_print_exception
    importlib._bootstrap._find_and_load_unlocked = original_find_and_load_unlocked
    if sys.excepthook is sys.__excepthook__ or full_recovery:
        sys.excepthook = sys.__excepthook__ = original_sys_excepthook
    else:
        sys.__excepthook__ = original_sys_excepthook


def rechange(full_rechange=False):
    traceback.TracebackException.__init__ = new_init
    traceback.TracebackException.format_exception_only = new_format_exception_ony
    runpy._get_module_details = _get_module_details
    if _has_idlelib:
        idlelib.run.print_exception = print_exception
    importlib._bootstrap._find_and_load_unlocked = _find_and_load_unlocked
    if sys.excepthook is sys.__excepthook__ or full_rechange:
        sys.excepthook = sys.__excepthook__ = _excepthook
    else:
        sys.__excepthook__ = _excepthook
