from __future__ import annotations
import datetime as dt
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
import pandas as pd
import sqlalchemy
from secrets import token_hex
from sqlalchemy.pool import NullPool


class Client:

    def __init__(
        self,
        username: str,
        pwd: str,
        server: str,
        database: str,
        port: int = 1433,
        driver: str = "mssql+pyodbc",
        controller: str = "SQL Server",
    ) -> None:

        self.engine_params = sqlalchemy.engine.url.URL(
            drivername=driver,
            username=username,
            password=pwd,
            host=server,
            port=port,
            database=database,
            query={"driver": controller},
        )

        self.engine = sqlalchemy.create_engine(self.engine_params, poolclass=NullPool)

    def __enter__(self, *args, **kwargs) -> Client:
        return self

    def __exit__(self, *args, **kwargs):
        return self.dispose()

    def dispose(self):
        return self.engine.dispose()

    @property
    def table_names(self):
        return self.engine.table_names()

    def query_execute(self, query: str, to_records: bool = False, **kwargs):
        """
        Open/close connection and Execute a custom query and return result.
        """

        # create connection and execute query
        connection = self.engine.execute(query, **kwargs)

        # if query doesn't return rows, return bool
        if not connection.returns_rows:
            # safety only
            connection.close()
            # return affected rows
            return connection.rowcount

        # create dataframe with result
        df = pd.DataFrame(connection.fetchall(), columns=connection.keys())

        # close connection --safety--
        connection.close()

        # return json format
        if to_records:
            return df.to_dict("records")

        # return pandas DataFrame
        return df

    def read_sql_query(
        self, query: str, to_records: bool = False
    ) -> Union[List[Dict], pd.DataFrame]:
        """Execute query with active engine and return pandas dataframe."""

        # query execute
        df = pd.read_sql_query(query, self.engine)

        if to_records:
            # return json format
            return df.to_dict("records")

        return df

    def insert_values(
        self,
        df: pd.DataFrame,
        table: str,
        schema: str = None,
        if_exists: str = "append",
        index: bool = False,
        index_label: str = None,
        chunksize: int = None,
        method: str = None,
        from_records: bool = False,
    ) -> Optional[int]:
        """Insert a dataframe in database with recived data."""

        if from_records and not isinstance(df, pd.DataFrame):
            # create pandas dataframe
            df = pd.DataFrame.from_records(df)

        # to sql
        return df.to_sql(
            name=table,
            con=self.engine,
            schema=schema,
            if_exists=if_exists,
            index=index,
            index_label=index_label,
            chunksize=chunksize,
            method=method,
        )

        # return true for general propose
        # return True

    def run_import_lips(
        self,
        table: str,
        lips_name: str,
        hash_: str = None,
        source: str = "spec-utils",
        downconf_table: str = "AR_DOWNCONF",
        **kwargs,
    ) -> Optional[int]:
        """Insert into AR_DOWN_CONF table so LIPS can import."""

        # create dataframe
        df = pd.DataFrame(
            [
                {
                    "DATE_TIME": dt.datetime.now(),
                    "TABLE_NAME": table,
                    "PARTIAL": True,
                    "SOURCE": source,
                    "LIPS": lips_name,
                    "HASH_CODE": hash_ or token_hex(8),
                    "END_TIME": None,
                }
            ]
        )

        # insert in AR_DOWNCONF
        return self.insert_values(df=df, table=downconf_table, **kwargs)

    def get_from_table(
        self,
        table: str,
        fields: list = ["*"],
        top: int = 5,
        where: str = None,
        group_by: list = [],
        **kwargs,
    ) -> Union[List[Dict], pd.DataFrame]:
        """Create and execute a query for get results from Database."""

        # create query
        query = "SELECT {}{} FROM {}{}{}".format(
            f"TOP {top}" if top else "",
            ", ".join(fields),
            table,
            f" WHERE {where}" if where else "",
            f" GROUP BY {group_by}" if group_by else "",
        )

        # return results
        return self.read_sql_query(query=query, **kwargs)

    def get_employees(
        self, table: str = "PERSONAS", **kwargs
    ) -> Union[List[Dict], pd.DataFrame]:
        """Get employees from database."""

        return self.get_from_table(table=table, **kwargs)

    def get_exports(
        self, table: str = "AR_EXPORTS", **kwargs
    ) -> Union[List[Dict], pd.DataFrame]:
        return self.get_from_table(table=table, **kwargs)

    def get_raw_exports(
        self, table: str = "AR_EXPORTS", include_previous: bool = True, **kwargs
    ) -> Union[List[Tuple[Any, Any]], List[Dict], pd.DataFrame]:

        where = "EXP_STATUS='PENDING'"
        pendings = self.get_from_table(table=table, where=where, **kwargs)

        if not include_previous:
            return pendings

        # when include previous, ever work with to_records
        pairs: List[Tuple[Any, Any]] = []
        _ecc = "EXP_CENTER_CODE"
        _ect = "EXP_COUNTERS_TEMPLATE"
        _edt = "EXP_DATE_TO"
        _edf = "EXP_DATE_FROM"

        pendings = (
            pendings if isinstance(pendings, list) else pendings.to_dict("records")
        )

        for _pending in pendings:
            _previous = self.get_from_table(
                table=table,
                where=str(
                    "EXP_STATUS='COMPLETED' and EXP_OK=1 and "
                    f"{_ecc}='{_pending[_ecc]}' and "
                    f"{_ect}='{_pending[_ect]}' and "
                    f"{_edt} between {_pending[_edf]} and {_pending[_edt]}"
                ),
                to_records=True,
            )

            if _previous:
                pairs.append((_pending, _previous[0]))
            else:
                pairs.append((_pending, None))

        return pairs

    def set_export_status(
        self,
        export_ids: Iterable[Union[int, str]],
        status: str,
        table: str = "AR_EXPORTS",
        result: Optional[Union[str, int]] = "NULL",
        **kwargs,
    ):
        ids = ",".join(list(map(str, export_ids)))
        # _result = "NULL" if result is None else result
        q_ = "UPDATE {} SET EXP_STATUS='{}', EXP_OK={} WHERE EXP_ID in ({});"
        query = q_.format(table, status, result, ids)
        return self.query_execute(query)

    def get_export_items(
        self,
        export_ids: List[Tuple[Union[int, str], Optional[Union[int, str]]]],
        table: str = "AR_EXPORT_ITEMS",
        auto_update: bool = True,
        update_first_only: bool = True,
        **kwargs,
    ) -> Union[List[Dict], pd.DataFrame]:

        all_ = set()
        first_only = set()
        for item in export_ids:
            if isinstance(item, int):
                # only one element
                all_.add(item)
                first_only.add(item)
            else:
                # iterable (include current and previous)
                all_.add(item[0])
                first_only.add(item[0])
                if item[1]:
                    # if previous is not None
                    all_.add(item[1])

        ids = ",".join(list(map(str, all_)))
        exports = self.get_exports(
            table="AR_EXPORTS",
            where=f"EXP_ID in ({ids})",
            top=100,
            to_records=True,
        )
        if not exports:
            raise ValueError(f"Not exports with id in ({ids})")

        export_items = self.get_from_table(
            table=table, where=f"EXP_ID in ({ids})", **kwargs
        )

        if auto_update:
            _ = self.set_export_status(
                export_ids=first_only if update_first_only else all_,
                status="PROCESSING",
            )

        return export_items

    def import_employees(
        self,
        employees: pd.DataFrame,
        table: str = "AR_IMP_PERSONAL",
        lips_name: str = "IMP_PERSONAL",
        chunksize: int = 300,
        **kwargs,
    ) -> Union[bool, int, None]:
        """Insert a dataframe of employees in database."""

        # do nothing with empty dataframe
        if employees.empty:
            return True

        # insert dataframe
        try:
            self.insert_values(df=employees, table=table, chunksize=chunksize)

            # force import inserting new line in ar_down_conf
            return self.run_import_lips(table=table, lips_name=lips_name, **kwargs)

        except Exception as err:
            raise RuntimeError(f"Error inserting employees in DB.\n{str(err)}")

    def sync_results(
        self, from_table: str, marc_col: str, auto_update: bool = True, **kwargs
    ) -> Union[List[Dict], pd.DataFrame]:
        """
        Get rows from table with marc_col = 0 (False).
        After of get rows, update marc_col to 1 (True).
        """

        # get rows
        results = self.get_from_table(
            table=from_table, where=f"{marc_col} = 0", **kwargs
        )

        if auto_update:
            # query prepare and execute
            _ = self.query_execute(
                f"UPDATE {from_table} SET {marc_col} = 1 WHERE {marc_col} = 0;"
            )

        # return rows
        return results
