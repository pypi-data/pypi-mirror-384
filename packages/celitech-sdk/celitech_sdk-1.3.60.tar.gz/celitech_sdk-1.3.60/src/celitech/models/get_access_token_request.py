from enum import Enum
from .utils.json_map import JsonMap
from .utils.base_model import BaseModel
from .utils.sentinel import SENTINEL


class GrantType(Enum):
    """An enumeration representing different categories.

    :cvar CLIENTCREDENTIALS: "client_credentials"
    :vartype CLIENTCREDENTIALS: str
    """

    CLIENTCREDENTIALS = "client_credentials"

    def list():
        """Lists all category values.

        :return: A list of all category values.
        :rtype: list
        """
        return list(map(lambda x: x.value, GrantType._member_map_.values()))


@JsonMap({})
class GetAccessTokenRequest(BaseModel):
    """GetAccessTokenRequest

    :param grant_type: grant_type, defaults to None
    :type grant_type: GrantType, optional
    :param client_id: client_id, defaults to None
    :type client_id: str, optional
    :param client_secret: client_secret, defaults to None
    :type client_secret: str, optional
    """

    def __init__(
        self,
        grant_type: GrantType = SENTINEL,
        client_id: str = SENTINEL,
        client_secret: str = SENTINEL,
        **kwargs
    ):
        """GetAccessTokenRequest

        :param grant_type: grant_type, defaults to None
        :type grant_type: GrantType, optional
        :param client_id: client_id, defaults to None
        :type client_id: str, optional
        :param client_secret: client_secret, defaults to None
        :type client_secret: str, optional
        """
        self.grant_type = (
            self._enum_matching(grant_type, GrantType.list(), "grant_type")
            if grant_type
            else None
        )
        self.client_id = self._define_str("client_id", client_id, nullable=True)
        self.client_secret = self._define_str(
            "client_secret", client_secret, nullable=True
        )
        self._kwargs = kwargs
