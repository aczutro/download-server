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

"""Config and command line parsing for czytget."""

import czutils.utils.czcode


@czutils.utils.czcode.autoStr
class ServerConfig:
    """server config"""

    def __init__(self):
        self.numThreads = 4
    #__init__

    def parseCommandLine(self):
        pass
    #parseCommandLine

#ServerConfig


@czutils.utils.czcode.autoStr
class ClientConfig:
    """client config"""

    def __init__(self):
        self.responseTimeout = 10 # seconds
    #__init__

#ClientConfig


### aczutro ###################################################################
