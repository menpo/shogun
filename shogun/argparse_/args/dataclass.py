import dataclasses
from typing import Any, Callable, Optional, Sequence, TypeVar, Union

from shogun.utils import remove_dict_nones

T = TypeVar("T")


def dc_arg(
    nargs: Optional[Union[str, int]] = None,
    const: Optional[T] = None,
    default: Union[dataclasses._MISSING_TYPE, T] = dataclasses.MISSING,
    choices: Optional[Sequence[T]] = None,
    help: Optional[str] = None,
    metavar: Optional[str] = None,
    aliases: Sequence[str] = (),
    converter: Optional[Callable[[str], T]] = None,
    **kwargs: Any,
):
    """
    Helper method to more easily add parsing-related behavior.
    Supports aliases:
    >>> from shogun import make_parser, parse
    >>> @dataclasses.dataclass
    ... class Args:
    ...     num: int = dc_arg(aliases=["-n"])
    >>> parse(Args, ["--num", "0"])
    Args(num=0)
    >>> parse(Args, ["-n", "0"])
    Args(num=0)

    Accepts all arguments to both `ArgumentParser.add_argument` and `dataclass.field`:
    >>> @dataclasses.dataclass
    ... class Args:
    ...     invisible_arg: int = dc_arg(default=0, repr=False, metavar="MY_ARG", help="argument description")
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
                converter=converter,
            )
        ),
        default=default,
        **kwargs,
    )
