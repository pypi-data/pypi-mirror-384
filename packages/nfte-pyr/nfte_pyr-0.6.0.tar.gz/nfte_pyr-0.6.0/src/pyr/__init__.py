import importlib
import inspect
import signal
import sys
from types import ModuleType

from . import sigexcept


@lambda x: x()
class __all__(list[str]):
    def __call__(self, item):
        self.append(item.__name__)
        return item


@__all__
def add_lazy_import(package: str | ModuleType):
    """Add lazy import to package.

    If the package already has a __getattr__, then this does nothing.

    This is designed to be used in two ways:
    * add_lazy_import(__name__)  # Applied to the current package.
    * import X; add_lazy_import(X)
    """
    if isinstance(package, str):
        package_name = package
        package = sys.modules[package_name]
    else:
        package_name = package.__name__
        assert package is sys.modules[package_name], package
    if hasattr(package, "__getattr__"):
        return

    def __getattr__(name):
        try:
            module = importlib.import_module("." + name, package_name)
        except ImportError as e:
            raise AttributeError(name) from e
        return module

    package.__getattr__ = __getattr__


class EmptyType:
    def __bool__(self):
        return False

    def __repr__(self):
        return "<EMPTY>"


EMPTY = EmptyType()


@__all__
def flush_or_close(stream, suppress=False):
    """Flush stream, maybe close it, and handle exceptions.

    If flushing raises, then close the stream, ignoring any exception on close, and if suppress, ignore the flush exception too.

    If the stream is None or already closed, then do nothing.

    See: https://github.com/python/cpython/issues/55589 (migrated from https://bugs.python.org/issue11380)
    """
    try:
        if stream and not stream.closed:
            stream.flush()
    except:
        try:
            stream.close()
        except:
            pass
        if not suppress:
            raise


@__all__
def try_print(*args, sep=" ", end="\n", file=None, flush=False, suppress=True) -> bool:
    """Print while suppressing exceptions.

    Returns whether successful.  Note when flush=False, there can still be an error later when flushing.

    Only exceptions derived from Exception are suppressed, not BaseException.
    """
    try:
        print(*args, sep=sep, end=end, file=file, flush=flush)
    except Exception:
        if suppress:
            return False
        raise
    return True


@__all__
def iter_pop_opts(args: list[str], start=0, end=None):
    """Yield (name, value) options, then modify args in-place."""
    start, end, _ = slice(start, end, 1).indices(len(args))
    for n in range(start, end, 1):
        x = args[n]
        if x == "--":
            del args[start : n + 1]
            break
        elif x.startswith("-") and len(x) != 1:
            if x.startswith("--"):
                name, sep, value = x[2:].partition("=")
                if not name:
                    exit("usage", "missing option name")
                if not sep:
                    value = None
            else:
                name, value = x[1], x[2:] or None
            if any(x in _BAD_NAME_CHARS for x in name):
                exit("usage", "bad option name")
            if name == "+":
                if value is not None:
                    for name in value:
                        if name == "+":
                            continue
                        if any(x in _BAD_NAME_CHARS for x in name):
                            exit("usage", "bad option name")
                        yield name, None
            else:
                yield name, value
        else:
            del args[start:n]
            break
    else:
        del args[start:end]


@__all__
def pop_opts(args, start=0, end=None):
    """Return list(iter_pop_opts(args, start, end)).

    >>> args = ["-x", "-y42", "-+ab", "--c=", "--d", "-", "z"]
    >>> pop_opts(args)
    [('x', None), ('y', '42'), ('a', None), ('b', None), ('c', ''), ('d', None)]
    >>> args
    ['-', 'z']

    >>> args = ["first", "-24", "third"]
    >>> pop_opts(args, start=1)
    [('2', '4')]
    >>> args
    ['first', 'third']

    >>> args = ["first", "-2", "-3"]
    >>> pop_opts(args, start=1, end=-1)
    [('2', None)]
    >>> args
    ['first', '-3']
    """
    return list(iter_pop_opts(args, start, end))


# Above code is relatively self-contained.
add_lazy_import(__name__)
EXIT_CODES = {
    "success": 0,
    "other": 1,
    # FreeBSD: man sysexits
    "usage": 64,
    "dataerr": 65,
    "noinput": 66,
    "nouser": 67,
    "nohost": 68,
    "unavailable": 69,
    "unknown": 69,
    "internal": 70,
    "to" "do": 70,
    "os": 71,
    "osfile": 72,
    "cantcreat": 73,
    "cantcreate": 73,
    "io": 74,
    "tempfail": 75,
    "protocol": 76,
    "noperm": 77,
    "config": 78,
}
_SIGNAL_RERAISE = False
_BAD_NAME_CHARS = set(" !\"#$%&'()*,/;<=>?@[\\]^`{|}~")
_PREFIX_ERROR = "error: "
_PREFIX_INFO = None  # None used to detect initial unset value.


