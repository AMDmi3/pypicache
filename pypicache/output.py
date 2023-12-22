# Copyright (C) 2020,2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import datetime
import os
import re
from typing import Any, BinaryIO, Iterable


def generate_output(src_path: str, dst_path: str, dump_file_name: str, item_iter: Iterable[str], compression_level: int = 5) -> None:
    if not os.path.exists(dst_path):
        os.mkdir(dst_path)

    html_inpath = os.path.join(src_path, 'index.html')
    css_inpath = os.path.join(src_path, 'style.css')

    dump_outpath = os.path.join(dst_path, dump_file_name)
    html_outpath = os.path.join(dst_path, 'index.html')
    css_outpath = os.path.join(dst_path, 'style.css')

    num_packages = _generate_dump(dump_outpath, item_iter, compression_level)
    dump_size = os.stat(dump_outpath).st_size

    template_vars = {
        'FILENAME': dump_file_name,
        'SIZE': f'{dump_size / 1024 / 1024:.2f} MiB',
        'DATE': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
        'PACKAGES': num_packages,
    }

    _copy_template(html_inpath, html_outpath, template_vars)
    _copy_template(css_inpath, css_outpath)


def _copy_template(src_path: str, dst_path: str, template_vars: dict[str, Any] = {}) -> None:
    def template_subst(match: re.Match[str]) -> str:
        key = match.group(0).strip('%')
        if key in template_vars:
            return str(template_vars[key])
        return match.group(0)

    tmppath = dst_path + '.tmp'

    with open(src_path) as infd:
        with open(tmppath, 'w') as outfd:
            for line in infd:
                outfd.write(re.sub('%[A-Z]+%', template_subst, line))

            outfd.flush()
            os.fsync(outfd.fileno())

    os.replace(tmppath, dst_path)


def _generate_dump(path: str, item_iter: Iterable[str], compression_level: int = 5) -> int:
    tmppath = path + '.tmp'
    success = False

    def remove_temp_file() -> None:
        if not success and os.path.exists(tmppath):
            os.remove(tmppath)

    num_records = 0

    with contextlib.ExitStack() as stack:
        stack.callback(remove_temp_file)

        outfd: BinaryIO = stack.enter_context(open(tmppath, 'wb'))

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

        outfd.write(b'\n]\n')

        outfd.flush()

        success = True

    os.replace(tmppath, path)

    return num_records
