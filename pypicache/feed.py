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

import xml.etree.ElementTree as ET
from typing import Optional, Set, Tuple


class FeedParser:
    _prev_first_title: Optional[str] = None

    def parse_feed(self, feed: str) -> Tuple[bool, Set[str]]:
        new_updates = set()
        prev_first_title_seen = False

        first_title = None

        for item in ET.fromstring(feed).findall('channel/item'):
            if (elt := item.find('title')) is None:
                raise RuntimeError('Cannot fild <title> item element')

            title = elt.text
            assert(isinstance(title, str))

            if first_title is None:
                first_title = title

            if title == self._prev_first_title:
                prev_first_title_seen = True
                break

            new_updates.add(title.split()[0])

        self._prev_first_title = first_title

        return prev_first_title_seen, new_updates
