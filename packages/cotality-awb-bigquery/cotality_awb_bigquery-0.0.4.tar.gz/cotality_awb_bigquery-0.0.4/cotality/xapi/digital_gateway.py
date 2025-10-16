# Copyright 2025 Cotality
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
"""Apigee client."""
from __future__ import annotations

import base64
import json
import logging
import time
from datetime import datetime
from typing import Any

import requests

from ..core.clgxtyping import Country, Environment
from ..core.exception import ClgxException, CommonErrorCodes

logger = logging.getLogger()

_API_OAUTH = "/oauth/token?grant_type=client_credentials"

_US_DOMAINS_LEGACY = {
    Environment.UAT: "https://api-uat.corelogic.com",
    Environment.PROD: "https://api-prod.corelogic.com",
}

_US_DOMAINS_X = {
    Environment.UAT: "https://api-uat.cotality.com",
    Environment.PROD: "https://prod.cotality.com",
}


_AU_DOMAINS = {
    Environment.UAT: "",
    Environment.PROD: "",
}

_UK_DOMAINS = {
    Environment.UAT: "",
    Environment.PROD: "",
}

_DOMAINS = {
    Country.US: _US_DOMAINS_LEGACY,
    Country.AU: _AU_DOMAINS,
    Country.GB: _UK_DOMAINS,
}

_KEY_EXPIRES_IN = "expires_in"
_KEY_TOKEN_TYPE = "token_type"
_KEY_ACCESS = "access_token"

# These parameters to control the number of retries and sleep time
# for the gateway and API calls.
GATEWAY_MAX_RETRIES = 3
GATEWAY_SLEEP_TIME_IN_SECONDS = 10


