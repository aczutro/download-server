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

from .config import ClientConfig
from .messages import *
from .server import Server
from czutils.utils import czlogging, czthreading
import cmd


_logger = czlogging.LoggingChannel("czytget.client",
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
    _logger = czlogging.LoggingChannel("czytget.client", level, colour=colour)

#setLoggingOptions


class Client(czthreading.Thread, cmd.Cmd):
    """
    An "integrated" czytget client that talks directly with the server via
    message passing (without additional protocol).  Meant to run in the same
    process as the server.

    Offers a basic shell (command prompt loop).
    """

    def __init__(self, config: ClientConfig, server: Server):
        super().__init__("czytget-client")
        self._config = config
        self._server = server

    #__init__


    def threadCode(self):
        self.prompt = "\nczytget> "
        self.intro = "\nIntegrated czytget client"\
                     "\n=========================\n" \
                     "\nType 'help' or '?' to list commands."
        self.cmdloop()

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
        self.stdout.write("\nslp     'Session Load Pending': load all available sessions,")
        self.stdout.write("\n        but only unfinished codes")
        self.stdout.write("\n")
        self.stdout.write("\nq       terminate the server and the client")
        self.stdout.write("\n")
        return False # on true, prompt loop will end

    #do_help


    def do_a(self, args: str) -> bool:
        """
        Implements the ADD command.
        :param args: space-separated list of YT codes.
        :return: False
        """
        codes = args.split()
        if len(codes) == 0:
            self._error("add: YT code expected")
        else:
            response = queue.Queue(maxsize=1)
            for ytCode in codes:
                if len(ytCode) == 11:
                    _logger.info("adding code", ytCode)
                    self._server.comm(MsgAddCode(ytCode, response))
                    self._getResponse(response)
                elif len(ytCode) == 34:
                    _logger.info("adding code", ytCode)
                    self._server.comm(MsgAddList(ytCode, response))
                    self._getResponse(response, multiLine=True)
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
        self._server.comm(MsgRetry())
        return False # on true, prompt loop will end
    #do_r


    def do_d(self, args) -> bool:
        """
        Implements RETRY command.
        :param args: ignored
        :return: False
        """
        self._server.comm(MsgDiscard())
        return False # on true, prompt loop will end
    #do_d


    def do_l(self, args) -> bool:
        """
        Implements LIST command.
        :param args: ignored
        :return: False
        """
        responseBuffer = queue.Queue()
        self._server.comm(MsgList(responseBuffer))
        self._getResponse(responseBuffer)
        return False # on true, prompt loop will end
    #do_l


    def do_sls(self, args) -> bool:
        """
        Implements SESSION LS command.
        :param args: ignored
        :return: False
        """
        responseBuffer = queue.Queue()
        self._server.comm(MsgSessionList(responseBuffer))
        self._getResponse(responseBuffer)
        return False # on true, prompt loop will end
    #do_sls


    def do_sld(self, args) -> bool:
        """
        Implements SESSION LOAD command.
        :param args: ignored
        :return: False
        """
        sessions = args.split()
        if len(sessions) == 0:
            self._error("add: YT code expected")
        else:
            response = queue.Queue(maxsize=1)
            for session in sessions:
                _logger.info("loading session", session)
                self._server.comm(MsgLoadSession(session, response))
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
        responseBuffer = queue.Queue()
        self._server.comm(MsgLoadAll(False, responseBuffer))
        self._getResponse(responseBuffer)
        return False # on true, prompt loop will end
    #do_sls


    def do_slp(self, args) -> bool:
        """
        Implements SESSION LOAD PENDING command.
        :param args: ignored
        :return: False
        """
        responseBuffer = queue.Queue()
        self._server.comm(MsgLoadAll(True, responseBuffer))
        self._getResponse(responseBuffer)
        return False # on true, prompt loop will end
    #do_sls


    def do_q(self, args) -> bool:
        """
        Implements QUIT command.
        :param args: ignored
        :return: True
        """
        _logger.info("terminating server")
        self._server.comm(czthreading.QuitMessage())
        return True # on true, prompt loop will end
    #do_q


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

#Client


### aczutro ###################################################################
