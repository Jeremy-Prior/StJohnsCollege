from geopy.compat import urlencode
from geopy.location import Location
from geopy.geocoders.base import (
    Geocoder,
    DEFAULT_FORMAT_STRING,
    DEFAULT_SCHEME
)


class OneMap(Geocoder):
    SERVER = 'https://www.1map.co.za'
    PATH_LOGIN = '/api/v1/auth/login'
    PATH_LOGOUT = '/api/v1/auth/logout'
    PATH_ADDRESS = '/api/v1/address/search'

    def __init__(
        self,
        username,
        password,
        format_string=DEFAULT_FORMAT_STRING,
        scheme=DEFAULT_SCHEME,
        timeout=5,
        proxies=None
    ):
        super().__init__(format_string, scheme, timeout, proxies)
        self.username = username
        self.password = password
        self.token = None

        self.login()

    def login(self):
        url = self.SERVER + self.PATH_LOGIN
        params = {"email": self.username, "password": self.password}

        url = "?".join((url, urlencode(params)))
        response = self._call_geocoder(url, timeout=None)
        self.token = response['apiToken']['token']

    def logout(self):
        url = self.SERVER + self.PATH_LOGOUT
        params = {"token": self.token}
        url = "?".join((url, urlencode(params)))
        self._call_geocoder(url, timeout=None)

    def geocode(self, query, exactly_one=True, timeout=None):
        url = self.SERVER + self.PATH_ADDRESS
        params = {
            "token": self.token,
            "address": query
        }
        if exactly_one:
            params['limit'] = 1
        
        url = "?".join((url, urlencode(params)))
        response = self._call_geocoder(url, timeout=timeout)        
        return self._parse_json(
            response.get('result', {}).get('nadAddresses', []), exactly_one
        )

    def _parse_item(self, item):
        latitude = item.get('latitude', None)
        longitude = item.get('longitude', None)
        placename = item.get('addressLabel', None)
        if latitude and longitude:
            latitude = float(latitude)
            longitude = float(longitude)
        return Location(placename, (latitude, longitude), item)

    def _parse_json(self, places, exactly_one):
        if places is None:
            return None
        if not isinstance(places, list):
            places = [places]
        if not len(places):
            return None
        if exactly_one is True:
            return self._parse_item(places[0])
        else:
            return [self._parse_item(place) for place in places]
