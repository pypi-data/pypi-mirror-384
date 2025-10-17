from typing import Awaitable, Union
from .utils.to_async import to_async
from ..destinations import DestinationsService
from ...models import ListDestinationsOkResponse


class DestinationsServiceAsync(DestinationsService):
    """
    Async Wrapper for DestinationsServiceAsync
    """

    def list_destinations(self) -> Awaitable[ListDestinationsOkResponse]:
        return to_async(super().list_destinations)()
