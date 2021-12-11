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
import queue
import random
import time


_logger = czlogging.LoggingChannel("czytget.server",
                                   czlogging.LoggingLevel.SILENT,
                                   colour=True)

def setLoggingLevel(level: int, colour=True) -> None:
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

#setLoggingLevel


class Worker(czthreading.ReactiveThread):
    """

    """

    def __init__(self, threadName: str, server):
        super().__init__(threadName, 1)
        self._server = server
        self._free = True
        self.addMessageProcessor("MsgTask", self.processMsgTask)

    #__init__


    def free(self) -> bool:
        return self._free

    #free


    def processMsgTask(self, message: MsgTask):
        self._free = False
        ytCode = message.ytCode
        success = self._downloadVideo(ytCode)
        self._server.comm(MsgAck(ytCode, success))
        self._free = True

    #processMsgTask


    def _downloadVideo(self, ytCode: str) -> bool:
        """
        just simulating
        """

        ans = bool(random.randint(0, 1))
        time.sleep(10 * random.random())
        return ans

    #_downloadVideo

#Worker


class Server(czthreading.ReactiveThread):
    """

    """

    def __init__(self, config: ServerConfig):
        super().__init__('czytget-server', 1)
        self._config = config
        self._workers = [ Worker("worker-%d" % i, self)
                          for i in range(self._config.numThreads) ]
        self._queuedCodes = set()
        self._processingCodes = set()
        self._finishedCodes = set()
        self.serverResponse = queue.Queue(maxsize = 1)
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
        ytCode = message.ytCode
        if ytCode in self._processingCodes:
            self.serverResponse.put("YT code '%s' already being processed"
                                    % message.ytCode)
        elif ytCode in self._finishedCodes:
            self.serverResponse.put("YT code '%s' already processed"
                                    % message.ytCode)
        else:
            self._queuedCodes.add(ytCode)
            self.serverResponse.put("YT code '%s' queued" % message.ytCode)
            self.comm(MsgAllocate())
        #else

    #processMsgAdd


    def processMsgList(self, message: MsgList):
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
        self.serverResponse.put(response)

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
