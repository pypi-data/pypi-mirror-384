from typing import Any, List, Dict, Optional

import requests

from audiosalad_sdk.utils import cache


class AudioSaladWeb:
    """
    Service for interacting with AudioSalad web API.
    This service handles web-based API calls that require browser-like headers and cookies.
    """

    CACHE_KEY_AUTH_TOKEN = "audiosalad_web_x-auth-token"
    CACHE_TIMEOUT = 24 * 60 * 60  # 24 hours in seconds

    @classmethod
    def get_auth_token_instructions(cls) -> str:
        return (
            "Please follow these steps to get the auth token:\n"
            "1. Log in to AudioSalad web interface (https://<client-namespace>.audiosalad.com)\n"
            "2. Open browser developer tools (F12)\n"
            "3. Go to Network tab\n"
            "4. Find any request to the API\n"
            '5. Look for "x-auth-token" in the request headers\n'
            "6. Copy the token value\n"
            "7. Use this token with the service"
        )

    def __init__(
        self, auth_token: Optional[str] = None, cookie_token: Optional[str] = None
    ):
        # First try to get token from cache if no token provided
        if not auth_token:
            auth_token = self._get_cached_token()

        if not auth_token:
            raise ValueError(
                "No auth token provided. " + self.get_auth_token_instructions()
            )

        # If a new token was provided, cache it
        if auth_token and auth_token != self._get_cached_token():
            self._cache_token(auth_token)

        self.auth_token = auth_token
        self.cookie_token = cookie_token
        self.base_url = "https://<client-namespace>.audiosalad.com/api"
        self.session = requests.Session()
        self._setup_session()
        self._update_auth_header()

    def _get_cached_token(self) -> Optional[str]:
        return cache.get(self.CACHE_KEY_AUTH_TOKEN)

    def _cache_token(self, token: str):
        cache.set(self.CACHE_KEY_AUTH_TOKEN, token, self.CACHE_TIMEOUT)

    def _update_auth_header(self):
        if self.auth_token:
            self.session.headers.update({"x-auth-token": self.auth_token})

    def _setup_session(self):
        self.session.headers.update(
            {
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-US,en;q=0.9,pl;q=0.8",
                "cache-control": "no-cache",
                "dnt": "1",
                "pragma": "no-cache",
                "priority": "u=1, i",
                "referer": "https://<client-namespace>.audiosalad.com/labels",
                "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/137.0.0.0 Safari/537.36"
                ),
            }
        )

        cookies = {
            "_gcl_au": "1.1.551314839.1741700432",
            "_ga": "GA1.1.1763456114.1741700456",
            "_ga_0WMZ88LVKB": "GS1.1.1745413770.4.1.1745413780.0.0.0",
            "_ga_QSL7D5DRB3": "GS2.1.s1748251997$o25$g1$t1748252417$j0$l0$h0",
            "AWSALBTG": "dummy",
            "AWSALBTGCORS": "dummy",
        }

        if self.cookie_token:
            cookies["cookie_token"] = self.cookie_token

        self.session.cookies.update(cookies)

    def _get_paginated_data(
        self, endpoint: str, page: int = 1, page_length: int = 25
    ) -> List[Dict[str, Any]]:
        all_items: List[Dict[str, Any]] = []
        current_page = page

        while True:
            response = self.session.get(
                f"{self.base_url}/{endpoint}",
                params={"page": current_page, "page_length": page_length},
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                items = data
            elif endpoint == "config/labels":
                items = data.get("labels", [])
            else:
                items = data.get("data", [])

            if not items:
                break

            all_items.extend(items)

            if len(items) < page_length:
                break

            current_page += 1

        return all_items

    def get_artists(self, page: int = 1, page_length: int = 25) -> List[Dict[str, Any]]:
        return self._get_paginated_data("artists", page, page_length)

    def get_labels(self, page: int = 1, page_length: int = 25) -> List[Dict[str, Any]]:
        response = self.session.get(f"{self.base_url}/config/labels")
        response.raise_for_status()
        data = response.json()
        return data.get("labels", [])

    def get_genres(self, page: int = 1, page_length: int = 25) -> List[Dict[str, Any]]:
        return self._get_paginated_data("genres", page=1, page_length=1000)

    def get_genre(self, genre_id: str) -> Dict[str, Any]:
        return self.session.get(f"{self.base_url}/genres/{genre_id}").json()
