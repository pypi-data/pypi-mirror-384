"""
Log management
"""

import mflog

mflog.add_override("cfgrib.*", "WARNING")
mflog.add_override("pint.util*", "ERROR")


class Logger:
    """Logger class wrapping created to dynamically create loggers
    it prevents fails when the mflog.set_config is changed during runtime
    after some logger have already been created.
    """

    def __init__(self, name: str, **bind_kwargs):
        self._name = name
        self._bind_kwargs = bind_kwargs

    @property
    def mflog(self):
        return mflog.getLogger(self._name)

    def _log(self, method: str, *args, **kwargs):
        """Default method triggering a logger creation and usage.

        Args:
            method: method to use. For instance, self._log("info", "toto")
                will display the INFO-level message "toto".
            *args: argument of the given method
            **kwargs: keyword arguments of the given method

        Returns:
            Any: returns the given method's return
        """
        logger = self.mflog.bind(**self._bind_kwargs)
        return getattr(logger, method)(*args, **kwargs)

    def debug(self, *args, **kwargs):
        return self._log("debug", *args, **kwargs)

    def info(self, *args, **kwargs):
        return self._log("info", *args, **kwargs)

    def warning(self, *args, **kwargs):
        return self._log("warning", *args, **kwargs)

    def error(self, *args, **kwargs):
        return self._log("error", *args, **kwargs)

    def exception(self, *args, **kwargs):
        return self._log("exception", *args, **kwargs)

    def critical(self, *args, **kwargs):
        return self._log("critical", *args, **kwargs)

    def bind(self, *args, **kwargs):
        return self._log("bind", *args, **kwargs)

    def try_unbind(self, *args, **kwargs):
        return self._log("try_unbind", *args, **kwargs)


def get_logger(name: str, **kwargs) -> Logger:
    return Logger(name=name, **kwargs)
