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

from . import __version__, __author__
from .config import ServerConfig
from .messages import *
from .ytconnector import YTConfig, YTConnector, mergeCookieFiles, getYTList
from czutils.utils import czlogging, czthreading, cztext
import datetime
import os
import pickle
import shutil


_logger = czlogging.LoggingChannel("czytget.server",
                                   czlogging.LoggingLevel.SILENT,
                                   colour=True)


def setLoggingOptions(level: int, colour=True) -> None:
    """Sets this module's logging level and colour option.
    If not called, the logging level is SILENT.
    """
    global _logger
    _logger = czlogging.LoggingChannel("czytget.server", level, colour=colour)
#setLoggingOptions


class ServerError(Exception):
    """
    Exception class thrown by Server
    """
    def __init__(self, what: str):
        super().__init__(what)
    #__init__

#ServerError


class Worker(czthreading.ReactiveThread):
    """
    A worker thread that processes a YT code on demand.
    """

    def __init__(self, threadName: str, ytConfig: YTConfig, server):
        super().__init__(threadName, 1)
        self._server = server
        self._free = True
        self.addMessageProcessor("MsgTask", self.processMsgTask)
        self._cookies = ytConfig.cookies
        self._ytdl = YTConnector(ytConfig)
    #__init__


    def threadCodePost(self) -> None:
        self._ytdl.close()
    #threadCodePost


    def cookieFile(self) -> str:
        """
        :returns: cookie file name.
        """
        return self._cookies
    #cookieFile


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
        successful, errorMsg = self._ytdl.download(ytCode)
        if successful:
            _logger.info("[%s] download succeeded:" % ytCode)
        else:
            _logger.error("[%s] download failed:" % ytCode, errorMsg)
        #else
        return successful
    #__processCode

#Worker


_FAILED_FILE = "failed.pkl"
_FINISHED_FILE = "finished.pkl"
_PROCESSING_FILE = "processing.pkl"
_QUEUED_FILE = "queued.pkl"

_FILE_CANDIDATES = ( _FAILED_FILE, _FINISHED_FILE, _PROCESSING_FILE, _QUEUED_FILE )


def _getSubdirs(root: str) -> list[str]:
    """
    Returns a list of subdirectories of 'root' that contain at least one of
    the files in _FILE_CANDIDATES.
    """
    return sorted(list([ os.path.basename(direc) \
                         for direc, subdirs, files in os.walk(root) \
                         if len(set(files).intersection(_FILE_CANDIDATES)) ]))
#_getSubDirs


def _dumpFile(filename: str, q: set) -> None:
    """
    Writes the contents of q to file.
    """
    try:
        with open(filename, "wb") as f:
            pickle.dump(q, f)
        #with
    except Exception as e:
        _logger.error("Server: failed to dump data to file '%s': %s"
                      % (filename, e))
    #except
#_dumpFile


def _loadFile(filename: str) -> set:
    """
    Load a data file and returns the loaded data as a set of codes.
    """
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
        if type(data) == set:
            return data
        else:
            _logger.error("Server: corrupted data file '%s'" % filename)
            raise ServerError("ERROR: corrupted data file '%s'" % filename)
        #else
    else:
        return set()
    #else
#_loadFile


def _makeYTConfig(srcCookieFile: str, dstCookieFile:str, descriptions: bool) \
        -> YTConfig:
    """
    Copies file 'src' to 'dst' if 'src' exists.
    Then adds 'dst' to the returned YT config, even if 'src' does not exist.

    :returns: a YTConfig
    """
    if os.path.exists(srcCookieFile):
        shutil.copyfile(srcCookieFile, dstCookieFile)
    #if
    ans = YTConfig()
    ans.cookies = dstCookieFile
    ans.descriptions = descriptions
    return ans
#_copyCookies


def _printQueue(q: set, label: str) -> str:
    response = ""
    if len(q):
        response = label
        for ytCode in q:
            response = "%s\n  %s" % (response, ytCode)
        #for
    #if
    return response
#_printQueue


