# -*- encoding: UTF-8 -*-


from neko.Common.Interfaces import IParseable
from ..NumeralTypes import BYTE, WORD, DWORD


class GUID(IParseable):
    def __init__(self):
        self.Data1 = DWORD()
        self.Data2 = WORD()
        self.Data3 = WORD()
        self.Data4 = [BYTE() for _ in range(8)]

    def __len__(self):
        return 16

    def __str__(self):
        return "{{{DATA1}-{DATA2}-{DATA3}-{DATA4_PART1}-{DATA4_PART2}}}".format(
            DATA1 = str(self.Data1)[2:],
            DATA2 = str(self.Data2)[2:],
            DATA3 = str(self.Data3)[2:],
            DATA4_PART1 = "".join(map(lambda x: str(x)[2:], self.Data4[0:2])),
            DATA4_PART2 = "".join(map(lambda x: str(x)[2:], self.Data4[2:8]))
        )

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.Data1.Parse(data[i:i + 4])
        i += len(self.Data1)
        self.Data2.Parse(data[i:i + 2])
        i += len(self.Data2)
        self.Data3.Parse(data[i:i + 2])
        i += len(self.Data3)

        for j in range(8):
            self.Data4[j].Parse(data[i:i + 1])
            i += len(self.Data4[j])

        return self
