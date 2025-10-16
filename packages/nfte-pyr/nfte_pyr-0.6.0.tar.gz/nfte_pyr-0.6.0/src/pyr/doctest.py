"""% MODULE..

Run doctests in MODULEs and any submodules, recursively.
"""

# TODO: Add options for --quiet, doctest's FAIL_FAST, and maybe more.

import doctest
import sys
from importlib import import_module
from importlib.machinery import all_suffixes as all_module_suffixes
from importlib.resources import files as resource_files
from typing import Iterator

from . import UsageError, print_info, run


class UsageError(UsageError):
    usage = "MODULE.."


all_module_suffixes = all_module_suffixes()


def iter_package_files(package) -> Iterator:
    """Return importlib.resources.files(package).iterdir().

    Returns an empty iterator when package is a non-package module.
    """
    if not hasattr(package, "__path__"):
        return iter(())
    return resource_files(package).iterdir()


def iter_submodule_names(
    package, *, suffixes=all_module_suffixes, dunder=()
) -> Iterator[str]:
    """Return submodule names of package.

    Returns an empty iterator when package is a non-package module.

    Suffixes defaults to importlib.machinery.all_suffixes().

    Double-underscore ("dunder") names are skipped, unless the name is in dunder.
    """
    for path in iter_package_files(package):
        name = path.name
        if not path.is_dir():
            for suffix in suffixes:
                if name.endswith(suffix):
                    name = name[: -len(suffix)]
                    break
            else:
                continue
        if not name.isidentifier():
            continue
        if name.startswith("__") and name.endswith("__") and name not in dunder:
            continue
        yield name


def load_submodules(package) -> Iterator:
    """Find and import submodules of package, recursively."""
    for name in iter_submodule_names(package):
        try:
            m = import_module("." + name, package.__name__)
        except Exception as e:
            print_info(f"skipping {package.__name__}.{name}, {type(e).__name__}: {e}")
            continue
        yield m
        if hasattr(m, "__path__"):
            yield from load_submodules(m)


def main(opts: None, args):
    if not args:
        raise UsageError("missing argument: MODULE")

    modules = []
    for name in args:
        if not name or not all(x.isidentifier() for x in name.split(".")):
            raise UsageError(f"bad module name: {name!r}")
        try:
            m = import_module(name)
        except ImportError as e:
            raise UsageError(e)
        if m not in modules:
            modules.append(m)
            for m in load_submodules(m):
                if m not in modules:
                    modules.append(m)

    total_failed = total_attempted = 0
    results = []
    for m in modules:
        r = doctest.testmod(m)
        if r.attempted:
            total_failed += r.failed
            total_attempted += r.attempted
            results.append((m.__name__, r))

    if not total_attempted:
        raise CommandExit("no tests found", "dataerr")

    if total_failed:
        print()
    prefix_len = max(len(name) for name, _ in results)
    for name, r in results:
        if r.failed:
            msg = f"failed {r.failed} of {r.attempted}"
        else:
            msg = f"passed {r.attempted}"
        print(name.ljust(prefix_len), msg)
    if len(results) > 1:
        if total_failed:
            msg = f"failed {total_failed} of {total_attempted}"
        else:
            msg = f"passed {total_attempted}"
        print("total".rjust(prefix_len), msg)

    return 1 if total_failed else 0


if __name__ == "__main__":
    run(main)
