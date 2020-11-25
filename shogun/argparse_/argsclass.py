import dataclasses
from argparse import ArgumentDefaultsHelpFormatter
from functools import partial
from typing import Any, Dict, Mapping, Optional, get_type_hints

from shogun.records.error import NotARecordClass
from shogun.records.generic import DatargsParams, RecordClass


def make_class(
    cls,
    *args: Any,
    parser_params: Optional[Mapping[str, Any]] = None,
    **kwargs: Any,
):
    try:
        RecordClass.wrap_class(cls)
    except NotARecordClass:
        for key, value in cls.__dict__.items():
            if (
                not isinstance(value, dataclasses.Field)
                or value.default is not dataclasses.MISSING
            ):
                continue
            typ = value.type or get_type_hints(cls)[key]
            if typ is bool:
                value.default = False
        new_cls = dataclasses.dataclass(*args, **kwargs)(cls)
    else:
        new_cls = cls
    new_cls.__datargs_params__ = DatargsParams(
        parser=parser_params,
    )
    return new_cls


def argsclass(
    cls: Optional[type] = None,
    *args: Any,
    description: Optional[str] = None,
    parser_params: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """
    A wrapper around `dataclass` for passing `description` and other params (in `parser_params`)
    to the `ArgumentParser` constructor.
    """
    parser_params = parser_params or {}
    parser_params.setdefault("description", description)
    parser_params.setdefault("formatter_class", ArgumentDefaultsHelpFormatter)

    if cls is None:
        # We're called with parens.
        return partial(
            make_class,
            *args,
            parser_params=parser_params,
            **kwargs,
        )

    return make_class(
        cls,
        *args,
        parser_params=parser_params,
        **kwargs,
    )
