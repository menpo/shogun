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
from abc import ABCMeta, abstractmethod
from argparse import (
    ArgumentDefaultsHelpFormatter,
    ArgumentParser,
    ArgumentTypeError,
)
from collections import deque
from enum import Enum
from functools import partial
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    get_type_hints,
    overload,
)

from datargs.records.error import NotARecordClass
from datargs.records.generic import DatargsParams, RecordClass, RecordField


@dataclasses.dataclass()
class Action:
    aliases: Sequence[str] = dataclasses.field(default_factory=list)
    kwargs: Mapping[str, Any] = dataclasses.field(default_factory=dict)


def field_name_to_arg_name(name: str, underscore_to_hyphen: bool = True) -> str:
    return f"--{name.replace('_', '-') if underscore_to_hyphen else name}"


class TypeDispatch:
    # Intentionally static
    dispatch: List["DispatcherBase"] = []

    @classmethod
    def build_actions(cls, field: RecordField) -> Sequence[Action]:
        for dispatcher in cls.dispatch:
            if dispatcher.is_type(field.type):
                return dispatcher.build_actions(field)
        return (add_default(field),)

    @classmethod
    def register(cls, dispatcher_type: Type["DispatcherBase"]):
        cls.dispatch.append(dispatcher_type())


class DispatcherBase(metaclass=ABCMeta):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls):
            TypeDispatch.register(cls)

    @abstractmethod
    def is_type(self, field_type: type) -> bool:
        ...

    @abstractmethod
    def build_actions(self, field: RecordField) -> Sequence[Action]:
        ...


class DispatcherIsSubclass(DispatcherBase):
    type_: type

    @abstractmethod
    def build_action(self, field: RecordField) -> Action:
        ...

    def is_type(self, field_type: type) -> bool:
        return issubclass(field_type, self.type_)

    def build_actions(self, field: RecordField) -> Sequence[Action]:
        return (self.build_action(field),)


def get_arg_alias_list(name: str, field: RecordField) -> List[str]:
    return [name, *field.metadata.get("aliases", [])]


def common_kwargs(field: RecordField):
    return {"type": field.type, **filter_dict(field.metadata, {"aliases"})}


def filter_dict(dct, remove_keys):
    return {key: value for key, value in dct.items() if key not in remove_keys}


def add_default(field: RecordField, **kwargs) -> Action:
    kwargs = {
        "default": field.default,
        "required": field.is_required(),
        **common_kwargs(field),
        **kwargs,
    }
    return Action(
        aliases=get_arg_alias_list(field_name_to_arg_name(field.name), field),
        kwargs=kwargs,
    )


T = TypeVar("T")


class DispatcherIsDataclass(DispatcherBase):
    def is_type(self, field_type: type) -> bool:
        return dataclasses.is_dataclass(field_type)

    def _add_prefix(self, prefix: str, aliases: Sequence[str]) -> Sequence[str]:
        new_aliases = []
        for alias in aliases:
            assert alias[:2] == "--"
            new_alias = f"--{prefix}-{alias[2:]}"
            new_aliases.append(new_alias)
        return new_aliases

    def build_actions(self, field: RecordField) -> Sequence[Action]:
        # TODO: Make this configurable
        prefix = field.name.replace("_", "-")

        actions = []
        record_class = RecordClass.wrap_class(field.type)
        for sub_field in record_class.fields_dict().values():
            sub_actions = TypeDispatch.build_actions(sub_field)

            for s_a in sub_actions:
                s_a.aliases = self._add_prefix(prefix, s_a.aliases)

            actions.extend(sub_actions)

        return actions


class DispatcherBool(DispatcherIsSubclass):
    type_ = bool

    def build_action(self, field: RecordField) -> Action:
        kwargs = {
            **filter_dict(common_kwargs(field), {"type"}),
            "action": "store_false"
            if field.default and field.has_default()
            else "store_true",
        }
        return Action(
            aliases=get_arg_alias_list(
                field_name_to_arg_name(field.name),
                field,
            ),
            kwargs=kwargs,
        )


