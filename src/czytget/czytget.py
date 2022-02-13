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

from .config import parseConfig, setLoggingLevel as setLoggingLevelConfig
from .server import Server, setLoggingLevel as setLoggingLevelServer
from .client import Client, setLoggingLevel as setLoggingLevelClient
from czutils.utils import czlogging, czsystem, czthreading
import sys


def main():
    """
    Main routine of the czytget daemon/server.
    """
    logger = czlogging.LoggingChannel(czsystem.appName(),
                                      czlogging.LoggingLevel.WARNING)
    #czsystem.setLoggingLevel(czlogging.LoggingLevel.INFO)
    #czthreading.setLoggingLevel(czlogging.LoggingLevel.INFO)
    #setLoggingLevelConfig(czlogging.LoggingLevel.INFO)
    #setLoggingLevelClient(czlogging.LoggingLevel.INFO)
    setLoggingLevelServer(czlogging.LoggingLevel.INFO)

    try:
        serverConfig, clientConfig = parseConfig(".config/czytgetrc")
        logger.info(serverConfig)
        logger.info(clientConfig)

        server = Server(serverConfig)
        server.start()

        client = Client(clientConfig, server)
        client.start()

        server.wait()
        client.wait()
        sys.exit(0)
    except AssertionError as e:
        raise e
    # except ServerError as e:
    #     logger.error(e)
    #     sys.exit(1)
    except Exception as e:
        logger.error(e)
        sys.exit(2)
    #except
#autoStr


### aczutro ###################################################################
