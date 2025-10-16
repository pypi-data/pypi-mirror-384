from __future__ import annotations
import json
import asyncio
import datetime as dt
import sys
from math import ceil
from pydantic.decorator import validate_arguments
from typing import Optional, Union, Dict, List
from spec_utils.clients.http import AsyncAPIKeyClient, JSONResponse
from spec_utils.schemas import certronic as cert_schema


if (
    sys.platform.startswith("win")
    and sys.version_info[0] == 3
    and sys.version_info[1] >= 8
):
    policy = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)


class AsyncClient(AsyncAPIKeyClient):

    __name__ = "Certronic"

    async def __aenter__(self, *args, **kwargs) -> AsyncClient:
        return await super().__aenter__(*args, **kwargs)

    @validate_arguments
    async def get_employees(
        self,
        page: Optional[int] = 1,
        pageSize: Optional[int] = None,
        updatedFrom: Optional[Union[dt.datetime, str]] = None,
        includeDocuments: Optional[bool] = None,
        customFields: Optional[List[str]] = None,
        inactive: Optional[bool] = None,
        dni: Optional[Union[int, str]] = None,
        all_pages: Optional[bool] = None,
        **kwargs,
    ) -> JSONResponse:

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
            "pageSize": pageSize or self.defaults.PAGE_SIZE,
            "page": page,
            "dni": dni,
        }

        # request.get -> json
        employees = await self.get(path="employees.php", params=params, **kwargs)

        if not all_pages:
            return employees

        _count = employees.get("count", 0)
        _pageSize = int(employees.get("pageSize", self.defaults.PAGE_SIZE))

        # calculate pages number
        _pages = ceil(_count / _pageSize) if _count else 1

        if _pages > 1:
            # remove page of params
            params.pop("page", None)

            coroutines = [
                self.get(path="employees.php", params={**params, "page": i}, **kwargs)
                for i in range(2, _pages + 1)
            ]

            tasks = self.get_async_tasks(*coroutines)
            responses = await asyncio.gather(*tasks)

            for child_response in responses:
                employees["employees"].extend(child_response.get("employees"))

        return employees

    @validate_arguments
    async def post_clockings(
        self, clockings: cert_schema.ClockingList, **kwargs
    ) -> Union[Dict, List]:

        # return response
        return await self.post(
            path="clocking.php",
            json={"clockings": json.loads(clockings.model_dump(mode="json"))},
            **kwargs,
        )
