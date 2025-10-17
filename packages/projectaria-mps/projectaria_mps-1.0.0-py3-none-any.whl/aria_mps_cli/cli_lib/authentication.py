# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import json
import logging
import os
import time
from enum import Enum
from http import HTTPStatus
from typing import Any, Final, Mapping, Optional

import aiohttp

try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

from aria_mps_cli.cli_lib.common import retry
from aria_mps_cli.cli_lib.constants import (
    AUTH_API_VERSION,
    AUTH_TOKEN_FILE,
    CONTENT_TYPE_JSON,
    HEADER_API_VERSION,
    HEADER_CONTENT_TYPE,
    KEY_ACCESS_TOKEN,
    KEY_ACCESS_TOKEN_PAYLOAD,
    KEY_APP_ID,
    KEY_AUTH_CODE,
    KEY_CONTACT_POINT,
    KEY_CREATE_TOKEN,
    KEY_DATA,
    KEY_DEVICE_CODE,
    KEY_DOC_ID,
    KEY_KEY_ID,
    KEY_OC_ACCESS_TOKEN,
    KEY_PASSWORD,
    KEY_PROFILE_TOKENS,
    KEY_PUBLIC_KEY,
    KEY_VARIABLES,
)
from aria_mps_cli.cli_lib.http_helper import HttpHelper

from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

logger = logging.getLogger(__name__)


class LoginMethod(Enum):
    """
    Enum representing different login methods available for users.
    """

    MMA = "MMA"
    PASSWORD = "Password"
    UNKNOWN = "Unknown"


# Keyring constants
_KEYRING_SERVICE_NAME: Final[str] = "projectaria_tools"
_KEYRING_SESSION_AUTH_TOKEN: Final[str] = "session_auth_token"

# OAuth FRL|FRL App ID| Client Token
_CLIENT_TOKEN: Final[str] = "FRL|844405224048903|ed1d75011c9a461b1f6c83c91f1fecb9"
_FB_APP_ACCESS_TOKEN: Final[str] = "651116310904236|e0782a32c77405233c4594dd5cbf7a0c"
# OC App ID
_CLIENT_APPLICATION: Final[int] = 6715036791927135
_DOC_ID_GET_HORIZON_PROFILE_TOKEN: Final[int] = 7806394482748426

# Standard Meta authentication endpoints
_URL_ACCOUNTS_LOGIN: Final[str] = (
    "https://meta.graph.meta.com/accounts_login"  # Login with username/password
)
_URL_ACCOUNTS_LOGOUT: Final[str] = "https://graph.oculus.com/logout"  # Logout endpoint
_URL_META_GQL: Final[str] = (
    "https://meta.graph.meta.com/graphql"  # GraphQL endpoint for profile token generation
)
_URL_ENCRYPTION_KEY: Final[str] = (  # Public key endpoint for password encryption
    "https://meta.graph.meta.com/passwords_encryption?version=2"
)

# Work/MMA (Managed Meta Account) authentication endpoints
_URL_WORK_ACCOUNT_PRE_LOGIN_INFO: Final[str] = (  # Check if email has MMA account
    "https://graph.work.meta.com/work_account/pre_login_info"
)
_URL_WORK_ACCOUNT_LOGIN: Final[str] = (
    "https://graph.work.meta.com/device/login"  # Initiate MMA device flow
)
_URL_WORK_ACCOUNT_GET_AUTH_CODE: Final[str] = (  # Poll for auth code in MMA device flow
    "https://api2.work.meta.com/oauth/poll_auth_code"
)
_URL_WORK_ACCOUNT_GET_ACCESS_TOKEN: Final[
    str
] = (  # Exchange auth code for access token
    "https://api2.work.meta.com/oauth/get_profile_token"
)


class AuthenticationError(RuntimeError):
    """
    Raised when authentication fails
    """

    pass


