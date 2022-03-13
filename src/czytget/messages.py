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
Messages sent between server and client, and server and its worker threads.
"""

from czutils.utils import czthreading
import queue


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


class MsgAddCode(czthreading.Message):
    """
    Add command sent by client to server.
    Interprets 'ytCode' as an individual code.
    """
    def __init__(self, ytCode: str, responseBuffer: queue.Queue):
        super().__init__()
        self.ytCode = ytCode
        self.responseBuffer = responseBuffer
    #__init__

#MsgAddCode


class MsgAddList(czthreading.Message):
    """
    Add command sent by client to server.
    Interprets 'ytCode' as a playlist code.
    """
    def __init__(self, ytCode: str, responseBuffer: queue.Queue):
        super().__init__()
        self.ytCode = ytCode
        self.responseBuffer = responseBuffer
    #__init__

#MsgAddList


class MsgRetry(czthreading.Message):
    """
    Retry command sent by client to server.
    """
    pass
#MsgRetry


class MsgDiscard(czthreading.Message):
    """
    Discard command sent by client to server.
    """
    pass
#MsgDiscard


class MsgList(czthreading.Message):
    """
    List command sent by client to server.

    The response buffer must not be None.
    """
    def __init__(self, responseBuffer: queue.Queue):
        super().__init__()
        self.responseBuffer = responseBuffer
    #__init__
#MsgList


class MsgSessionList(czthreading.Message):
    """
    "Session ls" command sent by client to server.

    The response buffer must not be None.
    """
    def __init__(self, responseBuffer: queue.Queue):
        super().__init__()
        self.responseBuffer = responseBuffer
    #__init__
#MsgSessionList


class MsgLoadSession(czthreading.Message):
    """
    "Session load" command sent by client to server.
    """
    def __init__(self, session: str, responseBuffer: queue.Queue):
        super().__init__()
        self.session = session
        self.responseBuffer = responseBuffer
    #__init__
#MsgLoadSession


class MsgLoadAllSelection:
    ALL = 0,
    PENDING_ONLY = -1,
    FINISHED_ONLY = 1
#MsgLoadAllSelection

class MsgLoadAll(czthreading.Message):
    """
    "Session load all/pending" commands sent by client to server.
    """
    def __init__(self, selection: int, responseBuffer: queue.Queue):
        """
        :param selection: one of the constants defined in class
                          MsgLoadAllSelection
        """
        super().__init__()
        self.selection = selection
        self.responseBuffer = responseBuffer
    #__init__
#MsgLoadAll


### aczutro ###################################################################
