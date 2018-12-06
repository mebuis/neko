# -*- encoding: UTF-8 -*-


import struct

from neko.Common.Interfaces import IParseable


class UInt(IParseable):
    LITTLE_ENDIAN = "<"
    BIG_ENDIAN = ">"
    UINT_TYPE_CODE = {1: "B", 2: "H", 4: "I", 8: "Q"}

    def __init__(self, size, endianness):
        self.Size = size
        self.Endianness = endianness

        self.pValue = 0

    @property
    def SizeInBytes(self):
        return self.Size

    @property
    def SizeInBits(self):
        return self.SizeInBytes * 8

    @property
    def Value(self):
        return self.pValue

    @Value.setter
    def Value(self, value):
        self.pValue = value % (2 ** self.SizeInBits)

    def __len__(self):
        return self.SizeInBytes

    def __str__(self):
        return f"0x{hex(self.Value)[2:].zfill(self.SizeInBytes * 2).upper()}"

    def Parse(self, data: bytes, **kwargs):
        try:
            self.Value = struct.unpack(self.Endianness + UInt.UINT_TYPE_CODE[self.SizeInBytes], data[:self.SizeInBytes])[0]
        except struct.error:
            self.Value = 0

        return self


class UInt8(UInt):
    def __init__(self, endianness = UInt.LITTLE_ENDIAN):
        super().__init__(size = 1, endianness = endianness)


class UInt16(UInt):
    def __init__(self, endianness = UInt.LITTLE_ENDIAN):
        super().__init__(size = 2, endianness = endianness)


class UInt32(UInt):
    def __init__(self, endianness = UInt.LITTLE_ENDIAN):
        super().__init__(size = 4, endianness = endianness)


class UInt64(UInt):
    def __init__(self, endianness = UInt.LITTLE_ENDIAN):
        super().__init__(size = 8, endianness = endianness)


BYTE = UInt8
WORD = UInt16
DWORD = UInt32
QWORD = UInt64
