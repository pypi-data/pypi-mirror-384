"""python3 -I -m pyr ..."""

import os
import runpy
import sys

import pyr


def fatal(*message):
    """This allows a different prefix than the current command name."""
    try:
        print("pyr error:", *message, file=sys.stderr, flush=True)
    except Exception:
        pass
    raise SystemExit(70)


class Options:
    command = None
    module = False
    script = False
    path: list[str]

    def __init__(self, opts):
        self.path = []
        for name, value in opts:
            if name == "as":
                if not value:
                    fatal("missing value for option", name)
                self.command = value
            elif name in ("m", "module"):
                if value:
                    fatal("unexpected value for option", name)
                self.module = True
            elif name in ("c", "code"):
                if value:
                    fatal("unexpected value for option", name)
                self.script = True
            elif name in ("p", "path"):
                if value:
                    for x in value.split(os.pathsep):
                        if x:
                            x = os.path.abspath(x)
                            self.path.append(x)
            elif name == "rpath":
                if value:
                    for x in value.split(os.pathsep):
                        if x:
                            self.path.append(x)
            elif name == "signal-tb":
                if value:
                    fatal("unexpected value for option", name)
                pyr.set_raise_signals()
            else:
                fatal("unknown option", name)

    def add_paths(self, target: str | None):
        """Add paths to sys.path from self.path, adjusting relative paths to target."""
        dirname = os.path.dirname(os.path.abspath(target)) if target else None
        for x in self.path:
            if dirname:
                # If x is already absolute, this will be a no-op.
                x = os.path.join(dirname, x)
            elif not os.path.isabs(x):
                fatal("unable to adjust --rpath without a filename TARGET")
            if x not in sys.path:
                sys.path.append(x)

    def parse_args(self, args):
        if not args:
            if self.module:
                fatal("missing module TARGET")
            if self.script:
                fatal("missing filename TARGET")
            self.module = True
            target = "pyr.console"
            if not self.command:
                self.command = target
            return [target]

        target = args[0]
        if self.module:
            self.add_paths(None)
            if not target:
                fatal("module TARGET cannot be empty")
            if not all(x.isidentifier() for x in target.split(".")):
                fatal("invalid module dotted name:", repr(target))
            if not self.command:
                self.command = target
        elif self.script:
            self.add_paths(None)
            if not target:
                fatal("code TARGET cannot be empty")
            self.script = target
        elif target == "-":
            self.add_paths(None)
            if sys.stdin.isatty():
                self.module = True
                args[0] = "pyr.console"
            else:
                self.script = sys.stdin.read() or "pass"
        else:
            self.add_paths(target)
            if not target:
                fatal("filename TARGET cannot be empty")
            if not self.command:
                self.command = target.removeprefix("./")
        return args


def main(opts, args):
    options = Options(opts)
    sys.argv = options.parse_args(args)
    pyr.set_command_name(options.command)
    if options.module:
        if sys.argv[0] == "pyr":
            args = sys.argv[1:]
            opts = pyr.pop_opts(args)
            return main(opts, args)
        try:
            runpy.run_module(sys.argv[0], run_name="__main__", alter_sys=True)
        except ImportError as e:
            if e.name:
                raise
            fatal(e)
    elif options.script:
        args = sys.argv[1:]
        g = {"opts": pyr.pop_opts(args), "args": args, "pyr": pyr}
        exec(options.script, g)
    else:
        runpy.run_path(sys.argv[0], run_name="__main__")


if __name__ == "__main__":
    pyr.run(main, name=False)
