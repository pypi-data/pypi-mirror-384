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

from typing import Final

BASE_URL: Final[str] = "http://localhost:8000"

RECORDINGS_ON_GLASSES_SUB: Final[str] = "/glasses"
RECORDINGS_ON_COMPUTER_SUB: Final[str] = "/files"
GROUPS_SUB: Final[str] = "/groups"
PAST_MPS_REQUESTS_SUB: Final[str] = "/services"
LOGIN_SUB: Final[str] = "/login"
FORGOT_PASSWORD_SUB: Final[str] = "/forgotpassword"

LOGIN_URL: Final[str] = BASE_URL + LOGIN_SUB
RECORDINGS_ON_GLASSES_URL: Final[str] = BASE_URL + RECORDINGS_ON_GLASSES_SUB
RECORDINGS_ON_COMPUTER_URL: Final[str] = BASE_URL + RECORDINGS_ON_COMPUTER_SUB
GROUPS_URL: Final[str] = BASE_URL + GROUPS_SUB
PAST_MPS_REQUESTS_URL: Final[str] = BASE_URL + PAST_MPS_REQUESTS_SUB
FORGOT_PASSWORD_URL: Final[str] = BASE_URL + FORGOT_PASSWORD_SUB

LOGIN_API_URL: Final[str] = f"{BASE_URL}/auth/login"
LOGOUT_API_URL: Final[str] = f"{BASE_URL}/auth/logout"
IS_LOGGED_IN_API_URL: Final[str] = f"{BASE_URL}/auth/is-logged-in"

ARIA_STUDIO_PASSWORD: Final[str] = "aria_password"
ARIA_STUDIO_USERNAME: Final[str] = "aria_username"