class DispatcherEnum(DispatcherIsSubclass):
    type_ = Enum

    def build_action(self, field: RecordField) -> Action:
        def enum_type_func(value: str):
            result = field.type.__members__.get(value)
            if not result:
                raise ArgumentTypeError(
                    f"invalid choice: {value!r} (choose from {[e.name for e in field.type]})"
                )
            return result

        return add_default(
            field,
            type=enum_type_func,
            choices=field.type,
            metavar=f"{{{','.join(field.type.__members__)}}}",
        )


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


ParserType = TypeVar("ParserType", bound=ArgumentParser)


@overload
def make_parser(cls: type) -> ArgumentParser:
    pass


@overload
def make_parser(cls: type, parser: None = None) -> ArgumentParser:
    pass


@overload
def make_parser(cls: type, parser: ParserType) -> ParserType:
    pass


def make_parser(cls, parser=None):
    # noinspection PyShadowingNames
    """
    Create parser that parses command-line arguments according to the fields of `cls`.
    Use this if you want to do anything with the parser other than immediately parsing the command-line arguments.
    If you do want to parse immediately, use `parse()`.
    :param cls: class according to which argument parser is created
    :param parser: parser to add arguments to, by default creates a new parser
    :return: instance of `parser_cls` which parses command line according to `cls`

    >>> @dataclass
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


def _make_parser(record_class: RecordClass, parser: ParserType = None) -> ParserType:
    if not parser:
        parser = ArgumentParser(**record_class.parser_params)

    for name, field in record_class.fields_dict().items():
        # TODO: Use the correct description - need to push creating the arguments
        #       into the dispatcher
        group = parser

        actions = TypeDispatch.build_actions(field)
        if len(actions) > 1:
            group = parser.add_argument_group(
                description=record_class.datargs_params.parser.get("description")
            )

        for action in actions:
            group.add_argument(*action.aliases, **action.kwargs)

    return parser


def parse(cls: Type[T], args: Optional[Sequence[str]] = None, *, parser=None) -> T:
    """
    Parse command line arguments according to the fields of `cls` and populate it.
    Accepts classes decorated with `dataclass` or `attr.s`.
    :param cls: class to parse command-line arguments by
    :param parser: existing parser to add arguments to and parse from
    :param args: arguments to parse (default: `sys.arg`)
    :return: an instance of cls

    >>> @dataclass
    ... class Args:
    ...     is_flag: bool
    ...     num: int = 0
    >>> parse(Args, ["--num", "1"])
    Args(is_flag=False, num=1)
    """
    result = vars(make_parser(cls, parser=parser).parse_args(args))
    return build_record_instance_from_parsed_args(RecordClass.wrap_class(cls), result)


def argsclass(
    cls: type = None,
    *args,
    description: str = None,
    parser_params: Dict[str, Any] = None,
    **kwargs,
):
    """
    A wrapper around `dataclass` for passing `description` and other params (in `parser_params`)
    to the `ArgumentParser` constructor.
    """
    parser_params = parser_params or {}
    datargs_kwargs = {
        "description": description,
        "parser_params": parser_params,
    }
    parser_params.setdefault("formatter_class", ArgumentDefaultsHelpFormatter)

    if cls is None:
        # We're called with parens.
        return partial(
            make_class,
            *args,
            **datargs_kwargs,
            **kwargs,
        )

    return make_class(
        cls,
        *args,
        **datargs_kwargs,
        **kwargs,
    )


def make_class(
    cls,
    description: str = None,
    parser_params: dict = None,
    *args,
    **kwargs,
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
        parser={"description": description, **(parser_params or {})},
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
    >>> @dataclass
    ... class Args:
    ...     num: int = arg(aliases=["-n"])
    >>> parse(Args, ["--num", "0"])
    Args(num=0)
    >>> parse(Args, ["-n", "0"])
    Args(num=0)

    Accepts all arguments to both `ArgumentParser.add_argument` and `dataclass.field`:
    >>> @dataclass
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


def remove_dict_nones(dct: dict) -> dict:
    return {key: value for key, value in dct.items() if value is not None}
