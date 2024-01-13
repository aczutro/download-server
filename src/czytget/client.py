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

"""czytget client"""

from . import __version__, __author__
from . import config, msg, protocol, czcommunicator, czcode2
from .msg import client
from czutils.utils import czlogging, czthreading
import cmd
import queue
import threading


_logger = czlogging.LoggingChannel("czytget.client",
                                   czlogging.LoggingLevel.SILENT,
                                   colour=True)


def setLoggingOptions(level: int, colour=True) -> None:
    """Sets this module's logging level and colour option.
    If not called, the logging level is SILENT.
    """
    global _logger
    _logger = czlogging.LoggingChannel("czytget.client", level, colour=colour)
#setLoggingOptions


class ClientError(Exception):
    pass
#ClientError


class KillSwitch(Exception):
    pass
#KillSwitch


class Client(czthreading.ReactiveThread, cmd.Cmd):
    """
    An "integrated" czytget client that talks directly with the server via
    message passing (without additional protocol).  Meant to run in the same
    process as the server.

    Offers a basic shell (command prompt loop).
    """

    def __init__(self, conf: config.ClientConfig, commConfig: config.CommConfig):
        super().__init__("czytget.client", 1)
        self._config = conf
        try:
            self._connector = protocol.Protocol(commConfig, False, self)
        except czcommunicator.CommError as e:
            _logger.error(e)
            raise ClientError(f"communication error: {e}")
        #except
        self._processingMessages = True
        self._msgLoop = threading.Thread(target=self._messageLoop,
                                         name="czytget.client.msgLoop",
                                         daemon=True)
        self._cmdLoopRunning = False
        self._killSwitch = None
    #__init__


    def threadCode(self):
        self._msgLoop.start()
        self._connector.start()

        self.prompt = "\nczytget> "
        self.intro = f"czytget client v.{__version__}" \
                     f"\n{__author__}\n" \
                     "\nType 'help' or '?' to list commands."
        self._cmdLoopRunning = True
        try:
            self.cmdloop()
        except KillSwitch:
            self.stdout.write(self._killSwitch)
        #except
        self._cmdLoopRunning = False

        self._connector.stop()
        self._connector.wait()
        self._processingMessages = False
        self._msgLoop.join()
    #threadCode


    def emptyline(self) -> bool:
        """
        Overwrites cmd.Cmd.emptyline so that an empty input line does nothing.
        :returns: False
        """
        return False # on true, prompt loop will end
    #emptyline


    def do_help(self, arg: str) -> bool:
        """
        Overwrites cmd.Cmd.do_help to print custom help message.
        :param arg: ignored
        :returns: False
        """
        self._checkKillSwitch()

        self.stdout.write("\nCommands")
        self.stdout.write("\n========")
        self.stdout.write("\n")
        self.stdout.write("\na CODE [CODE ...]")
        self.stdout.write("\n        add YT codes to the download list")
        self.stdout.write("\n")
        self.stdout.write("\nf FILE [FILE ...]")
        self.stdout.write("\n        add all YT codes found in files to the download list")
        self.stdout.write("\n")
        self.stdout.write("\nl       list queued, processed and finished codes")
        self.stdout.write("\n")
        self.stdout.write("\nr       retry: queue all failed codes again")
        self.stdout.write("\n")
        self.stdout.write("\nd       discard: empty the queue of failed codes")
        self.stdout.write("\n")
        self.stdout.write("\nsls     'Session LS': list previous sessions")
        self.stdout.write("\n")
        self.stdout.write("\nsld SESSION [SESSION ...]")
        self.stdout.write("\n        'Session LoaD': load session SESSION")
        self.stdout.write("\n")
        self.stdout.write("\nsla     'Session Load All': load all available sessions")
        self.stdout.write("\n")
        self.stdout.write("\nslf     'Session Load Finished': load all available sessions,")
        self.stdout.write("\n        but only finished codes")
        self.stdout.write("\n")
        self.stdout.write("\nslp     'Session Load Pending': load all available sessions,")
        self.stdout.write("\n        but only unfinished codes")
        self.stdout.write("\n")
        self.stdout.write("\nq       terminate the client")
        self.stdout.write("\n")
        return False # on true, prompt loop will end
    #do_help


    def do_a(self, args: str) -> bool:
        """ Implements the ADD command.

        :param args: space-separated list of YT codes.
        """
        self._checkKillSwitch()

        codes = args.split()
        if len(codes) == 0:
            self._error("add: YT code expected")
        else:
            for ytCode in codes:
                if len(ytCode) == 11:
                    _logger.info("adding code", ytCode)
                    message = msg.client.MsgAddCode(ytCode)
                    self._connector.send(message)
                    self._waitForResponse(message.queryID)
                    #self._getResponse(response)
                elif len(ytCode) == 34:
                    _logger.info("adding code", ytCode)
                    message = msg.client.MsgAddList(ytCode)
                    self._connector.send(message)
                    self._waitForResponse(message.queryID)
                    #self._getResponse(response, multiLine=True)
                else:
                    self._error("bad YT code:", ytCode)
                #else
            #for
        #else
        return False # on true, prompt loop will end
    #do_a


    def do_f(self, args) -> bool:
        """
        Implements FILE command.
        :param args: space-separated list of file names.
        :return: False
        """
        self._checkKillSwitch()

        files = args.split()
        if len(files) == 0:
            self._error("add: filename expected")
        else:
            for file in files:
                try:
                    with open(file, "r") as f:
                        codes = f.read()
                    #with
                    if len(codes) == 0:
                        self._error("file '%s' is empty" % file)
                    else:
                        _logger.info("adding file", file)
                        self.do_a(codes)
                    #else
                except FileNotFoundError:
                    self._error("file '%s' not found" % file)
                except PermissionError:
                    self._error("no read permission for file '%s'" % file)
                #except
            #for
        #else
        return False # on true, prompt loop will end
    #do_f


    def do_r(self, args) -> bool:
        """
        Implements RETRY command.
        :param args: ignored
        :return: False
        """
        czcode2.nop(args)
        self._checkKillSwitch()

        self._connector.send(msg.client.MsgRetry())
        return False # on true, prompt loop will end
    #do_r


    def do_d(self, args) -> bool:
        """
        Implements RETRY command.
        :param args: ignored
        :return: False
        """
        czcode2.nop(args)
        self._checkKillSwitch()

        self._connector.send(msg.client.MsgDiscard())
        return False # on true, prompt loop will end
    #do_d


    def do_l(self, args) -> bool:
        """
        Implements LIST command.
        :param args: ignored
        :return: False
        """
        czcode2.nop(args)
        self._checkKillSwitch()

        responseBuffer = queue.Queue()
        self._connector.send(msg.client.MsgList(responseBuffer))
        self._getResponse(responseBuffer)
        return False # on true, prompt loop will end
    #do_l


    def do_sls(self, args) -> bool:
        """
        Implements SESSION LS command.
        :param args: ignored
        :return: False
        """
        czcode2.nop(args)
        self._checkKillSwitch()

        responseBuffer = queue.Queue()
        self._connector.send(msg.client.MsgSessionList(responseBuffer))
        self._getResponse(responseBuffer)
        return False # on true, prompt loop will end
    #do_sls


    def do_sld(self, args) -> bool:
        """
        Implements SESSION LOAD command.
        :param args: ignored
        :return: False
        """
        czcode2.nop(args)
        self._checkKillSwitch()

        sessions = args.split()
        if len(sessions) == 0:
            self._error("add: YT code expected")
        else:
            response = queue.Queue(maxsize=1)
            for session in sessions:
                _logger.info("loading session", session)
                self._connector.send(msg.client.MsgLoadSession(session, response))
                self._getResponse(response)
            #for
        #else
        return False # on true, prompt loop will end
    #do_sld


    def do_sla(self, args) -> bool:
        """
        Implements SESSION LOAD ALL command.
        :param args: ignored
        :return: False
        """
        czcode2.nop(args)
        self._checkKillSwitch()

        responseBuffer = queue.Queue()
        self._connector.send(msg.client.MsgLoadAll(msg.client.LoadAllSelection.ALL,
                                                   responseBuffer))
        self._getResponse(responseBuffer)
        return False # on true, prompt loop will end
    #do_sls


    def do_slf(self, args) -> bool:
        """
        Implements SESSION LOAD FINISHED command.
        :param args: ignored
        :return: False
        """
        czcode2.nop(args)
        self._checkKillSwitch()

        responseBuffer = queue.Queue()
        self._connector.send(msg.client.MsgLoadAll(msg.client.LoadAllSelection.FINISHED_ONLY,
                                                   responseBuffer))
        self._getResponse(responseBuffer)
        return False # on true, prompt loop will end
    #do_slf


    def do_slp(self, args) -> bool:
        """
        Implements SESSION LOAD PENDING command.
        :param args: ignored
        :return: False
        """
        czcode2.nop(args)
        self._checkKillSwitch()

        responseBuffer = queue.Queue()
        self._connector.send(msg.client.MsgLoadAll(msg.client.LoadAllSelection.PENDING_ONLY,
                                                   responseBuffer))
        self._getResponse(responseBuffer)
        return False # on true, prompt loop will end
    #do_slp


    def do_q(self, args) -> bool:
        """
        Implements QUIT command.
        :param args: ignored
        :return: True
        """
        czcode2.nop(self, args)
        return True # on true, prompt loop will end
    #do_q


    def _checkKillSwitch(self):
        if self._killSwitch:
            raise KillSwitch
        #if
    #_checkKillSwitch


    def _messageLoop(self) -> None:
        while self._processingMessages:
            try:
                message = self._messages.get(block = True,
                                             timeout = self._messageWaitingTime)
                messageType = message.msgType()
                _logger.info(f"received {message}")
                if messageType == "MsgConnected":
                    pass
                elif messageType == "MsgDisconnected":
                    if self._cmdLoopRunning:
                        _logger.warning("connection to server interrupted; client has to close")
                        self._killSwitch = ("error: connection to server interrupted; client has "
                                            "to close\n")
                    #if
                elif messageType == "MsgResponse":
                    raise NotImplementedError
                else:
                    _logger.warning(f"don't know what to do with messages of type {messageType}")
                #else
            except queue.Empty:
                pass
            #except
        #while
    #_messageLoop


    def _error(self, *args) -> None:
        """
        Prints error message.
        """
        self.stdout.write("ERROR: ")
        self.stdout.write(' '.join(args))
        self.stdout.write("\n")
    #_error


    def _getResponse(self, responseBuffer: queue.Queue, multiLine=False) -> None:
        """
        Waits for a message (string) to be put into 'responseBuffer' and prints
        the message to STDOUT.
        In case of timeout, prints an error message.
        """

        # at least one response string must arrive
        try:
            self.stdout.write(
                responseBuffer.get(
                    block = True,
                    timeout = self._config.longResponseTimeout \
                        if multiLine else self._config.responseTimeout
                ))
            self.stdout.write("\n")
        except queue.Empty:
            self._error("server response timeout")
        #except

        # additional response strings are optional
        if multiLine:
            while True:
                try:
                    self.stdout.write(
                        responseBuffer.get(
                            block = True,
                            timeout = self._config.shortResponseTimeout))
                    self.stdout.write("\n")
                except queue.Empty:
                    return
                #except
            #while
        #if
    #_getResponse


    def _waitForResponse(self, queryID: int) -> None:
        """
        Waits for response message from the server and prints the message to
        STDOUT.

        In case of timeout, prints an error message.
        """
        pass
    #_waitForResponse

#Client


### aczutro ###################################################################
