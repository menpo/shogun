from argparse import ArgumentParser
from typing import NoReturn, Text


class ParserError(ValueError):
    pass


class NoExitArgumentParser(ArgumentParser):
    def error(self, message: Text) -> NoReturn:
        raise ParserError(message)
