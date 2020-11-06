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

import contextlib
import os
from typing import Iterable


def generate_dump(item_iter: Iterable[str], path: str, compression_level: int = 5) -> int:
    tmppath = path + '.tmp'
    success = False

    def remove_temp_file() -> None:
        if not success and os.path.exists(tmppath):
            os.remove(tmppath)

    num_records = 0

    with contextlib.ExitStack() as stack:
        stack.callback(remove_temp_file)

        outfd = stack.enter_context(open(tmppath, 'wb'))

        if path.endswith('.json'):
            stack.callback(os.fsync, outfd.fileno())
        elif path.endswith('.zst'):
            import zstandard
            cctx = zstandard.ZstdCompressor(level=compression_level)
            outfd = stack.enter_context(cctx.stream_writer(outfd))
        else:
            raise RuntimeError(f'cannot guess dump file format {path} (use .json or .zst extension)')

        outfd.write(b'[\n')

        first = True

        for item in item_iter:
            if first:
                first = False
            else:
                outfd.write(b',\n')

            outfd.write(item.encode('utf-8'))
            num_records += 1

        outfd.write(b']\n')

        outfd.flush()

        success = True

    os.replace(tmppath, path)

    return num_records