@__all__
@sigexcept.register("SIGABRT", ignore_missing=True)
@sigexcept.register("SIGHUP", ignore_missing=True)
@sigexcept.register("SIGQUIT", ignore_missing=True)
@sigexcept.register("SIGTERM", ignore_missing=True)
@sigexcept.register("SIGXCPU", ignore_missing=True)
@sigexcept.register("SIGXFSZ", ignore_missing=True)
class SignalExit(SystemExit):
    pass


@__all__
class SignalException(Exception):
    @property
    def code(self):
        return self.args[0] if self.args else EXIT_CODES.get("internal", 70)


@__all__
@sigexcept.register("SIGALRM")
class AlarmSignal(SignalException):
    pass


@__all__
class CommandExit(SystemExit):
    message: str | None
    code: str | int | None

    def __init__(self, message=None, code=None):
        if not isinstance(code, int):
            code = EXIT_CODES.get(code)
            if code is None:
                code = EXIT_CODES.get("unknown", 69)
            assert isinstance(code, int), code
        if not code:
            message = None
        super().__init__(code, message)
        self.message = message
        self.code = code


def exit(code, message=None):
    raise CommandExit(message, code)


@__all__
class UsageError(CommandExit):
    """Command usage error.

    To avoid specifying the usage argument multiple times when it doesn't change, create a subclass with a "usage" class attribute:

    >>> class MyUsage(UsageError):
    ...     usage = "[EXAMPLE]"
    >>> e = MyUsage("message")

    >>> set_command_name(None)
    >>> print_usage(e, file=sys.stdout)
    error: message
    usage: % [EXAMPLE]

    >>> set_command_name("test")
    >>> print_usage(e, file=sys.stdout)
    test error: message
    usage: test [EXAMPLE]
    >>> print_usage(e, message=None, file=sys.stdout)
    usage: test [EXAMPLE]
    """

    usage = None

    def __init__(self, message=None, usage=None):
        CommandExit.__init__(self, message, EXIT_CODES.get("usage", 64))
        if usage:  # Default to class attribute.
            self.usage = usage

    def __str__(self):
        return self.message


@__all__
def apply_annotations(target, opts: list, args: list) -> tuple[list | None]:
    """Using target's None annotations, return a maybe-empty tuple for opts and args.

    >>> def neither  (): ...
    >>> def neither2 (opts: None, args: None): ...
    >>> def args_only(opts: None, args      ): ...
    >>> def opts_only(opts      , args: None): ...
    >>> def both     (opts      , args      ): ...

    >>> apply_annotations(neither, [], [])
    ()
    >>> apply_annotations(neither2, [], [])
    (None, None)

    >>> apply_annotations(args_only, [], ["args"])
    (None, ['args'])
    >>> apply_annotations(opts_only, [("opt", None)], [])
    ([('opt', None)], None)

    >>> apply_annotations(both, [("opt", None)], ["args"])
    ([('opt', None)], ['args'])

    >>> apply_annotations(neither, [], ["args"])
    Traceback (most recent call last):
        ...
    pyr.UsageError: unexpected arguments

    * If a list is non-empty and the corresponding annotation is None, raise UsageError.
    * Keyword-only parameters are ignored.
    * At most 2 parameters are inspected, though later calling the function will cause an error if additional parameters do not have a default.
    * If the first parameter is variable (VAR_POSITIONAL), then it is also used as the second parameter.
    * Only a None annotation is significant.
        * "None" (a string annotation) is treated the same as None to handle __future__.annotations until it is removed sometime after Python 3.13; see PEP 749.
    * Parameter names are ignored, even though they have consistent names in examples.
    """
    anno2 = []
    for x in inspect.signature(target, follow_wrapped=False).parameters.values():
        if x.kind is x.VAR_POSITIONAL:
            while len(anno2) < 2:
                anno2.append(x.annotation)
            break
        if x.kind in (x.POSITIONAL_ONLY, x.POSITIONAL_OR_KEYWORD):
            anno2.append(x.annotation)
            if len(anno2) == 2:
                break

    if len(anno2) == 1:
        raise TypeError("target must accept 0, 2, or more positional parameters")

    if not anno2:
        if opts:
            raise UsageError("unexpected options")
        if args:
            raise UsageError("unexpected arguments")
        return ()

    if anno2[0] in (None, "None"):
        if opts:
            raise UsageError("unexpected options")
        opts = None
    if anno2[1] in (None, "None"):
        if args:
            raise UsageError("unexpected arguments")
        args = None
    return opts, args


@__all__
def print_error(
    *args, command=EMPTY, sep=" ", end="\n", file=None, flush=True, suppress=True
):
    """Print command error prefix and args to file (default sys.stderr).

    * If suppress, then ignore any Exception.
    """
    if not args:
        return
    if file is None:
        file = sys.stderr
    try:
        if command is EMPTY:
            command = _PREFIX_ERROR
        else:
            command = f"{command} error: "
        print(_PREFIX_ERROR, end="", file=file)
        print(*args, sep=sep, end=end, file=file, flush=flush)
    except Exception:
        if not suppress:
            raise


