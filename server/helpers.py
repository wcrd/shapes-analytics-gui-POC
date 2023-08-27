from enum import Enum
import json
from uuid import UUID
import math

MsgType = Enum("MsgType", ['ERROR', 'SUCCESS'])

def msg(msg_type:MsgType, msg:str, **kwargs):
    return {
        "msg_type": msg_type.name,
        "msg": msg,
        "meta": kwargs
    }

def data(*args, meta={}, **kwargs):
    if len(args)==1:
        return { "data": args[0], "meta": meta }
    elif args: print("Too many args provided. Provide one arg, or a set of kwargs")
    else:
        return { "data": kwargs, "meta": meta }

# Special JSON encoder to handle SET and UUID conversion from Pandas
class MatchJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, UUID):
            return str(obj)
        elif math.isnan(obj):
            return ""
        return json.JSONEncoder.default(self, obj)