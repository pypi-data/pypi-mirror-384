# Copyright (c) 2013 Qumulo, Inc.
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


from typing import Optional

import qumulo.lib.request as request

from qinternal.core.byte_units import GIBIBYTE
from qumulo.lib.auth import Credentials
from qumulo.lib.uri import UriBuilder
from qumulo.lib.util import tabulate


def fmt_unconfigured_nodes(unconfigured_nodes_response: request.RestResponse) -> str:
    """
    @param unconfigured_nodes_response The result of list_unconfigured_nodes
    @return a string containing a pretty table of the given nodes.
    """
    if not unconfigured_nodes_response.data.get('nodes'):
        return 'No unconfigured nodes found.'

    def disk_report(num_disks: int, partition_size: str) -> str:
        if num_disks == 0:
            return '---'
        size_in_gb = int(partition_size) // GIBIBYTE

        return f'({num_disks}, {size_in_gb}GB)'

    # Flatten the list of dicts (containing dicts) to a square array, with column headers.
    rows = []
    for node in unconfigured_nodes_response.data['nodes']:
        disk_info = node['disk_info']
        ssd_report = disk_report(disk_info['slot_counts']['ssds'], disk_info['ssd_partition_size'])
        hdd_report = disk_report(disk_info['slot_counts']['hdds'], disk_info['hdd_partition_size'])

        rows.append(
            (
                node['label'],
                node['model_number'],
                node['node_version']['revision_id'],
                node['node_version']['build_id'],
                node['uuid'],
                ssd_report,
                hdd_report,
            )
        )

    return tabulate(rows, headers=['LABEL', 'MODEL', 'VERSION', 'BUILD', 'UUID', 'SSD', 'HDD'])


@request.request
def list_unconfigured_nodes(
    conninfo: request.Connection,
    _credentials: Optional[Credentials],
    include_incompatibles: bool = False,
) -> request.RestResponse:
    method = 'GET'
    uri = UriBuilder(path='/v1/unconfigured/nodes/', rstrip_slash=False)

    if include_incompatibles:
        uri.add_query_param('include-incompatibles', 'true')

    return conninfo.send_request(method, str(uri))
