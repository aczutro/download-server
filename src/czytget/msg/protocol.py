# Copyright (C) 2021 - present  Alexander Czutro <github@czutro.ch>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# For more details, see the provided licence file or
# <http://www.gnu.org/licenses>.
#
################################################################### aczutro ###

"""
Messages sent by protocol.
"""

from czutils.utils import czthreading


class MsgConnected(czthreading.Message):
    """Sent by Protocol to Server/Client when other side has connected.
    """
    def __init__(self, clientID: int):
        super().__init__()
        self.clientID = clientID
    #__init__
#MsgConnected


class MsgDisconnected(czthreading.Message):
    """Sent by Protocol to Server/Client when other side has disconnected.
    """
    def __init__(self, clientID: int):
        super().__init__()
        self.clientID = clientID
    #__init__
#MsgDisconnected


### aczutro ###################################################################
