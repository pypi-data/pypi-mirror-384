import json
import logging
import re

logger = logging.getLogger(__name__)


class RequestResponse:
    """Request Response Model"""

    def __init__(self, response=None, **kwargs):
        """
        Args:
            response (requests.Response)
        """
        self._redirect_location = None
        if response is not None:
            self.url = response.url
            try:
                self._orig_content = response.content.decode()
                self.is_decoded = True
            except UnicodeDecodeError:
                self._orig_content = response.content
                self.is_decoded = False
            logger.info(f"Response status={response.status_code} to {self.url}")
            logger.debug(f"Response content={self._orig_content}")
            if response.ok:
                if self.is_decoded:
                    try:
                        self._content = json.loads(response.content)
                    except ValueError:
                        self._content = self._orig_content
                else:
                    self._content = self._orig_content
            else:
                self._content = (
                    self._orig_content if not response.reason else response.reason
                )

            self._success = response.ok
            self._status_code = response.status_code
            self._headers = response.headers
            if int(self._status_code) == 302:
                self._redirect_location = response.headers["Location"]
                logger.info(f"Redirect location={self._redirect_location}")
        else:
            # only for testing purpose
            self.url = kwargs.get("url", "http://dummy.com/")
            self._success = kwargs.get("success", None)
            self._status_code = kwargs.get("status_code", None)
            self._headers = kwargs.get("headers", None)
            self._orig_content = kwargs.get("orig_content", None)
            self.is_decoded = kwargs.get("is_decoded", True)
            if int(self._status_code) == 302:  # pragma: no cover (todo one day)
                self._redirect_location = kwargs["headers"]["Location"]
            content = kwargs.get("content", None)
            try:
                self._content = json.loads(content)
            except ValueError:
                self._content = content

    @property
    def content(self):
        """dict: response content"""
        return self._content

    @property
    def success(self):
        """bool: request succeeded ?"""
        return self._success

    @property
    def status_code(self):
        """int: status code"""
        return self._status_code

    @property
    def orig_content(self):
        """original response content"""
        return self._orig_content

    @property
    def redirect_location(self):  # pragma: no cover (todo one day)
        """redirect location"""
        return self._redirect_location

    @property
    def is_redirect(self):
        """Check if reponse is redirect"""
        return self._redirect_location is not None

    def get_header(self, name):
        """Get header name value"""
        if name in self._headers:
            return self._headers[name]
        return None

    def get_content_filename(self):
        """Get filename if exists"""
        content_disposition = self.get_header("content-disposition")
        if content_disposition:
            fname = re.findall('filename="(.+)"', content_disposition)
            if len(fname) == 0:
                return None
            return fname[0]

        # parsing url to get the filename
        if not self.is_decoded and self.url.find("/"):
            return self.url.rsplit("/", 1)[1]
        return None

    def as_attachment(self):
        """check if header Content-Disposition header specify as attachment"""
        content_disposition = self.get_header("content-disposition")
        return content_disposition is not None and "attachment" in content_disposition

    def __str__(self) -> str:  # pragma: no cover (todo one day)
        if self.success:
            return f"status code: {self.status_code}"
        return f"{self.status_code} - {self.content}"
