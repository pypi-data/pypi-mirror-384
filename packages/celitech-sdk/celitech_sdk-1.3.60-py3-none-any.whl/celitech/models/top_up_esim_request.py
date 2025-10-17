from .utils.json_map import JsonMap
from .utils.base_model import BaseModel
from .utils.sentinel import SENTINEL


@JsonMap(
    {
        "data_limit_in_gb": "dataLimitInGB",
        "start_date": "startDate",
        "end_date": "endDate",
        "reference_id": "referenceId",
        "email_brand": "emailBrand",
        "start_time": "startTime",
        "end_time": "endTime",
    }
)
class TopUpEsimRequest(BaseModel):
    """TopUpEsimRequest

    :param iccid: ID of the eSIM
    :type iccid: str
    :param data_limit_in_gb: Size of the package in GB. The available options are 0.5, 1, 2, 3, 5, 8, 20GB
    :type data_limit_in_gb: float
    :param start_date: Start date of the package's validity in the format 'yyyy-MM-dd'. This date can be set to the current day or any day within the next 12 months.
    :type start_date: str
    :param end_date: End date of the package's validity in the format 'yyyy-MM-dd'. End date can be maximum 90 days after Start date.
    :type end_date: str
    :param email: Email address where the purchase confirmation email will be sent (excluding QR Code & activation steps)., defaults to None
    :type email: str, optional
    :param reference_id: An identifier provided by the partner to link this purchase to their booking or transaction for analytics and debugging purposes., defaults to None
    :type reference_id: str, optional
    :param email_brand: Customize the email subject brand. The `emailBrand` parameter cannot exceed 25 characters in length and must contain only letters, numbers, and spaces. This feature is available to platforms with Diamond tier only., defaults to None
    :type email_brand: str, optional
    :param start_time: Epoch value representing the start time of the package's validity. This timestamp can be set to the current time or any time within the next 12 months., defaults to None
    :type start_time: float, optional
    :param end_time: Epoch value representing the end time of the package's validity. End time can be maximum 90 days after Start time., defaults to None
    :type end_time: float, optional
    """

    def __init__(
        self,
        iccid: str,
        data_limit_in_gb: float,
        start_date: str,
        end_date: str,
        email: str = SENTINEL,
        reference_id: str = SENTINEL,
        email_brand: str = SENTINEL,
        start_time: float = SENTINEL,
        end_time: float = SENTINEL,
        **kwargs
    ):
        """TopUpEsimRequest

        :param iccid: ID of the eSIM
        :type iccid: str
        :param data_limit_in_gb: Size of the package in GB. The available options are 0.5, 1, 2, 3, 5, 8, 20GB
        :type data_limit_in_gb: float
        :param start_date: Start date of the package's validity in the format 'yyyy-MM-dd'. This date can be set to the current day or any day within the next 12 months.
        :type start_date: str
        :param end_date: End date of the package's validity in the format 'yyyy-MM-dd'. End date can be maximum 90 days after Start date.
        :type end_date: str
        :param email: Email address where the purchase confirmation email will be sent (excluding QR Code & activation steps)., defaults to None
        :type email: str, optional
        :param reference_id: An identifier provided by the partner to link this purchase to their booking or transaction for analytics and debugging purposes., defaults to None
        :type reference_id: str, optional
        :param email_brand: Customize the email subject brand. The `emailBrand` parameter cannot exceed 25 characters in length and must contain only letters, numbers, and spaces. This feature is available to platforms with Diamond tier only., defaults to None
        :type email_brand: str, optional
        :param start_time: Epoch value representing the start time of the package's validity. This timestamp can be set to the current time or any time within the next 12 months., defaults to None
        :type start_time: float, optional
        :param end_time: Epoch value representing the end time of the package's validity. End time can be maximum 90 days after Start time., defaults to None
        :type end_time: float, optional
        """
        self.iccid = self._define_str("iccid", iccid, min_length=18, max_length=22)
        self.data_limit_in_gb = data_limit_in_gb
        self.start_date = start_date
        self.end_date = end_date
        self.email = self._define_str("email", email, nullable=True)
        self.reference_id = self._define_str(
            "reference_id", reference_id, nullable=True
        )
        self.email_brand = self._define_str("email_brand", email_brand, nullable=True)
        self.start_time = self._define_number("start_time", start_time, nullable=True)
        self.end_time = self._define_number("end_time", end_time, nullable=True)
        self._kwargs = kwargs
