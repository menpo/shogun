# Initial implementation courtesy of https://github.com/roee30/datargs
# under the MIT license - maintained in this repository at LICENSE-datargs
# noinspection PyUnresolvedReferences
"""
Declerative, type safe `argparse` parsers.

>>> @dataclass
... class Args:
...     just_a_string: str
...     num: int
...     store_true: bool = False
...     store_false: bool = True
>>> args = parse(Args, ["--just-a-string", "STRING", "--num", "0", "--store-true", "--store-false"])
>>> args
Args(just_a_string='STRING', num=0, store_true=True, store_false=False)

Pycharm correctly infers that `args` is of type `Args`.
Trying to access a non-existent member is a type error:
>>> args.nope  # doctest: +SKIP
Pycharm says: Unresolved attribute reference 'nope' for class 'Args'

A flag with no defaults is assumed to be False by default:
>>> @dataclass
... class Args:
...     no_default: bool
>>> parse(Args, [])
Args(no_default=False)

Enums are supported. They should be specified by name on the command line:
>>> class FoodEnum(Enum):
...     gnocchi = 0
...     kimchi = 1
>>> @dataclass
... class Args:
...     food: FoodEnum
>>> parse(Args, ["--food", "kimchi"])
Args(food=<FoodEnum.kimchi: 1>)
>>> parse(Args, ["--food", "poutine"]) # doctest: +SKIP
usage: make.py [-h] --food {gnocchi,kimchi}
make.py: error: argument --food: 'poutine': invalid value
...
SystemExit: 2

Specifying enums by name is not currently supported.
"""

import dataclasses

# noinspection PyUnresolvedReferences,PyProtectedMember
import inspect
from argparse import (
    ArgumentDefaultsHelpFormatter,
    ArgumentParser,
)
from collections import deque
from enum import Enum
from functools import partial
from typing import (
    Any,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    get_type_hints,
)

from datargs.dispatch import TypeRegistry
from datargs.records.error import NotARecordClass
from datargs.records.generic import DatargsParams, RecordClass
from datargs.utils import remove_dict_nones

T = TypeVar("T")


def build_record_instance_from_parsed_args(
    record_class: RecordClass, args: Dict[str, Any]
):
    # New dictionary of args guaranteed to iterate by sorted key
    args = {k: v for k, v in sorted(args.items())}
    unpacked = {}
    for field_name, field in sorted(record_class.fields_dict().items()):
        for arg_name in list(args):
            if arg_name == field_name:
                unpacked[field_name] = args.pop(arg_name)
                break
            elif arg_name.startswith(field_name):
                slice_index = len(field_name) + 1
                sub_args = {}

                sub_arg_names = deque(args)
                while sub_arg_names and sub_arg_names[0].startswith(field_name):
                    sa_name = sub_arg_names.popleft()
                    sub_args[sa_name[slice_index:]] = args.pop(sa_name)

                sub_record_class = RecordClass.wrap_class(field.type)
                sub_value = build_record_instance_from_parsed_args(
                    sub_record_class, sub_args
                )
                unpacked[field_name] = sub_value
                break

    return record_class.cls(**unpacked)


def make_parser(cls, parser: Optional[ArgumentParser] = None) -> ArgumentParser:
    # noinspection PyShadowingNames
    """
    Create parser that parses command-line arguments according to the fields of `cls`.
    Use this if you want to do anything with the parser other than immediately parsing the command-line arguments.
    If you do want to parse immediately, use `parse()`.
    :param cls: class according to which argument parser is created
    :param parser: parser to add arguments to, by default creates a new parser
    :return: instance of `parser_cls` which parses command line according to `cls`

    >>> @dataclasses.dataclass
    ... class Args:
    ...     first_arg: int
    >>> parse(Args, ["--first-arg", "0"])
    Args(first_arg=0)
    >>> parser = make_parser(Args)
    >>> parser.add_argument("--second-arg", type=float) # doctest: +ELLIPSIS
    [...]
    >>> parser.parse_args(["--first-arg", "0", "--second-arg", "1.5"])
    Namespace(first_arg=0, second_arg=1.5)
    """
    record_class = RecordClass.wrap_class(cls)
    return _make_parser(record_class, parser=parser)


def _make_parser(
    record_class: RecordClass, parser: Optional[ArgumentParser] = None
) -> ArgumentParser:
    if parser is None:
        parser = ArgumentParser(**record_class.parser_params)

    for name, field in record_class.fields_dict().items():
        # TODO: Add argument groups for dataclasses (as they are nested)
        actions = TypeRegistry.build_actions(field)
        for action in actions:
            parser.add_argument(*action.aliases, **action.kwargs)

    return parser


def parse(
    cls: Type[T],
    args: Optional[Sequence[str]] = None,
    *,
    parser: Optional[ArgumentParser] = None,
) -> T:
    """
    Parse command line arguments according to the fields of `cls` and populate it.
    Accepts classes decorated with `dataclass` or `attr.s`.
    :param cls: class to parse command-line arguments by
    :param parser: existing parser to add arguments to and parse from
    :param args: arguments to parse (default: `sys.arg`)
    :return: an instance of cls

    >>> @dataclasses.dataclass
    ... class Args:
    ...     is_flag: bool
    ...     num: int = 0
    >>> parse(Args, ["--num", "1"])
    Args(is_flag=False, num=1)
    """
    result = vars(make_parser(cls, parser=parser).parse_args(args))
    return build_record_instance_from_parsed_args(RecordClass.wrap_class(cls), result)


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


# noinspection PyShadowingBuiltins
def arg(
    nargs=None,
    const=None,
    default=dataclasses.MISSING,
    choices=None,
    help=None,
    metavar=None,
    aliases: Sequence[str] = (),
    **kwargs,
):
    """
    Helper method to more easily add parsing-related behavior.
    Supports aliases:
    >>> @dataclasses.dataclass
    ... class Args:
    ...     num: int = arg(aliases=["-n"])
    >>> parse(Args, ["--num", "0"])
    Args(num=0)
    >>> parse(Args, ["-n", "0"])
    Args(num=0)

    Accepts all arguments to both `ArgumentParser.add_argument` and `dataclass.field`:
    >>> @dataclasses.dataclass
    ... class Args:
    ...     invisible_arg: int = arg(default=0, repr=False, metavar="MY_ARG", help="argument description")
    >>> print(Args())
    Args()
    >>> make_parser(Args).print_help() # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    usage: ...
      --invisible-arg MY_ARG    argument description
    """
    return dataclasses.field(
        metadata=remove_dict_nones(
            dict(
                nargs=nargs,
                choices=choices,
                const=const,
                help=help,
                metavar=metavar,
                aliases=aliases,
            )
        ),
        default=default,
        **kwargs,
    )
