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

from dataclasses import dataclass
from typing import Dict, List, Optional

from dataclasses_json import DataClassJsonMixin

import qumulo.lib.request as request

DEFAULT_PORTAL_PORT_NUMBER = 3713


@dataclass
class HubPortal(DataClassJsonMixin):
    id: int
    state: str
    status: str
    root: str
    root_path: Optional[str]
    spoke_cluster_uuid: str
    spoke_cluster_name: str
    spoke_address: Optional[str]
    spoke_port: Optional[int]
    spoke_type: str


@dataclass
class SpokePortal(DataClassJsonMixin):
    id: int
    state: str
    status: str
    spoke_root: str
    spoke_root_path: str
    spoke_type: str
    hub_root: Optional[str]
    hub_cluster_uuid: Optional[str]
    hub_address: Optional[str]
    hub_port: Optional[int]
    hub_id: Optional[int]


@dataclass
class EvictionResult(DataClassJsonMixin):
    evicted_blocks: int


@dataclass
class EvictionSettings(DataClassJsonMixin):
    # Fraction of free total cluster capacity that the system will try to maintain by evicting
    # cached spoke portal data, in the range [0.0, 1.0].
    # 0 means no eviction, 1 means always try to evict.
    free_threshold: float


@dataclass
class PortalFileSystemInfo(DataClassJsonMixin):
    uuid: Optional[str]
    usage_bytes: int


@dataclass
class PortalHost(DataClassJsonMixin):
    address: str
    port: int


@dataclass
class MultiRootHubPortal(DataClassJsonMixin):
    id: int
    type: str
    state: str
    status: str
    spoke_hosts: List[PortalHost]
    spoke_cluster_uuid: str
    spoke_cluster_name: str
    pending_roots: List[str]
    authorized_roots: List[str]


@dataclass
class SpokeRootPair(DataClassJsonMixin):
    local_root: str
    remote_root: str
    authorized: bool


@dataclass
class MultiRootSpokePortal(DataClassJsonMixin):
    id: int
    type: str
    state: str
    status: str
    hub_hosts: List[PortalHost]
    hub_id: int
    hub_cluster_uuid: str
    roots: List[SpokeRootPair]


