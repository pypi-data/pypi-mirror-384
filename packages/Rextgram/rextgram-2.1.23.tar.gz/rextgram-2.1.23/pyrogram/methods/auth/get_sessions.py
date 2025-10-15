#  pyrogram - Telegram MTProto API Client Library for Python
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

import logging

import pyrogram
from pyrogram import raw, types

log = logging.getLogger(__name__)


class GetSessions:
    async def get_sessions(
        self: "pyrogram.Client",
    ) -> list["types.Session"]:
        """Get your info data by other sessions .

        Returns:
            List[:obj:`~pyrogram.types.Session`]: List of active sessions.
        """

        authorizations = await self.invoke(raw.functions.account.GetAuthorizations())
        return [types.Session._parse(auth) for auth in authorizations.authorizations]
