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


import argparse
import operator

from typing import Any, Dict, List

import qumulo.lib.auth
import qumulo.lib.opts
import qumulo.lib.util
import qumulo.rest.analytics as analytics

from qumulo.lib.opts import str_decode
from qumulo.rest_client import RestClient


def time_series_to_csv(series: List[Dict[str, Any]]) -> str:
    series = sorted(series, key=operator.itemgetter('id'))
    header = ','.join(['epoch'] + [sample['id'] for sample in series])
    table = [header]

    for i, epoch in enumerate(series[0]['times'][:-1]):
        row = [f'{epoch}'] + [f'{sample["values"][i]}' for sample in series]
        table.append(','.join(row))

    return '\n'.join(table)


class GetTimeSeriesCommand(qumulo.lib.opts.Subcommand):
    NAME = 'time_series_get'
    SYNOPSIS = 'Get specified time series data.'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            '-b',
            '--begin-time',
            default=0,
            help='Begin time for time series intervals, in epoch seconds',
        )
        parser.add_argument(
            '--csv',
            action='store_true',
            required=False,
            help='Format output as Comma Separated Values',
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        series = analytics.time_series_get(
            rest_client.conninfo, rest_client.credentials, args.begin_time
        )
        if args.csv:
            print(time_series_to_csv(series.data))
        else:
            print(series)


class GetCurrentActivityCommand(qumulo.lib.opts.Subcommand):
    NAME = 'current_activity_get'
    SYNOPSIS = 'Get the current sampled IOP and throughput rates'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            '-t',
            '--type',
            type=str_decode,
            default=None,
            choices=[
                'file-iops-read',
                'file-iops-write',
                'metadata-iops-read',
                'metadata-iops-write',
                'file-throughput-read',
                'file-throughput-write',
            ],
            help='The specific type of throughput to get',
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        print(
            analytics.current_activity_get(rest_client.conninfo, rest_client.credentials, args.type)
        )


class GetCapacityHistoryCommand(qumulo.lib.opts.Subcommand):
    NAME = 'capacity_history_get'
    SYNOPSIS = 'Get capacity history data.'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            '--begin-time',
            type=int,
            required=True,
            help='Lower bound on history returned, in epoch seconds.',
        )
        parser.add_argument(
            '--end-time',
            type=int,
            required=False,
            help=(
                'Upper bound on history returned, in epoch seconds. '
                'Defaults to the most recent period for which data is '
                'available.'
            ),
        )
        parser.add_argument(
            '--interval',
            type=str_decode,
            default='hourly',
            choices=['hourly', 'daily', 'weekly'],
            help='The interval at which to sample',
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        print(
            analytics.capacity_history_get(
                rest_client.conninfo,
                rest_client.credentials,
                args.interval,
                args.begin_time,
                args.end_time,
            )
        )


class GetCapacityHistoryFilesCommand(qumulo.lib.opts.Subcommand):
    NAME = 'capacity_history_files_get'
    SYNOPSIS = 'Get historical largest file data.'

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            '--timestamp',
            type=int,
            required=True,
            help='Time period to retrieve, in epoch seconds.',
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        print(
            analytics.capacity_history_files_get(
                rest_client.conninfo, rest_client.credentials, args.timestamp
            )
        )
