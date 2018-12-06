# -*- encoding: UTF-8 -*-


import logging
from typing import List, Dict

from neko.Common.Interfaces import IParseable, IDebuggable
from neko.Common.Utilities import ToChunks
from neko.Common.Utilities.Logger import logger
from .DataStructures import CFBFHeader, SectorEntry, DiFATSectorEntry, FATSectorEntry, MiniFATSectorEntry, DirectorySectorEntry, DiFATSector, FATSector, MiniFATSector, DirectorySector


class CFBFParser(IParseable, IDebuggable):
    def __init__(self):
        self.CFBFHeader = CFBFHeader()

        self.Sectors: List[bytes] = None
        self.MiniSectors: List[bytes] = None

        self.DiFATEntries: Dict[int, DiFATSectorEntry] = dict()
        self.FATEntries: Dict[int, FATSectorEntry] = dict()
        self.MiniFATEntries: Dict[int, MiniFATSectorEntry] = dict()
        self.DirectoryEntries: Dict[int, DirectorySectorEntry] = dict()

        self.ParserState: bool = None

    @property
    def SectorSize(self):
        return 2 ** self.CFBFHeader.SectorShift.Value

    @property
    def MiniSectorSize(self):
        return 2 ** self.CFBFHeader.MiniSectorShift.Value

    def ReadSectorData(self, sector_id, data_length, sector_size):
        buffer = [b"" for _ in range(data_length)]
        ii = 0

        if sector_size == self.MiniSectorSize:
            if self.MiniSectors is None:  # uninitialized
                _level = logger.level
                logger.setLevel(logging.CRITICAL)  # temporarily suppress the error messages during parsing the MiniFAT sectors
                self.MiniSectors = ToChunks(
                    self.ReadSectorData(
                        sector_id = self.DirectoryEntries[0].StartingSectorLocation.Value,
                        data_length = self.MiniSectorSize * len(self.MiniFATEntries.keys()),
                        sector_size = self.SectorSize
                    ),
                    self.MiniSectorSize
                )
                logger.setLevel(_level)
            data_source = self.MiniSectors
            data_relationship = self.MiniFATEntries
        else:
            data_source = self.Sectors
            data_relationship = self.FATEntries

        sector_type = "Mini Sector" if (data_source == self.MiniSectors) else ("Sector")

        length_to_read = data_length
        while length_to_read > 0:
            if sector_id >= len(data_source):  # sector id out of range
                logger.error(f"The {sector_type} #{sector_id} is not a valid data source.")
                break

            buffer[ii] = data_source[sector_id][:min(length_to_read, len(data_source[sector_id]))]
            ii += 1
            length_to_read -= len(data_source[sector_id])

            if sector_id in data_relationship:
                if data_relationship[sector_id].NextSector < len(data_source):
                    sector_id = data_relationship[sector_id].NextSector
                elif data_relationship[sector_id].NextSector == SectorEntry.END_OF_CHAIN:  # encountered a "END OF CHAIN" sector while reading data
                    if length_to_read > 0:  # increase the sector id by 1(temporarily ignore the linked list)
                        logger.warning("Encountered \"END OF CHAIN\" while reading data.")
                    sector_id += 1
                else:  # next sector id out of range
                    logger.error(f"The next sector of {sector_type} #{sector_id} is not a valid data source.")
                    break
            else:  # next sector not registered in the linkedlist(which usually indicates there's some overlay data)
                logger.error(f"The next sector of {sector_type} #{sector_id} wasn't registered.")
                break

        return b"".join(buffer)

    def ReadStreamData(self, directory: DirectorySectorEntry):
        if directory.StreamSize.Value >= self.CFBFHeader.MiniStreamCutoffSize.Value:  # stored in the FAT stream
            sector_size = self.SectorSize
        else:  # stored in the MiniFAT stream
            sector_size = self.MiniSectorSize

        return self.ReadSectorData(
            sector_id = directory.StartingSectorLocation.Value,
            data_length = directory.StreamSize.Value,
            sector_size = sector_size
        )

    def Parse(self, data: bytes, **kwargs):
        self.CFBFHeader.Parse(data[:512])

        self.Sectors = ToChunks(memoryview(data)[self.SectorSize:], self.SectorSize)

        # parse DiFAT sector entries
        entry_id = 0
        for chunk in ToChunks(self.CFBFHeader.DiFAT.Data, 4):  # DiFAT sector entries from the CFBF header
            self.DiFATEntries[entry_id] = DiFATSectorEntry().Parse(chunk)
            entry_id += 1

        sector_id = self.CFBFHeader.FirstDiFATSectorLocation.Value  # DiFAT sector entries from the DiFAT sectors
        while sector_id < len(self.Sectors):
            sector = DiFATSector().Parse(self.Sectors[sector_id])
            for entry in sector.Entries:
                self.DiFATEntries[entry_id] = entry
                entry_id += 1
            sector_id = sector.NextDiFATSectorLocation

        # parse FAT sector entries
        entry_id = 0
        for difat_entry in self.DiFATEntries.values():
            sector_id = difat_entry.FATSectorLocation
            if sector_id < len(self.Sectors):
                sector = FATSector().Parse(self.Sectors[sector_id])
                for entry in sector.Entries:
                    self.FATEntries[entry_id] = entry
                    entry_id += 1

        # parse MiniFAT sector entries
        entry_id = 0
        sector_id = self.CFBFHeader.FirstMiniFATSectorLocation.Value
        while sector_id < len(self.Sectors):
            sector = MiniFATSector().Parse(self.Sectors[sector_id])
            for entry in sector.Entries:
                self.MiniFATEntries[entry_id] = entry
                entry_id += 1
            sector_id = self.FATEntries[sector_id].NextSector

        # parse Directory sector entries
        entry_id = 0
        sector_id = self.CFBFHeader.FirstDirectorySectorLocation.Value
        while sector_id < len(self.Sectors):
            sector = DirectorySector().Parse(self.Sectors[sector_id])
            for entry in sector.Entries:  # read stream data for the directory sector entries
                if entry.ObjectType.Value == DirectorySectorEntry.STREAM_OBJECT:
                    if self.CFBFHeader.MajorVersion.Value == 0x0003:
                        entry.StreamSize.Value %= 0x80000000
                    if entry.StreamSize.Value > len(data):
                        logger.warning("The stream size specified is too large.")
                        entry.StreamData = b""
                    else:
                        entry.StreamData = self.ReadStreamData(entry)

                self.DirectoryEntries[entry_id] = entry
                entry.EntryID = entry_id
                entry_id += 1
            sector_id = self.FATEntries[sector_id].NextSector

        for entry in self.DirectoryEntries.values():  # find the child objects(using BFS) for the directory sector entries
            if entry.ObjectType.Value == DirectorySectorEntry.STREAM_OBJECT:
                continue

            child_entries = set()
            bfs_queue: List[DirectorySectorEntry] = list()

            if entry.ChildID.Value in self.DirectoryEntries:
                bfs_queue.append(self.DirectoryEntries[entry.ChildID.Value])

            while len(bfs_queue) > 0:
                left_sibling = self.DirectoryEntries.get(bfs_queue[0].LeftSiblingID.Value, None)
                right_sibling = self.DirectoryEntries.get(bfs_queue[0].RightSiblingID.Value, None)

                if (left_sibling) and (left_sibling not in child_entries):
                    bfs_queue.append(left_sibling)
                if (right_sibling) and (right_sibling not in child_entries):
                    bfs_queue.append(right_sibling)

                child_entries.add(bfs_queue[0].EntryID)
                bfs_queue.pop(0)

            entry.ChildList = sorted(list(child_entries))

        self.ParserState = True

        return self

    def ShowDebugInformation(self, **kwargs):
        logger.debug("---------- CFBF PARSER ----------")
        logger.debug(f"Parser State: {'Uninitialized' if (self.ParserState is None) else (str(self.ParserState))}")

        if self.ParserState:
            header = self.CFBFHeader
            logger.debug(f"Header Signature: {str(header.HeaderSignature)} (should be 0xD0CF11E0A1B11AE1)")
            logger.debug(f"Major Version: {str(header.MajorVersion)} (should be 0x0003 or 0x0004)")
            logger.debug(f"Minor Version: {str(header.MinorVersion)} (should be 0x003E)")
            logger.debug(f"Sector Shift: {str(header.SectorShift)} (should be 0x0009(v3) or 0x000C(v4))")
            logger.debug(f"Mini Sector Shift: {str(header.MiniSectorShift)} (should be 0x0006)")
            logger.debug(f"Root Entry CLSID: {str(self.DirectoryEntries[0].CLSID)}")

            directory_entries = self.DirectoryEntries
            logger.debug(f"Found {len(directory_entries)} directory entries.")

            for directory in directory_entries.values():  # type: DirectorySectorEntry
                object_type = {
                    DirectorySectorEntry.ROOT_STORAGE_OBJECT: "Root Storage Object",
                    DirectorySectorEntry.STORAGE_OBJECT: "Storage Object",
                    DirectorySectorEntry.STREAM_OBJECT: "Stream Object",
                    DirectorySectorEntry.UNKNOWN_OR_UNALLOCATED_OBJECT: "Unknown or Unallocated Object"
                }.get(directory.ObjectType.Value, "Invalid Object Type")
                logger.debug(
                    f"Directory Entry #{directory.EntryID}: \"{directory.ObjectName}\" ({object_type}"
                    + (f", 0x{hex(directory.StreamSize.Value)[2:].upper()} byte(s)" if (directory.ObjectType.Value == DirectorySectorEntry.STREAM_OBJECT) else "")
                    + ")"
                )

        return self.ParserState
