from typing import Union
from .utils.validator import Validator
from .utils.base_service import BaseService
from ..net.transport.serializer import Serializer
from ..net.environment.environment import Environment
from ..models.utils.sentinel import SENTINEL
from ..models.utils.cast_models import cast_models
from ..models import BadRequest, ListPackagesOkResponse, Unauthorized


class PackagesService(BaseService):

    @cast_models
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
    ) -> ListPackagesOkResponse:
        """List Packages

        :param destination: ISO representation of the package's destination. Supports both ISO2 (e.g., 'FR') and ISO3 (e.g., 'FRA') country codes., defaults to None
        :type destination: str, optional
        :param start_date: Start date of the package's validity in the format 'yyyy-MM-dd'. This date can be set to the current day or any day within the next 12 months., defaults to None
        :type start_date: str, optional
        :param end_date: End date of the package's validity in the format 'yyyy-MM-dd'. End date can be maximum 90 days after Start date., defaults to None
        :type end_date: str, optional
        :param after_cursor: To get the next batch of results, use this parameter. It tells the API where to start fetching data after the last item you received. It helps you avoid repeats and efficiently browse through large sets of data., defaults to None
        :type after_cursor: str, optional
        :param limit: Maximum number of packages to be returned in the response. The value must be greater than 0 and less than or equal to 160. If not provided, the default value is 20, defaults to None
        :type limit: float, optional
        :param start_time: Epoch value representing the start time of the package's validity. This timestamp can be set to the current time or any time within the next 12 months, defaults to None
        :type start_time: int, optional
        :param end_time: Epoch value representing the end time of the package's validity. End time can be maximum 90 days after Start time, defaults to None
        :type end_time: int, optional
        :param duration: Duration in seconds for the package's validity. If this parameter is present, it will override the startTime and endTime parameters. The maximum duration for a package's validity period is 90 days, defaults to None
        :type duration: float, optional
        ...
        :raises RequestError: Raised when a request fails, with optional HTTP status code and details.
        ...
        :return: The parsed response data.
        :rtype: ListPackagesOkResponse
        """

        Validator(str).is_optional().validate(destination)
        Validator(str).is_optional().validate(start_date)
        Validator(str).is_optional().validate(end_date)
        Validator(str).is_optional().validate(after_cursor)
        Validator(float).is_optional().validate(limit)
        Validator(int).is_optional().validate(start_time)
        Validator(int).is_optional().validate(end_time)
        Validator(float).is_optional().validate(duration)

        serialized_request = (
            Serializer(
                f"{self.base_url or Environment.DEFAULT.url}/packages",
            )
            .add_query("destination", destination)
            .add_query("startDate", start_date)
            .add_query("endDate", end_date)
            .add_query("afterCursor", after_cursor)
            .add_query("limit", limit)
            .add_query("startTime", start_time)
            .add_query("endTime", end_time)
            .add_query("duration", duration)
            .add_error(400, BadRequest)
            .add_error(401, Unauthorized)
            .serialize()
            .set_method("GET")
            .set_scopes(set())
        )

        response, status, _ = self.send_request(serialized_request)
        return ListPackagesOkResponse._unmap(response)
