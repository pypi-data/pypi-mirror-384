from enum import Enum, unique


# Symbols for referencing Mime types
class MimeTypes(Enum):
    TextPlain = ("text/plain")
    ImagePng = ("image/png")
    S3URI = ("text/uri-list")


# Symbols for referencing session types
@unique
class SessionType(Enum):

    def __new__(cls, value, pretty_name, python_version):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._pretty_name = pretty_name
        obj._python_version = python_version
        return obj

    etl = ("glueetl", 'etl', "3")
    streaming = ("gluestreaming", 'streaming', "3")

    def python_version(self):
        return self._python_version

    def session_type(self):
        return self._value_

    def pretty_name(self):
        return self._pretty_name


WAIT_TIME_IN_SEC = 1

READY_SESSION_STATUS = "READY"
PROVISIONING_SESSION_STATUS = "PROVISIONING"
NOT_FOUND_SESSION_STATUS = "NOT_FOUND"
FAILED_SESSION_STATUS = "FAILED"
STOPPING_SESSION_STATUS = "STOPPING"
STOPPED_SESSION_STATUS = "STOPPED"
TIMEOUT_SESSION_STATUS = "TIMEOUT"
UNHEALTHY_SESSION_STATUS = [NOT_FOUND_SESSION_STATUS, FAILED_SESSION_STATUS, STOPPING_SESSION_STATUS,
                            STOPPED_SESSION_STATUS]

ERROR_STATEMENT_STATUS = "ERROR"
FAILED_STATEMENT_STATUS = "FAILED"
CANCELLED_STATEMENT_STATUS = "CANCELLED"
AVAILABLE_STATEMENT_STATUS = "AVAILABLE"
COMPLETED_STATEMENT_STATUS = "COMPLETED"
FINAL_STATEMENT_STATUS = [FAILED_STATEMENT_STATUS, ERROR_STATEMENT_STATUS, CANCELLED_STATEMENT_STATUS,
                          AVAILABLE_STATEMENT_STATUS, COMPLETED_STATEMENT_STATUS]

CHINA_REGIONS = {"cn-north-1", "cn-northwest-1"}
US_GOV_REGIONS = {"us-gov-east-1", "us-gov-west-1"}
