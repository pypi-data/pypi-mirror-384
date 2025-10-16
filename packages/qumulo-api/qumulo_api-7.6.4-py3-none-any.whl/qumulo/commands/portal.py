# Copyright (c) 2024 Qumulo, Inc.
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
import sys

from argparse import SUPPRESS
from typing import Any, Dict, List, Optional

import qumulo.lib.opts

from qumulo.lib.request import pretty_json, RequestError
from qumulo.lib.util import tabulate
from qumulo.rest.portal import DEFAULT_PORTAL_PORT_NUMBER as PORTAL_PORT
from qumulo.rest.portal import (
    EvictionSettings,
    MultiRootHubPortal,
    MultiRootSpokePortal,
    PortalHost,
)
from qumulo.rest_client import RestClient

JSON_HELP = 'Pretty-print JSON'
ADDR_HELP = 'The IP address of a node in the remote cluster'
PORT_HELP = (
    'The TCP port for portal activity on the remote cluster. The default port 3713 is used if this '
    'field is not provided.'
)
HOSTS_HELP = (
    'The IP addresses and TCP ports of the remote cluster. Use a comma-delimited list to specify '
    'multiple hosts. Use colon as a separator after each IP address to provide custom TCP port '
    '(3713 is used by default).'
)

HUB_ROOT_HELP = (
    'The full path to the prospective directory that will serve as the hub portal root directory'
)
SPOKE_ROOT_HELP = (
    'The full path to the directory that serves as the spoke portal root directory. Qumulo Core'
    ' creates this directory for you automatically. If this directory exists already, the system'
    ' outputs an error.'
)
RO_SPOKE_HELP = (
    'Create a read-only spoke portal. Read-only spoke portals prevent users from creating or'
    ' modifying files or directories under the hub portal root directory.'
    " Important: It isn't possible to change a read-only spoke portal to a read-write portal"
    ' after creating it.'
)
FORCE_DELETE_DETAIL = (
    'Caution: This operation deletes all data from the spoke portal, including any new and'
    ' modified data on the spoke that has not yet synchronized with the hub portal. Data under'
    ' the hub portal root directory is not affected.'
)
NO_PATHS_HELP = 'Do not attempt to resolve file IDs present on the local cluster to paths.'


def pretty_portal_type(type_: str) -> str:
    return {'PORTAL_READ_ONLY': 'RO', 'PORTAL_READ_WRITE': 'RW'}.get(type_, type_)


def pretty_portal_hosts(hosts: List[PortalHost]) -> str:
    if len(hosts) == 0:
        return '-'
    return ', '.join(f'{host.address}:{host.port}' for host in hosts)


def pretty_root_state(authorized: bool) -> str:
    return 'Authorized' if authorized else 'Unauthorized'


def get_spoke_local_roots(spoke: MultiRootSpokePortal) -> List[str]:
    return [pair.local_root for pair in spoke.roots]


def get_hub_local_roots(hub: MultiRootHubPortal) -> List[str]:
    return hub.authorized_roots + hub.pending_roots


class ResolvedRoots:
    def __init__(self, label: str, roots: Dict[str, str]) -> None:
        self.label = label
        self.roots = roots


def resolve_local_roots(rest_client: RestClient, no_paths: bool, roots: List[str]) -> ResolvedRoots:
    if no_paths:
        resolved = {root: root for root in roots}
        return ResolvedRoots('Local ID', resolved)

    resolved = {result['id']: result['path'] for result in rest_client.fs.resolve_paths(roots)}
    return ResolvedRoots('Local Path', resolved)


