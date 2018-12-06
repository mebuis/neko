# -*- encoding: UTF-8 -*-


from neko.Common.DataStructures import UInt, WORD, DWORD, QWORD, ByteArray
from neko.Common.DataStructures.Windows import GUID
from neko.Common.Interfaces import IParseable


class CFBFHeader(IParseable):
    def __init__(self):
        self.HeaderSignature = QWORD(UInt.BIG_ENDIAN)
        self.HeaderCLSID = GUID()
        self.MinorVersion = WORD()
        self.MajorVersion = WORD()
        self.ByteOrder = WORD()
        self.SectorShift = WORD()
        self.MiniSectorShift = WORD()
        self.Reserved1 = ByteArray(preset_size = 2)
        self.Reserved2 = ByteArray(preset_size = 4)
        self.NumberOfDirectorySectors = DWORD()
        self.NumberOfFATSectors = DWORD()
        self.FirstDirectorySectorLocation = DWORD()
        self.TransactionSignatureNumber = DWORD()
        self.MiniStreamCutoffSize = DWORD()
        self.FirstMiniFATSectorLocation = DWORD()
        self.NumberOfMiniFATSectors = DWORD()
        self.FirstDiFATSectorLocation = DWORD()
        self.NumberOfDiFATSectors = DWORD()
        self.DiFAT = ByteArray(preset_size = 436)

    def __len__(self):
        return 2 ** self.SectorShift.Value

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.HeaderSignature.Parse(data[i:i + 8])
        i += len(self.HeaderSignature)
        self.HeaderCLSID.Parse(data[i:i + 16])
        i += len(self.HeaderCLSID)
        self.MinorVersion.Parse(data[i:i + 2])
        i += len(self.MinorVersion)
        self.MajorVersion.Parse(data[i:i + 2])
        i += len(self.MajorVersion)
        self.ByteOrder.Parse(data[i:i + 2])
        i += len(self.ByteOrder)
        self.SectorShift.Parse(data[i:i + 2])
        i += len(self.SectorShift)
        self.MiniSectorShift.Parse(data[i:i + 2])
        i += len(self.MiniSectorShift)
        self.Reserved1.Parse(data[i:i + 2])
        i += len(self.Reserved1)
        self.Reserved2.Parse(data[i:i + 4])
        i += len(self.Reserved2)
        self.NumberOfDirectorySectors.Parse(data[i:i + 4])
        i += len(self.NumberOfDirectorySectors)
        self.NumberOfFATSectors.Parse(data[i:i + 4])
        i += len(self.NumberOfFATSectors)
        self.FirstDirectorySectorLocation.Parse(data[i:i + 4])
        i += len(self.FirstDirectorySectorLocation)
        self.TransactionSignatureNumber.Parse(data[i:i + 4])
        i += len(self.TransactionSignatureNumber)
        self.MiniStreamCutoffSize.Parse(data[i:i + 4])
        i += len(self.MiniStreamCutoffSize)
        self.FirstMiniFATSectorLocation.Parse(data[i:i + 4])
        i += len(self.FirstMiniFATSectorLocation)
        self.NumberOfMiniFATSectors.Parse(data[i:i + 4])
        i += len(self.NumberOfMiniFATSectors)
        self.FirstDiFATSectorLocation.Parse(data[i:i + 4])
        i += len(self.FirstDiFATSectorLocation)
        self.NumberOfDiFATSectors.Parse(data[i:i + 4])
        i += len(self.NumberOfDiFATSectors)
        self.DiFAT.Parse(data[i:i + 436])
        i += len(self.DiFAT)

        return self
