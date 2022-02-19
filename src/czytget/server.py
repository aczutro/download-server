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

"""czytget server"""

from .config import ServerConfig
from .messages import *
from czutils.utils import czlogging, czthreading
import random
import time


_logger = czlogging.LoggingChannel("czytget.server",
                                   czlogging.LoggingLevel.SILENT,
                                   colour=True)

def setLoggingOptions(level: int, colour=True) -> None:
    """
    Sets this module's logging level.  If not called, the logging level is
    SILENT.

    :param level: One of the following:
                  - czlogging.LoggingLevel.INFO
                  - czlogging.LoggingLevel.WARNING
                  - czlogging.LoggingLevel.ERROR
                  - czlogging.LoggingLevel.SILENT

    :param colour: If true, use colour in log headers.
    """
    global _logger
    _logger = czlogging.LoggingChannel("czytget.server", level, colour=colour)

#setLoggingOptions


class Worker(czthreading.ReactiveThread):
    """
    A worker thread that processes a YT code on demand.
    """

    def __init__(self, threadName: str, server):
        super().__init__(threadName, 1)
        self._server = server
        self._free = True
        self.addMessageProcessor("MsgTask", self.processMsgTask)
    #__init__


    def free(self) -> bool:
        """
        :returns: True if it is not working.
        """
        return self._free
    #free


    def processMsgTask(self, message: MsgTask):
        """
        Processes the YT code contained in 'message' and sends a MsgAck message
        back to the server when the processing is finished.
        """
        self._free = False
        ytCode = message.ytCode
        success = self._processCode(ytCode)
        self._server.comm(MsgAck(ytCode, success))
        self._free = True
    #processMsgTask


    def _processCode(self, ytCode: str) -> bool:
        """
        Processes a YT code.

        :returns: True if successful.
        """
        ans = bool(random.randint(0, 1))
        time.sleep(10 * random.random())
        return ans
    #__processCode

#Worker


class Server(czthreading.ReactiveThread):
    """
    Implements a loop that takes commands from a client via messages of the
    following types:
        - MsgAck
        - MsgAdd
        - MsgList
        - MsgAllocate

    Some commands expect a server response.  If the command message provides
    a response buffer (queue.Queue), the server puts the response into that
    buffer.
    """

    def __init__(self, config: ServerConfig):
        super().__init__('czytget-server', 1)
        self._config = config
        self._workers = [ Worker("worker-%d" % i, self)
                          for i in range(self._config.numThreads) ]
        self._queuedCodes = set()
        self._processingCodes = set()
        self._finishedCodes = set()
        self.addMessageProcessor("MsgAck", self.processMsgAck)
        self.addMessageProcessor("MsgAdd", self.processMsgAdd)
        self.addMessageProcessor("MsgList", self.processMsgList)
        self.addMessageProcessor("MsgAllocate", self.processMsgAllocate)

    #__init__


    def threadCodePre(self):
        print("starting czytget server")
        for worker in self._workers:
            worker.start()
        #for

    #threadCodePre


    def threadCodePost(self):
        print("stopping czytget server")
        for worker in self._workers:
            worker.stop()
        #for

    #threadCodePost


    def processMsgAck(self, message: MsgAck):
        _logger.info("received", message)
        ytCode = message.ytCode
        success = message.success
        self._processingCodes.remove(ytCode)
        if success:
            self._finishedCodes.add(ytCode)
        else:
            self._queuedCodes.add(ytCode)
        #if
        self.comm(MsgAllocate())
    #processMsgAck


    def processMsgAdd(self, message: MsgAdd):
        """
        Processes a message of type MsgAdd, i.e. adds message.ytCode to the
        processing queue and, if message.responseBuffer is not None, puts a
        response string into it.
        """
        ytCode = message.ytCode
        if ytCode in self._processingCodes:
            if message.responseBuffer is not None:
                message.responseBuffer.put("YT code '%s' already being processed"
                                           % message.ytCode)
            #if
        elif ytCode in self._finishedCodes:
            if message.responseBuffer is not None:
                message.responseBuffer.put("YT code '%s' already processed"
                                           % message.ytCode)
            #if
        else:
            if message.responseBuffer is not None:
                message.responseBuffer.put("YT code '%s' queued" % message.ytCode)
            #if
            self._queuedCodes.add(ytCode)
            self.comm(MsgAllocate())
        #else

    #processMsgAdd


    def processMsgList(self, message: MsgList):
        """
        Processes a message of type MsgList, creates a string listing the
        contents of the internal code queue and puts the result into
        'message.responseBuffer'.  'message.responseBuffer' must not be None.
        """
        response = "queued codes:"
        for ytCode in self._queuedCodes:
            response = "%s\n  %s" % (response, ytCode)
        #for
        response = "%s\ncodes in process:" % response
        for ytCode in self._processingCodes:
            response = "%s\n  %s" % (response, ytCode)
        #for
        response = "%s\nfinished codes:" % response
        for ytCode in self._finishedCodes:
            response = "%s\n  %s" % (response, ytCode)
        #for
        message.responseBuffer.put(response)

    #processMsgList


    def processMsgAllocate(self, message: MsgAllocate):
        for worker in self._workers:
            if worker.free():
                try:
                    ytCode = self._queuedCodes.pop()
                    worker.comm(MsgTask(ytCode))
                    self._processingCodes.add(ytCode)
                except KeyError:
                    pass
                #except
            #if
        #for

    #processMsgAllocate


    # def process(self, message: Msg):
    #     pass
    #
    # #process


    # def process(self, message: Msg):
    #     pass
    #
    # #process


    # def process(self, message: Msg):
    #     pass
    #
    # #process


    # def process(self, message: Msg):
    #     pass
    #
    # #process

#Server


### aczutro ###################################################################
