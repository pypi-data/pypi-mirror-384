from __future__ import annotations
import asyncio
import datetime as dt
import sys
from aiohttp import ClientSession
from base64 import b64decode
from pathlib import Path
from typing import Any, Callable, List, Optional, Union, Dict
from spec_utils.clients.nettime6.query import Query
from spec_utils.utils import create_random_suffix, async_range
from spec_utils.clients.http import AsyncOAuthClient, JSONResponse


if (
    sys.platform.startswith("win")
    and sys.version_info[0] == 3
    and sys.version_info[1] >= 8
):
    policy = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)

__nettime__ = "6.0.1.19025"


class AsyncClient(AsyncOAuthClient):

    __name__ = "netTime6"

    def __init__(
        self,
        *,
        url: Union[str, Path],
        username: str,
        pwd: str,
        session: Optional[ClientSession] = None,
    ) -> None:
        """Create a conection with visma app using recived parameters.

        Args:
            url (Union[str, Path]): Visma URL.
            username (str): Visma User
            pwd (str): Visma Password
            session (Optional[requests.Session], optional):
                Optional session handler. Defaults to None.
            tenant_filter (Optional[Dict[str, Any]], optional):
                Optional filters to get tenant. Defaults to None.
        """

        super().__init__(url=url, username=username, pwd=pwd, session=session)

        # base headers
        self.headers = {"DNT": "1", "Accept-Encoding": "gzip,deflate"}

        # None values
        self.access_token = None
        self.user_rol = None
        self.settings = None

        # add extra to defaults
        setattr(
            self.defaults.Extra,
            "NODE_EXISTS",
            "Ya existe un elemento con el mismo nombre",
        )

    async def __aenter__(self) -> AsyncClient:
        return await super().__aenter__()

    def refresh_headers(
        self,
        access_token: Optional[str] = None,
        remove_token: Optional[bool] = False,
        remove_content_type: Optional[bool] = False,
    ) -> None:
        if remove_token:
            self.access_token = None
            self.headers.pop("Cookie", None)
            self.session.headers.pop("Cookie", None)

        if remove_content_type:
            self.headers.pop("Content-Type", None)
            self.session.headers.pop("Content-Type", None)

        if access_token:
            self.access_token = access_token

        if self.access_token:
            self.headers.update(
                {"Cookie": f"sessionID={self.access_token}; i18next=es"}
            )

        if "Content-Type" not in self.headers and not remove_content_type:
            self.headers.update({"Content-Type": "application/json;charset=UTF-8"})

    @property
    def is_connected(self):
        """Informs if client has headers and access_token."""
        return bool("Cookie" in self.headers and bool(self.access_token))

    async def post(
        self,
        path: str,
        params: dict = None,
        data: dict = None,
        json: JSONResponse = None,
        **kwargs,
    ) -> JSONResponse:

        # to json -> json
        json_response = await super().post(
            path=path, params=params, data=data, json=json, **kwargs
        )

        # get task results if is generated
        if isinstance(json_response, dict) and json_response.get("taskId", None):
            json_response = await self.get_task_response(json_response.get("taskId"))

        # return json response
        return json_response

    async def login(self) -> None:
        if self.is_connected:
            return

        # remove content type from headers. Must be not json
        self.refresh_headers(remove_token=True, remove_content_type=True)

        # data prepare
        data = {
            "username": self.username,
            "pwd": b64decode(self.pwd).decode("utf-8"),
        }

        # consulting nettime
        json_data = await self.post(path="/api/login", data=data)

        if not json_data.get("ok", None):
            raise ConnectionError({"status": 401, "detail": json_data.get("message")})

        # update access token and headers
        self.refresh_headers(access_token=json_data.get("access_token"))

        # refresh session with updated headers
        self.refresh_session()

        self.settings = await self.get_settings()
        self.user_rol = self.get_user_rol()

    async def logout(self) -> None:
        if not self.is_connected:
            return

        # disconnect ...
        _ = await self.post(path="/api/logout")

        # clean token and headers for safety
        self.refresh_headers(remove_token=True, remove_content_type=True)
        self.refresh_session()

    async def relogin(self) -> None:
        """Reconnect client cleaning headers and access_token."""

        # logout and login. Will fail if has no token
        _ = await self.logout()
        _ = await self.login()

    async def get_settings(self) -> dict:
        """Get settings of netTime Server."""

        return await self.get(path="/api/settings")

    def get_user_rol(self) -> str:
        """Get user_rol of current session."""

        return self.settings.get("rol", None)

    def get_days_offset(self, days: List[Union[dt.date, str]]) -> List[int]:

        # wait active conection
        if not self.is_connected:
            raise ConnectionError(
                {
                    "status": 500,
                    "detail": "Client disconnected. Use relogin() to connect.",
                }
            )

        firstYear = self.settings.get("firstDate", None)
        if not firstYear:
            raise RuntimeError(
                {
                    "status": 500,
                    "detail": "Client disconnected. Use relogin() to connect.",
                }
            )

        # set first_date
        first_date = dt.date(firstYear, 1, 1)

        # process dates
        days_numbers = []
        for day in days:
            # ensuredt.date type
            if not isinstance(day, dt.date):
                day = dt.date.fromisoformat(day)

            delta = day - first_date
            days_numbers.append(delta.days)

        return days_numbers

    def get_days_from_offsets(self, offsets: List[Union[int, str]]) -> List[str]:

        # wait active conection
        if not self.is_connected:
            raise ConnectionError("Cliente desconectado. Utilice connect().")

        firstYear = self.settings.get("firstDate", None)
        if not firstYear:
            raise RuntimeError("No se puede obtener el setting firstDate.")

        # set first_date
        first_date = dt.date(firstYear, 1, 1)

        # process dates
        dates = []
        for offset in offsets:
            date = first_date + dt.timedelta(days=int(offset))
            dates.append(date.isoformat())

        return dates

    async def get_app_resource(self, name: str, **kwargs):

        return await self.get(path=f"/AppResources/{name}", **kwargs)

    async def get_fields(
        self, container: str, filterFields: bool = False, **kwargs
    ) -> JSONResponse:
        path = "/api/container/fields"

        # prepare task parameters
        params = {"container": container, "filterFields": filterFields}

        # request.get
        return await self.get(path=path, params=params, **kwargs)

    async def get_elements(
        self, container: str, query=Query(["id", "name"]), **kwargs
    ) -> JSONResponse:

        # prepare task parameters
        params = {
            "pageStartIndex": 0,
            "pageSize": kwargs.get("pageSize", self.defaults.PAGE_SIZE),
            "search": kwargs.get("search", ""),
            "order": kwargs.get("order", ""),
            "desc": kwargs.get("desc", ""),
            "container": container,
            "query": query.prepare(),
        }

        # request.get -> json
        json_response = await self.get(path="/api/container/elements", params=params)

        # get task results
        if json_response.get("taskId", None):
            json_response = await self.get_task_response(json_response.get("taskId"))

        return json_response

    async def get_employees(self, query=Query(["id", "nif"]), **kwargs) -> JSONResponse:

        # use get general propose
        return await self.get_elements(container="Persona", query=query, **kwargs)

    async def container_action_exec(
        self,
        container: str,
        action: str,
        elements: list,
        all_: bool = False,
        dataObj: dict = None,
        **kwargs,
    ) -> JSONResponse:

        # prepare task parameters
        json_data = {
            "container": container,
            "action": action,
            "all": all_,
            "elements": elements,
            "dataObj": dataObj,
        }
        # json_data.update(kwargs)

        # request.get -> json
        return await self.post(
            path="/api/container/action/exec", json=json_data, **kwargs
        )

    async def save_element(
        self,
        container: str,
        dataObj: dict,
        elements: list = [],
        all_: bool = False,
        **kwargs,
    ) -> JSONResponse:

        # executing and processing
        return await self.container_action_exec(
            action="Save",
            container=container,
            elements=elements,
            all_=all_,
            dataObj=dataObj,
            **kwargs,
        )

    async def delete_element(
        self,
        container: str,
        elements: list,
        confirm_: bool = True,
        all_: bool = False,
    ) -> JSONResponse:
        """Delete an element of a container with the received values."""

        # data prepare
        data = {
            "action": "Delete",
            "container": container,
            "elements": elements,
            "all_": all_,
        }

        # default auto confirm
        if confirm_:
            data["dataObj"] = {
                "_confirm": confirm_,
            }

        # executing and processing
        return await self.container_action_exec(**data)

    async def get_for_duplicate(
        self, container: str, element: int, all_: bool = False
    ) -> JSONResponse:

        # executing and processing
        response = await self.container_action_exec(
            action="Copy", container=container, elements=[element], all_=all_
        )

        if not response:
            raise ValueError("Error getting duplicate form.")

        # data of response
        # obj = response[0]
        return response[0].get("dataObj")

    async def get_element_def(
        self,
        container: str,
        elements: list,
        all_: bool = False,
        read_only: bool = False,
        **kwargs,
    ) -> JSONResponse:

        # executing and processing
        response = await self.container_action_exec(
            container=container,
            elements=elements,
            all_=all_,
            action="editForm" if not read_only else "View",
            **kwargs,
        )

        return [ed.get("dataObj") for ed in response]

    async def get_create_form(self, container: str, **kwargs) -> JSONResponse:

        # execute and process
        response = await self.get_element_def(
            container=container, elements=[-1], **kwargs
        )

        if not response:
            raise ValueError({"status": 500, "detail": "Error getting creation form."})

        return response[0]

    async def get_day_info(
        self,
        employee: int,
        from_: Optional[Union[dt.date, str]] = None,
        to: Optional[Union[dt.date, str]] = None,
        **kwargs,
    ) -> JSONResponse:

        if isinstance(from_, (dt.date, dt.datetime)):
            from_ = from_.isoformat()

        if isinstance(to, (dt.date, dt.datetime)):
            to = to.isoformat()

        # prepare task parameters
        params = {
            "idemp": employee,
            "from": from_ or self.defaults.DATE_FROM.isoformat(),
            "to": to or self.defaults.DATE_FROM.isoformat(),
        }

        # request.get -> json
        return await self.get(path="/api/day/results", params=params, **kwargs)

    async def get_access_clockings(
        self,
        employee: int,
        from_: Optional[Union[dt.date, str]] = None,
        to: Optional[Union[dt.date, str]] = None,
        **kwargs,
    ) -> JSONResponse:

        if isinstance(from_, (dt.date, dt.datetime)):
            from_ = from_.isoformat()

        if isinstance(to, (dt.date, dt.datetime)):
            to = to.isoformat()

        # prepare task parameters
        params = {
            "idemp": employee,
            "from": from_ or self.defaults.DATE_FROM.isoformat(),
            "to": to or self.defaults.DATE_FROM.isoformat(),
        }

        # request.get -> json
        return await self.get(path="/api/access/clockings", params=params, **kwargs)

    async def get_task_status(self, task: int, **kwargs) -> JSONResponse:

        # prepare task parameters
        params = {"taskid": task}

        # request.get -> json
        return await self.get(path="/api/async/status", params=params, **kwargs)

    async def get_task_response(self, task: int, **kwargs) -> JSONResponse:

        # ensure the task is complete
        task_status = await self.get_task_status(task)
        while not task_status.get("completed", False):
            task_status = await self.get_task_status(task)

        # prepare task parameters
        params = {"taskid": task}

        # request.get -> json
        return await self.get(path="/api/async/response", params=params, **kwargs)

    async def get_results(
        self,
        employee: int,
        from_: Optional[Union[dt.date, str]] = None,
        to: Optional[Union[dt.date, str]] = None,
        **kwargs,
    ) -> JSONResponse:

        if isinstance(from_, (dt.date, dt.datetime)):
            from_ = from_.isoformat()

        if isinstance(to, (dt.date, dt.datetime)):
            to = to.isoformat()

        # prepare task parameters
        params = {
            "idemp": employee,
            "from": from_ or self.defaults.DATE_FROM.isoformat(),
            "to": to or self.defaults.DATE_FROM.isoformat(),
        }

        # generate async task
        async_task = await self.get(path="/api/results", params=params, **kwargs)

        # get task results
        return await self.get_task_response(async_task.get("taskId"))

    def _clocking_prepare(
        self,
        date_time: Union[str, dt.datetime],
        reader: int = -1,
        clocking_id: int = -1,
        action: Optional[str] = None,
    ) -> Dict[str, Any]:

        # ensuredt.datetime type
        if isinstance(date_time, dt.datetime):
            date_time = date_time.isoformat(timespec="miliseconds")

        # prepare structure
        return {
            "id": clocking_id,
            "action": action,
            "app": True,
            "type": "timetypes",
            "date": date_time,
            "idReader": reader,
            "idElem": 0,
            "isNew": True if clocking_id == -1 else False,
        }

    async def post_clocking(
        self,
        *,
        employee: int,
        date_time: Union[dt.datetime, str],
        date_time_fmt: Optional[str] = None,
        action: Optional[str] = None,
        reader: int = -1,
        clocking_id: int = -1,
        **kwargs,
    ) -> JSONResponse:

        if self.user_rol == "Persona":
            raise ValueError(
                {
                    "status": 400,
                    "detail": "Method not allowed for `person` type",
                }
            )

        if isinstance(date_time, str):
            if date_time_fmt:
                date_time = dt.datetime.strptime(date_time, date_time_fmt)
            else:
                date_time = dt.datetime.fromisoformat(date_time)

        json_data = {
            "idEmp": employee,
            "date": date_time.date().isoformat(),
            "clockings": [
                self._clocking_prepare(
                    employee=employee,
                    date_time=date_time.isoformat(),
                    reader=reader,
                    action=action,
                    clocking_id=clocking_id,
                )
            ],
        }

        return await self.post(path="/api/day/post/", json=json_data, **kwargs)

    async def get_day_clockings(
        self,
        *,
        employee: int,
        date: Optional[Union[str, dt.date]] = None,
        **kwargs,
    ) -> JSONResponse:

        if isinstance(date, (dt.date, dt.datetime)):
            date = date.isoformat()

        # prepare task parameters
        params = {
            "path": "/api/clockings",
            "method": "get",
            "idemp": employee,
            "date": date or self.defaults.DATE_FROM.isoformat(),
        }

        # generate async task
        task = await self.get(path="/api/clockings", params=params, **kwargs)

        # get and return task results
        return self.get_task_response(task.get("taskId"))

    async def add_clocking(
        self,
        *,
        employee: int,
        date_time: Union[dt.datetime, str],
        date_time_fmt: Optional[str] = None,
        reader: int = -1,
        **kwargs,
    ):

        if isinstance(date_time, str):
            if date_time_fmt:
                date_time = dt.datetime.strptime(date_time, date_time_fmt)
            else:
                date_time = dt.datetime.fromisoformat(date_time)

        return await self.post_clocking(
            employee=employee, date_time=date_time, reader=reader, **kwargs
        )

    async def edit_clocking(
        self,
        employee: int,
        clocking_id: int,
        date_time: Union[dt.datetime, str],
        date_time_fmt: Optional[str] = None,
        reader: int = -1,
        **kwargs,
    ):

        if isinstance(date_time, str):
            if date_time_fmt:
                date_time = dt.datetime.strptime(date_time, date_time_fmt)
            else:
                date_time = dt.datetime.fromisoformat(date_time)

        return await self.post_clocking(
            employee=employee,
            date_time=date_time,
            reader=reader,
            clocking_id=clocking_id,
            **kwargs,
        )

    async def delete_clocking(
        self,
        employee: int,
        clocking_id: int,
        date_time: Union[dt.datetime, str],
        date_time_fmt: Optional[str] = None,
        **kwargs,
    ) -> JSONResponse:

        if isinstance(date_time, str):
            if date_time_fmt:
                date_time = dt.datetime.strptime(date_time, date_time_fmt)
            else:
                date_time = dt.datetime.fromisoformat(date_time)

        return await self.post_clocking(
            employee=employee,
            date_time=date_time,
            action="Delete",
            clocking_id=clocking_id,
            **kwargs,
        )

    async def add_planning(
        self,
        *,
        employee: int,
        name: str,
        days: List[Union[dt.date, str]],
        allDay: bool = True,
        timetype: int = 0,
        extra_fields: Dict[str, Any] = {},
        **kwargs,
    ) -> JSONResponse:

        # getting form and update data
        planning = await self.get_create_form(
            container="Persona", action="NewPlanificacion"
        )
        planning.update(
            {
                "name": name,
                "allDay": allDay,
                "allDayId": timetype,  # Timetype ID
                "employee": [employee],  # Employee ID
                "dateInterval": self.get_days_offset(days=days),
            }
        )
        planning.update(extra_fields)
        return await self.save_element(
            container="IncidenciaFutura", dataObj=planning, **kwargs
        )

    async def add_activator(
        self,
        *,
        name: str,
        employees: List[Union[int, str]],
        days: List[Union[dt.date, str]],
        activator: Union[int, str],
        value: Optional[int] = None,
        comment: Optional[str] = None,
        **kwargs,
    ) -> JSONResponse:
        """
        Create an activator for an employee on the indicated days using \
        the received activator id.
        """

        new_activator = await self.get_create_form(container="UsoActivadores")
        new_activator.update(
            {
                "name": name,
                "multiname": {"es-ES": name},
                "activators": [
                    {
                        "activator": activator,
                        "value": value,
                    }
                ],
                "comment": comment,
                "days": self.get_days_offset(days=days),
                "employees": employees,
            }
        )

        return await self.save_element(
            container="UsoActivadores", dataObj=new_activator, **kwargs
        )

    async def get_activity_monitor(
        self,
        *,
        employees: List[int, str],
        from_: Union[str, dt.date],
        to: Union[str, dt.date],
        **kwargs,
    ) -> JSONResponse:
        """Return the activity monitor structure."""

        if isinstance(from_, dt.date):
            from_ = from_.isoformat()

        if isinstance(to, dt.date):
            to = to.isoformat()

        # prepare task parameters
        json_data = {
            "clockings": True,
            "from": from_,
            "to": to,
            "ids": employees,
        }

        # generate and get async task result
        return await self.post(
            path="/api/planification/manager", json=json_data, **kwargs
        )

        # get and return task results
        # return await self.get_task_response(async_tasK.get('taskId'))

    async def get_cube_results(
        self,
        *,
        dimensions: List[List[Union[str, Any]]],
        dateIni: Union[str, dt.date],
        dateEnd: Union[str, dt.date],
        interFilters: Optional[list] = None,
        filters: Optional[list] = None,
        ids: Optional[list] = None,
        **kwargs,
    ) -> JSONResponse:

        if isinstance(dateIni, dt.date):
            dateIni = dateIni.isoformat()

        if isinstance(dateEnd, dt.date):
            dateEnd = dateEnd.isoformat()

        # prepare task parameters
        json_data = {
            "container": "Persona",
            "dateIni": dateIni,
            "dateEnd": dateEnd,
            "dimensions": dimensions,
            "ids": ids or [],
            "filters": filters or [],
            "interFilters": interFilters or [],
        }

        # post and return response
        return await self.post(path="/api/data/cube", json=json_data, **kwargs)

    async def set_employee_calendar(
        self, *, employee: Union[int, str], calendar: str, **kwargs
    ) -> JSONResponse:
        """Get a calendar with name and assign to employee."""

        # searching employee
        search_employee = await self.get_element_def(
            container="Persona", elements=[employee]
        )
        if not search_employee:
            raise ValueError({"status": 404, "detail": "Employee not found"})

        # searching calendar
        query = Query(fields=["id", "name"], filterExp=f"this.name == '{calendar}'")
        calendars = await self.get_elements(container="Calendario", query=query)
        if not calendars.get("total"):
            raise ValueError({"status": 404, "detail": "Calendar not found"})

        # processing calendars
        employee_calendar = search_employee[0].get("Calendar")
        employee_calendar["Calendars"] = calendars.get("items")

        # assign position
        # for i in range(len(employee_calendar["Calendars"])):
        #     employee_calendar["Calendars"][i].update({"__elemPosition": i})

        async for i in async_range(len(employee_calendar["Calendars"])):
            employee_calendar["Calendars"][i].update({"__elemPosition": i})

        # saving data
        dataObj = {"Calendar": employee_calendar}

        return await self.save_element(
            container="Persona", elements=[employee], dataObj=dataObj, **kwargs
        )

    async def create_department_node(
        self, name: str, parent: int = -1, **kwargs
    ) -> JSONResponse:

        # constant return if element exist
        # EXIST_TEXT = "Ya existe un elemento con el mismo nombre descriptivo."

        # getting form
        node = self.get_create_form(container="Arbol")
        node["name"] = name
        node["idNodeParent"] = parent
        node["internalName"] = kwargs.get("internalName", None)

        # save new node
        new_elem = self.save_element(container="Arbol", dataObj=node, **kwargs)

        if self.defaults.Extra.NODE_EXISTS in new_elem[0].get("message"):
            return await self.create_department_node(
                name=name,
                parent=parent,
                internalName=create_random_suffix(name),
                **kwargs,
            )

        # if couldn't be created
        if new_elem[0].get("type") != 6:
            raise RuntimeError({"status": 500, "detail": new_elem[0].get("message")})

        return new_elem

    async def set_employee_department(
        self,
        employee: int,
        node_path: List[str],
        auto_create: bool = True,
        **kwargs,
    ) -> JSONResponse:

        def make_filter(parent: int) -> Callable:
            # create dynamic function
            def node_filter(department) -> bool:
                return department["idNodeParent"] == parent

            # return fynamic func
            return node_filter

        depto_id_rel = {}
        async for i in async_range(len(node_path)):
            # get elements by name
            query = Query(
                fields=["id", "name", "idNodeParent"],
                filterExp=f"this.name = '{node_path[i]}'",
            )
            departs = await self.get_elements(container="Arbol", query=query)

            # create dynamic filter
            filter_node = make_filter(depto_id_rel.get(node_path[i - 1], -1))

            # filter elements
            search = list(filter(filter_node, departs.get("items")))

            if not search:
                # raise if not auto_create
                if not auto_create:
                    raise ValueError({"status": 404, "detail": "Node not found"})

                # create node
                new_node = await self.create_department_node(
                    name=node_path[i],
                    parent=depto_id_rel.get(node_path[i - 1], -1),
                )

                # refresh search
                search = [new_node[0].get("dataObject")]

            # put result in rels
            depto_id_rel.update({node_path[i]: search[0].get("id")})

        # department structure
        object_assign = []
        if node_path:
            object_assign = [{"id": depto_id_rel.get(node_path[-1])}]

        # saving data
        dataObj = {"Departments": object_assign}

        return await self.save_element(
            container="Persona", elements=[employee], dataObj=dataObj, **kwargs
        )

    async def get_timetypes_ids(self) -> JSONResponse:

        # get nt resposne
        nt_timetypes = await self.get_elements(container="Incidencia")

        # parse response to list
        return [{"id": t.get("id")} for t in nt_timetypes.get("items")]

    async def get_readers_ids(self) -> JSONResponse:

        # get nt resposne
        nt_readers = await self.get_elements(container="Lector")

        # parse response to list
        [{"id": r.get("id")} for r in nt_readers.get("items")]

    async def import_employee(
        self, structure: dict, identifier: str = "nif", **kwargs
    ) -> JSONResponse:

        # employee structure
        data = {"container": "Persona"}

        # search employee by nif
        query = Query(
            fields=["id", identifier],
            filterExp=f'this.{identifier} = "{structure.get(identifier)}"',
        )
        results = await self.get_employees(query=query)

        # safety only
        if results.get("total") > 1:
            raise ValueError(
                {
                    "status": 400,
                    "detail": "More than one employee with the same identifier",
                }
            )

        # update employee
        if results.get("total") == 1:
            # set element
            data["elements"] = [results.get("items")[0].get("id")]
            # empty data
            dataObj = {}

        # create element
        else:
            # create form and assign all timetypes and readers
            dataObj = await self.get_create_form(container="Persona")

            # assign all if not in structure
            if not structure.get("TimeTypesEmployee"):
                dataObj.update({"TimeTypesEmployee": await self.get_timetypes_ids()})

            # assign all if not in structure
            if not structure.get("Readers"):
                dataObj.update({"Readers": await self.get_readers_ids()})

            # delete elements kw
            if data.get("elements", None):
                del data["elements"]

        dataObj.update(structure)
        data["dataObj"] = dataObj

        # save employee
        return await self.save_element(**data, **kwargs)
