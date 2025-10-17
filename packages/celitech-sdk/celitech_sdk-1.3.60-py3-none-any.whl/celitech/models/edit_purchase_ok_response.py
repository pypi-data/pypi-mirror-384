from typing import Union
from .utils.json_map import JsonMap
from .utils.base_model import BaseModel
from .utils.sentinel import SENTINEL


@JsonMap(
    {
        "purchase_id": "purchaseId",
        "new_start_date": "newStartDate",
        "new_end_date": "newEndDate",
        "new_start_time": "newStartTime",
        "new_end_time": "newEndTime",
    }
)
class EditPurchaseOkResponse(BaseModel):
    """EditPurchaseOkResponse

    :param purchase_id: ID of the purchase
    :type purchase_id: str
    :param new_start_date: Start date of the package's validity in the format 'yyyy-MM-ddThh:mm:ssZZ'
    :type new_start_date: str
    :param new_end_date: End date of the package's validity in the format 'yyyy-MM-ddThh:mm:ssZZ'
    :type new_end_date: str
    :param new_start_time: Epoch value representing the new start time of the package's validity, defaults to None
    :type new_start_time: float, optional
    :param new_end_time: Epoch value representing the new end time of the package's validity, defaults to None
    :type new_end_time: float, optional
    """

    def __init__(
        self,
        purchase_id: str,
        new_start_date: Union[str, None],
        new_end_date: Union[str, None],
        new_start_time: Union[float, None] = SENTINEL,
        new_end_time: Union[float, None] = SENTINEL,
        **kwargs
    ):
        """EditPurchaseOkResponse

        :param purchase_id: ID of the purchase
        :type purchase_id: str
        :param new_start_date: Start date of the package's validity in the format 'yyyy-MM-ddThh:mm:ssZZ'
        :type new_start_date: str
        :param new_end_date: End date of the package's validity in the format 'yyyy-MM-ddThh:mm:ssZZ'
        :type new_end_date: str
        :param new_start_time: Epoch value representing the new start time of the package's validity, defaults to None
        :type new_start_time: float, optional
        :param new_end_time: Epoch value representing the new end time of the package's validity, defaults to None
        :type new_end_time: float, optional
        """
        self.purchase_id = purchase_id
        self.new_start_date = self._define_str(
            "new_start_date", new_start_date, nullable=True
        )
        self.new_end_date = self._define_str(
            "new_end_date", new_end_date, nullable=True
        )
        self.new_start_time = self._define_number(
            "new_start_time", new_start_time, nullable=True
        )
        self.new_end_time = self._define_number(
            "new_end_time", new_end_time, nullable=True
        )
        self._kwargs = kwargs
