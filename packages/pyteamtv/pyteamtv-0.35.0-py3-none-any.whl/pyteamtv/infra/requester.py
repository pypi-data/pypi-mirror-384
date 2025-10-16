import time
from copy import copy
from typing import Optional

import requests
import logging


logger = logging.getLogger(__name__)


class Requester(object):
    def __init__(
        self,
        base_url,
        jwt_token,
        headers: dict = None,
        use_cache: bool = False,
        timeout: Optional[int] = 30,
    ):
        self._base_url = base_url
        self.jwt_token = jwt_token
        self.headers = dict(**headers) if headers else {}
        self.use_cache = use_cache
        self.timeout = timeout
        self._session = None

    @property
    def session(self):
        if not getattr(self, "_session", None):
            if self.use_cache:
                import requests_cache
                import hashlib
                from datetime import timedelta

                self._session = requests_cache.CachedSession(
                    hashlib.md5(self.jwt_token.encode("ascii")).hexdigest(),
                    expire_after=timedelta(days=1),
                )
            else:
                self._session = requests.Session()

        return self._session

    def __getstate__(self):
        d = copy(self.__dict__)
        if "_session" in d:
            del d["_session"]
        return d

    def request(self, method, url, input_=None):
        import pyteamtv

        start = time.time()
        headers = self.headers
        headers["Authorization"] = f"Bearer {self.jwt_token}"
        headers["User-Agent"] = f"pyteamtv {pyteamtv.__version__}"
        logger.debug(f"Sending {method} request to {url} - {self.headers}")
        response = self.session.request(
            method,
            self._base_url + url,
            headers=headers,
            json=input_,
            timeout=self.timeout,
        )
        took = time.time() - start
        logger.debug(f"Request took: {took * 1000:.2f}ms")
        response.raise_for_status()

        return response.json()

    def with_extra_headers(self, headers: dict):
        new_headers = dict(**self.headers)
        new_headers.update(headers)
        return self.__class__(
            self._base_url,
            jwt_token=self.jwt_token,
            headers=new_headers,
            use_cache=self.use_cache,
        )
