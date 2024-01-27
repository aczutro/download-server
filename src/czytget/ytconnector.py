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
from . import czcode2
from czutils.utils import czlogging, czcode
import contextlib
import io
import yt_dlp


_logger = czlogging.LoggingChannel("czytget.ytconnector",
                                   czlogging.LoggingLevel.SILENT,
                                   colour=True)

def setLoggingOptions(level: int, colour=True) -> None:
    """Sets this module's logging level and colour option.
    If not called, the logging level is SILENT.
    """
    global _logger
    _logger = czlogging.LoggingChannel("czytget.ytconnector", level, colour=colour)
#setLoggingOptions


class _YTLogger:
    """
    A logger to pass to yt_dlp.
    """

    def __init__(self):
        self._logger = czlogging.LoggingChannel("ytdlp",
                                                czlogging.LoggingLevel.SILENT,
                                                colour=True)
    #__init__

    def debug(self, msg, *args, **kwargs):
        czcode2.nop(args, kwargs)
        self._logger.info(msg)
    #debug

    def info(self, msg, *args, **kwargs):
        czcode2.nop(args, kwargs)
        self._logger.info(msg)
    #info

    def warning(self, msg, *args, **kwargs):
        czcode2.nop(args, kwargs)
        self._logger.warning(msg)
    #warning

    def error(self, msg, *args, **kwargs):
        czcode2.nop(args, kwargs)
        self._logger.error(msg)
    #error
#_YTLogger


class _YTListExtractor:
    """
    A logger to pass to yt_dlp.
    """

    def __init__(self):
        self._stdout = []
        self._stderr = []
    #__init__

    def debug(self, msg, *args, **kwargs):
        czcode2.nop(args, kwargs)
        self._stdout.append(msg)
    #debug

    def info(self, msg, *args, **kwargs):
        czcode2.nop(args, kwargs)
        self._stdout.append(msg)
    #info

    def warning(self, msg, *args, **kwargs):
        czcode2.nop(args, kwargs)
        self._stdout.append(msg)
    #warning

    def error(self, msg, *args, **kwargs):
        czcode2.nop(args, kwargs)
        self._stderr.append(msg)
    #error

    def stdout(self) -> list:
        return self._stdout
    #stdout

    def stderr(self) -> list:
        return self._stderr
    #stderr
#_YTLogger


@czcode.autoStr
class YTConfig:
    """
    Configuration passed to YTConnector:

    - cookies: path to the cookies file.
    - descriptions: if True, download descriptions.
    """

    def __self__(self):
        self.cookies = ""
        self.descriptions = True
    #__self__

#YTConfig


class YTConnector:
    """
    Interface to yt downloading library (currently yt_dlp).

    It needs to be instantiated in a 'with' statement in order to ensure that
    the cookie file is written correctly on exit.  Alternatively, call close()
    to force the closing of the back-end library (and thus the writing of the
    cookie file).
    """

    def __init__(self, config: YTConfig):
        ydlOptions = { "quiet": True,
                       "no_warnings": True,
                       "no_color": True,
                       "verbose": False,
                       "restrictfilenames": True,
                       "windowsfilenames": True,
                       "writedescription": config.descriptions,
                       "logger": _YTLogger(),
                       "cookiefile": config.cookies,
                       "updatetime": False }
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
        cookie file.  Not necessary if the YTConnector object is instantiated
        in a 'with' statement.

        DO NOT use download(...) after this.
        """
        if self._ydl is not None:
            self._ydl.__exit__()
            _logger.info("yt_dlp closed")
        #if
        self._ydl = None
    #close


    def download(self, ytCode: str) -> tuple[int, str]:
        """
        Downloads a YT code.
        :param ytCode: a valid YT code (individual video)
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


def _filter(lines: list) -> set:
    """
    Returns all yt codes contained in 'lines'.

    This greps for "Available formats for" to single out lines of the form
    "[info] Available formats for g2Tm7WZ1jPs:".
    Then extracts the code (the last word minus the colon).
    """
    ans = set()
    for line in lines:
        if "Available formats for" in line:
            ans.add(line.split()[-1][:-1])
        #if
    #for
    return ans
#_filter


def getYTList(ytCode: str, cookies: str) -> tuple[set, str]:
    """
    Treats 'ytCode' like a playlist and extract the codes of all individual
    videos.  Returns the codes as a set.

    :returns: If successful, returns [ <code set>, "" ].
              Else, [ None, <error description> ].
    """
    extractor = _YTListExtractor()
    ydlOptions = { "quiet": True,
                   "no_warnings": True,
                   "no_color": True,
                   "verbose": False,
                   "listformats": True,
                   "encoding": "utf-8",
                   "cookiefile": cookies,
                   "logger": extractor,
                   }

    formatInfo = io.StringIO()
    try:
        with contextlib.redirect_stdout(formatInfo):
            with yt_dlp.YoutubeDL(ydlOptions) as ytdl:
                if ytdl.download([ytCode]) != 0:
                    _logger.warning("yt_dlp failed to download", ytCode)
                    return None, "unknown yt_dlp failure"
                #if
            #with
        #with
    except yt_dlp.utils.YoutubeDLError as e:
        _logger.warning("yt_dlp failed to download %s:" % ytCode, e)
        return None, str(e)
    #except

    codes = _filter(extractor.stdout())

    if len(codes):
        return codes, ""
    else:
        return None, "successfully extracted list info, but list is empty"
    #else
#getYTList


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


### aczutro ###################################################################
