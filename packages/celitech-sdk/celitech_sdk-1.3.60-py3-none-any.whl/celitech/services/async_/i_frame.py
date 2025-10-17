from typing import Awaitable, Union
from .utils.to_async import to_async
from ..i_frame import IFrameService
from ...models import TokenOkResponse


class IFrameServiceAsync(IFrameService):
    """
    Async Wrapper for IFrameServiceAsync
    """

    def token(self) -> Awaitable[TokenOkResponse]:
        return to_async(super().token)()
