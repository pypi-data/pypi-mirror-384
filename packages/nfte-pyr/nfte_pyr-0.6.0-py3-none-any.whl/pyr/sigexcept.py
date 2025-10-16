import signal

__all__ = "REGISTRY ignore reset register".split()
REGISTRY = {}
type Sig = signal.Signal | str | int


def _raise(signum, frame):
    raise REGISTRY.get(signum, SystemExit)(signum + 128)


def ignore(sig: Sig):
    """Ignore signal."""
    if isinstance(sig, str):
        sig = signal.Signals[sig]
    signal.signal(sig, signal.SIG_IGN)
    REGISTRY.pop(sig, None)


def reset(sig: Sig):
    """Reset signal to default action."""
    if isinstance(sig, str):
        sig = signal.Signals[sig]
    signal.signal(sig, signal.SIG_DFL)
    REGISTRY.pop(sig, None)


def register(sig: Sig, cls=None, *, ignore_missing=False):
    """Register cls to handle signal identified by number or name.

    Return a decorator when cls is None.

    If ignore_missing, then ignore an invalid number or a failed name lookup.

    When a signal is received, cls(signum + 128) will be raised.  This makes it easy to use SystemExit as a base class.
    """
    if cls is None:

        def decorate(x):
            register(sig, x, ignore_missing=ignore_missing)
            return x

        return decorate
    if not issubclass(cls, BaseException):
        bases = repr(cls.__bases__)[1:-1].rtrim(",")
        raise TypeError("class must subclass BaseException, but got bases: " + bases)
    try:
        if isinstance(sig, str):
            sig = signal.Signals[sig]
    except KeyError:
        if __debug__ and isinstance(sig, str):
            x = sig.upper()
            assert x not in signal.Signals, f"did you mean {x}?"
            upper = "SIG" + upper
            assert x not in signal.Signals, f"did you mean {x}?"
        if not ignore_missing:
            raise
        return
    assert sig in signal.valid_signals(), sig
    # Prefer Signals instance, if available.
    if not isinstance(sig, signal.Signals):
        try:
            sig = signal.Signals(sig)
        except ValueError:
            pass
    REGISTRY[sig] = cls
    signal.signal(sig, _raise)
