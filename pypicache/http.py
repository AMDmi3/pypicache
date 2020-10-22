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

import requests


class HTTPClient:
    _user_agent: str
    _timeout: int

    def __init__(self, user_agent: str, timeout: int) -> None:
        self._user_agent = user_agent
        self._timeout = timeout

    def get(self, url: str) -> requests.Response:
        headers = {'user-agent': self._user_agent}

        response = requests.get(url, headers=headers, timeout=self._timeout)
        response.raise_for_status()

        return response
