# Copyright (c) 2025 Qumulo, Inc.
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
import json
import os
import re
import shutil
import subprocess
import tempfile
import textwrap

from typing import Dict, Optional

import qumulo.lib.opts

from qumulo.commands.network import parse_comma_deliminated_args
from qumulo.lib.request import pretty_json
from qumulo.rest.network_v3 import AddressesKind
from qumulo.rest_client import RestClient


class GetClusterNetworkConfig(qumulo.lib.opts.Subcommand):
    NAME = 'network_get_config'
    # XXX SQUALL: Remove ALIASES after next quaterly, 7.8.0?
    ALIASES = ['network_v3_get_config', 'network_preview_get_config']
    SYNOPSIS = 'Retrieve the cluster-wide network config'
    DESCRIPTION = textwrap.dedent(
        """\
        Retrieve the cluster-wide network config.
        """
    )

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            '-o',
            '--output',
            type=str,
            help='The file to which the network config should be written.',
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        config = pretty_json(rest_client.network_v3.get_config_raw().data, sort_keys=False)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(config)
        else:
            print(config)


WELL_KNOWN_EDITORS = ['editor', 'vim', 'vi']


def find_default_editor() -> str:
    editor = os.environ.get('EDITOR') or os.environ.get('VISUAL')
    if editor:
        return editor

    for e in WELL_KNOWN_EDITORS:
        path = shutil.which(e)
        if path is not None:
            return path

    raise FileNotFoundError(
        'Unable to find a text editor on this system. '
        'Consider setting your $EDITOR environment variable'
    )


def yes_or_no(message: str) -> bool:
    responses = {'': True, 'y': True, 'yes': True, 'n': False, 'no': False}
    while True:
        line = input(message)
        answer = responses.get(line.lower().strip(), None)
        if answer is not None:
            return answer


HELPER_MESSAGE = r"""
 _____ _____ __  __ ____  _        _  _____ _____ ____
|_   _| ____|  \/  |  _ \| |      / \|_   _| ____/ ___|
  | | |  _| | |\/| | |_) | |     / _ \ | | |  _| \___ \
  | | | |___| |  | |  __/| |___ / ___ \| | | |___ ___) |
  |_| |_____|_|  |_|_|   |_____/_/   \_\_| |_____|____/

To communicate with the API endpoint, you can use the following JSON templates based on typical
network configurations. Use these examples to structure your JSON and adjust the values to fit
your configuration needs.

Add a vlan interface over the frontend bond:
"frontend_vlan_configs": [
    ...
    {
        "vlan_id": <1-4094>,
        "mtu": <u32, optional>,
        "network_id": <u32>,
        "second_network_id": <u32, optional>
    }
]

Add a DHCP network config:
"frontend_networks": [
    ...
    {
        "id": <u32>,
        "name": <str>,
        "tenant_id": <u32, optional>,
        "addresses": {
            "type": "DHCP",
            "dhcp_addresses": {
                "floating_ip_ranges": [<IP ranges, "1.1.1.1-4">]
            }
        }
    }
]

Add a STATIC network config:
"frontend_networks": [
    ...
    {
        "id": <u32>,
        "name": <str>,
        "tenant_id": <u32, optional>,
        "addresses": {
            "type": "STATIC",
            "static_addresses": {
                "default_gateway": <IP addr, "1.1.1.1", empty-able>,
                "ip_ranges": [<IP ranges, "1.1.1.1-4">],
                "floating_ip_ranges": [<IP ranges, "1.1.1.1-4">],
                "netmask": <Ip addr or CIDR format, "255.0.0.0", "aa:bb::/64">
            }
        }
    }
]

Add a HOST network config:
"frontend_networks": [
    ...
    {
        "id": <u32>,
        "name": <str>,
        "tenant_id": <u32, optional>,
        "addresses": {
            "type": "HOST",
            "host_addresses": {
                "floating_ip_ranges": [<IP ranges, "1.1.1.1-4">],
                "netmask": <Ip addr or CIDR format, "255.0.0.0", "aa:bb::/64">
            }
        }
    }
]
"""