class DigitalGatewayClient:
    """ApigeeClient."""

    def __init__(
        self,
        environment: Environment,
        country_code: Country,
        username: str = "",
        password: str = "",
    ):
        """Initialize.

        Args:
            environment (Environment): Environment
            country_code (Country): Country code
            username (str): Username
            password (str): Password
        """
        self._digital_gateway_token = ""
        self.__token_ttl = 0
        self.__token = None
        self.__domain = _DOMAINS[country_code][environment]
        self.set_credential(username=username, password=password)

    def __enter__(self):
        """Enter."""

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exist."""

    @property
    def domain(self) -> str:
        """Return domain property.

        Returns:
            str: Domain
        """
        return self.__domain

    @property
    def masked_credential(self) -> str | None:
        """Return masked credential.

        Returns:
            str | None: Masked credential
        """
        if self._digital_gateway_token:
            return f"******{self._digital_gateway_token[-6:]}"

    def set_credential(
        self, username: str, password: str, validate: bool = False
    ) -> str | None:
        """Set credential.

        Args:
            username (str): Username
            password (str): Password
            validate (bool): Validate the credentials. Defaults to False.
        """
        self.__token_ttl = 0
        self.__token = None
        if username and password:
            usr_pwd = f"{username}:{password}"
            self._digital_gateway_token = base64.b64encode(usr_pwd.encode()).decode(
                "utf-8"
            )
            if validate:
                self.__get_token(self.__domain + _API_OAUTH)
        else:
            self._digital_gateway_token = ""
        return self.__token

    def get_authorization_token(
        self, access_token_expiration_buffer: int = 50, force: bool = False
    ) -> str | None:
        """Generate Bearer token.

        Args:
            oath_path (str): Oauth path
            access_token_expiration_buffer (int, optional): Timeout in seconds. Defaults to 50.

        Returns:
            Optional[str]: Token
        """
        # Force to expire for existing token is its remaining expired seconds is less than time_out_in_seconds
        if force:
            self.__token_ttl = 0

        if self.__token_ttl != 0:
            now = int(round(time.time()))
            delta = now - self.__token_ttl
            if delta > access_token_expiration_buffer:
                logger.debug(
                    "Token:%s expired: now=%s, ttl=%s, delta={delta}, time out=%d",
                    self.__token,
                    now,
                    self.__token_ttl,
                    access_token_expiration_buffer,
                )
                self.__token_ttl = 0

        if self.__token_ttl == 0:
            self.__token = self.__get_token(self.__domain + _API_OAUTH)
        return self.__token

    def get(
        self,
        api: str,
        headers: dict[str, str] | None = None,
        timeout: float = 300,
        valid_status_codes: list[int] | None = None,
    ) -> requests.Response:
        """Get method.

        Args:
            api (str): API path.
            headers (dict): Header dict object
            timeout (float): timeout in seconds for this API call. Default: 300
            valid_status_codes (list[int] | None): Valid status codes. Defaults to [200, 201].
        Returns:
            Response: HTTP response
        """
        start_dt = datetime.now()
        if valid_status_codes is None:
            valid_status_codes = [200, 201]
        url = self.__resolve_url(api=api)
        info: str = f"URL:{url}, Method:Get"
        response: requests.Response | None = None
        try:
            for _ in range(GATEWAY_MAX_RETRIES):
                hdr = self.__set_header(headers)
                logger.info(info)
                response = requests.get(url=url, headers=hdr, timeout=timeout)
                logger.debug(
                    "%s, Status:%d, Elapsed time (sec):%s. Response:%s",
                    info,
                    response.status_code,
                    datetime.now() - start_dt,
                    response.text,
                )
                if not self.__retriable(url, response):
                    break
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.GEN_RUN_TIME, message=info, cause=ex
            ) from ex
        return self.__validate_response(
            valid_status_codes=valid_status_codes, response=response, info=info
        )

    def sanitize(self, input_string: str) -> str:
        """santize input string."""
        return (
            input_string.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        )

    def post(
        self,
        api: str,
        data: str | dict | None = None,
        headers: dict | None = None,
        timeout: float | None = 300,
        valid_status_codes: list[int] | None = None,
    ) -> requests.Response:
        """Post method.

        Args:
            api (str): API path
            data (str|dict|None): Data
            headers (Optional[dict]): Header dict
            timeout (Optional[float]): timeout in seconds for this API call. Default: 300
            valid_status_codes (Optional[list[int]]): Valid status codes. Defaults to [200, 201].
        Returns:
            Response: HTTP response
        """
        return self.__post_put_patch(
            method="post",
            api=api,
            data=data,
            headers=headers,
            timeout=timeout,
            valid_status_codes=valid_status_codes,
        )

    def put(
        self,
        api: str,
        data: str | dict | None = None,
        headers: dict | None = None,
        timeout: float | None = 300,
        valid_status_codes: list[int] | None = None,
    ) -> requests.Response:
        """Put method.

        Args:
            api (str): API path
            data (str|dict|None): Data
            headers (Optional[dict]): Header dict
            timeout (Optional[float]): timeout in seconds for this API call. Default: 300
            valid_status_codes (Optional[list[int]]): Valid status codes. Defaults to [200, 201].
        Returns:
            Response: HTTP response
        """
        return self.__post_put_patch(
            method="put",
            api=api,
            data=data,
            headers=headers,
            timeout=timeout,
            valid_status_codes=valid_status_codes,
        )

    def patch(
        self,
        api: str,
        data: str | dict | None = None,
        headers: dict | None = None,
        timeout: float | None = 300,
        valid_status_codes: list[int] | None = None,
    ) -> requests.Response:
        """Patch method.

        Args:
            api (str): API path
            data (str|dict|None): Data
            headers (Optional[dict]): Header dict
            timeout (Optional[float]): timeout in seconds for this API call. Default: 300
            valid_status_codes (Optional[list[int]]): Valid status codes. Defaults to [200, 201].
        Returns:
            Response: HTTP response
        """
        return self.__post_put_patch(
            method="patch",
            api=api,
            data=data,
            headers=headers,
            timeout=timeout,
            valid_status_codes=valid_status_codes,
        )

    def delete(
        self,
        api: str,
        data: str | dict | None = None,
        headers: dict[Any, Any] | None = None,
        timeout: float | None = 300,
        valid_status_codes: list[int] | None = None,
    ) -> requests.Response:
        """Delete method.

        Args:
            api (str): API path
            data (str|dict|None): Data
            headers (Optional[dict]): Header dict
            timeout (Optional[float]): timeout in seconds for this API call. Default: 300
            valid_status_codes (Optional[list[int]]): Valid status codes. Defaults to [200, 201].
        Returns:
            Response: HTTP response
        """
        start_dt = datetime.now()
        if valid_status_codes is None:
            valid_status_codes = [200, 201]
        url = self.__resolve_url(api)
        info: str = f"URL:{url}, Method:Delete"
        payload: str = f"Data:{data}"
        response = None
        try:
            for _ in range(GATEWAY_MAX_RETRIES):
                hdr = self.__set_header(headers)
                logger.info(info)
                if data and isinstance(data, str):
                    response = requests.delete(
                        url=url, headers=hdr, data=data, timeout=timeout
                    )
                elif data and isinstance(data, dict):
                    response = requests.delete(
                        url=url, headers=hdr, json=data, timeout=timeout
                    )
                else:
                    response = requests.delete(url=url, headers=hdr, timeout=timeout)
                logger.debug(
                    "%s, Status:%d, Elapsed time (sec):%s. Response:%s",
                    info,
                    response.status_code,
                    datetime.now() - start_dt,
                    response.text,
                )
                if not self.__retriable(url, response):
                    break
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.GEN_RUN_TIME,
                message=f"{info}, {payload}",
                cause=ex,
            ) from ex
        return self.__validate_response(
            valid_status_codes=valid_status_codes,
            response=response,
            info=info,
            payload=payload,
        )

    # =========== Private methods
    def __resolve_url(self, api: str) -> str:
        """Determine if this is a proxy or direct api and which oauth path to use.

        Args:
            api (str): API URL.
                If absolute URL, eg starts with https then it is direct api URL.
                Otherwise, it is Apige proxy API

        Raises:
            ClgxException: Exception

        Returns:
            str: resolved URL
        """
        if not api:
            raise ClgxException(
                error=CommonErrorCodes.API_INVALID_URL,
                parameters={"name": api},
                message="API URL/URI is required!",
            )
        # Direct API URL, e.g. without Apigee Proxy
        if not api.startswith("https://"):
            resolved_api = api if api.startswith("/") else f"/{api}"
            resolved_api = f"{self.__domain}{resolved_api}"
        else:
            resolved_api = api
        return resolved_api

    def __set_header(
        self,
        headers: dict[Any, Any] | None,
        access_token_expiration_buffer: int = 50,
    ) -> dict[Any, Any]:
        """Set headers.

        Args:
            oath_path (str): Oauth path
            headers (dict): Input headers
            access_token_expiration_buffer (int, optional): Access token expiration buffer.
                Defaults to 50. If the remaining expired seconds is less than this value,
                a new token will be generated.

        Returns:
            dict: Headers with tokens
        """
        token = self.get_authorization_token(access_token_expiration_buffer)
        if headers:
            headers["Authorization"] = token
        else:
            headers = {"Authorization": token}
        if not headers.get("Content-Type"):
            headers["Content-Type"] = "application/json"
        # logger.debug("__set_header() - %s", headers)
        return headers

    def __get_token(
        self, oath_url: str, call_timeout: float | None = 300
    ) -> str | None:
        """Get token.

        Args:
            oath_url (str): Oauth path
            call_timeout (int, optional): Timeout in seconds. Defaults to 50.
        Raises:
            ClgxException: Exception

        Returns:
            str: Token
        """
        if not self._digital_gateway_token:
            raise ClgxException(
                error=CommonErrorCodes.API_AUTHENTICATION,
                message="Digital Gateway credentials are not set!",
            )
        credentials = self._digital_gateway_token
        response_text: str = ""
        # logger.info("__get_token() - credentials=(%s).", credentials)
        logger.debug("__get_token() - Get access token directly.")
        headers = {"Authorization": f"Basic {credentials}"}
        # logger.info("Get token: URL:%s, headers=%s", url, headers)
        response = requests.post(url=oath_url, headers=headers, timeout=call_timeout)
        if response.status_code != 200:
            msg = (
                f"get_authorization_token - Exception calling {oath_url}. "
                f"Status: {response.status_code}, Text:{response.text}"
            )
            raise ClgxException(error=CommonErrorCodes.API_AUTHENTICATION, message=msg)
        response_text = response.text
        # logger.info("__get_token() - Access token:%s", response)
        return self.__parse_token(response_text)

    def __parse_token(self, response: str | dict[Any, Any]) -> str | None:
        """Parse token response.

        Args:
            response (Union[str, dict]): Response to extract token from

        Raises:
            ClgxException: Exception

        Returns:
            str: Bearer Token
        """
        # logger.debug("__parse_token() - response type:%s", type(response))
        json_obj = json.loads(response) if isinstance(response, str) else response
        expired_in = json_obj.get(_KEY_EXPIRES_IN)
        token_type = json_obj.get(_KEY_TOKEN_TYPE)
        token_value = json_obj.get(_KEY_ACCESS)
        if not expired_in or not token_type or not token_value:
            raise ClgxException(
                error=CommonErrorCodes.API_PARSE_TOKEN,
                message=(
                    f"Invalid Apigee Token Response:{response}. "
                    f"Required keys:[{_KEY_EXPIRES_IN}, {_KEY_TOKEN_TYPE}, {_KEY_ACCESS}]"
                ),
            )
        try:
            seconds = int(expired_in)
            expires_in_seconds = int(time.time()) + seconds
        except Exception as err:
            raise ClgxException(
                error=CommonErrorCodes.API_PARSE_TOKEN,
                message=f"Expected a number from key:{_KEY_EXPIRES_IN}. Value={expired_in}",
            ) from err

        self.__token = f"{token_type} {token_value}"
        self.__token_ttl = expires_in_seconds
        return self.__token

    def __post_put_patch(
        self,
        method: str,
        api: str,
        data: str | dict | None = None,
        headers: dict | None = None,
        timeout: float | None = 300,
        valid_status_codes: list[int] | None = None,
    ) -> requests.Response:
        """Post method.

        Args:
            method (str): HTTP method (post, put, patch)
            api (str): API path
            data (str|dict|None): Data
            headers (Optional[dict]): Header dict
            timeout (Optional[float]): timeout in seconds for this API call. Default: 300
            valid_status_codes (Optional[list[int]]): Valid status codes. Defaults to [200, 201].
        Returns:
            Response: HTTP response
        """
        start_dt = datetime.now()
        if valid_status_codes is None:
            valid_status_codes = [200, 201]
        url = self.__resolve_url(api=api)
        info: str = f"URL:{url}, Method:Post"
        payload: str = f"Data:{data}"
        response: requests.Response | None = None

        try:
            for _ in range(GATEWAY_MAX_RETRIES):
                hdr = self.__set_header(headers)
                logger.debug(info)
                if data and isinstance(data, str):
                    response = requests.request(
                        method=method, url=url, headers=hdr, data=data, timeout=timeout
                    )
                elif data and isinstance(data, dict):
                    response = requests.request(
                        method=method, url=url, headers=hdr, json=data, timeout=timeout
                    )
                else:
                    response = requests.request(
                        method=method, url=url, headers=hdr, timeout=timeout
                    )

                status_code = str(response.status_code) if response else "None"
                response_text = response.text if response else "None"

                logger.debug(
                    "%s, Status:%s, Elapsed time (sec):%s. Response:%s",
                    self.sanitize(info),
                    status_code,
                    datetime.now() - start_dt,
                    self.sanitize(response_text),
                )
                if not self.__retriable(url, response):
                    break
        except Exception as ex:
            raise ClgxException(
                error=CommonErrorCodes.GEN_RUN_TIME,
                message=f"{info}, {payload}",
                cause=ex,
            ) from ex
        return self.__validate_response(
            valid_status_codes=valid_status_codes,
            response=response,
            info=info,
            payload=payload,
        )

    def __retriable(self, url: str, response: requests.Response | None) -> bool:
        """Return True if token is invalied or expired.

        Args:
            url (str): URL
            response (Response): Response

        Returns:
            bool: True if retry is needed.
        """
        retry = False
        if response is not None and response.status_code == 401:
            expires_in_seconds_str = datetime.fromtimestamp(self.__token_ttl).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            logger.info(
                "Access token expired! Url:%s, Expired time:%s",
                url,
                expires_in_seconds_str,
            )
            self.__token_ttl = 0
            retry = True
            time.sleep(GATEWAY_SLEEP_TIME_IN_SECONDS)
        return retry

    def __validate_response(
        self,
        valid_status_codes: list[int],
        response: requests.Response | None = None,
        info: str | None = "",
        payload: str | None = "",
    ) -> requests.Response:
        """Validate the response. Must be [200, 201].

        Args:
            valid_status_codes (list[int]): List of valid status codes
            response (Optional[Response]): Response
            info (Optional[str]): Display info
            payload (Optional[str]): Payload

        Raises:
            ClgxException: Exception

        Returns:
            Response: Good response
        """
        if response is None:
            raise ClgxException(
                error=CommonErrorCodes.API_INVALID_RESPONSE,
                message="Info:{info}, Response is None!. Payload:{payload}.",
            )
        elif response.status_code not in valid_status_codes:
            raise ClgxException(
                error=CommonErrorCodes.API_INVALID_RESPONSE,
                message=(
                    f"Info:{info}. Invalid Status code. Status:{response.status_code}, "
                    f"Payload:{payload}, Response:{response.text}"
                ),
            )
        return response
