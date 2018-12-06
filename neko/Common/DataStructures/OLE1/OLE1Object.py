# -*- encoding: UTF-8 -*-


from neko.Common.Interfaces import IParseable
from .LengthPrefixedByteArray import LengthPrefixedByteArray
from .LengthPrefixedStringTypes import LengthPrefixedAnsiString
from ..ByteArray import ByteArray
from ..NumeralTypes import DWORD


class OLE1ObjectHeader(IParseable):
    def __init__(self):
        self.OLEVersion = DWORD()
        self.FormatID = DWORD()
        self.ClassName = LengthPrefixedAnsiString()
        self.TopicName = LengthPrefixedAnsiString()
        self.ItemName = LengthPrefixedAnsiString()

    def __len__(self):
        return len(self.OLEVersion) + len(self.FormatID) + len(self.ClassName) + len(self.TopicName) + len(self.ItemName)

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.OLEVersion.Parse(data[i:i + 4])
        i += len(self.OLEVersion)
        self.FormatID.Parse(data[i:i + 4])
        i += len(self.FormatID)
        self.ClassName.Parse(data[i:])
        i += len(self.ClassName)
        self.TopicName.Parse(data[i:])
        i += len(self.TopicName)
        self.ItemName.Parse(data[i:])
        i += len(self.ItemName)

        return self


class OLE1LinkedObject(IParseable):
    def __init__(self):
        self.NetworkName = LengthPrefixedAnsiString()
        self.Reserved = ByteArray(preset_size = 4)
        self.LinkUpdateOption = DWORD()

    def __len__(self):
        return len(self.NetworkName) + len(self.Reserved) + len(self.LinkUpdateOption)

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.NetworkName.Parse(data[i:])
        i += len(self.NetworkName)
        self.Reserved.Parse(data[i:i + 4])
        i += len(self.Reserved)
        self.LinkUpdateOption.Parse(data[i:i + 4])
        i += len(self.LinkUpdateOption)

        return self


class OLE1EmbeddedObject(IParseable):
    def __init__(self):
        self.NativeData = LengthPrefixedByteArray()

    def __len__(self):
        return len(self.NativeData)

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.NativeData.Parse(data[i:])
        i += len(self.NativeData)

        return self


class OLE1Object(IParseable):
    OLE1_NULL = 0x00000000
    OLE1_LINKED_OBJECT = 0x00000001
    OLE1_EMBEDDED_OBJECT = 0x00000002
    OLE1_PRESENTATION_OBJECT = 0x00000005

    def __init__(self):
        self.ObjectHeader = OLE1ObjectHeader()
        self.ObjectBody = None

    def __len__(self):
        return len(self.ObjectHeader) + (0 if (self.ObjectBody is None) else (len(self.ObjectBody)))

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.ObjectHeader.Parse(data[i:])
        i += len(self.ObjectHeader)

        if self.ObjectHeader.FormatID.Value == OLE1Object.OLE1_NULL:
            self.ObjectBody = None
        elif self.ObjectHeader.FormatID.Value == OLE1Object.OLE1_LINKED_OBJECT:
            self.ObjectBody = OLE1LinkedObject()
        elif self.ObjectHeader.FormatID.Value == OLE1Object.OLE1_EMBEDDED_OBJECT:
            self.ObjectBody = OLE1EmbeddedObject()
        else:
            self.ObjectBody = None

        if self.ObjectBody is not None:
            self.ObjectBody.Parse(data[i:])
            i += len(self.ObjectBody)

        return self
