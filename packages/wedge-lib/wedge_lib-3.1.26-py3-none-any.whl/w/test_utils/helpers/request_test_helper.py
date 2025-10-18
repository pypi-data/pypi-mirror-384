from contextlib import contextmanager
from unittest.mock import patch

from w.services.technical.json_service import JsonService
from w.services.technical.filesystem_service import FilesystemService
from w.services.technical.models.request_response import RequestResponse


@contextmanager
def request_failure(response: dict, method="get"):
    """
    Request failure
    Args:
        response (dict): response params :
            {
                "url": <optional:url>
                "status_code": <optional:status code default 200>,
                "headers": <optional:list[dict]|dict: headers or list of headers>,
                "content": <optional:str|dict: content to use for response>,
                "json_file": <optional:json file or list json files for response>,
                "file": <optional:file for response>,
                "success": <bool: default True>
            }
        method(str): get|post|patch|put|del
    """
    default_response = {"status_code": 400, "success": False, "reason": "Bad Request"}
    response = {**default_response, **response}
    params = _get_patch_params(response, method)
    with patch(**params) as m:
        yield m


@contextmanager
def request_success(response: dict, method="get"):
    """
    Request success
    Args:
        response (dict): response params :
            {
                "url": <optional:url>
                "status_code": <optional:status code default 200>,
                "headers": <optional:list[dict]|dict: headers or list of headers>,
                "content": <optional:str|dict: content to use for response>,
                "json_file": <optional:json file or list json files for response>,
                "file": <optional:file for response>,
                "success": <bool: default True>
            }
        method(str): get|post|patch|put|del
    """
    default_response = {"status_code": 200}
    response = {**default_response, **response}

    with patch(**_get_patch_params(response, method)) as m:
        yield m


@contextmanager
def mock_request(responses, method="get"):
    """
    Request success
    Args:
        responses (list): list of responses
        method(str): get|post|patch|put|del
    """
    params = {
        "target": f"w.services.technical.request_service.RequestService.{method}",
        "side_effect": responses,
    }
    with patch(**params) as m:
        yield m


def _get_response_from_json(json_file, params):
    with open(json_file) as f:
        content = f.read()
        if "reason" not in params:
            params["content"] = content
        else:
            params["content"] = params["reason"]
            params["orig_content"] = content
    return RequestResponse(**params)


def get_response(**params):
    """
    Get request response

    Args:
        params (**): response params :
            {
                "url": <optional:url>
                "status_code": <optional:status code default 200>,
                "headers": <optional:list[dict]|dict: headers or list of headers>,
                "content": <optional:str|dict: content to use for response>,
                "json_file": <optional:str|list:json file or json files list for response>,
                "file": <optional:file for response>,
                "success": <bool: default True>
            }

    Returns:
        Union[RequestResponse,List[RequestResponse]]: response or list of responses (if json_file is list)
    """
    default_params = {
        "content": "some content",
        "status_code": 200,
        "headers": {},
        "success": True,
    }
    params = {**default_params, **params}

    if "file" in params:
        params["content"] = FilesystemService.read_file(params["file"])

    if "content" in params and isinstance(params["content"], dict):
        params["content"] = JsonService.dump(params["content"])

    if "json_file" not in params:
        return RequestResponse(**params)

    if not isinstance(params["json_file"], list):
        return _get_response_from_json(params["json_file"], params)

    result = []
    for json_file in params["json_file"]:
        result.append(_get_response_from_json(json_file, params))
    return result


def get_401_response(**params):
    default_params = {
        "return_content": "Unauhtorized",
        "status_code": 401,
        "success": False,
    }
    params = {**default_params, **params}
    return get_response(**params)


def get_400_response(**params):
    default_params = {"status_code": 400, "success": False, "reason": "Bad Request"}
    params = {**default_params, **params}
    return get_response(**params)


def _get_patch_params(response, method):
    response = get_response(**response)
    params = {"target": f"w.services.technical.request_service.RequestService.{method}"}
    if not isinstance(response, list):
        params["return_value"] = response
    else:
        params["side_effect"] = response
    return params
