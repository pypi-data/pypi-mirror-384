import os
import typing as t

from google.api_core.exceptions import PermissionDenied
from google.auth.environment_vars import CREDENTIALS as GOOGLE_CREDENTIALS_FILE_PATH
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError


class IAPToolkitBaseException(Exception):
    pass


class IAPBadResponse(IAPToolkitBaseException):
    pass


class TokenException(IAPToolkitBaseException):
    pass


class TokenStorageException(TokenException):
    pass


class IAPClientIDException(IAPToolkitBaseException):
    pass


class ServiceAccountTokenException(TokenException):
    def __init__(
        self, message: str, google_exception: t.Union[DefaultCredentialsError, RefreshError, PermissionDenied] | None
    ):
        self.google_exception = google_exception
        credentials_env_var_value = os.environ.get(GOOGLE_CREDENTIALS_FILE_PATH)
        metadata_server_attempted = not credentials_env_var_value
        self.message = (
            f"{message}, "
            f"metadata_attempted='{metadata_server_attempted}', "
            f"env_var='{GOOGLE_CREDENTIALS_FILE_PATH}', "
            f"env_var_value='{credentials_env_var_value or ''}', "
            f"google_exception='{str(google_exception)}'"
        )
        super().__init__(self.message)

    @property
    def retryable(self):
        if not self.google_exception:
            return False
        return getattr(self.google_exception, "_retryable", False)


class ServiceAccountNoDefaultCredentials(ServiceAccountTokenException):
    pass


class ServiceAccountTokenFailedRefresh(ServiceAccountTokenException):
    pass


class JWTPermissionException(ServiceAccountTokenException):
    pass


class InvalidDomain(IAPToolkitBaseException):
    pass


class PublicKeyException(IAPToolkitBaseException):
    pass


class JWTVerificationFailure(IAPToolkitBaseException):
    pass
