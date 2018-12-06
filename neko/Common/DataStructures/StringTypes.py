# -*- encoding: UTF-8 -*-


from neko.Common.Interfaces import IParseable


class String(IParseable):
    CHARACTER_WIDTH = {"ascii": 1, "utf-16-le": 2}

    def __init__(self, encoding):
        self.Encoding = encoding

        self.pData = b""

    @property
    def CharacterWidth(self):
        return String.CHARACTER_WIDTH[self.Encoding]

    @property
    def Data(self) -> bytes or memoryview:
        return self.pData

    @Data.setter
    def Data(self, value):
        self.pData = value[:len(value) // self.CharacterWidth * self.CharacterWidth]

    def __len__(self):
        return len(self.Data)

    def __str__(self):
        return self.Data.decode(self.Encoding)

    def Parse(self, data: bytes, **kwargs):
        self.Data = data

        return self


class NullTerminatedString(String):
    def Parse(self, data: bytes, **kwargs):
        is_null_terminated = False
        for i in range(len(data) // self.CharacterWidth):
            character = data[i * self.CharacterWidth:(i + 1) * self.CharacterWidth]
            self.Data += character

            if character == bytes(self.CharacterWidth):
                is_null_terminated = True
                break

        if not is_null_terminated:
            self.Data += bytes(self.CharacterWidth)

        return self


class AnsiString(String):
    def __init__(self):
        super().__init__(encoding = "ascii")


class UnicodeString(String):
    def __init__(self):
        super().__init__(encoding = "utf-16-le")


class NullTerminatedAnsiString(NullTerminatedString):
    def __init__(self):
        super().__init__(encoding = "ascii")


class NullTerminatedUnicodeString(NullTerminatedString):
    def __init__(self):
        super().__init__(encoding = "utf-16-le")
