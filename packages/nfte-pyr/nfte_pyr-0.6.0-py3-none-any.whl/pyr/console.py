import types

import pyr

try:
    from _pyrepl.main import interactive_console
except ImportError:
    import code

    def main(opts, args):
        code.interact(local=locals(), banner="", exitmsg="")

else:

    def main(opts, args):
        main = types.ModuleType("__main__")
        main.__dict__["opts"] = opts
        main.__dict__["args"] = args
        interactive_console(main, quiet=True)


if __name__ == "__main__":
    pyr.run(main)
