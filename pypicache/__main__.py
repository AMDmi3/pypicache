# Copyright (C) 2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
#
# This file is part of pypicache
#
# pypicache is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pypicache is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pypicache.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import logging
import sys

from pypicache.worker import Worker


def main() -> int:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('--dsn', default='dbname=pypicache user=pypicache password=pypicache', help='database connection params')
    parser.add_argument('--debug', action='store_true', help='enable debug logging')
    parser.add_argument('--once-only', action='store_true', help="do just a single update pass, don't loop")

    grp = parser.add_argument_group('Update settings')
    grp.add_argument('--update-interval', type=int, default=60, help='interval between PyPi feed updates')
    grp.add_argument('--feed-overlap', type=int, default=0, help='overlap of feed update timestan')
    grp.add_argument('--recheck', type=int, default=0, help='interval in seconds to issue additional request in')
    grp.add_argument('--retry', type=int, default=0, help='interval in seconds to retry failed requests')
    grp.add_argument('--timeout', type=int, default=10, help='HTTP timeout')
    grp.add_argument('--pypi-url', type=str, default='https://pypi.org/pypi', help='PyPi host to fetch data from')
    grp.add_argument('--frontend-url', type=str, help='frontend URL to use in user-agent header')
    grp.add_argument('--queue-batch-size', type=int, default=1000, help='number of packages to process from queue in one iteration')

    grp = parser.add_argument_group('Output settings')
    grp.add_argument('--output-interval', type=int, default=600, help='interval between dump generation')
    grp.add_argument('--output-path', type=str, help='path to output directory')
    grp.add_argument('--html-path', type=str, default='./html', help='path to directory with html template')
    grp.add_argument('--dump-file-name', type=str, default='pypicache.json.zst', help='dump file name (extensions controls used compression)')
    grp.add_argument('--dump-compression-level', type=int, default=5, help='dump compression level, if compression is used')

    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG if args.debug else logging.INFO,
    )

    Worker(args).run()

    return 0


if __name__ == '__main__':
    sys.exit(main())
