import ast
import json
import time
from configparser import ConfigParser
import os
import pytest
import requests
from pytest_bdd import given, when, then, parsers
from pathlib import Path
from dotenv import dotenv_values
from typing import List

from opengate_data.utils.utils import send_request
from opengate_data.ai_models.ai_models import AIModelsBuilder
from opengate_data.ai_pipelines.ai_pipelines import AIPipelinesBuilder
from opengate_data.ai_transformers.ai_transformers import AITransformersBuilder
from opengate_data.rules.rules import RulesBuilder
from opengate_data.searching.builder.entities_search import EntitiesSearchBuilder
from opengate_data.searching.builder.datasets_search import DatasetsSearchBuilder
from opengate_data.searching.builder.timeseries_search import TimeseriesSearchBuilder
from opengate_data.searching.builder.datapoints_search import DataPointsSearchBuilder
from opengate_data.searching.builder.rules_search import RulesSearchBuilder as SearchingRulesBuilder
from opengate_data.collection.iot_collection import IotCollectionBuilder
from opengate_data.collection.iot_bulk_collection import IotBulkCollectionBuilder
from opengate_data.provision.bulk.provision_bulk import ProvisionBulkBuilder
from opengate_data.provision.asset.provision_asset import ProvisionAssetBuilder
from opengate_data.provision.devices.provision_device import ProvisionDeviceBuilder
from opengate_data.collection.iot_pandas_collection import PandasIotCollectionBuilder

BUILDER_MAP = {
    "model": AIModelsBuilder,
    "transformer": AITransformersBuilder,
    "pipeline": AIPipelinesBuilder,
    "rule": RulesBuilder,
    "entity": EntitiesSearchBuilder,
    "dataset": DatasetsSearchBuilder,
    "timeserie": TimeseriesSearchBuilder,
    "datapoint": DataPointsSearchBuilder,
    "iot collection": IotCollectionBuilder,
    "iot bulk collection": IotBulkCollectionBuilder,
    "iot pandas collection": PandasIotCollectionBuilder, 
    "provision bulk": ProvisionBulkBuilder,
    "searching rules": SearchingRulesBuilder,
    "provision asset": ProvisionAssetBuilder,
    "provision device": ProvisionDeviceBuilder,
}

# --- Cleanup automatic ---
@pytest.fixture(scope="module")
def _created_devices_registry():
    return set()

@pytest.fixture
def api_ctx():
    return {"response": None}

def _env_cfg():
    BASE_DIR = Path(__file__).resolve().parents[4]
    env_path = BASE_DIR / ".env"
    env = dotenv_values(str(env_path))

    org = env.get("ORGANIZATION")
    channel = env.get("CHANNEL", "default_channel")
    service_group = env.get("SERVICE_GROUP", "emptyServiceGroup")
    url = env.get("OPENGATE_URL")
    api_key = env.get("OPENGATE_API_KEY")
    jwt = env.get("JWT")
    if not org:
        raise RuntimeError(f"You must define ORGANIZATION in {env_path}")

    return {
        "ORGANIZATION": org,
        "CHANNEL": channel,
        "SERVICE_GROUP": service_group,
        "OPENGATE_URL": url,
        "OPENGATE_API_KEY": api_key,
        "JWT": jwt
    }

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]

def _resolve_test_path(p: str | os.PathLike) -> Path:
    p = Path(p)
    if p.is_absolute():
        return p
    return _repo_root() / p

def _ensure_ini_section(config_file: str, section: str, key: str):
    cfg_path = _resolve_test_path(config_file)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)

    cp = ConfigParser()
    if cfg_path.exists():
        cp.read(cfg_path)
    if not cp.has_section(section):
        cp.add_section(section)
    if not cp.has_option(section, key):
        cp.set(section, key, "")

    with cfg_path.open("w") as f:
        cp.write(f)

def _parse_ids(ids_literal: str) -> List[str]:
    ids_str = ids_literal.strip()
    if ids_str.startswith("["):
        import json
        return json.loads(ids_str)
    return [s.strip().strip('"').strip("'") for s in ids_str.split(",") if s.strip()]


