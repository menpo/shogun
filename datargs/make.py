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
# noinspection PyUnresolvedReferences,PyProtectedMember
from argparse import (
    ArgumentParser,
    ArgumentTypeError,
    _SubParsersAction,
    Namespace,
)
from enum import Enum
from functools import wraps, partial
from inspect import signature
from typing import (
    Callable,
    Dict,
    TypeVar,
    Type,
    Sequence,
    Optional,
    overload,
    Any,
    Mapping,
    Union,
    cast,
    get_type_hints,
)

import dataclasses
from dataclasses import dataclass, MISSING

from .compat import RecordField, RecordClass, NotARecordClass, DatargsParams


@dataclass
class Action:
    args: Sequence[Any] = dataclasses.field(default_factory=list)
    kwargs: Mapping[str, Any] = dataclasses.field(default_factory=dict)


DispatchCallback = Callable[[str, RecordField], Action]
AddArgFunc = Callable[[RecordField], Action]


def field_name_to_arg_name(name: str, positional=False) -> str:
    if positional:
        return name
    return f"--{name.replace('_','-')}"


class TypeDispatch:

    dispatch: Dict[type, AddArgFunc] = {}

    @classmethod
    def add_arg(cls, field: RecordField):
        for typ, func in cls.dispatch.items():
            if issubclass(field.type, typ):
                return func(field)
        return add_any(field)

    @classmethod
    def register(cls, typ):
        def decorator(func: DispatchCallback) -> AddArgFunc:
            cls.dispatch[typ] = new_func = add_name_formatting(func)
            return new_func

        return decorator


def add_name_formatting(func: DispatchCallback) -> AddArgFunc:
    @wraps(func)
    def new_func(field: RecordField):
        return func(
            field_name_to_arg_name(field.name, positional=field.is_positional),
            field,
        )

    return new_func


@add_name_formatting
def add_any(name: str, field: RecordField) -> Action:
    return add_default(name, field)


def get_option_strings(name: str, field: RecordField):
    return [name, *field.metadata.get("aliases", [])]


def common_kwargs(field: RecordField):
    return {"type": field.type, **subdict(field.metadata, {"aliases"})}


def subdict(dct, remove_keys):
    return {key: value for key, value in dct.items() if key not in remove_keys}


def add_default(name, field: RecordField, **kwargs) -> Action:
    kwargs = {
        "default": field.default,
        "field": field.is_required(),
        **common_kwargs(field),
        **kwargs,
    }
    return Action(kwargs=kwargs, args=get_option_strings(name, field))


T = TypeVar("T")


def call_func_with_matching_kwargs(func: Callable[..., T], *args, **kwargs) -> T:
    sig = signature(func)
    new_kwargs = {key: value for key, value in kwargs.items() if key in sig.parameters}
    return func(*args, **new_kwargs)


@TypeDispatch.register(bool)
def bool_arg(name: str, field: RecordField) -> Action:
    kwargs = {
        **subdict(common_kwargs(field), ["type"]),
        "action": "store_false"
        if field.default and field.has_default()
        else "store_true",
    }
    return Action(
        args=get_option_strings(name, field),
        kwargs=kwargs,
    )


@TypeDispatch.register(Enum)
def enum_arg(name: str, field: RecordField) -> Action:
    def enum_type_func(value: str):
        result = field.type.__members__.get(value)
        if not result:
            raise ArgumentTypeError(
                f"invalid choice: {value!r} (choose from {[e.name for e in field.type]})"
            )
        return result

    return add_default(
        name,
        field,
        type=enum_type_func,
        choices=field.type,
        metavar=f"{{{','.join(field.type.__members__)}}}",
    )


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
    assert parser is not None
    for name, field in record_class.fields_dict().items():
        action = TypeDispatch.add_arg(field)
        parser.add_argument(*action.args, **action.kwargs)
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
    try:
        command_dest = cls.__datargs_params__.sub_commands.get("dest", None)
    except AttributeError:
        pass
    else:
        if command_dest is not None and command_dest in result:
            del result[command_dest]
    return cls(**result)


def argsclass(
    cls: type = None,
    *args,
    description: str = None,
    parser_params: dict = None,
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
            if not isinstance(value, dataclasses.Field) or value.default is not MISSING:
                continue
            typ = value.type or get_type_hints(cls)[key]
            if typ is bool:
                value.default = False
        new_cls = dataclass(*args, **kwargs)(cls)
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
    default=MISSING,
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


if __name__ == "__main__":
    import doctest

    OC = doctest.OutputChecker

    class AEOutputChecker(OC):
        def check_output(self, want, got, optionflags):
            if optionflags & doctest.ELLIPSIS:
                want = want.replace("[...]", doctest.ELLIPSIS_MARKER)
            return super().check_output(want, got, optionflags)

    doctest.OutputChecker = AEOutputChecker
    doctest.testmod(optionflags=doctest.REPORT_NDIFF)
