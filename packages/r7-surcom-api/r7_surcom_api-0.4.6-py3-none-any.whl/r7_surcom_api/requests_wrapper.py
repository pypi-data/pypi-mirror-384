"""
Wrapper for a Requests 'Session'
"""
from importlib.metadata import PackageNotFoundError, version

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from r7_surcom_api import constants


class TimeoutAdapter(HTTPAdapter):
    """
    Override the HTTP timeout
    """
    # This TimeoutAdapter is used by the HttpSession (wrapper for access to third-party services).

    def __init__(self, *args, timeout=constants.REQUESTS_TIMEOUT, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # caller can specify a timeout, but not infinite (None). Otherwise default
        # to system constant
        self._timeout = timeout if timeout else constants.REQUESTS_TIMEOUT

    def send(self, *args, **kwargs):
        # Set timeout so that our total runtime is constrained
        kwargs["timeout"] = self._timeout
        result = super().send(*args, **kwargs)
        return result


class HttpSession(requests.Session):
    """
    Session for operations that call source REST APIs:
    - enables correct 'verify' behavior,
    - adds an enforced timeout whose timeout can be passed in or defaulted to system constant
    """
    def __init__(self,
                 timeout=constants.REQUESTS_TIMEOUT,
                 max_retries=None,
                 **kwargs) -> None:
        super().__init__()
        self.headers.update({"Accept-Encoding": "gzip"})

        # Add a fairly conservative retry-handler, unless the caller specifies their own.
        # Retry on 429 "retry", but also on "gatweway" error/timeout which are often temporary
        if max_retries is None:
            retry_methods = ["HEAD", "GET", "OPTIONS"]
            retry_statuses = [429, 502, 503, 504]
            max_retries = Retry(
                total=5,
                backoff_factor=2,
                allowed_methods=retry_methods,
                status_forcelist=retry_statuses
            )

        self.mount("http://", TimeoutAdapter(timeout=timeout, max_retries=max_retries))
        self.mount("https://", TimeoutAdapter(timeout=timeout, max_retries=max_retries))

        # Set identifiable headers
        self.headers.update({"Accept-Encoding": "gzip"})
        try:
            self.headers.update({
                "User-Agent": f"Noetic-Connector/{version(__package__)}"
            })
        except PackageNotFoundError:
            pass

    def merge_environment_settings(self, url, proxies, stream, verify, *args, **kwargs):
        """
        Setting 'session.verify' to False doesn't work when REQUESTS_CA_BUNDLE is set
        (and it is, for the Noetic runtime) - https://github.com/psf/requests/issues/3829
        so we use this wrapper class to ignore the envvar if verify=False.
        """
        if self.verify is False:
            verify = False

        return super(HttpSession, self).merge_environment_settings(url, proxies, stream, verify, *args, **kwargs)
