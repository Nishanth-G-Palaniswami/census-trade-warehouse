"""Offline unit tests for the Census API client — no network required."""

from census_trade.census_api import build_query, parse_response


def test_build_query_has_required_params():
    url = build_query("2023-12", api_key="SECRET")
    assert url.startswith(
        "https://api.census.gov/data/timeseries/intltrade/imports/hs?"
    )
    assert "time=2023-12" in url
    assert "COMM_LVL=HS2" in url
    assert "CTY_CODE=all" in url
    assert "key=SECRET" in url
    # all requested fields present in the get= list
    for field in ["CTY_CODE", "CTY_NAME", "I_COMMODITY", "GEN_VAL_MO"]:
        assert field in url


def test_build_query_omits_key_when_absent():
    assert "key=" not in build_query("2023-12")


def test_parse_response_maps_and_types_rows():
    payload = [
        ["CTY_CODE", "CTY_NAME", "I_COMMODITY", "GEN_VAL_MO", "time"],
        ["5700", "CHINA", "85", "15200400000", "2023-12"],
        ["2010", "MEXICO", "87", "10450900000", "2023-12"],
    ]
    rows = parse_response(payload, "2023-12")
    assert len(rows) == 2
    assert rows[0] == {
        "period": "2023-12",
        "cty_code": "5700",
        "cty_name": "CHINA",
        "hs2": "85",
        "gen_val_mo": 15200400000,
    }
    assert isinstance(rows[0]["gen_val_mo"], int)


def test_parse_response_skips_suppressed_or_blank_values():
    payload = [
        ["CTY_CODE", "CTY_NAME", "I_COMMODITY", "GEN_VAL_MO", "time"],
        ["5700", "CHINA", "85", "", "2023-12"],       # blank
        ["2010", "MEXICO", "87", "N", "2023-12"],      # non-numeric
        ["1220", "CANADA", "27", "9130600000", "2023-12"],
    ]
    rows = parse_response(payload, "2023-12")
    assert len(rows) == 1
    assert rows[0]["cty_name"] == "CANADA"


def test_parse_response_empty_payload():
    assert parse_response([], "2023-12") == []
    assert parse_response([["CTY_CODE", "GEN_VAL_MO"]], "2023-12") == []
