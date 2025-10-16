"""common look and feel for error messages about options and arguments"""

import functools
import inspect
import os
import pathlib
import sys

from . import CommandExit, exit


def exit_unknown_option(name):
    exit("usage", "unknown option " + name)


def exit_missing_value(name):
    exit("usage", "missing value for option " + name)


def exit_unexpected_value(name):
    exit("usage", "unexpected value for option " + name)


def exit_unknown_args():
    exit("usage", "unknown arguments")


def exit_missing_arg(name):
    exit("usage", "missing expected argument " + name)


def exit_missing_args(*names):
    message = "missing expected arguments"
    if names:
        message += " ".join(names)
    exit("usage", message)


def exit_unknown_extra_args(count):
    if count == 1:
        message = "1 unknown extra argument"
    else:
        message = "{} unknown extra arguments".format(count)
    exit("usage", message)


def exit_missing_file(name):
    exit("dataerr", f"missing file: {name}")


def no_opts(main):
    @functools.wraps(main)
    def wrapper(opts: None, args):
        for name, _ in opts:
            exit_unknown_option(name)
        return main(args)

    return wrapper


def no_args(main):
    @functools.wraps(main)
    def wrapper(opts, args: None):
        if args:
            exit_unknown_args()
        return main(opts)

    return wrapper


def no_opts_args(main):
    @functools.wraps(main)
    def wrapper(opts: None, args: None):
        for name, _ in opts:
            exit_unknown_option(name)
        if args:
            exit_unknown_args()
        return main()

    return wrapper


def setattr_from_opts(dest, opts):
    for name, value in opts:
        if not hasattr(dest, name):
            exit_unknown_option(name)
        setattr(dest, name, value)
    return dest


class option:
    def __init__(self, func, *, name=None, short=None, default=None):
        if hasattr(func, "__code__"):
            # prevent common errors
            # possible premature optimization: will these be common? does needing these mean the interface is not obvious enough?
            if not (2 <= func.__code__.co_argcount <= 3):
                raise ValueError(
                    "expected signature of (name, value) or (name, value, prev)"
                )
            if func.__code__.co_varnames[0] == "self":
                raise ValueError("first argument for transform function is not self")
        if short is not None and len(short) != 1:
            raise ValueError("short can only be None or len(short) must be 1")
        if name is not None and len(name) == 1:
            if short is None:
                short = name
                name = None
            elif name == short:
                name = None
        self._transform = func
        self._name = name
        self._short = short
        self._default = default

    def __new__(cls, func=None, *, name=None, short=None, default=None):
        if func is None:
            return lambda func: cls(func, name=name, short=short, default=default)
        return object.__new__(cls)

    def __set_name__(self, owner, name):
        self._key = "_" + name
        if self._short:
            if self._short in owner.__dict__:
                raise ValueError(f"{owner!r} already has attribute {self._short!r}")
            setattr(owner, self._short, self)
        if self._name is None:
            self._name = name.replace("_", "-")
        if self._name != name:
            if self._name in owner.__dict__:
                raise ValueError(f"{owner!r} already has attribute {self._name!r}")
            setattr(owner, self._name, self)

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return getattr(instance, self._key, self._default)

    def __set__(self, instance, value):
        t = self._transform
        if _needs_prev(t):
            prev = getattr(instance, self._key, self._default)
            value = t(self._name, value, prev)
        else:
            value = t(self._name, value)
        setattr(instance, self._key, value)

    def __delete__(self, instance):
        delattr(instance, self._key)

    @staticmethod
    def list_of(function):
        def f(name, value, prev):
            if prev is None:
                prev = []
            if _needs_prev(function):
                prev.append(function(name, value, None))
            else:
                prev.append(function(name, value))
            return prev

        return option(f)


def _add_shortcut(func):
    def shortcut(*, name=None, short=None, default=None):
        return option(func, name=name, short=short, default=default)

    setattr(option, func.__name__, shortcut)
    return func


@_add_shortcut
def any_string(name, value):
    return value or ""


@_add_shortcut
def nonempty_string(name, value):
    if not value:
        exit_missing_value(name)
    return value


@_add_shortcut
def store_true(name, value):
    if value is not None:
        exit_unexpected_value(name)
    return True


@_add_shortcut
def store_false(name, value):
    if value is not None:
        exit_unexpected_value(name)
    return False


