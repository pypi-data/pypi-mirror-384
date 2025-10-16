# Copyright (c) 2012 Qumulo, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.


import argparse
import getpass
import operator
import sys
import textwrap

from typing import (
    Any,
    Callable,
    cast,
    Final,
    Iterator,
    KeysView,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    TextIO,
    Type,
    TYPE_CHECKING,
)

import qumulo.lib.util as util

if TYPE_CHECKING:
    from qumulo.rest_client import RestClient

try:
    # use argcomplete if available
    import argcomplete
except ImportError:
    argcomplete = None


class Subcommand:
    NAME: str
    SYNOPSIS: str

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        pass


class HelpCommand(Subcommand):
    NAME = 'help'
    SYNOPSIS = 'QQ documentation'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        pass


MAX_EDIT_DISTANCE_CHOICES: Final[int] = 5


class SubcommandHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """
    Custom subcommand help formatter that suppresses hidden subcommands from
    help.
    """

    def _format_action(self, action: argparse.Action) -> str:
        """
        Override _format_action, which is called during parser.format_help() to
        format a single (sub)command. This implementation simply returns no
        information (empty string) for actions (i.e. (sub)commands) that have
        been suppressed.  The default behavior being overridden simply prints
        "== SUPPRESSED ==" for the action.
        """
        parts = super()._format_action(action)
        if action.help == argparse.SUPPRESS:
            return ''
        return parts


class HelpfulSubparserChoicesWrapper:
    """
    A wrapper around the subparser choices that provides more helpful
    suggestions on the CLI for flubbed commands. Also allows you to type
    partial parts of the command if you can't remember the full thing.

    You can still --help and | grep to find a subcommand, but hopefully this
    will make the error message on a snafu'd subcommand be less unhelpful.
    """

    def __init__(self, choices: Mapping[str, argparse.ArgumentParser], num_choices: int) -> None:
        self._real_choices = choices
        self._last_contains_check: Optional[str] = None
        self._num_choices = num_choices
        self._visible_choices: Optional[Mapping[str, argparse.ArgumentParser]] = None

    def _compute_visible_choices(self) -> Mapping[str, argparse.ArgumentParser]:
        visible_choices = {}
        for name, parser in self._real_choices.items():
            subcommand_class = None
            if hasattr(parser, '_defaults') and parser._defaults:
                subcommand_class = parser._defaults.get('subcommand')

            if subcommand_class is None:
                visible_choices[name] = parser
            else:
                synopsis = getattr(subcommand_class, 'SYNOPSIS', None)
                if synopsis is not argparse.SUPPRESS:
                    visible_choices[name] = parser
        return visible_choices

    @property
    def visible_choices(self) -> Mapping[str, argparse.ArgumentParser]:
        if self._visible_choices is None:
            self._visible_choices = self._compute_visible_choices()
        return self._visible_choices

    def __contains__(self, arg: str) -> bool:
        # When argparse is validating the subparser sub-command, it checks
        # if choices contains the argument. We can remember this to know
        # what the user typed in
        self._last_contains_check = arg
        return arg in self._real_choices

    def __getitem__(self, arg: str) -> argparse.ArgumentParser:
        # argcomplete calls into this to perform command completion
        return self._real_choices[arg]

    def __iter__(self) -> Iterator[str]:
        if self._last_contains_check is None:
            return iter(self.visible_choices)

        # Find all choices that contain the last_contains_check as a substring
        # This allows the user to type partial matches to sub-commands
        choices = []
        remaining = []
        for choice in sorted(self.visible_choices):
            if self._last_contains_check in choice:
                choices.append(choice)
            else:
                remaining.append(choice)

        # In the event that the user flubbed the sub-command and we have no
        # suggestions based on substring matches, use edit distance to give the
        # user helpful-ish suggestions
        if not choices:
            edit_distances = []
            for choice in remaining:
                dist = util.edit_distance(choice, self._last_contains_check)
                edit_distances.append((dist, choice))
            edit_distances.sort(key=operator.itemgetter(0))
            choices.extend(x[1] for x in edit_distances[: self._num_choices])
        return iter(choices)

    def keys(self) -> KeysView[str]:
        """
        N.B. argcomplete will call keys() on parser.choices to get options
        for auto-completion. This needs to be a pass-through to real_choices
        to support this use-case.
        """
        return self.visible_choices.keys()


