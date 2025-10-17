r"""
 ___           _
| _ \__ _ _  _| |___  ___ _ __
|  _/ _` | || | / _ \/ _ \ '_ \
|_| \__,_|\_, |_\___/\___/ .__/
          |__/           |_|AI             07312025 / optimus codex
"""

import json
import os
import pprint
import traceback

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from payloop._config import Config


class Api:
    def __init__(self, config: Config):
        self.__base = os.environ.get("PAYLOOP_API_URL_BASE")
        if self.__base is None:
            self.__base = "https://api.trypayloop.com"

        self.config = config

    def get(self, route):
        r = self.__session().get(
            self.url(route), headers={"Authorization": f"Bearer {self.config.api_key}"}
        )

        r.raise_for_status()

        return r.json()

    def patch(self, route, json={}):
        r = self.__session().patch(
            self.url(route),
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            json=json,
        )

        r.raise_for_status()

        return r.json()

    def post(self, route, json={}):
        r = self.__session().post(
            self.url(route),
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            json=json,
        )

        r.raise_for_status()

        return r.json()

    def __session(self):
        adapter = HTTPAdapter(
            max_retries=_ApiRetryRecoverable(
                allowed_methods=["GET", "PATCH", "POST", "PUT", "DELETE"],
                backoff_factor=1,
                raise_on_status=False,
                status=None,
                total=5,
            )
        )

        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def url(self, route):
        return f"{self.__base}/v1/-/{route}"


class _ApiRetryRecoverable(Retry):
    def is_retry(self, method, status_code, has_retry_after=False):
        return 500 <= status_code <= 599


class Collector:
    def __init__(self, config: Config):
        self.__base = os.environ.get("PAYLOOP_COLLECTOR_URL_BASE")
        if self.__base is None:
            self.__base = "https://collector.trypayloop.com"

        self.config = config

    def fire_and_forget(self, payload):
        if os.environ.get("PAYLOOP_TEST_MODE") is None:
            try:
                requests.post(
                    f"{self.__base}/rec",
                    json=payload,
                    timeout=self.config.secs_post_timeout,
                )
            except Exception as e:
                payload["meta"]["fnfg"] = {
                    "exc": traceback.format_exc(),
                    "status": "recovered",
                }

                try:
                    requests.post(
                        f"{self.__base}/rec",
                        json=json.loads(json.dumps(payload, default=str)),
                        timeout=self.config.secs_post_timeout,
                    )
                except:
                    if self.config.raise_final_request_attempt is True:
                        raise
                    else:
                        pass
        else:
            pprint.pprint(payload)

        return self
