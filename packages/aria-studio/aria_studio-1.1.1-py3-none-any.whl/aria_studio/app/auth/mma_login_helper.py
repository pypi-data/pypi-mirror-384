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

import logging
import os
import time
from dataclasses import dataclass
from hashlib import sha256
from typing import Final, Optional

from aria_studio.app.common.args import Args
from aria_studio.app.common.types import AriaError, AriaException
from aria_studio.app.constants import (
    KEY_MMA_DATA_BLOB,
    KEY_MMA_DATA_TOKEN,
    KEY_MMA_HEADER_AUTH,
    KEY_MMA_HEADER_CONTENT_TYPE,
    KEY_MMA_RESPONSE_ACCESS_TOKEN,
    KEY_MMA_RESPONSE_ETOKEN,
    KEY_MMA_RESPONSE_TOKEN,
    KEY_MMA_RESPONSE_USER_ID,
    KEY_MMA_VALUE_CONTENT_TYPE,
)
from aria_studio.app.singleton_base import SingletonBase
from aria_studio.app.utils import CliAuthHelper, CliHttpHelper

from projectaria_tools.aria_mps_cli.cli_lib.authentication import (
    _DOC_ID_GET_HORIZON_PROFILE_TOKEN,
    _URL_META_GQL,
)
from projectaria_tools.aria_mps_cli.cli_lib.constants import (
    KEY_ACCESS_TOKEN,
    KEY_APP_ID,
    KEY_CREATE_TOKEN,
    KEY_DATA,
    KEY_DOC_ID,
    KEY_PROFILE_TOKENS,
    KEY_VARIABLES,
)

logger = logging.getLogger(__name__)


@dataclass
class MmaTokenEntry:
    """
    A last response from the MMA token endpoint
    """

    # The time the response was received
    timestamp: float
    # the application token is issued for
    app_id: str
    # The native_sso_token (T1) value
    token: str
    # The Native Single Sign-On encrypted token (T2) value
    etoken: str


