from __future__ import annotations
import requests
from base64 import b64decode
from pathlib import Path
from typing import Any, List, Optional, Union, Dict
from spec_utils.clients.http import OAuthClient, JSONResponse
from spec_utils.schemas import JWT


class Client(OAuthClient):

    __name__ = "t3gateway"

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
                T3 api url. Eg `https://t3.gospec.net:8093/api/v1/`
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
                JSONResponse from 'Auth/login/' t3 api.
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

    def login(self) -> None:
        """Send user and password to t3 api and get token from response."""

        if self.is_connected:
            return

        self.refresh_headers(remove_token=True, remove_content_type=True)

        data = {
            "username": self.username,
            "password": b64decode(self.pwd).decode("utf-8"),
        }

        # consulting nettime
        json_data = self.post(path="Auth/login", data=data)

        # update access token and headers
        self.refresh_headers(token=json_data)

        # refresh session with updated headers
        self.refresh_session()

    def logout(self) -> None:
        """Send a token to blacklist in backend."""

        if not self.is_connected:
            return

        # disconnect ...
        _ = self.post(path="Auth/logout")

        # clean token and headers for safety
        self.refresh_headers(remove_token=True, remove_content_type=True)
        self.refresh_session()

    def relogin(self) -> None:
        """Reconnect client cleaning headers and access_token."""

        # logout and login. Will fail if has no token
        _ = self.logout()
        _ = self.login()

    def get_employees(self, active: Optional[bool] = None, **kwargs) -> JSONResponse:
        """Get active employees from nettime through t3 api.

        Args:
            active (Optional[bool], optional):
                Boolean to get active only -ignoring future-.
                Defaults to None.

        Returns:
            JSONResponse: List of employees from t3 api
        """

        return self.get(path="employees", params={"active": active}, **kwargs)

    def get_readers(self, **kwargs) -> JSONResponse:
        """Get readers from nettime through t3 api.

        Returns:
            JSONResponse: List of readers from t3 api
        """

        return self.get(path="readers", **kwargs)

    def get_reader(self, id: int, **kwargs) -> JSONResponse:
        """Get a reader from nettime through t3 api.

        Returns:
            JSONResponse: Reader detail from t3 api
        """

        return self.get(path=f"readers/{id}", **kwargs)

    def post_clockings(self, clockings: List[Dict[str, Any]], **kwargs) -> JSONResponse:
        """Send clockings to nettime through t3 api.

        Args:
            clockings (List[Dict[str, Any]]):
                List of clockings to import in nettime.
                See official documentation in `https://t3.gospec.net:8093/help`

        Returns:
            JSONResponse: List of clockings result from t3 api
        """

        return self.post(path="clockings/", json=clockings, **kwargs)