def resolve_spoke_root_path_or_id(
    rest_client: RestClient, spoke_id: int, root_path: Optional[str], root_id: Optional[str]
) -> str:
    if root_path:
        root_path = root_path.rstrip('/')

        spoke = rest_client.portal.v2_get_spoke_portal(spoke_id)
        roots = get_spoke_local_roots(spoke)
        resolved = {
            result['path'].rstrip('/'): result['id']
            for result in rest_client.fs.resolve_paths(roots)
        }

        if root_path not in resolved:
            raise SystemExit(
                f'Could not match {root_path} to a spoke root for spoke portal {spoke_id}'
            )
        return resolved[root_path]

    assert root_id is not None
    return root_id


def resolve_hub_root_path_or_id(
    rest_client: RestClient, root_path: Optional[str], root_id: Optional[str]
) -> str:
    if root_path:
        return rest_client.fs.get_file_attr(path=root_path)['id']

    assert root_id is not None
    return root_id


def print_spoke_portal(json: bool, spoke: MultiRootSpokePortal, resolved: ResolvedRoots) -> None:
    if json:
        print(pretty_json(spoke.to_dict()))
    else:
        columns = ['Role', 'ID', 'Type', 'State', 'Status', 'Peer']
        row = [
            'Spoke',
            spoke.id,
            pretty_portal_type(spoke.type),
            spoke.state.title(),
            spoke.status.title(),
            pretty_portal_hosts(spoke.hub_hosts),
        ]
        print(tabulate([row], columns))

        columns = ['Root State', resolved.label, 'Remote ID']
        rows = [
            [pretty_root_state(pair.authorized), resolved.roots[pair.local_root], pair.remote_root]
            for pair in spoke.roots
        ]
        print()
        print(tabulate(rows, columns))


def print_hub_portal(json: bool, hub: MultiRootHubPortal, resolved: ResolvedRoots) -> None:
    if json:
        print(pretty_json(hub.to_dict()))
    else:
        columns = ['Role', 'ID', 'Type', 'State', 'Status', 'Peer']
        row = [
            'Hub',
            hub.id,
            pretty_portal_type(hub.type),
            hub.state.title(),
            hub.status.title(),
            pretty_portal_hosts(hub.spoke_hosts),
        ]
        print(tabulate([row], columns))

        columns = ['Root State', resolved.label]
        rows = []
        rows.extend(
            [[pretty_root_state(False), resolved.roots[root]] for root in hub.pending_roots]
        )
        rows.extend(
            [[pretty_root_state(True), resolved.roots[root]] for root in hub.authorized_roots]
        )
        print()
        print(tabulate(rows, columns))


def print_portals_list(
    json: bool, spokes: List[MultiRootSpokePortal], hubs: List[MultiRootHubPortal]
) -> None:
    if json:
        combined = {'spokes': [s.to_dict() for s in spokes], 'hubs': [h.to_dict() for h in hubs]}
        print(pretty_json(combined))
    else:
        columns = ['Role', 'ID', 'Type', 'State', 'Status', 'Peer', 'Root Count']
        rows: List[List[Any]] = []
        rows.extend(
            [
                'Spoke',
                spoke.id,
                pretty_portal_type(spoke.type),
                spoke.state.title(),
                spoke.status.title(),
                pretty_portal_hosts(spoke.hub_hosts),
                len(spoke.roots),
            ]
            for spoke in spokes
        )
        rows.extend(
            [
                'Hub',
                hub.id,
                pretty_portal_type(hub.type),
                hub.state.title(),
                hub.status.title(),
                pretty_portal_hosts(hub.spoke_hosts),
                len(hub.authorized_roots) + len(hub.pending_roots),
            ]
            for hub in hubs
        )
        print(tabulate(rows, columns))


#           _       _   _                 _     _
#  _ __ ___| | __ _| |_(_) ___  _ __  ___| |__ (_)_ __
# | '__/ _ \ |/ _` | __| |/ _ \| '_ \/ __| '_ \| | '_ \
# | | |  __/ | (_| | |_| | (_) | | | \__ \ | | | | |_) |
# |_|  \___|_|\__,_|\__|_|\___/|_| |_|___/_| |_|_| .__/
#                                                |_|
#  FIGLET: relationship
#


