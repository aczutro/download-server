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

"""czytget messages"""

from czutils.utils import czthreading


class MsgTask(czthreading.Message):
    """
    Task sent by server to worker thread.
    """
    def __init__(self, ytCode: str):
        super().__init__()
        self.ytCode = ytCode
    #__init__

#MsgTask


class MsgAck(czthreading.Message):
    """
    Acknowledgement sent by worker thread to server.
    """
    def __init__(self, ytCode: str, success: bool):
        super().__init__()
        self.ytCode = ytCode
        self.success = success
    #__init__

#MsgAck


class MsgAllocate(czthreading.Message):
    """
    Sent by server to self to allocate a task to a free thread.
    """
    pass
#MsgAllocate


class MsgAdd(czthreading.Message):
    """
    Add command sent by client to server.
    """
    def __init__(self, ytCode: str):
        super().__init__()
        self.ytCode = ytCode
    #__init__

#MsgAdd


class MsgList(czthreading.Message):
    """
    List command sent by client to server.
    """
    pass
#MsgList
