# opengate_data/test/integration/steps_definitions/step_provision.py

from pytest_bdd import scenarios, given, when, then, parsers
import ast
import pandas as pd
from dotenv import dotenv_values
from pathlib import Path
from opengate_data.test.utils.path_resolver import resolve_test_path

scenarios("provision/provision_bulk.feature")
scenarios("provision/provision_asset.feature")
scenarios("provision/provision_device.feature")

# --------- ENV ---------
def _env_cfg():
    BASE_DIR = Path(__file__).resolve().parents[4]
    env_path = BASE_DIR / ".env"
    env = dotenv_values(str(env_path))
    org = env.get("ORGANIZATION")
    channel = env.get("CHANNEL", "default_channel")
    service_group = env.get("SERVICE_GROUP", "emptyServiceGroup")
    if not org:
        raise RuntimeError(f"You must define ORGANIZATION in {env_path}")
    return {"ORGANIZATION": org, "CHANNEL": channel, "SERVICE_GROUP": service_group}

from opengate_data.provision.asset.provision_asset import ProvisionAssetBuilder
from opengate_data.provision.devices.provision_device import ProvisionDeviceBuilder

def _provision_kind(builder_holder) -> str:
    inst = builder_holder.get("instance")
    if isinstance(inst, ProvisionAssetBuilder):
        return "asset"
    if isinstance(inst, ProvisionDeviceBuilder):
        return "device"
    return "device"

# --------- GIVEN  ---------
@given(parsers.parse('I want to use a provision identifier "{identifier}"'))
def given_provision_identifier(builder_holder, identifier):
    builder_holder["instance"].with_provision_identifier(identifier)

@given(parsers.parse('I want to use from dict "{json_dict}"'))
def given_from_dict(builder_holder, json_dict):
    builder_holder["instance"].from_dict(ast.literal_eval(json_dict))

@given(parsers.parse('I want to use from csv "{csv_path}"'))
def given_from_csv(builder_holder, csv_path):
    csv_abs = resolve_test_path(csv_path)
    builder_holder["instance"].from_csv(str(csv_abs))

@given(parsers.parse('I want to use from excel "{excel_path}"'))
def given_from_excel(builder_holder, excel_path):
    excel_abs = resolve_test_path(excel_path)
    builder_holder["instance"].from_excel(str(excel_abs))

@given(parsers.parse('I want to use from pandas "{pandas}"'))
def given_from_pandas(builder_holder, pandas):
    df1 = pd.DataFrame(ast.literal_eval(pandas))
    builder_holder["instance"].from_dataframe(df1)

@given(parsers.parse('I want to use a provision organization'))
def given_provision_org(builder_holder):
    cfg = _env_cfg()
    builder_holder["instance"].with_provision_organization(cfg["ORGANIZATION"])

@given(parsers.parse('I want to use a identifier "{identifier}"'))
def given_identifier(builder_holder, identifier):
    builder_holder["instance"].with_identifier(identifier)

@given(parsers.parse('I want to use a provision channel'))
def given_provision_channel(builder_holder):
    cfg = _env_cfg()
    builder_holder["instance"].with_provision_channel(cfg["CHANNEL"])

@given(parsers.parse('I want to use a provision serviceGroup'))
def given_provision_service_group(builder_holder):
    cfg = _env_cfg()
    builder_holder["instance"].with_provision_service_group(cfg["SERVICE_GROUP"])

@given(parsers.parse('I want to use add provision datastream value "{datastream}", {value}'))
def given_add_ds_value(builder_holder, datastream, value):
    builder_holder["instance"].add_provision_datastream_value(datastream, ast.literal_eval(value))


@given(parsers.parse('I want to use from dataframe for provision entity with identifier "{identifier}"'))
def given_df_for_entity(builder_holder, identifier):
    cfg = _env_cfg()
    kind = _provision_kind(builder_holder)
    data = {
        f'provision.{kind}.identifier.current.value': [identifier],
        'provision.administration.organization.current.value': [cfg["ORGANIZATION"]],
        'provision.administration.channel.current.value': [cfg["CHANNEL"]],
        'provision.administration.serviceGroup.current.value': [cfg["SERVICE_GROUP"]],
    }
    df = pd.DataFrame(data)
    builder_holder["instance"].from_dataframe(df)

@given(parsers.parse('I want to use update from dataframe for provision entity with identifier "{identifier}"'))
def given_df_update_for_entity(builder_holder, identifier):
    cfg = _env_cfg()
    kind = _provision_kind(builder_holder)
    data = {
        f'provision.{kind}.identifier.current.value': [identifier],
        'provision.administration.organization.current.value': [cfg["ORGANIZATION"]],
        'provision.administration.channel.current.value': [cfg["CHANNEL"]],
        'provision.administration.serviceGroup.current.value': ['level1SecurityServiceGroup'],
    }
    df = pd.DataFrame(data)
    builder_holder["instance"].from_dataframe(df)


@given(parsers.parse('I want to use from dict for provision {entity_type} with identifier "{identifier}"'))
def given_dict_for_entity(builder_holder, entity_type, identifier):
    entity_type = entity_type.strip().lower()
    if entity_type not in ("asset", "device"):
        raise RuntimeError(f"Unsupported entity_type '{entity_type}'")
    cfg = _env_cfg()
    dct = {
        "resourceType": {"_current": {"value": f"entity.{entity_type}"}},
        "provision": {
            "administration": {
                "channel": {"_current": {"value": cfg["CHANNEL"]}},
                "organization": {"_current": {"value": cfg["ORGANIZATION"]}},
                "serviceGroup": {"_current": {"value": cfg["SERVICE_GROUP"]}},
            },
            entity_type: {
                "identifier": {"_current": {"value": identifier}}
            },
        },
    }
    builder_holder["instance"].from_dict(dct)

@given(parsers.parse('I want to use update/modify from dict for provision {entity_type} with identifier "{identifier}"'))
def given_dict_update_for_entity(builder_holder, entity_type, identifier):
    entity_type = entity_type.strip().lower()
    if entity_type not in ("asset", "device"):
        raise RuntimeError(f"Unsupported entity_type '{entity_type}'")
    cfg = _env_cfg()
    dct = {
        "resourceType": {"_current": {"value": f"entity.{entity_type}"}},
        "provision": {
            "administration": {
                "channel": {"_current": {"value": cfg["CHANNEL"]}},
                "organization": {"_current": {"value": cfg["ORGANIZATION"]}},
                "serviceGroup": {"_current": {"value": "level1SecurityServiceGroup"}},
            },
            entity_type: {
                "identifier": {"_current": {"value": identifier}}
            },
        },
    }
    builder_holder["instance"].from_dict(dct)

@given(parsers.parse('I want to use from dataframe for provision device with identifier "{device_identifier}"'))
def alias_df_for_device(builder_holder, device_identifier):
    cfg = _env_cfg()
    df = pd.DataFrame({
        'provision.device.identifier.current.value': [device_identifier],
        'provision.administration.organization.current.value': [cfg["ORGANIZATION"]],
        'provision.administration.channel.current.value': [cfg["CHANNEL"]],
        'provision.administration.serviceGroup.current.value': [cfg["SERVICE_GROUP"]],
    })
    builder_holder["instance"].from_dataframe(df)


# --------- WHEN extra ---------

@when('I modify')
def when_modify(builder_holder):
    builder_holder["instance"].modify()