def parse_hub_hosts(args: argparse.Namespace) -> List[PortalHost]:
    hosts = []
    if args.hub_hosts:
        host_strs = [host.strip() for host in args.hub_hosts.split(',') if host]
        for host_str in host_strs:
            host_addr = host_str.split(':')[0]
            host_port = int(host_str.split(':')[1]) if (':' in host_str) else args.hub_port
            hosts.append(PortalHost.from_dict({'address': host_addr, 'port': host_port}))
    else:
        hosts.append(PortalHost.from_dict({'address': args.hub_address, 'port': args.hub_port}))
    return hosts


class CreatePortal(qumulo.lib.opts.Subcommand):
    NAME = 'portal_create'
    SYNOPSIS = (
        'Create a spoke portal on the current cluster and propose a hub portal on another cluster'
    )

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--spoke-root', help=SPOKE_ROOT_HELP)
        parser.add_argument('--hub-root', help=HUB_ROOT_HELP)
        parser.add_argument('-j', '--json', help=JSON_HELP, action='store_true')
        parser.add_argument('-r', '--read-only-spoke', help=RO_SPOKE_HELP, action='store_true')
        parser.add_argument('-n', '--no-paths', help=NO_PATHS_HELP, action='store_true')

        host_group = parser.add_mutually_exclusive_group(required=True)
        host_group.add_argument('-m', '--hub-hosts', help=HOSTS_HELP, type=str)
        host_group.add_argument('-a', '--hub-address', help=ADDR_HELP)
        parser.add_argument('-p', '--hub-port', default=PORTAL_PORT, help=PORT_HELP, type=int)

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        if bool(args.spoke_root) != bool(args.hub_root):
            print(
                '--spoke-root and --hub-root must be provided together or not at all',
                file=sys.stderr,
            )
            sys.exit(1)

        portal_type = 'PORTAL_READ_ONLY' if args.read_only_spoke else 'PORTAL_READ_WRITE'
        spoke = rest_client.portal.v2_create_portal(portal_type, parse_hub_hosts(args))

        if args.spoke_root:
            try:
                spoke = rest_client.portal.v2_propose_spoke_portal_root(
                    spoke.id, args.spoke_root, args.hub_root
                )
            except RequestError as e:
                print(
                    f'Spoke portal {spoke.id} created, but failed to propose initial spoke root',
                    file=sys.stderr,
                )
                raise e

        resolved = resolve_local_roots(rest_client, args.no_paths, get_spoke_local_roots(spoke))
        print_spoke_portal(args.json, spoke, resolved)


class AuthorizeHubPortal(qumulo.lib.opts.Subcommand):
    NAME = 'portal_authorize_hub'
    SYNOPSIS = SUPPRESS

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-i', '--id')
        parser.add_argument('-a', '--spoke-address')
        parser.add_argument('-p', '--spoke-port')
        parser.add_argument('-j', '--json')

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        print('Please use `portal_accept_hub --authorize-hub-roots ...` instead.', file=sys.stderr)
        sys.exit(1)


def parse_spoke_hosts(args: argparse.Namespace) -> List[PortalHost]:
    hosts = []
    if args.spoke_hosts:
        host_strs = [host.strip() for host in args.spoke_hosts.split(',') if host]
        for host_str in host_strs:
            host_addr = host_str.split(':')[0]
            host_port = int(host_str.split(':')[1]) if (':' in host_str) else args.spoke_port
            hosts.append(PortalHost.from_dict({'address': host_addr, 'port': host_port}))
    else:
        hosts.append(PortalHost.from_dict({'address': args.spoke_address, 'port': args.spoke_port}))
    return hosts


