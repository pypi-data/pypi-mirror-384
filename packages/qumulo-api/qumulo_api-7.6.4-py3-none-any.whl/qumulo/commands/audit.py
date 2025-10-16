# Copyright (c) 2019 Qumulo, Inc.
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


from argparse import ArgumentParser, Namespace

import qumulo.lib.opts
import qumulo.rest.audit as audit

from qumulo.lib.opts import str_decode
from qumulo.rest_client import RestClient

#                _
#  ___ _   _ ___| | ___   __ _
# / __| | | / __| |/ _ \ / _` |
# \__ \ |_| \__ \ | (_) | (_| |
# |___/\__, |___/_|\___/ \__, |
#      |___/             |___/
#  FIGLET: syslog
#


class GetAuditLogSyslogConfig(qumulo.lib.opts.Subcommand):
    NAME = 'audit_get_syslog_config'
    SYNOPSIS = 'Get audit syslog server configuration'

    @staticmethod
    def main(rest_client: RestClient, _args: Namespace) -> None:
        print(audit.get_syslog_config(rest_client.conninfo, rest_client.credentials))


class SetAuditLogSyslogConfig(qumulo.lib.opts.Subcommand):
    NAME = 'audit_set_syslog_config'
    SYNOPSIS = 'Change audit syslog server configuration'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        enabled_group = parser.add_mutually_exclusive_group(required=False)
        enabled_group.set_defaults(enabled=None)
        enabled_group.add_argument(
            '--enable', '-e', dest='enabled', action='store_true', help='Enable audit log.'
        )
        enabled_group.add_argument(
            '--disable', '-d', dest='enabled', action='store_false', help='Disable audit log.'
        )

        format_group = parser.add_mutually_exclusive_group(required=False)
        format_group.set_defaults(format_=None)
        format_group.add_argument(
            '--csv',
            action='store_const',
            const=audit.SyslogFormat.CSV,
            dest='format_',
            help='Output audit log as CSV.',
        )
        format_group.add_argument(
            '--json',
            action='store_const',
            const=audit.SyslogFormat.JSON,
            dest='format_',
            help='Output audit log as JSON.',
        )

        local_enabled_group = parser.add_mutually_exclusive_group(required=False)
        local_enabled_group.set_defaults(local_enabled=None)
        local_enabled_group.add_argument(
            '--local-enable',
            dest='local_enabled',
            action='store_true',
            help='Enable per-node local audit log.',
        )
        local_enabled_group.add_argument(
            '--local-disable',
            dest='local_enabled',
            action='store_false',
            help='Disable per-node local audit log.',
        )

        parser.add_argument(
            '--server-address',
            '-s',
            type=str_decode,
            help=(
                'The IP address, hostname, or fully qualified domain name of '
                'your remote syslog server.'
            ),
        )

        parser.add_argument(
            '--server-port',
            '-p',
            type=int,
            help='The port to connect to on your remote syslog server.',
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            audit.set_syslog_config(
                rest_client.conninfo,
                rest_client.credentials,
                enabled=args.enabled,
                format_=args.format_,
                local_enabled=args.local_enabled,
                server_address=args.server_address,
                server_port=args.server_port,
            )
        )


class GetAuditLogSyslogStatus(qumulo.lib.opts.Subcommand):
    NAME = 'audit_get_syslog_status'
    SYNOPSIS = 'Get audit syslog server status'

    @staticmethod
    def main(rest_client: RestClient, _args: Namespace) -> None:
        print(audit.get_syslog_status(rest_client.conninfo, rest_client.credentials))


#       _                 _               _       _
#   ___| | ___  _   _  __| |_      ____ _| |_ ___| |__
#  / __| |/ _ \| | | |/ _` \ \ /\ / / _` | __/ __| '_ \
# | (__| | (_) | |_| | (_| |\ V  V / (_| | || (__| | | |
#  \___|_|\___/ \__,_|\__,_| \_/\_/ \__,_|\__\___|_| |_|
#  FIGLET: cloudwatch
#


class GetAuditLogCloudwatchConfig(qumulo.lib.opts.Subcommand):
    NAME = 'audit_get_cloudwatch_config'
    SYNOPSIS = 'Get audit CloudWatch configuration'

    @staticmethod
    def main(rest_client: RestClient, _args: Namespace) -> None:
        print(audit.get_cloudwatch_config(rest_client.conninfo, rest_client.credentials))


class SetAuditLogCloudwatchConfig(qumulo.lib.opts.Subcommand):
    NAME = 'audit_set_cloudwatch_config'
    SYNOPSIS = 'Change audit CloudWatch configuration'

    @staticmethod
    def options(parser: ArgumentParser) -> None:
        enabled_group = parser.add_mutually_exclusive_group(required=False)
        enabled_group.set_defaults(enabled=None)
        enabled_group.add_argument(
            '--enable', '-e', dest='enabled', action='store_true', help='Enable audit log.'
        )
        enabled_group.add_argument(
            '--disable', '-d', dest='enabled', action='store_false', help='Disable audit log.'
        )

        parser.add_argument(
            '-l',
            '--log-group-name',
            type=str_decode,
            help='The group name in CloudWatch Logs to send logs to.',
        )
        parser.add_argument(
            '-r', '--region', type=str_decode, help='The AWS region to send logs to.'
        )

    @staticmethod
    def main(rest_client: RestClient, args: Namespace) -> None:
        print(
            audit.set_cloudwatch_config(
                rest_client.conninfo,
                rest_client.credentials,
                enabled=args.enabled,
                log_group_name=args.log_group_name,
                region=args.region,
            )
        )


class GetAuditLogCloudwatchStatus(qumulo.lib.opts.Subcommand):
    NAME = 'audit_get_cloudwatch_status'
    SYNOPSIS = 'Get audit CloudWatch status'

    @staticmethod
    def main(rest_client: RestClient, _args: Namespace) -> None:
        print(audit.get_cloudwatch_status(rest_client.conninfo, rest_client.credentials))
