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

from .ask import Ask
from .get_listener_matching_with_data import GetListenerMatchingWithData
from .get_listener_matching_with_identifier_pattern import GetListenerMatchingWithIdentifierPattern
from .get_many_listeners_matching_with_data import GetManyListenersMatchingWithData
from .get_many_listeners_matching_with_identifier_pattern import (
    GetManyListenersMatchingWithIdentifierPattern,
)
from .listen import Listen
from .register_next_step_handler import RegisterNextStepHandler
from .remove_listener import RemoveListener
from .stop_listener import StopListener
from .stop_listening import StopListening


class Pyromod(
    Ask,
    GetListenerMatchingWithData,
    GetListenerMatchingWithIdentifierPattern,
    GetManyListenersMatchingWithData,
    GetManyListenersMatchingWithIdentifierPattern,
    Listen,
    RegisterNextStepHandler,
    RemoveListener,
    StopListener,
    StopListening,
):
    pass
