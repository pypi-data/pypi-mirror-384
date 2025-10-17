from typing import List, Union
from .utils.validator import Validator
from .utils.base_service import BaseService
from ..net.transport.serializer import Serializer
from ..net.environment.environment import Environment
from ..models.utils.sentinel import SENTINEL
from ..models.utils.cast_models import cast_models
from ..models import (
    BadRequest,
    CreatePurchaseOkResponse,
    CreatePurchaseRequest,
    CreatePurchaseV2OkResponse,
    CreatePurchaseV2Request,
    EditPurchaseOkResponse,
    EditPurchaseRequest,
    GetPurchaseConsumptionOkResponse,
    ListPurchasesOkResponse,
    TopUpEsimOkResponse,
    TopUpEsimRequest,
    Unauthorized,
)


class PurchasesService(BaseService):

    @cast_models
    def create_purchase_v2(
        self, request_body: CreatePurchaseV2Request
    ) -> List[CreatePurchaseV2OkResponse]:
        """This endpoint is used to purchase a new eSIM by providing the package details.

        :param request_body: The request body.
        :type request_body: CreatePurchaseV2Request
        ...
        :raises RequestError: Raised when a request fails, with optional HTTP status code and details.
        ...
        :return: The parsed response data.
        :rtype: List[CreatePurchaseV2OkResponse]
        """

        Validator(CreatePurchaseV2Request).validate(request_body)

        serialized_request = (
            Serializer(
                f"{self.base_url or Environment.DEFAULT.url}/purchases/v2",
            )
            .add_error(400, BadRequest)
            .add_error(401, Unauthorized)
            .serialize()
            .set_method("POST")
            .set_scopes(set())
            .set_body(request_body)
        )

        response, status, _ = self.send_request(serialized_request)
        return [CreatePurchaseV2OkResponse._unmap(item) for item in response]

    @cast_models
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
    ) -> ListPurchasesOkResponse:
        """This endpoint can be used to list all the successful purchases made between a given interval.

        :param iccid: ID of the eSIM, defaults to None
        :type iccid: str, optional
        :param after_date: Start date of the interval for filtering purchases in the format 'yyyy-MM-dd', defaults to None
        :type after_date: str, optional
        :param before_date: End date of the interval for filtering purchases in the format 'yyyy-MM-dd', defaults to None
        :type before_date: str, optional
        :param email: Email associated to the purchase., defaults to None
        :type email: str, optional
        :param reference_id: The referenceId that was provided by the partner during the purchase or topup flow., defaults to None
        :type reference_id: str, optional
        :param after_cursor: To get the next batch of results, use this parameter. It tells the API where to start fetching data after the last item you received. It helps you avoid repeats and efficiently browse through large sets of data., defaults to None
        :type after_cursor: str, optional
        :param limit: Maximum number of purchases to be returned in the response. The value must be greater than 0 and less than or equal to 100. If not provided, the default value is 20, defaults to None
        :type limit: float, optional
        :param after: Epoch value representing the start of the time interval for filtering purchases, defaults to None
        :type after: float, optional
        :param before: Epoch value representing the end of the time interval for filtering purchases, defaults to None
        :type before: float, optional
        :param purchase_id: The id of a specific purchase., defaults to None
        :type purchase_id: str, optional
        ...
        :raises RequestError: Raised when a request fails, with optional HTTP status code and details.
        ...
        :return: The parsed response data.
        :rtype: ListPurchasesOkResponse
        """

        Validator(str).is_optional().min_length(18).max_length(22).validate(iccid)
        Validator(str).is_optional().validate(after_date)
        Validator(str).is_optional().validate(before_date)
        Validator(str).is_optional().validate(email)
        Validator(str).is_optional().validate(reference_id)
        Validator(str).is_optional().validate(after_cursor)
        Validator(float).is_optional().validate(limit)
        Validator(float).is_optional().validate(after)
        Validator(float).is_optional().validate(before)
        Validator(str).is_optional().validate(purchase_id)

        serialized_request = (
            Serializer(
                f"{self.base_url or Environment.DEFAULT.url}/purchases",
            )
            .add_query("iccid", iccid)
            .add_query("afterDate", after_date)
            .add_query("beforeDate", before_date)
            .add_query("email", email)
            .add_query("referenceId", reference_id)
            .add_query("afterCursor", after_cursor)
            .add_query("limit", limit)
            .add_query("after", after)
            .add_query("before", before)
            .add_query("purchaseId", purchase_id)
            .add_error(400, BadRequest)
            .add_error(401, Unauthorized)
            .serialize()
            .set_method("GET")
            .set_scopes(set())
        )

        response, status, _ = self.send_request(serialized_request)
        return ListPurchasesOkResponse._unmap(response)

    @cast_models
    def create_purchase(
        self, request_body: CreatePurchaseRequest
    ) -> CreatePurchaseOkResponse:
        """This endpoint is used to purchase a new eSIM by providing the package details.

        :param request_body: The request body.
        :type request_body: CreatePurchaseRequest
        ...
        :raises RequestError: Raised when a request fails, with optional HTTP status code and details.
        ...
        :return: The parsed response data.
        :rtype: CreatePurchaseOkResponse
        """

        Validator(CreatePurchaseRequest).validate(request_body)

        serialized_request = (
            Serializer(
                f"{self.base_url or Environment.DEFAULT.url}/purchases",
            )
            .add_error(400, BadRequest)
            .add_error(401, Unauthorized)
            .serialize()
            .set_method("POST")
            .set_scopes(set())
            .set_body(request_body)
        )

        response, status, _ = self.send_request(serialized_request)
        return CreatePurchaseOkResponse._unmap(response)

    @cast_models
    def top_up_esim(self, request_body: TopUpEsimRequest) -> TopUpEsimOkResponse:
        """This endpoint is used to top-up an existing eSIM with the previously associated destination by providing its ICCID and package details. To determine if an eSIM can be topped up, use the Get eSIM Status endpoint, which returns the `isTopUpAllowed` flag.

        :param request_body: The request body.
        :type request_body: TopUpEsimRequest
        ...
        :raises RequestError: Raised when a request fails, with optional HTTP status code and details.
        ...
        :return: The parsed response data.
        :rtype: TopUpEsimOkResponse
        """

        Validator(TopUpEsimRequest).validate(request_body)

        serialized_request = (
            Serializer(
                f"{self.base_url or Environment.DEFAULT.url}/purchases/topup",
            )
            .add_error(400, BadRequest)
            .add_error(401, Unauthorized)
            .serialize()
            .set_method("POST")
            .set_scopes(set())
            .set_body(request_body)
        )

        response, status, _ = self.send_request(serialized_request)
        return TopUpEsimOkResponse._unmap(response)

    @cast_models
    def edit_purchase(
        self, request_body: EditPurchaseRequest
    ) -> EditPurchaseOkResponse:
        """This endpoint allows you to modify the validity dates of an existing purchase.

        **Behavior:**
        - If the purchase has **not yet been activated**, both the start and end dates can be updated.
        - If the purchase is **already active**, only the **end date** can be updated, while the **start date must remain unchanged** (and should be passed as originally set).
        - Updates must comply with the same pricing structure; the modification cannot alter the package size or change its duration category.

        The end date can be extended or shortened as long as it adheres to the same pricing category and does not exceed the allowed duration limits.

        :param request_body: The request body.
        :type request_body: EditPurchaseRequest
        ...
        :raises RequestError: Raised when a request fails, with optional HTTP status code and details.
        ...
        :return: The parsed response data.
        :rtype: EditPurchaseOkResponse
        """

        Validator(EditPurchaseRequest).validate(request_body)

        serialized_request = (
            Serializer(
                f"{self.base_url or Environment.DEFAULT.url}/purchases/edit",
            )
            .add_error(400, BadRequest)
            .add_error(401, Unauthorized)
            .serialize()
            .set_method("POST")
            .set_scopes(set())
            .set_body(request_body)
        )

        response, status, _ = self.send_request(serialized_request)
        return EditPurchaseOkResponse._unmap(response)

    @cast_models
    def get_purchase_consumption(
        self, purchase_id: str
    ) -> GetPurchaseConsumptionOkResponse:
        """This endpoint can be called for consumption notifications (e.g. every 1 hour or when the user clicks a button). It returns the data balance (consumption) of purchased packages.

        :param purchase_id: ID of the purchase
        :type purchase_id: str
        ...
        :raises RequestError: Raised when a request fails, with optional HTTP status code and details.
        ...
        :return: The parsed response data.
        :rtype: GetPurchaseConsumptionOkResponse
        """

        Validator(str).validate(purchase_id)

        serialized_request = (
            Serializer(
                f"{self.base_url or Environment.DEFAULT.url}/purchases/{{purchaseId}}/consumption",
            )
            .add_path("purchaseId", purchase_id)
            .add_error(400, BadRequest)
            .add_error(401, Unauthorized)
            .serialize()
            .set_method("GET")
            .set_scopes(set())
        )

        response, status, _ = self.send_request(serialized_request)
        return GetPurchaseConsumptionOkResponse._unmap(response)
