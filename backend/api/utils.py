import datetime
import json
from typing import Any
from flask import Response
from dataclasses import is_dataclass, asdict


def make_response(data: Any, status_code: int = 200) -> Response:
    def convert(obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if is_dataclass(obj):
            return convert(asdict(obj))
        if hasattr(obj, "model_dump"):
            return convert(obj.model_dump())
        if isinstance(obj, list):
            return [convert(item) for item in obj]
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        return obj

    try:
        payload = convert(data)
        return Response(
            response=json.dumps(payload),
            status=status_code,
            content_type="application/json"
        )
    except Exception as e:
        # In case something went wrong with serialization
        error = {"error": "Internal Server Error", "message": str(e)}
        return Response(
            response=json.dumps(error),
            status=500,
            content_type="application/json"
        )
