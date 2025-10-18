import logging

import requests
import validators
from requests.exceptions import ConnectTimeout, ReadTimeout, ConnectionError

from w.services.abstract_service import AbstractService
from w.services.technical.models.request_response import RequestResponse
from w.services.technical.models.request_session import RequestSession

logger = logging.getLogger(__name__)


class RequestService(AbstractService):
    """Service Request"""

    @classmethod
    def init_session(cls, base_url, **options) -> RequestSession:
        """
        Initialize session

        Args:
            base_url (str): base url for request
            **options:
                auth (tuple): credentials (<username>, <password>)
                headers (dict): headers
                cookies (dict): cookies
                timeout (float): number of seconds before timeout

        Returns:
            RequestSession
        """
        if not validators.url(base_url):
            raise RuntimeError("Invalid url '{}'".format(base_url))

        default_options = {"headers": None, "cookies": None}
        options = {**default_options, **options}

        return RequestSession(base_url=base_url, **options)

    @staticmethod
    def _service_unavailable(exception):
        logger.warning(f"Request {exception}")
        return RequestResponse(
            success=False, content="Service unavailable", status_code=503
        )

    @classmethod
    def get_cookies(cls, session: RequestSession):  # pragma: no cover (todo one day)
        return session.request.cookies.get_dict()

    @classmethod
    def get(cls, url, session: RequestSession = None, **kwargs) -> RequestResponse:
        """
        Sends a GET request.
        Args:
            url (str): full url if no session else complete url part
            session (RequestSession|None): session from RequestService::init_session
            **kwargs:  Optional arguments that lib ``request`` takes (like timeout).

        Returns:
            Response
        """

        logger.info('Request GET %s kwargs="%s"', url, kwargs)
        try:
            if session is not None:
                if session.timeout is not None:
                    kwargs["timeout"] = session.timeout
                response = session.request.get(session.render_url(url), **kwargs)
            else:
                response = requests.get(url, **kwargs)
            return RequestResponse(response)
        except (ConnectTimeout, ReadTimeout, ConnectionError) as e:
            return cls._service_unavailable(e)

    @classmethod
    def _run_maj_action(
        cls, action, url, data, session: RequestSession = None, **kwargs
    ):
        """
        Sends a POST/PUT/PATCH request.
        Args:
            url (str): full url if no session else complete url part
            data (dict|str): data to post/put/patch
            session (RequestSession|None): session from RequestService::init_session
            **kwargs:  Optional arguments that lib ``request`` takes (like timeout).

        Returns:
            Response
        """
        logger.info("Request %s %s", action.upper(), url)
        logger.debug('data="%s" kwargs="%s"', data, kwargs)
        try:
            if session is not None:
                if session.timeout is not None:  # pragma: no cover (todo one day)
                    kwargs["timeout"] = session.timeout
                response = getattr(session.request, action)(
                    session.render_url(url), data=data, **kwargs
                )
            else:
                response = getattr(requests, action)(url, data=data, **kwargs)
            return RequestResponse(response)
        except (ConnectTimeout, ReadTimeout, ConnectionError) as e:
            return cls._service_unavailable(e)

    @classmethod
    def post(cls, url, data, session: RequestSession = None, **kwargs):
        """
        Sends a POST request.
        Args:
            url (str): full url if no session else complete url part
            data (dict|str): data to post
            session (RequestSession|None): session from RequestService::init_session
            **kwargs:  Optional arguments that lib ``request`` takes (like timeout).

        Returns:
            Response
        """
        return cls._run_maj_action("post", url, data, session, **kwargs)

    @classmethod
    def patch(cls, url, data, session: RequestSession = None, **kwargs):
        """
        Sends a PATCH request.
        Args:
            url (str): full url if no session else complete url part
            data (dict|str): data to patch
            session (RequestSession|None): session from RequestService::init_session
            **kwargs:  Optional arguments that lib ``request`` takes (like timeout).

        Returns:
            Response
        """
        return cls._run_maj_action("patch", url, data, session, **kwargs)

    @classmethod
    def put(cls, url, data, session: RequestSession = None, **kwargs):
        """
        Sends a PATCH request.
        Args:
            url (str): full url if no session else complete url part
            data (dict|str): data to put
            session (RequestSession|None): session from RequestService::init_session
            **kwargs:  Optional arguments that lib ``request`` takes (like timeout).

        Returns:
            Response
        """
        return cls._run_maj_action("put", url, data, session, **kwargs)

    @classmethod
    def delete(cls, url, data=None, session: RequestSession = None, **kwargs):
        """
        Sends a DELETE request.
        Args:
            url (str): full url if no session else complete url part
            data (dict|str): data to delete
            session (RequestSession|None): session from RequestService::init_session
            **kwargs:  Optional arguments that lib ``request`` takes (like timeout).

        Returns:
            Response
        """
        return cls._run_maj_action("delete", url, data, session, **kwargs)
