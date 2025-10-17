import hashlib
import hmac
from datetime import datetime
from typing import Optional, Dict, Any, List

import requests
from pydantic import BaseModel

from .auth_types import (
    AuthServiceConfig,
    AuthHeaders,
    SignupRequest,
    SignupResponse,
    LoginRequest,
    LoginResponse,
    OtpLoginRequest,
    RecoveryCodeLoginRequest,
    TwoFALoginRequest,
    CheckCredentialResponse,
    EnterCredentialForForgotPasswordResponse,
    RefreshTokenResponse,
    ListOfSecretKeysResponse,
    ListOfRecoveryCodeResponse,
    RemoveTwoFADeviceRequest,
    LoginActivityCountsRequest,
    LoginActivityCountResponse,
    LoginActivityDetailsRequest,
    LoginActivityDetailsResponse,
    MagicLinkResponse,
    VerifyMagicLinkRequest,
)


class AuthService:
    def __init__(self, config: AuthServiceConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "X-Public-Key": config.public_key,
                "X-Secret-Key": config.secret_key,
            }
        )
        self.base_url = config.url

    def _get_auth_headers(self, access_token: Optional[str] = None) -> Dict[str, str]:
        timestamp = str(int(datetime.now().timestamp() * 1000))
        signature_data = f"{self.config.public_key}{timestamp}"
        signature = hmac.new(
            self.config.secret_key.encode(), signature_data.encode(), hashlib.sha256
        ).hexdigest()

        headers = {
            "public-key": self.config.public_key,
            "timestamp": timestamp,
            "signature": signature,
        }

        # Use provided access_token or fall back to config authorization
        # Remove "Bearer " prefix if present (case insensitive)
        token = access_token or self.config.authorization
        if token:
            # Remove "Bearer " prefix if present
            token = (
                token.replace("Bearer ", "", 1)
                if token.lower().startswith("bearer ")
                else token
            )
            headers["Authorization"] = f"Bearer {token}"

        return headers

    def _handle_error(self, error: Exception) -> Exception:
        if isinstance(error, requests.exceptions.RequestException):
            message = (
                error.response.json().get("message", str(error))
                if error.response
                else str(error)
            )
            return Exception(f"Auth Service Error: {message}")
        return error

    def signup(self, params: SignupRequest) -> SignupResponse:
        """Signup a new user."""
        path = "/auth/signup"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}", json=params.model_dump(), headers=headers
            )
            response.raise_for_status()
            return SignupResponse(**response.json())
        except Exception as e:
            raise self._handle_error(e)

    def suggest_username(self, first_name: str, last_name: str) -> List[str]:
        """Suggest available usernames based on first and last name."""
        path = "/user/usernames"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(
                f"{self.base_url}{path}",
                params={"firstName": first_name, "lastName": last_name},
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def check_available_username(self, username: str) -> bool:
        """Check if a username is available."""
        path = "/user/checkUsername"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(
                f"{self.base_url}{path}",
                params={"username": username},
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def check_credential(self, credential: str) -> CheckCredentialResponse:
        """Check the type of credential (email or phone)."""
        path = "/auth/checkCredential"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(
                f"{self.base_url}{path}",
                params={"credential": credential},
                headers=headers,
            )
            response.raise_for_status()
            return CheckCredentialResponse(**response.json())
        except Exception as e:
            raise self._handle_error(e)

    def login_with_password(self, params: LoginRequest) -> LoginResponse:
        """Login using password."""
        path = "/auth/loginWithPassword"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}", json=params.model_dump(), headers=headers
            )
            response.raise_for_status()
            login_response = LoginResponse(**response.json())
            return login_response
        except Exception as e:
            raise self._handle_error(e)

    def login_with_otp(self, params: OtpLoginRequest) -> LoginResponse:
        """Login using OTP."""
        path = "/auth/loginWithOtp"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}", json=params.model_dump(), headers=headers
            )
            response.raise_for_status()
            return LoginResponse(**response.json())
        except Exception as e:
            raise self._handle_error(e)

    def login_with_recovery_code(
        self, params: RecoveryCodeLoginRequest
    ) -> LoginResponse:
        """Login using recovery code."""
        path = "/auth/recoveryCodeToLogin"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}", json=params.model_dump(), headers=headers
            )
            response.raise_for_status()
            return LoginResponse(**response.json())
        except Exception as e:
            raise self._handle_error(e)

    def verify_magic_link(self, params: VerifyMagicLinkRequest) -> MagicLinkResponse:
        """Verify magic link for authentication."""
        path = "/auth/verify-magic-link"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(
                f"{self.base_url}{path}",
                params=params.model_dump(),
                headers=headers,
            )
            response.raise_for_status()
            return MagicLinkResponse(**response.json())
        except Exception as e:
            raise self._handle_error(e)

    def send_otp_for_login(self, credential: str) -> CheckCredentialResponse:
        """Send OTP for login."""
        path = "/auth/sendOtpForLogin"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(
                f"{self.base_url}{path}",
                params={"credential": credential},
                headers=headers,
            )
            response.raise_for_status()
            return CheckCredentialResponse(**response.json())
        except Exception as e:
            raise self._handle_error(e)

    def verify_two_factor_authentication(
        self, params: TwoFALoginRequest
    ) -> LoginResponse:
        """Verify two factor authentication."""
        path = "/auth/verifyTwoFactorAuthToken"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}", json=params.model_dump(), headers=headers
            )
            response.raise_for_status()
            return LoginResponse(**response.json())
        except Exception as e:
            raise self._handle_error(e)

    def logout(self) -> str:
        """Logout user."""
        path = "/auth/userLogout"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(f"{self.base_url}{path}", headers=headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise self._handle_error(e)

    def enter_credential_for_forgot_password(
        self, credential: str
    ) -> EnterCredentialForForgotPasswordResponse:
        """Enter credential for forgot password to get type email or phone."""
        path = "/auth/enterCredentialForForgotPassword"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(
                f"{self.base_url}{path}",
                params={"credential": credential},
                headers=headers,
            )
            response.raise_for_status()
            return EnterCredentialForForgotPasswordResponse(**response.json())
        except Exception as e:
            raise self._handle_error(e)

    def forgot_password_send_otp(self, credential: str, otp_type: str) -> str:
        """Send OTP for forgot password authorization."""
        path = "/auth/forgotPasswordSendOTP"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}",
                json={"credential": credential, "type": otp_type},
                headers=headers,
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise self._handle_error(e)

    def verify_forgot_password_otp(self, credential: str, otp: str) -> str:
        """Verify OTP for forgot password reset."""
        path = "/auth/verifyForgotPasswordOtp"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}",
                json={"credential": credential, "otp": otp},
                headers=headers,
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise self._handle_error(e)

    def validate_forget_password_token(self, token: str) -> bool:
        """Check if forgot password generated token is valid."""
        path = "/auth/validateForgetPasswordToken"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(
                f"{self.base_url}{path}",
                params={"token": token},
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def verify_token_setup_password(self, token: str, password: str) -> bool:
        """Verify token and set new password."""
        path = "/auth/verifyTokenSetupPassword"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}",
                json={"token": token, "password": password},
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def update_password(
        self, credential: str, old_password: str, new_password: str
    ) -> bool:
        """Update password with old password verification."""
        path = "/auth/updatePassword"
        headers = self._get_auth_headers()

        try:
            response = self.session.put(
                f"{self.base_url}{path}",
                json={
                    "credential": credential,
                    "oldPassword": old_password,
                    "newPassword": new_password,
                },
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def refresh_access_token(self, refresh_token: str) -> RefreshTokenResponse:
        """Refresh access token."""
        path = "/auth/refreshAccessToken"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}",
                json={"refreshToken": refresh_token},
                headers=headers,
            )
            response.raise_for_status()
            return RefreshTokenResponse(**response.json())
        except Exception as e:
            raise self._handle_error(e)

    def verify_access_token(self, token: str) -> Dict[str, str]:
        """Verify access token validity."""
        path = "/auth/verifyAccessToken"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(
                f"{self.base_url}{path}", params={"token": token}, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def generate_recovery_codes(self) -> LoginResponse:
        """Generate recovery codes."""
        path = "/secret-keys/generateRecoveryCodes"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(f"{self.base_url}{path}", headers=headers)
            response.raise_for_status()
            return LoginResponse(**response.json())
        except Exception as e:
            raise self._handle_error(e)

    def list_of_two_fa_secrets(self) -> ListOfSecretKeysResponse:
        """List of 2FA secrets."""
        headers = self._get_auth_headers()

        path = "/secret-keys/listOfTwoFASecrets"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(f"{self.base_url}{path}", headers=headers)
            response.raise_for_status()
            return ListOfSecretKeysResponse(**response.json())
        except Exception as e:
            raise self._handle_error(e)

    def remove_two_fa_device(self, params: RemoveTwoFADeviceRequest) -> List[str]:
        """Remove 2FA device."""
        headers = self._get_auth_headers()

        path = "/secret-keys/removeTwoFADevice"
        headers = self._get_auth_headers()

        try:
            response = self.session.delete(
                f"{self.base_url}{path}", params={"key": params.key}, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def disable_two_fa(self) -> bool:
        """Disable 2FA."""
        headers = self._get_auth_headers()

        path = "/auth/disable2FA"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(f"{self.base_url}{path}", headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def list_of_recovery_code(self) -> ListOfRecoveryCodeResponse:
        """List of recovery codes."""
        headers = self._get_auth_headers()

        path = "/secret-keys/listOfRecoveryCode"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(f"{self.base_url}{path}", headers=headers)
            response.raise_for_status()
            return ListOfRecoveryCodeResponse(**response.json())
        except Exception as e:
            raise self._handle_error(e)

    def login_activity_counts(
        self, params: LoginActivityCountsRequest
    ) -> LoginActivityCountResponse:
        """Get login activity counts."""
        headers = self._get_auth_headers()

        path = "/logging-events/loginActivityCount"
        headers = self._get_auth_headers()

        params_dict = {
            "startDate": params.startDate,
            "endDate": params.endDate,
        }
        # Add any additional parameters if they exist
        if hasattr(params, "page") and params.page is not None:
            params_dict["page"] = str(params.page)
        if hasattr(params, "limit") and params.limit is not None:
            params_dict["limit"] = str(params.limit)

        try:
            response = self.session.get(
                f"{self.base_url}{path}", params=params_dict, headers=headers
            )
            response.raise_for_status()
            return LoginActivityCountResponse(**response.json())
        except Exception as e:
            raise self._handle_error(e)

    def login_activity_details(
        self, params: LoginActivityDetailsRequest
    ) -> LoginActivityDetailsResponse:
        """Get login activity details."""
        headers = self._get_auth_headers()

        path = "/logging-events/loginActivityDetails"
        headers = self._get_auth_headers()

        params_dict = {
            "startDate": params.startDate,
            "endDate": params.endDate,
        }
        # Add any additional parameters if they exist
        if hasattr(params, "page") and params.page is not None:
            params_dict["page"] = str(params.page)
        if hasattr(params, "limit") and params.limit is not None:
            params_dict["limit"] = str(params.limit)

        try:
            response = self.session.get(
                f"{self.base_url}{path}", params=params_dict, headers=headers
            )
            response.raise_for_status()
            return LoginActivityDetailsResponse(**response.json())
        except Exception as e:
            raise self._handle_error(e)

    # ===== NEW MISSING METHODS =====

    def verify_user_email(self, params: Dict[str, str]) -> bool:
        """Verify user email."""
        path = "/auth/verifyUserEmail"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}", json=params, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def verify_user_phone(self, params: Dict[str, str]) -> bool:
        """Verify user phone number."""
        path = "/auth/verifyUserPhone"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}", json=params, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def verify_user_all_email(self, params: Dict[str, str]) -> bool:
        """Verify all emails of a user."""
        path = "/auth/verifyUserAllEmail"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}", json=params, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def verify_user_all_phone(self, params: Dict[str, str]) -> bool:
        """Verify all phone numbers of a user."""
        path = "/auth/verifyUserAllPhonenumber"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}", json=params, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def set_password(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Set password for user."""
        path = "/auth/setPassword"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}", json=params, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def set_otp(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set OTP for user."""
        path = "/auth/setOtp"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}", json=params, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def enable_2fa(self) -> Dict[str, str]:
        """Enable 2FA for user."""
        headers = self._get_auth_headers()

        path = "/secret-keys/enable2FA"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(f"{self.base_url}{path}", headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def verify_2fa(self, params: Dict[str, str]) -> List[str]:
        """Verify 2FA setup."""
        headers = self._get_auth_headers()

        # Use params directly for the request body
        request_params = params

        path = "/secret-keys/verify2FA"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}", json=request_params, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def find_active_devices(self) -> List[Dict[str, Any]]:
        """Find active devices for user."""
        headers = self._get_auth_headers()

        path = "/logging-events/findActiveDevices"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(f"{self.base_url}{path}", headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def remove_active_device(self, params: Dict[str, str]) -> bool:
        """Remove active device."""
        headers = self._get_auth_headers()

        session_id = params.get("sessionId")
        path = "/logging-events/removeActiveDevice"
        headers = self._get_auth_headers()

        try:
            response = self.session.delete(
                f"{self.base_url}{path}",
                params={"sessionId": session_id} if session_id else None,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def remove_expired_sessions(self) -> None:
        """Remove expired sessions (Public endpoint)."""
        path = "/logging-events/removeExpiredSessions"
        headers = self._get_auth_headers()

        try:
            response = self.session.delete(f"{self.base_url}{path}", headers=headers)
            response.raise_for_status()
        except Exception as e:
            raise self._handle_error(e)

    def find_all_users(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find all users."""
        path = "/user/find"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(
                f"{self.base_url}{path}", params=params, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def fetch_user(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Fetch user by criteria."""
        path = "/user/fetch"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(
                f"{self.base_url}{path}", params=params, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def suggest_usernames(self, params: Dict[str, str]) -> List[str]:
        """Suggest usernames."""
        path = "/user/usernames"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(
                f"{self.base_url}{path}", params=params, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def check_username(self, params: Dict[str, str]) -> bool:
        """Check username availability."""
        path = "/user/checkUsername"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(
                f"{self.base_url}{path}", params=params, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def create_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create user."""
        path = "/user/create"
        headers = self._get_auth_headers()

        try:
            response = self.session.post(
                f"{self.base_url}{path}", json=params, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def update_user(self, auth_id: str, params: Dict[str, Any]) -> bool:
        """Update user by auth ID."""
        path = f"/user/update/{auth_id}"
        headers = self._get_auth_headers()

        try:
            response = self.session.put(
                f"{self.base_url}{path}", json=params, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def remove_user(self, params: Dict[str, str]) -> bool:
        """Remove user."""
        headers = self._get_auth_headers()

        auth_id = params["authId"]
        path = "/user/remove"
        headers = self._get_auth_headers()

        try:
            response = self.session.delete(
                f"{self.base_url}{path}", params={"authId": auth_id}, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise self._handle_error(e)

    def oauth_google(self, params: Dict[str, Any]) -> str:
        """OAuth Google authentication (Public endpoint)."""
        path = "/oauth/google"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(
                f"{self.base_url}{path}", params=params, headers=headers
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise self._handle_error(e)

    def oauth_github(self, params: Dict[str, Any]) -> str:
        """OAuth GitHub authentication (Public endpoint)."""
        path = "/oauth/github"
        headers = self._get_auth_headers()

        try:
            response = self.session.get(
                f"{self.base_url}{path}", params=params, headers=headers
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise self._handle_error(e)
