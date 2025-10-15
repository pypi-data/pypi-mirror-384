# To make the exception message valid on idle
import sys
import traceback

major, minor = sys.version_info[:2]


def get_message_lines(typ, exc, tb):
    """Return line composing the exception message."""
    if typ in (AttributeError, NameError):
        tb_exception = traceback.TracebackException(
            typ, exc, tb, capture_locals=False
        )
        return list(tb_exception.format_exception_only())
    else:
        return traceback.format_exception_only(typ, exc)


try:
    import idlelib.run
    from idlelib.run import flush_stdout, cleanup_traceback

    original_idlelib_run_print_exception = idlelib.run.print_exception
except:
    print_exception = original_idlelib_run_print_exception = None
else:
    def print_exception():
        import linecache
        linecache.checkcache()
        flush_stdout()
        efile = sys.stderr
        typ, val, tb = excinfo = sys.exc_info()
        sys.last_type, sys.last_value, sys.last_traceback = excinfo
        sys.last_exc = val
        seen = set()
        exclude = ("run.py", "rpc.py", "threading.py", "queue.py",
                   "debugger_r.py", "bdb.py", "friendly_module_not_found_error")

        def print_exc_group(typ, exc, tb, prefix=""):
            prefix2 = prefix or "  "
            if tb:
                if not prefix:
                    print("  + Exception Group Traceback (most recent call last):", file=efile)
                else:
                    print(f"{prefix}| Exception Group Traceback (most recent call last):", file=efile)
                tbe = traceback.extract_tb(tb)
                cleanup_traceback(tbe, exclude)
                for line in traceback.format_list(tbe):
                    for subline in line.rstrip().splitlines():
                        print(f"{prefix2}| {subline}", file=efile)
            lines = get_message_lines(typ, exc, tb)
            for line in lines:
                print(f"{prefix2}| {line}", end="", file=efile)
            for i, sub in enumerate(exc.exceptions, 1):
                if i == 1:
                    first_line_pre = "+-"
                else:
                    first_line_pre = "  "
                print(f"{prefix2}{first_line_pre}+---------------- {i} ----------------", file=efile)
                if id(sub) not in seen:
                    if not prefix:
                        print_exc(type(sub), sub, sub.__traceback__, "    ")
                    else:
                        print_exc(type(sub), sub, sub.__traceback__, prefix + "  ")
                    need_print_underline = not isinstance(sub, BaseExceptionGroup)
                else:
                    print(f"{prefix2}  | <exception {type(sub).__name__} has printed>")
                    need_print_underline = True
                need_print_underline *= (i == len(exc.exceptions))
                if need_print_underline:
                    print(f"{prefix2}  +------------------------------------", file=efile)

        def print_exc(typ, exc, tb, prefix=""):
            seen.add(id(exc))
            context = exc.__context__
            cause = exc.__cause__
            prefix2 = f"{prefix}| " if prefix else ""
            if cause is not None and id(cause) not in seen:
                print_exc(type(cause), cause, cause.__traceback__, prefix)
                print(f"{prefix2}\n{prefix2}The above exception was the direct cause "
                      f"of the following exception:\n{prefix2}", file=efile)
            elif (context is not None and
                  not exc.__suppress_context__ and
                  id(context) not in seen):
                print_exc(type(context), context, context.__traceback__, prefix)
                print(f"{prefix2}\n{prefix2}During handling of the above exception, "
                      f"another exception occurred:\n{prefix2}", file=efile)
            if minor >= 11 and isinstance(exc, BaseExceptionGroup):
                print_exc_group(typ, exc, tb, prefix=prefix)
            else:
                if tb:
                    print(f"{prefix2}Traceback (most recent call last):", file=efile)
                    tbe = traceback.extract_tb(tb)
                    cleanup_traceback(tbe, exclude)
                    if prefix:
                        for line in traceback.format_list(tbe):
                            for subline in line.rstrip().splitlines():
                                print(f"{prefix}| {subline}", file=efile)
                    else:
                        traceback.print_list(tbe, file=efile)
                lines = get_message_lines(typ, exc, tb)
                for line in lines:
                    print(f"{prefix2}{line}", end="", file=efile)

        print_exc(typ, val, tb)


    idlelib.run.print_exception = print_exception
