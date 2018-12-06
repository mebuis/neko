# -*- encoding: UTF-8 -*-


from ..NumeralTypes import DWORD
from ..StringTypes import String


class CountOfCharactersPrefixedString(String):
    def __init__(self, encoding):
        super().__init__(encoding = encoding)

        self.pCountOfCharacters = DWORD()

    @property
    def CountOfCharacters(self):
        return self.pCountOfCharacters.Value

    def __len__(self):
        return len(self.pCountOfCharacters) + super().__len__()

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.pCountOfCharacters.Parse(data[i:i + 4])
        i += len(self.pCountOfCharacters)

        super().Parse(data[i:i + self.CountOfCharacters * self.CharacterWidth])
        i += super().__len__()

        return self


class CountOfCharactersPrefixedAnsiString(CountOfCharactersPrefixedString):
    def __init__(self):
        super().__init__(encoding = "ascii")


class CountOfCharactersPrefixedUnicodeString(CountOfCharactersPrefixedString):
    def __init__(self):
        super().__init__(encoding = "utf-16-le")
