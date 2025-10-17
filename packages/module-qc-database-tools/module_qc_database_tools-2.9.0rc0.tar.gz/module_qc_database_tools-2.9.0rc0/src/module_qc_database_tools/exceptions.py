from __future__ import annotations


class JsonParsingError(Exception):
    """JSON parsing error"""


class ConfigError(Exception):
    """Config error"""


class DBServiceError(Exception):
    """Error with DB"""


class DBConnectionError(Exception):
    """Error in DB connection"""


class DBAuthenticationFailure(Exception):
    """Error in DB authentication"""


class ViewerConnectionError(Exception):
    """Error in viewer connection"""


class RegisterError(Exception):
    """Error in registering"""


class ValidationError(Exception):
    """Error in validating"""


class DcsDataError(Exception):
    """Error in accessing DCS data"""


class MissingData(Exception):
    """Error when data is missing"""


class CommandError(Exception):
    """Error in running a command"""


class DataError(ValueError):
    """General data error"""


class InteractiveExit(Exception):
    """Error when exiting via interactive"""


class SkipCheck(Exception):
    """Raised when we need to skip a check"""