def parse_subcommand(cls: Type[Subcommand], subparsers: Any) -> argparse.ArgumentParser:
    # Add a subparser for each subcommand. The synopsis goes in the list of
    # subcommands you get with `qq --help`. The description goes in the
    # subcommands --help output. Allow preformatted or explicit descriptions
    # or fall back to duplicating the sysnopsis.
    description = getattr(cls, 'DESCRIPTION', cls.SYNOPSIS)
    epilog = getattr(cls, 'EPILOG', None)
    aliases = getattr(cls, 'ALIASES', [])
    subparser = subparsers.add_parser(
        cls.NAME,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description,
        epilog=epilog,
        help=cls.SYNOPSIS,
        aliases=aliases,
    )

    # Add options particular to the subcommand
    cls.options(subparser)

    has_subparsers = any(
        isinstance(action, argparse._SubParsersAction) for action in subparser._actions
    )
    if has_subparsers and epilog is None:
        subparser.epilog = 'Use `{positional argument} --help` to see subcommand specific help.'

    # Set the subcommand class
    subparser.set_defaults(subcommand=cls)

    return subparser


def parse_help_options(cls: Type[HelpCommand], subparsers: Any) -> None:
    """
    Help commands have their own subclass for which we need another subparser
    """
    help_subparser = subparsers.add_parser(cls.NAME, description=cls.SYNOPSIS, help=cls.SYNOPSIS)
    help_subparsers = help_subparser.add_subparsers()
    help_subparsers.choices = HelpfulSubparserChoicesWrapper(
        help_subparsers.choices, MAX_EDIT_DISTANCE_CHOICES
    )
    for help_cls in sorted(HelpCommand.__subclasses__(), key=operator.attrgetter('NAME')):
        parse_subcommand(help_cls, help_subparsers)


def add_subcommands(parser: argparse.ArgumentParser) -> None:
    parser.formatter_class = SubcommandHelpFormatter
    subparsers = parser.add_subparsers(
        title='Qumulo Command Line Interface',
        description='Interact with the RESTful API by the command line',
        help='Action',
        metavar='',
    )
    subparsers.choices = HelpfulSubparserChoicesWrapper(  # type: ignore[assignment]
        subparsers.choices, MAX_EDIT_DISTANCE_CHOICES
    )

    for cls in sorted(Subcommand.__subclasses__(), key=operator.attrgetter('NAME')):
        if cls.NAME == 'help':
            parse_help_options(cast(Type[HelpCommand], cls), subparsers)
        else:
            parse_subcommand(cls, subparsers)


def parse_options(parser: argparse.ArgumentParser, argv: Sequence[str]) -> argparse.Namespace:
    add_subcommands(parser)
    if argcomplete is not None:
        argcomplete.autocomplete(parser, exit_method=sys.exit)
    return parser.parse_args(argv)


def read_password(user: Optional[str] = None, prompt: Optional[str] = None) -> str:
    password = getpass.getpass(prompt if prompt is not None else f'Enter password for {user}: ')

    return str_decode(password)


def ask(command: str, message: str, inputter: Callable[[str], str] = input) -> bool:
    # Wrap long lines to make the CLI output more readable
    wrapped_message = '\n'.join(textwrap.fill(line) for line in message.splitlines())
    f = inputter(f'{wrapped_message} (yes/no): ')
    if f.lower() == 'no':
        print(f'Canceling the {command} request...')
        return False
    elif f.lower() != 'yes':
        raise ValueError("Please enter 'yes' or 'no'")

    return True


def str_decode(arg: object) -> str:
    """
    Custom argparse type for decoding based on stdin-specific encoding. If stdin
    does not provide an encoding (e.g. is a pipe), then default to utf-8 for the
    sake of doing something relatively sane.
    """
    if isinstance(arg, str):
        # python3's `str()` errors when given a `str` instance and an encoding.
        return arg
    elif isinstance(arg, bytes):
        encoding = sys.stdin.encoding or 'utf-8'
        return str(arg, encoding)
    else:
        # For other types, convert to string using str()
        return str(arg)


class SubcommandProtocol(Protocol):
    @staticmethod
    def main(rest_client: 'RestClient', __args: argparse.Namespace) -> None:
        pass


class HelpCommandProtocol(Protocol):
    @staticmethod
    def main(args: argparse.Namespace, outfile: TextIO = sys.stdout) -> None:
        pass


def run_subcommand(
    subcommand: Type[Subcommand], rest_client: 'RestClient', args: argparse.Namespace
) -> None:
    if issubclass(subcommand, HelpCommand):
        # qq help commands are not REST wrappers, and therefore do not need the rest_client
        help_cmd = cast(HelpCommandProtocol, subcommand)
        help_cmd.main(args)
    else:
        sub_cmd = cast(SubcommandProtocol, subcommand)
        sub_cmd.main(rest_client, args)
