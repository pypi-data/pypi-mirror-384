from __future__ import annotations
from base64 import b64encode
from inspect import signature
from json.decoder import JSONDecodeError
from pathlib import Path
from types import TracebackType
from typing import Coroutine, Optional, Type, Union, Dict, List, Any
from urllib.parse import urlparse, urlencode, urljoin, quote, ParseResult
from pydantic_settings import BaseSettings

import aiohttp
import asyncio
import datetime as dt
import requests
import sys

from spec_utils.utils import Decorators
from spec_utils.schemas import KwargRelation


if (
    sys.platform.startswith("win")
    and sys.version_info[0] == 3
    and sys.version_info[1] >= 8
):
    policy = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)

_JSONValue = Union[str, int, float, bool, None, dt.date, dt.datetime, Any]
_JSONDict = Dict[str, _JSONValue]
JSONResponse = Union[_JSONDict, List[Union[_JSONDict, _JSONValue]]]


class Defaults(BaseSettings):
    PAGE_SIZE: int = 50
    TIME_OUT: int = 60
    DATE_FROM: dt.date = dt.date.today()

    class Extra: ...


class HTTPClient:
    __name__: Optional[str] = None

    def __init__(
        self,
        *,
        url: Union[str, Path, ParseResult],
        session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
        session_cfg: Optional[Dict[str, Any]] = None,
    ) -> None:

        # base
        self.url = url
        self.session = session
        self.session_cfg = session_cfg

        # needs
        if isinstance(url, ParseResult):
            self.client_url = url
        else:
            self.client_url = urlparse(url)

        # self.client_url.geturl() = url

        # unset
        self.headers = None

        # defaults
        self.defaults = Defaults()

    def __str__(self) -> str:
        return f"{self.__name__} Client for {self.client_url.geturl()}"

    def __repr__(self) -> str:
        try:
            return "{class_}({params})".format(
                class_=self.__class__.__name__,
                params=", ".join(
                    [
                        "{attr_name}={quote}{attr_val}{quote}".format(
                            attr_name=attr,
                            quote=("'" if type(getattr(self, attr)) == str else ""),
                            attr_val=getattr(self, attr),
                        )
                        for attr in signature(self.__init__).parameters
                    ]
                ),
            )
        except Exception:
            return super().__repr__()


