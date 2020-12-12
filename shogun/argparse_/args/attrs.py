from typing import Any, Callable, Optional, Sequence, TypeVar, Union, cast

from shogun.utils import remove_dict_nones

try:
    import attr

    __all__ = ["attrs_arg"]
except ImportError:
    __all__ = []
else:
    from attr._make import _Nothing

    T = TypeVar("T")

    def attrs_arg(
        nargs: Optional[Union[str, int]] = None,
        const: Optional[T] = None,
        # Have to cast because attrs lies about the type of NOTHING
        default: Union[_Nothing, T] = cast(_Nothing, attr.NOTHING),
        choices: Optional[Sequence[T]] = None,
        help: Optional[str] = None,
        metavar: Optional[str] = None,
        aliases: Sequence[str] = (),
        argparse_parse: Optional[Callable[[str], T]] = None,
        **kwargs: Any,
    ):
        """
        Helper method to more easily add parsing-related behavior.
        Supports aliases:
        >>> from shogun import make_parser, parse
        >>> @attr.s
        ... class Args:
        ...     num: int = attrs_arg(aliases=["-n"])
        >>> parse(Args, ["--num", "0"])
        Args(num=0)
        >>> parse(Args, ["-n", "0"])
        Args(num=0)

        Accepts all arguments to both `ArgumentParser.add_argument` and `attr.ib`:
        >>> @attr.s
        ... class Args:
        ...     invisible_arg: int = attrs_arg(default=0, repr=False, metavar="MY_ARG", help="argument description")
        >>> print(Args())
        Args()
        >>> make_parser(Args).print_help() # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        usage: ...
          --invisible-arg MY_ARG    argument description
        """
        return attr.ib(
            metadata=remove_dict_nones(
                dict(
                    nargs=nargs,
                    choices=choices,
                    const=const,
                    help=help,
                    metavar=metavar,
                    aliases=aliases,
                    argparse_parse=argparse_parse,
                )
            ),
            default=default,
            **kwargs,
        )
