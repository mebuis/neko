# -*- encoding: UTF-8 -*-


from neko.Common.Interfaces import IParseable
from .CountOfCharactersPrefixedStringTypes import CountOfCharactersPrefixedUnicodeString
from .LengthPrefixedByteArray import LengthPrefixedByteArray
from .LengthPrefixedStringTypes import LengthPrefixedAnsiString
from ..NumeralTypes import WORD, DWORD
from ..StringTypes import NullTerminatedAnsiString


class OLE1Package(IParseable):
    OLE1_PACKAGE_LINKED_OBJECT = 0x00010000
    OLE1_PACKAGE_EMBEDDED_OBJECT = 0x00030000

    def __init__(self):
        self.Header = WORD()
        self.LabelA = NullTerminatedAnsiString()
        self.SourcePathA = NullTerminatedAnsiString()
        self.ObjectType = DWORD()
        self.DestinationPathA = LengthPrefixedAnsiString()
        self.pData = LengthPrefixedByteArray()
        self.DestinationPathW = CountOfCharactersPrefixedUnicodeString()
        self.LabelW = CountOfCharactersPrefixedUnicodeString()
        self.SourcePathW = CountOfCharactersPrefixedUnicodeString()

    @property
    def Data(self):
        return self.pData.Data

    def __len__(self):
        return len(self.Header) + len(self.LabelA) + len(self.SourcePathA) + len(self.ObjectType) + len(self.DestinationPathA) + len(self.pData) + len(self.DestinationPathW) + len(self.LabelW) + len(self.SourcePathW)

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.Header.Parse(data[i:i + 2])
        i += len(self.Header)
        self.LabelA.Parse(data[i:])
        i += len(self.LabelA)
        self.SourcePathA.Parse(data[i:])
        i += len(self.SourcePathA)
        self.ObjectType.Parse(data[i:i + 4])
        i += len(self.ObjectType)
        self.DestinationPathA.Parse(data[i:])
        i += len(self.DestinationPathA)
        self.pData.Parse(data[i:])
        i += len(self.pData)
        self.DestinationPathW.Parse(data[i:])
        i += len(self.DestinationPathW)
        self.LabelW.Parse(data[i:])
        i += len(self.LabelW)
        self.SourcePathW.Parse(data[i:])
        i += len(self.SourcePathW)

        return self
