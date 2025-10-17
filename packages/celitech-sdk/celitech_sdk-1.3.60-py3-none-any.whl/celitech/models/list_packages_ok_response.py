from typing import List
from typing import Union
from .utils.json_map import JsonMap
from .utils.base_model import BaseModel


@JsonMap(
    {
        "id_": "id",
        "destination_iso2": "destinationISO2",
        "data_limit_in_bytes": "dataLimitInBytes",
        "min_days": "minDays",
        "max_days": "maxDays",
        "price_in_cents": "priceInCents",
    }
)
class Packages(BaseModel):
    """Packages

    :param id_: ID of the package
    :type id_: str
    :param destination: ISO3 representation of the package's destination.
    :type destination: str
    :param destination_iso2: ISO2 representation of the package's destination.
    :type destination_iso2: str
    :param data_limit_in_bytes: Size of the package in Bytes
    :type data_limit_in_bytes: float
    :param min_days: Min number of days for the package
    :type min_days: float
    :param max_days: Max number of days for the package
    :type max_days: float
    :param price_in_cents: Price of the package in cents
    :type price_in_cents: float
    """

    def __init__(
        self,
        id_: str,
        destination: str,
        destination_iso2: str,
        data_limit_in_bytes: float,
        min_days: float,
        max_days: float,
        price_in_cents: float,
        **kwargs
    ):
        """Packages

        :param id_: ID of the package
        :type id_: str
        :param destination: ISO3 representation of the package's destination.
        :type destination: str
        :param destination_iso2: ISO2 representation of the package's destination.
        :type destination_iso2: str
        :param data_limit_in_bytes: Size of the package in Bytes
        :type data_limit_in_bytes: float
        :param min_days: Min number of days for the package
        :type min_days: float
        :param max_days: Max number of days for the package
        :type max_days: float
        :param price_in_cents: Price of the package in cents
        :type price_in_cents: float
        """
        self.id_ = id_
        self.destination = destination
        self.destination_iso2 = destination_iso2
        self.data_limit_in_bytes = data_limit_in_bytes
        self.min_days = min_days
        self.max_days = max_days
        self.price_in_cents = price_in_cents
        self._kwargs = kwargs


@JsonMap({"after_cursor": "afterCursor"})
class ListPackagesOkResponse(BaseModel):
    """ListPackagesOkResponse

    :param packages: packages
    :type packages: List[Packages]
    :param after_cursor: The cursor value representing the end of the current page of results. Use this cursor value as the "afterCursor" parameter in your next request to retrieve the subsequent page of results. It ensures that you continue fetching data from where you left off, facilitating smooth pagination
    :type after_cursor: str
    """

    def __init__(
        self, packages: List[Packages], after_cursor: Union[str, None], **kwargs
    ):
        """ListPackagesOkResponse

        :param packages: packages
        :type packages: List[Packages]
        :param after_cursor: The cursor value representing the end of the current page of results. Use this cursor value as the "afterCursor" parameter in your next request to retrieve the subsequent page of results. It ensures that you continue fetching data from where you left off, facilitating smooth pagination
        :type after_cursor: str
        """
        self.packages = self._define_list(packages, Packages)
        self.after_cursor = self._define_str(
            "after_cursor", after_cursor, nullable=True
        )
        self._kwargs = kwargs
