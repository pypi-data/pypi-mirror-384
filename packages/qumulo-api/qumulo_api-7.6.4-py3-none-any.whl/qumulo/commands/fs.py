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
import base64
import binascii
import collections
import enum
import json
import os.path
import re
import sys
import textwrap

from argparse import ArgumentParser, Namespace, SUPPRESS
from datetime import datetime, timedelta, timezone
from typing import (
    Any,
    Dict,
    IO,
    Iterable,
    Iterator,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Protocol,
    Sequence,
    Set,
    Tuple,
)

from tqdm import tqdm

import qumulo.lib.opts
import qumulo.lib.request as request
import qumulo.lib.util as util
import qumulo.rest.auth as auth
import qumulo.rest.fs as fs

from qumulo.commands.auth import format_expanded_id
from qumulo.lib.acl_util import AceTranslator, AclEditor
from qumulo.lib.auth import Credentials
from qumulo.lib.identity_util import AD_DOMAIN, Identity
from qumulo.lib.opts import str_decode
from qumulo.lib.request import pretty_json
from qumulo.lib.rfc3339 import fmt_rfc3339_time
from qumulo.rest_client import RestClient

AGG_ORDERING_CHOICES = [
    'total_blocks',
    'total_datablocks',
    'total_named_stream_datablocks',
    'total_metablocks',
    'total_files',
    'total_directories',
    'total_symlinks',
    'total_other',
    'total_named_streams',
]

LOCK_RELEASE_FORCE_MSG = (
    'Manually releasing locks may cause data corruption, do you want to proceed?'
)


class GetStatsCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_get_stats'
    SYNOPSIS = 'Get file system statistics'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument('--json', action='store_true', help='Print the output in JSON format.')

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        stats = fs.read_fs_stats(rest_client.conninfo, rest_client.credentials).data
        used_capacity = int(stats['total_size_bytes']) - int(stats['free_size_bytes'])
        if args.json:
            stats['used_size_bytes'] = str(used_capacity)
            print(pretty_json(stats))
        else:
            output = f"""\
                Total capacity: {stats['total_size_bytes']} bytes
                Used capacity:  {used_capacity} bytes
                    Snapshots:  {stats['snapshot_size_bytes']} bytes
                Free capacity:  {stats['free_size_bytes']} bytes\
                """
            print(textwrap.dedent(output))


def get_stream_id(
    conninfo: request.Connection, credentials: Optional[Credentials], args: argparse.Namespace
) -> Optional[str]:
    sid = None
    if args.stream_id is not None or args.stream_name is not None:
        sid = translate_stream_args_to_id(
            conninfo, credentials, args.stream_id, args.stream_name, args.path, args.id
        )
    return sid


def add_ref_arguments(parser: ArgumentParser, name: str) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--path', help=f'{name} path', type=str_decode)
    group.add_argument('--id', help=f'{name} ID', type=str_decode)


class GetFileAttrCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_file_get_attr'
    SYNOPSIS = 'Get file attributes'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')
        parser.add_argument('--snapshot', help='Snapshot ID to read from', type=int)
        parser.add_argument(
            '--retrieve-file-lock',
            action='store_true',
            help='Retrieve the file lock for this file. Optional because it requires READ_ACL',
        )

        stream_group = parser.add_mutually_exclusive_group()
        stream_group.add_argument('--stream-id', help='Stream ID', type=str_decode)
        stream_group.add_argument('--stream-name', help='Stream name', type=str_decode)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            fs.get_file_attr(
                rest_client.conninfo,
                rest_client.credentials,
                id_=args.id,
                path=args.path,
                snapshot=args.snapshot,
                stream_id=get_stream_id(rest_client.conninfo, rest_client.credentials, args),
                retrieve_file_lock=args.retrieve_file_lock,
            )
        )


class SetFileAttrCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_file_set_attr'
    SYNOPSIS = 'Set file attributes'
    DESCRIPTION = textwrap.dedent(
        """\
        Set file attributes. Changing owner or mode bits is done POSIX-style; file\'s
        ACL is updated to match the requested permissions.
    """
    )

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')

        stream_group = parser.add_mutually_exclusive_group()
        stream_group.add_argument('--stream-id', help='Stream ID', type=str_decode)
        stream_group.add_argument('--stream-name', help='Stream name', type=str_decode)

        parser.add_argument('--mode', type=str_decode, help='Posix-style file mode (octal)')
        parser.add_argument('--size', help='File size', type=str_decode)
        parser.add_argument(
            '--creation-time', type=str_decode, help='File creation time (as RFC 3339 string)'
        )
        parser.add_argument(
            '--access-time', type=str_decode, help='File access time (as RFC 3339 string)'
        )
        parser.add_argument(
            '--modification-time',
            type=str_decode,
            help='File modification time (as RFC 3339 string)',
        )
        parser.add_argument(
            '--change-time', type=str_decode, help='File change time (as RFC 3339 string)'
        )

        owner_group = parser.add_mutually_exclusive_group()
        owner_group.add_argument('--owner', help='File owner as auth_id', type=str_decode)
        owner_group.add_argument(
            '--owner-local', help='File owner as local user name', type=fs.LocalUser
        )
        owner_group.add_argument('--owner-sid', help='File owner as SID', type=fs.SMBSID)
        owner_group.add_argument('--owner-uid', help='File owner as NFS UID', type=fs.NFSUID)

        group_group = parser.add_mutually_exclusive_group()
        group_group.add_argument('--group', help='File group as auth_id', type=str_decode)
        group_group.add_argument(
            '--group-local', help='File group as local group name', type=fs.LocalGroup
        )
        group_group.add_argument('--group-sid', help='File group as SID', type=fs.SMBSID)
        group_group.add_argument('--group-gid', help='File group as NFS GID', type=fs.NFSGID)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        owner = args.owner or args.owner_local or args.owner_sid or args.owner_uid
        group = args.group or args.group_local or args.group_sid or args.group_gid

        if all(
            x is None
            for x in [
                args.mode,
                owner,
                group,
                args.size,
                args.creation_time,
                args.access_time,
                args.modification_time,
                args.change_time,
            ]
        ):
            raise ValueError('Must specify at least one option to change.')

        print(
            fs.set_file_attr(
                rest_client.conninfo,
                rest_client.credentials,
                mode=args.mode,
                owner=owner,
                group=group,
                size=args.size,
                creation_time=args.creation_time,
                access_time=args.access_time,
                modification_time=args.modification_time,
                change_time=args.change_time,
                id_=args.id,
                path=args.path,
                stream_id=get_stream_id(rest_client.conninfo, rest_client.credentials, args),
            )
        )


EXTENDED_FILE_ATTRS = (
    'archive',
    'compressed',
    'hidden',
    'not_content_indexed',
    'read_only',
    'system',
    'temporary',
    'offline',
)


class SetSmbFileAttrsCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_file_set_smb_attrs'
    SYNOPSIS = 'Change SMB extended attributes on the file'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')

        for attr in EXTENDED_FILE_ATTRS:
            opt_string = '--' + attr.replace('_', '-')
            help_str = 'Set {} to a boolean-like value (e.g. true, false, yes, no, 1, 0).'.format(
                attr.upper()
            )
            parser.add_argument(
                opt_string, dest=attr, metavar='BOOL', type=util.bool_from_string, help=help_str
            )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        new_extended_attrs = {}
        etag = None
        if any(getattr(args, attr) is None for attr in EXTENDED_FILE_ATTRS):
            all_attrs, etag = fs.get_file_attr(
                rest_client.conninfo, rest_client.credentials, args.id, args.path
            )
            new_extended_attrs = all_attrs['extended_attributes']

        for attr in EXTENDED_FILE_ATTRS:
            attr_val = getattr(args, attr)
            if attr_val is not None:
                new_extended_attrs[attr] = attr_val

        print(
            fs.set_file_attr(
                rest_client.conninfo,
                rest_client.credentials,
                id_=args.id,
                path=args.path,
                extended_attributes=new_extended_attrs,
                if_match=etag,
            )
        )


NFS_GID_TRUSTEE_TYPE = 'NFS_GID'
NFS_UID_TRUSTEE_TYPE = 'NFS_UID'
LOCAL_USER_TRUSTEE_TYPE = 'LOCAL_USER'
LOCAL_GROUP_TRUSTEE_TYPE = 'LOCAL_GROUP'
SID_TRUSTEE_TYPE = 'SMB_SID'
INTERNAL_TRUSTEE_TYPE = 'INTERNAL'

EVERYONE_NAME = 'Everyone'
EVERYONE_AUTH_ID = str(0x200000000)  # WORLD_DOMAIN_ID << 32
FILE_OWNER_NAME = 'File Owner'
FILE_GROUP_OWNER_NAME = 'File Group Owner'

# These are the values actually produced / accepted by the API
ALL_RIGHTS = {
    'READ',
    'READ_EA',
    'READ_ATTR',
    'READ_ACL',
    'WRITE_EA',
    'WRITE_ATTR',
    'WRITE_ACL',
    'CHANGE_OWNER',
    'WRITE_GROUP',
    'DELETE',
    'EXECUTE',
    'MODIFY',
    'EXTEND',
    'ADD_FILE',
    'ADD_SUBDIR',
    'DELETE_CHILD',
    'SYNCHRONIZE',
}

# This maps the enum values used in the API to human-friendly output.
# A few of the right enum values have confusing names ("Modify" in particular
# gets confused with the Windows preset, and "Read" tends to suggest a much
# broader set of rights), so a simple text transform isn't great here:
API_RIGHTS_TO_CLI = {
    'READ': 'Read contents',
    'READ_EA': 'Read EA',
    'READ_ATTR': 'Read attr',
    'READ_ACL': 'Read ACL',
    'WRITE_EA': 'Write EA',
    'WRITE_ATTR': 'Write attr',
    'WRITE_ACL': 'Write ACL',
    'CHANGE_OWNER': 'Change owner',
    'WRITE_GROUP': 'Write group',
    'DELETE': 'Delete',
    'EXECUTE': 'Execute/Traverse',
    'MODIFY': 'Write data',
    'EXTEND': 'Extend file',
    'ADD_FILE': 'Add file',
    'ADD_SUBDIR': 'Add subdir',
    'DELETE_CHILD': 'Delete child',
    'SYNCHRONIZE': 'Synchronize',
}

# The reverse mapping, for interpreting input:
CLI_RIGHTS_TO_API = {v: k for k, v in API_RIGHTS_TO_CLI.items()}

# Plus some convenient aliases:
CLI_RIGHTS_TO_API.update(
    {'Execute': 'EXECUTE', 'Traverse': 'EXECUTE', 'Modify': 'MODIFY', 'Extend': 'EXTEND'}
)

# These correspond to Posix bits, and also QFSD default ACLs:
POSIX_READ_RIGHTS = frozenset(['READ', 'READ_EA', 'READ_ATTR', 'READ_ACL'])
POSIX_WRITE_FILE_RIGHTS = frozenset(['WRITE_ATTR', 'WRITE_EA', 'EXTEND', 'MODIFY'])

# POSIX_WRITE_DIR_RIGHTS is not included because trying to distinguish it from
# WINDOWS_MODIFY_DIR_RIGHTS makes for confusion.  DELETE_CHILD will just have
# to be input/output as a separate item.

# This corresponds to the Windows preset:
WINDOWS_TAKE_OWNERSHIP_RIGHTS = frozenset(['CHANGE_OWNER', 'WRITE_GROUP'])

# When applied to a directory, this set of rights has the same meaning as
# the Windows "Modify" preset.  Unfortunately, this set of rights does not
# have the same meaning as "Modify" when applied to a file.  Since those
# sets of QFSD rights are disjoint, there's no reasonably simple way of
# providing an exact equivalent to the "Modify" preset.
WINDOWS_MODIFY_DIR_RIGHTS = frozenset(['WRITE_ATTR', 'WRITE_EA', 'ADD_FILE', 'ADD_SUBDIR'])

# This maps user input to sets of rights that are commonly granted together:
SHORTHAND_RIGHTS_TO_API = {
    'All': frozenset(ALL_RIGHTS),
    'Read': POSIX_READ_RIGHTS,
    'Write file': POSIX_WRITE_FILE_RIGHTS,
    'Take ownership': WINDOWS_TAKE_OWNERSHIP_RIGHTS,
    'Write directory': WINDOWS_MODIFY_DIR_RIGHTS,
}

OBJECT_INHERIT_FLAG = 'OBJECT_INHERIT'
CONTAINER_INHERIT_FLAG = 'CONTAINER_INHERIT'
NO_PROPAGATE_INHERIT_FLAG = 'NO_PROPAGATE_INHERIT'
INHERIT_ONLY_FLAG = 'INHERIT_ONLY'
INHERITED_FLAG = 'INHERITED'

ALL_FLAGS = {
    OBJECT_INHERIT_FLAG,
    CONTAINER_INHERIT_FLAG,
    NO_PROPAGATE_INHERIT_FLAG,
    INHERIT_ONLY_FLAG,
    INHERITED_FLAG,
}

# A SID starts with S, followed by hyphen separated version, authority, and at
# least one sub-authority
SID_REGEXP = re.compile(r'S-[0-9]+-[0-9]+(?:-[0-9]+)+$')


def get_pretty_rights_string(rights: Set[str], hide_synchronize: bool = False) -> str:
    if rights == ALL_RIGHTS:
        # No need to print any other rights if we have ALL_RIGHTS
        return 'All'

    # Note that some of these overlap partially; printing both of the
    # overlapping sets is the desired outcome.
    res = []
    consumed_rights: Set[str] = set()
    for shorthand, values in SHORTHAND_RIGHTS_TO_API.items():
        if rights.issuperset(values):
            res.append(shorthand)
            consumed_rights.update(values)

    # The synchronize right is mostly useless, except that granting it is
    # basically mandatory for successful SMB access. Hide it from output on
    # allow ACEs because it's ugly and confusing.  Don't hide it for deny
    # because it probably shouldn't be there and is probably breaking things.
    # It's not included in the presets for the same reason - because it
    # shouldn't be included when deny ACEs are created with those presets.
    # (Windows permissions dialog is similarly insane)
    if hide_synchronize and len(rights) > 1:
        consumed_rights.add('SYNCHRONIZE')

    # Add any individual values that didn't get covered by a shorthand:
    for right in rights:
        if right not in consumed_rights:
            res.append(API_RIGHTS_TO_CLI[right])

    return ', '.join(sorted(res))


def get_pretty_flags(flags: Iterable[str]) -> str:
    pretty_flags = [r.replace('_', ' ') for r in flags]
    pretty_flags = [r.capitalize() for r in pretty_flags]
    return ', '.join(pretty_flags)


# list the shorthand rights ahead of the specific rights
RIGHT_CHOICES = sorted(list(SHORTHAND_RIGHTS_TO_API.keys())) + sorted(CLI_RIGHTS_TO_API.keys())


