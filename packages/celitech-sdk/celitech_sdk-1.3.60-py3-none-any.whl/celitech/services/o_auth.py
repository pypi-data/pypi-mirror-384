from .utils.validator import Validator
from .utils.base_service import BaseService
from ..net.transport.serializer import Serializer
from ..net.environment.environment import Environment
from ..models.utils.cast_models import cast_models
from ..models import GetAccessTokenOkResponse, GetAccessTokenRequest


class OAuthService(BaseService):

    @cast_models
    def get_access_token(
        self, request_body: GetAccessTokenRequest
    ) -> GetAccessTokenOkResponse:
        """This endpoint was added by liblab

        :param request_body: The request body.
        :type request_body: GetAccessTokenRequest
        ...
        :raises RequestError: Raised when a request fails, with optional HTTP status code and details.
        ...
        :return: The parsed response data.
        :rtype: GetAccessTokenOkResponse
        """

        Validator(GetAccessTokenRequest).validate(request_body)

        serialized_request = (
            Serializer(
                f"{self.base_url or Environment.DEFAULT.url}/oauth2/token",
            )
            .serialize()
            .set_method("POST")
            .set_body(request_body, "application/x-www-form-urlencoded")
        )

        response, _, _ = self.send_request(serialized_request)
        return GetAccessTokenOkResponse._unmap(response)
