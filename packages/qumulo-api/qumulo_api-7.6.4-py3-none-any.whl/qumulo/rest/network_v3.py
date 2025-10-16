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

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Set

from dataclasses_json import dataclass_json, DataClassJsonMixin

import qumulo.lib.request as request


class BackendBondNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__('Backend bond not found, is this a split networking cluster?')


class CannotModifyInterfaceInHostNetworks(Exception):
    def __init__(self) -> None:
        super().__init__(
            'No managed interfaces to modify, cannot modify interfaces for host managed networks'
        )


class NetworkAlreadyExistsError(Exception):
    def __init__(self, network_id: int) -> None:
        super().__init__(f'Network {network_id} already exists')


class NetworkNotFoundError(Exception):
    def __init__(self, network_id: int) -> None:
        super().__init__(f'Network {network_id} does not exist')


class OrphanedVlanError(Exception):
    def __init__(self, vlan_id: int) -> None:
        super().__init__(f'Vlan {vlan_id} does not have any networks')


class VlanAlreadyExistsError(Exception):
    def __init__(self, current_vlan_id: int, new_vlan_id: int) -> None:
        super().__init__(
            f'Tried to change vlan {current_vlan_id} to {new_vlan_id} but it already exists'
        )


class VlanNotFoundError(Exception):
    def __init__(self, vlan_id: int) -> None:
        super().__init__(f'Vlan {vlan_id} does not exist')


class VlanSecondaryNetworkAlreadyAssignedError(Exception):
    def __init__(self, vlan_id: int, network_id_primary: int, network_id_secondary: int) -> None:
        super().__init__(
            f'Vlan {vlan_id} secondary network is already assigned to networks {network_id_primary}'
            f', {network_id_secondary}. Cannot add new network. Consider using modify instead'
        )


@dataclass_json
@dataclass
class StaticAddresses:
    default_gateway: str
    ip_ranges: List[str]
    floating_ip_ranges: List[str]
    netmask: str


@dataclass_json
@dataclass
class DhcpAddresses:
    floating_ip_ranges: List[str]
    netmask: Optional[str]


@dataclass_json
@dataclass
class HostAddresses:
    floating_ip_ranges: List[str]
    netmask: Optional[str]


class AddressesKind(str, Enum):
    DHCP = 'DHCP'
    HOST = 'HOST'
    STATIC = 'STATIC'


class ConflictingNetworkTypesError(Exception):
    def __init__(self, type_desired: AddressesKind, type_present: AddressesKind) -> None:
        super().__init__(
            f'{type_desired} network cannot be mixed with {type_present} ' 'network already present'
        )
        self.type_desired = type_desired
        self.type_present = type_present


class RequestResultsinNetworkTypeMix(Exception):
    def __init__(
        self, type_desired: AddressesKind, type_present: AddressesKind, network_count: int
    ) -> None:
        super().__init__(
            f'Network requested is type {type_desired}, but current type is {type_present} and '
            f'{network_count} networks exist which would leave us with a mixed network mode which '
            'is not allowed. Reduce network count to 1 before transitioning network types'
        )


@dataclass_json
@dataclass
class Addresses:
    type: AddressesKind
    static_addresses: Optional[StaticAddresses] = None
    dhcp_addresses: Optional[DhcpAddresses] = None
    host_addresses: Optional[HostAddresses] = None


