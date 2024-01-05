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


_nullSubscriber = czcommunicator.Subscriber()


class CommServer(czcommunicator.Communicator):

    def __init__(self, conf: config.CommConfig):
        commConfig = czcommunicator.CommConfig()
        commConfig.name = "czytgetServer"
        commConfig.ip = conf.ip
        commConfig.port = conf.port
        commConfig.isServer = True
        super().__init__(commConfig, _nullSubscriber)
    #__init__

#CommunicatorServer


class CommClient(czcommunicator.Communicator):

    def __init__(self, conf: config.CommConfig):
        commConfig = czcommunicator.CommConfig()
        commConfig.name = "czytgetClient"
        commConfig.ip = conf.ip
        commConfig.port = conf.port
        commConfig.isServer = False
        super().__init__(commConfig, _nullSubscriber)
    #__init__

#CommunicatorClient


### aczutro ###################################################################
