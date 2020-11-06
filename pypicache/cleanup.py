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

import json


def cleanup_project(data: str) -> str:
    parsed = json.loads(data)

    del parsed['info']['description']

    versions_to_delete = [
        version
        for version in parsed['releases'].keys()
        if version != parsed['info']['version']
    ]

    for version in versions_to_delete:
        del parsed['releases'][version]

    return json.dumps(parsed)
