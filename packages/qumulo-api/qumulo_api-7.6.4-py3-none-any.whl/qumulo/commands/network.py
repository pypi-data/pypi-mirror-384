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


from argparse import ArgumentParser, Namespace, SUPPRESS
from typing import Any, Dict, List, Mapping, Sequence

import qumulo.lib.auth
import qumulo.lib.opts
import qumulo.lib.util
import qumulo.rest.network as network

from qumulo.lib.request import RestResponse
from qumulo.lib.util import tabulate
from qumulo.rest_client import RestClient


class MonitorNetworkCommand(qumulo.lib.opts.Subcommand):
    NAME = 'network_poll'
    SYNOPSIS = SUPPRESS

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument('--interface-id', type=int, default=1, help=SUPPRESS)
        parser.add_argument('--node-id', type=int, help='Node ID')

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        if args.node_id is not None:
            print(
                network.get_network_status_v2(
                    rest_client.conninfo, rest_client.credentials, args.interface_id, args.node_id
                )
            )
        else:
            print(
                network.list_network_status_v2(
                    rest_client.conninfo, rest_client.credentials, args.interface_id
                )
            )


class GetInterfaces(qumulo.lib.opts.Subcommand):
    NAME = 'network_list_interfaces'
    SYNOPSIS = SUPPRESS

    @staticmethod
    def main(rest_client: RestClient, _args: Namespace) -> None:
        print(network.list_interfaces(rest_client.conninfo, rest_client.credentials))


class GetInterface(qumulo.lib.opts.Subcommand):
    NAME = 'network_get_interface'
    SYNOPSIS = SUPPRESS

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument(
            '--interface-id', type=int, default=1, help='The unique ID of the interface'
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            network.get_interface(rest_client.conninfo, rest_client.credentials, args.interface_id)
        )


class GetNetworks(qumulo.lib.opts.Subcommand):
    NAME = 'network_list_networks'
    SYNOPSIS = SUPPRESS

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument('--interface-id', type=int, default=1, help=SUPPRESS)

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            network.list_networks(rest_client.conninfo, rest_client.credentials, args.interface_id)
        )


class GetNetwork(qumulo.lib.opts.Subcommand):
    NAME = 'network_get_network'
    SYNOPSIS = SUPPRESS

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument('--interface-id', type=int, default=1, help=SUPPRESS)
        parser.add_argument(
            '--network-id',
            type=int,
            required=True,
            help='The unique ID of the network on the interface',
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            network.get_network(
                rest_client.conninfo, rest_client.credentials, args.interface_id, args.network_id
            )
        )


