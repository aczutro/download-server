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

"""Config for czytget."""

from czutils.utils import czcode, czlogging, czsystem
import configparser
import os
import os.path
import typing


_logger = czlogging.LoggingChannel("czytget.config",
                                   czlogging.LoggingLevel.SILENT,
                                   colour=True)


def setLoggingOptions(level: int, colour=True) -> None:
    """Sets this module's logging level and colour option.
    If not called, the logging level is SILENT.
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
class CommConfig:
    """
    Comm config:

    - ip:   string:    host IP
    - port: int:       port
    """
    def __init__(self):
        self.ip = "127.0.0.1"
        self.port = 4747
    #__init__


    def verify(self) -> None:
        """
        Checks if all values comply with the specs.
        :raises: ConfigError
        """
        if self.port < 1024:
            raise ConfigError("port must be > 1023")
        #if
    #verify


    def configDict(self) -> dict:
        """
        :returns: a dictionary that can be passed to configparser.ConfigParser()
                  to write this object's contents to file
        """
        return { "ip" : self.ip,
                 "port" : self.port
                 }
    #configDict


    def fromConfigParser(self, section: configparser.SectionProxy) -> None:
        """
        Reads values from provided section and stores them to member variables.
        """
        self.ip = section.get("ip")
        self.port = section.getint("port")

        if self.ip is None:
            raise ConfigError("field 'ip' not found")
        #if
        if self.port is None:
            raise ConfigError("field 'port' not found")
        #if
    #fromConfigParser

#ServerConfig


@czcode.autoStr
class ServerConfig:
    """
    Server config:

    - numThreads: int:    number of worker threads, must be > 0.
    - dataDir: string:    the directory where code files
                          are read from and stored to; it must exist
    - cookies: string:    path to cookie file
    - descriptions: bool: if True, download descriptions
    """
    def __init__(self):
        self.numThreads = 4
        self.dataDir = ""
        self.cookies = ""
        self.descriptions = True
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
    #verify


    def configDict(self) -> dict:
        """
        :returns: a dictionary that can be passed to configparser.ConfigParser()
                  to write this object's contents to file
        """
        return { "numthreads" : self.numThreads,
                 "datadir" : self.dataDir,
                 "cookies" : self.cookies,
                 "descriptions" : self.descriptions
                 }
    #configDict


    def fromConfigParser(self, section: configparser.SectionProxy) -> None:
        """
        Reads values from provided section and stores them to member variables.
        """
        self.numThreads = section.getint("numthreads")
        self.dataDir = section.get("datadir")
        self.cookies = section.get("cookies")
        self.descriptions = section.getboolean("descriptions")

        if self.numThreads is None:
            raise ConfigError("field 'numthreads' not found")
        #if
        if self.dataDir is None:
            raise ConfigError("field 'datadir' not found")
        #if
        if self.cookies is None:
            raise ConfigError("field 'cookies' not found")
        #if
        if self.descriptions is None:
            raise ConfigError("field 'descriptions' not found")
        #if
    #fromConfigParser

#ServerConfig


@czcode.autoStr
class ClientConfig:
    """
    Client config

    - responseTimeout: float:      Maximum number of seconds to wait for server
                                   response.  Since the server queues all
                                   commands to execute them asynchronously in a
                                   separate thread, the response should be very
                                   quick, and this is just a safety measure in
                                   case the server itself is not reachable.
                                   Must be > 0.
    - longResponseTimeout: float:  Maximum number of seconds to wait for server
                                   response, only for "add playlist" command,
                                   which is the only command not executed
                                   asynchronously in a separate thread; hence,
                                   this needs to be large enough to allow the
                                   client to wait for the info extraction of
                                   long playlists without the generation of
                                   false error messages.
                                   Must be > 0.
    - shortResponseTimeout: float: Maximum number of seconds to wait for further
                                   response lines (from the second line
                                   onwards), if a multi-line response is
                                   expected.
                                   Must be > 0.
    """

    def __init__(self):
        self.responseTimeout = 10. # seconds
        self.longResponseTimeout = 10 * 60. # seconds
        self.shortResponseTimeout = 2. # seconds
    #__init__


    def verify(self) -> None:
        """
        Checks if all values comply with the specs.
        :raises: ConfigError
        """
        if self.responseTimeout <= 0:
            raise ConfigError("client.responsetimeout must be > 0")
        #if
        if self.longResponseTimeout <= 0:
            raise ConfigError("client.longResponseTimeout must be > 0")
        #if
        if self.shortResponseTimeout <= 0:
            raise ConfigError("client.shortResponseTimeout must be > 0")
        #if
    #verify


    def configDict(self) -> dict:
        """
        :returns: a dictionary that can be passed to configparser.ConfigParser()
                  to write this object's contents to file
        """
        return { "responsetimeout" : self.responseTimeout,
                 "longresponsetimeout" : self.longResponseTimeout,
                 "shortresponsetimeout" : self.shortResponseTimeout
                 }
    #configDict


    def fromConfigParser(self, section: configparser.SectionProxy) -> None:
        """
        Reads values from provided section and stores them to member variables.
        """
        self.responseTimeout = section.getfloat("responsetimeout")
        self.longResponseTimeout = section.getfloat("longresponsetimeout")
        self.shortResponseTimeout = section.getfloat("shortresponsetimeout")

        if self.responseTimeout is None:
            raise ConfigError("field 'responsetimeout' not found")
        #if
        if self.longResponseTimeout is None:
            raise ConfigError("field 'longresponsetimeout' not found")
        #if
        if self.shortResponseTimeout is None:
            raise ConfigError("field 'shortresponsetimeout' not found")
        #if
    #fromConfigParser

#ClientConfig


def _makeDefaultConfig(configFile: str) -> typing.Tuple[ CommConfig, ServerConfig, ClientConfig ]:
    """
    Creates a default configuration and writes it to file configFile.

    :returns: ServerConfig and ClientConfig objects that contain the data
              written to file.
    """
    commConfig = CommConfig()

    serverConfig = ServerConfig()
    serverConfig.dataDir = os.path.dirname(configFile)
    serverConfig.cookies = os.path.join(serverConfig.dataDir, ".cookies")

    clientConfig = ClientConfig()

    writeConfig(configFile, commConfig, serverConfig, clientConfig)

    return commConfig, serverConfig, clientConfig
#_makeDefaultConfig


def writeConfig(configFile: str,
                commConfig: CommConfig,
                serverConfig: ServerConfig,
                clientConfig: ClientConfig) -> None:
    """
    Writes configurations to file.
    """
    configWriter = configparser.ConfigParser()

    configWriter["comm"] = commConfig.configDict()
    configWriter["server"] = serverConfig.configDict()
    configWriter["client"] = clientConfig.configDict()

    os.makedirs(os.path.dirname(configFile), exist_ok=True)
    with open(configFile, 'w') as configFile:
        configWriter.write(configFile)
    #with
#writeConfig


def parseConfig(configDir: str) -> tuple[CommConfig, ServerConfig, ClientConfig]:
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

    commConfig = None
    serverConfig = None
    clientConfig = None

    configReader = configparser.ConfigParser()
    configReader.read(configFile)

    if "comm" in configReader.sections():
        commConfig = CommConfig()
        try:
            commConfig.fromConfigParser(configReader["comm"])
            commConfig.verify()
        except Exception as e:
            raise ConfigError("bad comm config: %s" % e)
        #except
    #if

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

    return commConfig, serverConfig, clientConfig

#parseConfig


### aczutro ###################################################################
