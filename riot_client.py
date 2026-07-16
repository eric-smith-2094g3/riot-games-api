import os
import time
import urllib.parse
import urllib.request
import urllib.error
import json

# mapping league platforms to regional routing groups for match-v5 and riot-account
ROUTING_REGIONS = {
    "na1": "americas",
    "br1": "americas",
    "la1": "americas",
    "la2": "americas",
    "euw1": "europe",
    "eun1": "europe",
    "tr1": "europe",
    "ru": "europe",
    "kr": "asia",
    "jp1": "asia",
    "oc1": "sea",
    "ph2": "sea",
    "sg2": "sea",
    "th2": "sea",
    "tw2": "sea",
    "vn2": "sea",
}


class RiotClient:
    """Bare client for account lookup and match-v5 endpoints."""

    def __init__(self, api_key: str = None, region: str = "na1"):
        self.api_key = api_key or os.environ.get("RIOT_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError("missing RIOT_API_KEY")
        self.region = region.lower()
        self.regional_host = ROUTING_REGIONS.get(self.region, "americas")

    def _request(self, host: str, path: str):
        url = f"https://{host}.api.riotgames.com{path}"
        req = urllib.request.Request(
            url,
            headers={
                "X-Riot-Token": self.api_key,
                "User-Agent": "lol-summary-tool",
            },
        )

        for attempt in range(5):
            try:
                with urllib.request.urlopen(req) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as err:
                if err.code == 429:
                    retry_header = err.headers.get("Retry-After")
                    # riot docs say retry-after is seconds, but fallback if header is omitted
                    wait = int(retry_header) if retry_header else (1.5 * (attempt + 1))
                    # print(f"backed off for {wait}s due to 429")
                    time.sleep(wait)
                    continue
                if err.code == 404:
                    return None
                raise RuntimeError(f"HTTP {err.code}: {err.reason} ({url})") from err
        raise RuntimeError("rate limits exhausted")

    def get_account_by_riot_id(self, game_name: str, tag_line: str):
        quoted_name = urllib.parse.quote(game_name)
        quoted_tag = urllib.parse.quote(tag_line)
        path = f"/riot/account/v1/accounts/by-riot-id/{quoted_name}/{quoted_tag}"
        return self._request(self.regional_host, path)

    def get_match_ids(self, puuid: str, count: int = 15, queue: int = None):
        params = [f"count={count}"]
        if queue:
            params.append(f"queue={queue}")
        qs = "&" + "&".join(params) if params else ""
        path = f"/lol/match/v5/matches/by-puuid/{puuid}/ids?{qs.lstrip('&')}"
        return self._request(self.regional_host, path) or []

    def get_match(self, match_id: str):
        path = f"/lol/match/v5/matches/{match_id}"
        return self._request(self.regional_host, path)
