from typing import List
from typing import Union
from .utils.json_map import JsonMap
from .utils.base_model import BaseModel
from .utils.sentinel import SENTINEL


@JsonMap(
    {
        "id_": "id",
        "data_limit_in_bytes": "dataLimitInBytes",
        "destination_iso2": "destinationISO2",
        "destination_name": "destinationName",
        "price_in_cents": "priceInCents",
    }
)
class Package(BaseModel):
    """Package

    :param id_: ID of the package
    :type id_: str
    :param data_limit_in_bytes: Size of the package in Bytes
    :type data_limit_in_bytes: float
    :param destination: ISO3 representation of the package's destination.
    :type destination: str
    :param destination_iso2: ISO2 representation of the package's destination.
    :type destination_iso2: str
    :param destination_name: Name of the package's destination
    :type destination_name: str
    :param price_in_cents: Price of the package in cents
    :type price_in_cents: float
    """

    def __init__(
        self,
        id_: str,
        data_limit_in_bytes: float,
        destination: str,
        destination_iso2: str,
        destination_name: str,
        price_in_cents: float,
        **kwargs
    ):
        """Package

        :param id_: ID of the package
        :type id_: str
        :param data_limit_in_bytes: Size of the package in Bytes
        :type data_limit_in_bytes: float
        :param destination: ISO3 representation of the package's destination.
        :type destination: str
        :param destination_iso2: ISO2 representation of the package's destination.
        :type destination_iso2: str
        :param destination_name: Name of the package's destination
        :type destination_name: str
        :param price_in_cents: Price of the package in cents
        :type price_in_cents: float
        """
        self.id_ = id_
        self.data_limit_in_bytes = data_limit_in_bytes
        self.destination = destination
        self.destination_iso2 = destination_iso2
        self.destination_name = destination_name
        self.price_in_cents = price_in_cents
        self._kwargs = kwargs


@JsonMap({})
class PurchasesEsim(BaseModel):
    """PurchasesEsim

    :param iccid: ID of the eSIM
    :type iccid: str
    """

    def __init__(self, iccid: str, **kwargs):
        """PurchasesEsim

        :param iccid: ID of the eSIM
        :type iccid: str
        """
        self.iccid = self._define_str("iccid", iccid, min_length=18, max_length=22)
        self._kwargs = kwargs


