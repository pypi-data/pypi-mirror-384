import grpc
from grpc import RpcError


LAZO_ERROR_TYPE_KEY = "lazo-error-type"


class LazoError(grpc.RpcError):
    def __init__(self, error):
        self.error = error

    def __str__(self):
        return self.error


class LazoUnavailableError(LazoError):
    def __init__(self, error):
        self.error = error

    def __str__(self):
        error_msg = (
            "LazoClient failed to connect to server."
            " StatusCode: {} Details: {}".format(
                self.error.code(), self.error.details()
            )
        )
        return error_msg


class LazoInvalidArgumentError(LazoError):
    def __init__(self, error):
        self.error = error

    def __str__(self):
        error_msg = (
            "Arguments sent by the client are invalid."
            " StatusCode: {} Details: {}".format(
                self.error.code(), self.error.details()
            )
        )
        return error_msg

    def error_type(self):
        if hasattr(self.error, "trailing_metadata"):
            # trailing_metadata is a tuple of _Metadatum named tuples
            trailing_metadata = self.error.trailing_metadata()
            for metadatum in trailing_metadata:
                if metadatum.key == LAZO_ERROR_TYPE_KEY:
                    return metadatum.value
        return None


class LazoUnexpectedError(LazoError):
    def __init__(self, error):
        self.error = error

    def __str__(self):
        error_msg = (
            "An unexpected error was returned by the server."
            " StatusCode: {} Details: {}".format(
                self.error.code(), self.error.details()
            )
        )
        return error_msg


def lazo_client_exception(func):
    def _lazo_client_exception(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RpcError as e:
            if hasattr(e, "code"):
                if e.code() == grpc.StatusCode.UNAVAILABLE:
                    raise LazoUnavailableError(e)
                elif e.code() == grpc.StatusCode.INVALID_ARGUMENT:
                    raise LazoInvalidArgumentError(e)
            raise LazoUnexpectedError(e)

    return _lazo_client_exception
