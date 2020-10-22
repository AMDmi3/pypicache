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
import os
from typing import Any


def dump_from_cursor(cursor: Any, path: str) -> None:
    tmppath = path + '.tmp'

    with open(tmppath, 'w') as outfd:
        outfd.write('[\n')

        field_names = [desc.name for desc in cursor.description]

        first = True

        for item in cursor:
            if first:
                first = False
            else:
                outfd.write(',\n')

            json.dump(dict(zip(field_names, item)), outfd)

        outfd.write(']\n')

        outfd.flush()
        os.fsync(outfd.fileno())

    os.replace(tmppath, path)
