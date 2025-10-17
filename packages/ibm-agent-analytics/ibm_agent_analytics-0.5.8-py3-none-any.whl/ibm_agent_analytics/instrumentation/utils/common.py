import inspect
import json
from pathlib import Path

from ibm_agent_analytics_common.interfaces.runnable import Runnable


def get_code_id(func):
    try:
        actual_func = inspect.unwrap(func)  # handle partials and decorators
        code = actual_func.__code__
        filename = Path(code.co_filename).name
        lineno = code.co_firstlineno
        module = getattr(actual_func, "__module__", "<unknown>")
        qualname = getattr(actual_func, "__qualname__", repr(actual_func))
        return f"{filename}:{lineno}:{module}:{qualname}"
    except Exception:
        return "<unknown>:<unknown>:<unknown>:<unknown>"


def _get_runnable_from_func(func) -> Runnable:
    sig = inspect.signature(func)
    input_schema = {
        name: {
            "annotation": str(param.annotation) if param.annotation != inspect.Parameter.empty else None,
            "default": str(param.default) if param.default != inspect.Parameter.empty else None,
            "kind": param.kind.name,
        }
        for name, param in sig.parameters.items()
    }

    output_schema = (
        str(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else None
    )
    runnable = Runnable(
        code_id=get_code_id(func),
        input_schema=json.dumps(input_schema),
        output_schema=output_schema,
    )
    return runnable
