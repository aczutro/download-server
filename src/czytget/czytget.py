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

from .config import parseConfig, ConfigError, setLoggingOptions as setLoggingOptionsConfig
from .server import Server, setLoggingOptions as setLoggingOptionsServer
from .client import Client, setLoggingOptions as setLoggingOptionsClient
from czutils.utils import czlogging, czsystem, czthreading
import sys


def czytget():
    """Entry point for czytget.
    """
    logger = czlogging.LoggingChannel(czsystem.appName(),
                                      czlogging.LoggingLevel.WARNING)
    #czsystem.setLoggingOptions(czlogging.LoggingLevel.INFO)
    #czthreading.setLoggingOptions(czlogging.LoggingLevel.INFO)
    #setLoggingOptionsConfig(czlogging.LoggingLevel.INFO)
    #setLoggingOptionsClient(czlogging.LoggingLevel.INFO)
    #setLoggingOptionsServer(czlogging.LoggingLevel.INFO)
    #setLoggingOptionsYTConnector(czlogging.LoggingLevel.INFO)

    try:
        commConfig, serverConfig, clientConfig = parseConfig(".config/czytget")
        logger.info(commConfig)
        logger.info(serverConfig)
        logger.info(clientConfig)

        server = Server(serverConfig)
        #server.start()

        client = Client(clientConfig, server)
        client.start()

        #server.wait()
        client.wait()

        sys.exit(0)
    except ConfigError as e:
        logger.error(e)
        sys.exit(1)
    except Exception as e:
       logger.error("unexpected exception:", e)
       #raise e
       sys.exit(2)
    #except
#czytget


def czytgetd():
    """Entry point for czytgetd.
    """
    logger = czlogging.LoggingChannel(czsystem.appName(),
                                      czlogging.LoggingLevel.WARNING)
    #czsystem.setLoggingOptions(czlogging.LoggingLevel.INFO)
    #czthreading.setLoggingOptions(czlogging.LoggingLevel.INFO)
    #setLoggingOptionsConfig(czlogging.LoggingLevel.INFO)
    #setLoggingOptionsClient(czlogging.LoggingLevel.INFO)
    #setLoggingOptionsServer(czlogging.LoggingLevel.INFO)
    #setLoggingOptionsYTConnector(czlogging.LoggingLevel.INFO)

    try:
        commConfig, serverConfig, clientConfig = parseConfig(".config/czytget")
        logger.info(commConfig)
        logger.info(serverConfig)
        logger.info(clientConfig)

        server = Server(serverConfig)
        server.start()
        server.wait()

        sys.exit(0)
    except ConfigError as e:
        logger.error(e)
        sys.exit(1)
    except Exception as e:
        logger.error("unexpected exception:", e)
        #raise e
        sys.exit(2)
    #except
#czytgetd


### aczutro ###################################################################
