from pathlib import Path
from types import SimpleNamespace

from w.services.technical.google_map_service import GoogleMapService
from w.services.technical.models.request_response import RequestResponse
from w.services.technical.request_service import RequestService
from w.tests.mixins.testcase_mixin import TestCaseMixin


def _get_dataset(relative_dataset):
    current_dir = Path(__file__).parent
    dataset_filename = current_dir.joinpath(
        "../fixtures/datasets", relative_dataset
    ).resolve()
    return TestCaseMixin._get_dataset(dataset_filename.name, dataset_filename)


def _mock_search_by_phone_number():
    response = SimpleNamespace(
        content=_get_dataset("google_map/search_by_phone_number").encode("utf8"),
        url="https://maps.googleapis.com/maps/api/place/findplac"
        "efromtext/json?input=%2B3309%2072%2037%2089%2011"
        "&inputtype=phonenumber&fields=place_id,name,formatted_address,type&key=None ",
        ok=True,
        headers={},
        status_code=200,
    )
    return {
        "service": RequestService,
        "method_name": "get",
        "return_value": RequestResponse(response=response),
    }


def _mock_parse_place_detail_response():
    return {
        "service": GoogleMapService,
        "method_name": "_parse_place_detail_response",
        "return_value": _get_dataset("google_map/_parse_place_detail_response.json"),
    }
