import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta

from aip.utils import CACHE_DIR, can_launch_browser, open_page_in_browser
from aip.utils.console import console, err_console
from dateutil.tz import tzutc

logger = logging.getLogger(__name__)


def _utc_now():
    return datetime.now(tzutc())


class AIPTokenProvider:
    METHOD = "AIP"

    def __init__(self, client, time_fetcher=_utc_now):
        self._client = client
        self._now = time_fetcher
        self._cache_dir = CACHE_DIR
        self._oidc_url = os.getenv(
            "AIP_OIDC_URL",
            self._client.url,
        )

    @property
    def _client_id(self):
        return os.getenv(
            "AIP_OIDC_CLIENT_ID",
            "aip_workbench",
        )

    @property
    def _cache_key(self):
        pass

    def _save_token(self, res):
        pass

    def _wait_for_token(self, device_code):
        pass

    def revoke_token(self, token=None):
        pass

    def get_user_info(self):
        pass

    def user_info(self):
        pass

    def generate_token(self):
        pass

    def load_token(self):
        return {"access_token": "123", "id_token": "321"}
