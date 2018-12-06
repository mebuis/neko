# -*- encoding: UTF-8 -*-


import string
from typing import List

from neko.Common.DataStructures import BYTE, WORD, DWORD, QWORD, UnicodeString
from neko.Common.DataStructures.Windows import FILETIME, GUID
from neko.Common.Interfaces import IParseable
from neko.Common.Utilities import ToChunks


class SectorEntry(IParseable):
    MAX_SECTOR_ID = 0xFFFFFFFA
    NOT_APPLICABLE = 0xFFFFFFFB
    DIFAT_SECTOR = 0xFFFFFFFC
    FAT_SECTOR = 0xFFFFFFFD
    END_OF_CHAIN = 0xFFFFFFFE
    FREE_SECTOR = 0xFFFFFFFF

    def __init__(self):
        self.EntryData = DWORD()

    def __len__(self):
        return 4

    def __str__(self):
        sector_id = self.EntryData.Value

        if sector_id == SectorEntry.MAX_SECTOR_ID:
            return "Max Sector ID"
        elif sector_id == SectorEntry.NOT_APPLICABLE:
            return "N/A"
        elif sector_id == SectorEntry.DIFAT_SECTOR:
            return "DiFAT Sector"
        elif sector_id == SectorEntry.FAT_SECTOR:
            return "FAT Sector"
        elif sector_id == SectorEntry.END_OF_CHAIN:
            return "End Of Chain"
        elif sector_id == SectorEntry.FREE_SECTOR:
            return "Free Sector"
        else:
            return f"Sector #{sector_id}"

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.EntryData.Parse(data[i:i + 4])
        i += len(self.EntryData)

        return self


class Sector(IParseable):
    def __init__(self, entry_type, entry_size):
        self.EntryType = entry_type
        self.EntrySize = entry_size
        self.Entries = list()

    def __len__(self):
        return len(self.Entries) * self.EntrySize

    def Parse(self, data: bytes, **kwargs):
        for chunk in ToChunks(data, self.EntrySize):
            self.Entries.append(self.EntryType().Parse(chunk))

        return self


class DiFATSectorEntry(SectorEntry):
    @property
    def FATSectorLocation(self):
        return self.EntryData.Value


class FATSectorEntry(SectorEntry):
    @property
    def NextSector(self):
        return self.EntryData.Value


class MiniFATSectorEntry(SectorEntry):
    @property
    def NextSector(self):
        return self.EntryData.Value


class DirectorySectorEntry(SectorEntry):
    MAX_STREAM_ID = 0xFFFFFFFA
    NO_STREAM = 0xFFFFFFFF

    UNKNOWN_OR_UNALLOCATED_OBJECT = 0x00
    STORAGE_OBJECT = 0x01
    STREAM_OBJECT = 0x02
    ROOT_STORAGE_OBJECT = 0x05

    def __init__(self):
        super().__init__()  # pSectorData is not used

        self.DirectoryEntryName = UnicodeString()
        self.DirectoryEntryNameLength = WORD()
        self.ObjectType = BYTE()
        self.ColorFlag = BYTE()
        self.LeftSiblingID = DWORD()
        self.RightSiblingID = DWORD()
        self.ChildID = DWORD()
        self.CLSID = GUID()
        self.StateBits = DWORD()
        self.CreationTime = FILETIME()
        self.ModifiedTime = FILETIME()
        self.StartingSectorLocation = DWORD()
        self.StreamSize = QWORD()

        self.EntryID: int = None
        self.StreamData: bytes = None
        self.ChildList: List[int] = list()

    @property
    def ObjectName(self) -> str:
        name = UnicodeString()
        name.Parse(self.DirectoryEntryName.Data[:self.DirectoryEntryNameLength.Value].tobytes())  # "memoryview", not "bytes"

        name = str(name).strip(string.whitespace + "\x00")
        name = "".join(
            map(
                lambda x: x if (x in (string.ascii_letters + string.digits + " _")) else (f"\\x{hex(ord(x))[2:].zfill(2).upper()}"),
                name
            )
        )

        return name

    def __len__(self):
        return 128

    def __str__(self):
        return self.ObjectName

    def Parse(self, data: bytes, **kwargs):
        i = 0

        self.DirectoryEntryName.Parse(data[i:i + 64])
        i += len(self.DirectoryEntryName)
        self.DirectoryEntryNameLength.Parse(data[i:i + 2])
        i += len(self.DirectoryEntryNameLength)
        self.ObjectType.Parse(data[i:i + 1])
        i += len(self.ObjectType)
        self.ColorFlag.Parse(data[i:i + 1])
        i += len(self.ColorFlag)
        self.LeftSiblingID.Parse(data[i:i + 4])
        i += len(self.LeftSiblingID)
        self.RightSiblingID.Parse(data[i:i + 4])
        i += len(self.RightSiblingID)
        self.ChildID.Parse(data[i:i + 4])
        i += len(self.ChildID)
        self.CLSID.Parse(data[i:i + 16])
        i += len(self.CLSID)
        self.StateBits.Parse(data[i:i + 4])
        i += len(self.StateBits)
        self.CreationTime.Parse(data[i:i + 8])
        i += len(self.CreationTime)
        self.ModifiedTime.Parse(data[i:i + 8])
        i += len(self.ModifiedTime)
        self.StartingSectorLocation.Parse(data[i:i + 4])
        i += len(self.StartingSectorLocation)
        self.StreamSize.Parse(data[i:i + 8])
        i += len(self.StreamSize)

        return self


class DiFATSector(Sector):
    def __init__(self):
        super().__init__(entry_type = DiFATSectorEntry, entry_size = 4)

        self.pNextDiFATSectorLocation = DWORD()

    @property
    def NextDiFATSectorLocation(self):
        return self.pNextDiFATSectorLocation.Value

    def Parse(self, data: bytes, **kwargs):
        chunks = ToChunks(data, chunk_size = self.EntrySize)

        self.pNextDiFATSectorLocation.Parse(chunks[-1])
        for chunk in chunks[:-1]:
            self.Entries.append(self.EntryType().Parse(chunk))

        return self


class FATSector(Sector):
    def __init__(self):
        super().__init__(entry_type = FATSectorEntry, entry_size = 4)


class MiniFATSector(Sector):
    def __init__(self):
        super().__init__(entry_type = MiniFATSectorEntry, entry_size = 4)


class DirectorySector(Sector):
    def __init__(self):
        super().__init__(entry_type = DirectorySectorEntry, entry_size = 128)
