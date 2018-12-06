# -*- encoding: UTF-8 -*-


from neko.Common.Interfaces import IParseable
from .MonikerStream import LengthPrefixedMonikerStream
from ..ByteArray import ByteArray
from ..NumeralTypes import DWORD
from ..OLE1.LengthPrefixedStringTypes import LengthPrefixedUnicodeString
from ..Windows.FILETIME import FILETIME
from ..Windows.GUID import GUID


class OLEStream(IParseable):
    def __init__(self):
        self.Version = DWORD()
        self.Flags = DWORD()
        self.LinkUpdateOption = DWORD()
        self.Reserved1 = ByteArray(preset_size = 4)
        self.ReservedMonikerStream = LengthPrefixedMonikerStream()
        self.RelativeMonikerStream = LengthPrefixedMonikerStream()
        self.AbsoluteMonikerStream = LengthPrefixedMonikerStream()
        self.CLSIDIndicator = DWORD()
        self.CLSID = GUID()
        self.ReservedDisplayName = LengthPrefixedUnicodeString()
        self.Reserved2 = ByteArray(preset_size = 4)
        self.LocalUpdateTime = FILETIME()
        self.LocalCheckUpdateTime = FILETIME()
        self.RemoteUpdateTime = FILETIME()

    def __len__(self):
        return len(self.Version) + len(self.Flags) + len(self.LinkUpdateOption) + len(self.Reserved1) + len(self.ReservedMonikerStream) + len(self.RelativeMonikerStream) + len(self.AbsoluteMonikerStream) + len(self.CLSIDIndicator) + len(self.CLSID) + len(self.ReservedDisplayName) + len(self.Reserved2) + len(self.LocalUpdateTime) + len(self.LocalCheckUpdateTime) + len(self.RemoteUpdateTime)

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.Version.Parse(data[i:i + 4])
        i += len(self.Version)
        self.Flags.Parse(data[i:i + 4])
        i += len(self.Flags)
        self.LinkUpdateOption.Parse(data[i:i + 4])
        i += len(self.LinkUpdateOption)
        self.Reserved1.Parse(data[i:i + 4])
        i += len(self.Reserved1)
        self.ReservedMonikerStream.Parse(data[i:])
        i += len(self.ReservedMonikerStream)
        self.RelativeMonikerStream.Parse(data[i:])
        i += len(self.RelativeMonikerStream)
        self.AbsoluteMonikerStream.Parse(data[i:])
        i += len(self.AbsoluteMonikerStream)
        self.CLSIDIndicator.Parse(data[i:i + 4])
        i += len(self.CLSIDIndicator)
        self.CLSID.Parse(data[i:i + 16])
        i += len(self.CLSID)
        self.ReservedDisplayName.Parse(data[i:])
        i += len(self.ReservedDisplayName)
        self.Reserved2.Parse(data[i:i + 4])
        i += len(self.Reserved2)
        self.LocalUpdateTime.Parse(data[i:i + 8])
        i += len(self.LocalUpdateTime)
        self.LocalCheckUpdateTime.Parse(data[i:i + 8])
        i += len(self.LocalCheckUpdateTime)
        self.RemoteUpdateTime.Parse(data[i:i + 8])
        i += len(self.RemoteUpdateTime)

        return self