@_add_shortcut
def integer(name, value):
    """allow any base 10 integer"""
    if not value:
        exit_missing_value(name)
    if value.startswith("-"):
        rest = value[1:]
    else:
        rest = value
    if any(c not in "0123456789" for c in rest):
        exit("usage", "expected integer for option " + name)
    return int(value)


@_add_shortcut
def nonneg_int(name, value):
    """allow zero and positive base 10 integers"""
    if not value:
        exit_missing_value(name)
    if not all(c in "0123456789" for c in value):
        exit("usage", "expected non-negative integer for option " + name)
    return int(value)


@_add_shortcut
def pos_int(name, value):
    """allow positive base 10 integers"""
    if not value:
        exit_missing_value(name)
    if not all(c in "0123456789" for c in value):
        exit("usage", "expected positive integer for option " + name)
    value = int(value)
    if value == 0:
        exit("usage", "expected positive integer for option " + name)
    return value


@_add_shortcut
def raw_list(name, value, prev):
    """create list of raw values"""
    if prev is None:
        prev = []
    prev.append(value)
    return prev


def list_of(function):
    """create list of function(name, value[, None])"""

    def f(name, value, prev):
        if prev is None:
            prev = []
        if _needs_prev(function):
            prev.append(function(name, value, None))
        else:
            prev.append(function(name, value))
        return prev

    return f


def default(default, function):
    """use default for missing value, otherwise call function

    Implements "--N[=V]" and "-N[V]".  Note difference from "--N=[V]".
    """
    if _needs_prev(function):

        def f(name, value, prev):
            if value is None:
                return default
            return function(name, value, prev)

    else:

        def f(name, value):
            if value is None:
                return default
            return function(name, value)

    return f


def _set_attr(target):
    def decorate(f):
        setattr(target, f.__name__, f)
        return f

    return decorate


def _path_attrs(f):
    @_set_attr(f)
    def absolute(name, value):
        value = f(name, value)
        return value.absolute()

    @_set_attr(f)
    def resolve(name, value):
        value = f(name, value)
        return value.resolve()

    @_set_attr(f)
    def exists(name, value):
        p = f(name, value)
        if not p.exists():
            exit("noinput", "no such path: " + value)
        return value

    return f


@_add_shortcut
@_path_attrs
def path(name, value):
    if not value:
        exit_missing_value(name)
    return pathlib.Path(value)


@_path_attrs
def filename(name, value):
    p = path(name, value)
    if p.exists() and not p.is_file():
        exit("noinput", "not a file: " + value)
    return p


@_add_shortcut
@_path_attrs
def directory(name, value):
    p = path(name, value)
    if p.exists() and not p.is_dir():
        exit("noinput", "not a directory: " + value)
    return p


@_path_attrs
def command(name, value):
    """filename.exists if "/" in value, else search os.environ["PATH"]

    Does NOT check if file is executable.
    """
    if not value:
        exit_missing_value(name)
    if "/" in value:
        return filename.exists(name, value)
    x = os.environ.get("PATH")
    if x is None:
        exit("noinput", "cannot lookup command without PATH: " + value)
    for x in x.split(":"):
        x = pathlib.Path(x, value)
        if x.exists():
            return x
    exit("noinput", "no such command: " + value)


@_add_shortcut
def pure_path(name, value):
    if not value:
        exit_missing_value(name)
    return pathlib.PurePath(value)


def _needs_prev(f):
    return len(inspect.getfullargspec(f).args) != 2


def parse_opts(opts, opt_map, out=None):
    """parse options through functions from opt_map

    If out is None, it becomes a new dict.

    For each (name, raw) in opts, depending on opt_map.get(name) as X:
    * if X is None: exit_unknown_option(name)
    * if X is a tuple of (other, func): out[other] = func(name, raw, out[other])
    * if X is a str: out[X] = opt_map[X](name, raw, out[X])
    * else: out[name] = X(name, raw, out[name])

    For every func call above:
    * if len(inspect.getargspec(func).args) == 2, then the third parameter will be elided

    That functions can use the previous value but not access other options' values is intentional.
    """
    if out is None:
        out = {}
    for name, value in opts:
        f = opt_map.get(name)
        if f is None:
            exit_unknown_option(name)
        if isinstance(f, tuple):
            target, f = f
        elif isinstance(f, str):
            target = f
            f = opt_map[f]
        else:
            target = name
        assert callable(f), f
        if _needs_prev(f):
            out[target] = f(name, value, out[target])
        else:
            out[target] = f(name, value)
    return out
