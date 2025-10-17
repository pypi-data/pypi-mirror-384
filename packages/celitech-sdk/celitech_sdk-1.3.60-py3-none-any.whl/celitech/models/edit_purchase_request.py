from .utils.json_map import JsonMap
from .utils.base_model import BaseModel
from .utils.sentinel import SENTINEL


@JsonMap(
    {
        "purchase_id": "purchaseId",
        "start_date": "startDate",
        "end_date": "endDate",
        "start_time": "startTime",
        "end_time": "endTime",
    }
)
class EditPurchaseRequest(BaseModel):
    """EditPurchaseRequest

    :param purchase_id: ID of the purchase
    :type purchase_id: str
    :param start_date: Start date of the package's validity in the format 'yyyy-MM-dd'. This date can be set to the current day or any day within the next 12 months.
    :type start_date: str
    :param end_date: End date of the package's validity in the format 'yyyy-MM-dd'. End date can be maximum 90 days after Start date.
    :type end_date: str
    :param start_time: Epoch value representing the start time of the package's validity. This timestamp can be set to the current time or any time within the next 12 months., defaults to None
    :type start_time: float, optional
    :param end_time: Epoch value representing the end time of the package's validity. End time can be maximum 90 days after Start time., defaults to None
    :type end_time: float, optional
    """

    def __init__(
        self,
        purchase_id: str,
        start_date: str,
        end_date: str,
        start_time: float = SENTINEL,
        end_time: float = SENTINEL,
        **kwargs
    ):
        """EditPurchaseRequest

        :param purchase_id: ID of the purchase
        :type purchase_id: str
        :param start_date: Start date of the package's validity in the format 'yyyy-MM-dd'. This date can be set to the current day or any day within the next 12 months.
        :type start_date: str
        :param end_date: End date of the package's validity in the format 'yyyy-MM-dd'. End date can be maximum 90 days after Start date.
        :type end_date: str
        :param start_time: Epoch value representing the start time of the package's validity. This timestamp can be set to the current time or any time within the next 12 months., defaults to None
        :type start_time: float, optional
        :param end_time: Epoch value representing the end time of the package's validity. End time can be maximum 90 days after Start time., defaults to None
        :type end_time: float, optional
        """
        self.purchase_id = purchase_id
        self.start_date = start_date
        self.end_date = end_date
        self.start_time = self._define_number("start_time", start_time, nullable=True)
        self.end_time = self._define_number("end_time", end_time, nullable=True)
        self._kwargs = kwargs
