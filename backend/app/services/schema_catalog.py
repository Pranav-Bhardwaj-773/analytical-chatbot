import json
from functools import lru_cache
from pathlib import Path

_CATALOG_PATH = Path(__file__).resolve().parents[2] / "schema_catalog.json"


@lru_cache
def load_schema_catalog() -> dict:
    with _CATALOG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def catalog_prompt_text() -> str:
    return json.dumps(load_schema_catalog(), indent=2)