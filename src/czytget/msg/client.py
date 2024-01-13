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
Messages sent by client.
"""

from czutils.utils import czthreading
import queue
import time


class MsgAddCode(czthreading.Message):
    """
    Add command sent by client to server.
    Interprets 'ytCode' as an individual code.
    """
    def __init__(self, ytCode: str):
        super().__init__()
        self.queryID = time.monotonic_ns()
        self.ytCode = ytCode
    #__init__
#MsgAddCode


class MsgAddList(MsgAddCode):
    """
    Add command sent by client to server.
    Interprets 'ytCode' as a playlist code.
    """
    pass
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


class LoadAllSelection:
    ALL = 0,
    PENDING_ONLY = -1,
    FINISHED_ONLY = 1
#LoadAllSelection


class MsgLoadAll(czthreading.Message):
    """
    "Session load all/pending" commands sent by client to server.
    """
    def __init__(self, selection: int, responseBuffer: queue.Queue):
        """
        :param selection: one of the constants defined in class
                          LoadAllSelection
        """
        super().__init__()
        self.selection = selection
        self.responseBuffer = responseBuffer
    #__init__
#MsgLoadAll


### aczutro ###################################################################
