from w.services.abstract_service import AbstractService
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from django.conf import settings
import os

from w.services.technical.json_service import JsonService
from w.services.technical.request_service import RequestService

API_KEY = str(os.getenv("GOOGLE_MAP_SECRET"))
API_KEY_PLACE = str(os.getenv("GOOGLE_MAP_API_KEY"))
GEOCODE_BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
AUTOCOMPLETE_BASE_URL = (
    "https://maps.googleapis.com/maps/api/place/queryautocomplete/json"
)
PLACE_DETAIL_URL = "https://maps.googleapis.com/maps/api/place/details/json"
FIND_PLACE_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"


class GoogleMapService(AbstractService):
    @classmethod
    def geocode_address(cls, textual_address):  # pragma: no cover (todo one day)
        if settings.MOCK_GMAP_CALLS:
            return {"lat": 10, "lng": 10}

        url = cls.build_geocode_url(textual_address)

        return cls._loop_until_endpoint_is_reached(url, cls._parse_geocode_response)

    @classmethod
    def search_by_phone_number(cls, phone_number):
        response = RequestService.get(
            f"{FIND_PLACE_URL}?input=%2B33{phone_number}&inputtype=phonenumber"
            f"&fields=place_id,"
            f"name,formatted_address,type&key={API_KEY_PLACE}"
        )
        if response.success:
            return response.content
        cls._raise_api_failed(
            response, "Failed to get google place"
        )  # pragma: no cover (todo one day)

    @classmethod
    def _raise_api_failed(cls, response, msg):  # pragma: no cover (todo one day)
        """
        raise RuntimeError for yousign api failure
        """
        if JsonService.is_valid(response.orig_content):
            error = json.loads(response.orig_content)
            error = error["detail"]
        else:
            error = "no detail"

        raise RuntimeError(
            f"{msg} ({response.status_code} - {response.content}) : {error}"
        )

    @classmethod
    def autocomplete_address(
        cls, textual_address, session_token=None
    ):  # pragma: no cover (todo one day)
        if settings.MOCK_GMAP_CALLS:
            return {"result": "1 rue du test", "location": {"lat": 10, "lng": 10}}

        url = cls.build_autocomplete_place_url(textual_address, session_token)

        return cls._loop_until_endpoint_is_reached(
            url, cls._parse_autocomplete_place_response
        )

    @classmethod
    def get_place_detail(cls, place_id):
        url = cls.build_place_detail_url(place_id)

        return cls._loop_until_endpoint_is_reached(
            url, cls._parse_place_detail_response
        )

    @classmethod
    def build_place_detail_url(cls, place_id):
        # Join the parts of the URL together into one string.
        return (
            f"{PLACE_DETAIL_URL}?place_id={place_id}&key="
            f"{API_KEY}&fields=geometry,formatted_address,place_id"
        )

    @classmethod
    def build_autocomplete_place_url(cls, address, session_token=None):
        # Join the parts of the URL together into one string.
        urls_params = {
            "input": f"{address}",
            "key": API_KEY,
            "langage": "fr",
            "components": "country:fr|country:ch|country:be|country:de|country:es",
        }
        if session_token:
            urls_params.update(sessiontoken=session_token)
        params = urllib.parse.urlencode(urls_params)
        return f"{AUTOCOMPLETE_BASE_URL}?{params}"

    @classmethod
    def build_geocode_url(cls, address):
        # Join the parts of the URL together into one string.
        params = urllib.parse.urlencode({"address": f"{address}", "key": API_KEY})
        return f"{GEOCODE_BASE_URL}?{params}"

    @classmethod
    def _loop_until_endpoint_is_reached(cls, url, parse_result_func):
        current_delay = 0.1  # Set the initial retry delay to 100ms.
        max_delay = 5  # Set the maximum retry delay to 5 seconds.
        while True:
            try:
                # Get the API response.
                response = urllib.request.urlopen(url)
            except urllib.error.URLError:  # pragma: no cover (todo one day)
                pass  # Fall through to the retry loop.
            else:
                # If we didn't get an IOError then parse the result.
                return parse_result_func(response)

            if current_delay > max_delay:  # pragma: no cover (todo one day)
                raise RuntimeError("Too many retry attempts.")
                # print("Waiting", current_delay, "seconds before retrying.")
                time.sleep(current_delay)
                current_delay *= 2  # Increase the delay each time we retry.

    @classmethod
    def _parse_geocode_response(
        cls, response_to_parse
    ):  # pragma: no cover (todo one day)
        result = json.load(response_to_parse)
        if result["status"] == "OK":
            return result["results"][0]["geometry"]["location"]
        elif result["status"] == "ZERO_RESULTS":
            return None
        elif result["status"] != "UNKNOWN_ERROR":
            # Many API errors cannot be fixed by a retry, e.g. INVALID_REQUEST
            raise RuntimeError(result["error_message"])

    @classmethod
    def _parse_autocomplete_place_response(
        cls, response_to_parse
    ):  # pragma: no cover (todo one day)
        result = json.load(response_to_parse)
        results_with_id = [
            p for p in result["predictions"] if p.get("place_id", None) is not None
        ]
        if result["status"] == "OK":
            parsed_results = list()
            for r in results_with_id:
                if r.get("structured_formatting", None) is None:
                    continue

                if r["structured_formatting"].get("main_text", None) is None:
                    continue

                if r["structured_formatting"].get("secondary_text", None) is not None:
                    parsed_results.append(
                        {
                            "main_text": r["structured_formatting"]["main_text"],
                            "secondary_text": r["structured_formatting"][
                                "secondary_text"
                            ],
                            "place_id": r["place_id"],
                        }
                    )
                else:
                    parsed_results.append(
                        {
                            "main_text": r["structured_formatting"]["main_text"],
                            "secondary_text": "",
                            "place_id": r["place_id"],
                        }
                    )
            return parsed_results
        elif result["status"] == "ZERO_RESULTS":
            return None
        elif result["status"] != "UNKNOWN_ERROR":
            # Many API errors cannot be fixed by a retry, e.g. INVALID_REQUEST
            raise RuntimeError(result["error_message"])

    @classmethod
    def _parse_place_detail_response(
        cls, response_to_parse
    ):  # pragma: no cover (todo one day)
        result = json.load(response_to_parse)
        if result["status"] == "OK":
            return result["result"]
        elif result["status"] == "ZERO_RESULTS":
            return None
        elif result["status"] != "UNKNOWN_ERROR":
            # Many API errors cannot be fixed by a retry, e.g. INVALID_REQUEST
            raise RuntimeError(result["error_message"])
