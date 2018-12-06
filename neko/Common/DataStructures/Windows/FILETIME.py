# -*- encoding: UTF-8 -*-


import datetime

from neko.Common.Interfaces import IParseable
from ..NumeralTypes import QWORD


class FILETIME(IParseable):
    def __init__(self):
        self.pDateTime = QWORD()

    @property
    def DateTime(self):
        return self.pDateTime.Value

    @property
    def HighDateTime(self):
        return self.DateTime // (2 ** 32)

    @property
    def LowDateTime(self):
        return self.DateTime % (2 ** 32)

    def __len__(self):
        return 8

    def __str__(self):
        try:
            time = datetime.datetime(year = 1601, month = 1, day = 1)
            time += datetime.timedelta(seconds = self.DateTime // 10000000)
            return time.isoformat(sep = " ")
        except OverflowError:
            return "FILETIME Overflowed"

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.pDateTime.Parse(data[i:i + 8])
        i += len(self.pDateTime)

        return self