@dataclass_json
@dataclass
class FrontendNetwork:
    id: int
    name: str
    addresses: Addresses
    tenant_id: Optional[int] = None

    def modify_addresses(self, **kwargs: Optional[object]) -> None:
        if self.addresses.type == AddressesKind.DHCP:
            assert self.addresses.dhcp_addresses is not None
            addresses_dict = asdict(self.addresses.dhcp_addresses)
            addresses_dict.update(kwargs)
            self.addresses.dhcp_addresses = DhcpAddresses(**addresses_dict)
        elif self.addresses.type == AddressesKind.HOST:
            assert self.addresses.host_addresses is not None
            addresses_dict = asdict(self.addresses.host_addresses)
            addresses_dict.update(kwargs)
            self.addresses.host_addresses = HostAddresses(**addresses_dict)
        elif self.addresses.type == AddressesKind.STATIC:
            assert self.addresses.static_addresses is not None
            addresses_dict = asdict(self.addresses.static_addresses)
            addresses_dict.update(kwargs)
            self.addresses.static_addresses = StaticAddresses(**addresses_dict)
        else:
            raise Exception('unreachable')

    def get_floating_ips(self) -> List[str]:
        if self.addresses.type == AddressesKind.DHCP:
            assert self.addresses.dhcp_addresses is not None
            return self.addresses.dhcp_addresses.floating_ip_ranges
        elif self.addresses.type == AddressesKind.HOST:
            assert self.addresses.host_addresses is not None
            return self.addresses.host_addresses.floating_ip_ranges
        elif self.addresses.type == AddressesKind.STATIC:
            assert self.addresses.static_addresses is not None
            return self.addresses.static_addresses.floating_ip_ranges
        else:
            raise Exception('unreachable')

    def get_netmask(self) -> Optional[str]:
        if self.addresses.type == AddressesKind.DHCP:
            assert self.addresses.dhcp_addresses is not None
            return self.addresses.dhcp_addresses.netmask
        elif self.addresses.type == AddressesKind.HOST:
            assert self.addresses.host_addresses is not None
            return self.addresses.host_addresses.netmask
        elif self.addresses.type == AddressesKind.STATIC:
            assert self.addresses.static_addresses is not None
            return self.addresses.static_addresses.netmask
        else:
            raise Exception('unreachable')

    def get_ip_ranges(self) -> List[str]:
        if self.addresses.type == AddressesKind.STATIC:
            assert self.addresses.static_addresses is not None
            return self.addresses.static_addresses.ip_ranges
        else:
            raise Exception('unreachable')


@dataclass_json
@dataclass
class BondConfig:
    interface_name: str
    bonding_mode: Literal['ACTIVE_BACKUP', 'IEEE_8023AD']
    mtu: int
    networks: List[int]


@dataclass_json
@dataclass
class VlanConfig:
    vlan_id: int
    mtu: Optional[int]
    network_id: int
    secondary_network_id: Optional[int]


@dataclass_json
@dataclass
class ManagedInterfaces:
    frontend_bond_config: BondConfig
    frontend_vlans: List[VlanConfig]
    backend_bond_config: Optional[BondConfig] = None


