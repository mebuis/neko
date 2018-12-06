# -*- encoding: UTF-8 -*-


from neko.Common.Interfaces import IParseable
from .Monikers import Moniker
from ..NumeralTypes import DWORD
from ..Windows.GUID import GUID


class MonikerStream(IParseable):
    def __init__(self):
        self.CLSID = GUID()
        self.Moniker = None

    def __len__(self):
        return len(self.CLSID) + len(self.Moniker)

    def __str__(self):
        return f"{self.CLSID} - {self.Moniker}"

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.CLSID.Parse(data[i:i + 16])
        i += len(self.CLSID)

        from .Monikers import NewMoniker, AntiMoniker, CompositeMoniker, FileMoniker, ItemMoniker, UrlMoniker, SOAPMoniker

        clsid = str(self.CLSID)
        if clsid == NewMoniker.CLSID:
            self.Moniker = NewMoniker()
        elif clsid == AntiMoniker.CLSID:
            self.Moniker = AntiMoniker()
        elif clsid == CompositeMoniker.CLSID:
            self.Moniker = CompositeMoniker()
        elif clsid == FileMoniker.CLSID:
            self.Moniker = FileMoniker()
        elif clsid == ItemMoniker.CLSID:
            self.Moniker = ItemMoniker()
        elif clsid == UrlMoniker.CLSID:
            self.Moniker = UrlMoniker()
        elif clsid == SOAPMoniker.CLSID:
            self.Moniker = SOAPMoniker()
        else:
            self.Moniker = Moniker()

        self.Moniker.Parse(data[i:])
        i += len(self.Moniker)

        return self


class LengthPrefixedMonikerStream(MonikerStream):
    def __init__(self):
        super().__init__()

        self.pLength = DWORD()

    @property
    def Length(self):
        return self.pLength.Value

    def __len__(self):
        return len(self.pLength) + (0 if (self.Length == 0) else (super().__len__()))

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.pLength.Parse(data[i:i + 4])
        i += len(self.pLength)

        if self.Length == 0:
            return self

        super().Parse(data[i:])
        if type(self.Moniker) is Moniker:  # the length depends on what the parser actually gets
            self.Moniker.Data = self.Moniker.Data[:self.Length - 4]
        i += super().__len__()

        return self