class AcceptHubPortal(qumulo.lib.opts.Subcommand):
    NAME = 'portal_accept_hub'
    SYNOPSIS = (
        'Accept the specified pending hub portal. Accepting a hub portal establishes '
        'a relationship with a spoke portal but does not provide data access automatically.'
    )

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-i', '--id', type=int, required=True, help='Hub portal ID')
        parser.add_argument('-j', '--json', help=JSON_HELP, action='store_true')
        parser.add_argument('-n', '--no-paths', help=NO_PATHS_HELP, action='store_true')
        parser.add_argument(
            '-A',
            '--authorize-hub-roots',
            help='Additionally authorize all pending hub portal roots',
            action='store_true',
        )

        host_group = parser.add_mutually_exclusive_group(required=True)
        host_group.add_argument('-m', '--spoke-hosts', help=HOSTS_HELP, type=str)
        host_group.add_argument('-a', '--spoke-address', help=ADDR_HELP)
        parser.add_argument('-p', '--spoke-port', default=PORTAL_PORT, help=PORT_HELP, type=int)

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        roots_to_authorize = []
        if args.authorize_hub_roots:
            hub = rest_client.portal.v2_get_hub_portal(args.id)
            roots_to_authorize = hub.pending_roots

        hub = rest_client.portal.v2_accept_hub_portal(
            args.id, parse_spoke_hosts(args), roots_to_authorize
        )

        resolved = resolve_local_roots(rest_client, args.no_paths, get_hub_local_roots(hub))
        print_hub_portal(args.json, hub, resolved)


class GetSpokePortal(qumulo.lib.opts.Subcommand):
    NAME = 'portal_get_spoke'
    SYNOPSIS = 'Get the configuration and status for a spoke portal on the current cluster'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-i', '--id', type=int, required=True, help='Spoke portal ID')
        parser.add_argument('-j', '--json', help=JSON_HELP, action='store_true')
        parser.add_argument('-n', '--no-paths', help=NO_PATHS_HELP, action='store_true')

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        spoke = rest_client.portal.v2_get_spoke_portal(args.id)
        resolved = resolve_local_roots(rest_client, args.no_paths, get_spoke_local_roots(spoke))
        print_spoke_portal(args.json, spoke, resolved)


# XXX rachel: special logic to handle breaking change after the 7.6.2 release, delete after 7.7.0.
def massage_hub_portal(resp: Dict['str', Any]) -> MultiRootHubPortal:
    resp['spoke_hosts'] = [resp['spoke_host']]
    del resp['spoke_host']
    return MultiRootHubPortal.schema().load(resp)


def massage_hub_portals(resp: Dict['str', Any]) -> List[MultiRootHubPortal]:
    hubs = []
    for hub_entry in resp['entries']:
        hubs.append(massage_hub_portal(hub_entry))
    return hubs


class GetHubPortal(qumulo.lib.opts.Subcommand):
    NAME = 'portal_get_hub'
    SYNOPSIS = 'Get the configuration and status for a hub portal on the current cluster'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-i', '--id', type=int, required=True, help='Hub portal ID')
        parser.add_argument('-j', '--json', help=JSON_HELP, action='store_true')
        parser.add_argument('-n', '--no-paths', help=NO_PATHS_HELP, action='store_true')

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        try:
            hub = rest_client.portal.v2_get_hub_portal(args.id)
        except Exception:
            resp = rest_client.request('GET', f'/v2/portal/hubs/{args.id}')
            hub = massage_hub_portal(resp)
        resolved = resolve_local_roots(rest_client, args.no_paths, get_hub_local_roots(hub))
        print_hub_portal(args.json, hub, resolved)


class ListPortals(qumulo.lib.opts.Subcommand):
    NAME = 'portal_list'
    SYNOPSIS = 'Get the configuration and status for all portals on the current cluster'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-j', '--json', help=JSON_HELP, action='store_true')

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        spokes = rest_client.portal.v2_list_spoke_portals()

        try:
            hubs = rest_client.portal.v2_list_hub_portals()
        except Exception:
            resp = rest_client.request('GET', '/v2/portal/hubs/')
            hubs = massage_hub_portals(resp)

        print_portals_list(args.json, spokes, hubs)


