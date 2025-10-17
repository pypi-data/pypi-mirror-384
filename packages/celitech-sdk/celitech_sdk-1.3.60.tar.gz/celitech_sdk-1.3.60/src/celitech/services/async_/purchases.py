from typing import Awaitable, List, Union
from .utils.to_async import to_async
from ..purchases import PurchasesService
from ...models.utils.sentinel import SENTINEL
from ...models import (
    CreatePurchaseV2OkResponse,
    CreatePurchaseV2Request,
    ListPurchasesOkResponse,
    CreatePurchaseOkResponse,
    CreatePurchaseRequest,
    TopUpEsimOkResponse,
    TopUpEsimRequest,
    EditPurchaseOkResponse,
    EditPurchaseRequest,
    GetPurchaseConsumptionOkResponse,
)


class PurchasesServiceAsync(PurchasesService):
    """
    Async Wrapper for PurchasesServiceAsync
    """

    def create_purchase_v2(
        self, request_body: CreatePurchaseV2Request
    ) -> Awaitable[List[CreatePurchaseV2OkResponse]]:
        return to_async(super().create_purchase_v2)(request_body)

    def list_purchases(
        self,
        iccid: str = SENTINEL,
        after_date: str = SENTINEL,
        before_date: str = SENTINEL,
        email: str = SENTINEL,
        reference_id: str = SENTINEL,
        after_cursor: str = SENTINEL,
        limit: float = SENTINEL,
        after: float = SENTINEL,
        before: float = SENTINEL,
        purchase_id: str = SENTINEL,
    ) -> Awaitable[ListPurchasesOkResponse]:
        return to_async(super().list_purchases)(
            iccid,
            after_date,
            before_date,
            email,
            reference_id,
            after_cursor,
            limit,
            after,
            before,
            purchase_id,
        )

    def create_purchase(
        self, request_body: CreatePurchaseRequest
    ) -> Awaitable[CreatePurchaseOkResponse]:
        return to_async(super().create_purchase)(request_body)

    def top_up_esim(
        self, request_body: TopUpEsimRequest
    ) -> Awaitable[TopUpEsimOkResponse]:
        return to_async(super().top_up_esim)(request_body)

    def edit_purchase(
        self, request_body: EditPurchaseRequest
    ) -> Awaitable[EditPurchaseOkResponse]:
        return to_async(super().edit_purchase)(request_body)

    def get_purchase_consumption(
        self, purchase_id: str
    ) -> Awaitable[GetPurchaseConsumptionOkResponse]:
        return to_async(super().get_purchase_consumption)(purchase_id)