@JsonMap(
    {
        "id_": "id",
        "start_date": "startDate",
        "end_date": "endDate",
        "created_date": "createdDate",
        "start_time": "startTime",
        "end_time": "endTime",
        "created_at": "createdAt",
        "purchase_type": "purchaseType",
        "reference_id": "referenceId",
    }
)
class Purchases(BaseModel):
    """Purchases

    :param id_: ID of the purchase
    :type id_: str
    :param start_date: Start date of the package's validity in the format 'yyyy-MM-ddThh:mm:ssZZ'
    :type start_date: str
    :param end_date: End date of the package's validity in the format 'yyyy-MM-ddThh:mm:ssZZ'
    :type end_date: str
    :param created_date: Creation date of the purchase in the format 'yyyy-MM-ddThh:mm:ssZZ'
    :type created_date: str
    :param start_time: Epoch value representing the start time of the package's validity, defaults to None
    :type start_time: float, optional
    :param end_time: Epoch value representing the end time of the package's validity, defaults to None
    :type end_time: float, optional
    :param created_at: Epoch value representing the date of creation of the purchase, defaults to None
    :type created_at: float, optional
    :param package: package
    :type package: Package
    :param esim: esim
    :type esim: PurchasesEsim
    :param source: The `source` indicates whether the purchase was made from the API, dashboard, landing-page, promo-page or iframe. For purchases made before September 8, 2023, the value will be displayed as 'Not available'.
    :type source: str
    :param purchase_type: The `purchaseType` indicates whether this is the initial purchase that creates the eSIM (First Purchase) or a subsequent top-up on an existing eSIM (Top-up Purchase).
    :type purchase_type: str
    :param reference_id: The `referenceId` that was provided by the partner during the purchase or top-up flow. This identifier can be used for analytics and debugging purposes., defaults to None
    :type reference_id: str, optional
    """

    def __init__(
        self,
        id_: str,
        start_date: Union[str, None],
        end_date: Union[str, None],
        created_date: str,
        package: Package,
        esim: PurchasesEsim,
        source: str,
        purchase_type: str,
        start_time: Union[float, None] = SENTINEL,
        end_time: Union[float, None] = SENTINEL,
        created_at: float = SENTINEL,
        reference_id: Union[str, None] = SENTINEL,
        **kwargs
    ):
        """Purchases

        :param id_: ID of the purchase
        :type id_: str
        :param start_date: Start date of the package's validity in the format 'yyyy-MM-ddThh:mm:ssZZ'
        :type start_date: str
        :param end_date: End date of the package's validity in the format 'yyyy-MM-ddThh:mm:ssZZ'
        :type end_date: str
        :param created_date: Creation date of the purchase in the format 'yyyy-MM-ddThh:mm:ssZZ'
        :type created_date: str
        :param start_time: Epoch value representing the start time of the package's validity, defaults to None
        :type start_time: float, optional
        :param end_time: Epoch value representing the end time of the package's validity, defaults to None
        :type end_time: float, optional
        :param created_at: Epoch value representing the date of creation of the purchase, defaults to None
        :type created_at: float, optional
        :param package: package
        :type package: Package
        :param esim: esim
        :type esim: PurchasesEsim
        :param source: The `source` indicates whether the purchase was made from the API, dashboard, landing-page, promo-page or iframe. For purchases made before September 8, 2023, the value will be displayed as 'Not available'.
        :type source: str
        :param purchase_type: The `purchaseType` indicates whether this is the initial purchase that creates the eSIM (First Purchase) or a subsequent top-up on an existing eSIM (Top-up Purchase).
        :type purchase_type: str
        :param reference_id: The `referenceId` that was provided by the partner during the purchase or top-up flow. This identifier can be used for analytics and debugging purposes., defaults to None
        :type reference_id: str, optional
        """
        self.id_ = id_
        self.start_date = self._define_str("start_date", start_date, nullable=True)
        self.end_date = self._define_str("end_date", end_date, nullable=True)
        self.created_date = created_date
        self.start_time = self._define_number("start_time", start_time, nullable=True)
        self.end_time = self._define_number("end_time", end_time, nullable=True)
        self.created_at = self._define_number("created_at", created_at, nullable=True)
        self.package = self._define_object(package, Package)
        self.esim = self._define_object(esim, PurchasesEsim)
        self.source = source
        self.purchase_type = purchase_type
        self.reference_id = self._define_str(
            "reference_id", reference_id, nullable=True
        )
        self._kwargs = kwargs


@JsonMap({"after_cursor": "afterCursor"})
class ListPurchasesOkResponse(BaseModel):
    """ListPurchasesOkResponse

    :param purchases: purchases
    :type purchases: List[Purchases]
    :param after_cursor: The cursor value representing the end of the current page of results. Use this cursor value as the "afterCursor" parameter in your next request to retrieve the subsequent page of results. It ensures that you continue fetching data from where you left off, facilitating smooth pagination.
    :type after_cursor: str
    """

    def __init__(
        self, purchases: List[Purchases], after_cursor: Union[str, None], **kwargs
    ):
        """ListPurchasesOkResponse

        :param purchases: purchases
        :type purchases: List[Purchases]
        :param after_cursor: The cursor value representing the end of the current page of results. Use this cursor value as the "afterCursor" parameter in your next request to retrieve the subsequent page of results. It ensures that you continue fetching data from where you left off, facilitating smooth pagination.
        :type after_cursor: str
        """
        self.purchases = self._define_list(purchases, Purchases)
        self.after_cursor = self._define_str(
            "after_cursor", after_cursor, nullable=True
        )
        self._kwargs = kwargs
