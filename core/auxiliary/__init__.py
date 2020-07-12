# -*- coding: utf-8 -*-

import hashlib
from time import time
from datetime import datetime
import json


def md5(s):
    return hashlib.md5(str(s).encode()).hexdigest()


def jsonDecode(data):
    try:
        return json.loads(data)
    except Exception:
        return None

class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()
