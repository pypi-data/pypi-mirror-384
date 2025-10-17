from .utils.json_map import JsonMap
from .utils.base_model import BaseModel


@JsonMap({"data_usage_remaining_in_bytes": "dataUsageRemainingInBytes"})
class GetPurchaseConsumptionOkResponse(BaseModel):
    """GetPurchaseConsumptionOkResponse

    :param data_usage_remaining_in_bytes: Remaining balance of the package in bytes
    :type data_usage_remaining_in_bytes: float
    :param status: Status of the connectivity, possible values are 'ACTIVE' or 'NOT_ACTIVE'
    :type status: str
    """

    def __init__(self, data_usage_remaining_in_bytes: float, status: str, **kwargs):
        """GetPurchaseConsumptionOkResponse

        :param data_usage_remaining_in_bytes: Remaining balance of the package in bytes
        :type data_usage_remaining_in_bytes: float
        :param status: Status of the connectivity, possible values are 'ACTIVE' or 'NOT_ACTIVE'
        :type status: str
        """
        self.data_usage_remaining_in_bytes = data_usage_remaining_in_bytes
        self.status = status
        self._kwargs = kwargs