class OAuthBase(HTTPClient):

    def __init__(
        self,
        *,
        url: Union[str, Path, ParseResult],
        username: str,
        pwd: str,
        session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
        session_cfg: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(url=url, session=session, session_cfg=session_cfg)

        self.username = username
        self.pwd = b64encode(pwd.encode("utf-8"))

    def __eq__(self, o: OAuthClient) -> bool:
        return self.url == o.url and self.username == o.username

    def __ne__(self, o: OAuthClient) -> bool:
        return self.url == o.url or self.username != o.username


class OAuthClient(OAuthBase):

    @property
    def is_connected(self):
        """Overwrite this property according to your need."""
        raise NotImplementedError("This method must be overloaded to work.")

    @property
    def session_expired(self):
        """Check if session has expired and if is necessary to reconnect."""
        raise NotImplementedError("This method must be overloaded to work.")

    def login(self) -> None:
        """Overwrite this method according to your need."""
        raise NotImplementedError("This method must be overloaded to work.")

    def logout(self) -> None:
        """Overwrite this method according to your need."""
        raise NotImplementedError("This method must be overloaded to work.")

    def relogin(self) -> None:
        """Overwrite this method according to your need."""
        raise NotImplementedError("This method must be overloaded to work.")

    def __enter__(self, *args, **kwargs) -> OAuthClient:
        self.start_session()
        return self

    def __exit__(self, *args, **kwargs) -> None:
        self.close_session()

    def start_session(self) -> None:
        self.session = requests.Session()
        if self.session_cfg:
            [setattr(self.session, k, v) for k, v in self.session_cfg.items()]
        self.session.headers.update(self.headers)

        # login
        self.login()

    def refresh_session(self) -> None:
        self.session.headers.update(self.headers)

    def close_session(self):
        self.logout()
        if self.session is not None:
            self.session.close()
        self.session = None

    @Decorators.merge_arguments(
        rels=[KwargRelation(inner="extra_params", outer="params")]
    )
    @Decorators.ensure_session
    def get(
        self,
        url: Optional[Union[str, Path, ParseResult]] = None,
        path: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Union[JSONResponse, requests.Response]:
        """
        Sends a GET request to visma url.

        :param path: path to add to URL for the new :class:`Request` object.
        :param params: (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
        :param **kwargs: Optional arguments that ``request`` takes.
        :return: :class:`dict` object
        :rtype: dict
        """

        # prepare url
        url = url or urljoin(self.client_url.geturl(), path)

        # consulting nettime
        response = self.session.get(url=url, params=params, **kwargs)

        # if session was closed, reconect client and try again
        if response.status_code == 401 and self.session_expired:
            self.relogin()
            return self.get(path=path, params=params, **kwargs)

        # raise if was an error
        if response.status_code not in range(200, 300):
            raise ConnectionError(
                {"status": response.status_code, "detail": response.text}
            )

        # if request is stream type, return all response
        if kwargs.get("stream"):
            return response

        # to json
        return response.json()

    @Decorators.merge_arguments(
        rels=[
            KwargRelation(inner="extra_params", outer="params"),
            KwargRelation(inner="extra_data", outer="data"),
            KwargRelation(inner="extra_json", outer="json"),
        ]
    )
    @Decorators.ensure_session
    def post(
        self,
        url: Optional[Union[str, Path, ParseResult]] = None,
        path: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Union[JSONResponse, requests.Response]:
        """
        Sends a POST request to visma url.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param json: (optional) json data to send in the body of the
            :class:`Request`.
        :param **kwargs: Optional arguments that ``request`` takes.
        :return: :class:`dict` object
        :rtype: dict
        """

        # prepare url
        url = url or urljoin(self.client_url.geturl(), path)

        # consulting visma
        response = self.session.post(
            url=url, params=params, data=data, json=json, **kwargs
        )

        # if session was closed, reconect client and try again
        if response.status_code == 401 and self.session_expired:
            self.relogin()
            return self.post(path=path, params=params, data=data, json=json, **kwargs)

        # raise if was an error
        if response.status_code not in range(200, 300):
            raise ConnectionError(
                {"status": response.status_code, "detail": response.text}
            )

        try:
            return response.json()
        except JSONDecodeError:
            return response.text

    @Decorators.ensure_session
    def patch(
        self,
        url: Optional[Union[str, Path, ParseResult]] = None,
        path: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Union[JSONResponse, requests.Response]:

        # prepare url
        url = url or urljoin(self.client_url.geturl(), path)

        # consulting visma
        response = self.session.patch(
            url=url, params=params, data=data, json=json, **kwargs
        )

        # if session was closed, reconect client and try again
        if response.status_code == 401 and self.session_expired:
            self.relogin()
            return self.patch(path=path, params=params, data=data, json=json, **kwargs)

        # raise if was an error
        if response.status_code not in range(200, 300):
            raise ConnectionError(
                {"status": response.status_code, "detail": response.text}
            )

        try:
            return response.json()
        except JSONDecodeError:
            return response.text

    @Decorators.ensure_session
    def delete(
        self,
        url: Optional[Union[str, Path, ParseResult]] = None,
        path: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Union[JSONResponse, requests.Response]:

        # prepare url
        url = url or urljoin(self.client_url.geturl(), path)

        # consulting visma
        response = self.session.delete(
            url=url, params=params, data=data, json=json, **kwargs
        )

        # if session was closed, reconect client and try again
        if response.status_code == 401 and self.session_expired:
            self.relogin()
            return self.delete(path=path, params=params, data=data, json=json, **kwargs)

        # raise if was an error
        if response.status_code not in range(200, 300):
            raise ConnectionError(
                {"status": response.status_code, "detail": response.text}
            )

        try:
            return response.json()
        except JSONDecodeError:
            return response.text

    @Decorators.ensure_session
    def put(
        self,
        url: Optional[Union[str, Path, ParseResult]] = None,
        path: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):

        # prepare url
        url = url or urljoin(self.client_url.geturl(), path)

        # consulting visma
        response = self.session.put(
            url=url, params=params, data=data, json=json, **kwargs
        )

        # if session was closed, reconect client and try again
        if response.status_code == 401 and self.session_expired:
            self.relogin()
            return self.put(path=path, params=params, data=data, json=json, **kwargs)

        # raise if was an error
        if response.status_code not in range(200, 300):
            raise ConnectionError(
                {"status": response.status_code, "detail": response.text}
            )

        try:
            return response.json()
        except JSONDecodeError:
            return response.text


class AsyncOAuthClient(OAuthBase):

    @property
    def is_connected(self):
        """Overwrite this property according to your need."""
        raise NotImplementedError("This method must be overloaded to work.")

    @property
    def session_expired(self):
        """Check if session has expired and if is necessary to reconnect."""
        raise NotImplementedError("This method must be overloaded to work.")

    async def login(self) -> None:
        """Overwrite this method according to your need."""
        raise NotImplementedError("This method must be overloaded to work.")

    async def logout(self) -> None:
        """Overwrite this method according to your need."""
        raise NotImplementedError("This method must be overloaded to work.")

    async def relogin(self) -> None:
        """Overwrite this method according to your need."""
        raise NotImplementedError("This method must be overloaded to work.")

    async def __aenter__(self) -> AsyncOAuthClient:
        await self.start_session()
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] = None,
        exc_value: BaseException = None,
        traceback: TracebackType = None,
    ) -> None:
        await self.close_session()

    async def start_session(self) -> None:
        self.session = aiohttp.ClientSession(headers=self.headers)
        self.session.headers.update(self.headers)

        await self.login()

    def refresh_session(self) -> None:
        self.session.headers.update(self.headers)

    async def close_session(self) -> None:
        await self.logout()
        if self.session is not None:
            await self.session.close()
        self.session = None

    def get_async_tasks(self, *coroutines: Coroutine) -> List[asyncio.Task]:
        """Create a list of coroutines to be executed with asyncio.gather

        Returns:
            List[asyncio.Task]: List of coroutines
        """
        return [asyncio.create_task(coroutine) for coroutine in coroutines]

    @Decorators.async_merge_arguments(
        rels=[KwargRelation(inner="extra_params", outer="params")]
    )
    @Decorators.ensure_async_session
    async def get(
        self,
        url: Optional[Union[str, Path, ParseResult]] = None,
        path: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Union[JSONResponse, aiohttp.ClientResponse]:

        # prepare url
        url = url or urljoin(self.client_url.geturl(), path)

        # update params
        if params:
            params = {k: str(v) for k, v in params.items() if v is not None}

        async with self.session.get(url=url, params=params, **kwargs) as response:

            # relogin and get response if error
            if response.status == 401 and self.session_expired:
                await self.relogin()
                response = await self.get(path=path, params=params, **kwargs)

            # raise if was an error
            if response.status not in range(200, 300):
                raise ConnectionError(
                    {"status": response.status, "detail": await response.text()}
                )

            # try to json
            json_response = await response.json()

        return json_response

    @Decorators.async_merge_arguments(
        rels=[
            KwargRelation(inner="extra_params", outer="params"),
            KwargRelation(inner="extra_data", outer="data"),
            KwargRelation(inner="extra_json", outer="json"),
        ]
    )
    @Decorators.ensure_async_session
    async def post(
        self,
        url: Optional[Union[str, Path, ParseResult]] = None,
        path: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json: Optional[JSONResponse] = None,
        **kwargs,
    ) -> JSONResponse:

        # prepare params
        url = url or urljoin(self.client_url.geturl(), path)

        # update params
        if params:
            params = {k: str(v) for k, v in params.items() if v is not None}

        async with self.session.post(
            url=url, params=params, data=data, json=json, **kwargs
        ) as response:

            # relogin and get response if error
            if response.status == 401 and self.session_expired:
                await self.relogin()
                response = await self.post(
                    url=url, params=params, data=data, json=json, **kwargs
                )

            # raise if was an error
            if response.status not in range(200, 300):
                raise ConnectionError(
                    {"status": response.status, "detail": await response.text()}
                )

            try:
                json_response = await response.json()
            except (JSONDecodeError, aiohttp.ContentTypeError):
                json_response = await response.text()

        # to json
        return json_response


class APIKeyClient(HTTPClient):

    def __init__(
        self,
        *,
        url: Union[str, Path, ParseResult],
        apikey: str,
        session: Optional[requests.Session] = None,
        session_cfg: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(url=url, session=session, session_cfg=session_cfg)

        self.apikey = apikey
        self.headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json",
            "Accept-Encoding": "gzip,deflate",
            "apikey": apikey,
        }

    def __eq__(self, o: object) -> bool:
        return self.url == o.url and self.apikey == o.apikey

    def __ne__(self, o: object) -> bool:
        return self.url == o.url or self.apikey != o.apikey

    def __enter__(self, *args, **kwargs) -> APIKeyClient:
        self.start_session()
        return self

    def __exit__(self, *args, **kwargs) -> None:
        self.close_session()

    def start_session(self):
        self.session = requests.Session()
        if self.session_cfg:
            [setattr(self.session, k, v) for k, v in self.session_cfg.items()]
        self.session.headers.update(self.headers)

    def close_session(self):
        if self.session is not None:
            self.session.close()
        self.session = None

    @property
    def is_connected(self):
        return self.session is not None

    @Decorators.merge_arguments(
        rels=[KwargRelation(inner="extra_params", outer="params")]
    )
    @Decorators.ensure_session
    def get(
        self,
        url: Optional[Union[str, Path, ParseResult]] = None,
        path: Optional[str] = None,
        params: dict = None,
        **kwargs,
    ) -> Union[JSONResponse, requests.Response]:
        """Sends a GET request to API Client.

        Args:
            path (str): Path to add to client full path URL
            params (dict, optional):
                Data to send in the query parameters of the request.
                Defaults to None.

        Raises:
            ConnectionError: If response status not in range(200, 300)

        Returns:
            JSONResponse: JSON Response if request is not stream.
            requests.Response: If request is stream.
        """

        # prepare url
        url = url or urljoin(self.client_url.geturl(), path)

        # consulting certronic
        response = self.session.get(url=url, params=params, **kwargs)

        # raise if was an error
        if response.status_code not in range(200, 300):
            raise ConnectionError(
                {"status": response.status_code, "detail": response.text}
            )

        # if request is stream type, return all response
        if kwargs.get("stream"):
            return response

        # return empty dict if not response text
        if not response.text:
            return {}

        # return json response
        return response.json()

    @Decorators.merge_arguments(
        rels=[
            KwargRelation(inner="extra_params", outer="params"),
            KwargRelation(inner="extra_data", outer="data"),
            KwargRelation(inner="extra_json", outer="json"),
        ]
    )
    @Decorators.ensure_session
    def post(
        self,
        url: Optional[Union[str, Path, ParseResult]] = None,
        path: Optional[str] = None,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        json: Optional[dict] = None,
        **kwargs,
    ) -> JSONResponse:
        """Sends a POST request to SPEC Manager url.

        Args:
            path (str): Path to add to client full path URL
            params (dict, optional):
                Data to send in the query parameters of the request.
                Defaults to None.
            data (dict, optional):
                Form Data to send in the request body.
                Defaults to None.
            json (dict, optional):
                JSON Data to send in the request body.
                Defaults to None.

        Raises:
            ConnectionError: If response status not in range(200, 300)

        Returns:
            JSONResponse: JSON Response
        """

        # prepare url
        url = url or urljoin(self.client_url.geturl(), path)

        # consulting certronic
        response = self.session.post(
            url=url,
            params=urlencode(params, quote_via=quote) if params else None,
            data=data,
            json=json,
            **kwargs,
        )

        # raise if was an error
        if response.status_code not in range(200, 300):
            raise ConnectionError(
                {"status": response.status_code, "detail": response.text}
            )

        # return empty dict if not response text
        if not response.text:
            return {}

        # return json response
        return response.json()


class AsyncAPIKeyClient(HTTPClient):

    def __init__(
        self,
        *,
        url: Union[str, Path, ParseResult],
        apikey: str,
        session: Optional[asyncio.ClientSession] = None,
    ) -> None:
        super().__init__(url=url, session=session)

        self.apikey = apikey
        self.headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json",
            "Accept-Encoding": "gzip,deflate",
            "apikey": apikey,
        }

    def __eq__(self, o: object) -> bool:
        return self.url == o.url and self.apikey == o.apikey

    def __ne__(self, o: object) -> bool:
        return self.url == o.url or self.apikey != o.apikey

    async def __aenter__(self, *args, **kwargs) -> APIKeyClient:
        self.start_session()
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] = None,
        exc_value: BaseException = None,
        traceback: TracebackType = None,
    ) -> None:
        await self.close_session()

    def start_session(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        self.session.headers.update(self.headers)

    async def close_session(self):
        if self.session is not None:
            await self.session.close()
        self.session = None

    def get_async_tasks(self, *coroutines: Coroutine) -> List[asyncio.Task]:
        """Create a list of coroutines to be executed with asyncio.gather

        Returns:
            List[asyncio.Task]: List of coroutines
        """
        return [asyncio.create_task(coroutine) for coroutine in coroutines]

    @Decorators.async_merge_arguments(
        rels=[KwargRelation(inner="extra_params", outer="params")]
    )
    @Decorators.ensure_async_session
    async def get(
        self,
        url: Optional[Union[str, Path, ParseResult]] = None,
        path: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Union[JSONResponse, aiohttp.ClientResponse]:

        # prepare url
        url = url or urljoin(self.client_url.geturl(), path)

        # update params
        if params:
            params = {k: str(v) for k, v in params.items() if v is not None}

        async with self.session.get(url=url, params=params, **kwargs) as response:

            # raise if was an error
            if response.status not in range(200, 300):
                raise ConnectionError(
                    {"status": response.status, "detail": await response.text()}
                )

            try:
                json_response = await response.json()
            except (JSONDecodeError, aiohttp.ContentTypeError):
                json_response = await response.text()

        return json_response

    @Decorators.async_merge_arguments(
        rels=[
            KwargRelation(inner="extra_params", outer="params"),
            KwargRelation(inner="extra_data", outer="data"),
            KwargRelation(inner="extra_json", outer="json"),
        ]
    )
    @Decorators.ensure_async_session
    async def post(
        self,
        url: Optional[Union[str, Path, ParseResult]] = None,
        path: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json: Optional[JSONResponse] = None,
        **kwargs,
    ) -> JSONResponse:

        # prepare params
        url = url or urljoin(self.client_url.geturl(), path)

        # update params
        if params:
            params = {k: str(v) for k, v in params.items() if v is not None}

        async with self.session.post(
            url=url, params=params, data=data, json=json, **kwargs
        ) as response:

            # raise if was an error
            if response.status not in range(200, 300):
                raise ConnectionError(
                    {"status": response.status, "detail": await response.text()}
                )

            try:
                json_response = await response.json()
            except (JSONDecodeError, aiohttp.ContentTypeError):
                json_response = await response.text()

        # to json
        return json_response