class MmaLoginHelper(metaclass=SingletonBase):
    """
    Helper class to handle MMA login procedure's:
    step 1 - request etoken, and
    step 3 - decrypt the blob.
    """

    __ARIA_STUDIO_PIP_PORT: Final[int] = 8000
    __ARIA_STUDIO_PIP_APP_ID: Final[str] = "1651773608907002"
    __ARIA_STUDIO_PIP_TOKEN: Final[str] = (
        f"FRL|{__ARIA_STUDIO_PIP_APP_ID}|93a02e233037a10b41cdc2648f648ef4"
    )

    __ARIA_STUDIO_DEV_PORT: Final[int] = 3000
    __ARIA_STUDIO_DEV_APP_ID: Final[str] = "1202537978157901"
    __ARIA_STUDIO_DEV_TOKEN: Final[str] = (
        f"FRL|{__ARIA_STUDIO_DEV_APP_ID}|7e4fc1eca5a47c016deac1a4462b0212"
    )

    __ARIA_STUDIO_ELECTRON_PORT: Final[int] = 8134
    __ARIA_STUDIO_ELECTRON_APP_ID: Final[str] = "628991273092935"
    __ARIA_STUDIO_ELECTRON_TOKEN: Final[str] = (
        f"FRL|{__ARIA_STUDIO_ELECTRON_APP_ID}|d555ff37c29bf1228dec7afcf7fa89f4"
    )

    __ARIA_STUDIO_OC_APP_ID: Final[str] = "7496476603813560"

    __ON_DEMAND: Final[str] = os.environ.get("ON_DEMAND", "")

    __TOKEN_URL: Final[str] = (
        f"https://meta.{__ON_DEMAND}graph.meta.com/webview_tokens_query"
    )
    __DECRYPT_BLOB_URL: Final[str] = (
        f"https://meta.{__ON_DEMAND}graph.meta.com/webview_blobs_decrypt"
    )

    # Time the token reamins valid for equal to nounce timeout - 5min
    __CACHE_EXPIRY: Final[int] = 300

    # The application ID for Aria Studio. Depends on port the Aria Studio runs on.
    __app_id: str
    # The application token for Aria Studio. Depends on port the Aria Studio runs on.
    __app_token: str
    # If next decrypted token should be saved to disk
    __save_token: bool = False

    __token_cache: Optional[MmaTokenEntry] = None

    def __init__(self) -> None:
        """
        Initialize the MMA login helper. Sets the application ID and application token
        based on the port the Aria Studio is running on. If the port is not supported,
        raises an AriaException. Port is set in the application's launch arguments.

        For more details regarding login procedure, please refer to:
        https://www.internalfb.com/wiki/Meta_Account_Access_Eng_Wiki/RL_Account_Access/Development_Guide/Partner_Integration/Login_%26_Registration_Integration/#encrypted-blob-decryptio

        Raises:
            AriaException: If the port is not supported.
        """

        args = Args.get_args()

        if args.port == self.__ARIA_STUDIO_PIP_PORT:
            self.__app_token = self.__ARIA_STUDIO_PIP_TOKEN
            self.__app_id = self.__ARIA_STUDIO_PIP_APP_ID
        elif args.port == self.__ARIA_STUDIO_DEV_PORT:
            self.__app_token = self.__ARIA_STUDIO_DEV_TOKEN
            self.__app_id = self.__ARIA_STUDIO_DEV_APP_ID
        elif args.port == self.__ARIA_STUDIO_ELECTRON_PORT:
            self.__app_token = self.__ARIA_STUDIO_ELECTRON_TOKEN
            self.__app_id = self.__ARIA_STUDIO_ELECTRON_APP_ID
        else:
            raise AriaException(
                AriaError.MMA_WRONG_PORT,
                f"Aria Studio running on {args.port} port is not supported",
            )

    async def request_token(self, save_token: bool = False) -> MmaTokenEntry:
        """
        Request a token from the MMA token endpoint. If the cache is not expired, returns
        the cached token. Otherwise, makes a request to the MMA token endpoint and stores
        the response in the cache.

        Args:
            save_token: Optional; Whether to persist the token. Defaults to False. The
            value is persistend during this call and used during decryption. There is no
            user interaction with Aria Studio between both calls hence the value is
            cached between them.

        Returns:
            A MmaTokenEntry object containing the Native Single Sign-On encrypted token
            and application ID.
        """

        if (
            self.__token_cache is None
            or time.time() - self.__token_cache.timestamp >= self.__CACHE_EXPIRY
        ):
            resp = await CliHttpHelper.get().post(
                url=self.__TOKEN_URL,
                headers={
                    KEY_MMA_HEADER_CONTENT_TYPE: KEY_MMA_VALUE_CONTENT_TYPE,
                    KEY_MMA_HEADER_AUTH: f"Bearer {self.__app_token}",
                },
            )

            # Store the result in the cache
            self.__token_cache = MmaTokenEntry(
                timestamp=time.time(),
                token=resp[KEY_MMA_RESPONSE_TOKEN],
                etoken=resp[KEY_MMA_RESPONSE_ETOKEN],
                app_id=self.__app_id,
            )

            logger.debug("Received MMA token response.")

        self.__save_token = save_token

        return self.__token_cache

    async def decrypt_blob(self, blob: str, token: str) -> None:
        """
        Decrypts the authentication token's blob using remote endpoint. Sets decrypted user token for the
        MPS CLI backend. If the user token is already set, uses it for authentication.
        Before decryption, checks if the token is expired or mismatched between requests. In case of
        mismatch, raises an AriaException.

        Args:
            blob: The blob to decrypt.
            token: The token to verify the user data.

        Raises:
            AriaException: If the token is expired or mismatched between requests.
        """

        if self.__token_cache is None:
            logger.error("Token cache is empty. Please request a token first.")
            raise AriaException(
                AriaError.MMA_TOKEN_EXPIRED,
                "Token cache is empty. Please request a token first.",
            )

        if time.time() - self.__token_cache.timestamp >= self.__CACHE_EXPIRY:
            self.__token_cache = None
            logger.warn("Token expired. Please log in again.")
            raise AriaException(
                AriaError.MMA_TOKEN_EXPIRED,
                "Token expired. Please log in again.",
            )

        token_hash: str = sha256(self.__token_cache.token.encode()).hexdigest()[:16]
        if token_hash != token:
            self.__token_cache = None
            logger.error("Token mismatched between requests. Please log in again.")
            raise AriaException(
                AriaError.MMA_TOKEN_MISMATCH,
                "Token mismatched between requests. Please log in again.",
            )

        try:
            endpoint_response = await CliHttpHelper.get().post(
                url=self.__DECRYPT_BLOB_URL,
                headers={
                    KEY_MMA_HEADER_CONTENT_TYPE: KEY_MMA_VALUE_CONTENT_TYPE,
                    KEY_MMA_HEADER_AUTH: f"Bearer {self.__app_token}",
                },
                data={
                    KEY_MMA_DATA_BLOB: blob,
                    KEY_MMA_DATA_TOKEN: self.__token_cache.token,
                },
            )

            logger.debug("Received MMA blob decode response.")
        except Exception as e:
            logger.error(f"Failed to decrypt blob: {e}")
            raise AriaException(
                AriaError.MMA_DECRYPT_BLOB_FAILED,
                f"Failed to decrypt blob: {e}",
            )

        try:
            gql_response = await CliHttpHelper.get().post(
                url=_URL_META_GQL,
                json={
                    KEY_DOC_ID: _DOC_ID_GET_HORIZON_PROFILE_TOKEN,
                    # All FRL apps are mapped to the same OC app
                    KEY_VARIABLES: {KEY_APP_ID: self.__ARIA_STUDIO_OC_APP_ID},
                },
                auth_token=endpoint_response[KEY_MMA_RESPONSE_ACCESS_TOKEN],
            )

            logger.debug("Received OC user token")

            # Setter performs verification of the provided token
            # - queries GraphQL to obtain corresponing user name
            await CliAuthHelper.get().set_auth_token(
                token=gql_response[KEY_DATA][KEY_CREATE_TOKEN][KEY_PROFILE_TOKENS][0][
                    KEY_ACCESS_TOKEN
                ],
                save_token=self.__save_token,
            )

            logger.debug("Set the OC user token for MPS CLI")
        except Exception as e:
            logger.error(f"Failed to set the OC user token: {e}")
            raise AriaException(
                AriaError.MMA_SET_USER_TOKEN_FAILED,
                f"Failed to acquire the OC user token: {e}",
            )

        logger.debug("Login completed, clearing cache.")

        self.__token_cache = None
