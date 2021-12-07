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

"""A simple server to execute multiple parallel download jobs."""

from .commandline import CommandLineParser
from .server import Server, ServerError
from czutils.utils import czlogging, czsystem
import sys

def mainServer():
    """
    Main routine of the czytget daemon/server.
    """
    L = czlogging.LogChannel(czsystem.appName())
    try:
        CLP = CommandLineParser()
        args = CLP.parseCommandLine()
        L.info(args)
        S = Server()
        S.start()
        S.wait()
        sys.exit(0)
    except AssertionError as e:
        raise e
    except ServerError as e:
        L.error(e)
        sys.exit(1)
    except Exception as e:
        L.error(e)
        sys.exit(2)
    #except
#autoStr


### aczutro ###################################################################
