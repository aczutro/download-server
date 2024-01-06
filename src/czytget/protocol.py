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

from . import config, czcommunicator
from czutils.utils import czthreading, czlogging


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


class Protocol(czcommunicator.Communicator, czcommunicator.Subscriber):

    def __init__(self, conf: config.CommConfig, isServer: bool):
        commConfig = czcommunicator.CommConfig()
        commConfig.name = "czytgetServer" if isServer else "czytgetClient"
        commConfig.ip = conf.ip
        commConfig.port = conf.port
        commConfig.isServer = isServer
        czcommunicator.Subscriber.__init__(self)
        czcommunicator.Communicator.__init__(self, commConfig, self)
        self._isServer = isServer
    #__init__


    def cbkReceived(self, packet: czcommunicator.Packet) -> None:
        _logger.info("sender:", self.clientName(packet.sender))
        _logger.info("data:", packet.data)
        if self._isServer:
            self.send(packet.data, packet.sender)
        #if
    #_cbkReceived


    def cbkConnected(self, clientID: int) -> None:
        _logger.info(self.clientName(clientID), "connected")
    #_cbkConnected


    def cbkDisconnected(self, clientID: int) -> None:
        _logger.info(self.clientName(clientID), "disconnected")
    #_cbkDisconnected

#Protocol


### aczutro ###################################################################