def normalize_rights_args(rights: Iterable[str]) -> List[str]:
    """
    Takes a list of right arguments (which are any strings) and maps them to
    matching keys in CLI_RIGHTS_TO_API or SHORTHAND_RIGHTS_TO_API, normalizing
    for comma separation, missing whitespace escaping, and case.

    In addition to being broadly tolerant of minor "errors", this means that
    it's possible to copy+paste rights from a pretty-printed ACL directly in to
    a command line without quoting, escaping, or removing commas.
    """
    # Tokenize to lowercase words, by commas and whitespace:
    lower_rights = [r.lower() for r in rights]
    tokens = ' '.join(lower_rights).replace(',', ' ').replace('_', ' ').split()

    # Greedily put the tokens back together into a sequence of valid choices:
    lower_choices = {c.lower(): c for c in RIGHT_CHOICES}
    accumulator = []
    res = []
    for i, tok in enumerate(tokens):
        accumulator.append(tok)
        joined = ' '.join(accumulator)

        # Crude look-ahead to see if we can build a longer right if we add the
        # next token, which resolves the ambiguity between e.g.
        # ["read", "execute"] and ["read", "contents"].
        if i + 1 < len(tokens):
            if joined + ' ' + tokens[i + 1] in lower_choices:
                continue

        if joined in lower_choices:
            res.append(lower_choices[joined])
            accumulator = []

    if accumulator:
        raise ValueError(
            'Bad rights, error near "{}": {}'.format(
                accumulator[0], ' '.join([repr(r) for r in rights])
            )
        )

    return res


class FsAceTranslator(AceTranslator):
    def parse_rights_enum_values(self, rights: Iterable[str]) -> Set[str]:
        res: Set[str] = set()

        # Expand any shorthand rights, map and validate the rest as enum values
        for arg_right in rights:
            if arg_right in SHORTHAND_RIGHTS_TO_API:
                res.update(SHORTHAND_RIGHTS_TO_API[arg_right])
            else:
                api_right = CLI_RIGHTS_TO_API[arg_right]
                assert api_right in ALL_RIGHTS
                res.add(api_right)
        return res

    def parse_rights(self, rights: Iterable[str], ace: MutableMapping[str, Any]) -> None:
        rights = normalize_rights_args(rights)
        rights = self.parse_rights_enum_values(rights)

        # Although the synchronize right means nothing to Qumulo, SMB clients
        # will often ask for it.  If it's not granted, they will be denied
        # access, rendering the rest of the granted rights useless.  So,
        # whenever rights are granted, implicitly also grant the synchronize
        # right.  This can't be done unconditionally, because doing this for a
        # deny ACE would effectively deny access over SMB. (Windows permissions
        # dialog has the same insanity)
        if ace['type'] == ALLOWED_TYPE:
            rights.add('SYNCHRONIZE')

        ace['rights'] = list(sorted(rights))

    def pretty_rights(self, ace: Mapping[str, Any]) -> str:
        # Translate as many of the values to shorthand as possible.  Note that
        # there is some overlap between some of the shorthand.  Rights lists
        # that include multiple overlapping shorthands should produce all of
        # those shorthands (i.e. the common rights may be represented multiple
        # times)
        rights = set(ace['rights'])
        hide_synchronize = ace.get('type') == ALLOWED_TYPE
        return get_pretty_rights_string(rights, hide_synchronize)

    def ace_rights_equal(self, ace: Mapping[str, Any], rights: Iterable[str]) -> bool:
        return set(ace['rights']) == self.parse_rights_enum_values(rights)

    @property
    def has_flags(self) -> bool:
        return True

    def parse_flags_enum_values(self, flags: Iterable[str]) -> List[str]:
        if not flags:
            return []

        res = [f.upper().replace(' ', '_') for f in flags]
        assert all(f in ALL_FLAGS for f in res)
        return res

    def parse_flags(self, flags: Iterable[str], ace: MutableMapping[str, Any]) -> None:
        ace['flags'] = self.parse_flags_enum_values(flags)

    def pretty_flags(self, ace: Mapping[str, Any]) -> str:
        return get_pretty_flags(ace['flags'])

    def ace_flags_equal(self, ace: Mapping[str, Any], flags: Iterable[str]) -> bool:
        return set(ace['flags']) == set(self.parse_flags_enum_values(flags))

    def find_grant_position(self, acl: Sequence[Mapping[str, Any]]) -> int:
        """
        Return a canonically ordered position for a new allow ACE.

        The canonical ACL order is explicit (non-inherited) denies followed by
        explicit allows followed by denies inherited from parent, allows
        inherited from parent, denies inherited from grandparent, and so on.
        So, any position between the last explicit deny and the first inherited
        ACE is correct.  This method chooses the position immediately before the
        first inherited ACE.

        Note that this has no special logic to locate a correct position for a
        new ACE that has the inherited flag set. The correct position for such
        an ACE is not well defined given that the ACE is not actually inherited.
        If the position is not specified explicitly, it might as well go where a
        normal explicit ACE would.
        """
        for pos, ace in enumerate(acl):
            if INHERITED_FLAG in ace['flags']:
                return pos
        return len(acl)


def pretty_acl(body: MutableMapping[str, Any]) -> str:
    # Print "None" if there are no POSIX special permissions
    if len(body['posix_special_permissions']) == 0:
        body['posix_special_permissions'] = ['None']

    res = 'Control: {}\n'.format(
        ', '.join([r.replace('_', ' ').capitalize() for r in body['control']])
    )
    res += 'Posix Special Permissions: {}\n'.format(
        ', '.join([r.replace('_', ' ').capitalize() for r in body['posix_special_permissions']])
    )
    res += '\nPermissions:\n'
    res += AclEditor(FsAceTranslator(), body['aces']).pretty_str()
    return res


def pretty_acl_response(response: request.RestResponse, print_json: bool) -> str:
    if print_json:
        return str(response)
    else:
        body, _etag = response
        return pretty_acl(body)


class GetAclCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_get_acl'
    SYNOPSIS = 'Get file ACL'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')
        parser.add_argument('--snapshot', help='Snapshot ID to read from', type=int)
        parser.add_argument('--json', action='store_true', help='Print raw response JSON')

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            pretty_acl_response(
                fs.get_acl_v2(
                    rest_client.conninfo,
                    rest_client.credentials,
                    args.path,
                    args.id,
                    snapshot=args.snapshot,
                ),
                args.json,
            )
        )


class SetAclCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_set_acl'
    SYNOPSIS = 'Set file ACL'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')
        parser.add_argument(
            '--file',
            help=(
                'Local file containing ACL JSON with control flags, '
                'ACEs, and optionally special POSIX permissions '
                '(sticky, setgid, setuid)'
            ),
            required=False,
            type=str_decode,
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        if not bool(args.file):
            raise ValueError('Must specify --file')

        with open(args.file) as f:
            contents = f.read()
            try:
                acl = json.loads(contents)
            except ValueError as e:
                raise ValueError('Error parsing ACL data: %s\n' % str(e))

        print(
            fs.set_acl_v2(
                rest_client.conninfo, rest_client.credentials, acl, path=args.path, id_=args.id
            )
        )


ALLOWED_TYPE = 'ALLOWED'
DENIED_TYPE = 'DENIED'

TYPE_CHOICES = sorted(tc.capitalize() for tc in [ALLOWED_TYPE, DENIED_TYPE])
FLAG_CHOICES = sorted(fc.replace('_', ' ').capitalize() for fc in ALL_FLAGS)

SPECIAL_POSIX_PERMISSIONS = ['STICKY_BIT', 'SET_GID', 'SET_UID']
SPECIAL_POSIX_CHOICES = [sp.replace('_', ' ').capitalize() for sp in SPECIAL_POSIX_PERMISSIONS]


def _put_new_acl(
    fs_mod: Any,
    conninfo: request.Connection,
    creds: Optional[Credentials],
    acl: Mapping[str, Any],
    editor: AclEditor,
    etag: str,
    args: argparse.Namespace,
) -> str:
    acl = {
        'control': acl['control'],
        'posix_special_permissions': acl['posix_special_permissions'],
        'aces': editor.acl,
    }

    result = fs_mod.set_acl_v2(conninfo, creds, acl, path=args.path, id_=args.id, if_match=etag)

    if args.json:
        return str(result)
    else:
        body, etag = result
        return 'New permissions:\n{}'.format(
            AclEditor(FsAceTranslator(), body['aces']).pretty_str()
        )


def do_add_entry(
    fs_mod: Any,
    conninfo: request.Connection,
    creds: Optional[Credentials],
    args: argparse.Namespace,
) -> str:
    acl, etag = fs_mod.get_acl_v2(conninfo, creds, args.path, args.id)

    translator = FsAceTranslator()
    editor = AclEditor(translator, acl['aces'])
    ace_type = translator.parse_type_enum_value(args.type)
    if ace_type == ALLOWED_TYPE:
        editor.grant([args.trustee], args.rights, args.flags, args.insert_after)
    else:
        assert ace_type == DENIED_TYPE
        editor.deny([args.trustee], args.rights, args.flags, args.insert_after)

    return _put_new_acl(fs_mod, conninfo, creds, acl, editor, etag, args)


def do_remove_entry(
    fs_mod: Any,
    conninfo: request.Connection,
    creds: Optional[Credentials],
    args: argparse.Namespace,
) -> str:
    acl, etag = fs_mod.get_acl_v2(conninfo, creds, args.path, args.id)

    editor = AclEditor(FsAceTranslator(), acl['aces'])
    editor.remove(
        position=args.position,
        trustee=args.trustee,
        ace_type=args.type,
        rights=args.rights,
        flags=args.flags,
        allow_multiple=args.all_matching,
    )

    if args.dry_run:
        return f'New permissions would be:\n{editor.pretty_str()}'

    return _put_new_acl(fs_mod, conninfo, creds, acl, editor, etag, args)


def do_modify_entry(
    fs_mod: Any,
    conninfo: request.Connection,
    creds: Optional[Credentials],
    args: argparse.Namespace,
) -> str:
    acl, etag = fs_mod.get_acl_v2(conninfo, creds, args.path, args.id)
    editor = AclEditor(FsAceTranslator(), acl['aces'])
    editor.modify(
        args.position,
        args.old_trustee,
        args.old_type,
        args.old_rights,
        args.old_flags,
        args.new_trustee,
        args.new_type,
        args.new_rights,
        args.new_flags,
        args.all_matching,
    )

    if args.dry_run:
        return f'New permissions would be:\n{editor.pretty_str()}'

    return _put_new_acl(fs_mod, conninfo, creds, acl, editor, etag, args)


def do_set_posix(
    fs_mod: Any, conninfo: request.Connection, creds: Credentials, args: argparse.Namespace
) -> str:
    bits = [p.replace(' ', '_').upper() for p in args.permissions]
    assert all(b in SPECIAL_POSIX_PERMISSIONS for b in bits)

    # XXX iain: PATCH would be real nice...
    acl, etag = fs_mod.get_acl_v2(conninfo, creds, args.path, args.id)
    acl['posix_special_permissions'] = bits
    result = fs_mod.set_acl_v2(conninfo, creds, acl, path=args.path, id_=args.id, if_match=etag)

    return pretty_acl_response(result, args.json)


class ModifyAclCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_modify_acl'
    SYNOPSIS = 'Modify file ACL'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')

        parser.add_argument('--json', action='store_true', help='Print the raw JSON response.')

        subparsers = parser.add_subparsers()

        add_entry = subparsers.add_parser('add_entry', help="Add an entry to the file's ACL.")
        add_entry.set_defaults(function=do_add_entry)
        add_entry.add_argument(
            '-t',
            '--trustee',
            type=str_decode,
            required=True,
            help=(
                'The trustee to add.  e.g. Everyone, uid:1000, gid:1001, '
                'sid:S-1-5-2-3-4, or auth_id:500'
            ),
        )
        add_entry.add_argument(
            '-y',
            '--type',
            type=str_decode,
            required=True,
            choices=TYPE_CHOICES,
            help='Whether the trustee should be allowed or denied the given rights',
        )
        add_entry.add_argument(
            '-r',
            '--rights',
            type=str_decode,
            nargs='+',
            required=True,
            metavar='RIGHT',
            help='The rights that should be allowed or denied.  Choices: '
            + ', '.join(RIGHT_CHOICES),
        )
        add_entry.add_argument(
            '-f',
            '--flags',
            type=str_decode,
            nargs='*',
            metavar='FLAG',
            choices=FLAG_CHOICES,
            help='The flags the entry should have. Choices: ' + ', '.join(FLAG_CHOICES),
        )
        # Allows specification of the position after which the new ACE will be
        # inserted.  That is, 0 will insert at the beginning, 1 will insert
        # after the first entry, etc.
        # Hidden because overriding the default canonical position is not
        # recommended.
        add_entry.add_argument('--insert-after', type=int, default=None, help=SUPPRESS)

        remove_entry = subparsers.add_parser(
            'remove_entry', help="Remove an entry from the file's ACL."
        )
        remove_entry.set_defaults(function=do_remove_entry)
        remove_entry.add_argument(
            '-p', '--position', type=int, help='The position of the entry to remove.'
        )
        remove_entry.add_argument(
            '-t',
            '--trustee',
            type=str_decode,
            help=(
                'Remove an entry with this trustee.  e.g. Everyone, '
                'uid:1000, gid:1001, sid:S-1-5-2-3-4, or auth_id:500'
            ),
        )
        remove_entry.add_argument(
            '-y',
            '--type',
            type=str_decode,
            choices=TYPE_CHOICES,
            help='Remove an entry of this type',
        )
        remove_entry.add_argument(
            '-r',
            '--rights',
            type=str_decode,
            nargs='+',
            metavar='RIGHT',
            help='Remove an entry with these rights.  Choices: ' + ', '.join(RIGHT_CHOICES),
        )
        remove_entry.add_argument(
            '-a',
            '--all-matching',
            action='store_true',
            help='If multiple entries match the arguments, remove all of them',
        )
        remove_entry.add_argument(
            '-f',
            '--flags',
            type=str_decode,
            nargs='*',
            metavar='FLAG',
            choices=FLAG_CHOICES,
            help='Remove an entry with these flags. Choices: ' + ', '.join(FLAG_CHOICES),
        )
        remove_entry.add_argument(
            '-d',
            '--dry-run',
            action='store_true',
            help='Do nothing; display what the result of the change would be.',
        )

        modify_entry = subparsers.add_parser(
            'modify_entry', help='Modify an existing permission entry in place'
        )
        modify_entry.set_defaults(function=do_modify_entry)
        modify_entry.add_argument(
            '-p', '--position', type=int, help='The position of the entry to modify.'
        )
        modify_entry.add_argument(
            '--old-trustee',
            type=str_decode,
            help=(
                'Modify an entry with this trustee.  e.g. Everyone, '
                'uid:1000, gid:1001, sid:S-1-5-2-3-4, or auth_id:500'
            ),
        )
        modify_entry.add_argument(
            '--old-type', type=str_decode, choices=TYPE_CHOICES, help='Modify an entry of this type'
        )
        modify_entry.add_argument(
            '--old-rights',
            type=str_decode,
            nargs='+',
            metavar='RIGHT',
            help='Modify an entry with these rights.  Choices: ' + ', '.join(RIGHT_CHOICES),
        )
        modify_entry.add_argument(
            '--old-flags',
            type=str_decode,
            nargs='*',
            metavar='FLAG',
            choices=FLAG_CHOICES,
            help='Modify an entry with these flags. Choices: ' + ', '.join(FLAG_CHOICES),
        )
        modify_entry.add_argument(
            '--new-trustee',
            type=str_decode,
            help=(
                'Set the entry to have this trustee.  e.g. Everyone, '
                'uid:1000, gid:1001, sid:S-1-5-2-3-4, or auth_id:500'
            ),
        )
        modify_entry.add_argument(
            '--new-type', type=str_decode, choices=TYPE_CHOICES, help='Set the type of the entry.'
        )
        modify_entry.add_argument(
            '--new-rights',
            type=str_decode,
            nargs='+',
            metavar='RIGHT',
            help='Set the rights of the entry.  Choices: ' + ', '.join(RIGHT_CHOICES),
        )
        modify_entry.add_argument(
            '--new-flags',
            type=str_decode,
            nargs='*',
            metavar='FLAG',
            choices=FLAG_CHOICES,
            help='Set the flags of the entry. Choices: ' + ', '.join(FLAG_CHOICES),
        )
        modify_entry.add_argument(
            '-a',
            '--all-matching',
            action='store_true',
            help='If multiple entries match the arguments, modify all of them',
        )
        modify_entry.add_argument(
            '-d',
            '--dry-run',
            action='store_true',
            help='Do nothing; display what the result of the change would be.',
        )

        set_posix = subparsers.add_parser(
            'set_posix_special_permissions', help='Set the Set UID, Set GID, and Sticky bits.'
        )
        set_posix.set_defaults(function=do_set_posix)
        # Should probably just be positional, but argparse seemingly has a bug
        # where it won't accept zero choices for a positional argument.
        set_posix.add_argument(
            '-p',
            '--permissions',
            choices=SPECIAL_POSIX_CHOICES,
            required=True,
            nargs='*',
            help='The special posix bits that should be set',
        )

    @staticmethod
    def main(
        rest_client: RestClient,
        args: argparse.Namespace,
        outfile: IO[str] = sys.stdout,
        fs_mod: Any = fs,
    ) -> None:
        if not hasattr(args, 'function'):
            raise ValueError('Sub-command is required')
        outfile.write(
            f'{args.function(fs_mod, rest_client.conninfo, rest_client.credentials, args)}\n'
        )


class CreateFileCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_create_file'
    SYNOPSIS = 'Create a new file'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'Parent directory')
        parser.add_argument('--name', type=str_decode, help='New file name', required=True)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            fs.create_file(
                rest_client.conninfo,
                rest_client.credentials,
                args.name,
                dir_path=args.path,
                dir_id=args.id,
            )
        )


class CreateDirectoryCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_create_dir'
    SYNOPSIS = 'Create a new directory'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'Parent directory')
        parser.add_argument('--name', type=str_decode, help='New directory name', required=True)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            fs.create_directory(
                rest_client.conninfo,
                rest_client.credentials,
                args.name,
                dir_path=args.path,
                dir_id=args.id,
            )
        )


# This is the list of FS_FILE_TYPEs that matter in terms of the create symlink
# API. The API accepts all possible FS_FILE_TYPEs, but only makes decisions
# based on these three. Others are simply ignored and treated the same as
# FS_FILE_TYPE_UNKNOWN
CREATE_SYMLINK_FS_FILE_TYPES = [
    'FS_FILE_TYPE_UNKNOWN',
    'FS_FILE_TYPE_FILE',
    'FS_FILE_TYPE_DIRECTORY',
]


class CreateSymlinkCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_create_symlink'
    SYNOPSIS = 'Create a new symbolic link'
    DESCRIPTION = textwrap.dedent(
        """\
        This command will create a symlink.

        The --target option takes the path of the symlink target, and will be
        interpreted by clients, not the qumulo filesystem. If you are accessing
        this symlink via an NFS export or SMB share then the client will
        interpret this symlink target as-is but from the perspective of its
        local filesystem mount tree and not qumulo's file system or share/export
        path.

        As such, we recommend using relative paths for symlink targets when they
        will be accessed via exports/shares so that they will reliably resolve
        to qumulo file system mountpoints. This also avoids encoding the
        mountpoint inside the symlink path which necessitates a rewrite of the
        symlinks if client mountpoints change or vary.
        """
    )
    EPILOG = textwrap.dedent(
        """\
        Examples:

        Given NFS Export:
          export-path (not real fs path): /user_export
          fs-path: /home/user/export
          client mounted /user_export at: /mnt/user_mount

        Correct usage: Successfully creating a symlink with a relative path inside the export:

          qq fs_create_symlink --path /home/user/export --target file0 --name sym0
          creates symlink /home/user/export/sym0 -> file0

          > ls -l /mnt/user_mount/
          -rw-r--r-- 1 root  nogroup      6 Jul 14 17:02 file0
          lrwxrwxrwx 1 root  nogroup      5 Jul 14 16:53 sym0 -> file0

          Then if the client reads /mnt/user_mount/sym0 it will get the contents
          of qumulo file /home/user/export/file0 because the client interprets the
          'file0' target path as the /mnt/user_mount/file0 in its local filesystem
          mount tree and properly traverse into the NFS export.

        Incorrect usage: creating a symlink with an absolute path that unexpectedly
        resolves to a client-local directory instead of the qumulo filesystem
        directory (probably not intended):

          qq fs_create_symlink --path /home/user/export --target /home/user/export/file0 --name sym1
          creates symlink /home/user/export/sym1 -> /home/user/export/file0

          > ls -l /mnt/user_mount/
          total 4
          -rw-r--r-- 1 root  nogroup      6 Jul 14 17:02 file0
          lrwxrwxrwx 1 root  nogroup      5 Jul 14 16:53 sym1 -> /home/user/export/file0

          Then if the client reads /mnt/user_mount/sym1 it will look at the
          client's local /home/user/export directory and NOT qumulo's /home/user/export

        Incorrect usage: Unsuccessfully using the export-path (/user_export) instead of
        the fs-path (/home/user/export) for the directory in which to create the symlink:

          qq fs_create_symlink --path /user_export --target file0 --name sym0
          > Error 404: fs_no_such_entry_error: user_export
    """
    )

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'Parent directory')
        parser.add_argument(
            '--target', help='Link target (relative path recommended)', required=True
        )
        parser.add_argument(
            '--target-type',
            choices=CREATE_SYMLINK_FS_FILE_TYPES,
            help=(
                "Symlink target's type. If this is unspecified or FS_FILE_TYPE_UNKNOWN,"
                " the effect is the same as using 'ln -s' on a Unix NFS client. If this is "
                'FS_FILE_TYPE_FILE or FS_FILE_TYPE_DIRECTORY, the effect is the same as '
                "using 'mklink' or 'mklink /D' on a Windows SMB client."
            ),
        )
        parser.add_argument('--name', help='New symlink name', required=True)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            fs.create_symlink(
                rest_client.conninfo,
                rest_client.credentials,
                args.name,
                args.target,
                dir_path=args.path,
                dir_id=args.id,
                target_type=args.target_type,
            )
        )


def parse_major_minor_numbers(major_minor_numbers: Optional[str]) -> Optional[Dict[str, int]]:
    if major_minor_numbers is None:
        return None
    major, _, minor = major_minor_numbers.partition(',')
    return {'major': int(major), 'minor': int(minor)}


class CreateUNIXFileCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_create_unix_file'
    SYNOPSIS = 'Create a new pipe, character device, block device or socket'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        TYPES = (
            'FS_FILE_TYPE_UNIX_PIPE, FS_FILE_TYPE_UNIX_CHARACTER_DEVICE,'
            ' FS_FILE_TYPE_UNIX_BLOCK_DEVICE, FS_FILE_TYPE_UNIX_SOCKET'
        )

        add_ref_arguments(parser, 'Parent directory')
        parser.add_argument(
            '--major-minor-numbers',
            metavar='major,minor',
            help='Major and minor numbers for Character Device or Block Device',
        )
        parser.add_argument('--name', help='New file name', required=True)
        parser.add_argument('--type', help=f'Type of UNIX file to create: {TYPES}', required=True)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        major_minor_numbers = parse_major_minor_numbers(args.major_minor_numbers)
        print(
            fs.create_unix_file(
                rest_client.conninfo,
                rest_client.credentials,
                name=args.name,
                file_type=args.type,
                major_minor_numbers=major_minor_numbers,
                dir_path=args.path,
                dir_id=args.id,
            )
        )


class CreateLinkCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_create_link'
    SYNOPSIS = 'Create a new link'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'Parent directory')
        parser.add_argument('--target', help='Link target', required=True)
        parser.add_argument('--name', help='New link name', required=True)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            fs.create_link(
                rest_client.conninfo,
                rest_client.credentials,
                args.name,
                args.target,
                dir_path=args.path,
                dir_id=args.id,
            )
        )


class RenameCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_rename'
    SYNOPSIS = 'Rename a file system object'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'Destination parent directory')
        parser.add_argument('--source', help='Source file path', required=True)
        parser.add_argument('--name', help='New name in destination directory', required=True)
        parser.add_argument('--clobber', action='store_true', help='Clobber destination if exists')

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            fs.rename(
                rest_client.conninfo,
                rest_client.credentials,
                args.name,
                args.source,
                dir_path=args.path,
                dir_id=args.id,
                clobber=args.clobber,
            )
        )


class DeleteCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_delete'
    SYNOPSIS = 'Delete a file system object'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File system object')

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        fs.delete(rest_client.conninfo, rest_client.credentials, path=args.path, id_=args.id)
        print('File system object was deleted.')


class UnlinkCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_unlink'
    SYNOPSIS = 'Delete a directory entry by name'
    DESCRIPTION = textwrap.dedent(
        """\
        Delete the link specified by name in the given parent directory.
        The file system object is deleted if this was its last link.
    """
    )

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'Parent directory')
        parser.add_argument('--name', help='Entry to delete', required=True, type=str_decode)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        fs.unlink(
            rest_client.conninfo,
            rest_client.credentials,
            dir_path=args.path,
            dir_id=args.id,
            entry_name=args.name,
        )
        print('Directory entry was deleted.')


class WriteFileCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_write'
    SYNOPSIS = 'Write data to an object'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')

        stream_group = parser.add_mutually_exclusive_group()
        stream_group.add_argument('--stream-id', help='Stream ID', type=str_decode)
        stream_group.add_argument('--stream-name', help='Stream name', type=str_decode)
        stream_group.add_argument(
            '--create',
            action='store_true',
            help='Create file before writing. Fails if exists or is used with stream identifiers.',
        )

        parser.add_argument(
            '--offset',
            type=int,
            help=(
                'Offset at which to write data. If not specified, the existing'
                ' contents of the file will be replaced with the given '
                'contents.'
            ),
        )
        parser.add_argument('--file', help='File data to send', type=str_decode)
        parser.add_argument('--stdin', action='store_true', help='Write file from stdin')

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        if args.id and args.create:
            raise ValueError('cannot use --create with --id')

        if args.stdin:
            if args.file:
                raise ValueError('--stdin conflicts with --file')

            infile = sys.stdin.buffer

        elif args.file:
            if not os.path.isfile(args.file):
                raise ValueError('%s is not a file' % args.file)

            infile = open(args.file, 'rb')

        else:
            raise ValueError('Must specify --stdin or --file')

        if args.create:
            dirname, basename = util.unix_path_split(args.path)
            if not basename:
                raise ValueError('Path has no basename')
            fs.create_file(rest_client.conninfo, rest_client.credentials, basename, dirname)

        print(
            fs.write_file(
                rest_client.conninfo,
                rest_client.credentials,
                data_file=infile,
                path=args.path,
                id_=args.id,
                offset=args.offset,
                stream_id=get_stream_id(rest_client.conninfo, rest_client.credentials, args),
            )
        )


class TrackedProgressBar:
    def __init__(self, progress_bar: Any):
        self.progress_bar = progress_bar
        self.current = 0

    def update(self, progress: int) -> None:
        self.current += progress
        self.progress_bar.update(progress)

    def update_to_completion(self) -> None:
        delta = self.progress_bar.total - self.current
        if delta > 0:
            self.update(delta)


class CopyCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_copy'
    SYNOPSIS = 'Server-side copy a file.'
    DESCRIPTION = textwrap.dedent(
        """\
        This command will create a file by copying a source file's attributes
        and data for all streams. You can omit copying attributes and named
        streams with command line options.

        If you choose to --overwrite an existing file, that file will be
        removed before creating the new file as the copy destination.

        Data copying is done server side but driven by the client. This allows
        better performance while still being interruptible.

        An independent change to either the source or destination file during
        the copy is detected and results in an error. If the command is
        interrupted or an error occurs while copying, the destination file is
        left on the cluster.
    """
    )

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument('source', type=str_decode, help='Source file absolute path')
        parser.add_argument('target', type=str_decode, help='Target file absolute path')

        parser.add_argument('--source-snapshot', type=int, help='Snapshot ID to copy from')
        parser.add_argument(
            '--overwrite', action='store_true', help='Overwrite an existing target file'
        )
        parser.add_argument('--quiet', action='store_true', help='Do not show progress bar')
        parser.add_argument(
            '--no-attributes',
            action='store_true',
            help='Do not copy file attributes and ACLs in addition to data',
        )
        parser.add_argument(
            '--no-named-streams', action='store_true', help='Do not copy named streams'
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        if args.source == args.target and not args.source_snapshot:
            raise ValueError('Target file and source file are the same.')

        source_attrs, source_etag = fs.get_file_attr(
            rest_client.conninfo,
            rest_client.credentials,
            path=args.source,
            snapshot=args.source_snapshot,
        )

        if source_attrs['type'] != 'FS_FILE_TYPE_FILE':
            raise ValueError('Only regular files can be copied')

        total_bytes = int(source_attrs['size'])
        total_streams = 1

        source_id = source_attrs['id']

        if not args.no_attributes:
            source_acl, _source_acl_etag = fs.get_acl_v2(
                rest_client.conninfo,
                rest_client.credentials,
                id_=source_id,
                snapshot=args.source_snapshot,
            )

        if not args.no_named_streams:
            source_named_streams, _source_streams_etag = fs.list_named_streams(
                rest_client.conninfo,
                rest_client.credentials,
                id_=source_id,
                snapshot=args.source_snapshot,
            )
            total_bytes += sum(int(x['size']) for x in source_named_streams)
            total_streams += len(source_named_streams)
        else:
            source_named_streams = []

        # Test if the target exists and remove it before creating if
        # --overwrite is specified. We create a new file always so that other
        # links to the target aren't disrupted and because it makes this code
        # simpler. This is like the --remove-destination argument to cp(1).
        #
        # XXX scott: it would be nice if create_file took a clobber option that
        # was translated over the rest api into an atomic unlink on create with
        # a new enum choice in duplicate_create_mode. Until then this is kind
        # or racy and janky.
        try:
            fs.get_file_attr(rest_client.conninfo, rest_client.credentials, path=args.target)
            if args.overwrite:
                fs.delete(rest_client.conninfo, rest_client.credentials, path=args.target)
            else:
                raise ValueError(
                    f'Target file {args.target} exists. Use --overwrite to overwrite it.'
                )
        except request.RequestError as e:
            if e.error_class != 'fs_no_such_entry_error':
                raise

        dir_path, name = os.path.split(args.target)
        target_attrs, target_etag = fs.create_file(
            rest_client.conninfo, rest_client.credentials, name=name, dir_path=dir_path
        )

        target_id = target_attrs['id']

        with tqdm(
            desc='Copying', unit='B', total=total_bytes, unit_scale=True, disable=args.quiet
        ) as copy_progress:
            copy_progress.set_description(f'Copying stream 1/{total_streams}')

            # track total bytes copied so that we can update the progress bar
            # for small files that don't cause tqdm to update
            progress_tracker = TrackedProgressBar(copy_progress)

            target_etag = fs.copy(
                rest_client.conninfo,
                rest_client.credentials,
                source_id=source_id,
                source_stream_id='0',
                source_snapshot=args.source_snapshot,
                source_etag=source_etag,
                target_id=target_id,
                target_etag=target_etag,
                progress_tracker=progress_tracker,
            )

            for i, source_stream in enumerate(source_named_streams):
                copy_progress.set_description(f'Copying stream {2 + i}/{total_streams}')

                target_stream, target_etag = fs.create_stream(
                    rest_client.conninfo,
                    rest_client.credentials,
                    stream_name=source_stream['name'],
                    id_=target_id,
                    if_match=target_etag,
                )

                target_etag = fs.copy(
                    rest_client.conninfo,
                    rest_client.credentials,
                    source_id=source_id,
                    source_stream_id=source_stream['id'],
                    source_snapshot=args.source_snapshot,
                    source_etag=source_etag,
                    target_id=target_id,
                    target_stream_id=target_stream['id'],
                    target_etag=target_etag,
                    progress_tracker=progress_tracker,
                )

            copy_progress.set_description('Copying done')

        if not args.no_attributes:
            _attr, target_etag = fs.set_file_attr(
                rest_client.conninfo,
                rest_client.credentials,
                id_=target_id,
                owner=source_attrs['owner'],
                group=source_attrs['group'],
                creation_time=source_attrs['creation_time'],
                access_time=source_attrs['access_time'],
                modification_time=source_attrs['modification_time'],
                change_time=source_attrs['change_time'],
                extended_attributes=source_attrs['extended_attributes'],
                if_match=target_etag,
            )
            fs.set_acl_v2(
                rest_client.conninfo,
                rest_client.credentials,
                id_=target_id,
                acl=source_acl,
                if_match=target_etag,
            )


class ReadFileCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_read'
    SYNOPSIS = 'Read an object'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')

        stream_group = parser.add_mutually_exclusive_group()
        stream_group.add_argument('--stream-id', help='Stream ID', type=str_decode)
        stream_group.add_argument('--stream-name', help='Stream name', type=str_decode)

        parser.add_argument('--snapshot', help='Snapshot ID to read from', type=int)
        parser.add_argument(
            '--offset',
            type=int,
            help=(
                'Offset at which to read data. If not specified, read from the'
                ' beginning of the file.'
            ),
        )
        parser.add_argument(
            '--length',
            type=int,
            help='Amount of data to read. If not specified, read the entire file.',
        )
        parser.add_argument('--file', help='File to receive data', type=str_decode)
        parser.add_argument('--force', action='store_true', help='Overwrite an existing file')
        parser.add_argument(
            '--stdout', action='store_const', const=True, help='Output data to standard out'
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        if args.stdout:
            if args.file:
                raise ValueError('--stdout conflicts with --file')
        elif args.file:
            if os.path.exists(args.file) and not args.force:
                raise ValueError('%s already exists.' % args.file)
        else:
            raise ValueError('Must specify --stdout or --file')

        if args.file is None:
            f = sys.stdout.buffer
        else:
            f = open(args.file, 'wb')

        fs.read_file(
            rest_client.conninfo,
            rest_client.credentials,
            f,
            path=args.path,
            id_=args.id,
            snapshot=args.snapshot,
            offset=args.offset,
            length=args.length,
            stream_id=get_stream_id(rest_client.conninfo, rest_client.credentials, args),
        )


class ReadDirectoryCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_read_dir'
    SYNOPSIS = 'Read directory'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'Directory')
        parser.add_argument(
            '--page-size',
            type=int,
            help=(
                'REST API pagination size to use. This affects the number of API calls made, and '
                'the structure of the resulting JSON output, but does not affect what entries '
                'are returned. Note that the system may impose an upper limit on the page size.'
            ),
        )
        parser.add_argument('--snapshot', help='Snapshot ID to read from', type=int)
        parser.add_argument('--smb-pattern', type=str_decode, help='SMB style match pattern.')

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        if args.page_size is not None and args.page_size < 1:
            raise ValueError('Page size must be greater than 0')

        page = fs.read_directory(
            rest_client.conninfo,
            rest_client.credentials,
            page_size=args.page_size,
            path=args.path,
            id_=args.id,
            snapshot=args.snapshot,
            smb_pattern=args.smb_pattern,
        ).data

        print(request.pretty_json(page))

        next_uri = page['paging']['next']
        while next_uri != '':
            page = rest_client.request('GET', next_uri)
            print(request.pretty_json(page))
            next_uri = page['paging']['next']


class ReadDirectoryCapacityCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_read_dir_aggregates'
    SYNOPSIS = (
        'Read aggregated data for the specified directory. '
        "To include the directory's children, use the --recursive flag."
    )

    RECURSIVE_HELP = textwrap.dedent(
        """\
        This operation performs a breadth-first traversal of directories up to the limit specified
        by the --max_entries and --max_depth flags, or up to the system-imposed limit. It omits
        directory entries which are smaller than 10%% of the directory's total size.
        """
    )

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'Directory')
        parser.add_argument(
            '--recursive', action='store_true', help=ReadDirectoryCapacityCommand.RECURSIVE_HELP
        )
        parser.add_argument('--max-entries', help='Maximum number of entries to return', type=int)
        parser.add_argument(
            '--max-depth', help='Maximum depth to recurse when --recursive is set', type=int
        )
        parser.add_argument(
            '--order-by',
            choices=AGG_ORDERING_CHOICES,
            help='Specify field used for top N selection and sorting',
        )
        parser.add_argument('--snapshot', type=int, help='Snapshot ID to read from')

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            fs.read_dir_aggregates(
                rest_client.conninfo,
                rest_client.credentials,
                path=args.path,
                id_=args.id,
                recursive=args.recursive,
                max_entries=args.max_entries,
                max_depth=args.max_depth,
                order_by=args.order_by,
                snapshot=args.snapshot,
            )
        )


class TreeWalkCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_walk_tree'
    SYNOPSIS = 'Walk file system tree'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument(
            '--path', help='Tree root path', type=str_decode, required=False, default='/'
        )
        parser.add_argument('--snapshot', help='Snapshot ID to read from', type=int)

        file_type_filter = parser.add_mutually_exclusive_group()
        file_type_filter.add_argument(
            '--file-only',
            help='Only display files',
            action='store_const',
            const='FS_FILE_TYPE_FILE',
            dest='type_filter',
        )
        file_type_filter.add_argument(
            '--directory-only',
            help='Only display directories',
            action='store_const',
            const='FS_FILE_TYPE_DIRECTORY',
            dest='type_filter',
        )
        file_type_filter.add_argument(
            '--symlink-only',
            help='Only display symlinks',
            action='store_const',
            const='FS_FILE_TYPE_SYMLINK',
            dest='type_filter',
        )

        display_group = parser.add_mutually_exclusive_group()
        display_group.add_argument(
            '--display-ownership',
            help='Display detailed owner and group information',
            action='store_true',
        )
        display_group.add_argument(
            '--display-all-attributes', help='Display all attributes', action='store_true'
        )

        parser.add_argument(
            '--output-file',
            help='Output a file at the specified path instead of stdout',
            type=str_decode,
            required=False,
            default=None,
        )

        parser.add_argument(
            '--max-depth',
            help=(
                'The maximum layers to traverse down the tree, starting from '
                'the path specified. For example, if the file tree is '
                '/dir/file, running the command with max-depth of 1 from root '
                'will yield / and /dir'
            ),
            type=int,
            required=False,
            default=sys.maxsize,
        )

    @staticmethod
    def write_file_tree_to_file(
        conninfo: request.Connection,
        credentials: Optional[Credentials],
        args: argparse.Namespace,
        fh: IO[str],
    ) -> None:
        fh.write('{"tree_nodes": [\n')
        first_entry = True

        def file_should_be_filtered(f: Mapping[str, Any]) -> bool:
            return args.type_filter and args.type_filter != f['type']

        for f, _etag in fs.tree_walk_preorder(
            conninfo, credentials, args.path, args.snapshot, max_depth=args.max_depth
        ):
            if file_should_be_filtered(f):
                continue

            if args.display_all_attributes:
                data = f
            else:
                data = {}
                data['path'] = f['path']
                data['size'] = f['size']
                data['type'] = f['type']
                data['id'] = f['id']
                if args.display_ownership:
                    data['owner'] = f['owner']
                    data['group'] = f['group']
                    data['owner_id_type'] = f['owner_details']['id_type']
                    data['owner_id_value'] = f['owner_details']['id_value']
                    data['group_id_type'] = f['group_details']['id_type']
                    data['group_id_value'] = f['group_details']['id_value']

            # A new line for each tree node, for better readability
            if not first_entry:
                fh.write(',\n')

            first_entry = False
            fh.write(pretty_json(data, sort_keys=False, indent=None))

        fh.write(']}\n')

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        if args.output_file is None:
            fh = sys.stdout
        else:
            fh = open(args.output_file, 'w')

        TreeWalkCommand.write_file_tree_to_file(
            rest_client.conninfo, rest_client.credentials, args, fh
        )

        # Close open file handle, if any
        if args.output_file is not None:
            fh.close()


class GetFileSamplesCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_file_samples'
    SYNOPSIS = 'Get a number of sample files from the file system'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'Query root')
        parser.add_argument('--count', type=int, required=True)
        parser.add_argument(
            '--sample-by',
            choices=['capacity', 'data', 'file', 'named_streams'],
            help=(
                'Weight the sampling by the value specified: capacity (total '
                'bytes used for data and metadata), data (total bytes used for '
                'data only), file (file count), named_streams (named stream count)'
            ),
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            fs.get_file_samples(
                rest_client.conninfo,
                rest_client.credentials,
                args.path,
                args.count,
                args.sample_by,
                id_=args.id,
            )
        )


class ResolvePathsCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_resolve_paths'
    SYNOPSIS = 'Resolve file IDs to paths'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument('--ids', required=True, nargs='*', help='File IDs to resolve')
        parser.add_argument('--snapshot', help='Snapshot ID to read from', type=int)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            fs.resolve_paths(
                rest_client.conninfo, rest_client.credentials, args.ids, snapshot=args.snapshot
            )
        )


class LockIter:
    def __init__(
        self,
        rest_client: RestClient,
        first_page: Dict[str, Any],
        page_limit: int,
        res_type: str,
        want_paths: bool,
        want_hostnames: bool,
    ) -> None:
        """
        This is a streaming iterator over a list of locks, i.e. it fetches pages
        as needed without loading the full list in to memory first.  It is
        intended to be created via the @ref all and @ref by_file factory methods

        @p first_page the first page of results, as returned by
            list_locks_by_file or list_locks_by_client.
        @p page_limit the number of results per page.
        @p res_type whether the results are pages of 'grants' or 'waiters'.
        @p want_paths whether file ids should be resolved to full paths.
        @p want_hostnames whether ip addresses should be resolved to hostnames
        """
        self.rest_client = rest_client
        self.res_type = res_type
        self.page_limit = page_limit
        self.want_paths = want_paths
        self.want_hostnames = want_hostnames

        self.resolved_paths: Dict[str, Optional[str]] = {}
        self.resolved_hostnames: Dict[str, Optional[str]] = {}
        self.entry_iter: Optional[Iterator[Dict[str, Any]]] = None
        self._advance_to_page(first_page)

    def __next__(self) -> Dict[str, Any]:
        assert self.entry_iter is not None
        try:
            return next(self.entry_iter)
        except StopIteration:
            # End of the current page, time to advance.
            # Don't wait for an empty page token or empty result, because that's
            # not guaranteed to terminate when clients are frequently taking
            # new locks.
            if len(self.cur_page[self.res_type]) != self.page_limit:
                raise
            self._advance_to_page(self.rest_client.request('GET', self.cur_page['paging']['next']))
            # If this raises, we're really done:
            return next(self.entry_iter)

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        # Required by iteration protocol
        return self

    def _advance_to_page(self, new_page: Dict[str, Any]) -> None:
        self.cur_page = new_page
        locks = new_page[self.res_type]
        if self.want_paths:
            # Resolve all paths that haven't been seen yet:
            new_ids = list(
                {
                    l['file_id']
                    for l in locks  # noqa: E741
                    if l['file_id'] not in self.resolved_paths
                }
            )
            if new_ids:
                new_paths = self.rest_client.fs.resolve_paths(new_ids)
                for r in new_paths:
                    self.resolved_paths[r['id']] = r['path'] or None
            # Add the paths to the lock entries
            for l in locks:  # noqa: E741
                l['path'] = self.resolved_paths[l['file_id']]
        if self.want_hostnames:
            # Resolve all hostnames that haven't been seen yet
            new_ips = list(
                {
                    l['owner_address']
                    for l in locks  # noqa: E741
                    if l['owner_address'] not in self.resolved_hostnames
                }
            )
            if new_ips:
                new_hostnames = self.rest_client.dns.resolve_ips_to_names(new_ips)
                for h in new_hostnames:
                    # Normalize all failures to "None"
                    if h['result'] != 'OK':
                        self.resolved_hostnames[h['ip_address']] = None
                    else:
                        self.resolved_hostnames[h['ip_address']] = h['hostname'] or None

            # Now map IP to hostnames for all locks
            for l in locks:  # noqa: E741
                l['owner_hostname'] = self.resolved_hostnames[l['owner_address']]
        self.entry_iter = iter(locks)

    @staticmethod
    def by_file(
        rest_client: RestClient,
        protocol: str,
        lock_type: str,
        file_path: Optional[str] = None,
        file_id: Optional[str] = None,
        snapshot_id: Optional[str] = None,
        limit: int = 1000,
        want_paths: bool = False,
        want_hostnames: bool = False,
    ) -> 'LockIter':
        return LockIter(
            rest_client,
            rest_client.fs.list_locks_by_file(
                protocol, lock_type, file_path, file_id, snapshot_id, limit
            ),
            limit,
            'grants',
            want_paths,
            want_hostnames,
        )

    @staticmethod
    def all(
        rest_client: RestClient,
        protocol: str,
        lock_type: str,
        owner_name: Optional[str] = None,
        owner_address: Optional[str] = None,
        limit: int = 1000,
        want_paths: bool = False,
        want_hostnames: bool = False,
    ) -> 'LockIter':
        """
        Iterate over all locks of the given @p lock_type, with optional
        (server-side) filtering on @p owner_name or @p owner_address.
        """
        return LockIter(
            rest_client,
            # The underlying API is somewhat misleadingly named :(
            rest_client.fs.list_locks_by_client(
                protocol, lock_type, owner_name, owner_address, limit
            ),
            limit,
            'grants',
            want_paths,
            want_hostnames,
        )


class ListLocksCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_list_locks'
    SYNOPSIS = 'List file locks held by clients.'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument(
            '--protocol',
            type=str_decode,
            required=True,
            choices={str(p) for p, t in fs.VALID_LOCK_PROTO_TYPE_COMBINATIONS},
            help='The protocol whose locks should be listed',
        )
        parser.add_argument(
            '--lock-type',
            type=str_decode,
            required=True,
            choices={str(t) for p, t in fs.VALID_LOCK_PROTO_TYPE_COMBINATIONS},
            help='The type of lock to list.',
        )

        # Locks can be filtered by file, by client, or not at all:
        filters = parser.add_mutually_exclusive_group(required=False)
        filters.add_argument('--path', type=str_decode, help='File path')
        filters.add_argument('--id', type=str_decode, help='File ID')
        filters.add_argument(
            '--ip', type=str_decode, help='List all locks held by the client with this IP address.'
        )
        filters.add_argument(
            '--hostname',
            type=str_decode,
            help=(
                'List all locks held by the client with this hostname. '
                'Only available for NLM locks.'
            ),
        )

        parser.add_argument(
            '--snapshot',
            type=str_decode,
            help='When a file is specified, list locks held on a specific snapshot.',
        )
        parser.add_argument(
            '--no-resolve',
            dest='resolve',
            default=True,
            action='store_false',
            help=(
                "Don't execute additional API calls to obtain file paths and "
                'client hostnames for results.'
            ),
        )
        parser.add_argument('--json', action='store_true', help='Print a raw JSON response.')
        parser.add_argument(
            '--sort',
            choices=['file', 'client'],
            default=None,
            help='Sort results by this attribute.',
        )

    @staticmethod
    def fmt_lock_mode(lock: Mapping[str, Any]) -> str:
        # Squash the mode enum-array to a short, readable list:
        mode = ', '.join(
            [
                m.replace('API_BYTE_RANGE_', '')
                .replace('API_SHARE_MODE_', '')
                .replace('_', ' ')
                .capitalize()
                for m in lock['mode']
            ]
        )
        # May be byte range, which has a range, or share mode, which doesn't
        if 'offset' in lock:
            return '{} [{}, {})'.format(
                mode, lock['offset'], int(lock['offset']) + int(lock['size'])
            )
        else:
            return mode

    @staticmethod
    def fmt_lock_table(
        locks: Iterable[Mapping[str, Any]], sort_field: str, output: IO[str]
    ) -> None:
        # locks is a streaming iterator, so stream output if possible, which
        # is important when trying to find a file/client that has many locks.

        def map_entry(lock: Mapping[str, Any]) -> Tuple[str, str, str]:
            return (
                ListLocksCommand.fmt_lock_mode(lock),
                lock.get('owner_hostname') or lock['owner_address'],
                lock.get('path') or lock['file_id'],
            )

        if sort_field:
            # This obviously prevents streaming of output:
            sort_field_to_idx = {'client': 1, 'file': 2}

            def sort_key(lock: Mapping[str, Any]) -> Tuple[str, Tuple[str, str, str]]:
                m = map_entry(lock)
                return (m[sort_field_to_idx[sort_field]], m)

            locks = sorted(locks, key=sort_key)

        for l in locks:  # noqa: E741
            output.write('{}\t{}\t{}\n'.format(*map_entry(l)))

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        if args.snapshot and not (args.path or args.id):
            raise ValueError('--snapshot requires --path or --id.')

        # Get the locks
        if args.path or args.id:
            locks = LockIter.by_file(
                rest_client,
                args.protocol,
                args.lock_type,
                args.path,
                args.id,
                args.snapshot,
                want_paths=args.resolve,
                want_hostnames=args.resolve,
            )
        else:
            locks = LockIter.all(
                rest_client,
                args.protocol,
                args.lock_type,
                args.hostname,
                args.ip,
                want_paths=args.resolve,
                want_hostnames=args.resolve,
            )

        if args.json:
            # Emit a valid json array, but stream the entries:
            sys.stdout.write('[')
            first = True
            for l in locks:  # noqa: E741
                if first:
                    first = False
                else:
                    sys.stdout.write(', ')
                sys.stdout.write(pretty_json(l, sort_keys=False))
            sys.stdout.write(']\n')
        else:
            ListLocksCommand.fmt_lock_table(locks, args.sort, sys.stdout)


class ListWaitersByFileCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_list_lock_waiters_by_file'
    SYNOPSIS = 'List waiting lock requests for a particular file'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')
        parser.add_argument(
            '--protocol',
            type=str_decode,
            required=True,
            choices={p for p, t in fs.VALID_WAITER_PROTO_TYPE_COMBINATIONS},
            help='The protocol whose lock waiters should be listed',
        )
        parser.add_argument(
            '--lock-type',
            type=str_decode,
            required=True,
            choices={t for p, t in fs.VALID_WAITER_PROTO_TYPE_COMBINATIONS},
            help='The type of lock whose waiters should be listed',
        )
        parser.add_argument(
            '--snapshot', type=str_decode, help='Snapshot id of the specified file.'
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        if (args.protocol, args.lock_type) not in fs.VALID_WAITER_PROTO_TYPE_COMBINATIONS:
            raise ValueError(
                f'Lock type {args.lock_type} not available for protocol {args.protocol}'
            )

        print(
            pretty_json(
                fs.list_all_waiters_by_file(
                    rest_client.conninfo,
                    rest_client.credentials,
                    args.protocol,
                    args.lock_type,
                    args.path,
                    args.id,
                    args.snapshot,
                ),
                sort_keys=False,
            )
        )


class ListWaitersByClientCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_list_lock_waiters_by_client'
    SYNOPSIS = 'List waiting lock requests for a particular client machine'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument(
            '--protocol',
            type=str_decode,
            required=True,
            choices={p for p, t in fs.VALID_WAITER_PROTO_TYPE_COMBINATIONS},
            help='The protocol whose lock waiters should be listed',
        )
        parser.add_argument(
            '--lock-type',
            type=str_decode,
            required=True,
            choices={t for p, t in fs.VALID_WAITER_PROTO_TYPE_COMBINATIONS},
            help='The type of lock whose waiters should be listed',
        )
        parser.add_argument('--name', help='Client hostname', type=str_decode)
        parser.add_argument('--address', help='Client IP address', type=str_decode)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        if (args.protocol, args.lock_type) not in fs.VALID_WAITER_PROTO_TYPE_COMBINATIONS:
            raise ValueError(
                f'Lock type {args.lock_type} not available for protocol {args.protocol}'
            )

        if args.name and (args.protocol != 'nlm'):
            raise ValueError('--name may only be specified for NLM locks')

        print(
            pretty_json(
                fs.list_all_waiters_by_client(
                    rest_client.conninfo,
                    rest_client.credentials,
                    args.protocol,
                    args.lock_type,
                    args.name,
                    args.address,
                ),
                sort_keys=False,
            )
        )


class ReleaseNLMLocksByClientCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_release_nlm_locks_by_client'
    SYNOPSIS = """Release NLM byte range locks held by client. This method
    releases all locks held by a particular client. This is dangerous, and
    should only be used after confirming that the client is dead."""

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument(
            '--force',
            help='This command can cause corruption, add this flag to release lock',
            action='store_true',
            required=False,
        )
        parser.add_argument('--name', help='Client hostname', type=str_decode)
        parser.add_argument('--address', help='Client IP address', type=str_decode)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        if not args.name and not args.address:
            raise ValueError('Must specify --name or --address')

        if not args.force and not qumulo.lib.opts.ask(
            ReleaseNLMLocksByClientCommand.NAME, LOCK_RELEASE_FORCE_MSG
        ):
            return  # Operation canceled.

        fs.release_nlm_locks_by_client(
            rest_client.conninfo, rest_client.credentials, args.name, args.address
        )
        params = ''
        if args.name:
            params += f'owner_name: {args.name}'
        if args.name and args.address:
            params += ', '
        if args.address:
            params += f'owner_address: {args.address}'
        print(f'NLM byte-range locks held by {params} were released.')


class ReleaseNLMLockCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_release_nlm_lock'
    SYNOPSIS = """Release an arbitrary NLM byte-range lock range. This is
    dangerous, and should only be used after confirming that the owning process
    has leaked the lock, and only if there is a very good reason why the
    situation should not be resolved by terminating that process."""

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')
        parser.add_argument(
            '--offset', help='NLM byte-range lock offset', required=True, type=str_decode
        )
        parser.add_argument(
            '--size', help='NLM byte-range lock size', required=True, type=str_decode
        )
        parser.add_argument('--owner-id', help='Owner id', required=True, type=str_decode)
        parser.add_argument(
            '--force',
            help='This command can cause corruption, add this flag to release lock',
            action='store_true',
            required=False,
        )
        parser.add_argument('--snapshot', help='Snapshot ID of the specified file', type=str_decode)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        if not args.force and not qumulo.lib.opts.ask(
            ReleaseNLMLockCommand.NAME, LOCK_RELEASE_FORCE_MSG
        ):
            return  # Operation canceled.

        fs.release_nlm_lock(
            rest_client.conninfo,
            rest_client.credentials,
            args.offset,
            args.size,
            args.owner_id,
            args.path,
            args.id,
            args.snapshot,
        )

        file_path_or_id = ''
        if args.path is not None:
            file_path_or_id = f'file_path: {args.path}'
        if args.id is not None:
            file_path_or_id = f'file_id: {args.id}'

        snapshot = ''
        if args.snapshot is not None:
            snapshot = f', snapshot: {args.snapshot}'

        output = (
            'NLM byte-range lock with (offset: {}, size: {}, owner-id: {}, {}{}) was released.'
        ).format(args.offset, args.size, args.owner_id, file_path_or_id, snapshot)

        print(output)


class PunchHoleCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_punch_hole'
    SYNOPSIS = """Create a hole in a region of a file. Destroys all data
        within the hole."""

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')

        stream_group = parser.add_mutually_exclusive_group()
        stream_group.add_argument('--stream-id', help='Stream ID', type=str_decode)
        stream_group.add_argument('--stream-name', help='Stream name', type=str_decode)

        parser.add_argument(
            '--offset',
            help='Offset in bytes specifying the start of the hole to create',
            required=True,
            type=int,
        )
        parser.add_argument(
            '--size', help='Size in bytes of the hole to create', required=True, type=int
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            fs.punch_hole(
                rest_client.conninfo,
                rest_client.credentials,
                args.offset,
                args.size,
                path=args.path,
                id_=args.id,
                stream_id=get_stream_id(rest_client.conninfo, rest_client.credentials, args),
            )
        )


#                  _       _          __           _
#   _____  ___ __ | | __ _(_)_ __    / _|_ __ ___ | |_
#  / _ \ \/ / '_ \| |/ _` | | '_ \  | |_| '_ ` _ \| __|
# |  __/>  <| |_) | | (_| | | | | | |  _| | | | | | |_
#  \___/_/\_\ .__/|_|\__,_|_|_| |_| |_| |_| |_| |_|\__|
#           |_|
#  FIGLET: explain fmt
#

SINGLE_LEVEL_INDENT = ' ' * 4


class ExplainAceFormatter:
    """
    Common translator for explanation ACEs in permissions explainers
    """

    def __init__(self, indent_lvl: int = 0) -> None:
        self.fs_ace_translator = FsAceTranslator()
        self.indent_lvl = indent_lvl

    def indent(self, s: str) -> str:
        return SINGLE_LEVEL_INDENT * self.indent_lvl + s

    def pretty_fs_ace(self, fs_ace: Mapping[str, Any]) -> str:
        ace_type = self.fs_ace_translator.pretty_type(fs_ace)
        trustee = self.fs_ace_translator.pretty_trustee(fs_ace)
        rights = self.fs_ace_translator.pretty_rights(fs_ace)
        flags = self.fs_ace_translator.pretty_flags(fs_ace)

        return self.indent(
            '{type}\t{trustee}\t{rights}{flags}'.format(
                type=ace_type,
                trustee=trustee,
                rights=rights if rights else 'None',
                flags=f'\t({flags})' if flags else '',
            )
        )


PRETTY_HEADER_PADDING = '===='


def pretty_explain_header(
    conninfo: request.Connection,
    credentials: Optional[Credentials],
    body: Mapping[str, Any],
    acl: MutableMapping[str, Any],
) -> str:
    settings, _etag = fs.get_permissions_settings(conninfo, credentials)
    pretty_mode = settings['mode'].replace('_', ' ').capitalize()

    header = (
        f'Permissions Mode: {pretty_mode}\n'
        + 'Owner: {}\n'.format(str(Identity(body['owner'])))
        + 'Group: {}\n'.format(str(Identity(body['group_owner'])))
        + '\n'
        + '{h} Current ACL {h}\n'.format(h=PRETTY_HEADER_PADDING)
        + f'{pretty_acl(acl)}\n'
        + '\n'
    )
    return header


class ExplainAceFormatterProtocol(Protocol):
    def pretty_explanation_ace(self, ace: Mapping[str, Any]) -> Optional[str]:
        ...


def pretty_explain_acl(
    aces: Iterable[Mapping[str, Any]], formatter: ExplainAceFormatterProtocol
) -> str:
    """
    From @p aces, as returned by an explain API response, produce the prettified
    output for the explain ACL, providing a position to note in each ACE's
    header. e.g.,
        ==== 1 ====
        <Prettified ACE 1>

        ==== 2 ====
        <Prettified ACE 2>
        ...
        ==== N ====
        <Prettified ACE N>
    """
    lines = []
    for idx, ace in enumerate(aces):
        lines.append(
            '{h} {p} {h}\n'.format(h=PRETTY_HEADER_PADDING, p=idx + 1)
            + str(formatter.pretty_explanation_ace(ace))
        )

    return '\n\n'.join(lines)


#                  _       _                             _
#   _____  ___ __ | | __ _(_)_ __    _ __ ___   ___   __| | ___
#  / _ \ \/ / '_ \| |/ _` | | '_ \  | '_ ` _ \ / _ \ / _` |/ _ \
# |  __/>  <| |_) | | (_| | | | | | | | | | | | (_) | (_| |  __/
#  \___/_/\_\ .__/|_|\__,_|_|_| |_| |_| |_| |_|\___/ \__,_|\___|
#           |_|
#  FIGLET: explain mode
#

MODE_CLASSES = ('OWNER', 'GROUP', 'OTHER')


def select_classes_by_match_type(matches: Mapping[str, str], _type: str) -> List[str]:
    'Returns only the mode classes in @p matches that map to @p type'
    return [mc.upper() for mc in matches.keys() if matches[mc] == _type]


POSIX_SPECIAL_PERMISSIONS = frozenset(['STICKY_BIT', 'SET_GID', 'SET_UID'])


def pretty_mode_bits(bits_str: str) -> List[str]:
    """
    From a single digit representation of the bits, @p bits_str (e.g. '4'),
    produce the char array of its prettier form.
    Example:
        pretty_mode_bits(5) = ['r', '-', 'x']
    """
    pretty_bits = ['-', '-', '-']
    bit_strs = 'xwr'
    for x in range(3):
        if (1 << x) & int(bits_str) != 0:
            pretty_bits[2 - x] = bit_strs[x]

    return pretty_bits


def pretty_posix_mode(
    mode_octal: str, posix_special: Iterable[str], file_type: str = 'FS_FILE_TYPE_FILE'
) -> str:
    """
    @param mode_octal       Non-special POSIX mode to prettify
    @param posix_special    POSIX special permissions bitfield vals
    @param file_type        File-type enum value
    @return                 Full posix mode in pretty form, e.g. 'drwSr--r-t'
    """
    assert all(p in POSIX_SPECIAL_PERMISSIONS for p in posix_special)

    u = mode_octal[-3]
    g = mode_octal[-2]
    o = mode_octal[-1]

    segments = [
        ['d' if file_type == 'FS_FILE_TYPE_DIRECTORY' else '-'],
        pretty_mode_bits(u),
        pretty_mode_bits(g),
        pretty_mode_bits(o),
    ]

    # Incorporate posix_special into the pretty mode segments
    if 'STICKY_BIT' in posix_special:
        segments[-1][2] = 'T' if segments[-1][2] != 'x' else 't'
    if 'SET_GID' in posix_special:
        segments[-2][2] = 'S' if segments[-2][2] != 'x' else 's'
    if 'SET_UID' in posix_special:
        segments[-3][2] = 'S' if segments[-3][2] != 'x' else 's'

    return ''.join(''.join(s) for s in segments)


class ExplainPosixModeAceFormatter(ExplainAceFormatter):
    """
    Translator for the explanation ACEs in fs_acl_explain_posix_mode
    """

    def pretty_matches(self, ace: Mapping[str, Any]) -> Optional[str]:
        """
        Gathers the mode segment match information for each mode class in the
        provided @p ace, and prints a summary of which segments were matched and
        why. This will return None if the ace is inherit-only, or if there is
        an unexpected set of matches, which should be impossible in the API
        contract.
        """
        if ace['is_inherit_only']:
            return None

        matches = collections.OrderedDict(
            (mc, ace[mc.lower() + '_rights']['match']) for mc in MODE_CLASSES
        )
        match_lines = []

        if all(m == 'NONE' for m in matches.values()):
            match_lines = ['Matched: NONE']

        if all(m == 'EVERYONE' for m in matches.values()):
            match_lines = ['Matched: EVERYONE']

        equivalents = select_classes_by_match_type(matches, 'EQUIVALENT')
        potentially_affected = select_classes_by_match_type(matches, 'POTENTIALLY_AFFECTED')

        if equivalents:
            match_lines.append('Matched: ' + ','.join(equivalents))
        if potentially_affected:
            match_lines.append('Potentially affects rights for: ' + ','.join(potentially_affected))

        match_lines = [self.indent(m) for m in match_lines]
        return '\n'.join(match_lines) if match_lines else None

    def pretty_cumulative_rights(self, ace: Mapping[str, Any]) -> Optional[str]:
        """
        If @p ace is explaining an ALLOW ACE, reports the cumulative allowed
        rights for each mode segment, otherwise denied. This will return None
        if the ace is inherit-only.
        """
        if ace['is_inherit_only']:
            return None

        assert ace['ace']['type'].upper() in (ALLOWED_TYPE, DENIED_TYPE)
        allowed = ace['ace']['type'].upper() == ALLOWED_TYPE

        cumulative_rights_lines = []
        if allowed:
            cumulative_rights_lines.append(self.indent('Cumulative rights allowed:'))
        else:
            cumulative_rights_lines.append(self.indent('Cumulative rights denied:'))

        for mc in MODE_CLASSES:
            self.indent_lvl += 1
            rights = ace[mc.lower() + '_rights']
            cumulative = rights['cumulative_allowed'] if allowed else rights['cumulative_denied']

            rights_str = 'None'
            if cumulative != []:
                rights_str = self.fs_ace_translator.pretty_rights(ace={'rights': cumulative})

            cumulative_rights_lines.append(self.indent(mc.capitalize() + ': ' + rights_str))
            self.indent_lvl -= 1

        return '\n'.join(cumulative_rights_lines)

    def pretty_mode_bits_granted(self, ace: Mapping[str, Any]) -> Optional[str]:
        """
        Represent mode-bit contribution of @p ace in human-readable
        form. If the ace is inherit-only, or if the mode_bits_granted was some
        representation of zero (e.g. '0', '0000', '00000'), return None.
        Example output:
            Mode Bit Contribution: --x--x--x
        """
        if ace['is_inherit_only'] or all(b == '0' for b in ace['mode_bits_granted']):
            return None

        # N.B. First bit of the pretty mode is discarded here as ACEs don't
        # contribute to the first file-type bit
        return self.indent(
            'Mode Bit Contribution: {}'.format(
                pretty_posix_mode(ace['mode_bits_granted'], posix_special=[])[1:]
            )
        )

    def pretty_explanation_ace(self, ace: Mapping[str, Any]) -> str:
        """
        Produces the full explanation for the given ACE. The prettified FS ACE
        will always be printed, but the other explanation fields will be
        prettified and printed only if the ACE is not inherit-only.
        """
        lines = []
        lines.append(self.pretty_fs_ace(ace['ace']))
        self.indent_lvl += 1
        if ace['is_inherit_only']:
            lines.append(self.indent('Inherit-Only: No effect'))
            self.indent_lvl -= 1
            return '\n'.join(lines)

        matches = self.pretty_matches(ace)
        if matches:
            lines.append(matches)

        cumulative = self.pretty_cumulative_rights(ace)
        if cumulative:
            lines.append(cumulative)

        mode_contribution = self.pretty_mode_bits_granted(ace)
        if mode_contribution:
            lines.append(mode_contribution)

        self.indent_lvl -= 1
        return '\n'.join(lines)


def _print_explain_posix_mode_response(
    body: Mapping[str, Any], attrs: Mapping[str, Any], outfile: IO[str]
) -> None:
    outfile.write('Mode derivation from ACL for "{}":\n\n'.format(attrs['path']))
    outfile.write(
        '{}\n'.format(pretty_explain_acl(body['annotated_acl'], ExplainPosixModeAceFormatter()))
    )
    outfile.write('\n')
    outfile.write(
        'Final Derived Mode: {}\n'.format(
            pretty_posix_mode(
                body['mode'], body['posix_special_permissions'], file_type=attrs['type']
            )
        )
    )


class AclExplainPosixModeCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_acl_explain_posix_mode'
    SYNOPSIS = "Explain the derivation of POSIX mode from a file's ACL"

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File or directory')

        parser.add_argument(
            '--json', action='store_true', help='Print JSON representation of POSIX mode derivation'
        )

    @staticmethod
    def main(
        rest_client: RestClient, args: argparse.Namespace, outfile: IO[str] = sys.stdout
    ) -> None:
        response = fs.acl_explain_posix_mode(
            rest_client.conninfo, rest_client.credentials, path=args.path, id_=args.id
        )
        if args.json:
            print(response)
            return

        attrs, _etag = fs.get_file_attr(
            rest_client.conninfo, rest_client.credentials, path=args.path, id_=args.id
        )
        acl, _etag = fs.get_acl_v2(
            rest_client.conninfo, rest_client.credentials, path=args.path, id_=args.id
        )

        outfile.write(
            pretty_explain_header(rest_client.conninfo, rest_client.credentials, response.data, acl)
        )
        _print_explain_posix_mode_response(response.data, attrs, outfile)


#                  _       _              _                         _
#   _____  ___ __ | | __ _(_)_ __     ___| |__  _ __ ___   ___   __| |
#  / _ \ \/ / '_ \| |/ _` | | '_ \   / __| '_ \| '_ ` _ \ / _ \ / _` |
# |  __/>  <| |_) | | (_| | | | | | | (__| | | | | | | | | (_) | (_| |
#  \___/_/\_\ .__/|_|\__,_|_|_| |_|  \___|_| |_|_| |_| |_|\___/ \__,_|
#           |_|
#  FIGLET: explain chmod
#

CHMOD_ACTIONS = ('COPY_ACE', 'MODIFY_ACE', 'INSERT_ACE', 'REMOVE_ACE')
# The possible longest string in the left column of an explanation entry, for
# alignment purposes
MAX_COLUMN = 'Rights removed'


class ExplainSetModeAceFormatter(ExplainAceFormatter):
    """
    Translator for the explanation entries in fs_acl_explain_chmod. Note that
    each entry is not an ACE per se, but corresponds to an action taken on an
    ACE, old or new, to achieve the resulting ACL.
    """

    def pretty_action(self, entry: Mapping[str, Any]) -> Optional[str]:
        """
        Returns the string for the action performed on a given explanation entry
        """
        if entry['action'] not in CHMOD_ACTIONS:
            return None
        if entry['action'] == 'COPY_ACE':
            return 'Use original entry'

        action = entry['action'].split('_')[0].title()
        return action + ' entry'

    def pretty_explanation_row(self, field_name: str, value: str) -> str:
        return '{field}:{pad}\t{value}'.format(
            field=field_name, pad=' ' * (len(MAX_COLUMN) - len(field_name)), value=value
        )

    def pretty_trustee_match(self, entry: Mapping[str, Any]) -> Optional[str]:
        match = entry['source_trustee_match']
        if 'NO_MATCH' in match:
            return None

        trustee = self.fs_ace_translator.pretty_trustee(entry.get('source_ace'))
        pretty_mapping = {
            'NON_POSIX': 'non-POSIX trustee',
            'POSIX_OWNER': 'POSIX owner',
            'POSIX_GROUP_OWNER': 'POSIX group owner',
            'POSIX_OTHERS': 'POSIX others',
        }
        matches = [pretty_mapping[m] for m in match]

        return "'{trustee}' matches {matches}".format(trustee=trustee, matches=', '.join(matches))

    def pretty_explanation_ace(self, entry: Mapping[str, Any]) -> Optional[str]:
        """
        Produces the prettified explanation entry. Only print the fields that
        are relevant to the action.
        """
        lines = []
        lines.append(self.pretty_explanation_row('Action', str(self.pretty_action(entry))))
        if entry['source_ace'] is not None:
            lines.append(
                self.pretty_explanation_row('Source entry', self.pretty_fs_ace(entry['source_ace']))
            )
        if len(entry['source_trustee_match']) > 0:
            lines.append(
                self.pretty_explanation_row('Trustee match', str(self.pretty_trustee_match(entry)))
            )
        if len(entry['rights_removed']) > 0:
            lines.append(
                self.pretty_explanation_row(
                    'Rights removed', get_pretty_rights_string(set(entry['rights_removed']))
                )
            )
        if len(entry['flags_removed']) > 0:
            lines.append(
                self.pretty_explanation_row(
                    'Flags removed', get_pretty_flags(entry['flags_removed'])
                )
            )
        if len(entry['flags_added']) > 0:
            lines.append(
                self.pretty_explanation_row('Flags added', get_pretty_flags(entry['flags_added']))
            )
        if entry['result_ace']:
            lines.append(
                self.pretty_explanation_row('New entry', self.pretty_fs_ace(entry['result_ace']))
            )
        lines.append(self.pretty_explanation_row('Reason', entry['reason']))
        return '\n'.join(lines)


def summarize_class_rights(body: Mapping[str, Any], mode_segment: str) -> str:
    rights = set(body[f'{mode_segment}_rights_from_mode'])
    rights_str = 'None' if not rights else get_pretty_rights_string(rights)
    return SINGLE_LEVEL_INDENT + '{segment}: {rights}\n'.format(
        segment=mode_segment, rights=rights_str
    )


def _print_verbose_explain_chmod_info(body: Mapping[str, Any], outfile: IO[str]) -> None:
    outfile.write(
        'Rights POSIX trustees always keep (never produced by mode): {}\n'.format(
            get_pretty_rights_string(set(body['not_produced_by_any_mode']))
        )
    )
    outfile.write(
        'Rights non-POSIX trustees always keep (never displayed in mode): {}\n'.format(
            get_pretty_rights_string(set(body['not_visible_in_mode']))
        )
    )
    outfile.write('Maximum rights on non-POSIX ACEs (trustee not POSIX owner/group/everyone):\n')
    outfile.write(
        SINGLE_LEVEL_INDENT
        + 'Allow ACE: {}\n'.format(get_pretty_rights_string(set(body['max_extra_ace_allow'])))
    )
    outfile.write(
        SINGLE_LEVEL_INDENT
        + 'Deny ACE: {}\n'.format(get_pretty_rights_string(set(body['max_extra_ace_deny'])))
    )
    outfile.write('\n')


def _print_explain_chmod_response(
    body: Mapping[str, Any], mode: str, verbose: bool, outfile: IO[str]
) -> None:
    outfile.write(f'Mode {mode} translates to rights:\n')
    outfile.write(summarize_class_rights(body, 'owner'))
    outfile.write(summarize_class_rights(body, 'group'))
    outfile.write(summarize_class_rights(body, 'other'))
    outfile.write('\n')
    if verbose:
        _print_verbose_explain_chmod_info(body, outfile)
    outfile.write(f'Steps for applying mode {mode} to original permissions:\n')
    outfile.write(
        '{}\n'.format(pretty_explain_acl(body['annotated_aces'], ExplainSetModeAceFormatter()))
    )
    outfile.write('\n')
    outfile.write('{h} Resulting ACL {h}\n'.format(h=PRETTY_HEADER_PADDING))
    outfile.write(pretty_acl(body['result_acl']))
    outfile.write('\n\n')


def posix_mode(mode: str) -> str:
    """
    Custom argparse type for POSIX mode. Accepts the following formats:
        0744
        rwxr--r--
    """
    mode_regex = re.compile(r'([r-][w-][x-]){3,3}')
    mode_map = {'r': 4, 'w': 2, 'x': 1, '-': 0}
    if mode_regex.match(mode):
        mode_out = '0'
        for bit in textwrap.wrap(mode, 3):
            bit_value = sum(mode_map[v] for v in bit)
            mode_out += str(bit_value)
        return mode_out

    mode_out = f'0{int(mode, base=8):o}'
    # If needed, prepend zeros for a friendlier mode display
    if len(mode_out) < 4:
        mode_out = '0' * (4 - len(mode_out)) + mode_out

    return mode_out


class AclExplainSetModeCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_acl_explain_chmod'
    SYNOPSIS = "Explain how setting a POSIX mode would affect a file's ACL"

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File or directory')

        parser.add_argument(
            '--mode',
            required=True,
            type=posix_mode,
            help='POSIX mode to hypothetically apply (e.g., 0744, rwxr--r--)',
        )
        parser.add_argument(
            '-v', '--verbose', action='store_true', help='Print more information in output'
        )
        parser.add_argument(
            '--json', action='store_true', help='Print JSON representation of POSIX mode derivation'
        )

    @staticmethod
    def main(
        rest_client: RestClient, args: argparse.Namespace, outfile: IO[str] = sys.stdout
    ) -> None:
        response = fs.acl_explain_chmod(
            rest_client.conninfo,
            rest_client.credentials,
            path=args.path,
            id_=args.id,
            mode=args.mode,
        )
        if args.json:
            print(response)
            return

        outfile.write(
            pretty_explain_header(
                rest_client.conninfo,
                rest_client.credentials,
                response.data,
                response.data['initial_acl'],
            )
        )
        _print_explain_chmod_response(response.data, args.mode, args.verbose, outfile)


#                  _       _              _       _     _
#   _____  ___ __ | | __ _(_)_ __    _ __(_) __ _| |__ | |_ ___
#  / _ \ \/ / '_ \| |/ _` | | '_ \  | '__| |/ _` | '_ \| __/ __|
# |  __/>  <| |_) | | (_| | | | | | | |  | | (_| | | | | |_\__ \
#  \___/_/\_\ .__/|_|\__,_|_|_| |_| |_|  |_|\__, |_| |_|\__|___/
#           |_|                             |___/
#  FIGLET: explain rights
#


def _print_explain_rights_ace(ace: Mapping[str, Any], aligner: util.TextAligner) -> None:
    ace_translator = FsAceTranslator()
    ace_detail_fmt = '{ace_key} {ace_value}'
    # Print "type 'trustee' rights, (flags)" without padding:
    aligner.add_line(
        "{ace_key} {0} '{1}' {2} {3}",
        ace_translator.pretty_type(ace['ace']),
        ace_translator.pretty_trustee(ace['ace']),
        ace_translator.pretty_rights(ace['ace']),
        '' if not ace['ace']['flags'] else '({})'.format(ace_translator.pretty_flags(ace['ace'])),
        ace_key='Entry:',
    )
    aligner.add_line(ace_detail_fmt, ace_key='Trustee Matches:', ace_value=ace['trustee_matches'])
    if not ace['trustee_matches']:
        return
    if ace['skipped_inherit_only']:
        aligner.add_line(
            ace_detail_fmt, ace_key='Inherit-only:', ace_value='True; ACE has no effect'
        )
        return
    if ace['ace']['type'] == ALLOWED_TYPE:
        aligner.add_line(
            ace_detail_fmt,
            ace_key='Allowed so far:',
            ace_value=get_pretty_rights_string(set(ace['cumulative_allowed'])),
        )
    else:
        aligner.add_line(
            ace_detail_fmt,
            ace_key='Denied so far:',
            ace_value=get_pretty_rights_string(set(ace['cumulative_denied'])),
        )


def _add_implicit_rights_line(
    aligner: util.TextAligner,
    type_: str,
    rights: Optional[Iterable[str]],
    no_rights_override: Optional[str] = None,
) -> None:
    if rights:
        rights_str = get_pretty_rights_string(set(rights))
    elif no_rights_override:
        rights_str = no_rights_override
    else:
        rights_str = f'Not {type_}'
    aligner.add_line(
        '{implicit_type} {implicit_rights}',
        implicit_type=f'{type_} rights:',
        implicit_rights=rights_str,
    )


def _print_implicit_rights(body: Mapping[str, Any], aligner: util.TextAligner) -> None:
    _add_implicit_rights_line(aligner, 'Administrator', body.get('admin_priv_rights'))
    _add_implicit_rights_line(
        aligner,
        'File Owner',
        body.get('implicit_owner_rights'),
        None
        if not body.get('implicit_owner_rights_suppressed_by_ace')
        else 'Overridden by explicit Owner Rights ACE',
    )
    _add_implicit_rights_line(
        aligner, 'Parent Directory', body.get('implicit_rights_from_parent'), 'None'
    )


RIGHT_EXPLANATIONS = {
    'READ': 'Read file data or list directory',
    'READ_EA': 'Read extended attributes',
    'READ_ATTR': 'Read attributes',
    'READ_ACL': 'Read access control list',
    'WRITE_EA': 'Write extended attributes',
    'WRITE_ATTR': 'Write attributes',
    'WRITE_ACL': 'Write access control list',
    'CHANGE_OWNER': 'Change file owner',
    'WRITE_GROUP': 'Change file group-owner',
    'DELETE': 'Delete this object',
    'EXECUTE': 'Execute file or traverse directory',
    'MODIFY': 'Modify file data',
    'EXTEND': 'Append to file',
    'ADD_FILE': 'Add file to directory',
    'ADD_SUBDIR': 'Add directory to directory',
    'DELETE_CHILD': "Delete any of a directory's immediate children",
    'SYNCHRONIZE': 'Meaningless, exists for compatibility',
}


def _print_explain_rights_response(body: Mapping[str, Any], outfile: IO[str]) -> None:
    outfile.write(
        'File Owner: {}\nFile Group Owner: {}\n\n'.format(
            str(Identity(body['owner'])), str(Identity(body['group_owner']))
        )
    )

    user_str = str(Identity(body['requestor']['user']))

    aligner = util.TextAligner()
    aligner.add_line(f"ACL evaluation steps for '{user_str}':")
    for idx, ace in enumerate(body['annotated_aces'], 1):
        aligner.add_line('{0} {idx} {0}', PRETTY_HEADER_PADDING, idx=idx)
        with aligner.indented():
            _print_explain_rights_ace(ace, aligner)

    aligner.add_line('')
    aligner.add_line(f"Implicit Rights for '{user_str}':")
    with aligner.indented():
        _print_implicit_rights(body, aligner)

    aligner.add_line('')
    aligner.add_line(f"Rights that would be granted to '{user_str}':")
    with aligner.indented():
        for right in body['effective_rights']:
            verbose = RIGHT_EXPLANATIONS.get(right, 'Unknown')
            aligner.add_line(
                '{granted_right} {verbose_right}',
                granted_right=API_RIGHTS_TO_CLI.get(right, right),
                verbose_right=f'({verbose})',
            )

    aligner.write(outfile)


def _expand_for_explain(
    rest_client: RestClient, args: argparse.Namespace, outfile: IO[str]
) -> Tuple[List[Identity], List[Identity]]:
    res, _etag = auth.expand_identity(
        rest_client.conninfo,
        rest_client.credentials,
        Identity(args.users[0]),
        list(map(Identity, args.users[1:])),
        list(map(Identity, args.groups)),
    )
    if res['type'] == auth.ID_TYPE_GROUP:
        raise ValueError('User ID is actually a group: {}'.format(Identity(res['id'])))
    if res['id']['domain'] == AD_DOMAIN:
        ad_conf = rest_client.ad.poll_ad()
        if not ad_conf['use_ad_posix_attributes']:
            outfile.write(
                "Warning: Asked to explain an AD user's rights, but "
                "AD Posix Attributes are not enabled.  The user's "
                'group membership cannot be found automatically, and '
                'must be specified manually.\n'
            )
    user = Identity(res['id'])
    equiv = list(map(Identity, res['equivalent_ids']))
    groups = list(map(Identity, res['group_ids']))

    if not groups:
        raise ValueError('No groups given or found. At least one group is required.')

    if args.verbose:
        outfile.write(format_expanded_id(res) + '\n\n')
    else:
        outfile.write(
            '{} has {} equivalent IDs and is a member of {} groups.\n'.format(
                str(user), len(equiv), len(groups)
            )
        )

    return [user] + equiv, groups


class AclExplainRightsCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_acl_explain_rights'
    SYNOPSIS = 'Explain how rights are granted to a user for a file.'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File or directory')

        parser.add_argument(
            '-u',
            '--user',
            nargs='+',
            metavar='ID',
            type=str_decode,
            dest='users',
            required=True,
            help=(
                'User for whom to explain rights. e.g. Alice, uid:1000, '
                'sid:S-1-5-2-3-4, or auth_id:500.  If multiple are given, '
                'they will be considered equivalent for the purpose of the '
                'explanation.'
            ),
        )
        parser.add_argument(
            '-g',
            '--groups',
            nargs='*',
            metavar='ID',
            type=str_decode,
            default=[],
            help=(
                'Groups that the user should be considered a member of for '
                'the purpose of the explanation.'
            ),
        )
        parser.add_argument(
            '--no-expand',
            dest='expand',
            action='store_false',
            default=True,
            help=(
                "Don't expand the given user and group IDs. This can be "
                "useful if you want to test a hypothetical (e.g 'what happens "
                "if I add/remove a user to some group?')"
            ),
        )
        parser.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            help=(
                'Prints the credential that will be used for the explanation, '
                'after it has been expanded.'
            ),
        )
        parser.add_argument(
            '--json', action='store_true', help='Print JSON representation of rights explanation.'
        )

    @staticmethod
    def main(
        rest_client: RestClient, args: argparse.Namespace, outfile: IO[str] = sys.stdout
    ) -> None:
        if args.expand:
            users, groups = _expand_for_explain(rest_client, args, outfile)
        elif not args.groups:
            sys.stderr.write('At least one group must be given with --no-expand\n')
            sys.exit(2)
        else:
            users = list(map(Identity, args.users))
            groups = list(map(Identity, args.groups))

        response = fs.acl_explain_rights(
            rest_client.conninfo,
            rest_client.credentials,
            path=args.path,
            id_=args.id,
            user=users[0],
            # Note that it doesn't really matter which group is "primary",
            # except that one must be chosen for the purposes of constructing
            # a hypothetical cred to evaluate:
            group=groups[0],
            ids=users[1:] + groups[1:],
        )

        if args.json:
            print(response)
        else:
            _print_explain_rights_response(response.data, outfile)


