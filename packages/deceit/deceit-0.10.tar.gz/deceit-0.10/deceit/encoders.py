from datetime import date
from datetime import datetime
from decimal import Decimal
import json


def make_json_serializable(value, fn=lambda x: x):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat('T', 'seconds')
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return fn(value)


class JsonEncoder(json.JSONEncoder):
    def default(self, o):  # pylint: disable=method-hidden
        return make_json_serializable(o, super(JsonEncoder, self).default)