class Portal:
    def __init__(self, client: request.SendRequestObject):
        self.client = client

    def create_portal(self, spoke_root: str, is_writable_spoke: bool = False) -> int:
        method = 'POST'
        uri = '/v1/portal/spokes/'

        body: Dict[str, object] = {'spoke_root': spoke_root, 'is_writable_spoke': is_writable_spoke}
        return int(self.client.send_request(method, uri, body=body).data)

    def propose_hub_portal(
        self, spoke_id: int, hub_address: str, hub_port: int, hub_root: str
    ) -> SpokePortal:
        method = 'POST'
        uri = f'/v1/portal/spokes/{spoke_id}/propose'

        body: Dict[str, object] = {
            'hub_root': hub_root,
            'hub_address': hub_address,
            'hub_port': hub_port,
        }

        response = self.client.send_request(method, uri, body=body)
        return self._decode_spoke_portal(response.data)

    def authorize_hub_portal(
        self, portal_id: int, spoke_address: str, spoke_port: int
    ) -> HubPortal:
        method = 'POST'
        uri = f'/v1/portal/hubs/{portal_id}/authorize'
        body: Dict[str, object] = {'spoke_address': spoke_address, 'spoke_port': spoke_port}

        response = self.client.send_request(method, uri, body=body)
        return self._decode_hub_portal(response.data)

    def get_hub_portal(self, portal_id: int) -> HubPortal:
        method = 'GET'
        uri = f'/v1/portal/hubs/{portal_id}'

        response = self.client.send_request(method, uri)
        return self._decode_hub_portal(response.data)

    def get_spoke_portal(self, portal_id: int) -> SpokePortal:
        method = 'GET'
        uri = f'/v1/portal/spokes/{portal_id}'
        response = self.client.send_request(method, uri)
        return self._decode_spoke_portal(response.data)

    def modify_hub_portal(self, portal_id: int, spoke_address: str, spoke_port: int) -> HubPortal:
        method = 'PATCH'
        uri = f'/v1/portal/hubs/{portal_id}'
        body: Dict[str, object] = {'spoke_address': spoke_address, 'spoke_port': spoke_port}

        response = self.client.send_request(method, uri, body=body)
        return self._decode_hub_portal(response.data)

    def modify_spoke_portal(self, portal_id: int, hub_address: str, hub_port: int) -> SpokePortal:
        method = 'PATCH'
        uri = f'/v1/portal/spokes/{portal_id}'
        body: Dict[str, object] = {'hub_address': hub_address, 'hub_port': hub_port}
        response = self.client.send_request(method, uri, body=body)
        return self._decode_spoke_portal(response.data)

    def delete_hub_portal(self, portal_id: int, force: bool = False) -> None:
        method = 'DELETE'
        query = '?force=true' if force else ''
        uri = f'/v1/portal/hubs/{portal_id}{query}'
        self.client.send_request(method, uri)

    def delete_spoke_portal(self, portal_id: int, force: bool = False) -> None:
        method = 'DELETE'
        query = '?force=true' if force else ''
        uri = f'/v1/portal/spokes/{portal_id}{query}'
        self.client.send_request(method, uri)

    def list_hub_portals(self) -> List[HubPortal]:
        method = 'GET'
        uri = '/v1/portal/hubs/'

        responses = self.client.send_request(method, uri).data['entries']
        results: List[HubPortal] = []

        for response in responses:
            results.append(self._decode_hub_portal(response))

        return results

    def list_spoke_portals(self) -> List[SpokePortal]:
        method = 'GET'
        uri = '/v1/portal/spokes/'

        responses = self.client.send_request(method, uri).data['entries']
        results: List[SpokePortal] = []

        for response in responses:
            results.append(self._decode_spoke_portal(response))

        return results

    def get_eviction_settings(self) -> request.ResponseWithEtag[EvictionSettings]:
        response = self.client.send_request('GET', '/v1/portal/spokes/eviction-settings')
        assert response.etag is not None
        return request.ResponseWithEtag(
            EvictionSettings.schema().load(response.data), response.etag
        )

    def set_eviction_settings(
        self, config: EvictionSettings, etag: Optional[str] = None
    ) -> request.ResponseWithEtag[EvictionSettings]:
        response = self.client.send_request(
            'PUT', '/v1/portal/spokes/eviction-settings', body=config.to_dict(), if_match=etag
        )
        assert response.etag is not None
        return request.ResponseWithEtag(
            EvictionSettings.schema().load(response.data), response.etag
        )

    def list_file_systems(self) -> List[PortalFileSystemInfo]:
        response = self.client.send_request('GET', '/v1/portal/file-systems/')
        return [PortalFileSystemInfo.from_dict(fs, infer_missing=True) for fs in response.data]

    def get_file_system(self, uuid: str) -> PortalFileSystemInfo:
        response = self.client.send_request('GET', f'/v1/portal/file-systems/{uuid}')
        return PortalFileSystemInfo.from_dict(response.data, infer_missing=True)

    @staticmethod
    def _decode_spoke_portal(portal: Dict[str, object]) -> SpokePortal:
        base: Dict[str, object] = {'status': 'DEGRADED'}
        base.update(portal)
        return SpokePortal.from_dict(base, infer_missing=True)

    @staticmethod
    def _decode_hub_portal(portal: Dict[str, object]) -> HubPortal:
        base: Dict[str, object] = {'status': 'DEGRADED'}
        base.update(portal)
        return HubPortal.from_dict(base, infer_missing=True)

    def v2_create_portal(
        self, portal_type: str, hub_hosts: List[PortalHost]
    ) -> MultiRootSpokePortal:
        method = 'POST'
        uri = '/v2/portal/spokes/'
        body = {'type': portal_type, 'hub_hosts': [host.to_dict() for host in hub_hosts]}

        response = self.client.send_request(method, uri, body=body)
        return MultiRootSpokePortal.schema().load(response.data)

    def v2_accept_hub_portal(
        self, hub_id: int, spoke_hosts: List[PortalHost], authorized_roots: List[str] = []
    ) -> MultiRootHubPortal:
        method = 'POST'
        uri = f'/v2/portal/hubs/{hub_id}/accept'
        body = {
            'spoke_hosts': [host.to_dict() for host in spoke_hosts],
            'authorized_roots': authorized_roots,
        }

        response = self.client.send_request(method, uri, body=body)
        return MultiRootHubPortal.schema().load(response.data)

    def v2_get_hub_portal(self, hub_id: int) -> MultiRootHubPortal:
        method = 'GET'
        uri = f'/v2/portal/hubs/{hub_id}'

        response = self.client.send_request(method, uri)
        return MultiRootHubPortal.schema().load(response.data)

    def v2_list_hub_portals(self) -> List[MultiRootHubPortal]:
        method = 'GET'
        uri = '/v2/portal/hubs/'

        response = self.client.send_request(method, uri)
        return [MultiRootHubPortal.schema().load(portal) for portal in response.data['entries']]

    def v2_delete_hub_portal(
        self, hub_id: int, force: bool = False
    ) -> Optional[MultiRootHubPortal]:
        method = 'DELETE'
        query = '?force=true' if force else ''
        uri = f'/v2/portal/hubs/{hub_id}{query}'

        response = self.client.send_request(method, uri)
        if response.data:
            return MultiRootHubPortal.schema().load(response.data)
        return None

    def v2_modify_hub_portal_host(
        self, hub_id: int, spoke_hosts: List[PortalHost]
    ) -> MultiRootHubPortal:
        method = 'PATCH'
        uri = f'/v2/portal/hubs/{hub_id}'
        body = {'spoke_hosts': [host.to_dict() for host in spoke_hosts]}

        response = self.client.send_request(method, uri, body=body)
        return MultiRootHubPortal.schema().load(response.data)

    def v2_authorize_hub_portal_root(self, hub_id: int, hub_root: str) -> MultiRootHubPortal:
        method = 'POST'
        uri = f'/v2/portal/hubs/{hub_id}/roots/{hub_root}'

        response = self.client.send_request(method, uri)
        return MultiRootHubPortal.schema().load(response.data)

    def v2_deny_hub_portal_root(self, hub_id: int, hub_root: str) -> MultiRootHubPortal:
        method = 'DELETE'
        uri = f'/v2/portal/hubs/{hub_id}/roots/{hub_root}'

        response = self.client.send_request(method, uri)
        return MultiRootHubPortal.schema().load(response.data)

    def v2_get_spoke_portal(self, spoke_id: int) -> MultiRootSpokePortal:
        method = 'GET'
        uri = f'/v2/portal/spokes/{spoke_id}'

        response = self.client.send_request(method, uri)
        return MultiRootSpokePortal.schema().load(response.data)

    def v2_list_spoke_portals(self) -> List[MultiRootSpokePortal]:
        method = 'GET'
        uri = '/v2/portal/spokes/'

        response = self.client.send_request(method, uri)
        return [MultiRootSpokePortal.schema().load(portal) for portal in response.data['entries']]

    def v2_delete_spoke_portal(
        self, spoke_id: int, force: bool = False
    ) -> Optional[MultiRootSpokePortal]:
        method = 'DELETE'
        query = '?force=true' if force else ''
        uri = f'/v2/portal/spokes/{spoke_id}{query}'

        response = self.client.send_request(method, uri)
        if response.data:
            return MultiRootSpokePortal.schema().load(response.data)
        return None

    def v2_modify_spoke_portal_host(
        self, spoke_id: int, hub_hosts: List[PortalHost]
    ) -> MultiRootSpokePortal:
        method = 'PATCH'
        uri = f'/v2/portal/spokes/{spoke_id}'
        body = {'hub_hosts': [host.to_dict() for host in hub_hosts]}

        response = self.client.send_request(method, uri, body=body)
        return MultiRootSpokePortal.schema().load(response.data)

    def v2_propose_spoke_portal_root(
        self, spoke_id: int, spoke_root_path: str, hub_root_path: str
    ) -> MultiRootSpokePortal:
        method = 'POST'
        uri = f'/v2/portal/spokes/{spoke_id}/roots/'
        body = {'spoke_root_path': spoke_root_path, 'hub_root_path': hub_root_path}

        response = self.client.send_request(method, uri, body=body)
        return MultiRootSpokePortal.schema().load(response.data)

    def v2_delete_spoke_portal_root(self, spoke_id: int, spoke_root: str) -> MultiRootSpokePortal:
        method = 'DELETE'
        uri = f'/v2/portal/spokes/{spoke_id}/roots/{spoke_root}'

        response = self.client.send_request(method, uri)
        return MultiRootSpokePortal.schema().load(response.data)