#     _    ____  ____
#    / \  |  _ \/ ___|
#   / _ \ | | | \___ \
#  / ___ \| |_| |___) |
# /_/   \_\____/|____/
#  FIGLET: ADS
#


def translate_stream_args_to_id(
    conninfo: request.Connection,
    credentials: Optional[Credentials],
    stream_id: Optional[str],
    stream_name: Optional[str],
    path: Optional[str],
    id_: Optional[str],
) -> str:
    sid = stream_id

    # If a stream-name is passed in, list all named streams to find
    # corresponding stream id.
    if sid is None:
        streams, _ = fs.list_named_streams(conninfo, credentials, path=path, id_=id_)
        for stream in streams:
            if stream['name'] == stream_name:
                sid = stream['id']
                break

    # Error out if stream does not exist.
    if sid is None:
        raise request.RequestError(
            404,
            'Not Found',
            {'error_class': 'fs_no_such_entry_error', 'description': 'Stream name not found'},
        )

    return sid


class ListNamedStreams(qumulo.lib.opts.Subcommand):
    NAME = 'fs_list_named_streams'
    SYNOPSIS = 'List all named streams on file or directory'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File or directory')
        parser.add_argument('--snapshot', help='Snapshot ID to read from', type=int)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            fs.list_named_streams(
                rest_client.conninfo,
                rest_client.credentials,
                path=args.path,
                id_=args.id,
                snapshot=args.snapshot,
            )
        )


class RemoveStream(qumulo.lib.opts.Subcommand):
    NAME = 'fs_remove_stream'
    SYNOPSIS = 'Remove a stream from file or directory'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File or directory')

        stream_group = parser.add_mutually_exclusive_group(required=True)
        stream_group.add_argument('--stream-id', help='Stream id to remove', type=str_decode)
        stream_group.add_argument('--stream-name', help='Stream name to remove', type=str_decode)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        sid = translate_stream_args_to_id(
            rest_client.conninfo,
            rest_client.credentials,
            args.stream_id,
            args.stream_name,
            args.path,
            args.id,
        )
        fs.remove_stream(
            rest_client.conninfo,
            rest_client.credentials,
            stream_id=sid,
            path=args.path,
            id_=args.id,
        )

        info = args.stream_name if args.stream_id is None else args.stream_id
        print(f'Successfully removed stream {info}')


#   ____ _                              _   _       _   _  __
#  / ___| |__   __ _ _ __   __ _  ___  | \ | | ___ | |_(_)/ _|_   _
# | |   | '_ \ / _` | '_ \ / _` |/ _ \ |  \| |/ _ \| __| | |_| | | |
# | |___| | | | (_| | | | | (_| |  __/ | |\  | (_) | |_| |  _| |_| |
#  \____|_| |_|\__,_|_| |_|\__, |\___| |_| \_|\___/ \__|_|_|  \__, |
#                          |___/                              |___/
#  FIGLET: Change Notify
#


# The key names here are sent over the API and parsed by qfsd. When changing one side of the API
# a corresponding change must be made on the other side. see fs/api/notify.h
class FSNotifyFilters(enum.Enum):
    # Child path event types
    child_file_added = enum.auto()
    child_dir_added = enum.auto()
    child_file_removed = enum.auto()
    child_dir_removed = enum.auto()
    child_file_moved_from = enum.auto()
    child_file_moved_to = enum.auto()
    child_dir_moved_from = enum.auto()
    child_dir_moved_to = enum.auto()

    # Child attribute event types
    child_btime_changed = enum.auto()
    child_mtime_changed = enum.auto()
    child_atime_changed = enum.auto()
    child_size_changed = enum.auto()
    child_extra_attrs_changed = enum.auto()
    child_acl_changed = enum.auto()
    child_owner_changed = enum.auto()
    child_group_changed = enum.auto()
    child_data_written = enum.auto()

    # Child stream event types.
    child_stream_added = enum.auto()
    child_stream_removed = enum.auto()
    child_stream_moved_from = enum.auto()
    child_stream_moved_to = enum.auto()
    child_stream_size_changed = enum.auto()
    child_stream_data_written = enum.auto()

    # Self event types
    self_removed = enum.auto()


class ChangeNotifyCanceler:
    """
    Input raises an EOFError on ctrl-d while sys.stdin treats that as 'end of read'
    Input doesn't have a concept of fileno, but it is the same as the stdin fileno
    """

    def fileno(self) -> int:
        return sys.stdin.fileno()

    def read(self) -> str:
        return input()


class ChangeNotifyCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_notify'
    SYNOPSIS = (
        'Notify on changes to files and directories under the specified directory. '
        'To cancel the listener, send a SIGQUIT signal (press CTRL+D).'
    )

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'Directory')

        parser.add_argument(
            '--recursive', action='store_true', help='Listen for changes recursively.'
        )
        parser.add_argument(
            '--filter',
            nargs='+',
            help='Specific notify types to filter to.',
            choices=FSNotifyFilters.__members__.keys(),
        )
        parser.add_argument(
            '--file', help='File to receive data', type=argparse.FileType('w'), default=sys.stdout
        )
        parser.add_argument('--json', action='store_true', help='Output results as a json stream.')

    @staticmethod
    def write_json(data: fs.ChangesIterator, args: Namespace) -> None:
        started = False
        args.file.write('[\n')
        for change in data:
            if started:
                args.file.write(',\n')
            args.file.write('\n'.join(pretty_json([change]).split('\n')[1:-1]))
            args.file.flush()
            started = True
        args.file.write('\n]\n')

    @staticmethod
    def write_table(data: fs.ChangesIterator, args: Namespace) -> None:
        spacing = {'Type': 23, 'Path': 29, 'Stream Name': 0}
        header = ' '.join(
            [
                f'{"Type" : <{spacing["Type"]}}',
                f'{"Path" : <{spacing["Path"]}}',
                f'{"Stream Name" : <{spacing["Stream Name"]}}\n',
            ]
        )
        args.file.write(header)
        args.file.write('=' * 64 + '\n')

        def write_result(row: object) -> None:
            if isinstance(row, dict):
                type_ = str(row.get('type', None))
                path = str(row.get('path', None))
                stream_name = str(row.get('stream_name', None))

                row_str = ' '.join(
                    [
                        f'{type_ : <{spacing["Type"]}}',
                        f'{path : <{spacing["Path"]}}',
                        f'{stream_name : <{spacing["Stream Name"]}}\n',
                    ]
                )
                args.file.write(row_str)
            elif isinstance(row, Iterable):
                for item in row:
                    write_result(item)
            args.file.flush()

        for change in data:
            write_result(change)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        resp = fs.get_change_notify_listener(
            rest_client.conninfo,
            rest_client.credentials,
            recursive=args.recursive,
            type_filter=args.filter,
            id_=args.id,
            path=args.path,
            canceler=ChangeNotifyCanceler(),
        )

        if args.json:
            ChangeNotifyCommand.write_json(resp.data, args)
        else:
            ChangeNotifyCommand.write_table(resp.data, args)


