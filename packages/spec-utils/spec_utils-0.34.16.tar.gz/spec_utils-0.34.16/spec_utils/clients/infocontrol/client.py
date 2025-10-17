from __future__ import annotations
from datetime import datetime
import requests
from base64 import b64decode
from pathlib import Path
from typing import Any, Generator, Optional, Union, Dict
from spec_utils.clients.http import OAuthClient
from spec_utils.clients.infocontrol.models import (
    LoginResponse,
    Supplier,
    SuppliersListResponse,
    Worker,
    WorkersListResponse,
)
from spec_utils.schemas import JWT


class Client(OAuthClient):

    __name__ = "infocontrol"

    def __init__(
        self,
        *,
        url: Union[str, Path],
        username: str,
        pwd: str,
        session: Optional[requests.Session] = None,
        session_cfg: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create a connector with InfoControl gateway api using recived parameters

        Args:
            url (Union[str, Path]):
                InfoControl api url. Eg `https://InfoControl.gospec.net:8093/api/v1/`
            username (str): InfoControl username
            pwd (str): InfoControl password
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
        self.login_url = "web/workers/login"

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
                JSONResponse from 'Auth/login/' InfoControl api.
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
        """Send user and password to InfoControl api and get token from response."""

        if self.is_connected:
            return

        self.refresh_headers(remove_token=True)

        data = {
            "username": self.username,
            "password": b64decode(self.pwd).decode("utf-8"),
        }

        # consulting nettime
        response = self.post(path=self.login_url, json=data)
        parsed = LoginResponse(**response)
        token_data = JWT(
            access_token=parsed.data.token,
            token_type="Bearer",
            expires_in=parsed.data.token_expires_in,
        )
        # update access token and headers
        self.refresh_headers(token=token_data.model_dump())

        # refresh session with updated headers
        self.refresh_session()

    def logout(self) -> None:
        """Send a token to blacklist in backend."""

        if not self.is_connected:
            return

        # clean token and headers for safety
        self.refresh_headers(remove_token=True, remove_content_type=True)
        self.refresh_session()

    def relogin(self) -> None:
        """Reconnect client cleaning headers and access_token."""

        # logout and login. Will fail if has no token
        self.logout()
        self.login()

    def suppliers_list_data(
        self,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SuppliersListResponse:
        """
        Get suppliers list data from InfoControl api.

        Args:
            params (Optional[Dict[str, Any]], optional):
                Dict of parameters to send in the query string.
                Defaults to None.

        Returns:
            SuppliersListResponse: Response from InfoControl api.
        """

        path = "web/suppliers/list_data"
        response = self.get(path=path, params=params, **kwargs)
        return SuppliersListResponse(**response)

    def get_suppliers(
        self,
        update_dt: datetime,
        offset: Optional[int] = 0,
        limit: Optional[int] = 100,
        all_pages: Optional[bool] = False,
        **kwargs,
    ) -> Generator[Supplier, None, None]:
        """
        Retrieve a list of suppliers from the InfoControl API, optionally paginating through all pages.

        Args:
            update_dt (datetime): The datetime to filter the suppliers based on the update date.
            offset (Optional[int], optional): The number of items to skip before starting to collect the result set. Defaults to 0.
            limit (Optional[int], optional): The maximum number of suppliers to return in the response. Defaults to 100.
            all_pages (Optional[bool], optional): Determines whether to retrieve all pages of suppliers. Defaults to False.
            **kwargs: Additional keyword arguments passed to the API request.

        Yields:
            Supplier: An instance of `Supplier` for each supplier returned by the API.
        """

        params = {
            "offset": offset,
            "limit": limit,
            "update_dt": update_dt.strftime("%Y-%m-%d %H:%M:%S"),
        }
        response = self.suppliers_list_data(params=params, **kwargs)
        if not response.data:
            return

        for supplier in response.data:
            yield supplier

        if all_pages:
            yield from self.get_suppliers(
                update_dt=update_dt,
                offset=offset + limit,
                limit=limit,
                all_pages=all_pages,
                **kwargs,
            )

    def workers_list_data(
        self,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> WorkersListResponse:
        """
        Get workers list data from the InfoControl API.

        Args:
            update_dt (Optional[datetime]): The datetime to filter the workers based on the update date.
            params (Optional[Dict[str, Any]], optional): Dictionary of parameters to send in the query string. Defaults to None.
            **kwargs: Additional keyword arguments passed to the API request.

        Returns:
            WorkersListResponse: Response from the InfoControl API.
        """

        path = "web/workers/list_data"
        response = self.get(path=path, params=params, **kwargs)
        return WorkersListResponse(**response)

    def get_workers(
        self,
        update_dt: datetime,
        offset: Optional[int] = 0,
        limit: Optional[int] = 100,
        all_pages: Optional[bool] = False,
        **kwargs,
    ) -> Generator[Worker, None, None]:
        """
        Get workers from the InfoControl API.

        Args:
            update_dt (datetime): The datetime to filter the workers based on the update date.
            offset (Optional[int], optional): The number of records to skip before starting to return records. Defaults to 0.
            limit (Optional[int], optional): The maximum number of records to return. Defaults to 100.
            all_pages (Optional[bool], optional): If True, the function will yield all pages. Defaults to False.
            **kwargs: Additional keyword arguments passed to the API request.

        Yields:
            Worker: Worker object.
        """
        params = {
            "offset": offset,
            "limit": limit,
            "update_dt": update_dt.strftime("%Y-%m-%d %H:%M:%S"),
        }
        response = self.workers_list_data(params=params, **kwargs)
        if not response.data:
            return

        for supplier in response.data:
            yield supplier

        if all_pages:
            yield from self.get_workers(
                update_dt=update_dt,
                offset=offset + limit,
                limit=limit,
                all_pages=all_pages,
                **kwargs,
            )
