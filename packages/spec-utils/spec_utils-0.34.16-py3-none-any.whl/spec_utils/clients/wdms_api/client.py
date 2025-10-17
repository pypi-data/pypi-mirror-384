from __future__ import annotations
import datetime as dt
import requests
from base64 import b64decode
from pathlib import Path
from typing import Any, Optional, Union, Dict
from spec_utils.clients.http import OAuthClient
from spec_utils.schemas import JWT
from spec_utils.schemas.wdms_api import TransactionPage
from spec_utils.clients.wdms_api.typos import TimeStampType


class Client(OAuthClient):

    __name__ = "wdms_api"

    def __init__(
        self,
        *,
        url: Union[str, Path],
        username: str,
        pwd: str,
        session: Optional[requests.Session] = None,
        session_cfg: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create a connector with t3 gateway api using recived parameters

        Args:
            url (Union[str, Path]):
                wdms custom api url. Eg `https://zkt.gospec.net:8093/api/v1/`
            username (str): T3 username
            pwd (str): T3 password
            session (Optional[requests.Session], optional):
                Optional session handler. Defaults to None.
        """
        super().__init__(
            url=url,
            username=username,
            pwd=pwd,
            session=session,
            session_cfg=session_cfg,
        )

        self.headers = {}

        # None values
        self.token = None
        self.expire_time = None

    def __enter__(self, *args, **kwargs) -> Client:
        return super().__enter__(*args, **kwargs)

    def refresh_headers(
        self,
        token: Optional[Dict[str, Any]] = None,
        remove_token: Optional[bool] = False,
        remove_content_type: Optional[bool] = False,
    ) -> None:
        """Refresh client headers for requests structure

        Args:
            token (Optional[Dict[str, Any]], optional):
                JSONResponse from 'Auth/login/' wdms custom api.
                Defaults to None.
            remove_token (Optional[bool], optional):
                Boolean to remove token from client.
                Defaults to False.
            remove_content_type (Optional[bool], optional):
                Boolean to remove content type for form encoded requests.
                Defaults to False.
        """

        if remove_token:
            self.token = None
            self.headers.pop("Authorization", None)
            self.session.headers.pop("Authorization", None)

        if remove_content_type:
            self.headers.pop("Content-Type", None)
            self.session.headers.pop("Content-Type", None)

        if token:
            self.token = JWT(**token)

        if self.token:
            self.headers.update(
                {
                    "Authorization": "{} {}".format(
                        self.token.token_type, self.token.access_token
                    )
                }
            )

        if "Content-Type" not in self.headers and not remove_content_type:
            self.headers.update({"Content-Type": "application/json;charset=UTF-8"})

    @property
    def is_connected(self):
        """Informs if client has headers and access_token."""
        return bool("Authorization" in self.headers and self.token is not None)

    @property
    def session_expired(self):
        """
        Informs if the session has expired and it is necessary to reconnect.
        """
        # not logged yet
        if self.expire_time is None:
            return False

        return self.expire_time > dt.datetime.now()

    @staticmethod
    def get_expire_time(expires_in: int) -> dt.datetime:
        expires_in = int(expires_in)
        now = dt.datetime.now()
        return now + dt.timedelta(seconds=expires_in - 10)

    def login(self) -> None:
        """Send user and password to wdms custom api and get token from response."""

        if self.is_connected:
            return

        self.refresh_headers(remove_token=True, remove_content_type=True)

        data = {
            "username": self.username,
            "password": b64decode(self.pwd).decode("utf-8"),
        }

        # consulting nettime
        json_data = self.post(path="Auth/login", data=data)

        # calc expire time
        _expire_time = json_data.get("expires_in", None)
        if _expire_time is not None:
            self.expire_time = self.get_expire_time(_expire_time)

        # update access token and headers
        self.refresh_headers(token=json_data)

        # refresh session with updated headers
        self.refresh_session()

    def logout(self) -> None:
        """Send a token to blacklist in backend."""

        if not self.is_connected:
            return

        # disconnect ...
        # response = self.post(path='Auth/logout')

        # clean token and headers for safety
        self.refresh_headers(remove_token=True, remove_content_type=True)
        self.refresh_session()

    def relogin(self) -> None:
        """Reconnect client cleaning headers and access_token."""

        # logout and login. Will fail if has no token
        _ = self.logout()
        _ = self.login()

    def get_transactions(
        self,
        id: Optional[int] = None,
        id_more_than: Optional[int] = None,
        emp_code: Optional[str] = None,
        terminal_sn: Optional[str] = None,
        terminal_alias: Optional[str] = None,
        start_time: Optional[TimeStampType] = None,
        end_time: Optional[TimeStampType] = None,
        upload_time: Optional[TimeStampType] = None,
        upload_time_more_than: Optional[TimeStampType] = None,
        order_by: Optional[str] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
        **kwargs,
    ) -> TransactionPage:
        """Get readers from nettime through wdms custom api.

        Returns:
            TransactionPage: List of readers from wdms custom api
        """

        _params = {
            "id": id,
            "id_more_than": id_more_than,
            "emp_code": emp_code,
            "terminal_sn": terminal_sn,
            "terminal_alias": terminal_alias,
            "start_time": start_time,
            "end_time": end_time,
            "upload_time": upload_time,
            "upload_time_more_than": upload_time_more_than,
            "order_by": order_by,
            "page": page,
            "size": size,
        }
        return TransactionPage(
            **self.get(path="transactions/", params=_params, **kwargs)
        )
