# -*- encoding: UTF-8 -*-


from neko.Common.Interfaces import IParseable
from ..ByteArray import ByteArray
from ..NumeralTypes import WORD, DWORD
from ..OLE1.LengthPrefixedByteArray import LengthPrefixedByteArray
from ..OLE1.LengthPrefixedStringTypes import LengthPrefixedAnsiString
from ..StringTypes import UnicodeString, NullTerminatedUnicodeString
from ..Windows.GUID import GUID


class Moniker(IParseable):
    CLSID = "{00000000-0000-0000-0000-000000000000}"

    def __init__(self, name = None):
        self.Name = name or "Unknown"
        self.Data = ByteArray()

    def __len__(self):
        return len(self.Data)

    def __str__(self):
        return f"{self.Name} Moniker"

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.Data.Parse(data[i:])
        i += len(self.Data)

        return self


class NewMoniker(Moniker):
    CLSID = "{ECABAFC6-7F19-11D2-978E-0000F8757E2A}"

    def __init__(self):
        super().__init__(name = "New")


class AntiMoniker(Moniker):
    CLSID = "{00000305-0000-0000-C000-000000000046}"

    def __init__(self):
        super().__init__(name = "Anti")

        self.Count = DWORD()

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.Count.Parse(data[i:i + 4])
        i += len(self.Count)

        self.Data.Parse(data[:i])

        return self


class CompositeMoniker(Moniker):
    CLSID = "{00000309-0000-0000-C000-000000000046}"

    def __init__(self):
        super().__init__(name = "Composite")

        self.CMonikers = DWORD()
        self.MonikerArray = list()

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.CMonikers.Parse(data[i:i + 4])
        i += len(self.CMonikers)

        for _ in range(self.CMonikers.Value):
            if i > len(data):
                break

            from .MonikerStream import MonikerStream
            moniker_stream = MonikerStream().Parse(data[i:])
            i += len(moniker_stream)

            self.MonikerArray.append(moniker_stream)

        self.Data.Parse(data[:i])

        return self


class FileMoniker(Moniker):
    CLSID = "{00000303-0000-0000-C000-000000000046}"

    def __init__(self):
        super().__init__(name = "File")

        self.CAnti = WORD()
        self.AnsiPath = LengthPrefixedAnsiString()
        self.EndServer = WORD()
        self.Version = WORD()
        self.Reserved1 = ByteArray(preset_size = 16)
        self.Reserved2 = ByteArray(preset_size = 4)
        self.UnicodePathSize = DWORD()
        self.UnicodePathBytes = DWORD()
        self.KeyValue = WORD()
        self.UnicodePath = UnicodeString()

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.CAnti.Parse(data[i:i + 2])
        i += len(self.CAnti)
        self.AnsiPath.Parse(data[i:])
        i += len(self.AnsiPath)
        self.EndServer.Parse(data[i:i + 2])
        i += len(self.EndServer)
        self.Version.Parse(data[i:i + 2])
        i += len(self.Version)
        self.Reserved1.Parse(data[i:i + 16])
        i += len(self.Reserved1)
        self.Reserved2.Parse(data[i:i + 4])
        i += len(self.Reserved2)
        self.UnicodePathSize.Parse(data[i:i + 4])
        i += len(self.UnicodePathSize)

        if self.UnicodePathSize.Value > 0:
            self.UnicodePathBytes.Parse(data[i:i + 4])
            i += len(self.UnicodePathBytes)
            self.KeyValue.Parse(data[i:i + 2])
            i += len(self.KeyValue)
            self.UnicodePath.Parse(data[i:i + self.UnicodePathBytes.Value])
            i += len(self.UnicodePath)

        self.Data.Parse(data[:i])

        return self


class ItemMoniker(Moniker):
    CLSID = "{00000304-0000-0000-C000-000000000046}"

    def __init__(self):
        super().__init__(name = "Item")

        self.Delimiter = LengthPrefixedByteArray()
        self.Item = LengthPrefixedByteArray()

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.Delimiter.Parse(data[i:])
        i += len(self.Delimiter)
        self.Item.Parse(data[i:])
        i += len(self.Item)

        self.Data.Parse(data[:i])

        return self


class UrlMoniker(Moniker):
    CLSID = "{79EAC9E0-BAF9-11CE-8C82-00AA004BA90B}"

    def __init__(self):
        super().__init__(name = "Url")

        self.Length = DWORD()
        self.Url = NullTerminatedUnicodeString()
        self.SerialGUID = GUID()
        self.SerialVersion = DWORD()
        self.UriFlags = DWORD()

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.Length.Parse(data[i:i + 4])
        i += len(self.Length)
        self.Url.Parse(data[i:])
        i += len(self.Url)

        if len(self.Url) < self.Length.Value:
            self.SerialGUID.Parse(data[i:i + 16])
            i += len(self.SerialGUID)
            self.SerialVersion.Parse(data[i:i + 4])
            i += len(self.SerialVersion)
            self.UriFlags.Parse(data[i:i + 4])
            i += len(self.UriFlags)

        self.Data.Parse(data[:i])

        return self


class SOAPMoniker(Moniker):
    CLSID = "{ECABB0C7-7F19-11D2-978E-0000F8757E2A}"

    def __init__(self):
        super().__init__(name = "SOAP")

        self.Reserved = ByteArray(preset_size = 4)
        self.Url = LengthPrefixedByteArray()

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.Reserved.Parse(data[i:i + 4])
        i += len(self.Reserved)
        self.Url.Parse(data[i:])
        i += len(self.Url)

        self.Data.Parse(data[:i])

        return self
