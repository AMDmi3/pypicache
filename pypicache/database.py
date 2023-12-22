# Copyright (C) 2020-2021,2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from datetime import timedelta
from typing import Any, Iterable, cast

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

                    added timestamptz NOT NULL DEFAULT clock_timestamp(),
                    updated timestamptz NOT NULL DEFAULT clock_timestamp(),

                    etag text,

                    data_len integer,
                    orig_len integer
                );

                CREATE TABLE IF NOT EXISTS projects_data (
                    name text NOT NULL PRIMARY KEY REFERENCES projects ON DELETE CASCADE,
                    data text NOT NULL
                );

                CREATE TABLE IF NOT EXISTS queue (
                    id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    name text NOT NULL,
                    ready_time timestamptz
                );

                CREATE TABLE IF NOT EXISTS statistics (
                    key integer NOT NULL DEFAULT 0 PRIMARY KEY,
                    num_added integer NOT NULL DEFAULT 0,
                    num_changed integer NOT NULL DEFAULT 0,
                    num_removed integer NOT NULL DEFAULT 0,
                    num_too_big integer NOT NULL DEFAULT 0,
                    num_requests integer NOT NULL DEFAULT 0,
                    last_serial integer NULL
                );

                INSERT INTO statistics DEFAULT VALUES
                ON CONFLICT (key) DO NOTHING;
                """
            )

    def update_project(self, name: str, data: str, orig_len: int, etag: str | None) -> bool:
        with self._db.cursor() as cur:
            cur.execute(
                """
                WITH metadata_update AS (
                    INSERT INTO projects (
                        name,
                        updated,
                        etag,
                        data_len,
                        orig_len
                    )
                    VALUES (
                        %(name)s,
                        clock_timestamp(),
                        %(etag)s,
                        %(data_len)s,
                        %(orig_len)s
                    )
                    ON CONFLICT (name)
                    DO UPDATE SET
                        updated = clock_timestamp(),
                        etag = EXCLUDED.etag,
                        data_len = EXCLUDED.data_len,
                        orig_len = EXCLUDED.orig_len
                    WHERE
                        projects.etag IS DISTINCT FROM EXCLUDED.etag
                    RETURNING name
                ), data_update AS (
                    INSERT INTO projects_data (
                        name,
                        data
                    )
                    SELECT
                        name,
                        %(data)s
                    FROM metadata_update
                    ON CONFLICT (name)
                    DO UPDATE SET
                        data = EXCLUDED.data
                )
                SELECT 1 FROM metadata_update
                """,
                {
                    'name': name,
                    'data': data,
                    'etag': etag,
                    'data_len': len(data),
                    'orig_len': orig_len,
                }
            )

            row = cur.fetchone()

            return bool(row and row[0])

    def remove_project(self, name: str) -> bool:
        with self._db.cursor() as cur:
            cur.execute(
                """
                DELETE FROM projects WHERE name = %(name)s RETURNING 1
                """,
                {
                    'name': name
                }
            )

            row = cur.fetchone()

            return bool(row and row[0])

    def get_etag(self, name: str) -> str | None:
        with self._db.cursor() as cur:
            cur.execute('SELECT etag FROM projects WHERE name = %(name)s', {'name': name})

            row = cur.fetchone()

            return row[0] if row else None

    def iter_projects(self) -> Iterable[str]:
        with self._db.cursor('iter_projects') as cur:
            cur.execute('SELECT data FROM projects_data')

            yield from (row[0] for row in cur)

    def get_last_serial(self) -> int | None:
        with self._db.cursor() as cur:
            cur.execute('SELECT last_serial FROM statistics')

            return cast(int | None, next(cur)[0])

    def set_last_serial(self, last_serial: int) -> None:
        with self._db.cursor() as cur:
            cur.execute('UPDATE statistics SET last_serial = %(last_serial)s', {'last_serial': last_serial})

    def add_queue(self, name: str, postpone: timedelta | None = None) -> None:
        with self._db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO queue(
                    name,
                    ready_time
                )
                VALUES(
                    %(name)s,
                    clock_timestamp() + %(postpone)s
                )
                """,
                {
                    'name': name,
                    'postpone': postpone
                }
            )

    def remove_queue(self, id_: int) -> None:
        with self._db.cursor() as cur:
            cur.execute('DELETE FROM queue WHERE id = %(id)s', {'id': id_})

    def get_queue(self, limit: int) -> list[tuple[int, str]]:
        with self._db.cursor() as cur:
            cur.execute(
                """
                SELECT id, name FROM queue WHERE ready_time < clock_timestamp()
                UNION ALL
                SELECT id, name FROM queue WHERE ready_time IS NULL
                LIMIT %(limit)s
                """,
                {
                    'limit': limit
                }
            )

            return list(cur)

    def update_statistics(self, num_added: int = 0, num_changed: int = 0, num_removed: int = 0, num_too_big: int = 0, num_requests: int = 0) -> None:
        with self._db.cursor() as cur:
            cur.execute(
                """
                UPDATE statistics
                SET
                    num_added = num_added + %(num_added)s,
                    num_changed = num_changed + %(num_changed)s,
                    num_removed = num_removed + %(num_removed)s,
                    num_too_big = num_too_big + %(num_too_big)s,
                    num_requests = num_requests + %(num_requests)s
                """,
                {
                    'num_added': num_added,
                    'num_changed': num_changed,
                    'num_removed': num_removed,
                    'num_too_big': num_too_big,
                    'num_requests': num_requests,
                }
            )

    def commit(self) -> None:
        self._db.commit()
