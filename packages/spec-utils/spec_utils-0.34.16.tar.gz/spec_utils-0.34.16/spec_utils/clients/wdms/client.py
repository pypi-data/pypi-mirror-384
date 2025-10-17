from __future__ import annotations
import datetime as dt
import requests
from base64 import b64decode
from pathlib import Path
from pydantic.decorator import validate_arguments
from typing import Any, List, Optional, Union, Dict
from urllib.parse import ParseResult
from spec_utils.clients.http import OAuthClient, JSONResponse
from spec_utils.schemas import JWT
from spec_utils.schemas.wdms import (
    Company,
    CompanyList,
    Area,
    AreaList,
    Department,
    DepartmentList,
    Position,
    PositionList,
    Terminal,
    TerminalList,
    Employee,
    EmployeeList,
    Transaction,
    TransactionList,
    PublicMessage,
    PublicMessageList,
    PrivateMessage,
    PrivateMessageList,
    WorkCode,
    WorkCodeList,
)


class Client(OAuthClient):

    __name__ = "WDMS"

    def __init__(
        self,
        *,
        url: Union[str, Path],
        username: str,
        pwd: str,
        session: Optional[requests.Session] = None,
        session_cfg: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            url=url,
            username=username,
            pwd=pwd,
            session=session,
            session_cfg=session_cfg,
        )

        self.headers = {}
        self.personnel_api_url = "/personnel/api/"
        self.device_api_url = "/iclock/api/"
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
            self.token = JWT(access_token=token.get("token", ""), token_type="JWT")

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

    def get(
        self,
        url: Optional[Union[str, Path, ParseResult]] = None,
        path: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Union[JSONResponse, requests.Response]:

        if kwargs.get("page", None):
            params.update({"page": kwargs.get("page")})
            kwargs.pop("page")
        if kwargs.get("page_size", None):
            params.update({"page_size": kwargs.get("page_size")})
            kwargs.pop("page_size")
        return super().get(url, path, params, **kwargs)

    def login(self) -> None:
        """Login to WDMS api."""

        if self.is_connected:
            return

        self.refresh_headers(remove_token=True)

        credentials = {
            "username": self.username,
            "password": b64decode(self.pwd).decode("utf-8"),
        }

        # consulting nettime
        json_data = self.post(path="/jwt-api-token-auth/", json=credentials)

        # update access token and headers
        self.refresh_headers(token=json_data)

        # refresh session with updated headers
        self.refresh_session()

    def logout(self) -> None:
        """Send a token to blacklist in backend."""

        if not self.is_connected:
            return

        # clean token and headers for safety
        self.refresh_headers(remove_token=True)
        self.refresh_session()

    def relogin(self) -> None:
        """Reconnect client cleaning headers and access_token."""

        # logout and login. Will fail if has no token
        _ = self.logout()
        _ = self.login()

    @validate_arguments
    def get_terminals(
        self,
        id: Optional[int] = None,
        sn: Optional[str] = None,
        sn_icontains: Optional[str] = None,
        alias: Optional[str] = None,
        alias_icontains: Optional[str] = None,
        ip_address: Optional[str] = None,
        area: Optional[int] = None,
        state: Optional[Union[str, int]] = None,
        company_code: Optional[str] = None,
        company_code_icontains: Optional[str] = None,
        company_name: Optional[str] = None,
        company_name_icontains: Optional[str] = None,
        **kwargs,
    ) -> Union[Terminal, TerminalList]:
        """Get terminal/s from WDMS api

        Args:
            id (Optional[int], optional):
                Use to get a single item.
                Defaults to None.
            sn (Optional[str], optional):
                Use to filter by serial number.
                Defaults to None.
            sn_icontains (Optional[str], optional):
                Use to filter by serial number.
                Defaults to None.
            alias (Optional[str], optional):
                Use to filter by alias.
                Defaults to None.
            alias_icontains (Optional[str], optional):
                Use to filter by alias.
                Defaults to None.
            ip_address (Optional[str], optional):
                Use to filter by ip_address.
                Defaults to None.
            area (Optional[int], optional):
                Use id to filter by area.
                Defaults to None.
            state (Optional[Union[str, int]], optional):
                Use to filter by state.
                Defaults to None.
            company_code (Optional[str], optional):
                Use to filter by company.
                Defaults to None.
            company_code_icontains (Optional[str], optional):
                Use to filter by company.
                Defaults to None.
            company_name (Optional[str], optional):
                Use to filter by company.
                Defaults to None.
            company_name_icontains (Optional[str], optional):
                Use to filter by company.
                Defaults to None.

        Returns:
            Union[Terminal, TerminalList]:
                `Terminal` if `id` is not `None`
                `TerminalList` if `id` is `None`
        """

        # path prepare
        path = "{}terminals/{}".format(self.device_api_url, f"{id}/" if id else "")

        # params prepare
        params = {
            "sn": sn,
            "sn_icontains": sn_icontains,
            "alias": alias,
            "alias_icontains": alias_icontains,
            "ip_address": ip_address,
            "area": area,
            "state": state,
            "company_code": company_code,
            "company_code_icontains": company_code_icontains,
            "company_name": company_name,
            "company_name_icontains": company_name_icontains,
        }

        # list structure
        if not id:
            return TerminalList(**self.get(path=path, params=params, **kwargs))

        # single structure
        return Terminal(**self.get(path=path, params=params, **kwargs))

    @validate_arguments
    def create_terminal(self, terminal: Terminal, **kwargs) -> Terminal:
        """Create a terminal with WDMS api

        Args:
            terminal (Terminal): `Terminal` schema instance.

        Returns:
            Terminal: `Terminal` schema instance.
        """

        return Terminal(
            **self.post(
                path=f"{self.device_api_url}terminals/",
                json=terminal.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def update_terminal(self, id: int, terminal: Terminal, **kwargs) -> Terminal:
        """Update a terminal with WDMS api

        Args:
            id (int): Terminal id.
            terminal (Terminal): `Terminal` schema instance.

        Returns:
            Terminal: `Terminal` schema instance.
        """

        return Terminal(
            **self.put(
                path=f"{self.device_api_url}terminals/{id}/",
                json=terminal.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def delete_terminal(self, id: int, **kwargs) -> bool:
        """Delete a terminal with WDMS api

        Args:
            id (int): Terminal id.

        Returns:
            bool: Operation result.
        """

        return self.delete(path=f"{self.device_api_url}terminals/{id}/", **kwargs)

    @validate_arguments
    def terminals_upload_all(self, terminals: List[int], **kwargs) -> Any:
        """Upload all to terminal from WDMS api

        Args:
            terminals (List[int]): List of terminal ids.

        Returns:
            Any: Operation result.
        """

        return self.post(
            path=f"{self.device_api_url}terminals/upload_all/",
            json={"terminals": terminals},
            **kwargs,
        )

    @validate_arguments
    def terminals_upload_transaction(self, terminals: List[int], **kwargs) -> Any:
        """Upload transactions to terminal from WDMS api

        Args:
            terminals (List[int]): List of terminal ids.

        Returns:
            Any: Operation result.
        """

        return self.post(
            path=f"{self.device_api_url}terminals/upload_transaction/",
            json={"terminals": terminals},
            **kwargs,
        )

    @validate_arguments
    def terminals_reboot(self, terminals: List[int], **kwargs) -> Any:
        """Reboot terminals from WDMS api

        Args:
            terminals (List[int]): List of terminal ids.

        Returns:
            Any: Operation result.
        """

        return self.post(
            path=f"{self.device_api_url}terminals/reboot/",
            json={"terminals": terminals},
            **kwargs,
        )

    @validate_arguments
    def get_employees(
        self,
        id: Optional[int] = None,
        emp_code: Optional[Union[str, int]] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        emp_code_icontains: Optional[str] = None,
        departments: Optional[int] = None,
        status: Optional[int] = None,
        first_name_icontains: Optional[str] = None,
        last_name_icontains: Optional[str] = None,
        areas: Optional[int] = None,
        position: Optional[int] = None,
        multiple_employee: Optional[str] = None,
        company_code: Optional[Union[int, str]] = None,
        **kwargs,
    ) -> Union[Employee, EmployeeList]:
        """Get employee/s from WDMS api

        Args:
            id (Optional[int], optional):
                Use to get a single item.
                Defaults to None.
            emp_code (Optional[Union[str, int]], optional):
                Use to filter by employee code.
                Defaults to None.
            first_name (Optional[str], optional):
                Use to filter by employee first name.
                Defaults to None.
            last_name (Optional[str], optional):
                Use to filter by employee last name.
                Defaults to None.
            emp_code_icontains (Optional[str], optional):
                Use to filter by employee code.
                Defaults to None.
            departments (Optional[int], optional):
                Use department id to filter by departments.
                Defaults to None.
            status (Optional[int], optional):
                Use to filter by status.
                Defaults to None.
            first_name_icontains (Optional[str], optional):
                Use to filter by employee first name.
                Defaults to None.
            last_name_icontains (Optional[str], optional):
                Use to filter by employee last name.
                Defaults to None.
            areas (Optional[int], optional):
                Use area id to filter by area.
                Defaults to None.
            position (Optional[int], optional):
                Use position id to filter by positions.
                Defaults to None.
            multiple_employee (Optional[str], optional):
                Use comma splited ids to filter by id.
                Defaults to None.
            company_code (Optional[Union[int, str]], optional):
                Use company code to filter by company.
                Defaults to None.

        Returns:
            Union[Employee, EmployeeList]:
                `Employee` if `id` is not `None`
                `EmployeeList` if `id` is `None`
        """

        # path prepare
        path = "{}employees/{}".format(self.personnel_api_url, f"{id}/" if id else "")

        # params prepare
        params = {
            "emp_code": emp_code,
            "first_name": first_name,
            "last_name": last_name,
            "emp_code_icontains": emp_code_icontains,
            "departments": departments,
            "status": status,
            "first_name_icontains": first_name_icontains,
            "last_name_icontains": last_name_icontains,
            "areas": areas,
            "position": position,
            "multiple_employee": multiple_employee,
            "company_code": company_code,
        }

        # list structure
        if not id:
            return EmployeeList(**self.get(path=path, params=params, **kwargs))

        # one element
        return Employee(**self.get(path=path, params=params, **kwargs))

    @validate_arguments
    def create_employee(self, employee: Employee, **kwargs) -> Employee:
        """Create a employee with WDMS api

        Args:
            employee (Employee): `Employee` schema instance.

        Returns:
            Employee: `Employee` schema instance.
        """

        return Employee(
            **self.post(
                path=f"{self.personnel_api_url}employees/",
                json=employee.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def update_employee(self, id: int, employee: Employee, **kwargs) -> Employee:
        """Update a employee with WDMS api

        Args:
            id (int): Employee id.
            employee (Employee): `Employee` schema instance.

        Returns:
            Employee: `Employee` schema instance.
        """

        return Employee(
            **self.put(
                path=f"{self.personnel_api_url}employees/{id}/",
                json=employee.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def delete_employee(self, id: int, **kwargs) -> bool:
        """Delete a employee with WDMS api

        Args:
            id (int): Employee id.

        Returns:
            bool: Operation result.
        """

        return self.delete(path=f"{self.personnel_api_url}employees/{id}/", **kwargs)

    @validate_arguments
    def get_departments(
        self,
        id: Optional[int] = None,
        dept_code: Optional[str] = None,
        dept_name: Optional[str] = None,
        parent_dept: Optional[Union[str, int]] = None,
        company: Optional[Union[str, int]] = None,
        dept_code_icontains: Optional[str] = None,
        dept_name_icontains: Optional[str] = None,
        **kwargs,
    ) -> Union[Department, DepartmentList]:
        """AI is creating summary for get_departments

        Args:
            id (Optional[int], optional):
                Use to get a single item.
                Defaults to None.
            dept_code (Optional[str], optional):
                Use to filter by code.
                Defaults to None.
            dept_name (Optional[str], optional):
                Use to filter by name.
                Defaults to None.
            parent_dept (Optional[Union[str, int]], optional):
                Use id to filter by parent.
                Defaults to None.
            company (Optional[Union[str, int]], optional):
                Use Company id to filter by company.
                Defaults to None.
            dept_code_icontains (Optional[str], optional):
                Use to filter by code.
                Defaults to None.
            dept_name_icontains (Optional[str], optional):
                Use to filter by name.
                Defaults to None.

        Returns:
            Union[Department, DepartmentList]:
                `Department` if `id` is not `None`
                `DepartmentList` if `id` is `None`
        """

        # path prepare
        path = "{}departments/{}".format(self.personnel_api_url, f"{id}/" if id else "")

        params = {
            "dept_code": dept_code,
            "dept_name": dept_name,
            "parent_dept": parent_dept,
            "company": company,
            "dept_code_icontains": dept_code_icontains,
            "dept_name_icontains": dept_name_icontains,
        }

        # list structure
        if not id:
            return DepartmentList(**self.get(path=path, params=params, **kwargs))

        # one element
        return Department(**self.get(path=path, params=params, **kwargs))

    @validate_arguments
    def create_department(self, department: Department, **kwargs) -> Department:
        """Create a department with WDMS api

        Args:
            department (Department): `Department` schema instance.

        Returns:
            Department: `Department` schema instance.
        """

        return Department(
            **self.post(
                path=f"{self.personnel_api_url}departments/",
                json=department.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def update_department(
        self, id: int, department: Department, **kwargs
    ) -> Department:
        """Update a department with WDMS api

        Args:
            id (int): Department id.
            department (Department): `Department` schema instance.

        Returns:
            Department: `Department` schema instance.
        """

        return Department(
            **self.put(
                path=f"{self.personnel_api_url}departments/{id}/",
                json=department.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def delete_department(self, id: int, **kwargs) -> bool:
        """Delete a department with WDMS api

        Args:
            id (int): Department id.

        Returns:
            bool: Operation result.
        """

        return self.delete(path=f"{self.personnel_api_url}departments/{id}/", **kwargs)

    @validate_arguments
    def get_companies(
        self,
        id: Optional[int] = None,
        company_code: Optional[str] = None,
        company_name: Optional[str] = None,
        **kwargs,
    ) -> Union[Company, CompanyList]:
        """Get company/companies from WDMS api

        Args:
            id (Optional[int], optional):
                Use to get a single item.
                Defaults to None.
            company_code (Optional[str], optional):
                Use to filter by code.
                Defaults to None.
            company_name (Optional[str], optional):
                Use to filter by name.
                Defaults to None.

        Returns:
            Union[Company, CompanyList]:
                `Company` if `id` is not `None`
                `CompanyList` if `id` is `None`
        """

        # path prepare
        path = "{}company/{}".format(self.personnel_api_url, f"{id}/" if id else "")

        params = {"company_code": company_code, "company_name": company_name}

        # list structure
        if not id:
            return CompanyList(**self.get(path=path, params=params, **kwargs))

        # one element
        return Company(**self.get(path=path, params=params, **kwargs))

    @validate_arguments
    def create_company(self, company: Company, **kwargs) -> Company:
        """Create a company with WDMS api

        Args:
            company (Company): `Company` schema instance.

        Returns:
            Company: `Company` schema instance.
        """

        return Company(
            **self.post(
                path=f"{self.personnel_api_url}company/",
                json=company.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def update_company(self, id: int, company: Company, **kwargs) -> Company:
        """Update a company with WDMS api

        Args:
            id (int): Company id.
            company (Company): `Company` schema instance.

        Returns:
            Company: `Company` schema instance.
        """

        return Company(
            **self.put(
                path=f"{self.personnel_api_url}company/{id}/",
                json=company.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def delete_company(self, id: int, **kwargs) -> bool:
        """Delete a company with WDMS api

        Args:
            id (int): Company id.

        Returns:
            bool: Operation result.
        """

        return self.delete(path=f"{self.personnel_api_url}company/{id}/", **kwargs)

    @validate_arguments
    def get_areas(
        self,
        id: Optional[int] = None,
        area_code: Optional[str] = None,
        area_name: Optional[str] = None,
        parent_area: Optional[Union[str, int]] = None,
        company: Optional[Union[str, int]] = None,
        area_code_icontains: Optional[str] = None,
        area_name_icontains: Optional[str] = None,
        **kwargs,
    ) -> Union[Area, AreaList]:
        """Get area/s from WDMS api

        Args:
            id (Optional[int], optional):
                Use to get a single item.
                Defaults to None.
            area_code (Optional[str], optional):
                Use to filter by code.
                Defaults to None.
            area_name (Optional[str], optional):
                Use to filter by name.
                Defaults to None.
            parent_area (Optional[Union[str, int]], optional):
                Use id to filter by parent.
                Defaults to None.
            company (Optional[Union[str, int]], optional):
                Use comapny id to filter by company.
                Defaults to None.
            area_code_icontains (Optional[str], optional):
                Use to filter by code.
                Defaults to None.
            area_name_icontains (Optional[str], optional):
                Use to filter by name.
                Defaults to None.

        Returns:
            Union[Area, AreaList]:
                `Area` if `id` is not `None`
                `AreaList` if `id` is `None`
        """

        # path prepare
        path = "{}areas/{}".format(self.personnel_api_url, f"{id}/" if id else "")

        params = {
            "area_code": area_code,
            "area_name": area_name,
            "parent_area": parent_area,
            "company": company,
            "area_code_icontains": area_code_icontains,
            "area_name_icontains": area_name_icontains,
        }

        # area or list structure
        if not id:
            return AreaList(**self.get(path=path, params=params, **kwargs))

        return Area(**self.get(path=path, params=params, **kwargs))

    @validate_arguments
    def create_area(self, area: Area, **kwargs) -> Area:
        """Create a area with WDMS api

        Args:
            area (Area): `Area` schema instance.

        Returns:
            Area: `Area` schema instance.
        """

        return Area(
            **self.post(
                path=f"{self.personnel_api_url}areas/",
                json=area.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def update_area(self, id: int, area: Area, **kwargs) -> Area:
        """Update a area with WDMS api

        Args:
            id (int): Area id.
            area (Area): `Area` schema instance.

        Returns:
            Area: `Area` schema instance.
        """

        return Area(
            **self.put(
                path=f"{self.personnel_api_url}areas/{id}/",
                json=area.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def delete_area(self, id: int, **kwargs) -> bool:
        """Delete a area with WDMS api

        Args:
            id (int): Area id.

        Returns:
            bool: Operation result.
        """

        return self.delete(path=f"{self.personnel_api_url}areas/{id}/", **kwargs)

    @validate_arguments
    def get_positions(
        self,
        id: Optional[int] = None,
        position_code: Optional[str] = None,
        position_name: Optional[str] = None,
        parent_position: Optional[Union[str, int]] = None,
        company: Optional[Union[str, int]] = None,
        position_code_icontains: Optional[str] = None,
        position_name_icontains: Optional[str] = None,
        **kwargs,
    ) -> Union[Position, PositionList]:
        """Get position/s from WDMS api

        Args:
            id (Optional[int], optional):
                Use to get a single item.
                Defaults to None.
            position_code (Optional[str], optional):
                Use to filter by code.
                Defaults to None.
            position_name (Optional[str], optional):
                Use to filter by name.
                Defaults to None.
            parent_position (Optional[Union[str, int]], optional):
                Use id to filter by parent.
                Defaults to None.
            company (Optional[Union[str, int]], optional):
                Use company id to filter by company.
                Defaults to None.
            position_code_icontains (Optional[str], optional):
                Use to filter by code.
                Defaults to None.
            position_name_icontains (Optional[str], optional):
                Use to filter by name.
                Defaults to None.

        Returns:
            Union[Position, PositionList]:
                `Position` if `id` is not `None`
                `PositionList` if `id` is `None`
        """

        # path prepare
        path = "{}positions/{}".format(self.personnel_api_url, f"{id}/" if id else "")

        params = {
            "position_code": position_code,
            "position_name": position_name,
            "parent_position": parent_position,
            "company": company,
            "position_code_icontains": position_code_icontains,
            "position_name_icontains": position_name_icontains,
        }

        # list structure
        if not id:
            return PositionList(**self.get(path=path, params=params, **kwargs))

        return Position(**self.get(path=path, params=params, **kwargs))

    @validate_arguments
    def create_position(self, position: Position, **kwargs) -> Position:
        """Create a position with WDMS api

        Args:
            position (Position): `Position` schema instance.

        Returns:
            Position: `Position` schema instance.
        """

        return Position(
            **self.post(
                path=f"{self.personnel_api_url}positions/",
                json=position.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def update_position(self, id: int, position: Position, **kwargs) -> Position:
        """Update a position with WDMS api

        Args:
            id (int): Position id.
            position (Position): `Position` schema instance.

        Returns:
            Position: `Position` schema instance.
        """

        return Position(
            **self.put(
                path=f"{self.personnel_api_url}positions/{id}/",
                json=position.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def delete_position(self, id: int, **kwargs) -> bool:
        """Delete a position with WDMS api

        Args:
            id (int): Position id.

        Returns:
            bool: Operation result.
        """

        return self.delete(path=f"{self.personnel_api_url}positions/{id}/", **kwargs)

    @validate_arguments
    def get_transactions(
        self,
        id: Optional[int] = None,
        id_more_than: Optional[int] = None,
        emp_code: Optional[str] = None,
        terminal_sn: Optional[str] = None,
        terminal_alias: Optional[str] = None,
        start_time: Optional[Union[dt.date, dt.datetime, str]] = None,
        end_time: Optional[Union[dt.date, dt.datetime, str]] = None,
        upload_time: Optional[Union[dt.date, dt.datetime, str]] = None,
        upload_time_more_than: Optional[Union[dt.date, dt.datetime, str]] = None,
        **kwargs,
    ) -> Union[Transaction, TransactionList]:
        """AI is creating summary for get_transactions

        Args:
            id (Optional[int], optional):
                Use to get a single item.
                Defaults to None.
            id_more_than (Optional[int], optional):
                Use to filter by id.
                Defaults to None.
            emp_code (Optional[str], optional):
                Use to filter by employee.
                Defaults to None.
            terminal_sn (Optional[str], optional):
                Use to filter by terminal.
                Defaults to None.
            terminal_alias (Optional[str], optional):
                Use to filter by terminal.
                Defaults to None.
            start_time (Optional[Union[dt.date, dt.datetime, str]], optional):
                Use to filter by start_time.
                Defaults to None.
            end_time (Optional[Union[dt.date, dt.datetime, str]], optional):
                Use to filter by end_time.
                Defaults to None.
            upload_time (Optional[Union[dt.date, dt.datetime, str]], optional):
                Use to filter by upload_time.
                Defaults to None.
            upload_time_more_than (
                Optional[Union[dt.date, dt.datetime, str]], optional
            ):
                Use to filter by upload_time.
                Defaults to None.

        Returns:
            Union[Transaction, TransactionList]:
                `Transaction` if `id` is not `None`
                `TransactionList` if `id` is `None`
        """

        # path prepare
        path = "{}transactions/{}".format(self.device_api_url, f"{id}/" if id else "")

        # params prepare
        params = {
            "id_more_than": id_more_than,
            "emp_code": emp_code,
            "terminal_sn": terminal_sn,
            "terminal_alias": terminal_alias,
            "start_time": start_time,
            "end_time": end_time,
            "upload_time": upload_time,
            "upload_time_more_than": upload_time_more_than,
        }

        # list structure
        if not id:
            return TransactionList(**self.get(path=path, params=params, **kwargs))

        # single structure
        return Transaction(**self.get(path=path, params=params, **kwargs))

    @validate_arguments
    def delete_transaction(self, id: int, **kwargs) -> bool:
        """Delete a transaction with WDMS api

        Args:
            id (int): Transaction id.

        Returns:
            bool: Operation result.
        """

        return self.delete(path=f"{self.device_api_url}transactions/{id}/", **kwargs)

    @validate_arguments
    def get_public_messages(
        self,
        id: Optional[int] = None,
        terminal: Optional[int] = None,
        start_time: Optional[Union[dt.date, dt.datetime, str]] = None,
        duration: Optional[int] = None,
        **kwargs,
    ) -> Union[PublicMessage, PublicMessageList]:
        """Get public messages/s from WDMS api

        Args:
            id (Optional[int], optional):
                Use to get a single item.
                Defaults to None.
            terminal (Optional[int], optional):
                Use terminal id to filter by terminal.
                Defaults to None.
            start_time (Optional[Union[dt.date, dt.datetime, str]], optional):
                Use to filter by start_time.
                Defaults to None.
            duration (Optional[int], optional):
                Use to filter by duration.
                Defaults to None.

        Returns:
            Union[PublicMessage, PublicMessageList]:
                `PublicMessage` if `id` is not `None`
                `PublicMessageList` if `id` is `None`
        """

        # path prepare
        path = "{}publicmessages/{}".format(self.device_api_url, f"{id}/" if id else "")

        # params prepare
        params = {
            "terminal": terminal,
            "start_time": start_time,
            "duration": duration,
        }

        # list structure
        if not id:
            return PublicMessageList(**self.get(path=path, params=params, **kwargs))

        # single structure
        return PublicMessage(**self.get(path=path, params=params, **kwargs))

    @validate_arguments
    def create_public_message(
        self, public_message: PublicMessage, **kwargs
    ) -> PublicMessage:
        """Create a public message with WDMS api

        Args:
            public_message (PublicMessage): `PublicMessage` schema instance.

        Returns:
            PublicMessage: `PublicMessage` schema instance.
        """

        return PublicMessage(
            **self.post(
                path=f"{self.device_api_url}publicmessages/",
                json=public_message.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def update_public_message(
        self, id: int, public_message: PublicMessage, **kwargs
    ) -> PublicMessage:
        """Update a public message with WDMS api

        Args:
            id (int): Public Message id.
            public_message (PublicMessage): `PublicMessage` schema instance.

        Returns:
            PublicMessage: `PublicMessage` schema instance.
        """

        return PublicMessage(
            **self.put(
                path=f"{self.device_api_url}publicmessages/{id}/",
                json=public_message.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def delete_public_message(self, id: int, **kwargs) -> bool:
        """Delete a public message with WDMS api

        Args:
            id (int): Public Message id.

        Returns:
            bool: Operation result.
        """

        return self.delete(path=f"{self.device_api_url}publicmessages/{id}/", **kwargs)

    @validate_arguments
    def get_private_messages(
        self,
        id: Optional[int] = None,
        employee: Optional[int] = None,
        start_time: Optional[Union[dt.date, dt.datetime, str]] = None,
        duration: Optional[int] = None,
        **kwargs,
    ) -> Union[PrivateMessage, PrivateMessageList]:
        """Get private messages/s from WDMS api

        Args:
            id (Optional[int], optional):
                Use to get a single item.
                Defaults to None.
            employee (Optional[int], optional):
                Use employee id to filter by employee.
                Defaults to None.
            start_time (Optional[Union[dt.date, dt.datetime, str]], optional):
                Use to filter by start_time.
                Defaults to None.
            duration (Optional[int], optional):
                Use to filter by duration.
                Defaults to None.

        Returns:
            Union[PrivateMessage, PrivateMessageList]:
                `PrivateMessage` if `id` is not `None`
                `PrivateMessageList` if `id` is `None`
        """

        # path prepare
        path = "{}privatemessages/{}".format(
            self.device_api_url, f"{id}/" if id else ""
        )

        # params prepare
        params = {
            "employee": employee,
            "start_time": start_time,
            "duration": duration,
        }

        # list structure
        if not id:
            return PrivateMessageList(**self.get(path=path, params=params, **kwargs))

        # single structure
        return PrivateMessage(**self.get(path=path, params=params, **kwargs))

    @validate_arguments
    def create_private_message(
        self, private_message: PrivateMessage, **kwargs
    ) -> PrivateMessage:
        """Create a private message with WDMS api

        Args:
            private_message (PrivateMessage): `PrivateMessage` schema instance.

        Returns:
            PrivateMessage: `PrivateMessage` schema instance.
        """

        return PrivateMessage(
            **self.post(
                path=f"{self.device_api_url}privatemessages/",
                json=private_message.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def update_private_message(
        self, id: int, private_message: PrivateMessage, **kwargs
    ) -> PrivateMessage:
        """Update a private message with WDMS api

        Args:
            id (int): Private Message id.
            private_message (PrivateMessage): `PrivateMessage` schema instance.

        Returns:
            PrivateMessage: `PrivateMessage` schema instance.
        """

        return PrivateMessage(
            **self.put(
                path=f"{self.device_api_url}privatemessages/{id}/",
                json=private_message.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def delete_private_message(self, id: int, **kwargs) -> bool:
        """Delete a private message with WDMS api

        Args:
            id (int): Private Message id.

        Returns:
            bool: Operation result.
        """

        return self.delete(path=f"{self.device_api_url}privatemessages/{id}/", **kwargs)

    @validate_arguments
    def get_work_codes(
        self,
        id: Optional[int] = None,
        code: Optional[str] = None,
        alias: Optional[str] = None,
        last_activity: Optional[Union[dt.date, dt.datetime, str]] = None,
        **kwargs,
    ) -> Union[WorkCode, WorkCodeList]:
        """Get work code/s from WDMS api

        Args:
            id (Optional[int]):
                Use to get a single item.
                Defaults to None.
            code (Optional[str], optional):
                Use to filter by code.
                Defaults to None.
            alias (Optional[str], optional):
                Use to filter by alias.
                Defaults to None.
            last_activity (
                Optional[Union[dt.date, dt.datetime, str]], optional
            ):
                Use to filter by last_activity.
                Defaults to None.

        Returns:
            Union[WorkCode, WorkCodeList]:
                `WorkCode` if `id` is not `None`
                `WorkCodeList` if `id` is `None`
        """

        # path prepare
        path = "{}workcodes/{}".format(self.device_api_url, f"{id}/" if id else "")

        # params prepare
        params = {"code": code, "alias": alias, "last_activity": last_activity}

        # list structure
        if not id:
            return WorkCodeList(**self.get(path=path, params=params, **kwargs))

        # single structure
        return WorkCode(**self.get(path=path, params=params, **kwargs))

    @validate_arguments
    def create_work_code(self, work_code: WorkCode, **kwargs) -> WorkCode:
        """Create a work code with WDMS api

        Args:
            work_code (WorkCode): `WorkCode` schema instance.

        Returns:
            WorkCode: `WorkCode` schema instance.
        """

        return WorkCode(
            **self.post(
                path=f"{self.device_api_url}workcodes/",
                json=work_code.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def update_work_code(self, id: int, work_code: WorkCode, **kwargs) -> WorkCode:
        """Update a work code with WDMS api
        Args:
            id (int): WorkCode id.
            work_code (WorkCode): `WorkCode` schema instance.

        Returns:
            WorkCode: `WorkCode` schema instance.
        """

        return WorkCode(
            **self.put(
                path=f"{self.device_api_url}workcodes/{id}/",
                json=work_code.dict(exclude_unset=True),
                **kwargs,
            )
        )

    @validate_arguments
    def delete_work_code(self, id: int, **kwargs) -> bool:
        """Delete a work code with WDMS api

        Args:
            id (int): WorkCode id.

        Returns:
            bool: Operation result.
        """

        return self.delete(path=f"{self.device_api_url}workcodes/{id}/", **kwargs)
