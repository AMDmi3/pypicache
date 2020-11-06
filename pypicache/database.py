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

import time
from typing import Any, Iterable, Optional, cast

import psycopg2


class Database():
    _db: Any

    def __init__(self, dsn: str) -> None:
        self._db = psycopg2.connect(dsn, application_name='pypicache')

    def init(self) -> None:
        with self._db.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    name text NOT NULL PRIMARY KEY,

                    added timestamptz NOT NULL DEFAULT now(),
                    updated timestamptz NOT NULL DEFAULT now(),

                    data text not null,
                    etag text
                );

                CREATE TABLE IF NOT EXISTS queue (
                    name text NOT NULL PRIMARY KEY
                );

                CREATE TABLE IF NOT EXISTS last_update (
                    last_update integer NOT NULL
                );
                """
            )

        with self._db.cursor() as cur:
            cur.execute('SELECT max(last_update) FROM last_update')

            if not (last_update := next(cur)[0]):
                last_update = int(time.time())

            cur.execute('DELETE FROM last_update')
            cur.execute('INSERT INTO last_update VALUES(%(last_update)s)', {'last_update': last_update})

    def update_project(self, name: str, data: str, etag: str) -> None:
        with self._db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO projects (
                    name,
                    updated,
                    data,
                    etag
                )
                VALUES (
                    %(name)s,
                    now(),
                    %(data)s,
                    %(etag)s
                )
                ON CONFLICT (name)
                DO UPDATE SET
                    updated = now(),
                    data = EXCLUDED.data,
                    etag = EXCLUDED.etag
                WHERE
                    projects.etag IS DISTINCT FROM EXCLUDED.etag
                ;
                """,
                {
                    'name': name,
                    'data': data,
                    'etag': etag
                }
            )

    def get_etag(self, name: str) -> Optional[str]:
        with self._db.cursor() as cur:
            cur.execute('SELECT etag FROM projects WHERE name = %(name)s', {'name': name})

            row = cur.fetchone()

            return row[0] if row else None

    def iter_projects(self) -> Iterable[str]:
        with self._db.cursor() as cur:
            cur.execute('SELECT data FROM projects')

            yield from (row[0] for row in cur)

    def get_last_update(self) -> int:
        with self._db.cursor() as cur:
            cur.execute('SELECT last_update FROM last_update')

            return cast(int, next(cur)[0])

    def set_last_update(self, last_update: int) -> None:
        with self._db.cursor() as cur:
            cur.execute('UPDATE last_update SET last_update = %(last_update)s', {'last_update': last_update})

    def iter_queue(self) -> Iterable[str]:
        with self._db.cursor() as cur:
            cur.execute('DELETE FROM queue RETURNING name')

            yield from (row[0] for row in cur)

    def commit(self) -> None:
        self._db.commit()
