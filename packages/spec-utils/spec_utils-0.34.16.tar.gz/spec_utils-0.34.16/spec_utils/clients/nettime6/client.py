from __future__ import annotations
import datetime as dt
import requests
from base64 import b64decode
from pathlib import Path
from typing import Any, Optional, Union, Dict
from spec_utils.clients.nettime6.query import Query
from spec_utils.utils import Decorators, create_random_suffix
from spec_utils.clients.http import OAuthClient, JSONResponse


__nettime__ = "6.0.1.19025"


class Client(OAuthClient):

    __name__ = "netTime6"

    def __init__(
        self,
        *,
        url: Union[str, Path],
        username: str,
        pwd: str,
        session: Optional[requests.Session] = None,
        session_cfg: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create a connector with nettime app using recived parameters

        Args:
            url (Union[str, Path]): Nettime url. Eg `https://server-name:8091/`
            username (str): Nettime username
            pwd (str): Nettime password
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

        self.headers = {"DNT": "1", "Accept-Encoding": "gzip,deflate"}

        # None values
        self.access_token = None
        self.user_rol = None
        self.settings = None

    def __enter__(self, *args, **kwargs) -> Client:
        return super().__enter__(*args, **kwargs)

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

    @Decorators.ensure_session
    def post(
        self,
        path: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        json: JSONResponse = None,
        **kwargs,
    ) -> JSONResponse:
        """
        Sends a POST request to nettime url.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param json: (optional) json data to send in the body of the
            :class:`Request`.
        :param **kwargs: Optional arguments that ``request`` takes.
        :return: json object
        :rtype: json
        """

        # to json -> json
        json_response = super().post(
            path=path, params=params, data=data, json=json, **kwargs
        )

        # get task results if is generated
        if isinstance(json_response, dict) and json_response.get("taskId", None):
            json_response = self.get_task_response(json_response.get("taskId"))

        # return json response
        return json_response

    def login(self) -> None:
        """Connect the client to set access_token and headers values."""

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
        json_data = self.post(path="/api/login", data=data)

        if not json_data.get("ok", None):
            raise ConnectionError({"status": 401, "detail": json_data.get("message")})

        # update access token and headers
        self.refresh_headers(access_token=json_data.get("access_token"))

        # refresh session with updated headers
        self.refresh_session()

        self.settings = self.get_settings()
        self.user_rol = self.get_user_rol()

    def logout(self) -> None:
        """Disconnect a client to clean the access_token."""

        if not self.is_connected:
            return

        # disconnect ...
        _ = self.post(path="/api/logout")

        # clean token and headers for safety
        self.refresh_headers(remove_token=True, remove_content_type=True)
        self.refresh_session()

    def relogin(self) -> None:
        """Reconnect client cleaning headers and access_token."""

        # logout and login. Will fail if has no token
        _ = self.logout()
        _ = self.login()

    def get_settings(self) -> dict:
        """Get settings of netTime Server."""

        return self.get(path="/api/settings")

    def get_user_rol(self) -> str:
        """Get user_rol of current session."""

        return self.settings.get("rol", None)

    def get_days_offset(self, days: list) -> list:
        """
        Convert a list ofdt.date or str format to int offset with
        self.setting.firstDate.

        :param days: list ofdt.date or formatted str to get int offsets.

        :return: :class:`list` object
        :rtype: list
        """

        # wait active conection
        if not self.is_connected:
            raise ConnectionError("Cliente desconectado. Utilice connect().")

        firstYear = self.settings.get("firstDate", None)
        if not firstYear:
            raise RuntimeError("No se puede obtener el setting firstDate.")

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

    def get_days_from_offsets(self, offsets: list) -> list:
        """
        Convert a list of int offset todt.date or str format with \
        self.setting.firstDate.

        :param offsets: list of int to get dates.

        :return: :class:dt.date` object
        :rtype:dt.date
        """

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
            date = first_date + dt.timedelta(days=offset)
            dates.append(date.isoformat())

        return dates

    def get_app_resource(self, name: str, **kwargs):
        """
        Get a resource from 'AppResources' folder. You can set export path in
        nettime folder and after use this method to get export content.

        :param name: str with name of resource -including extension-.
        :param **kwargs: Optional arguments that ``request`` takes.

        :return: :class:`dict` object or stream if 'stream' in kwargs
        :rtype: json or stream
        """

        # request.get
        return self.get(path=f"/AppResources/{name}", **kwargs)

    def get_fields(self, container: str, filterFields: bool = False):
        """
        Get all fields of an specific container.

        :param container: (str) Name of nettime container.
        :param filterFields: (bool) True if needs ignore expression fields.

        :return: json object
        :rtype: json
        """

        # prepare task parameters
        params = {"container": container, "filterFields": filterFields}

        # request.get
        return self.get(path="/api/container/fields", params=params)

    def get_elements(self, container: str, query=Query(["id", "name"]), **kwargs):
        """
        Get elements of an specific container for general propose.

        :param container: (str) Name of nettime container.
        :param query: (Query) Fields you want to get. Must be an instanceb of
            nettime6.Query. See more information in the class documentation.

        :param **kwargs: Optional arguments that ``request`` takes.

        :return: json object
        :rtype: json
        """

        # prepare task parameters
        params = {
            "pageStartIndex": 0,
            "pageSize": kwargs.get("pageSize", 50),
            "search": kwargs.get("search", ""),
            "order": kwargs.get("order", ""),
            "desc": kwargs.get("desc", ""),
            "container": container,
            "query": query.prepare(),
        }

        # request.get -> json
        json_response = self.get(path="/api/container/elements", params=params)

        # get task results
        if json_response.get("taskId", None):
            json_response = self.get_task_response(json_response.get("taskId"))

        return json_response

    def get_employees(self, query=Query(["id", "nif"]), **kwargs):
        """
        Get employees from nettime.

        :param query: (Query) Fields you want to get. Must be an instanceb of
            nettime6.Query. See more information in the class documentation.
        :param *args: Optional arguments that ``request`` takes.
        :param **kwargs: Optional arguments that ``request`` takes.

        :return: json object
        :rtype: json
        """

        # use get general propose
        employees = self.get_elements(container="Persona", query=query, **kwargs)

        # TODO: Check if recurssion is necessary

        return employees

    def container_action_exec(
        self,
        container: str,
        action: str,
        elements: list,
        all_: bool = False,
        dataObj: dict = None,
        **kwargs,
    ):
        """Execute an action for a container."""

        # prepare task parameters
        json_data = {
            "container": container,
            "action": action,
            "all": all_,
            "elements": elements,
            "dataObj": dataObj,
        }
        json_data.update(kwargs)

        # request.get -> json
        return self.post(path="/api/container/action/exec", json=json_data)

    def save_element(
        self,
        container: str,
        dataObj: dict,
        elements: list = [],
        all_: bool = False,
    ):
        """Update an element of a container with the received values."""

        # data prepare
        data = {
            "action": "Save",
            "container": container,
            "elements": elements,
            "all_": all_,
            "dataObj": dataObj,
        }

        # executing and processing
        return self.container_action_exec(**data)

    def delete_element(
        self,
        container: str,
        elements: list,
        confirm_: bool = True,
        all_: bool = False,
    ):
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
        return self.container_action_exec(**data)

    def get_for_duplicate(self, container: str, element: int, all_: bool = False):
        """Get form for a new element with data of recived element."""

        # data prepare
        data = {
            "action": "Copy",
            "container": container,
            "elements": [element],
            "all_": all_,
        }

        # executing and processing
        response = self.container_action_exec(**data)

        if not response:
            raise ValueError("Error obteniendo el formulario de duplicado.")

        # data of response
        obj = response[0]
        return obj.get("dataObj")

    def get_element_def(
        self,
        container: str,
        elements: list,
        all_: bool = False,
        read_only: bool = False,
        **kwargs,
    ):
        """Get all properties of an object/s."""

        # data prepare
        data = {
            "container": container,
            "elements": elements,
            "all_": all_,
            "action": "editForm" if not read_only else "View",
        }
        data.update(kwargs)

        # executing and processing
        response = self.container_action_exec(**data)

        elem_defs = []
        for elem in response:
            elem_defs.append(elem.get("dataObj"))

        return elem_defs

    def get_create_form(self, container: str, *args, **kwargs):
        """Get default data for a new element."""

        # data prepare
        data = {
            "container": container,
            "elements": [-1],
        }

        # execute and process
        response = self.get_element_def(**data, **kwargs)

        if not response:
            raise ValueError("Error obteniendo formulario de creación")

        return response[0]

    def get_day_info(
        self,
        employee: int,
        from_: str = dt.date.today().isoformat(),
        to: str = dt.date.today().isoformat(),
    ):
        """
        Get info, days, shifts, and results for a employe in a specific period.
        """

        # prepare task parameters
        params = {"idemp": employee, "from": from_, "to": to}

        # request.get -> json
        return self.get(path="/api/day/results", params=params)

    def get_access_clockings(
        self,
        employee: int,
        from_: str = dt.date.today().isoformat(),
        to: str = dt.date.today().isoformat(),
    ):
        """Get access clockings for a employe in a specific period."""

        # prepare task parameters
        params = {"idemp": employee, "from": from_, "to": to}

        # request.get -> json
        return self.get(path="/api/access/clockings", params=params)

    def get_task_status(self, task: int):
        """Get status of an async task."""

        # prepare task parameters
        params = {"taskid": task}

        # request.get -> json
        return self.get(path="/api/async/status", params=params)

    def get_task_response(self, task: int):
        """Return the result of a async task."""

        # ensure the task is complete
        task_status = self.get_task_status(task)
        while not task_status.get("completed", False):
            task_status = self.get_task_status(task)

        # prepare task parameters
        params = {"taskid": task}

        # request.get -> json
        return self.get(path="/api/async/response", params=params)

    def get_results(
        self,
        employee: int,
        from_: str = dt.date.today().isoformat(),
        to: str = dt.date.today().isoformat(),
    ):
        """Get results of day for a employee."""

        # prepare task parameters
        params = {
            "idemp": employee,
            "from": from_,
            "to": to,
        }

        # generate async task
        async_task = self.get(path="/api/results", params=params)

        # get task results
        return self.get_task_response(async_task.get("taskId"))

    def clocking_prepare(
        self,
        employee: int,
        date_time: dt.datetime,
        reader: int = -1,
        clocking_id: int = -1,
        action: str = None,
    ):
        """Return a dict element with recived data."""

        # ensuredt.datetime type
        if not isinstance(date_time, dt.datetime):
            date_time = dt.datetime.fromisoformat(date_time)

        # prepare structure
        clocking_data = {
            "id": clocking_id,
            "action": action,
            "app": True,
            "type": "timetypes",
            "date": date_time.isoformat(timespec="milliseconds"),
            "idReader": reader,
            "idElem": 0,
            "isNew": True if clocking_id == -1 else False,
        }

        return clocking_data

    def post_clocking(
        self, employee: int, date: str, time: str, reader: int = -1, **kwargs
    ):
        """Add a clocking to a employee in a specific date an time."""

        if self.user_rol == "Persona":
            raise ValueError("Método no soportado para el tipo 'Persona'.")

        # teime process
        if not isinstance(date, dt.date):
            date = dt.date.fromisoformat(date)

        if not isinstance(date, dt.time):
            time = dt.datetime.strptime(time, "%H:%M").time()

        date_time = dt.datetime.combine(date, time)

        json_data = {
            "idEmp": employee,
            "date": date.isoformat(),
            "clockings": [
                self.clocking_prepare(
                    employee=employee,
                    date_time=date_time,
                    reader=reader,
                    action=kwargs.get("action", None),
                    clocking_id=kwargs.get("clocking_id", -1),
                )
            ],
        }

        return self.post(path="/api/day/post/", json=json_data)

    def get_day_clockings(self, employee: int, date: str = dt.date.today().isoformat()):
        """
        Get all the clockings (Horario) of an employe in a specific day.
        ** This method use portal API.
        """

        # prepare task parameters
        params = {
            "path": "/api/clockings",
            "method": "get",
            "idemp": employee,
            "date": date,
        }

        # generate async task
        async_tasK = self.get(path="/api/clockings", params=params)

        # get and return task results
        return self.get_task_response(async_tasK.get("taskId"))

    def add_clocking(self, employee: int, date: str, time: str, reader: int = -1):
        """Add a clocking using post_clocking() method."""

        return self.post_clocking(employee=employee, date=date, time=time)

    def edit_clocking(self, employee: int, clocking_id: int, date: str, time: str):
        """Delete a clocking using post_clocking() method."""

        return self.post_clocking(
            employee=employee, date=date, time=time, clocking_id=clocking_id
        )

    def delete_clocking(self, employee: int, clocking_id: int, date: str, time: str):
        """Delete a clocking using post_clocking() method."""

        return self.post_clocking(
            employee=employee,
            date=date,
            time=time,
            action="Delete",
            clocking_id=clocking_id,
        )

    def add_planning(
        self,
        employee: int,
        name: str,
        days: list,
        allDay: bool = True,
        timetype: int = 0,
        extra_fields: Dict[str, Any] = {},
        **kwargs,
    ):
        """
        Create an absence planning for an employee on the indicated days using
        the received timetype.
        """

        # getting form and update data
        planning = self.get_create_form("Persona", action="NewPlanificacion")
        planning.update(
            {
                "name": name,
                "allDay": allDay,
                "allDayId": timetype,  # Timetype ID
                "employee": [employee],  # Employee ID
                "dateInterval": self.get_days_offset(days),
            }
        )
        planning.update(extra_fields)
        return self.save_element(
            container="IncidenciaFutura", dataObj=planning, **kwargs
        )

    def add_activator(
        self,
        name: str,
        employees: list,
        days: list,
        activator: int,
        value: int = None,
        comment: str = None,
    ):
        """
        Create an activator for an employee on the indicated days using \
        the received activator id.
        """

        new_activator = self.get_create_form(container="UsoActivadores")
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
                "days": self.get_days_offset(days),
                "employees": employees,
            }
        )

        # prepare and save data
        data = {
            "container": "UsoActivadores",
            "dataObj": new_activator,
        }
        return self.save_element(**data)

    def get_activity_monitor(self, employees: list, from_: str, to: str):
        """Return the activity monitor structure."""

        # prepare task parameters
        json_data = {
            "clockings": True,
            "from": from_,
            "to": to,
            "ids": employees,
        }

        # generate async task
        async_tasK = self.post(path="/api/planification/manager", json=json_data)

        # get and return task results
        return self.get_task_response(async_tasK.get("taskId"))

    def get_cube_results(
        self,
        dimensions: list,
        dateIni: str,
        dateEnd: str,
        interFilters: list = [],
        filters: list = [],
        ids: list = [],
    ):
        """
        Gets nettime results using the "Results Query" window engine.

        :param dimensions: List of list where each one contains the desired
            fields or results. The order of the values does matter.
        :param dateIni: Start day where you want to calculate.
        :param dateIni: End day where you want to calculate.
        :param interfilters: (Optional) If you use the "system" dimension,
            specify the ids of the results in this parameter.
        :param filters: (Optional) Nettime compatible filter expression.
        :param ids: (Optional) List of employee ids in case you want to filter.

        :return: :class:`list` object
        :rtype: json
        """

        # prepare task parameters
        json_data = {
            "container": "Persona",
            "dateIni": dateIni,
            "dateEnd": dateEnd,
            "ids": ids,
            "filters": filters,
            "dimensions": dimensions,
            "interFilters": interFilters,
        }

        # post and return response
        return self.post(path="/api/data/cube", json=json_data)

    def set_employee_calendar(self, employee: int, calendar: str):
        """Get a calendar with name and assign to employee."""

        # searching employee
        emp = self.get_element_def("Persona", elements=[employee])
        if not emp:
            raise ValueError("No se encuentra el empleado.")

        # searching calendar
        query = Query(fields=["id", "name"], filterExp=f"this.name == '{calendar}'")
        calendars = self.get_elements(container="Calendario", query=query)
        if not calendars.get("total"):
            raise ValueError("No se encuentra el calendario.")

        # processing calendars
        employee_calendar = emp[0].get("Calendar")
        employee_calendar["Calendars"] = calendars.get("items")

        # assign position
        for i in range(len(employee_calendar["Calendars"])):
            employee_calendar["Calendars"][i].update({"__elemPosition": i})

        # saving data
        data = {
            "container": "Persona",
            "elements": [employee],
            "dataObj": {"Calendar": employee_calendar},
        }

        return self.save_element(**data)

    def create_department_node(self, name: str, parent: int = -1, **kwargs):
        """Create a new node in department structure."""

        # constant return if element exist
        # EXIST_TEXT = "Ya existe un elemento con el mismo nombre descriptivo."

        # getting form
        node = self.get_create_form("Arbol")
        node["name"] = name
        node["idNodeParent"] = parent
        node["internalName"] = kwargs.get("internalName", None)

        # save new node
        new_elem = self.save_element(container="Arbol", dataObj=node)

        # if couldn't be created
        if new_elem[0].get("type") != 6 and kwargs.get("internalName", None):
            raise RuntimeError(new_elem[0].get("message"))

        if new_elem[0].get("type") != 6:
            return self.create_department_node(
                name=name,
                parent=parent,
                internalName=create_random_suffix(name),
            )

        return new_elem

    def set_employee_department(
        self, employee: int, node_path: list, auto_create: bool = True
    ):
        """Get a Department with list of names and assign to employee."""

        def make_filter(parent: int):
            # create dynamic function
            def node_filter(department):
                return department["idNodeParent"] == parent

            # return fynamic func
            return node_filter

        depto_id_rel = {}
        for i in range(len(node_path)):
            # get elements by name
            query = Query(
                fields=["id", "name", "idNodeParent"],
                filterExp=f"this.name = '{node_path[i]}'",
            )
            departs = self.get_elements(container="Arbol", query=query)

            # create dynamic filter
            filter_node = make_filter(depto_id_rel.get(node_path[i - 1], -1))

            # filter elements
            search = list(filter(filter_node, departs.get("items")))

            if not search:
                # raise if not auto_create
                if not auto_create:
                    raise ValueError("Nodo no encontrado")

                # create node
                new_node = self.create_department_node(
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
        data = {
            "container": "Persona",
            "elements": [employee],
            "dataObj": {"Departments": object_assign},
        }

        return self.save_element(**data)

    def get_timetypes_ids(self):
        """
        Gets and returns a list of ids of timetypes with a nettime client.
        """

        # get nt resposne
        nt_timetypes = self.get_elements("Incidencia").get("items")

        # parse response to list
        timetypes = []
        for timetype in nt_timetypes:
            timetypes.append({"id": timetype.get("id")})

        return timetypes

    def get_readers_ids(self):
        """
        Gets and returns a list of ids of readers with a nettime client.
        """

        # get nt resposne
        nt_readers = self.get_elements("Lector").get("items")

        # parse response to list
        readers = []
        for reader in nt_readers:
            readers.append({"id": reader.get("id")})

        return readers

    def import_employee(self, structure: dict, identifier: str = "nif", **kwargs):
        """
        Create an employe from a structure. Update if exists, create if not.

        :param structure: Dict with employee structure, like propertie: value.
        :param identifier: (Optional) String with nettime field name to identiy
            employee.

        :return: :class:`dict` object
        :rtype: json
        """

        # employee structure
        data = {"container": "Persona"}

        # search employee by nif
        query = Query(
            fields=["id", identifier],
            filterExp=f'this.{identifier} = "{structure.get(identifier)}"',
        )
        results = self.get_employees(query=query)

        # safety only
        if results.get("total") > 1:
            raise ValueError("More than one employee with the same identifier")

        # update employee
        if results.get("total") == 1:
            # set element
            data["elements"] = [results.get("items")[0].get("id")]
            # empty data
            dataObj = {}

        # create element
        else:
            # create form and assign all timetypes and readers
            dataObj = self.get_create_form(container="Persona")

            # assign all if not in structure
            if not structure.get("TimeTypesEmployee"):
                dataObj.update({"TimeTypesEmployee": self.get_timetypes_ids()})

            # assign all if not in structure
            if not structure.get("Readers"):
                dataObj.update({"Readers": self.get_readers_ids()})

            # delete elements kw
            if data.get("elements", None):
                del data["elements"]

        dataObj.update(structure)
        data["dataObj"] = dataObj

        # save employee
        return self.save_element(**data)
