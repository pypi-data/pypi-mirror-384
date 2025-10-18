from django.utils.http import urlencode
import re

from w.services.abstract_service import AbstractService


class UrlService(AbstractService):
    @staticmethod
    def get_url_query_string(**query_params):
        return f"{urlencode(query_params, doseq=True)}"

    @staticmethod
    def resolve_absolute_url(base_url, relative_url):
        if base_url[-1:] == "/":
            # remove ending /
            base_url = base_url[:-1]

        if relative_url[:1] != "/":
            # add starting /
            relative_url = f"/{relative_url}"

        return f"{base_url}{relative_url}"

    @staticmethod
    def is_valid_url(url: str) -> bool:
        if (
            re.match(
                r"^[(http(s)?):\/\/(www\.)?a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&\/\/=]*)$",  # noqa
                url,
            )
            is not None
        ):
            return True
        return False
