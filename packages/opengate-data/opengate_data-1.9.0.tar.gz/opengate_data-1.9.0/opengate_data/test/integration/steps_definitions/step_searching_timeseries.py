import os
import json
import requests
import pytest
from dotenv import dotenv_values
from pytest_bdd import scenarios, given, when, then, parsers
import time

scenarios("searching/searching_timeseries.feature")

def _env_cfg():
    BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
    )
    env_path = os.path.join(BASE_DIR, ".env")
    return dotenv_values(env_path)

@pytest.fixture
def api_ctx():
    return {"payload": None, "response": None, "timeserie_identifier": None}

@given("I prepare a timeserie payload:")
def step_prepare_timeserie_payload(api_ctx, docstring):
    api_ctx["payload"] = json.loads(docstring)

@when('I provision the timeserie for organization')
def step_post_timeserie(api_ctx):
    cfg = _env_cfg()

    org = cfg.get("ORGANIZATION") or os.getenv("ORGANIZATION")
    if not org:
        raise RuntimeError("Key 'ORGANIZATION' not found in .env or environment")

    base_url = (cfg.get("OPENGATE_URL") or os.getenv("OPENGATE_URL") or "").rstrip("/")
    if not base_url:
        raise RuntimeError("OPENGATE_URL not found in .env or environment")
    if "/north/" not in base_url.lower():
        base_url += "/north/v80"

    url_base = f"{base_url}/timeseries/provision/organizations/{org}"
    payload = api_ctx["payload"]

    api_key = cfg.get("OPENGATE_API_KEY") or os.getenv("OPENGATE_API_KEY")
    jwt_token = cfg.get("JWT") or os.getenv("JWT")

    headers = {"Content-Type": "application/json", "User-Agent": "pytest-bdd/og-data-py"}
    if api_key:
        headers["X-ApiKey"] = api_key
    elif jwt_token:
        headers["Authorization"] = f"Bearer {jwt_token}"
    else:
        raise RuntimeError("Provide OPENGATE_API_KEY or JWT in .env or environment")

    user = cfg.get("OPENGATE_USER") or os.getenv("OPENGATE_USER")
    password = cfg.get("OPENGATE_PASSWORD") or os.getenv("OPENGATE_PASSWORD")
    auth = (user, password) if user and password else None

    try:
        r_list = requests.get(url_base, headers=headers, verify=False, timeout=30)
        if "application/json" in (r_list.headers.get("Content-Type") or ""):
            data = r_list.json()
            existing = next((t for t in (data.get("timeseries") or data.get("items") or [])
                             if t.get("name") == payload.get("name")), None)
            if existing and existing.get("identifier"):
                del_url = f"{url_base}/{existing['identifier']}"
                requests.delete(del_url, headers=headers, verify=False, timeout=30)
    except Exception:
        pass

    r = requests.post(url_base, json=payload, headers=headers, auth=auth, verify=False, timeout=30)

    api_ctx["response"] = {
        "status_code": r.status_code,
        "body": (r.json() if "application/json" in (r.headers.get("Content-Type") or "") else None),
        "text": r.text,
        "url": r.url,
    }

@given(parsers.parse('I search for timeserie by name "{timeserie_name}"'))
def step_search_timeserie_by_name(api_ctx, builder_holder, timeserie_name: str):
    cfg = _env_cfg()
    org = cfg.get("ORGANIZATION") or os.getenv("ORGANIZATION")
    if not org:
        raise RuntimeError("Key 'ORGANIZATION' not found in .env or environment")

    base_url = (cfg.get("OPENGATE_URL") or os.getenv("OPENGATE_URL") or "").rstrip("/")
    if not base_url:
        raise RuntimeError("OPENGATE_URL not found in .env or environment")
    if "/north/" not in base_url.lower():
        base_url += "/north/v80"

    url = f"{base_url}/timeseries/provision/organizations/{org}"

    api_key = cfg.get("OPENGATE_API_KEY") or os.getenv("OPENGATE_API_KEY")
    jwt_token = cfg.get("JWT") or os.getenv("JWT")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-ApiKey"] = api_key
    elif jwt_token:
        headers["Authorization"] = f"Bearer {jwt_token}"
    else:
        raise RuntimeError("Provide OPENGATE_API_KEY or JWT")

    r = requests.get(url, headers=headers, verify=False, timeout=30)
    data = r.json() if "application/json" in (r.headers.get("Content-Type") or "") else {}
    lst = data.get("timeseries") or data.get("items") or []
    match = next((t for t in lst if t.get("name") == timeserie_name), None)
    if not match:
        raise RuntimeError(f"Timeserie with name {timeserie_name} not found")
    identifier = match["identifier"]
    api_ctx["timeserie_identifier"] = identifier

    if builder_holder.get("instance"):
        print("identifier", identifier)
        builder_holder["instance"].with_identifier(identifier)


# ===== Delete =====
@when("I delete the timeserie")
def step_delete_timeserie(api_ctx):
    cfg = _env_cfg()
    org = cfg.get("ORGANIZATION") or os.getenv("ORGANIZATION")
    if not org:
        raise RuntimeError("Key 'ORGANIZATION' not found in .env or environment")

    base_url = (cfg.get("OPENGATE_URL") or os.getenv("OPENGATE_URL") or "").rstrip("/")
    if not base_url:
        raise RuntimeError("OPENGATE_URL not found in .env or environment")
    if "/north/" not in base_url.lower():
        base_url += "/north/v80"

    identifier = api_ctx.get("timeserie_identifier")
    if not identifier:
        raise RuntimeError("Timeserie identifier not set in context (run the search step first)")

    url = f"{base_url}/timeseries/provision/organizations/{org}/{identifier}"

    api_key = cfg.get("OPENGATE_API_KEY") or os.getenv("OPENGATE_API_KEY")
    jwt_token = cfg.get("JWT") or os.getenv("JWT")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-ApiKey"] = api_key
    elif jwt_token:
        headers["Authorization"] = f"Bearer {jwt_token}"

    r = requests.delete(url, headers=headers, verify=False, timeout=30)

    api_ctx["response"] = {
        "status_code": r.status_code,
        "body": (r.json() if "application/json" in (r.headers.get("Content-Type") or "") else None),
        "text": r.text,
        "url": r.url,
    }
    

# ===== Asserts =====
@then(parsers.parse("The HTTP status should be {code:d}"))
def step_check_status(api_ctx, code: int):
    assert api_ctx["response"] and api_ctx["response"]["status_code"] == code, \
        f"Expected {code}, got {api_ctx['response']}"
    time.sleep(2)


