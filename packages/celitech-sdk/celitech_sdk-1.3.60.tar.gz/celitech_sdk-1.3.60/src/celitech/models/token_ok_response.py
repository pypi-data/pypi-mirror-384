from .utils.json_map import JsonMap
from .utils.base_model import BaseModel


@JsonMap({})
class TokenOkResponse(BaseModel):
    """TokenOkResponse

    :param token: The generated token
    :type token: str
    """

    def __init__(self, token: str, **kwargs):
        """TokenOkResponse

        :param token: The generated token
        :type token: str
        """
        self.token = token
        self._kwargs = kwargs
