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

from pypicache import __version__
from pypicache.api_client import PyPIClient
from pypicache.cleanup import cleanup_project
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

            if (res := self._pypi.get_project(name, etag)):
                data, etag = res
            else:
                logging.info(f'project {name} not modified')
                return

            self._db.update_project(name, cleanup_project(data), etag)
            logging.info(f'project {name} updated')

        except Exception as e:
            logging.info(f'project {name} update failed: {str(e)}')

    def _process_changes(self) -> None:
        names, last_update = self._pypi.get_changes(self._db.get_last_update())

        if names:
            logging.info(f'{len(names)} project(s) to update')

            for name in names:
                self._update_single_project(name)

            self._db.set_last_update(last_update)

    def _process_queue(self) -> None:
        first = True
        for name in self._db.iter_queue():
            if first:
                logging.info('updating projects from queue')
                first = False

            self._update_single_project(name)

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
        last_update = 0
        last_output = 0

        while True:
            logging.info('iteration started')

            now = int(time.time())

            since_last_update = now - last_update
            since_last_output = now - last_output

            if since_last_update >= self._args.update_interval:
                self._process_changes()
                self._process_queue()
                self._db.commit()

                last_update = now

            if since_last_output >= self._args.output_interval:
                self._generate_output()

                last_output = now

            if self._args.once_only:
                logging.info('iteration done')
                return

            wait_time = min(self._args.update_interval, self._args.output_interval)
            logging.info(
                f'sleeping for {wait_time:.1f} second(s) before next iteration'
            )
            time.sleep(wait_time)