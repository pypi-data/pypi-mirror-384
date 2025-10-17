#  pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2020-present Cezar H. <https://github.com/usernein>
#  Copyright (C) 2023-present pyrogram <https://pyrogram.org>
#
#  This file is part of pyrogram.
#
#  pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with pyrogram.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Identifier:
    inline_message_id: str | list[str] | None = None
    chat_id: int | str | list[int | str] | None = None
    message_id: int | list[int] | None = None
    from_user_id: int | str | list[int | str] | None = None

    def matches(self, update: Identifier) -> bool:
        # Compare each property of other with the corresponding property in self
        # If the property in self is None, the property in other can be anything
        # If the property in self is not None, the property in other must be the same
        for field in self.__annotations__:
            pattern_value = getattr(self, field)
            update_value = getattr(update, field)

            if pattern_value is not None:
                if isinstance(update_value, list):
                    if isinstance(pattern_value, list):
                        if not set(update_value).intersection(set(pattern_value)):
                            return False
                    elif pattern_value not in update_value:
                        return False
                elif isinstance(pattern_value, list):
                    if update_value not in pattern_value:
                        return False
                elif update_value != pattern_value:
                    return False
        return True

    def count_populated(self):
        non_null_count = 0

        for attr in self.__annotations__:
            if getattr(self, attr) is not None:
                non_null_count += 1

        return non_null_count
