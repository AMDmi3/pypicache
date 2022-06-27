# Copyright (C) 2020,2022 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import json
import logging
import time
from datetime import timedelta

import requests

from pypicache import __version__
from pypicache.api_client import PyPIClient
from pypicache.cleanup import prepare_project_data
from pypicache.database import Database
from pypicache.output import generate_output


class Worker:
    _args: argparse.Namespace

    _db: Database
    _pypi: PyPIClient

    def __init__(self, args: argparse.Namespace) -> None:
        ua = f'pypicache/{__version__}'
        if args.frontend_url:
            ua += f' (+{args.frontend_url}'

        self._args = args
        self._db = Database(dsn=args.dsn)
        self._pypi = PyPIClient(user_agent=ua, api_url=args.pypi_url, timeout=args.timeout)

        self._db.init()

    def _update_single_project(self, name: str) -> None:
        try:
            etag = self._db.get_etag(name)

            res = self._pypi.get_project(name, etag)
            self._db.update_statistics(num_requests=1)

            # redirects are not expected to happen after https://github.com/pypa/warehouse/commit/f7f48cb7fd58e08c1f8beba3846569e074e0b297
            assert not res.history

            if res.status_code == 404:
                if self._db.remove_project(name):
                    self._db.update_statistics(num_removed=1)
                    logging.info(f'  {name}: not found, removed')
                else:
                    logging.info(f'  {name}: not found')
            elif res.status_code == 304:
                logging.info(f'  {name}: not modified')
            elif res.status_code == 200:
                if len(res.text) > 1024 * 1024 * 5:
                    self._db.update_statistics(num_too_big=1)
                    logging.info(f'  {name}: response too big ({len(res.text)} bytes), refusing to process')
                    return

                data = json.loads(res.text)

                real_name = data['info']['name']

                updated = self._db.update_project(real_name, prepare_project_data(data), len(res.text), res.headers.get('etag'))

                if real_name != name:
                    if self._db.remove_project(name):
                        self._db.update_statistics(num_removed=1)
                        logging.info(f'  {name}: actual name is {real_name}, project under old name removed')
                    else:
                        logging.info(f'  {name}: actual name is {real_name}')

                if updated and etag is None:
                    logging.info(f'  {real_name}: added')
                    self._db.update_statistics(num_added=1)
                elif updated:
                    logging.info(f'  {real_name}: updated')
                    self._db.update_statistics(num_changed=1)
                else:
                    logging.info(f'  {real_name}: not updated')
            else:
                logging.info(f'  {name} failed: bad HTTP code {res.status_code}, readding to queue')
                if self._args.retry:
                    self._db.add_queue(name, timedelta(seconds=self._args.retry))

        except requests.Timeout:
            logging.info(f'  {name}: failed: timeout, readding to queue')
            if self._args.retry:
                self._db.add_queue(name, timedelta(seconds=self._args.retry))

    def _process_changes(self) -> None:
        names, last_update = self._pypi.get_changes(self._db.get_last_update() - self._args.feed_overlap)

        if names:
            logging.info(f'updating {len(names)} project(s) from feed')

            for name in names:
                self._update_single_project(name)
                if self._args.recheck:
                    self._db.add_queue(name, timedelta(seconds=self._args.recheck))

            self._db.set_last_update(last_update)

    def _process_queue(self) -> None:
        if queue := self._db.get_queue(1000):
            count = len(set(name for _, name in queue))

            logging.info(f'updating {count} project(s) from queue')

            processed = set()

            for id_, name in queue:
                if name not in processed:
                    self._update_single_project(name)
                    processed.add(name)
                self._db.remove_queue(id_)

    def _generate_output(self) -> None:
        logging.info('generating output')

        start = time.time()
        generate_output(
            self._args.html_path,
            self._args.output_path,
            self._args.dump_file_name,
            self._db.iter_projects(),
            self._args.dump_compression_level
        )
        end = time.time()

        logging.info(f'output generated in {end-start:.2f} seconds')

    def run(self) -> None:
        last_update = 0.0
        last_output = 0.0

        while True:
            logging.info('iteration started')

            now = time.time()

            if now - last_update >= self._args.update_interval:
                self._process_changes()
                self._process_queue()
                self._db.commit()
                last_update = now

            now = time.time()

            if self._args.output_path and now - last_output >= self._args.output_interval:
                self._generate_output()
                self._db.commit()
                last_output = now

            if self._args.once_only:
                logging.info('iteration done')
                return

            now = time.time()

            wait_times = [last_update + self._args.update_interval - now]

            if self._args.output_path:
                wait_times.append(last_output + self._args.output_interval - now)

            wait_time = min(wait_times)

            if wait_time > 0:
                logging.info(
                    f'sleeping for {wait_time:.1f} second(s) before next iteration'
                )
                time.sleep(wait_time)
