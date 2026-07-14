"""Client for the U.S. Census Bureau International Trade API (imports/hs).

Kept deliberately dependency-free (stdlib `urllib`) and split into pure,
unit-testable pieces: `build_query` assembles a URL, `parse_response` turns the
Census "list of lists" payload into typed row dicts. `CensusClient.fetch` is the
only part that touches the network.

Docs: https://api.census.gov/data/timeseries/intltrade/imports/hs.html
A free API key is required: https://api.census.gov/data/key_signup.html
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass

BASE_URL = "https://api.census.gov/data/timeseries/intltrade/imports/hs"

# The columns we pull. GEN_VAL_MO is the general customs import value for the
# period; I_COMMODITY at COMM_LVL=HS2 is the 2-digit Harmonized System chapter.
GET_FIELDS = ["CTY_CODE", "CTY_NAME", "I_COMMODITY", "GEN_VAL_MO"]


def build_query(
    period: str,
    *,
    cty_code: str = "all",
    comm_lvl: str = "HS2",
    api_key: str | None = None,
) -> str:
    """Return the fully-formed request URL for one month of imports.

    `period` is 'YYYY-MM'. `cty_code='all'` pulls every trading partner.
    """
    params = {
        "get": ",".join(GET_FIELDS),
        "time": period,
        "COMM_LVL": comm_lvl,
        "CTY_CODE": cty_code,
    }
    if api_key:
        params["key"] = api_key
    return f"{BASE_URL}?{urllib.parse.urlencode(params)}"


def parse_response(payload: list[list[str]], period: str) -> list[dict]:
    """Turn the Census response (first row = header) into typed row dicts.

    Rows with a missing/non-numeric value are skipped rather than crashing the
    load — the API occasionally returns blank GEN_VAL_MO for suppressed cells.
    """
    if not payload or len(payload) < 2:
        return []
    header = payload[0]
    idx = {name: header.index(name) for name in GET_FIELDS if name in header}
    rows: list[dict] = []
    for raw in payload[1:]:
        try:
            value = int(raw[idx["GEN_VAL_MO"]])
        except (KeyError, ValueError, IndexError):
            continue
        rows.append(
            {
                "period": period,
                "cty_code": raw[idx["CTY_CODE"]],
                "cty_name": raw[idx["CTY_NAME"]],
                "hs2": raw[idx["I_COMMODITY"]],
                "gen_val_mo": value,
            }
        )
    return rows


@dataclass
class CensusClient:
    api_key: str | None = None
    timeout: int = 60

    @classmethod
    def from_env(cls) -> "CensusClient":
        return cls(api_key=os.environ.get("CENSUS_API_KEY"))

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)

    def fetch(self, period: str, *, cty_code: str = "all") -> list[dict]:
        if not self.has_key:
            raise RuntimeError(
                "CENSUS_API_KEY is not set. Get a free key at "
                "https://api.census.gov/data/key_signup.html, or run the "
                "pipeline without a key to use the bundled offline sample."
            )
        url = build_query(period, cty_code=cty_code, api_key=self.api_key)
        with urllib.request.urlopen(url, timeout=self.timeout) as resp:
            payload = json.load(resp)
        return parse_response(payload, period)
