from typing import Union
from .utils.json_map import JsonMap
from .utils.base_model import BaseModel
from .utils.sentinel import SENTINEL


@JsonMap(
    {
        "id_": "id",
        "package_id": "packageId",
        "start_date": "startDate",
        "end_date": "endDate",
        "created_date": "createdDate",
        "start_time": "startTime",
        "end_time": "endTime",
    }
)
class TopUpEsimOkResponsePurchase(BaseModel):
    """TopUpEsimOkResponsePurchase

    :param id_: ID of the purchase
    :type id_: str
    :param package_id: ID of the package
    :type package_id: str
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
    """

    def __init__(
        self,
        id_: str,
        package_id: str,
        start_date: Union[str, None],
        end_date: Union[str, None],
        created_date: str,
        start_time: Union[float, None] = SENTINEL,
        end_time: Union[float, None] = SENTINEL,
        **kwargs
    ):
        """TopUpEsimOkResponsePurchase

        :param id_: ID of the purchase
        :type id_: str
        :param package_id: ID of the package
        :type package_id: str
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
        """
        self.id_ = id_
        self.package_id = package_id
        self.start_date = self._define_str("start_date", start_date, nullable=True)
        self.end_date = self._define_str("end_date", end_date, nullable=True)
        self.created_date = created_date
        self.start_time = self._define_number("start_time", start_time, nullable=True)
        self.end_time = self._define_number("end_time", end_time, nullable=True)
        self._kwargs = kwargs


@JsonMap({})
class TopUpEsimOkResponseProfile(BaseModel):
    """TopUpEsimOkResponseProfile

    :param iccid: ID of the eSIM
    :type iccid: str
    """

    def __init__(self, iccid: str, **kwargs):
        """TopUpEsimOkResponseProfile

        :param iccid: ID of the eSIM
        :type iccid: str
        """
        self.iccid = self._define_str("iccid", iccid, min_length=18, max_length=22)
        self._kwargs = kwargs


@JsonMap({})
class TopUpEsimOkResponse(BaseModel):
    """TopUpEsimOkResponse

    :param purchase: purchase
    :type purchase: TopUpEsimOkResponsePurchase
    :param profile: profile
    :type profile: TopUpEsimOkResponseProfile
    """

    def __init__(
        self,
        purchase: TopUpEsimOkResponsePurchase,
        profile: TopUpEsimOkResponseProfile,
        **kwargs
    ):
        """TopUpEsimOkResponse

        :param purchase: purchase
        :type purchase: TopUpEsimOkResponsePurchase
        :param profile: profile
        :type profile: TopUpEsimOkResponseProfile
        """
        self.purchase = self._define_object(purchase, TopUpEsimOkResponsePurchase)
        self.profile = self._define_object(profile, TopUpEsimOkResponseProfile)
        self._kwargs = kwargs
