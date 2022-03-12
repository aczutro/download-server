# Copyright (C) 2022 - present  Alexander Czutro <github@czutro.ch>
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

"""interface to yt downloading library"""
import logging

from czutils.utils import czlogging, czcode
import yt_dlp


_logger = czlogging.LoggingChannel("czytget.ytconnector",
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
    _logger = czlogging.LoggingChannel("czytget.ytconnector", level, colour=colour)

#setLoggingOptions


class _YTLogger(logging.Logger):
    """
    A logger to pass to yt_dlp.
    """

    def __init__(self):
        super().__init__("yt_dlp", level=logging.NOTSET)
        self._logger = czlogging.LoggingChannel("ytdlp",
                                                czlogging.LoggingLevel.ERROR,
                                                colour=True)
    #__init__

    def info(self, msg, *args, **kwargs):
        self._logger.info(msg)
    #info

    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg)
    #warning

    def error(self, msg, *args, **kwargs):
        self._logger.error(msg)
    #error

#_YTLogger


@czcode.autoStr
class YTConfig:
    def __self__(self):
        self.cookies = ""
        self.descriptions = True
    #__self__

#YTConfig


class YTConnector:
    """
    Interface to yt downloading library.
    """

    def __init__(self, config: YTConfig):
        ydlOptions = { "quiet": True,
                       "no_warnings": True,
                       "no_color": True,
                       "restrictfilenames": True,
                       "windowsfilenames": True,
                       "writedescription": config.descriptions,
                       "logger": _YTLogger(),
                       "logtostderr": True,
                       "cookiefile": config.cookies }
        self._ydl = yt_dlp.YoutubeDL(ydlOptions)
    #__init__


    def __del__(self):
        self.close()
    #__del__


    def __enter__(self):
        return self
    #__enter__


    def __exit__(self, *args):
        self.close()
    #__exit__


    def close(self) -> None:
        """
        Closes the downloader, in particular forcing it to write the
        cookies file.  Not necessary if the YTConnector object is instantiated
        in a with statement.

        DO NOT use download(...) after this.
        """
        if self._ydl is not None:
            self._ydl.__exit__()
            #_logger.info("yt_dlp closed")
        #if
        self._ydl = None
    #close


    def download(self, ytCode: str) -> tuple[int, str]:
        """
        Downloads a YT code.
        :param ytCode: a valid YT code
        :return: If successful, [ True, "" ].
                 Else, [ False, <error description> ].
        """
        try:
            exitCode = self._ydl.download([ytCode])
            if exitCode == 0:
                _logger.info("yt_dlp successfully downloaded", ytCode)
                return True, ""
            else:
                _logger.warning("yt_dlp failed to download", ytCode)
                return False, "unknown yt_dlp failure"
            #else
        except yt_dlp.utils.YoutubeDLError as e:
            _logger.warning("yt_dlp failed to download %s:" % ytCode, e)
            return False, str(e)
        #except
    #download

#YTConnector


def mergeCookieFiles(outputFile: str, *filenames) -> None:
    """
    Merges all cookies found in the input files and writes them to one
    single cookie file.

    :param outputFile: output file
    :param filenames: input files
    """
    with open(outputFile, "w") as ofile:
        ofile.write("# Netscape HTTP Cookie File\n")
        for inputFile in filenames:
            with open(inputFile, "r") as ifile:
                for line in ifile:
                    if len(line):
                        if line[0] != '#':
                            ofile.write(line)
                        #if
                    #if
                #for
            #with
        #for
    #with
    ytConfig = YTConfig()
    ytConfig.cookies = outputFile
    ytConfig.descriptions = False
    with YTConnector(ytConfig):
        pass
    #with
#mergeCookieFiles
