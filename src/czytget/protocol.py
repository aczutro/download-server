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

"""Communicator for czytgetd and czytget"""

from . import config, czcommunicator, msg
from .msg import protocol
from czutils.utils import czthreading, czlogging
import queue


_logger = czlogging.LoggingChannel("czytget.protocol",
                                   czlogging.LoggingLevel.SILENT,
                                   colour=True)


def setLoggingOptions(level: int, colour=True) -> None:
    """Sets this module's logging level and colour option.
    If not called, the logging level is SILENT.
    """
    global _logger
    _logger = czlogging.LoggingChannel("czytget.protocol", level, colour=colour)
#setLoggingOptions


class Protocol(czthreading.Thread, czcommunicator.Subscriber):

    def __init__(self,
                 conf: config.CommConfig,
                 isServer: bool,
                 subscriber: czthreading.ReactiveThread):
        name = "czytget.server" if isServer else "czytget.client"
        commConfig = czcommunicator.CommConfig()
        commConfig.name = f"{name}.comm"
        commConfig.ip = conf.ip
        commConfig.port = conf.port
        commConfig.isServer = isServer
        czthreading.Thread.__init__(self, f"{name}.protocol")
        czcommunicator.Subscriber.__init__(self)
        self._communicator = czcommunicator.Communicator(commConfig, self)
        self._serialiser = czcommunicator.Serialiser()
        self._subscriber = subscriber
        self._received = queue.Queue()
        self._timeout = 2.0
    #__init__


    def cbkReceived(self, packet: czcommunicator.Packet) -> None:
        _logger.info("sender:", self._communicator.clientName(packet.sender))
        _logger.info("data:", packet.data)
        self._received.put(packet, block = True, timeout = None)
    #_cbkReceived


    def cbkConnected(self, clientID: int) -> None:
        _logger.info(self._communicator.clientName(clientID), "connected")
        if self._subscriber:
            self._subscriber.comm(msg.protocol.MsgConnected(clientID))
        #if
    #_cbkConnected


    def cbkDisconnected(self, clientID: int) -> None:
        _logger.info(self._communicator.clientName(clientID), "disconnected")
        if self._subscriber:
            self._subscriber.comm(msg.protocol.MsgDisconnected(clientID))
        #if
    #_cbkDisconnected


    def start(self) -> None:
        czthreading.Thread.start(self)
        self._communicator.start()
    #start


    def stop(self) -> None:
        czthreading.Thread.stop(self)
        self._communicator.stop()
    #start


    def threadCode(self) -> None:
        while self.running():
            try:
                packet = self._received.get(block=True, timeout=self._timeout)
                decoded = self._serialiser.addAndDecode(packet.data, packet.sender)
                if decoded is None:
                    _logger.warning(f"{decoded} is not a valid message; discarding")
                else:
                    if issubclass(type(decoded), czthreading.Message):
                        _logger.info(f"sending '{decoded}' to subscriber")
                        if self._subscriber:
                            self._subscriber.comm(decoded)
                        #if
                    else:
                        _logger.warning(f"{decoded} is not a valid message; discarding")
                    #else
                #if
            except queue.Empty:
                pass
            #except
        #while
    #threadCode


    def send(self, message: czthreading.Message, clientID: int | None = None) -> None:
        self._communicator.send(self._serialiser.encode(message), clientID)
    #send

#Protocol


### aczutro ###################################################################
