# -*- encoding: UTF-8 -*-


from ..NumeralTypes import DWORD
from ..StringTypes import String


class LengthPrefixedString(String):
    def __init__(self, encoding):
        super().__init__(encoding = encoding)

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


class LengthPrefixedAnsiString(LengthPrefixedString):
    def __init__(self):
        super().__init__(encoding = "ascii")


class LengthPrefixedUnicodeString(LengthPrefixedString):
    def __init__(self):
        super().__init__(encoding = "utf-16-le")
