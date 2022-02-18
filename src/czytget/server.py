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
import datetime
import os
import pickle
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


class ServerError(Exception):
    """
    Exception class thrown by parseConfig
    """
    def __init__(self, what: str):
        super().__init__(what)
    #__init__

#ServerError


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


_FINISHED_FILE = "finished.pkl"
_PROCESSING_FILE = "processing.pkl"
_QUEUED_FILE = "queued.pkl"

_FILE_CANDIDATES = ( _FINISHED_FILE, _PROCESSING_FILE, _QUEUED_FILE )


def _getSubdirs(root: str) -> list[str]:
    return sorted(list([ os.path.basename(direc) \
                         for direc, subdirs, files in os.walk(root) \
                         if len(set(files).intersection(_FILE_CANDIDATES)) ]))
#_getSubDirs


def _dumpFile(filename: str, q: set):
    try:
        with open(filename, "wb") as f:
            pickle.dump(q, f)
        #with
    except Exception as e:
        _logger.error("Server: failed to dump data to file '%s': %s"
                      % (filename, e))
    #except
#_dumpFile


def _loadFile(filename: str, previous: set) -> set:
    if os.path.exists(filename):
        try:
            with open(filename, "rb") as f:
                data = pickle.load(f)
            #with
        except Exception as e:
            _logger.error("Server: failed to read data file '%s': %s"
                          % (filename, e))
            raise ServerError("ERROR: failed to read data file '%s': %s"
                              % (filename, e))
        #except
        if type(data) != set:
            _logger.error("Server: corrupted data file '%s'" % filename)
            raise ServerError("ERROR: corrupted data file '%s'" % filename)
        else:
            return previous.union(data)
        #else
    #if
#_loadFile


class Server(czthreading.ReactiveThread):
    """
    Implements a loop that takes commands from a client via messages of the
    following types:
        - MsgAck
        - MsgAdd
        - MsgList
        - MsgAllocate
        - MsgDateList

    Some commands expect a server response.  If the command message provides
    a response buffer (queue.Queue), the server puts the response into that
    buffer.
    """

    def __init__(self, config: ServerConfig):
        """
        Constructor.

        :raises: ServerError
        """
        super().__init__('czytget-server', 1)
        self._dataDir \
            = os.path.join(config.dataDir,
                           datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        try:
            os.makedirs(self._dataDir)
            _logger.info("Server: writing data to", self._dataDir)
        except OSError as e:
            errorString = "Server: cannot create data dir '%s': %s"\
                          % (self._dataDir, e)
            _logger.error(errorString)
            raise ServerError(errorString)
        #except
        self._finishedFile = os.path.join(self._dataDir, _FINISHED_FILE)
        self._processingFile = os.path.join(self._dataDir, _PROCESSING_FILE)
        self._queuedFile = os.path.join(self._dataDir, _QUEUED_FILE)
        self._workers = [ Worker("worker-%d" % i, self)
                          for i in range(config.numThreads) ]
        self._queuedCodes = set()
        self._processingCodes = set()
        self._finishedCodes = set()
        self.addMessageProcessor("MsgAck", self.processMsgAck)
        self.addMessageProcessor("MsgAdd", self.processMsgAdd)
        self.addMessageProcessor("MsgList", self.processMsgList)
        self.addMessageProcessor("MsgAllocate", self.processMsgAllocate)
        self.addMessageProcessor("MsgSessionList", self.processMsgSessionList)
        self.addMessageProcessor("MsgLoadSession", self.processMsgLoadSession)
        self.addMessageProcessor("MsgLoadAll", self.processMsgLoadAll)
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
        self._dumpAll()
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
            self._dumpQueued()
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
                    self._processingCodes.add(ytCode)
                    self._dumpQueued()
                    self._dumpProcessing()
                    worker.comm(MsgTask(ytCode))
                except KeyError:
                    pass
                #except
            #if
        #for
    #processMsgAllocate


    def processMsgSessionList(self, message: MsgSessionList):
        message.responseBuffer.put(
            '\n'.join(_getSubdirs(os.path.dirname(self._dataDir))))
    #processMsgDateList


    def _loadSession(self, session: str, finishedToo: bool):
        _logger.info("loading", session)
        if not os.path.exists(session):
            raise ServerError("ERROR: session '%s' does not exist" % session)
        #if
        self._queuedCodes = _loadFile(
            os.path.join(session, _PROCESSING_FILE), self._queuedCodes)
        self._queuedCodes = _loadFile(
            os.path.join(session, _QUEUED_FILE), self._queuedCodes)
        if finishedToo:
            self._finishedCodes = _loadFile(
                os.path.join(session, _FINISHED_FILE), self._finishedCodes)
        #if
    #_loadSession


    def processMsgLoadSession(self, message: MsgLoadSession):
        dataDir = os.path.join(os.path.dirname(self._dataDir), message.session)
        try:
            self._loadSession(dataDir, True)
            if message.responseBuffer is not None:
                message.responseBuffer.put("successfully loaded session '%s'"
                                           % message.session)
            #if
        except ServerError as e:
            if message.responseBuffer is not None:
                message.responseBuffer.put(str(e))
            #if
        #except
        self.comm(MsgAllocate())
    #processMsgLoadSession


    def processMsgLoadAll(self, message: MsgLoadAll):
        sessions = _getSubdirs(os.path.dirname(self._dataDir))
        try:
            for session in sessions:
                self._loadSession(os.path.join(os.path.dirname(self._dataDir), session),
                                  not message.pendingOnly)
            #for
            if message.responseBuffer is not None:
                message.responseBuffer.put("successfully loaded all sessions")
            #if
        except ServerError as e:
            if message.responseBuffer is not None:
                message.responseBuffer.put(str(e))
            #if
        #except
        self.comm(MsgAllocate())
    #processMsgLoadAll


    # def process(self, message: Msg):
    #     pass
    #
    # #process


    def _dumpAll(self):
        self._dumpQueued()
        self._dumpProcessing()
        self._dumpFinished()
    #_dumpAll

    def _dumpFinished(self):
        _dumpFile(self._finishedFile, self._finishedCodes)
    #_dumpFinished

    def _dumpProcessing(self):
        _dumpFile(self._processingFile, self._processingCodes)
    #_dumpProcessing

    def _dumpQueued(self):
        _dumpFile(self._queuedFile, self._queuedCodes)
    #_dumpQueued

#Server


### aczutro ###################################################################
