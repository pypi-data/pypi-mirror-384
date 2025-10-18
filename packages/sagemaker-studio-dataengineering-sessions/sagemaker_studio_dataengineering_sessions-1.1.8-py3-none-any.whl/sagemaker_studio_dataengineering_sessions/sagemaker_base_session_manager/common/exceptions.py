class StartSessionException(RuntimeError):
    pass


class StopSessionException(RuntimeError):
    pass


class NoSessionException(RuntimeError):
    pass


class LanguageNotSupportedException(RuntimeError):
    pass


class NotAllowedSecondaryMagicException(RuntimeError):
    pass


class ConnectionNotFoundException(RuntimeError):
    """
    Exception raised when SageMaker connection name is not found in
    existing connections
    """
    pass


class ConnectionNotSupportedException(RuntimeError):
    """
    Exception raised when SageMaker connection type provided by
    customer is not supported.
    """
    pass


class SessionExpiredError(RuntimeError):
    '''
    Exception raised when SageMaker connection session is expired
    '''
    pass

class AuthenticationError(RuntimeError):
    '''
    Exception raised when authentication fails when connecting to remote compute
    '''
    pass

class ConnectionDetailError(RuntimeError):
    '''
    Exception raised when SageMaker connection detail is invalid
    '''
    pass

class ExecutionException(RuntimeError):
    '''
    Exception raised when execution failed
    '''
    pass