def trim_comments(s: str) -> str:
    trimmed_one_line_comments = re.sub(r'(#|//).*', '', s, flags=re.MULTILINE)
    trimmed_block_comments = re.sub(r'/\*.*?\*/', '', trimmed_one_line_comments, flags=re.DOTALL)
    return trimmed_block_comments


class ValidateOrPutClusterNetworkConfig(qumulo.lib.opts.Subcommand):
    NAME = 'network_put_config'
    # XXX SQUALL: Remove ALIASES after next quaterly, 7.8.0?
    ALIASES = ['network_v3_put_config', 'network_preview_put_config']
    SYNOPSIS = 'Validate or overwrite the cluster-wide network configuration.'
    DESCRIPTION = textwrap.dedent(
        """\
        Validate or overwrite the cluster-wide network configuration.
        """
    )

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate a new cluster-wide network config without writing it to disk.',
            default=False,
        )
        input_group = parser.add_mutually_exclusive_group(required=True)
        input_group.add_argument(
            '--file',
            type=str,
            help='The path to the JSON file that contains your new cluster-wide network config.',
        )
        input_group.add_argument(
            '--modify',
            action='store_true',
            help='Open the current cluster-wide network config in your default editor. '
            'After saving and closing your editor, the modified config will be validated.',
        )
        input_group.add_argument(
            '--templates',
            action='store_true',
            help='Print out the templates for configuring the API endpoint.',
            default=False,
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        if args.templates:
            print(HELPER_MESSAGE)
            return

        # XXX SQUALL-564: Figure out the best way to display the error backtrace to
        # make it easier to debug API errors.

        def execute(config: Dict[str, object], if_match: Optional[str] = None) -> None:
            if args.dry_run:
                rest_client.network_v3.validate(config, if_match)
            else:
                print(rest_client.network_v3.put_config(config, if_match))

        if args.file:
            with open(args.file) as file:
                contents = trim_comments(file.read())
                config: Dict[str, object] = json.loads(contents)
            execute(config)

        elif args.modify:
            current_config = rest_client.network_v3.get_config_raw()
            current_config_str = pretty_json(current_config.data, sort_keys=False)
            with tempfile.NamedTemporaryFile() as f:
                f.write(current_config_str.encode())
                f.write(('\n\n/*' + HELPER_MESSAGE + '*/').encode())
                f.flush()

                stop = False
                while not stop:
                    try:
                        subprocess.call([find_default_editor(), f.name])
                        f.seek(0)
                        contents = trim_comments(f.read().decode())
                        config = json.loads(contents)

                        execute(config, current_config.etag)

                        stop = True
                    except (json.decoder.JSONDecodeError, qumulo.lib.request.RequestError) as e:
                        if isinstance(e, json.decoder.JSONDecodeError):
                            print(str(e))
                        else:
                            print(e.pretty_str())

                        stop = not yes_or_no('\nContinue editing [Y/n]: ')
                        if stop:
                            print('Stop editing the configuration.')
                            return

        if args.dry_run:
            print('Proposed cluster-wide network configuration is valid!')
        else:
            print('Successfully updated the cluster-wide network configuration!')


class NetworkStatusCommand(qumulo.lib.opts.Subcommand):
    NAME = 'network_status'
    # XXX SQUALL: Remove ALIASES after next quaterly, 7.8.0?
    ALIASES = ['network_v3_status', 'network_preview_status']
    SYNOPSIS = 'Retrieve the comprehensive network status'
    DESCRIPTION = textwrap.dedent(
        """\
        Retrieve the comprehensive network status.
        """
    )

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--node-id', type=int, help='Node ID')

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        if args.node_id is not None:
            print(
                pretty_json(
                    rest_client.network_v3.get_network_status(args.node_id), sort_keys=False
                )
            )
        else:
            # sort the output by node id, to provide a less confusing and deterministic output.
            output = rest_client.network_v3.list_network_statuses()
            output.sort(key=lambda x: int(x['node_id']))

            print(pretty_json(output, sort_keys=False))


class FrontendInterfacesCommand(qumulo.lib.opts.Subcommand):
    NAME = 'network_frontend_interfaces'
    # XXX SQUALL: Remove ALIASES after next quaterly, 7.8.0?
    ALIASES = ['network_v3_frontend_interfaces', 'network_preview_frontend_interfaces']
    SYNOPSIS = 'Retrieve the list of frontend interfaces for every node in the cluster.'
    DESCRIPTION = textwrap.dedent(
        """\
        Retrieve the list of frontend interfaces for every node in the cluster.
        """
    )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        output = rest_client.network_v3.get_cluster_frontend_interfaces()

        print(pretty_json(output))


class BackendInterfacesCommand(qumulo.lib.opts.Subcommand):
    NAME = 'network_backend_interfaces'
    # XXX SQUALL: Remove ALIASES after next quaterly, 7.8.0?
    ALIASES = ['network_v3_backend_interfaces', 'network_preview_backend_interfaces']
    SYNOPSIS = 'Retrieve the list of backend interfaces for every node in the cluster.'
    DESCRIPTION = textwrap.dedent(
        """\
        Retrieve the list of backend interfaces for every node in the cluster.
        """
    )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        output = rest_client.network_v3.get_cluster_backend_interfaces()

        print(pretty_json(output))


class CreateNetworkCommand(qumulo.lib.opts.Subcommand):
    NAME = 'network_create_network'
    # XXX SQUALL: Remove ALIASES after next quaterly, 7.8.0?
    ALIASES = ['network_v3_add_network', 'network_preview_add_network']
    SYNOPSIS = 'Add a network to the cluster-wide network config.'
    DESCRIPTION = textwrap.dedent(
        """\
        Add a network to the cluster-wide network config.
        """
    )

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--network-id', type=int, required=True, help='Network ID')
        parser.add_argument('--name', required=True, help='Network name')
        parser.add_argument(
            '--tenant-id',
            type=int,
            help=(
                'The tenant that the network will be assigned to. If only one tenant exists, the '
                'network will default to that tenant. Otherwise, not specifying the tenant will '
                'create the network unassigned.'
            ),
        )

        common_parent = argparse.ArgumentParser(add_help=False)
        common_parent.add_argument(
            '--floating-ip-ranges',
            nargs='+',
            default=[],
            action='append',
            metavar='<address-or-range>',
            help=(
                'List of floating IP ranges to replace the'
                ' current ranges. Can be single addresses or ranges,'
                ' comma separated. eg. 10.1.1.20-21 or 10.1.1.20,10.1.1.21'
            ),
        )

        netmask_parent = argparse.ArgumentParser(add_help=False)
        netmask_parent.add_argument(
            '--netmask',
            metavar='<netmask-or-subnet>',
            help='IPv4 or IPv6 Netmask or Subnet CIDR eg. 255.255.255.0 or 10.1.1.0/24',
        )

        subparsers = parser.add_subparsers(
            dest='assigned_by', required=True, help='The kind of network you want to add.'
        )

        vlan_parent = argparse.ArgumentParser(add_help=False)
        vlan_parent.add_argument(
            '--vlan-id',
            type=int,
            help=(
                '(if STATIC) User assigned VLAN tag for network configuration.'
                ' 1-4094 are valid VLAN IDs and 0 is used for untagged networks.'
            ),
        )
        vlan_parent.add_argument(
            '--vlan-mtu', type=int, help='The maximum transfer unit (MTU) in bytes of the interface'
        )

        host = subparsers.add_parser(
            'host_managed',
            help='Assign floating IPs to an interface not managed by Qumulo Core.',
            parents=[common_parent, netmask_parent],
        )
        host.set_defaults(run=CreateNetworkCommand.host_network)

        dhcp = subparsers.add_parser(
            'dhcp',
            help='Create a network on an interface managed by Qumulo Core.',
            parents=[common_parent, vlan_parent],
        )
        dhcp.set_defaults(run=CreateNetworkCommand.dhcp_network)

        static = subparsers.add_parser(
            'static',
            help='Create a network on an interface managed by Qumulo Core.',
            parents=[common_parent, vlan_parent],
        )
        static.set_defaults(run=CreateNetworkCommand.static_network)
        static.add_argument(
            '--default-gateway',
            default='',
            metavar='<default-gateway>',
            help='IPv4 or IPv6 default gateway eg. 10.1.1.1',
        )
        static.add_argument(
            '--ip-ranges',
            nargs='+',
            action='append',
            metavar='<address-or-range>',
            required=True,
            help='List of IP ranges eg. 10.1.1.20-21 or 10.1.1.20,10.1.1.21',
        )
        static.add_argument(
            '--netmask',
            metavar='<netmask-or-subnet>',
            required=True,
            help='IPv4 or IPv6 Netmask or Subnet CIDR eg. 255.255.255.0 or 10.1.1.0/24',
        )

    @staticmethod
    def host_network(rest_client: RestClient, args: argparse.Namespace) -> None:
        rest_client.network_v3.modify_config(
            lambda old_config: old_config.create_network(
                network_id=args.network_id,
                name=args.name,
                addresses_kind=AddressesKind.HOST,
                tenant_id=args.tenant_id,
                netmask=args.netmask,
                floating_ip_ranges=parse_comma_deliminated_args(args.floating_ip_ranges),
            )
        )

    @staticmethod
    def dhcp_network(rest_client: RestClient, args: argparse.Namespace) -> None:
        rest_client.network_v3.modify_config(
            lambda old_config: old_config.create_network(
                network_id=args.network_id,
                name=args.name,
                addresses_kind=AddressesKind.DHCP,
                tenant_id=args.tenant_id,
                floating_ip_ranges=parse_comma_deliminated_args(args.floating_ip_ranges),
                vlan_id=args.vlan_id,
                vlan_mtu=args.vlan_mtu,
            )
        )

    @staticmethod
    def static_network(rest_client: RestClient, args: argparse.Namespace) -> None:
        rest_client.network_v3.modify_config(
            lambda old_config: old_config.create_network(
                network_id=args.network_id,
                name=args.name,
                addresses_kind=AddressesKind.STATIC,
                tenant_id=args.tenant_id,
                default_gateway=args.default_gateway,
                ip_ranges=parse_comma_deliminated_args(args.ip_ranges),
                netmask=args.netmask,
                floating_ip_ranges=parse_comma_deliminated_args(args.floating_ip_ranges),
                vlan_id=args.vlan_id,
                vlan_mtu=args.vlan_mtu,
            )
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        args.run(rest_client, args)


class ModifyNetworkCommand(qumulo.lib.opts.Subcommand):
    NAME = 'network_modify_network'
    # XXX SQUALL: Remove ALIASES after next quaterly, 7.8.0?
    ALIASES = ['network_v3_modify_network', 'network_preview_modify_network']
    SYNOPSIS = 'Modify a network in the cluster-wide network config.'
    DESCRIPTION = textwrap.dedent(
        """\
        Modify a network in the cluster-wide network config.
        """
    )

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--network-id', type=int, required=True, help='Network ID')
        parser.add_argument('--name', help='Network name')
        exclusive_tenant = parser.add_mutually_exclusive_group()
        exclusive_tenant.add_argument(
            '--tenant-id',
            type=int,
            help=(
                'The tenant that the network will be assigned to. If only one tenant exists, the '
                'network will default to that tenant. Otherwise, not specifying the tenant will '
                'create the network unassigned.'
            ),
        )
        exclusive_tenant.add_argument(
            '--clear-tenant-id',
            default=False,
            action='store_true',
            help='Clear the tenant from the network, making the network unassigned',
        )

        common_parent = argparse.ArgumentParser(add_help=False)
        exclusive_floating_ips = common_parent.add_mutually_exclusive_group()
        exclusive_floating_ips.add_argument(
            '--floating-ip-ranges',
            nargs='+',
            action='append',
            metavar='<address-or-range>',
            help=(
                'List of floating IP ranges to replace the'
                ' current ranges. Can be single addresses or ranges,'
                ' comma separated. eg. 10.1.1.20-21 or 10.1.1.20,10.1.1.21'
            ),
        )
        exclusive_floating_ips.add_argument(
            '--clear-floating-ips',
            default=False,
            action='store_true',
            help='Clear the floating IPs from the network',
        )

        netmask_parent = argparse.ArgumentParser(add_help=False)
        netmask_parent.add_argument(
            '--netmask',
            metavar='<netmask-or-subnet>',
            help='IPv4 or IPv6 Netmask or Subnet CIDR eg. 255.255.255.0 or 10.1.1.0/24',
        )

        subparsers = parser.add_subparsers(
            dest='assigned_by', required=True, help='The kind of network you want to add.'
        )
        host = subparsers.add_parser(
            'host_managed',
            help='Assign floating IPs to an interface not managed by Qumulo Core.',
            parents=[common_parent, netmask_parent],
        )
        host.set_defaults(run=ModifyNetworkCommand.host_network)

        dhcp = subparsers.add_parser(
            'dhcp',
            help='Modify a network on an interface managed by Qumulo Core.',
            parents=[common_parent],
        )
        dhcp.set_defaults(run=ModifyNetworkCommand.dhcp_network)

        static = subparsers.add_parser(
            'static',
            help='Modify a network on an interface managed by Qumulo Core.',
            parents=[common_parent, netmask_parent],
        )
        static.set_defaults(run=ModifyNetworkCommand.static_network)
        static.add_argument(
            '--default-gateway',
            metavar='<default-gateway>',
            help='IPv4 or IPv6 default gateway eg. 10.1.1.1',
        )
        static.add_argument(
            '--ip-ranges',
            nargs='+',
            action='append',
            metavar='<address-or-range>',
            help='List of IP ranges eg. 10.1.1.20-21 or 10.1.1.20,10.1.1.21',
        )

    @staticmethod
    def host_network(rest_client: RestClient, args: argparse.Namespace) -> None:
        if (
            args.name is None
            and args.tenant_id is None
            and args.clear_tenant_id is False
            and args.clear_floating_ips is False
            and args.netmask is None
            and not args.floating_ip_ranges
        ):
            raise ValueError('One or more options must be specified')

        floating_ip_ranges = None
        if args.floating_ip_ranges:
            floating_ip_ranges = parse_comma_deliminated_args(args.floating_ip_ranges)

        rest_client.network_v3.modify_config(
            lambda old_config: old_config.modify_network(
                network_id=args.network_id,
                name=args.name,
                addresses_kind=AddressesKind.HOST,
                tenant_id=args.tenant_id,
                clear_tenant_id=args.clear_tenant_id,
                netmask=args.netmask,
                floating_ip_ranges=[] if args.clear_floating_ips else floating_ip_ranges,
            )
        )

    @staticmethod
    def dhcp_network(rest_client: RestClient, args: argparse.Namespace) -> None:
        floating_ip_ranges = None
        if args.floating_ip_ranges:
            floating_ip_ranges = parse_comma_deliminated_args(args.floating_ip_ranges)

        rest_client.network_v3.modify_config(
            lambda old_config: old_config.modify_network(
                network_id=args.network_id,
                name=args.name,
                addresses_kind=AddressesKind.DHCP,
                tenant_id=args.tenant_id,
                clear_tenant_id=args.clear_tenant_id,
                floating_ip_ranges=[] if args.clear_floating_ips else floating_ip_ranges,
            )
        )

    @staticmethod
    def static_network(rest_client: RestClient, args: argparse.Namespace) -> None:
        floating_ip_ranges = None
        if args.floating_ip_ranges:
            floating_ip_ranges = parse_comma_deliminated_args(args.floating_ip_ranges)

        ip_ranges = None
        if args.ip_ranges:
            ip_ranges = parse_comma_deliminated_args(args.ip_ranges)

        if (
            args.name is None
            and args.tenant_id is None
            and args.clear_tenant_id is False
            and args.clear_floating_ips is False
            and args.netmask is None
            and args.default_gateway is None
            and args.ip_ranges is None
            and not args.floating_ip_ranges
        ):
            raise ValueError('One or more options must be specified')

        rest_client.network_v3.modify_config(
            lambda old_config: old_config.modify_network(
                network_id=args.network_id,
                name=args.name,
                addresses_kind=AddressesKind.STATIC,
                tenant_id=args.tenant_id,
                clear_tenant_id=args.clear_tenant_id,
                default_gateway=args.default_gateway,
                ip_ranges=ip_ranges,
                netmask=args.netmask,
                floating_ip_ranges=[] if args.clear_floating_ips else floating_ip_ranges,
            )
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        args.run(rest_client, args)


class RemoveNetworkCommand(qumulo.lib.opts.Subcommand):
    NAME = 'network_remove_network'
    # XXX SQUALL: Remove ALIASES after next quaterly, 7.8.0?
    ALIASES = ['network_preview_delete_network', 'network_v3_delete_network']
    SYNOPSIS = 'Delete a network from the cluster-wide network config.'
    DESCRIPTION = textwrap.dedent(
        """\
        Delete a network from the cluster-wide network config.
        """
    )

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--network-id', type=int, required=True, help='Network to delete')

        parser.add_argument(
            '--delete-orphaned-vlans',
            default=False,
            action='store_true',
            help=(
                'Delete the vlan associated with the specified network'
                ' if it is the only network on the VLAN.'
            ),
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        rest_client.network_v3.modify_config(
            lambda old_config: old_config.remove_network(
                network_id=args.network_id, delete_orphaned_vlans=args.delete_orphaned_vlans
            )
        )


class ModifyInterfaceCommand(qumulo.lib.opts.Subcommand):
    NAME = 'network_modify_interface'
    # XXX SQUALL: Remove ALIASES after next quaterly, 7.8.0?
    ALIASES = ['network_v3_modify_interface', 'network_preview_modify_interface']
    SYNOPSIS = 'Modify a network interface in the cluster-wide network config.'
    DESCRIPTION = textwrap.dedent(
        """\
        Modify a network interface in the cluster-wide network config.
        """
    )

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        common_parent = argparse.ArgumentParser(add_help=False)
        common_parent.add_argument(
            '--mtu', type=int, help='The maximum transfer unit (MTU) in bytes of the interface'
        )

        subparsers = parser.add_subparsers(
            dest='interface', required=True, help='The kind of interface you want to modify.'
        )

        bond = subparsers.add_parser(
            'bond',
            help='Modify the mtu or bonding mode of a bond interface.',
            parents=[common_parent],
        )
        bond.set_defaults(run=ModifyInterfaceCommand.bond_interface)
        bond.add_argument(
            '--bonding-mode', choices=['ACTIVE_BACKUP', 'IEEE_8023AD'], help='Ethernet bonding mode'
        )
        bond.add_argument(
            '--backend',
            action='store_true',
            default=False,
            help='Use this to modify the backend interface.',
        )

        vlan = subparsers.add_parser('vlan', help='', parents=[common_parent])
        vlan.set_defaults(run=ModifyInterfaceCommand.vlan_interface)
        vlan.add_argument(
            '--current-vlan-id',
            required=True,
            type=int,
            help=('The current vlan id of the interface.'),
        )
        vlan.add_argument(
            '--new-vlan-id',
            type=int,
            help=('Use this to modify the chosen vlan id to a new vlan id.'),
        )

    @staticmethod
    def bond_interface(rest_client: RestClient, args: argparse.Namespace) -> None:
        rest_client.network_v3.modify_config(
            lambda old_config: old_config.modify_bond_interface(
                mtu=args.mtu, bonding_mode=args.bonding_mode, backend_bond=args.backend
            )
        )

    @staticmethod
    def vlan_interface(rest_client: RestClient, args: argparse.Namespace) -> None:
        rest_client.network_v3.modify_config(
            lambda old_config: old_config.modify_vlan_interface(
                mtu=args.mtu, current_vlan_id=args.current_vlan_id, new_vlan_id=args.new_vlan_id
            )
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        args.run(rest_client, args)
