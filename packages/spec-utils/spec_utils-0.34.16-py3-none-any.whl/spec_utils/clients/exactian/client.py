from __future__ import annotations
from base64 import b64encode, b64decode
from urllib.parse import urlparse, urljoin
import requests


class Client:
    def __init__(self, url: str, username: str, pwd: str, *args, **kwargs):
        self.client_url = urlparse(url)
        self.username = username
        self.pwd = b64encode(pwd.encode("utf-8"))
        # headers compression
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip,deflate",
        }

    def __enter__(self, *args, **kwargs) -> Client:
        return self

    def __exit__(self, *args, **kwargs):
        return

    def get(self, path: str, params: dict = None, **kwargs):
        """
        Sends a GET request to nettime url.

        :param path: path to add to URL for the new :class:`Request` object.
        :param params: (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
        :param **kwargs: Optional arguments that ``request`` takes.
        :return: :class:`dict` object
        :rtype: dict
        """

        # query prepare
        query = {
            "url": urljoin(self.client_url.geturl(), path),
            "params": params,
            "headers": self.headers,
            "timeout": kwargs.get("timeout", 10),
            "auth": (self.username, b64decode(self.pwd).decode("utf-8")),
        }

        # consulting nettime
        response = requests.get(**query)

        # raise if was an error
        if response.status_code not in range(200, 300):
            raise ConnectionError(response.text)

        # to json -> json
        try:
            return response.json()
        except Exception:
            return {}

    def get_employees(
        self,
        cuil: str = None,
        cuit: str = None,
        business_type_opening: str = None,
        detail: bool = False,
        **kwargs,
    ):
        """
        Use the endpoint to obtain the employees with the received data.

        :param cuil: Optional cuil to filter employee.
        :param cuit: Oprtional str to filter company.
        :param business_type_opening: Optional str to filter plant.
        :param detail: Optional bool to get detail of documents.
        :param **kwargs: Optional arguments that ``request`` takes.
            Check oficial site to get more info.

        :return: :class:`dict` object
        :rtype: json
        """

        # path prepare
        path = "ws2/employees/Status"

        # parameters prepare
        params = {
            "cuil": cuil,
            "cuit": cuit,
            "business_type_opening": business_type_opening,
            "detail": str(detail).lower(),
        }

        # request.get -> json
        return self.get(path=path, params=params, **kwargs)
