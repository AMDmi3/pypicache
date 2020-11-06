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
from typing import Iterable, Optional, Set, Tuple, cast

import requests


class PyPIClient:
    _api_url: str
    _user_agent: Optional[str]
    _timeout: int
    _xmlrpc: xmlrpc.client.ServerProxy

    def __init__(self, user_agent: str, api_url: str = 'https://pypi.org/pypi', timeout: int = 60) -> None:
        self._api_url = api_url
        self._user_agent = user_agent
        self._timeout = timeout
        self._xmlrpc = xmlrpc.client.ServerProxy(api_url)  # XXX: user-agent

    def get_project(self, name: str, etag: Optional[str]) -> Optional[Tuple[str, str]]:
        headers = {}

        if self._user_agent:
            headers['user-agent'] = self._user_agent

        if etag:
            headers['if-none-match'] = etag

        url = f'{self._api_url}/{name}/json'

        response = requests.get(url, headers=headers, timeout=self._timeout)
        response.raise_for_status()

        if response.status_code == 304:
            return None

        return response.text, response.headers['etag']

    def get_changes(self, since: int) -> Tuple[Set[str], int]:
        changed_projects = set()
        last_update = 0

        for name, version, timestamp, action in cast(Iterable[Tuple[str, str, int, str]], self._xmlrpc.changelog(since)):
            changed_projects.add(name)
            last_update = max(last_update, timestamp)

        return changed_projects, last_update
