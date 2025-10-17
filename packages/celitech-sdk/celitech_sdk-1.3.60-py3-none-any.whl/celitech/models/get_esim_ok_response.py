from .utils.json_map import JsonMap
from .utils.base_model import BaseModel


@JsonMap(
    {
        "smdp_address": "smdpAddress",
        "activation_code": "activationCode",
        "manual_activation_code": "manualActivationCode",
        "is_top_up_allowed": "isTopUpAllowed",
    }
)
class GetEsimOkResponseEsim(BaseModel):
    """GetEsimOkResponseEsim

    :param iccid: ID of the eSIM
    :type iccid: str
    :param smdp_address: SM-DP+ Address
    :type smdp_address: str
    :param activation_code: QR Code of the eSIM as base64
    :type activation_code: str
    :param manual_activation_code: The manual activation code
    :type manual_activation_code: str
    :param status: Status of the eSIM, possible values are 'RELEASED', 'DOWNLOADED', 'INSTALLED', 'ENABLED', 'DELETED', or 'ERROR'
    :type status: str
    :param is_top_up_allowed: Indicates whether the eSIM is currently eligible for a top-up. This flag should be checked before attempting a top-up request.
    :type is_top_up_allowed: bool
    """

    def __init__(
        self,
        iccid: str,
        smdp_address: str,
        activation_code: str,
        manual_activation_code: str,
        status: str,
        is_top_up_allowed: bool,
        **kwargs
    ):
        """GetEsimOkResponseEsim

        :param iccid: ID of the eSIM
        :type iccid: str
        :param smdp_address: SM-DP+ Address
        :type smdp_address: str
        :param activation_code: QR Code of the eSIM as base64
        :type activation_code: str
        :param manual_activation_code: The manual activation code
        :type manual_activation_code: str
        :param status: Status of the eSIM, possible values are 'RELEASED', 'DOWNLOADED', 'INSTALLED', 'ENABLED', 'DELETED', or 'ERROR'
        :type status: str
        :param is_top_up_allowed: Indicates whether the eSIM is currently eligible for a top-up. This flag should be checked before attempting a top-up request.
        :type is_top_up_allowed: bool
        """
        self.iccid = self._define_str("iccid", iccid, min_length=18, max_length=22)
        self.smdp_address = smdp_address
        self.activation_code = self._define_str(
            "activation_code", activation_code, min_length=1000, max_length=8000
        )
        self.manual_activation_code = manual_activation_code
        self.status = status
        self.is_top_up_allowed = is_top_up_allowed
        self._kwargs = kwargs


@JsonMap({})
class GetEsimOkResponse(BaseModel):
    """GetEsimOkResponse

    :param esim: esim
    :type esim: GetEsimOkResponseEsim
    """

    def __init__(self, esim: GetEsimOkResponseEsim, **kwargs):
        """GetEsimOkResponse

        :param esim: esim
        :type esim: GetEsimOkResponseEsim
        """
        self.esim = self._define_object(esim, GetEsimOkResponseEsim)
        self._kwargs = kwargs
