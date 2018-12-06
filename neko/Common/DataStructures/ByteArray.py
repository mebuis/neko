# -*- encoding: UTF-8 -*-


import string

from neko.Common.Interfaces import IParseable
from neko.Common.Utilities import ToChunks


class ByteArray(IParseable):
    def __init__(self, preset_size = None):
        self.PresetSize = preset_size
        self.Data: bytes = b""

    @staticmethod
    def HexDump(data: bytes, characters_per_line = 16, max_characters = 128):
        if max_characters is not None:
            data = data[:max_characters]

        buffer = list()

        printable_characters = string.ascii_letters + string.digits + string.punctuation + " "

        lines = ToChunks(data, characters_per_line)
        for line in lines:
            left_pane = list()
            right_pane = list()

            for c in line:
                left_pane.append(hex(c)[2:].zfill(2).upper())

                if chr(c) in printable_characters:
                    right_pane.append(chr(c))
                else:
                    right_pane.append(".")

            buffer.append("{LEFT_PANE} | {RIGHT_PANE}".format(
                LEFT_PANE = " ".join(left_pane).ljust(3 * characters_per_line - 1),
                RIGHT_PANE = "".join(right_pane).ljust(characters_per_line)
            ))

        return "\n".join(buffer)

    def __len__(self):
        return len(self.Data)

    def __str__(self):
        return ByteArray.HexDump(self.Data)

    def Parse(self, data: bytes, **kwargs):
        if self.PresetSize is None:
            self.Data = data
        else:
            self.Data = data[:self.PresetSize]
            if len(data) < self.PresetSize:
                self.Data += bytes(self.PresetSize - len(data))

        return self