def _create_device(client, org, channel, service_group, device_id):
    url = f"{client.url}/north/v80/provision/organizations/{org}/devices?flattened=true"
    payload = {
        "provision.device.identifier": {"_value": {"_current": {"value": device_id}}},
        "provision.administration.organization": {"_value": {"_current": {"value": org}}},
        "provision.administration.channel": {"_value": {"_current": {"value": channel}}},
        "provision.administration.serviceGroup": {"_value": {"_current": {"value": service_group}}},
        "provision.device.software": {"_value": {"_current": {"value": []}}},
    }
    headers = {**client.headers, "Accept": "application/json", "Content-Type": "application/json"}
    resp = send_request(method="post", headers=headers, url=url, json_payload=payload)

    if resp.status_code in (200, 201, 409):
        return

    try:
        body = resp.json()
    except Exception:
        body = {}

    msg = str(body) if body else resp.text
    if resp.status_code == 400 and ("Entity duplicated" in msg or "0x010114" in msg):
        return

    raise AssertionError(f"Create {device_id} failed: HTTP {resp.status_code} - {resp.text}")

    
def _delete_device(client, org: str, device_id: str):
    url = f"{client.url}/north/v80/provision/organizations/{org}/devices/{device_id}?flattened=true"
    resp = send_request(method="delete", headers=client.headers, url=url)
    if resp.status_code not in (200, 204, 404):
        raise AssertionError(f"Delete {device_id} failed: HTTP {resp.status_code} - {resp.text}")

# --- Fixture to store the active builder ---
@pytest.fixture
def builder_holder():
    """Holds the current builder instance across steps."""
    return {"instance": None}


# ------Given ------

@given(parsers.parse('I want to build a "{build_type}"'))
def step_build(client, builder_holder, build_type):
    builder_cls = BUILDER_MAP.get(build_type)
    if not builder_cls:
        raise ValueError(f"Unknown builder type: {build_type}")
    builder_holder["instance"] = builder_cls(client)

@given(parsers.parse('I want to use a select {select}'))
def step_prediction_result(builder_holder, select):
    select = select.replace("'", '"')
    select_list = json.loads(select)
    builder_holder["instance"].with_select(select_list)

@given(parsers.re(r'^I want to use a filter\s+(?P<filter_data>.+)$'))
def step_with_filter(builder_holder, filter_data: str):
    s = filter_data.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1]
    data = ast.literal_eval(s)
    builder_holder["instance"].with_filter(data)

@given(parsers.parse('I want to use a format "{format_path}"'))
def step_with_format(builder_holder, format_path):
    builder_holder["instance"].with_format(format_path)

@given(parsers.parse('I want to use organization'))
def step_organization(builder_holder):
    org = _env_cfg()['ORGANIZATION']
    builder_holder["instance"].with_organization_name(org)

@given(parsers.parse('I want to use a channel'))
def step_with_channel(builder_holder):
    channel = _env_cfg()['CHANNEL']
    builder_holder["instance"].with_channel(channel)

@given(parsers.parse('I want to use a name "{name}"'))
def step_with_name(builder_holder, name):
    builder_holder["instance"].with_name(name)

@given('I want to use a active rule as False')
def step_rule_activate_false(builder_holder):
    builder_holder["instance"].with_active(False)

@given(parsers.parse('I want to search by name "{name}"'))
def step_search_by_name(builder_holder, name):
    builder_holder["instance"].with_find_by_name(name)

@given(parsers.parse('I want to use a mode "{mode}"'))
def step_with_mode(builder_holder, mode):
    builder_holder["instance"].with_mode(mode)

@given(parsers.parse('I want to use a type "{type_data}"'))
def step_with_type(builder_holder, type_data):
    builder_holder["instance"].with_type(ast.literal_eval(type_data))

@given(parsers.parse('I want to use a condition "{condition}"'))
def step_with_condition(builder_holder, condition):
    builder_holder["instance"].with_condition(ast.literal_eval(condition))

@given(parsers.parse('I want to use a actions delay {actions_delay}'))
def step_with_actions_delay(builder_holder, actions_delay):
    builder_holder["instance"].with_actions_delay(1000)

@given(parsers.parse('I want to use a actions "{actions}"'))
def step_with_actions(builder_holder, actions):
    builder_holder["instance"].with_actions(ast.literal_eval(actions))

@given(parsers.parse('I want to search id in a configuration file "{config_file}" "{section}" "{config_key}"'))
def step_search_id_config_file(builder_holder, config_file, section, config_key):
    cfg_path = _resolve_test_path(config_file)
    builder_holder["instance"].with_config_file(str(cfg_path), section, config_key)
    time.sleep(2)

@given(parsers.parse('I want to save id in a configuration file "{config_file}" "{section}" "{config_key}"'))
def step_set_id_config_file(builder_holder, config_file, section, config_key):
    cfg_path = _resolve_test_path(config_file)
    _ensure_ini_section(str(cfg_path), section, config_key)
    builder_holder["instance"].with_config_file(str(cfg_path), section, config_key)
    time.sleep(2)

