from typing import List
from .utils.json_map import JsonMap
from .utils.base_model import BaseModel
from .utils.sentinel import SENTINEL


@JsonMap({"status_date": "statusDate", "date_": "date"})
class History(BaseModel):
    """History

    :param status: The status of the eSIM at a given time, possible values are 'RELEASED', 'DOWNLOADED', 'INSTALLED', 'ENABLED', 'DELETED', or 'ERROR'
    :type status: str
    :param status_date: The date when the eSIM status changed in the format 'yyyy-MM-ddThh:mm:ssZZ'
    :type status_date: str
    :param date_: Epoch value representing the date when the eSIM status changed, defaults to None
    :type date_: float, optional
    """

    def __init__(
        self, status: str, status_date: str, date_: float = SENTINEL, **kwargs
    ):
        """History

        :param status: The status of the eSIM at a given time, possible values are 'RELEASED', 'DOWNLOADED', 'INSTALLED', 'ENABLED', 'DELETED', or 'ERROR'
        :type status: str
        :param status_date: The date when the eSIM status changed in the format 'yyyy-MM-ddThh:mm:ssZZ'
        :type status_date: str
        :param date_: Epoch value representing the date when the eSIM status changed, defaults to None
        :type date_: float, optional
        """
        self.status = status
        self.status_date = status_date
        self.date_ = self._define_number("date_", date_, nullable=True)
        self._kwargs = kwargs


@JsonMap({})
class GetEsimHistoryOkResponseEsim(BaseModel):
    """GetEsimHistoryOkResponseEsim

    :param iccid: ID of the eSIM
    :type iccid: str
    :param history: history
    :type history: List[History]
    """

    def __init__(self, iccid: str, history: List[History], **kwargs):
        """GetEsimHistoryOkResponseEsim

        :param iccid: ID of the eSIM
        :type iccid: str
        :param history: history
        :type history: List[History]
        """
        self.iccid = self._define_str("iccid", iccid, min_length=18, max_length=22)
        self.history = self._define_list(history, History)
        self._kwargs = kwargs


@JsonMap({})
class GetEsimHistoryOkResponse(BaseModel):
    """GetEsimHistoryOkResponse

    :param esim: esim
    :type esim: GetEsimHistoryOkResponseEsim
    """

    def __init__(self, esim: GetEsimHistoryOkResponseEsim, **kwargs):
        """GetEsimHistoryOkResponse

        :param esim: esim
        :type esim: GetEsimHistoryOkResponseEsim
        """
        self.esim = self._define_object(esim, GetEsimHistoryOkResponseEsim)
        self._kwargs = kwargs
