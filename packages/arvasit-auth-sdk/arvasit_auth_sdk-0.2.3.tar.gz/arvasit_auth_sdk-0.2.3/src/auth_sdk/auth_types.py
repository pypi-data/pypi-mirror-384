# Auto-generated Python Pydantic models from JSON schema
# Do not edit manually - regenerate from schemas/auth-types.json

from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class AuthHeaders(BaseModel):
    public_key: str
    timestamp: str
    signature: str
    Authorization: Optional[str] = None

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class AuthServiceConfig(BaseModel):
    url: str
    public_key: str
    secret_key: str
    authorization: Optional[str] = None  # Optional authorization token

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class CheckCredentialRequest(BaseModel):
    credential: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class CheckCredentialResponse(BaseModel):
    isValid: bool
    type: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class CheckUserNameRequest(BaseModel):
    username: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class CredentialForForgotPasswordRequest(BaseModel):
    credential: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class DeviceRegistry(BaseModel):
    deviceId: Optional[str] = None
    deviceName: Optional[str] = None
    os: Optional[str] = None
    browserName: Optional[str] = None
    deviceType: Optional[str] = None
    deviceIp: Optional[str] = None
    rememberThisDevice: Optional[bool] = None

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class EnterCredentialForForgotPasswordResponse(BaseModel):
    maskedEmail: Optional[str] = None
    maskedPhone: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class ForgotPasswordSendOTPRequest(BaseModel):
    credential: str
    type: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class GenerateQrCodeAndSecretFor2FAResponse(BaseModel):
    secret: str
    qrCode: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class GenerateRecoveryCodeRequest(BaseModel):
    authId: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class ListOfRecoveryCodeResponse(BaseModel):
    createdOn: str
    listOfRecoveryCode: List[Dict[str, Any]]

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class ListOfSecretKeysResponse(BaseModel):
    isTwoFactorEnabled: bool
    listOfSecret: List[Dict[str, Any]]

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class LoginActivityCountResponse(BaseModel):
    totalCount: int
    data: List[Dict[str, Any]]

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class LoginActivityCountsRequest(BaseModel):
    startDate: str
    endDate: str
    page: Optional[int] = None
    limit: Optional[int] = None
    sortBy: Optional[str] = None
    sortOrder: Optional[str] = None
    searchField: Optional[str] = None
    searchValue: Optional[str] = None

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class LoginActivityDetailsRequest(BaseModel):
    authId: Optional[str] = None
    startDate: str
    endDate: str
    page: Optional[int] = None
    limit: Optional[int] = None
    sortBy: Optional[str] = None
    sortOrder: Optional[str] = None
    searchField: Optional[str] = None
    searchValue: Optional[str] = None

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class LoginActivityDetailsResponse(BaseModel):
    totalCount: int
    data: List[Dict[str, Any]]

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class LoginRequest(BaseModel):
    credential: str
    password: str
    expireSessionAt: Optional[str] = None
    tokenMetadata: Optional[Dict[str, Any]] = None
    deviceRegistry: Optional[DeviceRegistry] = None

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class LoginResponse(BaseModel):
    type: str
    message: str
    accessToken: str
    refreshToken: str
    deviceId: str
    userResponse: Dict[str, Any]

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class LogoutRequest(BaseModel):
    token: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class MagicLinkResponse(BaseModel):
    type: str
    message: str
    refreshToken: str
    deviceId: str
    userResponse: Dict[str, Any]

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class OtpLoginRequest(BaseModel):
    credential: str
    otp: str
    deviceRegistry: Optional[DeviceRegistry] = None

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class RecoveryCodeLoginRequest(BaseModel):
    credential: str
    recoveryCode: str
    deviceRegistry: Optional[DeviceRegistry] = None

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class RefreshAccessTokenRequest(BaseModel):
    token: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class RefreshTokenResponse(BaseModel):
    refreshToken: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class RemoveTwoFADeviceRequest(BaseModel):
    key: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class SignupRequest(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    username: Optional[str] = None
    phoneNumber: Optional[str] = None
    email: Optional[str] = None
    avatarUrl: Optional[str] = None
    password: str
    alternatePhoneNumber: Optional[List[str]] = []
    alternateEmail: Optional[List[str]] = []
    role: Optional[str] = None
    recoveryEmail: Optional[str] = None

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class SignupResponse(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    isTwoFactorAuthenticationEnabled: Optional[bool] = None
    avatarUrl: Optional[str] = None
    authId: str
    role: Optional[str] = None
    defaultClient: Optional[bool] = None
    recoveryEmail: Optional[str] = None
    clientId: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    phoneNumber: Optional[str] = None
    alternatePhoneNumber: Optional[List[str]] = []
    alternateEmail: Optional[List[str]] = []

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class SuggestUsernameRequest(BaseModel):
    firstName: str
    lastName: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class TwoFALoginRequest(BaseModel):
    credential: str
    totp: str
    deviceRegistry: Optional[DeviceRegistry] = None

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class UpdatePasswordRequest(BaseModel):
    credential: str
    oldPassword: str
    newPassword: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class ValidateForgetPasswordTokenRequest(BaseModel):
    token: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class VerifyForgotPasswordOTPRequest(BaseModel):
    credential: str
    otp: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class VerifyMagicLinkRequest(BaseModel):
    token: str
    credential: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class VerifyQRCodeAndSecretFor2FARequest(BaseModel):
    totp: str
    secretKey: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()


class VerifyTokenSetupPasswordRequest(BaseModel):
    token: str
    password: str

    def to_json(self) -> str:
        """Convert model to JSON string."""
        import json

        return json.dumps(self.model_dump(), indent=2)

    def __str__(self) -> str:
        """String representation showing JSON structure."""
        return self.to_json()