class Authenticator:
    """
    Class to handle authentication with the MPS backend.
    It supports:
    - Logging in using Meta account (password or MMA)
    - Logging out
    - Cache the authentication token
    - Loading and validating cached token

    """

    def __init__(
        self,
        http_helper: HttpHelper,
        client_token: str = _CLIENT_TOKEN,
        client_app: int = _CLIENT_APPLICATION,
    ):
        self._http_helper: HttpHelper = http_helper
        self._client_token: str = client_token
        self._client_app: int = client_app
        self._auth_token: Optional[str] = None
        self._user_alias: Optional[str] = None
        self._token_saved_to_keyring: bool = False

    @property
    def user(self) -> str:
        """
        Return the alias of the logged in user
        """
        return self._user_alias

    @property
    def auth_token(self) -> str:
        """
        Return the auth token
        """
        return self._auth_token

    @property
    def token_saved_to_keyring(self) -> bool:
        """
        Return True if the token was successfully saved to keyring
        """
        return self._token_saved_to_keyring

    def is_logged_in(self) -> bool:
        """
        Returns True if the user is logged in
        """
        return self._auth_token is not None

    async def set_auth_token(self, token: str, save_token: bool = False) -> None:
        """
        Sets the authentication token and validates it by retrieving the user alias.

        Args:
            token: The authentication token to be set
            save_token: Whether to save the token to local storage for future use

        Raises:
            ValueError: If the token is not a string or is invalid
        """
        if not isinstance(token, str):
            raise ValueError("Token must be a string")

        self._auth_token = token

        # Validate token by attempting to get user alias
        self._user_alias = await self._get_user_alias()
        if not self._user_alias:
            logger.error("Failed to get user alias: Token is invalid.")
            self._user_alias = None
            self._auth_token = None
            raise ValueError("Token is invalid")

        # Clear any cached previous token from disk
        AUTH_TOKEN_FILE.unlink(missing_ok=True)

        if save_token:
            logger.info("Attempting to save token to keyring...")
            try:
                self._save_token_to_keyring(self._auth_token)
                logger.info("Token successfully saved to keyring")
                self._token_saved_to_keyring = True
            except Exception as e:
                logger.warning(f"Failed to save token to keyring: {e}")
                logger.info("Keyring is not available. Token not saved.")
                self._token_saved_to_keyring = False

    def _load_token_from_disk(self) -> Optional[str]:
        """
        Load token from disk file (for old token migration).
        Returns the token if found and valid, None otherwise.
        Always deletes the disk file after reading.
        """
        if not AUTH_TOKEN_FILE.is_file() or not os.access(AUTH_TOKEN_FILE, os.R_OK):
            return None

        token = None
        try:
            logger.debug("Reading cached token from disk")
            with AUTH_TOKEN_FILE.open("rb") as f:
                file_content = f.read()

                if not file_content:
                    logger.warning("Token file is empty")
                elif file_content.startswith(b"FRL"):
                    logger.info("Found old unencrypted token starting with 'FRL'")
                    token = file_content.decode().strip()
                else:
                    logger.warning(
                        "Token file has invalid content (does not start with 'FRL')"
                    )
        except (ValueError, KeyError, OSError) as e:
            logger.error(f"Token loading from disk failed: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error while loading token from disk: {e}")
        finally:
            # Always delete the token file from disk after reading
            logger.info("Deleting auth token from disk")
            AUTH_TOKEN_FILE.unlink(missing_ok=True)

        return token

    def _load_token_from_keyring(self) -> Optional[str]:
        """
        Load token from system keyring.
        Returns the token if found, None otherwise.
        """
        if not KEYRING_AVAILABLE:
            logger.debug("Keyring library not available")
            return None

        try:
            stored_token = keyring.get_password(
                _KEYRING_SERVICE_NAME, _KEYRING_SESSION_AUTH_TOKEN
            )
            if stored_token:
                logger.info("Found token in keyring")
                return stored_token
            else:
                logger.debug("No token found in keyring")
                return None
        except Exception as e:
            logger.warning(f"Failed to load token from keyring: {e}")
            return None

    def _migrate_token_to_keyring(self) -> None:
        """
        Migrate token to keyring (best effort).
        Updates _token_saved_to_keyring flag based on success.
        """
        logger.info(
            "Token is valid and not expired. Attempting to migrate to keyring..."
        )
        try:
            self._save_token_to_keyring(self._auth_token)
            logger.info("Token successfully migrated to keyring")
            self._token_saved_to_keyring = True
        except Exception as e:
            logger.warning(f"Failed to migrate token to keyring: {e}")
            logger.info("Keyring is not available. Continuing without keyring storage.")
            self._token_saved_to_keyring = False

    async def load_and_validate_token(self) -> bool:
        """
        Reads the token from local disk or keyring and validates it.
        Follows the login flow specification:
        1. Check if auth_token file exists on disk
        2. If file content starts with "FRL" (binary mode) - old unencrypted token
        3. If file starts with anything else - invalid
        4. If file not present, try loading from keyring
        5. If valid token found, check if token is expired
        6. If expired - return False (need to redo login)
        7. If not expired and from disk - migrate to keyring (best effort)

        Returns:
            True if the token is found and is valid and not expired
        """
        # Try loading token from disk first (old migration path)
        self._auth_token = self._load_token_from_disk()
        token_from_disk = self._auth_token is not None

        # If no token from disk, try loading from keyring
        if not self._auth_token:
            logger.debug("No cached token found on disk, trying keyring")
            self._auth_token = self._load_token_from_keyring()

        # If we still don't have a token, return False
        if not self._auth_token:
            logger.debug("No cached token found in disk or keyring")
            return False

        # Validate the token by getting user alias
        self._user_alias = await self._get_user_alias()
        if not self._user_alias:
            logger.warning("Token is expired or invalid")
            self._remove_token_from_keyring()
            self._auth_token = None
            return False

        # If token came from disk, try to migrate it to keyring
        if token_from_disk:
            self._migrate_token_to_keyring()
        else:
            # Token came from keyring, so it's already saved there
            self._token_saved_to_keyring = True

        return True

    async def has_mma_account(self, email: str) -> bool:
        """
        Check if the given email address has an associated MMA (Managed Meta Account).

        This method queries the graph.work.meta.com/work_account/pre_login_info API
        to determine if an email is associated with an MMA account.

        Args:
            email: Email address to check

        Returns:
            True if the email has an associated MMA account, False otherwise
        """
        logger.debug(f"Checking if email {email} has an MMA account")
        try:
            response = await self._http_helper.post(
                url=_URL_WORK_ACCOUNT_PRE_LOGIN_INFO,
                json={
                    "identifier": email,
                    "access_token": _FB_APP_ACCESS_TOKEN,
                },
            )

            # If the response contains a valid uid, it means the email is associated with an MMA account
            logger.debug(f"Response: {response}")
            return response.get("uid") is not None
        except aiohttp.client_exceptions.ClientResponseError as e:
            # If the response is a 400 error, it means the email is not associated with an MMA account
            if e.status == HTTPStatus.BAD_REQUEST:
                logger.debug(f"Email {email} not found")
                return False
            else:
                logger.exception(f"Failed to check MMA account status: {e}")
                raise e
        except Exception as e:
            logger.exception(f"Failed to check MMA account status: {e}")
            raise e

    async def get_mma_device_flow_info(self) -> Mapping[str, Any]:
        """
        Initiate MMA device flow and get authentication information.

        This method queries the graph.work.meta.com/device/login API to initiate
        the device authorization flow for MMA login.

        Returns:
            A dictionary containing:
                - user_code: Code for user to enter on the login page
                - device_code: Code used for polling authentication status
                - verification_uri: URL where user completes authentication
                - expires_in: Time in seconds until codes expire
                - interval: Recommended polling interval in seconds
        Raises:
            AuthenticationError: If the device flow initiation fails
        """
        logger.info("Initiating MMA device authorization flow")
        try:
            response = await self._http_helper.post(
                url=_URL_WORK_ACCOUNT_LOGIN,
                json={
                    "scope": "openid",
                    "access_token": _FB_APP_ACCESS_TOKEN,
                },
            )
            logger.debug(f"Device flow response: {response}")
            return response
        except Exception as e:
            raise AuthenticationError(f"Failed to initiate MMA device flow: {e}")

    async def validate_username(self, username: str) -> LoginMethod:
        """
        Validate a username and return the appropriate login method.

        This method determines whether a user should use MMA login, password login,
        or if the username is invalid/unknown.

        Args:
            username: Username to validate

        Returns:
            LoginMethod.MMA if the user has an MMA account
            LoginMethod.PASSWORD if the user has a password account
            LoginMethod.UNKNOWN if the user has neither or validation fails
        """
        # Convert username to email format
        email = _get_email(username)

        # Check if user has an MMA account
        if await self.has_mma_account(email):
            return LoginMethod.MMA
        else:
            # If no MMA account but valid email format, assume password account
            return LoginMethod.PASSWORD

    async def _login_mma(self, email: str, save_token: bool) -> bool:
        """
        Login using MMA (Managed Meta Account) and obtain the access token.

        This method is currently a placeholder and needs to be implemented
        to handle the complete MMA authentication flow.

        Args:
            email: User's email address
            save_token: Whether to save the token to local storage

        Returns:
            True if the login was successful

        Raises:
            NotImplementedError: This method is not yet fully implemented
        """
        logger.info("Logging in using MMA account")
        # This should include:
        # 1. Device flow initiation
        # 2. Token polling and validation
        # 3. Token caching if requested
        raise NotImplementedError("MMA login flow is not yet fully implemented")

    async def password_login(
        self, username: str, password: str, save_token: bool
    ) -> bool:
        """
        Authenticate using the provided credentials and returns the authentication token
        The login is done in 2 steps:
        1. Login using Meta account and get the access token
        2. Use the access token to get the profile scoped access token
        3. After login, save token to keyring (best effort)
        Args:
            username: Username
            password: Password
            save_token: If true, saves the token to the local disk
        Returns:
            True if the login was successful
        """
        ## Step 1 : Login using Meta account
        response: Mapping[str, Any] = {}
        # 1.1 Get public key
        response = await self._http_helper.post(
            url=_URL_ENCRYPTION_KEY,
            auth_token=self._client_token,
        )
        if KEY_KEY_ID not in response or KEY_PUBLIC_KEY not in response:
            raise AuthenticationError(
                f"Getting public key failed with response '{json.dumps(response, indent=2)}'"
            )

        # 1.2 Encrypt password
        encrypted_password: bytearray = self._encrypt_password(
            key_id=response[KEY_KEY_ID],
            pub_key=response[KEY_PUBLIC_KEY],
            raw_password=password,
        )

        # 1.3 Login
        try:
            response = await self._http_helper.post(
                url=_URL_ACCOUNTS_LOGIN,
                auth_token=self._client_token,
                json={
                    KEY_CONTACT_POINT: _get_email(username),
                    KEY_PASSWORD: encrypted_password,
                },
            )
        except Exception as e:
            raise AuthenticationError(f"Login failed with exception {e}")
        if KEY_ACCESS_TOKEN not in response:
            raise AuthenticationError(
                f"Login failed with response '{json.dumps(response, indent=2)}"
            )
        logger.debug("Got meta account access token")
        user_access_token = response[KEY_ACCESS_TOKEN]

        # Step 2 : Get Horizon profile scoped access token
        response = await self._http_helper.post(
            url=_URL_META_GQL,
            json={
                KEY_DOC_ID: _DOC_ID_GET_HORIZON_PROFILE_TOKEN,
                KEY_VARIABLES: {KEY_APP_ID: self._client_app},
            },
            auth_token=user_access_token,
        )

        try:
            self._auth_token = response[KEY_DATA][KEY_CREATE_TOKEN][KEY_PROFILE_TOKENS][
                0
            ][KEY_ACCESS_TOKEN]
        except KeyError as e:
            raise AuthenticationError(
                f"Getting profile scoped access token failed with response '{response}'"
            ) from e

        logger.debug("Got profile scoped access token")
        self._user_alias = await self._get_user_alias()

        if self._user_alias and save_token:
            logger.info("Login successful. Attempting to save token to keyring...")
            try:
                self._save_token_to_keyring(self._auth_token)
                logger.info("Token successfully saved to keyring")
                self._token_saved_to_keyring = True
            except Exception as e:
                logger.warning(f"Failed to save token to keyring: {e}")
                logger.info("Keyring is not available. Token not saved.")
                self._token_saved_to_keyring = False

        return self._user_alias is not None

    @retry(
        error_codes=[
            HTTPStatus.REQUEST_TIMEOUT,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.BAD_REQUEST,
        ],
    )
    async def logout(self) -> bool:
        """
        Log out the current user.
        """
        logger.info("Logging out...")
        if not self._auth_token and not await self.load_and_validate_token():
            logger.info("Not logged in and cached token invalid or not found")
            return False

        try:
            await self._http_helper.post(
                url=_URL_ACCOUNTS_LOGOUT, auth_token=self._auth_token
            )
            logger.info("Logged out successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to log out: {e}")
            return False
        finally:
            self._auth_token = None
            AUTH_TOKEN_FILE.unlink(missing_ok=True)
            self._remove_token_from_keyring()

    def _save_token_to_keyring(self, token: str) -> None:
        """
        Save the authentication token to the system keyring.
        This is a best-effort operation - errors are raised to the caller.

        Args:
            token: The authentication token to save

        Raises:
            Exception: If saving to keyring fails
        """
        if not KEYRING_AVAILABLE:
            raise Exception("Keyring library is not available")

        keyring.set_password(_KEYRING_SERVICE_NAME, _KEYRING_SESSION_AUTH_TOKEN, token)

    def _remove_token_from_keyring(self) -> None:
        """
        Remove the authentication token from the system keyring.
        This is a best-effort operation - errors are logged but not raised.
        """
        if not KEYRING_AVAILABLE:
            logger.debug("Keyring library is not available, nothing to remove")
            return

        try:
            keyring.delete_password(_KEYRING_SERVICE_NAME, _KEYRING_SESSION_AUTH_TOKEN)
            logger.info("Token removed from keyring")
        except keyring.errors.PasswordDeleteError:
            logger.debug("No token found in keyring to remove")
        except Exception as e:
            logger.warning(f"Failed to remove token from keyring: {e}")

    def _encrypt_password(self, key_id: int, pub_key: str, raw_password: str) -> str:
        """Encrypts the password using the public key

        Args:
            key_id: The key id used to identify the key
            pub_key: The public key used to encrypt the password
            raw_password: The password to encrypt

        Returns:
            The encrypted password in the format expected by the auth service
        """
        version_byte: int = 1
        encrypted_data: bytearray = bytearray([version_byte, key_id])
        iv = get_random_bytes(12)
        encrypted_data.extend(iv)

        # Generate a random symmetric key and encrypt it using the public key
        symmetric_key = get_random_bytes(32)  # for AES-256
        encrypted_key = PKCS1_v1_5.new(RSA.import_key(pub_key)).encrypt(symmetric_key)
        # Write encrypted key length (256 bytes) in little endian
        encrypted_data.extend(len(encrypted_key).to_bytes(2, byteorder="little"))
        # Write encrypted key
        encrypted_data.extend(encrypted_key)

        # Initialize a cipher with the symmetric key
        cipher = AES.new(symmetric_key, AES.MODE_GCM, iv)
        aad = str(int(time.time()))
        cipher.update(aad.encode())
        cipher_text, tag = cipher.encrypt_and_digest(raw_password.encode())
        encrypted_data.extend(tag)
        encrypted_data.extend(cipher_text)
        return f"#PWD_ENC:2:{aad}:{base64.urlsafe_b64encode(encrypted_data).decode()}"

    async def _get_user_alias(self) -> Optional[str]:
        """
        Gets the alias of the currently logged in user
        """
        try:
            ## This will throw if the token is invalid
            return await self._http_helper.query_me(auth_token=self._auth_token)
        except Exception:
            logger.warning("Token is invalid.")
            return None

    async def check_mma_device_authorization(self, device_code: str) -> Optional[str]:
        """
        Poll for auth code using device code (Get Auth Code API call).

        This corresponds to step 3 in the MMA authentication flow where we
        periodically check if the user has completed authentication on the
        verification URL and entered their user code.

        Args:
            device_code: The device code obtained from get_mma_device_flow_info()

        Returns:
            The auth code if authentication is complete, None if still pending

        Raises:
            AuthenticationError: If the polling request fails
        """
        logger.debug("Polling for auth code using device code")
        try:
            response = await self._http_helper.post(
                url=_URL_WORK_ACCOUNT_GET_AUTH_CODE,
                auth_token=_FB_APP_ACCESS_TOKEN,
                headers={
                    HEADER_CONTENT_TYPE: CONTENT_TYPE_JSON,
                    HEADER_API_VERSION: AUTH_API_VERSION,
                },
                json={
                    KEY_DEVICE_CODE: device_code,
                },
            )

            # If auth_code is present, authentication is complete
            auth_code: str = response.get(KEY_AUTH_CODE)
            if auth_code:
                logger.info("Device authorization completed, received auth code")
                return auth_code
            else:
                logger.debug("Device authorization still pending")
                return None

        except Exception as e:
            raise AuthenticationError(f"Failed to poll for auth code: {e}")

    async def get_mma_access_token(self, auth_code: str) -> str:
        """
        Get access token using auth code (Get Access Token API call).

        This corresponds to step 4 in the MMA authentication flow where we
        exchange the auth code for the final access token.

        Args:
            auth_code: The auth code obtained from check_mma_device_authorization()

        Returns:
            The FRL access token for authenticated requests

        Raises:
            AuthenticationError: If the token request fails
        """
        logger.info("Getting access token using auth code")
        try:
            response = await self._http_helper.post(
                url=_URL_WORK_ACCOUNT_GET_ACCESS_TOKEN,
                auth_token=_FB_APP_ACCESS_TOKEN,
                headers={HEADER_CONTENT_TYPE: CONTENT_TYPE_JSON},
                json={
                    KEY_AUTH_CODE: auth_code,
                },
            )

            frl_access_token: str = response[KEY_ACCESS_TOKEN_PAYLOAD][
                KEY_OC_ACCESS_TOKEN
            ]
            if not frl_access_token:
                raise AuthenticationError(
                    f"No access token in response: {json.dumps(response, indent=2)}"
                )

            logger.info("Successfully obtained FRL access token")
            return frl_access_token

        except Exception as e:
            raise AuthenticationError(f"Failed to get access token: {e}")


def _get_email(username: str) -> str:
    """
    Converts the username to email format if necessary.
    This function is needed because academic partner accounts are provisioned by us and
    they all have tfbnw.net domain. When logging in to the mobile CA, they are used to
    only entering the username without the @tfbnw.net suffix. However, we need the full
    email address to authenticate
    """
    _DEFAULT_DOMAIN = "tfbnw.net"
    _TEST_DOMAIN = ".wptst.com"
    _DOMAINS: set[str] = {_DEFAULT_DOMAIN, _TEST_DOMAIN}
    if any((username.lower().endswith(domain) for domain in _DOMAINS)):
        return username
    if username.count("@") >= 1:
        raise ValueError(
            f"Invalid email address: {username}. Expected format: <username>@tfbnw.net"
        )
    return f"{username}@{_DEFAULT_DOMAIN}"
