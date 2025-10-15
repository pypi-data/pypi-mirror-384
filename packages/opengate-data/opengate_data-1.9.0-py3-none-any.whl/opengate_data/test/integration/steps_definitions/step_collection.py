# opengate_data/test/integration/collect/steps_collection.py

import pytest
from pytest_bdd import scenarios, given, then, parsers
import ast, json, os
from dotenv import dotenv_values
import pandas as pd
from typing import List
from opengate_data.utils.utils import send_request
from pathlib import Path
from opengate_data.test.utils.path_resolver import resolve_test_path

scenarios("collect/iot_collection.feature")
scenarios("collect/iot_bulk_collection.feature")
scenarios("collect/iot_pandas_collection.feature")

# --------- Create/Delete devices ---------

def _env_cfg():
    BASE_DIR = Path(__file__).resolve().parents[4]
    env_path = BASE_DIR / ".env"
    env = dotenv_values(str(env_path))

    org = env.get("ORGANIZATION")
    channel = env.get("CHANNEL", "default_channel")
    service_group = env.get("SERVICE_GROUP", "emptyServiceGroup"),

    if not org:
        raise RuntimeError(f"You must define ORGANIZATION in {env_path}")

    return {
        "ORGANIZATION": org,
        "CHANNEL": channel,
        "SERVICE_GROUP": service_group
    }

@given(parsers.parse('I want to use add datastream datapoints "{datastream_id}", {datapoints}'))
def given_add_datastream_datapoints(builder_holder, datastream_id, datapoints):
    parsed = ast.literal_eval(datapoints)
    builder_holder["instance"].add_datastream_datapoints(datastream_id, parsed)

@given(parsers.parse('I want to use device identifier "{device_identifier}"'))
def given_device_identifier(builder_holder, device_identifier):
    builder_holder["instance"].with_device_identifier(device_identifier)

def _delete_device(client, org: str, device_id: str):
    url = f"{client.url}/north/v80/provision/organizations/{org}/devices/{device_id}?flattened=true"
    resp = send_request(method="delete", headers=client.headers, url=url)
    if resp.status_code not in (200, 204, 404):
        raise AssertionError(f"Delete {device_id} failed: HTTP {resp.status_code} - {resp.text}")

def _parse_ids(ids_literal: str) -> List[str]:
    ids_str = ids_literal.strip()
    if ids_str.startswith("["):
        import json
        return json.loads(ids_str)
    return [s.strip().strip('"').strip("'") for s in ids_str.split(",") if s.strip()]

# --- Cleanup automatic ---
@pytest.fixture(scope="module")
def _created_devices_registry():
    return set()

@pytest.fixture(scope="module", autouse=True)
def _cleanup_created_devices(client, _created_devices_registry):
    yield
    cfg = _env_cfg()
    for dev in list(_created_devices_registry):
        try:
            _delete_device(client, cfg["ORGANIZATION"], dev)
        except Exception:
            pass

# --------- Given ---------


@given(parsers.parse('I want to use add datastream datapoints "{datastream_id}", {datapoints}'))
def given_add_datastream_datapoints(builder_holder, datastream_id, datapoints):
    parsed = ast.literal_eval(datapoints)
    builder_holder["instance"].add_datastream_datapoints(datastream_id, parsed)

@given(parsers.parse('I want to use add datastream datapoints with from "{datastream_id}", {datapoints}'))
def given_add_datastream_datapoints_with_from(builder_holder, datastream_id, datapoints):
    parsed = ast.literal_eval(datapoints)
    builder_holder["instance"].add_datastream_datapoints_with_from(datastream_id, parsed)

@given("I set the JSON payload for the IoT collection")
def given_set_json_payload(builder_holder):
    data = {
        "version": "1.1.1",
        "datastreams": [
            {"id": "entity.location", "datapoints": [{"value": {"position": {"type": "Point", "coordinates": [1111, 3333]}}}]},
            {"id": "device.temperature.value", "datapoints": [{"value": 25, "at": 1000}]},
        ],
    }
    builder_holder["instance"].from_dict(data)

@given('I want to collect from spreadsheet')
def from_spreadsheet(builder_holder):
    xlsx_path = resolve_test_path("test/utils/collect.xlsx")
    builder_holder["instance"].from_spreadsheet(str(xlsx_path), 0)

@given(parsers.parse(
    'I want to use add device datastream datapoints with from "{device_id}", "{datastream_id}", {datapoints}'))
