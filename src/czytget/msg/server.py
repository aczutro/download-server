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
Messages sent by server components.
"""
from czutils.utils import czthreading
import collections


Job = collections.namedtuple("Job", "clientID ytCode")


class MsgTask(czthreading.Message):
    """
    Task sent by server to worker thread.
    """
    def __init__(self, job: Job):
        super().__init__()
        self.job = job
    #__init__
#MsgTask


class MsgAck(MsgTask):
    """
    Acknowledgement sent by worker thread to server.
    """
    def __init__(self, job: Job, success: bool, errorMsg: str):
        super().__init__(job)
        self.success = success
        self.errorMsg = errorMsg
    #__init__
#MsgAck


class MsgAllocate(czthreading.Message):
    """
    Sent by server to self to allocate a task to a free thread.
    """
    pass
#MsgAllocate


class Response:
    OK, NOK = range(2)
#Response


class MsgResponse(czthreading.Message):
    """
    Response sent by server to client.
    """
    def __init__(self, queryID: int, text: str):
        super().__init__()
        self.queryID = queryID
        self.text = text
    #__init__
#MsgResponse


### aczutro ###################################################################
