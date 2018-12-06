# -*- encoding: UTF-8 -*-


from ..ByteArray import ByteArray
from ..NumeralTypes import DWORD


class LengthPrefixedByteArray(ByteArray):
    def __init__(self):
        super().__init__()

        self.pLength = DWORD()

    @property
    def Length(self):
        return self.pLength.Value

    def __len__(self):
        return len(self.pLength) + super().__len__()

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.pLength.Parse(data[i:i + 4])
        i += len(self.pLength)

        super().Parse(data[i:i + self.Length])
        i += super().__len__()

        return self
