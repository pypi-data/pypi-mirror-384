from .utils.json_map import JsonMap
from .utils.base_model import BaseModel


@JsonMap({"id_": "id", "package_id": "packageId", "created_date": "createdDate"})
class CreatePurchaseV2OkResponsePurchase(BaseModel):
    """CreatePurchaseV2OkResponsePurchase

    :param id_: ID of the purchase
    :type id_: str
    :param package_id: ID of the package
    :type package_id: str
    :param created_date: Creation date of the purchase in the format 'yyyy-MM-ddThh:mm:ssZZ'
    :type created_date: str
    """

    def __init__(self, id_: str, package_id: str, created_date: str, **kwargs):
        """CreatePurchaseV2OkResponsePurchase

        :param id_: ID of the purchase
        :type id_: str
        :param package_id: ID of the package
        :type package_id: str
        :param created_date: Creation date of the purchase in the format 'yyyy-MM-ddThh:mm:ssZZ'
        :type created_date: str
        """
        self.id_ = id_
        self.package_id = package_id
        self.created_date = created_date
        self._kwargs = kwargs


@JsonMap(
    {
        "activation_code": "activationCode",
        "manual_activation_code": "manualActivationCode",
    }
)
class CreatePurchaseV2OkResponseProfile(BaseModel):
    """CreatePurchaseV2OkResponseProfile

    :param iccid: ID of the eSIM
    :type iccid: str
    :param activation_code: QR Code of the eSIM as base64
    :type activation_code: str
    :param manual_activation_code: Manual Activation Code of the eSIM
    :type manual_activation_code: str
    """

    def __init__(
        self, iccid: str, activation_code: str, manual_activation_code: str, **kwargs
    ):
        """CreatePurchaseV2OkResponseProfile

        :param iccid: ID of the eSIM
        :type iccid: str
        :param activation_code: QR Code of the eSIM as base64
        :type activation_code: str
        :param manual_activation_code: Manual Activation Code of the eSIM
        :type manual_activation_code: str
        """
        self.iccid = self._define_str("iccid", iccid, min_length=18, max_length=22)
        self.activation_code = self._define_str(
            "activation_code", activation_code, min_length=1000, max_length=8000
        )
        self.manual_activation_code = manual_activation_code
        self._kwargs = kwargs


@JsonMap({})
class CreatePurchaseV2OkResponse(BaseModel):
    """CreatePurchaseV2OkResponse

    :param purchase: purchase
    :type purchase: CreatePurchaseV2OkResponsePurchase
    :param profile: profile
    :type profile: CreatePurchaseV2OkResponseProfile
    """

    def __init__(
        self,
        purchase: CreatePurchaseV2OkResponsePurchase,
        profile: CreatePurchaseV2OkResponseProfile,
        **kwargs
    ):
        """CreatePurchaseV2OkResponse

        :param purchase: purchase
        :type purchase: CreatePurchaseV2OkResponsePurchase
        :param profile: profile
        :type profile: CreatePurchaseV2OkResponseProfile
        """
        self.purchase = self._define_object(
            purchase, CreatePurchaseV2OkResponsePurchase
        )
        self.profile = self._define_object(profile, CreatePurchaseV2OkResponseProfile)
        self._kwargs = kwargs
