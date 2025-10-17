from typing import List
from .utils.json_map import JsonMap
from .utils.base_model import BaseModel


@JsonMap(
    {"destination_iso2": "destinationISO2", "supported_countries": "supportedCountries"}
)
class Destinations(BaseModel):
    """Destinations

    :param name: Name of the destination
    :type name: str
    :param destination: ISO3 representation of the destination
    :type destination: str
    :param destination_iso2: ISO2 representation of the destination
    :type destination_iso2: str
    :param supported_countries: This array indicates the geographical area covered by a specific destination. If the destination represents a single country, the array will include that country. However, if the destination represents a broader regional scope, the array will be populated with the names of the countries belonging to that region.
    :type supported_countries: List[str]
    """

    def __init__(
        self,
        name: str,
        destination: str,
        destination_iso2: str,
        supported_countries: List[str],
        **kwargs
    ):
        """Destinations

        :param name: Name of the destination
        :type name: str
        :param destination: ISO3 representation of the destination
        :type destination: str
        :param destination_iso2: ISO2 representation of the destination
        :type destination_iso2: str
        :param supported_countries: This array indicates the geographical area covered by a specific destination. If the destination represents a single country, the array will include that country. However, if the destination represents a broader regional scope, the array will be populated with the names of the countries belonging to that region.
        :type supported_countries: List[str]
        """
        self.name = name
        self.destination = destination
        self.destination_iso2 = destination_iso2
        self.supported_countries = supported_countries
        self._kwargs = kwargs


@JsonMap({})
class ListDestinationsOkResponse(BaseModel):
    """ListDestinationsOkResponse

    :param destinations: destinations
    :type destinations: List[Destinations]
    """

    def __init__(self, destinations: List[Destinations], **kwargs):
        """ListDestinationsOkResponse

        :param destinations: destinations
        :type destinations: List[Destinations]
        """
        self.destinations = self._define_list(destinations, Destinations)
        self._kwargs = kwargs
