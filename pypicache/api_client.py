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

import xmlrpc.client
from typing import Iterable, cast

import requests


class PyPIClient:
    _api_url: str
    _user_agent: str | None
    _timeout: int
    _xmlrpc: xmlrpc.client.ServerProxy

    def __init__(self, user_agent: str, api_url: str = 'https://pypi.org/pypi', timeout: int = 60) -> None:
        self._api_url = api_url
        self._user_agent = user_agent
        self._timeout = timeout
        self._xmlrpc = xmlrpc.client.ServerProxy(api_url)  # XXX: user-agent

    def get_project(self, name: str, etag: str | None = None) -> requests.Response:
        headers = {}

        if self._user_agent:
            headers['user-agent'] = self._user_agent

        if etag:
            headers['if-none-match'] = etag

        url = f'{self._api_url}/{name}/json'

        return requests.get(url, headers=headers, timeout=self._timeout)

    def get_changes(self, since_serial: int) -> tuple[set[str], int]:
        changed_projects = set()

        current_serial = since_serial
        for name, version, timestamp, action, serial in cast(Iterable[tuple[str, str, int, str, int]], self._xmlrpc.changelog_since_serial(since_serial)):
            changed_projects.add(name)
            current_serial = max(current_serial, serial)

        return changed_projects, current_serial

    def get_all_packages(self) -> tuple[set[str], int]:
        projects = set()

        current_serial = 0
        for name, serial in cast(dict[str, int], self._xmlrpc.list_packages_with_serial()).items():
            projects.add(name)
            current_serial = max(current_serial, serial)

        return projects, current_serial
