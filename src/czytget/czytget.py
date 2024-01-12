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

from . import protocol, config, server, client, ytconnector, czcommunicator
from czutils.utils import czlogging, czsystem, czthreading
import sys
import threading


def czytgetd():
    """Entry point for czytgetd.
    """
    logger = czlogging.LoggingChannel(czsystem.appName(),
                                      czlogging.LoggingLevel.WARNING)
    # czsystem.setLoggingOptions(czlogging.LoggingLevel.INFO)
    czthreading.setLoggingOptions(czlogging.LoggingLevel.INFO)
    # config.setLoggingOptions(czlogging.LoggingLevel.INFO)
    # czcommunicator.setLoggingOptions(czlogging.LoggingLevel.INFO)
    protocol.setLoggingOptions(czlogging.LoggingLevel.INFO)
    server.setLoggingOptions(czlogging.LoggingLevel.INFO)
    # client.setLoggingOptions(czlogging.LoggingLevel.INFO)
    # ytconnector.setLoggingOptions(czlogging.LoggingLevel.INFO)

    try:
        commConfig, serverConfig, clientConfig = config.parseConfig(".config/czytget2")
        logger.info(commConfig)
        logger.info(serverConfig)
        logger.info(clientConfig)
    except config.ConfigError as e:
        logger.error(e)
        sys.exit(1)
    #except

    try:
        theServer = server.Server(serverConfig, commConfig)
    except server.ServerError as e:
        logger.error(e)
        sys.exit(1)
    #except

    theServer.start()
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        theServer.stop()
    #except

    sys.exit(0)
#czytgetd


def czytget():
    """Entry point for czytget.
    """
    logger = czlogging.LoggingChannel(czsystem.appName(),
                                      czlogging.LoggingLevel.WARNING)
    # czsystem.setLoggingOptions(czlogging.LoggingLevel.INFO)
    # czthreading.setLoggingOptions(czlogging.LoggingLevel.INFO)
    # config.setLoggingOptions(czlogging.LoggingLevel.INFO)
    # czcommunicator.setLoggingOptions(czlogging.LoggingLevel.INFO)
    # protocol.setLoggingOptions(czlogging.LoggingLevel.INFO)
    # server.setLoggingOptions(czlogging.LoggingLevel.INFO)
    client.setLoggingOptions(czlogging.LoggingLevel.INFO)
    # ytconnector.setLoggingOptions(czlogging.LoggingLevel.INFO)


    try:
        commConfig, serverConfig, clientConfig = config.parseConfig(".config/czytget2")
        logger.info(commConfig)
        logger.info(serverConfig)
        logger.info(clientConfig)

        try:
            theClient = client.Client(clientConfig, commConfig)
        except client.ClientError as e:
            logger.error(e)
            sys.exit(1)
        #except

        theClient.start()
        theClient.wait()

        sys.exit(0)
    except config.ConfigError as e:
        logger.error(e)
        sys.exit(1)
    #except
#czytget


### aczutro ###################################################################