def add_device_datastream_datapoints_with_from(builder_holder, device_id, datastream_id, datapoints):
    datapoints = eval(datapoints)
    builder_holder["instance"].add_device_datastream_datapoints_with_from(device_id, datastream_id, datapoints)

@given(parsers.parse('I want to use add device datastream datapoints "{device_id}", "{datastream_id}", {datapoints}'))
def add_device_datastream_datapoints(builder_holder, device_id, datastream_id, datapoints):
    datapoints = eval(datapoints)
    builder_holder["instance"].add_device_datastream_datapoints(device_id, datastream_id, datapoints)

@given(parsers.parse(
    'I want to use from dataframe with device id "{device_id}", datastream id "{datastream_id}" and value {value}'))
def from_dataframe(builder_holder, device_id, datastream_id, value):
    df = pd.DataFrame({'device_id': [device_id], "data_stream_id": [datastream_id], 'value': [value]})
    builder_holder["instance"].from_dataframe(df)

@given("I have a sample dataframe with multiple devices")
def given_sample_dataframe_multi(builder_holder):
    data = {
        'device_id': ["entityTestingOpendatePy1", "entityTestingOpendatePy2", "entityTestingOpendatePy1"],
        'at': ['20241126 11:39:45.211 +1:00', None, None],
        'device.temperature.value': [1.1, 1.2, 1.3],
        'device.name': ["name1", "name2", "name3"],
        'device.storage.disk.usage': [3.1, 300, 3.3],
        'feed': ["100", "200", "300"],
        'source': ["HTTP-Basic", "HTTP-Basic", "HTTP-Basic"],
        'sourceInfo': ["Collection OK", "Collection OK", "Collection OK"],
        'entity.location.current.value.position.coordinates': [
            [-3.7028, 40.0000],
            [-5.7028, 47.41675],
            [-3.7028, 40.41675],
        ]
    }
    df = pd.DataFrame(data)
    builder_holder["instance"].from_dataframe(df)

@given("I have a sample dataframe with columns with current.*")
def given_sample_dataframe_current(builder_holder):
    df = pd.DataFrame({
        "device_id": ["entityTestingOpendatePy1"],
        "at": [None],
        "entity.location.current.value.position.coordinates": [[-3.7028, 40.4168]]
    })
    builder_holder["instance"].from_dataframe(df)

@given(parsers.parse('I set the max bytes per request to "{max_bytes}"'))
def given_max_bytes(builder_holder, max_bytes: str):
    builder_holder["instance"].with_max_bytes_per_request(int(max_bytes))

@given(parsers.parse('I want to use columns {cols}'))
def given_with_columns(builder_holder, cols: str):
    cols_str = cols.strip()
    col_list = json.loads(cols_str) if cols_str.startswith('[') else ast.literal_eval(f'[{cols_str}]')
    assert isinstance(col_list, list) and all(isinstance(x, str) for x in col_list), "Columns must be list[str]"
    builder_holder["instance"].with_columns(col_list)

# --------- Then ---------

@then(parsers.parse('The status code from device "{device}" iot collection should be "{status_code}"'))
def check_response(builder_holder, device, status_code):
    response = builder_holder["instance"].build().execute()
    assert response[device]['status_code'] == int(status_code)

@then("The dictionary should match the expected JSON output")
def then_verify_dict(builder_holder):
    to_dict = builder_holder["instance"].build().to_dict()
    expect_dict = {
        "version": "1.1.1",
        "datastreams": [
            {"id": "entity.location", "datapoints": [{"value": {"position": {"type": "Point", "coordinates": [1111, 3333]}}}]},
            {"id": "device.temperature.value",
             "datapoints": [{"value": 25, "at": 1000}, {"value": 25, "at": 1431602523123, "from": 1431602523123},
                            {"value": 25, "at": 1431602523123}]},
        ],
    }
    assert to_dict == expect_dict

@then("The pandas dataframe should contain only selected columns plus base")
def then_verify_columns(builder_holder):
    df = builder_holder["instance"].build().execute()
    selected = builder_holder["instance"].columns
    expected_cols = ["device_id", "at"] + selected + ["status"]
    assert list(df.columns) == expected_cols, f"Got {list(df.columns)}"

@then(parsers.parse('I delete test device {ids}'))
def step_delete_devices(client, ids):
    cfg = _env_cfg()
    for dev in _parse_ids(ids):
        _delete_device(client, cfg["ORGANIZATION"], dev)




