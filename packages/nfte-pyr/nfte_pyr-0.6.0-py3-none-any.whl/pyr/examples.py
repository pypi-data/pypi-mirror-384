import string
import sys

from pyr import optics, run

_examples = []
SQUOTE_SAFE_CHARS = set(string.ascii_letters + string.digits + "-_=+:,./")


def squote(s):
    if not s:
        return "''"
    if all(c in SQUOTE_SAFE_CHARS for c in s):
        return s
    return "'" + s.replace("'", "'\\''") + "'"


def _example(func=None, name=None):
    if func is None:
        return lambda func: _example(func, name=name)
    _examples.append((name or func.__name__, func))
    return func


@_example
def main(opts: None, args):
    """% [EXAMPLE [ARG..]]

    Run EXAMPLE or list.
    """
    if not args:
        args = ["list"]
    name = args.pop(0)
    for x, f in _examples:
        if x == name:
            break
    else:
        optics.exit_unknown_args()
    run(f, name=name, args=args)


@_example(name="list")
def ls(opts, args: None):
    """%

    List examples.

    Options:
        --sort          sort examples
    -s  --short         show help synopsis only
    """
    opt_map = {
        "sort": optics.store_true,
        "short": optics.store_true,
        "s": "short",
    }
    opts = optics.parse_opts(opts, opt_map)
    examples = _examples
    if opts.get("sort"):
        examples = sorted(examples)
    for name, f in examples:
        doc = f.__doc__
        if not doc:
            print(name)
        else:
            doc = doc.strip().splitlines()
            first = doc[0]
            assert first.startswith("%"), repr(first)
            if first == "%" or first.startswith("% "):
                first = name + first[1:]
            print(first)
            if not opts.get("short") and len(doc) > 1:
                assert doc[1] == "", (name, doc[1])
                del doc[0:2]
                if sys.version_info[:2] >= (3, 13):
                    # 3.13 removes common leading indentation.
                    # See: https://docs.python.org/3/whatsnew/3.13.html#other-language-changes
                    doc = [("    " + x) if x else "" for x in doc]
                print("\n".join(doc))


@_example
def show(opts, args):
    """% [OPT..] [ARG..]

    Show parsed opts and args.
    """
    print(f"{opts = }")
    print(f"{args = }")


@_example
def showargs(opts, args):
    """% [OPT..] [ARG..]

    Show options and arguments.
    """
    for name, value in opts:
        if value is None:
            s = f"--{name}"
        else:
            r = repr(value)
            if value and r[1:-1] == value.strip():
                r = value
            s = f"--{name}={r}"
        print(s)
    width = min(3, len(repr(len(args))))
    for n, x in enumerate(args, start=1):
        r = repr(x)
        if x and r[1:-1] == x.strip():
            r = x
        print(f"{n:{width}} {r}")


@_example
def reconstruct(opts, args):
    """% [OPT..] [ARG..]

    Reconstruct command line.
    """
    output = ["%"]
    short = []

    def drain_short():
        if short:
            if len(short) == 1:
                output.append("-" + squote(short[0]))
            else:
                output.append("-+" + squote("".join(short)))
            del short[:]

    def append(x):
        drain_short()
        output.append(squote(x))

    for n, v in opts:
        if len(n) == 1:
            if not v:
                short.append(n)
            else:
                append("-" + n + v)
        elif v is None:
            append("--" + n)
        else:
            append(f"--{n}={v}")
    drain_short()
    if args:
        if args[0].startswith("-") and args[0] != "-":
            output.append("--")
        output.extend(squote(x) for x in args)
    print(" ".join(output))


@_example
def head(opts, args):
    """% [FILE..]

    Options:
    -nL --lines=L       show first L lines (default 10)
    -#                  --lines=# (where # >= 0)
    """
    opt_map = {
        "n": "lines",
        "lines": optics.nonneg_int,
    }

    def shortcut_int(name, value):
        return optics.nonneg_int(name, name + (value or ""))

    for x in "0123456789":
        opt_map[x] = ("lines", shortcut_int)
    lines = optics.parse_opts(opts, opt_map).get("lines", 10)

    if not args:
        args = ["-"]
    for filename in args:
        close = False
        try:
            if filename == "-":
                f = sys.stdin
            else:
                f = open(filename)
                close = True
            if len(args) > 1:
                print("==> {} <==".format(filename))
            if lines == 0:
                continue
            for n, line in enumerate(f, start=1):
                sys.stdout.write(line)
                if n == lines:
                    break
        finally:
            if close:
                f.close()


if __name__ == "__main__":
    run(main)
