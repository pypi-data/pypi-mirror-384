import inspect
import importlib.metadata 
import logging
import string.templatelib
import tstring

__version__ =  importlib.metadata.version('template-string-logger')


class TStringLogger(logging.Logger):
    """
    Custom logger that inteprets t-string when the logging levl is active
    """

    def debug(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.DEBUG):
            self._log(logging.DEBUG, self._parse_t(msg), args, **kwargs)

    def info(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.INFO):
            self._log(logging.INFO, self._parse_t(msg), args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.WARNING):
            self._log(logging.WARNING, self._parse_t(msg), args, **kwargs)

    def error(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.ERROR):
            self._log(logging.ERROR, self._parse_t(msg), args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.CRITICAL):
            self._log(logging.CRITICAL, self._parse_t(msg), args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        if not isinstance(level, int):
            raise TypeError("level must be an integer")
        if self.isEnabledFor(level):
            self._log(level, msg, args, **kwargs)

    def _parse_t(self, msg):
        if not isinstance(msg, string.templatelib.Template):
            return msg
        frame = inspect.currentframe()
        while frame:
            mod = frame.f_globals.get("__name__")
            if not (mod and mod.startswith("tstring_logger")):
                break
            frame = frame.f_back
        ctx = frame.f_globals | frame.f_locals if frame else {}
        return tstring.embed(msg, ctx)

logging.setLoggerClass(TStringLogger)
