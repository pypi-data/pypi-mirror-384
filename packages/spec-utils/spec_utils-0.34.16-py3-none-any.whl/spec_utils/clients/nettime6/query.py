from __future__ import annotations
from typing import List, Optional
import datetime as dt


class Query:

    def __init__(
        self,
        fields: list,
        startDate: Optional[str] = dt.date.today().isoformat(),
        filterExp: Optional[str] = "",
    ) -> None:
        self.queryfields = self.QueryFields(fields, startDate)
        self.filterExp = self.filter_prepare(expression=filterExp)

    def prepare(self) -> str:
        """Format a query in str for use in url."""

        query = '{}"fields":{}'.format("{", self.queryfields.prepare())

        if self.filterExp:
            query += f',"filterExp":"{self.filterExp}"'

        query += "}"
        return query

    def filter_prepare(self, expression: Optional[str] = "") -> str:
        return expression.replace('"', "'")

    class QueryFields:
        def __init__(
            self,
            names: List[str],
            startDate: Optional[str] = dt.date.today().isoformat(),
        ) -> None:
            self.names = names
            self.startDate = startDate

        def prepare(self) -> str:
            """Format a query in str for use in url."""

            fields = []
            for field in self.names:
                fields.append({"name": field, "startDate": self.startDate})

            return str(fields).replace("'", '"').replace(" ", "")
