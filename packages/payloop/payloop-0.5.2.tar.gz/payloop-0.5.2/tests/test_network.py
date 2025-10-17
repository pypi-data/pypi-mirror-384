import os

from payloop._config import Config
from payloop._network import Api


def test_api_url():
    os.environ["PAYLOOP_API_URL_BASE"] = "https://abc.def.com"

    assert Api(Config()).url("ghijkl") == "https://abc.def.com/v1/-/ghijkl"
