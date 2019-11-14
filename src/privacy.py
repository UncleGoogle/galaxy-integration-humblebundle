import logging
import re

from model.game import Key


class SensitiveFilter(logging.Filter):
    KEY = 'redeemed_key_value'    

    def __init__(self):
        super()

    def filter(self, record):
        if isinstance(record.args, dict):
            record = self.redact(record)
        # elif isinstance(record.extra)
        return True
    
    def redact(self, msg):
        if type(msg) == dict:
            if self.KEY in msg:
                msg[self.KEY] = '***'
        elif isinstance(msg, Key):
            if self.KEY in msg._data:
                msg._data[self.KEY] = '***'
        elif type(msg) == str:
            reg = r'((?:[A-Z0-9?]{3,8}-){1,6}[A-Z0-9?]{3,8})(?P<end>[\s\,\"]?)'
            msg = re.sub(reg, r'***\g<end>', msg, flags=re.IGNORECASE)
        return msg

