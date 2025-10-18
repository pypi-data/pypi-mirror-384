import re

from w.services.abstract_service import AbstractService


class IpService(AbstractService):
    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        if (
            re.match(
                r"^(?:\d{1,3}\.){3}\d{1,3}$",
                ip,
            )
            is not None
        ):
            return True
        return False
