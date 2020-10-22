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
import time
import sys
from typing import Any

import psycopg2

from pypicache import __version__
from pypicache.dump import dump_from_cursor
from pypicache.feed import FeedParser
from pypicache.http import HTTPClient


class Worker:
    _args: argparse.Namespace

    _db: Any

    _feed_parser: FeedParser
    _http_client: HTTPClient

    def __init__(self, args: argparse.Namespace) -> None:
        self._args = args
        self._db = psycopg2.connect(args.dsn, application_name='pypicache')
        self._feed_parser = FeedParser()

        ua = f'pypicache/{__version__}'
        if args.frontend_url:
            ua += f' (+{args.frontend_url}'

        self._http_client = HTTPClient(ua, args.timeout)

    def _init_db(self) -> None:
        with self._db.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    name text NOT NULL PRIMARY KEY,

                    added timestamptz NOT NULL DEFAULT now(),
                    updated timestamptz NOT NULL DEFAULT now(),

                    author text,
                    author_email text,
                    summary text,
                    homepage text,
                    version text,
                    downloads text[]
                )
                """
            )

    def _update_single_project(self, name: str) -> None:
        logging.info(f'updating project {name}')

        content = self._http_client.get(f'{self._args.pypi_url}/pypi/{name}/json').json()

        info = content['info']

        version = info['version']
        releases = content['releases'][version]
        downloads = [release['url'] for release in releases]

        with self._db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO projects (
                    name,
                    updated,
                    author,
                    author_email,
                    summary,
                    homepage,
                    version,
                    downloads
                )
                VALUES (
                    %(name)s,
                    now(),
                    %(author)s,
                    %(author_email)s,
                    %(summary)s,
                    %(homepage)s,
                    %(version)s,
                    %(downloads)s
                )
                ON CONFLICT (name)
                DO UPDATE SET
                    updated = now(),
                    author = EXCLUDED.author,
                    author_email = EXCLUDED.author_email,
                    summary = EXCLUDED.summary,
                    homepage = EXCLUDED.homepage,
                    version = EXCLUDED.version,
                    downloads = EXCLUDED.downloads
                ;
                """,
                {
                    'name': name,
                    'author': info['author'],
                    'author_email': info['author_email'],
                    'summary': info['summary'],
                    'homepage': info['home_page'],
                    'version': version,
                    'downloads': downloads,
                }
            )

    def _process_seed_file(self) -> None:
        if not self._args.seed_file_path:
            return

        logging.info('processing seed file')
        with open(self._args.seed_file_path) as fd:
            for line in fd:
                self._update_single_project(line.strip())
        logging.info('done processing seed file')

    def _process_feed(self) -> None:
        logging.info('processing feed')

        content = self._http_client.get(f'{self._args.pypi_url}/rss/updates.xml').text

        reliable, projects = self._feed_parser.parse_feed(content)

        if not reliable:
            logging.warning('first update from previous iteration was not encountered, some updates may have been lost')

        for project in projects:
            self._update_single_project(project)

        logging.info('done processing feed')

    def _generate_dump(self) -> None:
        logging.info('generating dump')

        with self._db.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    name,
                    author,
                    author_email,
                    summary,
                    homepage,
                    version,
                    downloads
                FROM projects
                """
            )

            dump_from_cursor(cursor, self._args.dump_path)

        logging.info('done generating dump')

    def run(self) -> None:
        self._init_db()

        self._process_seed_file()

        last_update = 0.0
        last_dump = 0.0

        while True:
            now = time.time()

            since_last_update = now - last_update
            since_last_dump = now - last_dump

            if since_last_update >= self._args.update_interval:
                try:
                    self._process_feed()
                    self._db.commit()
                except:
                    self._db.rollback()
                    raise

                last_update = now

            if since_last_dump >= self._args.dump_interval:
                self._generate_dump()

                last_dump = now

            if self._args.once_only:
                return

            wait_time = min(self._args.update_interval, self._args.dump_interval)
            logging.info(f'sleeping for {wait_time:.1f} second(s) before next iteration')
            time.sleep(wait_time)


def main() -> int:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--dsn', default='dbname=pypicache user=pypicache password=pypicache', help='database connection params')
    parser.add_argument('--debug', action='store_true', help='enable debug logging')
    parser.add_argument('--once-only', action='store_true', help="do just a single update pass, don't loop")

    parser.add_argument('--update-interval', type=float, default=10.0, help='inverval between PyPi feed updates')
    parser.add_argument('--dump-interval', type=float, default=3600.0, help='interval between dump generation')

    parser.add_argument('--dump-path', type=str, required=True, help='path to output dump file')
    parser.add_argument('--seed-file-path', type=str, help='path to file with project names to seed the database')

    parser.add_argument('--pypi-url', type=str, default='https://pypi.org', help='PyPi host to fetch data from')
    parser.add_argument('--frontend-url', type=str, help='frontend URL')

    parser.add_argument('--timeout', type=int, default=60, help='HTTP timeout')

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG if args.debug else logging.INFO)

    Worker(args).run()

    return 0


if __name__ == '__main__':
    sys.exit(main())