class ListSpokePortals(qumulo.lib.opts.Subcommand):
    NAME = 'portal_list_spokes'
    SYNOPSIS = 'Get the configuration and status for all spoke portals on the current cluster'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-j', '--json', help=JSON_HELP, action='store_true')

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        spokes = rest_client.portal.v2_list_spoke_portals()
        print_portals_list(args.json, spokes, [])


class ListHubPortals(qumulo.lib.opts.Subcommand):
    NAME = 'portal_list_hubs'
    SYNOPSIS = 'Get the configuration and status for all hub portals on the current cluster'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-j', '--json', help=JSON_HELP, action='store_true')

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        try:
            hubs = rest_client.portal.v2_list_hub_portals()
        except Exception:
            resp = rest_client.request('GET', '/v2/portal/hubs/')
            hubs = massage_hub_portals(resp)

        print_portals_list(args.json, [], hubs)


class ModifySpokeHost(qumulo.lib.opts.Subcommand):
    NAME = 'portal_modify_spoke_host'
    SYNOPSIS = 'Modify the remote hub address and port for a spoke portal'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-i', '--id', type=int, required=True, help='Spoke portal ID')
        parser.add_argument('-j', '--json', help=JSON_HELP, action='store_true')
        parser.add_argument('-n', '--no-paths', help=NO_PATHS_HELP, action='store_true')

        host_group = parser.add_mutually_exclusive_group(required=True)
        host_group.add_argument('-m', '--hub-hosts', help=HOSTS_HELP, type=str)
        host_group.add_argument('-a', '--hub-address', help=ADDR_HELP)
        parser.add_argument('-p', '--hub-port', default=PORTAL_PORT, help=PORT_HELP, type=int)

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        spoke = rest_client.portal.v2_modify_spoke_portal_host(args.id, parse_hub_hosts(args))
        resolved = resolve_local_roots(rest_client, args.no_paths, get_spoke_local_roots(spoke))
        print_spoke_portal(args.json, spoke, resolved)


class ModifyHubHost(qumulo.lib.opts.Subcommand):
    NAME = 'portal_modify_hub_host'
    SYNOPSIS = 'Modify the remote spoke address and port for a hub portal'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-i', '--id', type=int, required=True, help='Hub portal ID')
        parser.add_argument('-j', '--json', help=JSON_HELP, action='store_true')
        parser.add_argument('-n', '--no-paths', help=NO_PATHS_HELP, action='store_true')

        host_group = parser.add_mutually_exclusive_group(required=True)
        host_group.add_argument('-m', '--spoke-hosts', help=HOSTS_HELP, type=str)
        host_group.add_argument('-a', '--spoke-address', help=ADDR_HELP)
        parser.add_argument('-p', '--spoke-port', default=PORTAL_PORT, help=PORT_HELP, type=int)

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        hub = rest_client.portal.v2_modify_hub_portal_host(args.id, parse_spoke_hosts(args))
        resolved = resolve_local_roots(rest_client, args.no_paths, get_hub_local_roots(hub))
        print_hub_portal(args.json, hub, resolved)


