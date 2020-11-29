import collections
import typing

BUILTINS_MAPPING = {
    typing.ByteString: bytes,
    typing.Dict: dict,
    typing.List: list,
    typing.Set: set,
    typing.Tuple: tuple,
}

GenericCls = type(typing.List)
UnionCls = type(typing.Union)

IS_PYTHON_38 = hasattr(typing, "get_origin")
IS_PYTHON_37 = hasattr(typing.List, "_special")


def _convert_to_builtin(type_):
    if type_ in BUILTINS_MAPPING:
        return BUILTINS_MAPPING[type_]
    return type_


def _found_args_from__args__(type_):
    found_args = type_.__args__
    if (
        get_generic_origin(type_) is collections.abc.Callable
        and found_args[0] is not Ellipsis
    ):
        found_args = (list(found_args[:-1]), found_args[-1])
    return found_args


def get_generic_origin(type_):
    origin = None
    if IS_PYTHON_38:
        origin = typing.get_origin(type_)
    elif IS_PYTHON_37:
        if isinstance(type_, GenericCls) and not type_._special:
            origin = type_.__origin__
        elif hasattr(type_, "_special") and type_._special:
            origin = type_
        elif type_ is typing.Generic:
            origin = typing.Generic
    else:  # python 3.6
        if isinstance(type_, GenericCls):
            origin = type_.__origin__
            if origin is None:
                origin = type_
        elif isinstance(type_, UnionCls):
            origin = type_.__origin__
        elif type_ is typing.Generic:
            origin = typing.Generic

    return _convert_to_builtin(origin)


def get_generic_args(type_):
    found_args = tuple()

    if IS_PYTHON_38:
        found_args = typing.get_args(type_)
    elif IS_PYTHON_37:
        if isinstance(type_, GenericCls) and not type_._special:
            found_args = _found_args_from__args__(type_)
    else:  # python 3.6
        if isinstance(type_, (GenericCls, UnionCls)):
            found_args = _found_args_from__args__(type_)
    return tuple() if found_args is None else found_args
