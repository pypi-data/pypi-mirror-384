from typing import Any, Optional, List, Union
from pydantic import BaseModel, Field
from datetime import date, datetime

END_DATE = "20501231"


class Company(BaseModel):
    code: str
    name: str


class Center(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None


class ExpiringCenter(BaseModel):
    center: Center
    dueDate: Optional[Union[date, datetime]]

    class Config:
        json_encoders = {
            date: lambda v: v.strftime("%Y%m%d"),
            datetime: lambda v: v.strftime("%Y%m%d%H%M%S"),
        }


class Card(BaseModel):
    number: str


class CardList(BaseModel):
    cards: List[Card]
    required: Optional[bool] = False


class OptionalData(BaseModel):
    level: int
    value: str


class Department(BaseModel):
    path: Optional[str] = Field(
        default=None,
        title="Department path",
        description=""" Can be like SPEC/AR/IT.
            Use 'sep_in' param if you need change the splitted character.
        """,
    )
    sep_in: Optional[str] = "/"
    sep_out: Optional[str] = ";"
    levels: Optional[Union[dict, list, tuple, set]] = Field(
        default=None,
        title="Department levels",
        description=""" Can be like a dict or iterable item. E.g.
            {"1": "SPEC", "2": "AR", "3": "IT"}
            ["SPEC", "AR", "IT"]
            ...
        """,
    )


class HighPeriod(BaseModel):
    start: date
    end: Optional[date] = None

    class Config:
        json_encoders = {
            date: lambda v: v.strftime("%Y%m%d"),
        }


class Employee(BaseModel):
    nif: str
    isActive: Optional[Union[bool, int, str]] = None
    enrollment: Optional[str] = None
    code: Optional[Union[int, str]] = None
    lastName: Optional[str] = None
    firstName: Optional[str] = None
    comment: Optional[str] = None
    company: Optional[Company] = None
    center: Optional[Center] = None
    expCenters: Optional[List[ExpiringCenter]] = None
    cardList: Optional[CardList] = None
    optionalData: Optional[List[OptionalData]] = None
    department: Optional[Department] = None
    activeDays: Optional[List[HighPeriod]] = None

    def _get_field(self, field_name: str) -> Optional[Any]:
        """
        Retrieves the value of a specified field from the instance.

        If a method named 'get_<field_name>' exists and is callable, it invokes that method and returns its result.
        Otherwise, it attempts to access the attribute with the given field name directly.

        Args:
            field_name (str): The name of the field to retrieve.

        Returns:
            Optional[Any]: The value of the field, or None if the field or method does not exist.
        """
        method = getattr(self, f"get_{field_name}", None)
        if callable(method):
            return method()
        return getattr(self, field_name, None)

    def to_params(self) -> dict:
        """
        Serializes the model to a dictionary of parameters, excluding fields specified in `Meta.nondefault` and unset fields.
        Nondefault fields are added back if they have a value.

        Returns:
            dict: A dictionary representation of the model suitable for parameter passing.
        """
        out = self.model_dump(
            mode="json",
            exclude=self.Meta.nondefault,
            exclude_unset=True,
        )

        # add nondefault fields
        for nondef in self.Meta.nondefault:
            nondef_value = self._get_field(nondef)
            if nondef_value:
                out.update(nondef_value)

        return out

    def get_activeDays(self) -> dict:
        """
        Returns a dictionary containing the active days in a specific string format.

        The returned dictionary has a single key "activeDays" whose value is a string
        representing the active date ranges. Each range is formatted as "YYYYMMDD|YYYYMMDD"
        (start date | end date), and multiple ranges are separated by commas.

        If there are no active days, returns an empty dictionary.

        Returns:
            dict: A dictionary with the formatted active days or an empty dictionary.
        """
        if not self.activeDays:
            return {}

        # convert to specific format
        # 20250101|20250615,20250701|20251231
        return {
            "activeDays": ",".join(
                [
                    "{}|{}".format(
                        ad.start.strftime("%Y%m%d"),
                        (ad.end.strftime("%Y%m%d") if ad.end else END_DATE),
                    )
                    for ad in self.activeDays
                ]
            )
        }

    def get_cardList(self) -> dict:
        """
        Returns a dictionary containing information about the card list.

        If `self.cardList` exists, the dictionary includes:
            - "cards": a comma-separated string of card numbers from `self.cardList.cards`.
            - "cardRequired": a boolean or value indicating if cards are required from `self.cardList.required`.

        If `self.cardList` is None or falsy, returns an empty dictionary.

        Returns:
            dict: Dictionary with card list information or empty if no card list is present.
        """
        return (
            {
                "cards": ",".join([str(c_.number) for c_ in self.cardList.cards]),
                "cardRequired": self.cardList.required,
            }
            if self.cardList
            else {}
        )

    def get_company(self) -> dict:
        """
        Returns a dictionary containing the company's code and name.

        Returns:
            dict: A dictionary with keys 'companyCode' and 'companyName' if the company exists,
                  otherwise an empty dictionary.
        """
        if not self.company:
            return {}

        return {
            "companyCode": self.company.code,
            "companyName": self.company.name,
        }

    def get_center(self) -> dict:
        """
        Retrieves information about the center associated with the instance.

        Returns:
            dict: A dictionary containing either the center's code under the key 'centerCode',
                  the center's name under the key 'centerName', or an empty dictionary if no center is set.
        """
        if not self.center:
            return {}

        if self.center.code:
            return {"centerCode": self.center.code}

        return {"centerName": self.center.name}

    def get_expCenters(self) -> dict:
        """
        Returns a dictionary containing a string representation of experimental centers and their due dates.

        If no experimental centers are present, returns an empty dictionary.

        Returns:
            dict: A dictionary with a single key "centers" whose value is a comma-separated string.
                  Each entry in the string is formatted as "<center_code>:<due_date>", where
                  <center_code> is the code of the center and <due_date> is the due date in "YYYYMMDD" format.
        """
        if not self.expCenters:
            return {}

        return {
            "centers": ",".join(
                [
                    "{}:{}".format(ec.center.code, ec.dueDate.strftime("%Y%m%d"))
                    for ec in self.expCenters
                ]
            )
        }

    def get_optionalData(self) -> dict:
        """
        Returns a dictionary containing the optional data for the instance.

        If optional data exists, it is returned as a dictionary with the key "optionalData"
        and the value as a comma-separated string of "level:value" pairs for each item in self.optionalData.
        If no optional data exists, an empty dictionary is returned.

        Returns:
            dict: A dictionary with the optional data or an empty dictionary.
        """
        if not self.optionalData:
            return {}

        return {
            "optionalData": ",".join(
                ["{}:{}".format(od.level, od.value) for od in self.optionalData]
            )
        }

    def get_department(self) -> dict:
        """
        Retrieves the department information as a dictionary.

        Returns:
            dict: A dictionary containing department details. The returned dictionary may include:
                - "departPath": The department path with separators replaced, if available.
                - "departLvl{n}": Department levels, either from a dict (keys as levels) or from a sequence (indexed levels).
                - An empty dictionary if no department information is available.
        """
        if not self.department:
            return {}

        # depart path like SPEC/AR/IT/ID
        if self.department.path:
            return {
                "departPath": self.department.path.replace(
                    self.department.sep_in, self.department.sep_out
                )
            }
        # have not path or levels
        if not self.department.levels:
            return {}

        # can be like {"1": "SPEC", }
        if isinstance(self.department.levels, dict):
            return {f"departLvl{k}": v for k, v in self.department.levels.items()}

        if isinstance(self.department.levels, (list, tuple, set)):
            return {
                f"departLvl{i+1}": self.department.levels[i]
                for i in range(len(self.department.levels))
            }

    class Config:
        json_encoders = {
            date: lambda v: v.strftime("%Y%m%d"),
            datetime: lambda v: v.strftime("%Y%m%d%H%M%S"),
        }

    class Meta:
        nondefault: set = {
            "cardList",
            "company",
            "center",
            "expCenters",
            "optionalData",
            "department",
            "activeDays",
        }
