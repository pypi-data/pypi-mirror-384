import json
import datetime
from decimal import Decimal

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

class JSONDecoder(json.JSONDecoder):
    pass

class JSONProvider:
    def __init__(self, app=None):
        self.app = app
        self.encoder = JSONEncoder()
        self.decoder = JSONDecoder()

    def dumps(self, obj, **kwargs):
        return self.encoder.encode(obj)

    def loads(self, s, **kwargs):
        return self.decoder.decode(s)

    def response(self, data):
        from .response import Response
        return Response(self.dumps(data), content_type='application/json')

json_provider = JSONProvider()