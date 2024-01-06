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

"""Socket communicator."""
import collections

from czutils.utils import czthreading, czlogging, czcode
import queue
import socket
import threading
import time


_logger = czlogging.LoggingChannel("czutils.utils.czcommunicator",
                                   czlogging.LoggingLevel.SILENT,
                                   colour=True)


def setLoggingOptions(level: int, colour=True) -> None:
    """Sets this module's logging level and colour option.
    If not called, the logging level is SILENT.
    """
    global _logger
    _logger = czlogging.LoggingChannel("czutils.utils.czcommunicator",
                                       level, colour=colour)
#setLoggingOptions


class CommError(Exception):
    pass
#CommError


Packet = collections.namedtuple("Packet", "sender data")

class Subscriber:
    """Null subscriber (discards received data without action.

    You need one of these to instantiate a Communicator object.
    The communicator will call _cbkReceived every time it receives data from the
    socket.
    """
    def cbkReceived(self, packet: Packet) -> None:
        """Called by communicator to deliver data.
        Extend this class and override this function to fit your needs.

        :param packet: a tuple composed of the sender's ID (int) and the
                       received data (bytes).
        """
        _logger.info("subscriber receives:", packet)
    #_cbkReceived


    def cbkConnected(self, clientID: int) -> None:
        """Called by server-mode communicator when a client has connected.
        :param clientID: the client's ID
        """
        _logger.info("subscriber receives: client", clientID, "connected")
    #_cbkConnected


    def cbkDisconnected(self, clientID: int) -> None:
        """Called by server-mode communicator when a client has disconnected.
        :param clientID: the client's ID
        """
        _logger.info("subscriber receives: client", clientID, "disconnected")
    #_cbkDisconnected

#Subscriber


@czcode.autoStr
class CommConfig:
    """
    Comm config:

    - name : string     communicator name; used to name communicator threads
    - ip : string       socket IP
    - port : int:       socket port
    - packetSize : int  maximum number of bytes to request/send from/to socket
                        in one operations
    - timeout : float   maximum number of seconds to wait for data from socket
    - isServer : bool   if true, create socket; if false, connect to existing
                        socket
    """
    def __init__(self):
        self.name = ""
        self.ip = ""
        self.port = 0
        self.packetSize = 1024
        self.timeout = 2.0
        self.isServer = False
    #__init__
#CommConfig


def _addressToString(address: tuple) -> str:
    return f"{address[0]}:{address[1]}"
#_addressToString


class Communicator(czthreading.Thread):

    def __init__(self, conf: CommConfig, subscriber: Subscriber):
        super().__init__(conf.name)
        self._config = conf
        self._subscriber = subscriber
        self._connector = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._received = queue.Queue()
        self._threads = []
        try:
            if self._config.isServer:
                self._connector.bind((self._config.ip, self._config.port))
                self._connector.listen()
                self._connector.setblocking(False)
                self._connector.settimeout(self._config.timeout)
                self._connections = []
                self._lockConnections = threading.Lock()
            else:
                self._connector.connect((self._config.ip, self._config.port))
            #if
        except OSError as e:
            raise CommError(e)
        #except
    #__init__


    def threadCode(self) -> None:
        self._threads.append(threading.Thread(target=self._dispatch,
                                              name="dispatcher",
                                              daemon=True))
        self._threads[-1].start()

        if self._config.isServer:
            while self.running():
                try:
                    connection, address = self._connector.accept()
                    self._threads.append(
                        threading.Thread(target=self._receive,
                                         name=f"{self._config.name}:{_addressToString(address)}",
                                         daemon=True,
                                         args=(connection,)
                                         ))
                    self._threads[-1].start()
                except TimeoutError:
                    continue
                #except
            #while
        else:
            while self.running():
                time.sleep(1)
            #while
        #else

        self._connector.close()
        for thread in self._threads:
            thread.join()
        #for
    #threadCode


    def clientAddress(self, clientID: int) -> str:
        """
        :returns: the address of the client with ID clientID
        """
        if self._connections[clientID] is None:
            return f"client {clientID}"
        else:
            return _addressToString(self._connections[clientID].getpeername())
        #else
    #clientAddress


    def send(self, msg: str):
        if self.running():
            self._connector.sendall(msg.encode())
        #if
    #send


    def _receive(self, connection: socket.socket):
        connection.settimeout(self._config.timeout)
        self._lockConnections.acquire()
        clientID = len(self._connections)
        self._connections.append(connection)
        _logger.info("connections:", self._connections)
        self._lockConnections.release()
        self._subscriber.cbkConnected(clientID)

        while self.running():
            try:
                packet = connection.recv(self._config.packetSize)
                _logger.info(f"received {packet}")
            except TimeoutError:
                continue
            #except
            if packet == b"":
                break
            #if
            self._received.put(Packet(clientID, packet), block = True, timeout = None)
        #while

        connection.close()
        self._lockConnections.acquire()
        self._connections[clientID] = None
        _logger.info("connections:", self._connections)
        self._lockConnections.release()
        self._subscriber.cbkDisconnected(clientID)
    #_receive


    def _dispatch(self):
        while self.running():
            try:
                packet = self._received.get(block=True, timeout=self._config.timeout)
                _logger.info("dispatching", packet)
                self._subscriber.cbkReceived(packet)
            except queue.Empty:
                pass
            #except
        #while
    #_dispatch

#Communicator


### aczutro ###################################################################
