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


from typing import TYPE_CHECKING

from pyrogram.types import Identifier, Listener, ListenerTypes

if TYPE_CHECKING:
    import pyrogram


class GetManyListenersMatchingWithIdentifierPattern:
    def get_many_listeners_matching_with_identifier_pattern(
        self: "pyrogram.Client",
        pattern: Identifier,
        listener_type: ListenerTypes,
    ) -> list[Listener]:
        """
        Same of :meth:`pyrogram.Client.get_listener_matching_with_identifier_pattern` but returns a list of listeners instead of one.

        Parameters:
            pattern (:obj:`~pyrogram.types.Identifier`):
                Same as :meth:`pyrogram.Client.get_listener_matching_with_identifier_pattern`.

            listener_type (:obj:`~pyrogram.types.ListenerTypes`):
                Same as :meth:`pyrogram.Client.get_listener_matching_with_identifier_pattern`.

        Returns:
            List[:obj:`~pyrogram.types.Listener`]: A list of listeners that match the given identifier pattern.
        """
        return [
            listener
            for listener in self.listeners[listener_type]
            if pattern.matches(listener.identifier)
        ]