@given(parsers.parse('I ensure test devices exist: {ids}'))
def ensure_test_devices(client, _created_devices_registry, ids):
    """
    Deletes if it exists (ignores 404) and creates it afterward. Doesn't fail if it didn't exist.
    Logs for deletion at the end of the module.
    """
    cfg = _env_cfg()
    org = cfg["ORGANIZATION"]
    ch = cfg["CHANNEL"]
    sg = cfg["SERVICE_GROUP"]

    for dev in _parse_ids(ids):
        try:
            _delete_device(client, org, dev)
        except AssertionError:
            pass
        _create_device(client, org, ch, sg, dev)
        _created_devices_registry.add(dev)

@given(parsers.parse('I delete device if exists {ids}'))
def ensure_test_devices(client, ids):
    """
    Deletes if it exists (ignores 404) and creates it afterward. Doesn't fail if it didn't exist.
    Logs for deletion at the end of the module.
    """
    cfg = _env_cfg()
    org = cfg["ORGANIZATION"]

    for dev in _parse_ids(ids):
        try:
            _delete_device(client, org, dev)
        except AssertionError:
            pass

# ------When ------


@when('I create')
def step_create(builder_holder):
    builder_holder["instance"].create()
    time.sleep(2)


@when('I search')
def step_search(builder_holder):
    builder_holder["instance"].search()
    time.sleep(2)

@when('I delete')
def step_delete(builder_holder):
    builder_holder["instance"].delete()
    time.sleep(2)

@when('I update')
def step_update(builder_holder):
    builder_holder["instance"].update()
    time.sleep(2)

@when('I find one')
def step_find_one(builder_holder):
    builder_holder["instance"].find_one()
    time.sleep(2)

@when('I find all')
def step_find_all(builder_holder):
     builder_holder["instance"].find_all()
     time.sleep(2)
    
@when(parsers.parse('I collect IoT for device "{device_id}" with payload:'))
def when_collect_iot(api_ctx, device_id: str, docstring: str):
    cfg = _env_cfg()

    base_url = (cfg.get("OPENGATE_URL") or os.getenv("OPENGATE_URL") or "").rstrip("/")
    if not base_url:
        raise RuntimeError("OPENGATE_URL not found in .env or environment")

    # Asegura /south/v80 si no viene en la URL base
    if "/south/" not in base_url.lower():
        base_url = f"{base_url}/south/v80"

    api_key = cfg.get("OPENGATE_API_KEY") or os.getenv("OPENGATE_API_KEY")
    if not api_key:
        raise RuntimeError("OPENGATE_API_KEY not found in .env or environment")

    url = f"{base_url}/devices/{device_id}/collect/iot"
    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "X-ApiKey": api_key,
        "User-Agent": "pytest-bdd/og-data-py",
    }

    try:
        payload = json.loads(docstring)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON payload in feature docstring: {e}") from e

    r = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)

    api_ctx["response"] = {
        "status_code": r.status_code,
        "body": (r.json() if "application/json" in (r.headers.get("Content-Type") or "") else None),
        "text": r.text,
        "url": r.url,
    }

# ------Then ------
@then(parsers.parse("The HTTP status should be {code:d}"))
def step_check_status(api_ctx, code: int):
    assert api_ctx["response"] and api_ctx["response"]["status_code"] == code, \
        f"Expected {code}, got {api_ctx['response']}"
    
@then(parsers.parse('The status code from collection should be "{status_code}"'))
def then_collection_status_code(builder_holder, status_code):
    resp = builder_holder["instance"].build().execute()
    assert isinstance(resp, dict)
    assert "status_code" in resp
    assert resp["status_code"] == int(status_code)

@then(parsers.parse('The response should be "{status_code}"'))
def step_status_code(builder_holder, status_code):
    response = builder_holder["instance"].build().execute()
    assert response["status_code"] == int(status_code)

@then(parsers.parse('The response search should be "{expected_type}"'))
def step_response_type(builder_holder, expected_type):
    raw = builder_holder["instance"].build().execute()
    payload = raw.get("response", raw) if isinstance(raw, dict) else raw

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            pass

    if expected_type == "dict":
        prueba= isinstance(payload, dict)
        assert isinstance(payload, dict)
    elif expected_type == "csv":
        assert isinstance(payload, str)
    elif expected_type == "pandas":
        import pandas as pd
        assert isinstance(payload, pd.DataFrame)
    else:
        raise ValueError(f"Unsupported expected_type: {expected_type}")
