import inspect
import io
import sys
from typing import Callable, TypeAlias

from tstring import tstring_logger

_Payload: TypeAlias = Callable[[Callable, list], str]


def _capture_stdout(fn, args) -> str:
    # capture stdout of the call
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        func_return = fn(*args)
        tstring_logger.debug(f"{fn} returned {func_return}")
    finally:
        sys.stdout = old_stdout
    return buf.getvalue().rstrip("\n")

def _capture_return(fn, args) -> str:
    # capture return of the function
    func_return = fn(*args)
    tstring_logger.debug(f"{fn} returned {func_return}")
    return str(func_return)


# noinspection PyUnresolvedReferences
def _process(payload: _Payload, template: Template, ctx: dict[str, object] | None = None) -> str:
    """
    Interpret tstring, passing any !fn calls and arguments to 'payload' for processing
    """
    if ctx is None:
        # grab the caller’s frame
        frame = inspect.currentframe().f_back.f_back
        try:
            # caller’s globals and locals
            ctx = {**frame.f_globals, **frame.f_locals}
        finally:
            # avoid reference cycles
            del frame
    strings = template.strings
    interps = template.interpolations

    out: list[str] = []
    i = 0
    while i < len(interps):
        # 1) static text before this interpolation
        out.append(strings[i])

        interp = interps[i]
        expr = interp.expression
        spec = interp.format_spec

        if spec == "!fn":
            # deferred-eval the callable
            fn = eval(expr, ctx)
            if not callable(fn):
                raise ValueError(f"{expr!r} is not callable")

            # inspect how many fixed args, and if *args is present
            sig = inspect.signature(fn)
            params = sig.parameters.values()
            pos_count = sum(
                1 for p in params
                if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                              inspect.Parameter.POSITIONAL_OR_KEYWORD)
            )
            has_varargs = any(
                p.kind is inspect.Parameter.VAR_POSITIONAL
                for p in params
            )

            # decide how many following interps to consume
            available = len(interps) - (i + 1)
            take = available if has_varargs else min(pos_count, available)

            # eval each of the next `take` expressions
            args = [
                eval(interps[i + j].expression, ctx)
                for j in range(1, take + 1)
            ]
            out.append(payload(fn, args))

            # if func_return is not None:
            #     out.append(str(func_return))
            i += 1 + take
        else:
            # normal interpolation: deferred eval and str()
            val = eval(expr, ctx)
            out.append(str(val))
            i += 1

    # trailing static text
    out.append(strings[-1])

    result = "".join(out)
    return result


def render(template: Template, ctx: dict[str, object] | None = None) -> str:
    """
    Render a PEP 750 t-string, only treating interpolations whose
    format_spec == "!fn" as calls.  Any callable marked !fn will
    consume as many following interpolations as its positional args,
    be invoked, and its stdout captured inline. All other
    interpolations (excluding those consumed as args) and static text
    are rendered in order.
    """
    return _process(_capture_stdout, template, ctx)

def embed(template: Template, ctx: dict[str, object] | None = None) -> str:
    """
    Render a PEP 750 t-string, only treating interpolations whose
    format_spec == "!fn" as calls.  Any callable marked !fn will
    consume as many following interpolations as its positional args,
    be invoked, and its output converted to a str.
    All other interpolations (excluding those consumed as args) and static text
    are rendered in order.
    """
    return _process(_capture_return, template, ctx)
