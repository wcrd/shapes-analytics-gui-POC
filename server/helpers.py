from enum import Enum

MsgType = Enum("MsgType", ['ERROR', 'SUCCESS'])

def msg(msg_type:MsgType, msg:str, **kwargs):
    return {
        "msg_type": msg_type.name,
        "msg": msg,
        "meta": kwargs
    }

def data(*args, **kwargs):
    if len(args)==1:
        return { "data": args[0] }
    elif args: print("Too many args provided. Provide one arg, or a set of kwargs")
    else:
        return { "data": kwargs }