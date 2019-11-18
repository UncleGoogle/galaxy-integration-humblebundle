import logging
import copy
import re

from model.game import Key


class SensitiveFilter(logging.Filter):
    KEY = 'redeemed_key_val'
    SECRET = '***'

    def filter(self, record):
        record.msg = self.redact(record.msg)
        if hasattr(record, self.KEY):
            record.redeemed_key_val = self.redact(record.redeemed_key_val)
        if hasattr(record, 'game'):
            record.game = self.redact(record.game)
        if isinstance(record.args, dict):
            for k in record.args.keys():
                record.args[k] = self.redact(record.args[k])
        else:
            record.args = tuple(self.redact(arg) for arg in record.args)
        return True

    def redact(self, msg):
        if type(msg) == dict:
            if self.KEY in msg:
                msg[self.KEY] = self.SECRET
        elif isinstance(msg, Key):
            if self.KEY in msg._data:
                data_copy = copy.deepcopy(msg._data)
                msg = Key(data_copy)  # key clone to not edit original data
                msg._data[self.KEY] = self.SECRET
        elif type(msg) == str:
            reg = r'((?:[A-Z0-9?]{3,8}-){2,6}[A-Z0-9?]{3,8})(?P<end>[\s\,\"]?)'
            msg = re.sub(reg, rf'{self.SECRET}\g<end>', msg, flags=re.IGNORECASE)
        return msg

