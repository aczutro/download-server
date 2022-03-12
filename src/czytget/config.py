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

from czutils.utils import czcode, czlogging, czsystem
import configparser
import os
import os.path
import typing


_logger = czlogging.LoggingChannel("czytget.config",
                                   czlogging.LoggingLevel.SILENT,
                                   colour=True)

def setLoggingOptions(level: int, colour=True) -> None:
    """
    Sets this module's logging level.  If not called, the logging level is
    SILENT.

    :param level: One of the following:
                  - czlogging.LoggingLevel.INFO
                  - czlogging.LoggingLevel.WARNING
                  - czlogging.LoggingLevel.ERROR
                  - czlogging.LoggingLevel.SILENT

    :param colour: If true, use colour in log headers.
    """
    global _logger
    _logger = czlogging.LoggingChannel("czytget.config", level, colour=colour)

#setLoggingOptions


class ConfigError(Exception):
    """
    Exception class thrown by parseConfig
    """
    def __init__(self, what: str):
        super().__init__(what)
    #__init__

#ConfigError


@czcode.autoStr
class ServerConfig:
    """
    Server config:

    - numThreads: int: number of worker threads, must be > 0.
    - dataDir: string: the directory where code files
                       are read from and stored to; it must exist
    """
    def __init__(self):
        self.numThreads = 4
        self.dataDir = ""
        self.cookies = ""
    #__init__


    def verify(self) -> None:
        """
        Checks if all values comply with the specs.  It also creates the data
        directory if necessary.
        :raises: ConfigError
        """
        if self.numThreads < 1:
            raise ConfigError("server.numthreads must be > 0")
        #if
        if not os.path.exists(self.dataDir):
            try:
                os.makedirs(self.dataDir, exist_ok=True)
            except OSError as e:
                errorString = "ServerConfig: cannot create data dir '%s': %s" \
                              % (self.dataDir, e)
                _logger.error(errorString)
                raise ConfigError(errorString)
            #except
        else:
            if not os.path.isdir(self.dataDir):
                errorString = "ServerConfig: '%s' exists, but is not a directory" \
                              % self.dataDir
                _logger.error(errorString)
                raise ConfigError(errorString)
            #if
        #else
        if os.path.exists(self.cookies):
            if os.path.isdir(self.cookies):
                errorString = "ServerConfig: '%s' exists, but is not a directory" \
                              % self.cookies
                _logger.error(errorString)
                raise ConfigError(errorString)
            #if
        #if
    #check


    def configDict(self) -> dict:
        """
        :returns: a dictionary that can be passed to configparser.ConfigParser()
                  to write this object's contents to file
        """
        return { "numthreads" : self.numThreads,
                 "datadir" : self.dataDir,
                 "cookies" : self.cookies
                 }
    #configDict


    def fromConfigParser(self, section: configparser.SectionProxy) -> None:
        """
        Reads values from provided section and stores them to member variables.
        """
        self.numThreads = section.getint("numthreads")
        self.dataDir = section.get("datadir")
        self.cookies = section.get("cookies")

        if self.numThreads is None:
            raise ConfigError("field 'numthreads' not found")
        #if
        if self.dataDir is None:
            raise ConfigError("field 'datadir' not found")
        #if
        if self.cookies is None:
            raise ConfigError("field 'cookies' not found")
        #if
    #fromConfigParser

#ServerConfig


@czcode.autoStr
class ClientConfig:
    """
    Client config

    - responseTimeout: float: maximum number of seconds to wait for server
                              response, must be > 0.
    """

    def __init__(self):
        self.responseTimeout = 10. # seconds
    #__init__


    def verify(self) -> None:
        """
        Checks if all values comply with the specs.
        :raises: ConfigError
        """
        if self.responseTimeout <= 0:
            raise ConfigError("client.responsetimeout must be > 0")
        #if
    #check


    def configDict(self) -> dict:
        """
        :returns: a dictionary that can be passed to configparser.ConfigParser()
                  to write this object's contents to file
        """
        return { "responsetimeout" : self.responseTimeout }
    #configDict


    def fromConfigParser(self, section: configparser.SectionProxy) -> None:
        """
        Reads values from provided section and stores them to member variables.
        """
        self.responseTimeout = section.getfloat("responsetimeout")

        if self.responseTimeout is None:
            raise ConfigError("field 'responsetimeout' not found")
        #if
    #fromConfigParser

#ClientConfig


def _makeDefaultConfig(configFile: str) -> typing.Tuple[ ServerConfig, ClientConfig ]:
    """
    Creates a default configuration and writes it to file configFile.

    :returns: ServerConfig and ClientConfig objects that contain the data
              written to file.
    """
    serverConfig = ServerConfig()
    serverConfig.dataDir = os.path.dirname(configFile)
    serverConfig.cookies = os.path.join(serverConfig.dataDir, ".cookies")

    clientConfig = ClientConfig()

    writeConfig(configFile, serverConfig, clientConfig)

    return serverConfig, clientConfig
#_makeDefaultConfig


def writeConfig(configFile: str,
                serverConfig: ServerConfig,
                clientConfig: ClientConfig) -> None:
    """
    Writes configurations to file.
    """
    configWriter = configparser.ConfigParser()

    configWriter["server"] = serverConfig.configDict()
    configWriter["client"] = clientConfig.configDict()

    os.makedirs(os.path.dirname(configFile), exist_ok=True)
    with open(configFile, 'w') as configFile:
        configWriter.write(configFile)
    #with
#writeConfig


def parseConfig(configDir: str) -> tuple[ServerConfig, ClientConfig]:
    """
    Parses file '.config' in directory configDir, and returns
    ServerConfig and ClientConfig objects that contain the parsed data.

    :param configDir: Full path to config directory.  If not an absolute path,
                      understands it relative to ${HOME}.  If the HOME
                      environment variable is not defined, understands it
                      relative to the execution directory.
    :return:
    """
    configDirFullPath = czsystem.resolveAbsPath(configDir)
    configFile = os.path.join(configDirFullPath, ".config")
    _logger.info("parsing file", configFile)

    if not os.path.exists(configFile):
        return _makeDefaultConfig(configFile)
    #if

    serverConfig = None
    clientConfig = None

    configReader = configparser.ConfigParser()
    configReader.read(configFile)

    if "server" in configReader.sections():
        serverConfig = ServerConfig()
        try:
            serverConfig.fromConfigParser(configReader["server"])
            serverConfig.verify()
        except Exception as e:
            raise ConfigError("bad server config: %s" % e)
        #except
    #if

    if "client" in configReader.sections():
        clientConfig = ClientConfig()
        try:
            clientConfig.fromConfigParser(configReader["client"])
            clientConfig.verify()
        except Exception as e:
            raise ConfigError("bad client config: %s" % e)
        #except
    #if

    return serverConfig, clientConfig

#parseConfig


### aczutro ###################################################################
