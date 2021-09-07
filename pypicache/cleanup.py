# Copyright (C) 2020-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Any

from libversion import version_compare


def prepare_project_data(data: Any) -> str:
    del data['info']['description']

    latest_version = data['info']['version']

    def should_drop_version(version: str) -> bool:
        # Preserve latest version
        if version == latest_version:
            return False

        # Preserve all versions above latest
        # These include prerelease versions and yanked versions
        if version_compare(version, latest_version) > 0:
            return False

        return True

    for version in filter(should_drop_version, list(data['releases'].keys())):
        del data['releases'][version]

    return json.dumps(data, separators=(',', ':'))
