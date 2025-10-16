from typing import Optional

from geopy import Point

from .model import ExternalLocation, Location
from .paging import Page, PagingClient
from .util import parse_point


class LocationsClient(PagingClient[Location]):
    """
    Access to Locations API.

    Acquire an instance via ``SRFData.locations``.
    """

    def __init__(self, client):  # noqa: D107
        super().__init__(client, 'locations')

    def _parse_obj(self, data, uri) -> Location:
        return Location(
            client=self._client,
            uri=uri,
            org_uri=data['organisation']['_location'],
            name=data.get('name'),
            post_code=data.get('postCode'),
            point=parse_point(data.get('point'))
        )

    def find_all(self, lazy=False, **kwargs) -> Page[Location]:
        """
        Find all known locations.

        :param lazy: Defer fetching of the Location objects
        :param kwargs: Additional field filters
        """
        params = {'includeItems': not lazy, **self._filter_params(**kwargs)}
        return self.get_page('/locations', params)

    def lookup(self, point: Point) -> Optional[ExternalLocation]:
        """
        Lookup location details from an external system, e.g. the ONS.

        :param point: (latitude, longitude) point to query
        :return: details of nearest postcode, if found

        .. versionadded:: 2.7
        """
        params = {'point': f'{point.latitude},{point.longitude}'}
        response = self._client.get('locations/lookup', params=params)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        return ExternalLocation(name=data.get('name'),
                                post_code=data.get('postCode'),
                                point=parse_point(data.get('point')))
