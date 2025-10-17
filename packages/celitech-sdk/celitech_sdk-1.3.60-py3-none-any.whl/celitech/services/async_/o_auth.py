from typing import Awaitable
from .utils.to_async import to_async
from ..o_auth import OAuthService
from ...models import GetAccessTokenOkResponse, GetAccessTokenRequest


class OAuthServiceAsync(OAuthService):
    """
    Async Wrapper for OAuthServiceAsync
    """

    def get_access_token(
        self, request_body: GetAccessTokenRequest
    ) -> Awaitable[GetAccessTokenOkResponse]:
        return to_async(super().get_access_token)(request_body)
