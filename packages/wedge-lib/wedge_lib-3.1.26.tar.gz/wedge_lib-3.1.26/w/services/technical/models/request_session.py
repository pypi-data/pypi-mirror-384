from requests import Session


class RequestSession:
    def __init__(self, base_url, **options):
        self.request = Session()
        self.base_url = base_url
        self.timeout = options["timeout"] if "timeout" in options else None
        auth = options.pop("auth", None)
        headers = options.pop("headers", None)
        cookies = options.pop("cookies", None)

        if auth:
            self.request.auth = auth
        if headers:
            self.request.headers = headers
        if cookies:
            self.request.cookies = cookies

    def render_url(self, relative_url):
        return f"{self.base_url}{relative_url}"

    def get_cookies(self):  # pragma: no cover (todo one day)
        return self.request.cookies.get_dict()

    def __str__(self):
        return f"session on {self.base_url}"
