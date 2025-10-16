from mfire.settings import get_logger

# Logging
LOGGER = get_logger(name="exception.mod")


class PrometheeError(Exception):
    """Base class for Promethee's custom exceptions."""

    def __init__(self, err, **kwargs):
        self.err = err
        for key, value in kwargs.items():
            if value is None:
                continue
            try:
                self.err += " {}={}.".format(key, value)
            except Exception:
                LOGGER.error(
                    "Exception caught in PrometheeError execution", exc_info=True
                )
        super().__init__(self.err)


class ConfigurationError(PrometheeError):
    """Raised when a wrong configuration has been given."""


class LoaderError(Exception):
    """Exception raised for loader errors."""


class LocalisationError(ValueError, PrometheeError):
    """Raised when a error on localisation has been given."""


class LocalisationWarning(ValueError, PrometheeError):
    """Raised when no localisation is made but it maybe the case."""


class ConfigurationWarning(PrometheeError):
    """Raised when a misformed configuration has been given"""


class GribError(PrometheeError):
    """Raised when error in grib reader"""


class DataPreprocessingError(PrometheeError):
    """Raised when error in cumul data"""