#  ____            _                               _     _
# / ___| _   _ ___| |_ ___ _ __ ___      __      _(_) __| | ___
# \___ \| | | / __| __/ _ \ '_ ` _ \ ____\ \ /\ / / |/ _` |/ _ \
#  ___) | |_| \__ \ ||  __/ | | | | |_____\ V  V /| | (_| |  __/
# |____/ \__, |___/\__\___|_| |_| |_|      \_/\_/ |_|\__,_|\___|
#        |___/
#           _   _   _
#  ___  ___| |_| |_(_)_ __   __ _ ___
# / __|/ _ \ __| __| | '_ \ / _` / __|
# \__ \  __/ |_| |_| | | | | (_| \__ \
# |___/\___|\__|\__|_|_| |_|\__, |___/
#                           |___/
#  FIGLET: System-wide settings
#


class GetPermissionsSettingsCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_get_permissions_settings'
    SYNOPSIS = 'Get permissions settings'

    @staticmethod
    def main(rest_client: RestClient, _args: Namespace) -> None:
        print(fs.get_permissions_settings(rest_client.conninfo, rest_client.credentials))


VALID_PERMISSIONS_MODES = frozenset(['NATIVE', '_DEPRECATED_MERGED_V1', 'CROSS_PROTOCOL'])


def permissions_mode(arg: str) -> str:
    """
    XXX US20314: Allow, but suppress the help text for, _DEPRECATED_MERGED_V1
    until it has been fully deprecated and prepared for removal. At that point,
    this custom type should be removed and SetPermissionsSettingsCommand should
    utilize argparse choices for all valid modes.
    """
    mode = arg.upper()
    if mode in VALID_PERMISSIONS_MODES:
        return mode

    raise TypeError("Invalid argument '%s'" % arg)


class SetPermissionsSettingsCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_set_permissions_settings'
    SYNOPSIS = 'Set permissions settings'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument(
            'mode', help='Permissions mode to set (NATIVE or CROSS_PROTOCOL)', type=permissions_mode
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            fs.set_permissions_settings(
                rest_client.conninfo, rest_client.credentials, mode=args.mode
            )
        )


class GetAtimeSettingsCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_get_atime_settings'
    SYNOPSIS = 'Get access time (atime) settings.'

    @staticmethod
    def main(rest_client: RestClient, _args: Namespace) -> None:
        print(fs.get_atime_settings(rest_client.conninfo, rest_client.credentials))


class SetAtimeSettingsCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_set_atime_settings'
    SYNOPSIS = 'Set access time (atime) settings.'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        enabled_group = parser.add_mutually_exclusive_group(required=False)
        enabled_group.set_defaults(enabled=None)
        enabled_group.add_argument(
            '--enable',
            '-e',
            dest='enabled',
            action='store_true',
            help='Enable access time (atime) updates.',
        )
        enabled_group.add_argument(
            '--disable',
            '-d',
            dest='enabled',
            action='store_false',
            help='Disable access time (atime) updates.',
        )

        parser.add_argument(
            '--granularity',
            '-g',
            type=str_decode,
            default=None,
            choices=['HOUR', 'DAY', 'WEEK'],
            help='Specify granularity for access time (atime) updates.',
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        if args.enabled is None and args.granularity is None:
            raise ValueError('You must specify at least one option to change.')

        print(
            fs.set_atime_settings(
                rest_client.conninfo,
                rest_client.credentials,
                enabled=args.enabled,
                granularity=args.granularity,
            )
        )


class GetNotifySettingsCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_get_notify_settings'
    SYNOPSIS = 'Get FS notify settings.'

    @staticmethod
    def main(rest_client: RestClient, _args: Namespace) -> None:
        print(fs.get_notify_settings(rest_client.conninfo, rest_client.credentials))


class SetNotifySettingsCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_set_notify_settings'
    SYNOPSIS = 'Set FS notify settings'

    DESCRIPTION = SYNOPSIS + textwrap.dedent(
        """
        Change global FS settings for notify and change watch.

        Available modes:

        DISABLED_ERROR
            Recursive change-notify requests return errors immediately.

        DISABLED_IGNORE
            The system accepts recursive change-notify requests but sends notifications only for the
            top directory that it watches. In other words, the system behaves as if the user doesn't
            specify the recursive flag. You can use this setting to improve compatibility with
            applications that request recursive behavior but don't actually depend on it. Important:
            For scenarios that require recursive behavior, this setting can cause an application to
            become unresponsive or exhibit other unexpected behavior.

        ENABLED
            The ENABLED option is the default mode, unless you set a different one. This option
            provides full support for recursive change-notify requests. The system pushes
            notifications for all descendants of the watched directory to the watcher. Important:
            This configuration can affect system performance significantly. For example, watching
            the root of the file system creates a notification for every change on the entire
            cluster.
        """
    )

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument(
            '--recursive-mode',
            help='Notify recursive mode to set (ENABLED, DISABLED_ERROR, DISABLED_IGNORE)',
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            fs.set_notify_settings(
                rest_client.conninfo, rest_client.credentials, recursive_mode=args.recursive_mode
            )
        )


#  _    _               __  __      _            _       _
# | |  | |             |  \/  |    | |          | |     | |
# | |  | |___  ___ _ __| \  / | ___| |_ __ _  __| | __ _| |_ __ _
# | |  | / __|/ _ \ '__| |\/| |/ _ \ __/ _` |/ _` |/ _` | __/ _` |
# | |__| \__ \  __/ |  | |  | |  __/ || (_| | (_| | (_| | || (_| |
#  \____/|___/\___|_|  |_|  |_|\___|\__\__,_|\__,_|\__,_|\__\__,_|
#  FIGLET: User Metadata
#

S3_HELP_TEXT = """In Qumulo Core, there are two types of user metadata, generic and S3.
By default, qq CLI commands manipulate generic metadata.
When you use the --s3 flag, Qumulo Core makes user metadata visible to the S3 protocol as object metadata.
"""  # noqa: E501


class UserMetadataSet(qumulo.lib.opts.Subcommand):
    NAME = 'fs_set_user_metadata'
    SYNOPSIS = (
        'Set or update a user metadata value for a file by using the specified metadata key and'
        ' value'
    )

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')
        parser.add_argument('--s3', help=S3_HELP_TEXT, dest='s3', action='store_true')
        parser.add_argument('--key', help='Metadata key', type=str_decode, required=True)

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '--value', help='Plaintext metadata value', type=str_decode, dest='value'
        )
        group.add_argument(
            '--hex-value', help='Hex-encoded metadata value', type=str_decode, dest='hex_value'
        )
        group.add_argument(
            '--base64-value',
            help='Base64-encoded metadata value',
            type=str_decode,
            dest='base64_value',
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        type_ = fs.UserMetadataType.GENERIC
        if args.s3:
            type_ = fs.UserMetadataType.S3

        if args.hex_value:
            value = binascii.unhexlify(args.hex_value)
        elif args.base64_value:
            value = base64.b64decode(args.base64_value)
        else:
            value = args.value.encode('utf-8')

        fs.set_user_metadata(
            rest_client.conninfo,
            rest_client.credentials,
            type_=type_,
            key=args.key,
            value=value,
            id_=args.id,
            path=args.path,
        )


class UserMetadataGet(qumulo.lib.opts.Subcommand):
    NAME = 'fs_get_user_metadata'
    SYNOPSIS = 'Retrieve a user metadata value for a file by using the specified metadata key'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')
        parser.add_argument('--s3', help=S3_HELP_TEXT, dest='s3', action='store_true')
        parser.add_argument('--key', help='Metadata key', type=str_decode, required=True)
        parser.add_argument('--snapshot', help='Snapshot ID to read user metadata from', type=int)

        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument(
            '--hex', help='Print binary values as hex', dest='hex', action='store_true'
        )
        group.add_argument(
            '--base64', help='Print binary values as base64', dest='base64', action='store_true'
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        type_ = fs.UserMetadataType.GENERIC
        if args.s3:
            type_ = fs.UserMetadataType.S3

        value = fs.get_user_metadata(
            rest_client.conninfo,
            rest_client.credentials,
            type_=type_,
            key=args.key,
            id_=args.id,
            path=args.path,
            snapshot=args.snapshot,
        )

        if args.hex:
            b = binascii.hexlify(value[0])
            print(b.decode('utf-8'))
        elif args.base64:
            b = base64.b64encode(value[0])
            print(b.decode('utf-8'))
        else:
            try:
                print(value[0].decode('utf-8'))
            except UnicodeDecodeError:
                print('Value is not valid UTF8')


class UserMetadataDelete(qumulo.lib.opts.Subcommand):
    NAME = 'fs_delete_user_metadata'
    SYNOPSIS = 'Delete the user metadata for a file by using the specified metadata key'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')
        parser.add_argument('--s3', help=S3_HELP_TEXT, dest='s3', action='store_true')
        parser.add_argument('--key', help='Metadata key', type=str_decode, required=True)

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        type_ = fs.UserMetadataType.GENERIC
        if args.s3:
            type_ = fs.UserMetadataType.S3

        fs.delete_user_metadata(
            rest_client.conninfo,
            rest_client.credentials,
            type_=type_,
            key=args.key,
            id_=args.id,
            path=args.path,
        )

        print('Metadata key deleted successfully.')


def make_metadata_table(
    metadata: Sequence[Dict[str, bytes]], display_headers: bool, args: argparse.Namespace
) -> str:
    TRIM = 50
    headers = ['key', 'value'] if display_headers else None
    rows = []
    for m in metadata:
        row = []
        key = str(m['key'])
        key = key[:TRIM] + '...' if len(key) > TRIM else key
        row.append(key)
        if args.hex:
            value = binascii.hexlify(m['value']).decode('utf-8')
        elif args.base64:
            value = base64.b64encode(m['value']).decode('utf-8')
        else:
            try:
                value = m['value'].decode('utf-8')
            except UnicodeDecodeError:
                value = '<Binary Value>'
        value = value[:TRIM] + '...' if len(value) > TRIM else value
        row.append(value)
        rows.append(row)
    return util.tabulate(rows, headers)


class UserMetadataList(qumulo.lib.opts.Subcommand):
    NAME = 'fs_list_user_metadata'
    SYNOPSIS = 'Retrieve user metadata of the specified type for a file'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')
        parser.add_argument('--s3', help=S3_HELP_TEXT, dest='s3', action='store_true')

        PRINT_JSON = """Output the response in json.
Without this option, keys and values will only show the first 50 characters."""
        parser.add_argument('--json', help=PRINT_JSON, dest='json', action='store_true')
        parser.add_argument('--snapshot', help='Snapshot ID to read user metadata from', type=int)

        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument(
            '--hex', help='Print binary values as hex', dest='hex', action='store_true'
        )
        group.add_argument(
            '--base64', help='Print binary values as base64', dest='base64', action='store_true'
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        type_ = fs.UserMetadataType.GENERIC
        if args.s3:
            type_ = fs.UserMetadataType.S3

        iterator = fs.list_user_metadata(
            rest_client.conninfo,
            rest_client.credentials,
            type_=type_,
            limit=100,
            id_=args.id,
            path=args.path,
            snapshot=args.snapshot,
        )

        if not args.json:
            print_header = True
            for _, result in enumerate(iterator):
                print(make_metadata_table(result.data['entries'], print_header, args))
                print_header = False
        else:
            vals = []
            for _, result in enumerate(iterator):
                entries = result.data['entries']
                for entry in entries:
                    key = entry['key']
                    if args.hex:
                        value = binascii.hexlify(entry['value']).decode('utf-8')
                    elif args.base64:
                        value = base64.b64encode(entry['value']).decode('utf-8')
                    else:
                        try:
                            value = entry['value'].decode('utf-8')
                        except UnicodeDecodeError:
                            value = '<Binary Value>'

                    vals.append({'key': key, 'value': value})

            print(json.dumps(vals, indent=4))


class ModifyFileLockCommand(qumulo.lib.opts.Subcommand):
    NAME = 'fs_file_modify_lock'
    SYNOPSIS = 'Modify a retention period or legal hold on a file.'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        add_ref_arguments(parser, 'File')

        legal_hold_group = parser.add_mutually_exclusive_group(required=False)
        legal_hold_group.add_argument(
            '--enable-legal-hold',
            dest='legal_hold',
            action='store_true',
            help='Set a legal hold on the file.',
            default=None,
        )
        legal_hold_group.add_argument(
            '--disable-legal-hold',
            dest='legal_hold',
            action='store_false',
            help='Unset a legal hold on the file.',
            default=None,
        )

        retention_group = parser.add_mutually_exclusive_group(required=False)
        retention_group.add_argument(
            '--retention-period', type=str_decode, help='Set the retention period for a file lock.'
        )
        retention_group.add_argument(
            '--retention-days',
            type=int,
            help='Set the retention period for a file lock to the specified number of days from '
            'now.',
        )
        retention_group.add_argument(
            '--retention-years',
            type=int,
            help='Set the retention period for a file lock to the specified number of years from '
            'now.',
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        def validate_retention_value(value: int) -> None:
            if value == 0:
                raise ValueError('Retention values need to be greater than 0')

        retention_period = None
        if args.retention_period is not None:
            retention_period = args.retention_period
        elif args.retention_days is not None:
            validate_retention_value(args.retention_days)
            retention_period = fmt_rfc3339_time(
                datetime.now(timezone.utc) + timedelta(days=args.retention_days)
            )
        elif args.retention_years is not None:
            validate_retention_value(args.retention_years)
            retention_period = fmt_rfc3339_time(
                datetime.now(timezone.utc) + timedelta(days=365 * args.retention_years)
            )

        attrs = fs.modify_file_lock(
            rest_client.conninfo,
            rest_client.credentials,
            retention_period=retention_period,
            legal_hold=args.legal_hold,
            id_=args.id,
            path=args.path,
        )
        print(pretty_json(attrs.data['lock']))