class Server(czthreading.ReactiveThread):
    """
    Implements a loop that takes commands from a client via message passing.

    Some commands expect a server response.  If the command message provides
    a response buffer (queue.Queue), the server puts the response into that
    buffer.
    """

    def __init__(self, config: ServerConfig):
        """
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

        self._cookies = config.cookies

        self._workers = [
            Worker("worker-%d" % i,
                   _makeYTConfig(self._cookies,
                                 "%s-%d" % (self._cookies, i),
                                 config.descriptions),
                   self)
            for i in range(config.numThreads) ]

        self._failedFile = os.path.join(self._dataDir, _FAILED_FILE)
        self._finishedFile = os.path.join(self._dataDir, _FINISHED_FILE)
        self._processingFile = os.path.join(self._dataDir, _PROCESSING_FILE)
        self._queuedFile = os.path.join(self._dataDir, _QUEUED_FILE)

        self._failedCodes = set()
        self._queuedCodes = set()
        self._processingCodes = set()
        self._finishedCodes = set()

        self.addMessageProcessor("MsgAck", self.processMsgAck)
        self.addMessageProcessor("MsgAddCode", self.processMsgAddCode)
        self.addMessageProcessor("MsgAddList", self.processMsgAddList)
        self.addMessageProcessor("MsgRetry", self.processMsgRetry)
        self.addMessageProcessor("MsgDiscard", self.processMsgDiscard)
        self.addMessageProcessor("MsgList", self.processMsgList)
        self.addMessageProcessor("MsgAllocate", self.processMsgAllocate)
        self.addMessageProcessor("MsgSessionList", self.processMsgSessionList)
        self.addMessageProcessor("MsgLoadSession", self.processMsgLoadSession)
        self.addMessageProcessor("MsgLoadAll", self.processMsgLoadAll)
    #__init__


    def threadCodePre(self):
        print("czytget server v.%s" % __version__)
        print(__author__)
        for worker in self._workers:
            worker.start()
        #for
    #threadCodePre


    def threadCodePost(self):
        print("stopping czytget server")
        cookieFiles = []
        for worker in self._workers:
            cookieFiles.append(worker.cookieFile())
            worker.stop()
        #for
        mergeCookieFiles(self._cookies, *cookieFiles)
        for f in cookieFiles:
            os.remove(f)
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
            self._failedCodes.add(ytCode)
        #if
        self._dumpAll()
        self.comm(MsgAllocate())
    #processMsgAck


    def processMsgAddCode(self, message: MsgAddCode):
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

    #processMsgAddCode


    def processMsgAddList(self, message: MsgAddList):
        """
        Processes a message of type MsgAdd, i.e. adds message.ytCode to the
        processing queue and, if message.responseBuffer is not None, puts a
        response string into it.
        """
        codes, err = getYTList(message.ytCode, self._cookies)

        if codes is None:
            _logger.error(err)
            message.responseBuffer.put(err)
        else:
            for code in codes:
                self.comm(MsgAddCode(code, message.responseBuffer))
            #for
        #else

    #processMsgAddList


    def processMsgRetry(self, message: MsgRetry):
        """
        Processes a message of type MsgRetry, i.e. moves all failed code back
        to the processing queue.
        """
        self._queuedCodes.update(self._failedCodes)
        self._failedCodes.clear()
        self._dumpQueued()
        self._dumpFailed()
        self.comm(MsgAllocate())
    #processMsgRetry


    def processMsgDiscard(self, message: MsgDiscard):
        """
        Processes a message of type MsgRetry, i.e. moves all failed code back
        to the processing queue.
        """
        self._failedCodes.clear()
        self._dumpFailed()
    #processMsgDiscard


    def processMsgList(self, message: MsgList):
        """
        Processes a message of type MsgList, creates a string listing the
        contents of the internal code queue and puts the result into
        'message.responseBuffer'.  'message.responseBuffer' must not be None.
        """
        message.responseBuffer.put('\n'.join([ s for s in [
            _printQueue(self._finishedCodes,
                        cztext.colourise("finished codes:",
                                         foreground=cztext.Col16.GREEN)),
            _printQueue(self._failedCodes,
                        cztext.colourise("failed codes:",
                                         foreground=cztext.Col16.RED)),
            _printQueue(self._processingCodes,
                        cztext.colourise("codes in process:",
                                         foreground=cztext.Col16.BLUE)),
            _printQueue(self._queuedCodes,
                        cztext.colourise("queued codes:",
                                         foreground=cztext.Col16.YELLOW))
        ] if len(s) ]))
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


    def _loadSession(self, session: str, selection: int):
        """
        :param selection: one of the constants defined in class
                          MsgLoadAllSelection
        """
        _logger.info("loading", session)
        if not os.path.exists(session):
            raise ServerError("ERROR: session '%s' does not exist" % session)
        #if
        if selection in [ MsgLoadAllSelection.ALL, MsgLoadAllSelection.PENDING_ONLY ]:
            self._queuedCodes.update(_loadFile(os.path.join(session, _PROCESSING_FILE)))
            self._queuedCodes.update(_loadFile(os.path.join(session, _QUEUED_FILE)))
            self._failedCodes.update(_loadFile(os.path.join(session, _FAILED_FILE)))
        #if
        if selection in [ MsgLoadAllSelection.ALL, MsgLoadAllSelection.FINISHED_ONLY ]:
            self._finishedCodes.update(_loadFile(os.path.join(session, _FINISHED_FILE)))
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
                                  message.selection)
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


    def _dumpAll(self):
        self._dumpQueued()
        self._dumpProcessing()
        self._dumpFinished()
        self._dumpFailed()
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

    def _dumpFailed(self):
        _dumpFile(self._failedFile, self._failedCodes)
    #_dumpFailed

#Server


### aczutro ###################################################################