class ModInterface(qumulo.lib.opts.Subcommand):
    NAME = 'network_mod_interface'
    SYNOPSIS = SUPPRESS

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument(
            '--interface-id', type=int, default=1, help='The unique ID of the interface'
        )

        parser.add_argument('--default-gateway', help='The default IPv4 gateway address')
        parser.add_argument('--default-gateway-ipv6', help='The default IPv6 gateway address')
        parser.add_argument(
            '--bonding-mode', choices=['ACTIVE_BACKUP', 'IEEE_8023AD'], help='Ethernet bonding mode'
        )
        parser.add_argument(
            '--mtu',
            type=int,
            help=(
                'The maximum transfer unit (MTU) in bytes of the interface '
                'and any untagged STATIC network.'
            ),
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        attributes = {
            key: getattr(args, key)
            for key in network.V2_INTERFACE_FIELDS
            if getattr(args, key) is not None
        }

        if not attributes:
            raise ValueError('One or more options must be specified')

        print(
            network.modify_interface(
                rest_client.conninfo, rest_client.credentials, args.interface_id, **attributes
            )
        )


def parse_comma_deliminated_args(args: Sequence[Sequence[str]]) -> List[str]:
    """
    The use of nargs allows specifying multiple args in the following way:
    $ qq network_add_network --ip-ranges 1.2.3.4-7 1.2.3.10-13

    The use of append allows specifying multiple args in the following way:
    $ qq network_add_network --ip-ranges 1.2.3.4-7 --ip-ranges 1.2.3.10-13

    This causes argparse to format the argument as a List[List[str]], with each use of the flag
    adding a new sublist.

    Additionally, we allow splitting an arg based on commas:
    $ qq network_add_network --ip-ranges 1.2.3.4-7,1.2.3.10-13

    So we need to take a List[List[str]], split the entries based on commas, and flatten it all.
    """
    nested = [arg.split(',') for flag in args for arg in flag]
    return [a.strip() for arg in nested for a in arg if a.strip() != '']


class AddNetwork(qumulo.lib.opts.Subcommand):
    NAME = 'network_add_network'
    SYNOPSIS = SUPPRESS

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument('--interface-id', type=int, default=1, help=SUPPRESS)

        parser.add_argument('--name', required=True, help='Network name')

        parser.add_argument('--assigned-by', default='STATIC', help=SUPPRESS)

        parser.add_argument(
            '--netmask',
            required=True,
            metavar='<netmask-or-subnet>',
            help='(if STATIC) IPv4 or IPv6 Netmask or Subnet CIDR eg. 255.255.255.0 or 10.1.1.0/24',
        )

        parser.add_argument(
            '--ip-ranges',
            nargs='+',
            action='append',
            metavar='<address-or-range>',
            required=True,
            help=(
                '(if STATIC) List of persistent IP ranges to replace the'
                ' current ranges. Can be single addresses or ranges,'
                ' comma separated. eg. 10.1.1.20-21 or 10.1.1.20,10.1.1.21'
            ),
        )

        parser.add_argument(
            '--floating-ip-ranges',
            nargs='+',
            default=[],
            action='append',
            metavar='<address-or-range>',
            help=(
                '(if STATIC) List of floating IP ranges to replace the'
                ' current ranges. Can be single addresses or ranges,'
                ' comma separated. eg. 10.1.1.20-21 or 10.1.1.20,10.1.1.21'
            ),
        )

        parser.add_argument(
            '--dns-servers',
            nargs='+',
            action='append',
            metavar='<address-or-range>',
            help=(
                'List of DNS Server IP addresses. Can be a'
                ' single address or multiple comma separated addresses.'
                ' eg. 10.1.1.10 or 10.1.1.10,10.1.1.15'
            ),
        )

        parser.add_argument(
            '--dns-search-domains',
            nargs='+',
            action='append',
            metavar='<search-domain>',
            help=(
                'List of DNS Search Domains to use. Can be a single domain or multiple comma '
                'separated domains. eg. my.domain.com or my.domain.com,your.domain.com'
            ),
        )

        parser.add_argument(
            '--mtu',
            type=int,
            help=(
                '(if STATIC) The Maximum Transfer Unit (MTU) in bytes'
                ' of a tagged STATIC network. The MTU of an untagged STATIC'
                ' network needs to be specified through interface MTU.'
            ),
        )

        parser.add_argument(
            '--vlan-id',
            type=int,
            help=(
                '(if STATIC) User assigned VLAN tag for network configuration.'
                ' 1-4094 are valid VLAN IDs and 0 is used for untagged networks.'
            ),
        )

        parser.add_argument(
            '--tenant-id',
            type=int,
            help=(
                'The tenant that the network will be assigned to. If only one tenant exists, the '
                'network will default to that tenant. Otherwise, not specifying the tenant will '
                'create the network unassigned.'
            ),
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        attributes = {
            key: getattr(args, key)
            for key in network.V2_NETWORK_FIELDS
            if getattr(args, key) is not None
        }

        attributes['ip_ranges'] = parse_comma_deliminated_args(args.ip_ranges)
        floating_ips = attributes.get('floating_ip_ranges', None)
        if floating_ips:
            attributes['floating_ip_ranges'] = parse_comma_deliminated_args(floating_ips)
        dns_servers = attributes.get('dns_servers', None)
        if dns_servers:
            attributes['dns_servers'] = parse_comma_deliminated_args(dns_servers)
        dns_search_domains = attributes.get('dns_search_domains', None)
        if dns_search_domains:
            attributes['dns_search_domains'] = parse_comma_deliminated_args(dns_search_domains)

        if not attributes:
            raise ValueError('One or more options must be specified')

        print(
            network.add_network(
                rest_client.conninfo, rest_client.credentials, args.interface_id, **attributes
            )
        )


class DeleteNetwork(qumulo.lib.opts.Subcommand):
    NAME = 'network_delete_network'
    SYNOPSIS = SUPPRESS

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument('--interface-id', type=int, default=1, help=SUPPRESS)
        parser.add_argument(
            '--network-id',
            type=int,
            required=True,
            help='The unique ID of the network on the interface',
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            network.delete_network(
                rest_client.conninfo, rest_client.credentials, args.interface_id, args.network_id
            )
        )


class ModNetwork(qumulo.lib.opts.Subcommand):
    NAME = 'network_mod_network'
    SYNOPSIS = SUPPRESS

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument('--interface-id', type=int, default=1, help=SUPPRESS)

        parser.add_argument(
            '--network-id',
            type=int,
            required=True,
            help='The unique ID of the network on the interface',
        )

        parser.add_argument('--name', help='Network name')

        parser.add_argument(
            '--assigned-by',
            choices=['DHCP', 'STATIC'],
            help='How to assign IP address, either DHCP or STATIC',
        )

        parser.add_argument(
            '--netmask',
            metavar='<netmask-or-subnet>',
            help='(if STATIC) IPv4 or IPv6 Netmask or Subnet CIDR eg. 255.255.255.0 or 10.1.1.0/24',
        )

        parser.add_argument(
            '--ip-ranges',
            nargs='+',
            action='append',
            metavar='<address-or-range>',
            help=(
                '(if STATIC) List of persistent IP ranges to replace the'
                ' current ranges. Can be single addresses or ranges,'
                ' comma separated. eg. 10.1.1.20-21 or 10.1.1.20,10.1.1.21'
            ),
        )

        parser.add_argument(
            '--floating-ip-ranges',
            nargs='+',
            action='append',
            metavar='<address-or-range>',
            help=(
                '(if STATIC) List of floating IP ranges to replace the'
                ' current ranges. Can be single addresses or ranges,'
                ' comma separated. eg. 10.1.1.20-21 or 10.1.1.20,10.1.1.21'
            ),
        )

        parser.add_argument(
            '--clear-floating-ip-ranges',
            action='store_true',
            help='(if STATIC) Clear the floating IP address ranges',
        )

        parser.add_argument(
            '--dns-servers',
            nargs='+',
            action='append',
            metavar='<address-or-range>',
            help=(
                'List of DNS Server IP addresses to replace the'
                ' current ranges. Can be a single address or multiple comma'
                ' separated addresses. eg. 10.1.1.10 or 10.1.1.10,10.1.1.15'
            ),
        )

        parser.add_argument(
            '--clear-dns-servers', action='store_true', help='Clear the DNS servers'
        )

        parser.add_argument(
            '--dns-search-domains',
            nargs='+',
            action='append',
            metavar='<search-domain>',
            help=(
                'List of DNS Search Domains to replace the current domains. Can be a single domain '
                'or multiple comma separated domains. eg. my.domain.com or '
                'my.domain.com,your.domain.com'
            ),
        )

        parser.add_argument(
            '--clear-dns-search-domains', action='store_true', help='Clear the DNS search domains'
        )

        parser.add_argument(
            '--mtu',
            type=int,
            help=(
                '(if STATIC) The Maximum Transfer Unit (MTU) in bytes'
                ' of a tagged STATIC network. The MTU of an untagged STATIC'
                ' network needs to be specified through interface MTU.'
            ),
        )

        parser.add_argument(
            '--vlan-id',
            type=int,
            help=(
                '(if STATIC) User assigned VLAN tag for network configuration.'
                ' 1-4094 are valid VLAN IDs and 0 is used for untagged networks.'
            ),
        )

        tenant_group = parser.add_mutually_exclusive_group()
        tenant_group.add_argument(
            '--tenant-id',
            type=int,
            help=(
                'The tenant that the network is assigned to. If only one tenant exists, this will'
                ' default to that tenant.'
            ),
        )

        tenant_group.add_argument(
            '--clear-tenant-id',
            action='store_true',
            help='Clear the tenant from the network, making the network unassigned',
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        attributes = {
            key: getattr(args, key)
            for key in network.V2_NETWORK_FIELDS
            if getattr(args, key) is not None
        }

        if args.clear_floating_ip_ranges:
            attributes['floating_ip_ranges'] = []

        if args.clear_dns_servers:
            attributes['dns_servers'] = []

        if args.clear_dns_search_domains:
            attributes['dns_search_domains'] = []

        if args.clear_tenant_id:
            attributes['tenant_id'] = None

        if not attributes:
            raise ValueError('One or more options must be specified')

        persistent_ips = attributes.get('ip_ranges', None)
        if persistent_ips:
            attributes['ip_ranges'] = parse_comma_deliminated_args(persistent_ips)
        floating_ips = attributes.get('floating_ip_ranges', None)
        if floating_ips:
            attributes['floating_ip_ranges'] = parse_comma_deliminated_args(floating_ips)
        dns_servers = attributes.get('dns_servers', None)
        if dns_servers:
            attributes['dns_servers'] = parse_comma_deliminated_args(dns_servers)
        dns_search_domains = attributes.get('dns_search_domains', None)
        if dns_search_domains:
            attributes['dns_search_domains'] = parse_comma_deliminated_args(dns_search_domains)

        print(
            network.modify_network(
                rest_client.conninfo,
                rest_client.credentials,
                args.interface_id,
                args.network_id,
                **attributes,
            )
        )


class GetStaticIpAllocationCommand(qumulo.lib.opts.Subcommand):
    NAME = 'static_ip_allocation'
    SYNOPSIS = 'Get cluster-wide static IP allocation'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        parser.add_argument(
            '--try-ranges', help="Specify ip range list to try (e.g. '1.1.1.10-12,10.20.5.0/24'"
        )
        parser.add_argument(
            '--try-netmask', help='Specify netmask to apply when using --try-range option'
        )
        parser.add_argument(
            '--try-floating-ranges',
            help="Specify floating ip range list to try (e.g. '1.1.1.10-12,10.20.5.0/24'",
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            network.get_static_ip_allocation(
                rest_client.conninfo,
                rest_client.credentials,
                args.try_ranges,
                args.try_netmask,
                args.try_floating_ranges,
            )
        )


class GetFloatingIpAllocationCommand(qumulo.lib.opts.Subcommand):
    NAME = 'floating_ip_allocation'
    SYNOPSIS = 'Get cluster-wide floating IP allocation'

    @staticmethod
    def main(rest_client: RestClient, _args: Namespace) -> None:
        print(network.get_floating_ip_allocation(rest_client.conninfo, rest_client.credentials))


def print_connection_counts(connlist: RestResponse) -> None:
    def initial_counts() -> Dict[str, int]:
        return {
            'CONNECTION_TYPE_NFS': 0,
            'CONNECTION_TYPE_SMB': 0,
            'CONNECTION_TYPE_FTP': 0,
            'CONNECTION_TYPE_S3': 0,
            'CONNECTION_TYPE_REST': 0,
        }

    # Initialize counts to zero
    totals = initial_counts()
    per_node = {}
    for node_data in connlist.data:
        per_node[node_data['id']] = initial_counts()

    # Sum up connection counts
    for node_data in connlist.data:
        for conn in node_data['connections']:
            totals[conn['type']] += 1
            per_node[node_data['id']][conn['type']] += 1

    # Output pretty-printed connection counts
    print(
        'Total: SMB {} NFS {} FTP {} S3 {} REST {}'.format(
            totals['CONNECTION_TYPE_SMB'],
            totals['CONNECTION_TYPE_NFS'],
            totals['CONNECTION_TYPE_FTP'],
            totals['CONNECTION_TYPE_S3'],
            totals['CONNECTION_TYPE_REST'],
        )
    )
    for node in sorted(per_node.keys()):
        print(
            'Node{}: SMB {} NFS {} FTP {} S3 {} REST {}'.format(
                node,
                per_node[node]['CONNECTION_TYPE_SMB'],
                per_node[node]['CONNECTION_TYPE_NFS'],
                per_node[node]['CONNECTION_TYPE_FTP'],
                per_node[node]['CONNECTION_TYPE_S3'],
                per_node[node]['CONNECTION_TYPE_REST'],
            )
        )


def make_connections_table(data: Sequence[Mapping[str, Any]]) -> str:
    rows = []
    for node_data in data:
        node_id = node_data['id']
        for c in node_data['connections']:
            rows.append([node_id, c['tenant_id'], c['network_address'], c['type']])
    headers = ['NODE', 'TENANT', 'CLIENT_IP', 'PROTOCOL_TYPE']
    return tabulate(rows, headers)


class GetClientConnectionsCommand(qumulo.lib.opts.Subcommand):
    NAME = 'network_list_connections'
    SYNOPSIS = 'Get the list of SMB and NFS protocol connections per node.'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '-c',
            '--counts',
            help='Pretty-print connection counts for the cluster and each node',
            action='store_true',
        )
        group.add_argument(
            '--json',
            help='Print json instead of default pretty-printed connection table',
            action='store_true',
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        response = network.connections(rest_client.conninfo, rest_client.credentials)
        if args.counts:
            print_connection_counts(response)
        elif args.json:
            print(response)
        else:
            print(make_connections_table(response.data))