class DeleteSpokePortal(qumulo.lib.opts.Subcommand):
    NAME = 'portal_delete_spoke'
    SYNOPSIS = 'Delete a spoke portal on the current cluster'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-i', '--id', type=int, required=True, help='Spoke portal ID')
        parser.add_argument('-j', '--json', help=JSON_HELP, action='store_true')
        parser.add_argument('-n', '--no-paths', help=NO_PATHS_HELP, action='store_true')
        parser.add_argument(
            '--force',
            help=f'Force the deletion of the spoke portal. {FORCE_DELETE_DETAIL}',
            action='store_true',
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        spoke = rest_client.portal.v2_delete_spoke_portal(args.id, force=args.force)
        if spoke:
            resolved = resolve_local_roots(rest_client, args.no_paths, get_spoke_local_roots(spoke))
            print_spoke_portal(args.json, spoke, resolved)
        else:
            print('Spoke portal deleted successfully.')


class DeleteHubPortal(qumulo.lib.opts.Subcommand):
    NAME = 'portal_delete_hub'
    SYNOPSIS = 'Delete a hub portal on the current cluster'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-i', '--id', type=int, required=True, help='Hub portal ID')
        parser.add_argument('-j', '--json', help=JSON_HELP, action='store_true')
        parser.add_argument('-n', '--no-paths', help=NO_PATHS_HELP, action='store_true')
        parser.add_argument(
            '--force',
            help=f'Force the deletion of the hub portal. {FORCE_DELETE_DETAIL}',
            action='store_true',
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        hub = rest_client.portal.v2_delete_hub_portal(args.id, force=args.force)
        if hub:
            resolved = resolve_local_roots(rest_client, args.no_paths, get_hub_local_roots(hub))
            print_hub_portal(args.json, hub, resolved)
        else:
            print('Hub portal deleted successfully.')


#                  _
#  _ __ ___   ___ | |_ ___
# | '__/ _ \ / _ \| __/ __|
# | | | (_) | (_) | |_\__ \
# |_|  \___/ \___/ \__|___/
#  FIGLET: roots
#


class ProposeSpokeRoot(qumulo.lib.opts.Subcommand):
    NAME = 'portal_propose_spoke_root'
    SYNOPSIS = (
        'Propose a spoke root directory for the specified spoke portal. This '
        'creates a pending hub root directory on the paired remote hub portal.'
    )

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-i', '--id', type=int, required=True, help='Spoke portal ID')
        parser.add_argument('-j', '--json', help=JSON_HELP, action='store_true')
        parser.add_argument('-n', '--no-paths', help=NO_PATHS_HELP, action='store_true')
        parser.add_argument('--spoke-root-path', type=str, required=True, help=SPOKE_ROOT_HELP)
        parser.add_argument('--hub-root-path', type=str, required=True, help=HUB_ROOT_HELP)

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        spoke = rest_client.portal.v2_propose_spoke_portal_root(
            args.id, args.spoke_root_path, args.hub_root_path
        )
        resolved = resolve_local_roots(rest_client, args.no_paths, get_spoke_local_roots(spoke))
        print_spoke_portal(args.json, spoke, resolved)


class DeleteSpokeRoot(qumulo.lib.opts.Subcommand):
    NAME = 'portal_delete_spoke_root'
    SYNOPSIS = (
        'Delete the specified spoke root directory for the specified spoke portal. '
        'This action does not affect the data in the hub root directory.'
    )

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-i', '--id', type=int, required=True, help='Spoke portal ID')
        parser.add_argument('-j', '--json', help=JSON_HELP, action='store_true')
        parser.add_argument('-n', '--no-paths', help=NO_PATHS_HELP, action='store_true')

        root_group = parser.add_mutually_exclusive_group(required=True)
        root_group.add_argument(
            '--spoke-root-id', type=str, help='File ID of the spoke root directory'
        )
        root_group.add_argument(
            '--spoke-root-path', type=str, help='Path of the spoke root directory'
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        root_id = resolve_spoke_root_path_or_id(
            rest_client, args.id, args.spoke_root_path, args.spoke_root_id
        )
        spoke = rest_client.portal.v2_delete_spoke_portal_root(args.id, root_id)
        resolved = resolve_local_roots(rest_client, args.no_paths, get_spoke_local_roots(spoke))
        print_spoke_portal(args.json, spoke, resolved)


class AuthorizeHubRoot(qumulo.lib.opts.Subcommand):
    NAME = 'portal_authorize_hub_root'
    SYNOPSIS = (
        'Authorize the specified hub root directory for the specified hub portal. '
        'This allows the spoke portal to access the data in the hub root directory.'
    )

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-i', '--id', type=int, required=True, help='Hub portal ID')
        parser.add_argument('-j', '--json', help=JSON_HELP, action='store_true')
        parser.add_argument('-n', '--no-paths', help=NO_PATHS_HELP, action='store_true')

        root_group = parser.add_mutually_exclusive_group(required=True)
        root_group.add_argument('--hub-root-id', type=str, help='File ID of the hub root directory')
        root_group.add_argument('--hub-root-path', type=str, help='Path of the hub root directory')

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        root_id = resolve_hub_root_path_or_id(rest_client, args.hub_root_path, args.hub_root_id)
        hub = rest_client.portal.v2_authorize_hub_portal_root(args.id, root_id)
        resolved = resolve_local_roots(rest_client, args.no_paths, get_hub_local_roots(hub))
        print_hub_portal(args.json, hub, resolved)


class DenyHubRoot(qumulo.lib.opts.Subcommand):
    NAME = 'portal_deny_hub_root'
    SYNOPSIS = (
        'Deny access to the specified hub root directory for the specified hub portal. '
        'This action does not affect the data in the hub root directory.'
    )

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('-i', '--id', type=int, required=True, help='Hub portal ID')
        parser.add_argument('-j', '--json', help=JSON_HELP, action='store_true')
        parser.add_argument('-n', '--no-paths', help=NO_PATHS_HELP, action='store_true')

        root_group = parser.add_mutually_exclusive_group(required=True)
        root_group.add_argument('--hub-root-id', type=str, help='File ID of the hub root directory')
        root_group.add_argument('--hub-root-path', type=str, help='Path of the hub root directory')

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        root_id = resolve_hub_root_path_or_id(rest_client, args.hub_root_path, args.hub_root_id)
        hub = rest_client.portal.v2_deny_hub_portal_root(args.id, root_id)
        resolved = resolve_local_roots(rest_client, args.no_paths, get_hub_local_roots(hub))
        print_hub_portal(args.json, hub, resolved)


class GetEvictionSettings(qumulo.lib.opts.Subcommand):
    NAME = 'portal_get_eviction_settings'
    SYNOPSIS = 'Retrieve the configuration for automated removal of cached data'

    @staticmethod
    def main(rest_client: RestClient, _: argparse.Namespace) -> None:
        settings = rest_client.portal.get_eviction_settings()
        print(pretty_json(settings.data.to_dict()))


class SetEvictionSettings(qumulo.lib.opts.Subcommand):
    NAME = 'portal_set_eviction_settings'
    SYNOPSIS = 'Configure the automated removal of cached data'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            '-f',
            '--free-threshold',
            type=float,
            required=True,
            help=(
                'The threshold of remaining free capacity on a cluster, as a decimal number '
                'between 0 and 1, that triggers the automated removal of cached data. For example, '
                'if you set this value to 0.05, the system begins to remove cached data from spoke '
                'portals when the cluster is 95%% full.'
            ),
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        config = EvictionSettings(free_threshold=args.free_threshold)
        settings = rest_client.portal.set_eviction_settings(config)
        print(pretty_json(settings.data.to_dict()))


class ListFileSystems(qumulo.lib.opts.Subcommand):
    NAME = 'portal_list_file_systems'
    SYNOPSIS = 'Retrieve portal information for all file systems'

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        file_systems = rest_client.portal.list_file_systems()
        print(pretty_json([fs.to_dict() for fs in file_systems]))


class GetFileSystem(qumulo.lib.opts.Subcommand):
    NAME = 'portal_get_file_system'
    SYNOPSIS = 'Retrieve portal information for a specific file system'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--uuid', type=str, required=True, help='File System UUID')

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        file_system = rest_client.portal.get_file_system(args.uuid)
        print(pretty_json(file_system.to_dict()))
