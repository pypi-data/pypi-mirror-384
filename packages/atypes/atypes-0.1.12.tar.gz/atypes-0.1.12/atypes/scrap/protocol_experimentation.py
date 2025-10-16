"""
Experiences in protocols
"""
# https://www.python.org/dev/peps/pep-0560/
from typing import Protocol, Callable, runtime_checkable, Any, Protocol
from functools import wraps
from types import LambdaType
from i2 import Sig


def mk_function_protocol(name, call_method):
    protocol_cls = type(
        name,
        (Protocol,),
        {
            '__call__': call_method,
            '__reduce__': (mk_function_protocol, (name, call_method)),
            '__module__': __name__,
        },
    )
    return protocol_cls


def to_protocol(template, name=None, runtime_checking=True):
    # if isinstance(template, LambdaType):  # detects normal functions too, so no good
    #     template_sig = Sig(template)
    #     # use defaults of template as annotations
    #     sig = Sig(template_sig.names).ch_annotations(**template_sig.defaults)
    if not isinstance(template, Sig):
        sig = Sig(template)
    else:
        print('sdfdffd')
        sig = template
    name = name or sig.name
    assert name is not None, f'Your protocol needs a name'
    sig_with_self = Sig('self' + sig, return_annotation=sig.return_annotation)

    function_with_template_signature = sig_with_self(lambda: None)
    # protocol_cls = type(name, (Protocol,), {'__call__': function_with_template_signature})
    protocol_cls = mk_function_protocol(name, function_with_template_signature)
    if runtime_checking:
        return runtime_checkable(protocol_cls)
    else:
        return protocol_cls

    # return protocol_cls


# class IdxUpdaterProtocol(Protocol):
#     def __call__(self, idx: Any, obj: Any) -> Any:
#         pass
#
#
# func: IdxUpdaterProtocol
#
#
# def func(a, b, c):
#     pass
#
#
# def bar_():
#     return 1
#
#
# def bar(f: IdxUpdaterProtocol = lambda x: x):
#     return f
