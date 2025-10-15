# opengate_data/test/integration/conftest.py

import warnings
from pathlib import Path

import pytest
from dotenv import dotenv_values
from urllib3.exceptions import InsecureRequestWarning

from opengate_data.opengate_client import OpenGateClient

# Filtrado de warnings de peticiones inseguras (https)
warnings.filterwarnings("ignore", category=InsecureRequestWarning, module="urllib3")


@pytest.fixture(scope="session")
def client() -> OpenGateClient:
    def find_env(start: Path) -> Path | None:
        for p in [start, *start.parents]:
            cand = p / ".env"
            if cand.exists():
                return cand
        return None

    env_path = find_env(Path(__file__).resolve())
    env = dotenv_values(str(env_path)) if env_path else {}

    url = env.get("OPENGATE_URL")
    api_key = env.get("OPENGATE_API_KEY")
    user = env.get("OPENGATE_USER")
    password = env.get("OPENGATE_PASSWORD")

    if not url or not api_key:
        raise RuntimeError(
            f"You must define OPENGATE_URL and OPENGATE_API_KEY in {env_path or '.env not found'}"
        )

    return OpenGateClient(url=url, api_key=api_key, user=user, password=password)