@__all__
def print_info(
    *args, command=EMPTY, sep=" ", end="\n", file=None, flush=False, suppress=True
):
    """Print command prefix and args to file (default sys.stderr).

    * If suppress, then ignore any Exception.
    """
    if not args:
        return
    if file is None:
        file = sys.stderr
    try:
        if command is EMPTY:
            command = _PREFIX_INFO
        if command:
            print(command, end="", file=file, flush=False)
        print(*args, sep=sep, end=end, file=file, flush=flush)
    except Exception:
        if not suppress:
            raise


@__all__
def print_usage(
    usage: str | UsageError,
    message=EMPTY,
    command=EMPTY,
    *,
    file=None,
    flush=True,
    suppress=True,
):
    """Combine print_error with a usage line.

    >>> set_command_name("command")
    >>> print_usage("arguments", file=sys.stdout)
    usage: command arguments
    >>> print_usage("arguments", "message", file=sys.stdout)
    command error: message
    usage: command arguments
    >>> print_usage("arguments", "message", "other", file=sys.stdout)
    command error: message
    usage: other arguments
    """
    if isinstance(usage, UsageError):
        if message is EMPTY:
            message = usage.message
        usage = usage.usage

    if command is EMPTY:
        command = _PREFIX_INFO[:-2] if _PREFIX_INFO else "%"
    elif command is None:
        command = ""
    usage = f"usage: {command} {usage}"

    if message:
        print_error(f"{message}\n{usage}", file=file, flush=flush, suppress=suppress)
    else:
        try_print(usage, file=file or sys.stderr, flush=flush, suppress=suppress)


@__all__
def set_command_name(name: str | None):
    """Set command name for print_error, print_info, and print_usage.

    If not name, then reset to default prefixes: "error: ", "".
    """
    global _PREFIX_ERROR, _PREFIX_INFO, _USAGE
    if name:
        _PREFIX_ERROR = name + " error: "
        _PREFIX_INFO = name + ": "
    else:
        _PREFIX_ERROR = "error: "
        _PREFIX_INFO = ""


def _push_state(name):
    state = _PREFIX_ERROR, _PREFIX_INFO
    if name:
        set_command_name(name)
    elif _PREFIX_INFO is None:
        # Not previously set; calculate from interpreter state.
        spec = getattr(sys.modules.get("__main__"), "__spec__", None)
        if not spec:
            name = sys.argv[0].removeprefix("./")
        elif spec.name == "__main__" or spec.name.endswith(".__main__"):
            name = spec.parent
        else:
            name = spec.name
        set_command_name(name)
    return state


def _restore_state(state):
    global _PREFIX_ERROR, _PREFIX_INFO
    _PREFIX_ERROR, _PREFIX_INFO = state


@__all__
def set_raise_signals():
    """Re-raise signal exceptions instead of translating to SystemExit.

    These exceptions are KeyboardInterrupt, BrokenPipeError, pyr.SignalExit, pyr.SignalException, and any derived classes.

    This is a one-way gate so that exceptions propagate if run is nested.  However, if this is unset before a nested run(main), then it will be restored if main exits normally.

    Also see submodule pyr.sigexcept.
    """
    global _SIGNAL_RERAISE
    _SIGNAL_RERAISE = True


@__all__
def run(main, *, args=None, name=None) -> None:
    """Run main(opts, args) after parsing options from args.

    * If args is None, it defaults to sys.argv[1:].
    * See apply_annotations for alternative ways main is called.
    * See set_command_name for how name is used.

    An exception from main will either be translated to SystemExit or re-raised.  If main returns a true-ish value, then SystemExit will be raised.
    """
    # Implementing a stack of global state allows nested calls with a simple interface for the common case (without nested calls).
    global _SIGNAL_RERAISE
    saved_signal_reraise = _SIGNAL_RERAISE
    saved_state = None
    try:
        saved_state = _push_state(name)
        args = sys.argv[1:] if args is None else list(args)
        args = apply_annotations(main, pop_opts(args), args)
        try:
            error = main(*args)
            if error:
                raise SystemExit(error)
        except:
            flush_or_close(sys.stdout, suppress=True)
            flush_or_close(sys.stderr, suppress=True)
            raise
        else:
            flush_or_close(sys.stdout)
            flush_or_close(sys.stderr)
    except UsageError as e:
        e.print_usage()
        raise SystemExit(e.code)
    except CommandExit as e:
        if e.message:
            print_error(e.message)
        raise SystemExit(e.code)
    except KeyboardInterrupt:
        if _SIGNAL_RERAISE:
            raise
        raise SystemExit(128 + signal.SIGINT)
    except BrokenPipeError as e:
        if _SIGNAL_RERAISE:
            raise
        raise SystemExit(128 + signal.SIGPIPE)
    except (SignalExit, SignalException) as e:
        if _SIGNAL_RERAISE:
            raise
        raise SystemExit(e.code)
    except SystemExit as e:
        if not isinstance(e.code, int) and e.code is not None:
            print_error(e.code)
            e.code = EXIT_CODES.get("unknown", 69)
        raise
    finally:
        if saved_state:
            _restore_state(saved_state)
    _SIGNAL_RERAISE = saved_signal_reraise
