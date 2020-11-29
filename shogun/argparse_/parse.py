from argparse import ArgumentParser
from collections import OrderedDict, deque
from typing import Any, Dict, Optional, Sequence, Type, TypeVar

from shogun.dispatch import TypeRegistry
from shogun.records.generic import RecordClass

T = TypeVar("T")


def build_record_instance_from_parsed_args(
    record_class: RecordClass, args: Dict[str, Any]
):
    # New dictionary of args guaranteed to iterate by sorted key
    args = OrderedDict({k: v for k, v in sorted(args.items())})
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
