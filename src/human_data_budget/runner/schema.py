"""JSON Schema loading and artifact validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema


def validate_json(instance: dict[str, Any], schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=instance, schema=schema)
