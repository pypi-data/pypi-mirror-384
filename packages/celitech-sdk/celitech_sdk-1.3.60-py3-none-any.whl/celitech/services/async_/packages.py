from typing import Awaitable, Union
from .utils.to_async import to_async
from ..packages import PackagesService
from ...models.utils.sentinel import SENTINEL
from ...models import ListPackagesOkResponse


class PackagesServiceAsync(PackagesService):
    """
    Async Wrapper for PackagesServiceAsync
    """

    def list_packages(
        self,
        destination: str = SENTINEL,
        start_date: str = SENTINEL,
        end_date: str = SENTINEL,
        after_cursor: str = SENTINEL,
        limit: float = SENTINEL,
        start_time: int = SENTINEL,
        end_time: int = SENTINEL,
        duration: float = SENTINEL,
    ) -> Awaitable[ListPackagesOkResponse]:
        return to_async(super().list_packages)(
            destination,
            start_date,
            end_date,
            after_cursor,
            limit,
            start_time,
            end_time,
            duration,
        )
