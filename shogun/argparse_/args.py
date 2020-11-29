import dataclasses
from typing import Callable, Optional, Sequence, TypeVar

from shogun.utils import remove_dict_nones

T = TypeVar("T")


def arg(
    nargs=None,
    const=None,
    default=dataclasses.MISSING,
    choices=None,
    help=None,
    metavar=None,
    aliases: Sequence[str] = (),
    converter: Optional[Callable[[str], T]] = None,
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
                converter=converter,
            )
        ),
        default=default,
        **kwargs,
    )