@dataclass_json
@dataclass
class ClusterNetworkManagement(DataClassJsonMixin):
    managed_interfaces: Optional[ManagedInterfaces]
    frontend_networks: List[FrontendNetwork]

    def find_network(self, network_id: int) -> Optional[FrontendNetwork]:
        for network in self.frontend_networks:
            if network.id == network_id:
                return network

        return None

    def find_vlan(self, vlan_id: Optional[int]) -> Optional[VlanConfig]:
        if self.managed_interfaces is None:
            return None

        for vlan in self.managed_interfaces.frontend_vlans:
            if vlan.vlan_id == vlan_id:
                return vlan

        return None

    def networks_match_type(self, addresses_kind: AddressesKind) -> None:
        for network in self.frontend_networks:
            if network.addresses.type != addresses_kind:
                raise ConflictingNetworkTypesError(addresses_kind, network.addresses.type)

    def is_modification_allowed_and_network_type_changing(
        self, addresses_kind: AddressesKind
    ) -> bool:
        """
        This validates if we're changing the network type, if the modification is allowed
        """
        try:
            self.networks_match_type(addresses_kind)
            # Networks match, so the type is not changing
            return False
        except ConflictingNetworkTypesError as e:
            network_count = len(self.frontend_networks)
            if AddressesKind.HOST in (e.type_desired, e.type_present):
                # Types didn't match and one is HOST. We do not allow a change to or from HOST
                raise e
            elif network_count > 1:
                # Changing type, but there is more than 1 network, reduce to 1 network to switch
                # between DHCP & STATIC
                raise RequestResultsinNetworkTypeMix(e.type_desired, e.type_present, network_count)

        # The network type is changing
        return True

    def modify_network_addresses(self, network_id: int, **kwargs: Optional[object]) -> None:
        network = self.find_network(network_id)
        assert network is not None, f'Unable to locate network {network_id}'

        network.modify_addresses(**kwargs)

    def create_network(
        self,
        network_id: int,
        name: str,
        addresses_kind: AddressesKind,
        tenant_id: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        if self.find_network(network_id) is not None:
            raise NetworkAlreadyExistsError(network_id)

        self.networks_match_type(addresses_kind)

        if addresses_kind == AddressesKind.HOST:
            addresses = Addresses(
                type=addresses_kind,
                host_addresses=HostAddresses(
                    floating_ip_ranges=kwargs['floating_ip_ranges'], netmask=kwargs['netmask']
                ),
            )
        elif addresses_kind == AddressesKind.DHCP:
            addresses = Addresses(
                type=addresses_kind,
                dhcp_addresses=DhcpAddresses(
                    floating_ip_ranges=kwargs['floating_ip_ranges'], netmask=None
                ),
            )
        elif addresses_kind == AddressesKind.STATIC:
            addresses = Addresses(
                type=addresses_kind,
                static_addresses=StaticAddresses(
                    default_gateway=kwargs['default_gateway'],  # This must be specified
                    floating_ip_ranges=kwargs['floating_ip_ranges'],
                    ip_ranges=kwargs['ip_ranges'],  # This must be specified
                    netmask=kwargs['netmask'],  # This must be specified
                ),
            )
        else:
            raise Exception(f'Unsupported addresses_kind: {addresses_kind}')

        # In this block we handle where the network is added to the bond config or vlan config
        if addresses_kind in (AddressesKind.DHCP, AddressesKind.STATIC):
            assert isinstance(self.managed_interfaces, ManagedInterfaces)
            current_vlan_config = self.find_vlan(kwargs.get('vlan_id'))

            if kwargs.get('vlan_id') is not None and current_vlan_config is None:
                # New vlan and new network
                self.managed_interfaces.frontend_vlans.append(
                    VlanConfig(
                        vlan_id=kwargs['vlan_id'],
                        mtu=kwargs.get('vlan_mtu'),
                        network_id=network_id,
                        secondary_network_id=None,
                    )
                )
            elif kwargs.get('vlan_id') is not None and current_vlan_config is not None:
                # Existing vlan and new network
                if current_vlan_config.secondary_network_id is None:
                    current_vlan_config.secondary_network_id = network_id
                    current_vlan_config.mtu = kwargs.get('vlan_mtu') or current_vlan_config.mtu
                else:
                    raise VlanSecondaryNetworkAlreadyAssignedError(
                        current_vlan_config.vlan_id,
                        current_vlan_config.network_id,
                        current_vlan_config.secondary_network_id,
                    )
            else:
                # New network added to bond
                self.managed_interfaces.frontend_bond_config.networks.append(network_id)

        self.frontend_networks.append(
            FrontendNetwork(id=network_id, name=name, addresses=addresses, tenant_id=tenant_id)
        )

    def modify_network(
        self,
        network_id: int,
        name: Optional[str],
        addresses_kind: AddressesKind,
        tenant_id: Optional[int] = None,
        **kwargs: Optional[object],
    ) -> None:
        current_network = self.find_network(network_id)
        if current_network is None:
            raise NetworkNotFoundError(network_id)

        network_type_change = self.is_modification_allowed_and_network_type_changing(addresses_kind)
        if network_type_change:
            # If name is none, reuse current name of network
            if not name:
                name = self.frontend_networks[0].name

            assert self.managed_interfaces is not None
            # Delete the network
            self.remove_network(network_id, delete_orphaned_vlans=True)

            # In the modify call, this arg may not have been specified and is None, which is not a
            # valid input. Hence mutate here before calling create_network
            # default_gateway will not be provided if going from STATIC -> DHCP, hence .get()
            kwargs['default_gateway'] = kwargs.get('default_gateway') or ''
            kwargs['floating_ip_ranges'] = kwargs['floating_ip_ranges'] or []
            self.create_network(network_id, name, addresses_kind, tenant_id, **kwargs)
            return

        # We're not converting the network type, just modifying an existing network

        def _modify_frontend_network_except_address(network: FrontendNetwork) -> FrontendNetwork:
            network.name = name or network.name
            network.tenant_id = (
                None if kwargs['clear_tenant_id'] else tenant_id or network.tenant_id
            )
            return network

        if addresses_kind in [AddressesKind.HOST, AddressesKind.DHCP]:
            updated_frontend = _modify_frontend_network_except_address(current_network)
            address_related_kwargs = {
                k: v
                for k, v in kwargs.items()
                if k in ['floating_ip_ranges', 'netmask'] and v is not None
            }

            if address_related_kwargs:
                updated_frontend.modify_addresses(**address_related_kwargs)
        else:
            # Ensure it's a STATIC network, as that's the only other network we support
            assert addresses_kind == AddressesKind.STATIC
            updated_frontend = _modify_frontend_network_except_address(current_network)
            address_related_kwargs = {
                k: v
                for k, v in kwargs.items()
                if k in ['floating_ip_ranges', 'netmask', 'default_gateway', 'ip_ranges']
                and v is not None
            }
            if address_related_kwargs:
                updated_frontend.modify_addresses(**address_related_kwargs)

        for i, network in enumerate(self.frontend_networks):
            if network.id == network_id:
                self.frontend_networks[i] = updated_frontend

    def remove_network(self, network_id: int, delete_orphaned_vlans: bool = False) -> None:
        if self.find_network(network_id) is None:
            raise NetworkNotFoundError(network_id)

        self.frontend_networks = list(
            filter(lambda network: network.id != network_id, self.frontend_networks)
        )

        if self.managed_interfaces is None:
            return

        frontend_bond_config = self.managed_interfaces.frontend_bond_config
        backend_bond_config = self.managed_interfaces.backend_bond_config
        frontend_vlans = self.managed_interfaces.frontend_vlans

        # Remove any references to the deleted network
        frontend_bond_config.networks = list(
            filter(lambda id: id != network_id, frontend_bond_config.networks)
        )

        if backend_bond_config is not None:
            backend_bond_config.networks = list(
                filter(lambda id: id != network_id, backend_bond_config.networks)
            )

        vlan_ids_to_remove: Set[int] = set()
        for vlan in frontend_vlans:
            if vlan.network_id == network_id:
                if vlan.secondary_network_id is not None:
                    vlan.network_id = vlan.secondary_network_id
                    vlan.secondary_network_id = None
                elif delete_orphaned_vlans:
                    vlan_ids_to_remove.add(vlan.vlan_id)
                else:
                    raise OrphanedVlanError(vlan.vlan_id)
            elif vlan.secondary_network_id is not None and vlan.secondary_network_id == network_id:
                vlan.secondary_network_id = None

        self.managed_interfaces.frontend_vlans = list(
            filter(lambda vlan: vlan.vlan_id not in vlan_ids_to_remove, frontend_vlans)
        )

    def modify_bond_interface(
        self,
        *,
        mtu: Optional[int],
        bonding_mode: Optional[Literal['ACTIVE_BACKUP', 'IEEE_8023AD']],
        backend_bond: bool,
    ) -> None:
        if not isinstance(self.managed_interfaces, ManagedInterfaces):
            raise CannotModifyInterfaceInHostNetworks()

        def _modify_bond(
            bond: BondConfig,
            mtu: Optional[int],
            bonding_mode: Optional[Literal['ACTIVE_BACKUP', 'IEEE_8023AD']],
        ) -> None:
            bond.bonding_mode = bonding_mode or bond.bonding_mode
            bond.mtu = mtu or bond.mtu

        if backend_bond and self.managed_interfaces.backend_bond_config is not None:
            current_bond = self.managed_interfaces.backend_bond_config
            _modify_bond(current_bond, mtu, bonding_mode)
            self.managed_interfaces.backend_bond_config = current_bond
        elif not backend_bond:
            current_bond = self.managed_interfaces.frontend_bond_config
            _modify_bond(current_bond, mtu, bonding_mode)
            self.managed_interfaces.frontend_bond_config = current_bond
        else:
            raise BackendBondNotFoundError()

    def modify_vlan_interface(
        self, *, mtu: Optional[int], current_vlan_id: int, new_vlan_id: Optional[int]
    ) -> None:
        if not isinstance(self.managed_interfaces, ManagedInterfaces):
            raise CannotModifyInterfaceInHostNetworks()

        current_vlan = self.find_vlan(current_vlan_id)
        if current_vlan is None:
            raise VlanNotFoundError(current_vlan_id)

        if new_vlan_id is not None:
            if self.find_vlan(new_vlan_id) is not None:
                raise VlanAlreadyExistsError(current_vlan_id, new_vlan_id)

            # We didn't find the requested vlan, so we can change the current vlan id
            current_vlan.vlan_id = new_vlan_id

        current_vlan.mtu = mtu or current_vlan.mtu

        for i, vlan in enumerate(self.managed_interfaces.frontend_vlans):
            if vlan.vlan_id == current_vlan_id:
                self.managed_interfaces.frontend_vlans[i] = current_vlan


class NetworkV3:
    def __init__(self, client: request.SendRequestObject):
        self.client = client

    def get_config_raw(self) -> request.RestResponse:
        method = 'GET'
        uri = '/v3/network'

        return self.client.send_request(method, uri)

    def get_config(self) -> ClusterNetworkManagement:
        return ClusterNetworkManagement.from_dict(self.get_config_raw().data)

    def validate(
        self, config: Dict[str, Any], if_match: Optional[str] = None
    ) -> request.RestResponse:
        method = 'PUT'
        uri = '/v3/network/validate'

        return self.client.send_request(method, uri, body=config, if_match=if_match)

    def put_config(
        self, config: Dict[str, Any], if_match: Optional[str] = None
    ) -> request.RestResponse:
        method = 'PUT'
        uri = '/v3/network'

        return self.client.send_request(method, uri, body=config, if_match=if_match)

    def get_network_status(self, node_id: int) -> Dict[str, Any]:
        method = 'GET'
        uri = f'/v3/network/status/{node_id}'

        return self.client.send_request(method, uri).data

    def list_network_statuses(self) -> List[Any]:
        method = 'GET'
        uri = '/v3/network/status'

        return self.client.send_request(method, uri).data

    def get_cluster_frontend_interfaces(self) -> Dict[int, List[str]]:
        method = 'GET'
        uri = '/v3/network/frontend-interfaces'

        return self.client.send_request(method, uri).data

    def get_cluster_backend_interfaces(self) -> Dict[int, List[str]]:
        method = 'GET'
        uri = '/v3/network/backend-interfaces'

        return self.client.send_request(method, uri).data

    def modify_config(
        self, modify_cb: Callable[[ClusterNetworkManagement], None]
    ) -> request.RestResponse:
        response = self.get_config_raw()
        config = ClusterNetworkManagement.from_dict(response.data)
        modify_cb(config)
        return self.put_config(config.to_dict(), if_match=response.etag)
