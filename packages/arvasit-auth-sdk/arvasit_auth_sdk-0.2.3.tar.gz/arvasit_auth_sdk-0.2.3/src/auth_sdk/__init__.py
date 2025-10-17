# Auto-generated Python package init file
# Do not edit manually - regenerate from schemas/auth-types.json

from .auth_service import AuthService, AuthServiceConfig

# Import all generated types from schema
from .auth_types import AuthHeaders
from .auth_types import CheckCredentialRequest
from .auth_types import CheckCredentialResponse
from .auth_types import CheckUserNameRequest
from .auth_types import CredentialForForgotPasswordRequest
from .auth_types import DeviceRegistry
from .auth_types import EnterCredentialForForgotPasswordResponse
from .auth_types import ForgotPasswordSendOTPRequest
from .auth_types import GenerateQrCodeAndSecretFor2FAResponse
from .auth_types import GenerateRecoveryCodeRequest
from .auth_types import ListOfRecoveryCodeResponse
from .auth_types import ListOfSecretKeysResponse
from .auth_types import LoginActivityCountResponse
from .auth_types import LoginActivityCountsRequest
from .auth_types import LoginActivityDetailsRequest
from .auth_types import LoginActivityDetailsResponse
from .auth_types import LoginRequest
from .auth_types import LoginResponse
from .auth_types import LogoutRequest
from .auth_types import MagicLinkResponse
from .auth_types import OtpLoginRequest
from .auth_types import RecoveryCodeLoginRequest
from .auth_types import RefreshAccessTokenRequest
from .auth_types import RefreshTokenResponse
from .auth_types import RemoveTwoFADeviceRequest
from .auth_types import SignupRequest
from .auth_types import SignupResponse
from .auth_types import SuggestUsernameRequest
from .auth_types import TwoFALoginRequest
from .auth_types import UpdatePasswordRequest
from .auth_types import ValidateForgetPasswordTokenRequest
from .auth_types import VerifyForgotPasswordOTPRequest
from .auth_types import VerifyMagicLinkRequest
from .auth_types import VerifyQRCodeAndSecretFor2FARequest
from .auth_types import VerifyTokenSetupPasswordRequest

__all__ = [
    "AuthService",
    "AuthServiceConfig",
    "AuthHeaders",
    "CheckCredentialRequest",
    "CheckCredentialResponse",
    "CheckUserNameRequest",
    "CredentialForForgotPasswordRequest",
    "DeviceRegistry",
    "EnterCredentialForForgotPasswordResponse",
    "ForgotPasswordSendOTPRequest",
    "GenerateQrCodeAndSecretFor2FAResponse",
    "GenerateRecoveryCodeRequest",
    "ListOfRecoveryCodeResponse",
    "ListOfSecretKeysResponse",
    "LoginActivityCountResponse",
    "LoginActivityCountsRequest",
    "LoginActivityDetailsRequest",
    "LoginActivityDetailsResponse",
    "LoginRequest",
    "LoginResponse",
    "LogoutRequest",
    "MagicLinkResponse",
    "OtpLoginRequest",
    "RecoveryCodeLoginRequest",
    "RefreshAccessTokenRequest",
    "RefreshTokenResponse",
    "RemoveTwoFADeviceRequest",
    "SignupRequest",
    "SignupResponse",
    "SuggestUsernameRequest",
    "TwoFALoginRequest",
    "UpdatePasswordRequest",
    "ValidateForgetPasswordTokenRequest",
    "VerifyForgotPasswordOTPRequest",
    "VerifyMagicLinkRequest",
    "VerifyQRCodeAndSecretFor2FARequest",
    "VerifyTokenSetupPasswordRequest",
]
