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


import argparse
import os
import sys

import qumulo.lib.opts

from qumulo.rest_client import RestClient


class RawCommand(qumulo.lib.opts.Subcommand):
    NAME = 'raw'
    SYNOPSIS = (
        'Issue an HTTP request to a Qumulo REST endpoint. Content '
        'for modifying requests (i.e. PATCH, POST, and PUT) can be '
        'provided on stdin.  Output is provided on stdout.'
    )

    @staticmethod
    def options(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            'method',
            choices=['DELETE', 'GET', 'PATCH', 'POST', 'PUT'],
            help='HTTP method. PATCH, POST, and PUT accept input on stdin',
        )
        parser.add_argument('url', help='REST endpoint (e.g. /v1/ad/join)')
        parser.add_argument(
            '--content-type',
            choices=['application/json', 'application/octet-stream'],
            default='application/json',
            help=(
                'Content MIME type for sending data with PATCH, POST, and PUT. '
                'Use application/octet-stream for binary input. (Default: application/json)'
            ),
        )

    @staticmethod
    def main(rest_client: RestClient, args: argparse.Namespace) -> None:
        # N.B. Use sys.std(in|out).buffer for binary IO; sys.std(in|out) are text-based.
        response_file = sys.stdout.buffer

        if args.method in ('PATCH', 'POST', 'PUT'):
            if sys.stdin.isatty():
                EOF = 'D' if os.name == 'posix' else 'Z'
                print(f'Waiting for stdin. Send CTRL-{EOF} to continue.', file=sys.stderr)

            rest_client.request(
                args.method,
                args.url,
                body_file=sys.stdin.buffer,
                response_file=response_file,
                request_content_type=args.content_type,
                chunked=True,
            )
        else:
            rest_client.request(args.method, args.url, response_file=response_file)

        response_file.write(b'\n')
