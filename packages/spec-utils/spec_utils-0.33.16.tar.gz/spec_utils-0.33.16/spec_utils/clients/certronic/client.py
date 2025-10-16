from __future__ import annotations
import json
import datetime as dt
from pydantic.decorator import validate_arguments
from typing import Optional, Union, Dict, List
from spec_utils.clients.http import APIKeyClient
from spec_utils.schemas import certronic as cert_schema


class Client(APIKeyClient):

    __name__ = "Certronic"

    def __enter__(self, *args, **kwargs) -> Client:
        return super().__enter__(*args, **kwargs)

    @validate_arguments
    def get_employees(
        self,
        page: Optional[int] = 1,
        pageSize: Optional[int] = 50,
        updatedFrom: Optional[dt.datetime] = None,
        includeDocuments: Optional[bool] = None,
        customFields: Optional[List[str]] = None,
        inactive: Optional[bool] = None,
        dni: Optional[Union[int, str]] = None,
        **kwargs,
    ) -> Union[Dict, List]:
        """Get employees from Certronic API with client.get()

        Args:
            page (Optional[int], optional): Page number. Defaults to 1.
            pageSize (Optional[int], optional):
                Max results per page.
                Defaults to 50.
            updatedFrom (Optional[Union[dt.datetime, str]], optional):
                Datetime to apply as start filter of employees.
                Defaults to None.
            includeDocuments (bool, optional):
                Boolean to get documents detail.
                Defaults to None.
            customFields (Optional[List[Union[int, str]]], optional):
                List of Custom fields to get from employe.
                Defaults to None.

        Returns:
            Union[Dict, List]: List of JSON employees obtained from Certronic
        """

        # datetime to str
        if isinstance(updatedFrom, dt.datetime):
            updatedFrom = updatedFrom.strftime("%Y-%m-%d %H:%M:%S")

        # foce None if is False
        if not includeDocuments:
            includeDocuments = None
        if not inactive:
            inactive = None

        # parameters prepare
        params = {
            "updatedFrom": updatedFrom,
            "includeDocuments": includeDocuments,
            "customFields": customFields,
            "inactive": inactive,
            "pageSize": pageSize,
            "page": page,
            "dni": dni,
        }

        # request.get -> json
        return self.get(path="employees.php", params=params, **kwargs)

    @validate_arguments
    def post_clockings(
        self, clockings: cert_schema.ClockingList, **kwargs
    ) -> Union[Dict, List]:
        """Send clockings to Certronic API

        Args:
            clockings (cert_schema.ClockingList):
                List of clockings cert_schema.Clocking

        Returns:
            Union[Dict, List]: JSON Certronic API response.
        """

        # return response
        return self.post(
            path="clocking.php",
            json={"clockings": json.loads(clockings.model_dump(mode="json"))},
            **kwargs,
        )
