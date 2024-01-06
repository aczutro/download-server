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

from czutils.utils import czthreading, czlogging, czcode
import collections
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
    """Null subscriber (discards received data without action).

    You need one of these to instantiate a Communicator object.
    Derive from this class and override the callback functions to fit your
    needs.

    The communicator will call cbkReceived every time it receives data from the
    socket.  It will also call cbkConnected or cbkDisconnected every
    time a client connects or disconnects, respectively.
    """
    def cbkReceived(self, packet: Packet) -> None:
        """Called by the communicator to deliver data.

        :param packet: a tuple composed of the sender's ID (int) and the
                       received data (bytes).
        """
        _logger.info("subscriber receives:", packet)
    #cbkReceived


    def cbkConnected(self, clientID: int) -> None:
        """Called by the communicator when a client has connected.

        :param clientID: the client's ID
        """
        _logger.info("subscriber receives: client", clientID, "connected")
    #cbkConnected


    def cbkDisconnected(self, clientID: int) -> None:
        """Called by the communicator when a client has disconnected.

        :param clientID: the client's ID
        """
        _logger.info("subscriber receives: client", clientID, "disconnected")
    #cbkDisconnected

#Subscriber


@czcode.autoStr
class CommConfig:
    """
    Configuration for the instantiation of Communicator objects

    :ivar name:       (str) communicator name; used to name communicator
                      threads
    :ivar ip:         (str) socket IP
    :ivar port:       (int) socket port
    :ivar packetSize: (int) maximum number of bytes to request/send from/to
                      socket in one operation
    :ivar timeout:    (float) maximum number of seconds to wait for data from
                      socket
    :ivar isServer:   if true, run in server mode; else, run in client mode
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
    """
    :param address: tuple composed of an address (str) and a port (int)

    :returns: string of the form "address:port"
    """
    return f"{address[0]}:{address[1]}"
#_addressToString


class Communicator(czthreading.Thread):
    """A socket communicator.

    In server mode, creates a socket, listens for connections and manages
    connections.

    In client mode, connects to an existing socket.

    In both modes, sends incoming data to a subscriber using the Subscriber
    class's callback functions.  It also sends a message every time a client
    connects or disconnects.

    Both modes offer a send function to send messages back to the clients or the
    server.

    :param conf:       the communicator's configuration
    :param subscriber: the subscriber object that will receive data and
                       connection updates

    :raises: CommError
    """
    def __init__(self, conf: CommConfig, subscriber: Subscriber):
        super().__init__(conf.name)
        self._config = conf
        self._subscriber = subscriber
        self._connector = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._received = queue.Queue()
        self._threads = []
        self._connections = []
        self._lockConnections = threading.Lock()
        try:
            if self._config.isServer:
                self._connector.bind((self._config.ip, self._config.port))
                self._connector.listen()
                self._connector.settimeout(self._config.timeout)
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
            self._connector.close()
        else:
            self._receive(self._connector)
        #else

        for thread in self._threads:
            thread.join()
        #for
    #threadCode


    def clientName(self, clientID: int) -> str:
        """
        :returns: the name (address) of the client with ID clientID
        """
        with self._lockConnections:
            if self._connections[clientID] is None:
                return f"client {clientID}"
            else:
                return _addressToString(self._connections[clientID].getpeername())
            #else
        #with
    #clientAddress


    def send(self, msg: bytes, clientID: int | None = None) -> None:
        """Sends a message.

        :param msg:      A non-empty message.
        :param clientID: In server mode, ID of the client to send the message
                         to, or None, in which it will be sent to all clients.
                         Ignored in client mode.

        :raises: ValueError
        """
        if msg == b"":
            raise ValueError
        #if

        if self.running():
            if self._config.isServer:
                with self._lockConnections:
                    if clientID is None:
                        for connection in self._connections:
                            if connection is not None:
                                connection.sendall(msg)
                            #if
                        #for
                    elif clientID < 0 or clientID >= len(self._connections):
                        raise ValueError
                    elif self._connections[clientID] is None:
                        _logger.warning("connection to client", clientID,
                                        "has been closed; not sending message", msg)
                    else:
                        self._connections[clientID].sendall(msg)
                    #else
                #with
            else:
                if clientID is not None:
                    _logger.warning("operating in client mode; send(...) ignoring clientID")
                #if
                if self._connector.fileno() == -1:
                    _logger.warning("connection to server closed; cannot send message")
                else:
                    self._connector.sendall(msg)
                #else
            #else
        else:
            _logger.warning("communicator not running; not sending message", msg)
        #if
    #send


    def _receive(self, connection: socket.socket):
        connection.settimeout(self._config.timeout)
        with self._lockConnections:
            clientID = len(self._connections)
            self._connections.append(connection)
            _logger.info("connections:", self._connections)
        #with
        self._subscriber.cbkConnected(clientID)

        while self.running():
            try:
                packet = connection.recv(self._config.packetSize)
                _logger.info(f"received {packet}")
            except TimeoutError:
                continue
            except OSError:
                continue
            #except
            if packet == b"":
                break
            #if
            self._received.put(Packet(clientID, packet), block = True, timeout = None)
        #while

        connection.close()
        with self._lockConnections:
            self._connections[clientID] = None
            _logger.info("connections:", self._connections)
        #with
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
