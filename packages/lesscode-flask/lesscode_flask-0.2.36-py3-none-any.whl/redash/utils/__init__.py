import binascii

import datetime
import decimal

import json

import uuid

from sqlalchemy.orm.query import Query


class JSONEncoder(json.JSONEncoder):
    """Adapter for `json.dumps`."""

    def __init__(self, **kwargs):
        from redash.query_runner import query_runners

        self.encoders = [r.custom_json_encoder for r in query_runners.values() if hasattr(r, "custom_json_encoder")]
        super().__init__(**kwargs)

    def default(self, o):
        for encoder in self.encoders:
            result = encoder(self, o)
            if result:
                return result
        if isinstance(o, Query):
            result = list(o)
        elif isinstance(o, decimal.Decimal):
            result = float(o)
        elif isinstance(o, (datetime.timedelta, uuid.UUID)):
            result = str(o)
        # See "Date Time String Format" in the ECMA-262 specification.
        elif isinstance(o, datetime.datetime):
            result = o.isoformat()
            if o.microsecond:
                result = result[:23] + result[26:]
            if result.endswith("+00:00"):
                result = result[:-6] + "Z"
        elif isinstance(o, datetime.date):
            result = o.isoformat()
        elif isinstance(o, datetime.time):
            if o.utcoffset() is not None:
                raise ValueError("JSON can't represent timezone-aware times.")
            result = o.isoformat()
            if o.microsecond:
                result = result[:12]
        elif isinstance(o, memoryview):
            result = binascii.hexlify(o).decode()
        elif isinstance(o, bytes):
            result = binascii.hexlify(o).decode()
        else:
            result = super().default(o)
        return result


def json_loads(data, *args, **kwargs):
    """A custom JSON loading function which passes all parameters to the
    json.loads function."""
    return json.loads(data, *args, **kwargs)


def json_dumps(data, *args, **kwargs):
    """A custom JSON dumping function which passes all parameters to the
    json.dumps function."""
    kwargs.setdefault("cls", JSONEncoder)
    kwargs.setdefault("ensure_ascii", False)
    # Float value nan or inf in Python should be render to None or null in json.
    # Using allow_nan = True will make Python render nan as NaN, leading to parse error in front-end
    kwargs.setdefault("allow_nan", False)
    return json.dumps(data, *args, **kwargs)
