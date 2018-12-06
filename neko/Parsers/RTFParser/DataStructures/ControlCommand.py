# -*- encoding: UTF-8 -*-


import string

from neko.Common.Interfaces import IParseable
from neko.Common.Utilities.Logger import logger
from ..Database import KNOWN_CONTROL_COMMANDS, SPECIAL_DATA_CONSUMERS


class ControlCommand(IParseable):
    def __init__(self):
        self.Command: str = ""
        self.Parameter: str = ""

        self.Type: str = "Unknown"

        self.IsDataConsumer: bool = False
        self.Data: bytes = None
        self.DataLength: int = 0

    def __len__(self):
        return 1 + len(self.Command) + len(self.Parameter) + self.DataLength

    def __str__(self):
        return f"\\{self.Command}{self.Parameter}"

    @staticmethod
    def ToInt32(parameter):
        if (parameter == "") or (parameter == "-"):
            return 0

        has_minus_sign = False
        i = 0

        if parameter[i] == "-":  # only one leading minus sign is allowed
            has_minus_sign = True
            i += 1

        from ctypes import c_int32 as Int32
        n = Int32(0)

        while i < len(parameter):
            n = Int32(n.value * 10 + int(parameter[i]))
            i += 1

        if has_minus_sign:
            n = Int32(-1 * n.value).value
        else:
            n = n.value

        return (0 if (n <= 0) else (n))

    def Parse(self, data: bytes, **kwargs):
        skip_remaining_data = kwargs.get("skip_remaining_data", False)

        assert data and (chr(data[0]) == "\\")

        i = 1
        data_length = len(data)

        if (i < data_length) and (chr(data[i]) not in string.ascii_letters):
            self.Command = chr(data[i])
            if self.Command in ["\n", "\r", "'", "*", "-", ":", "\\", "_", "{", "|", "}", "~"]:  # from "wwlib.dll" of Microsoft Office 2010, may change in the future versions
                self.Type = "Symbol"
            else:  # other symbols will be considered as "Unknown" type
                self.Type = "Unknown"

            i += 1

            if (self.Command == "'") and (not skip_remaining_data):  # if "skip_remaining_data" is specified(as True), this control word does not require parameters
                assert i + 2 < data_length

                parameter = data[i:i + 2]
                if chr(parameter[0]) not in string.hexdigits:
                    self.Parameter = "5F"
                elif chr(parameter[1]) not in string.hexdigits:
                    self.Parameter = chr(parameter[0]) + "0"
                else:
                    self.Parameter = chr(parameter[0]) + chr(parameter[1])

            return self

        buffer_size = 0xFF - 1  # the control word and the parameter are both null-terminated strings, and they share a buffer of 0xFF(255) bytes
        buffer = [""] * buffer_size
        ii = 0

        while i < data_length:
            if ii >= buffer_size:  # buffer overflow case 1: control word too long
                break

            if chr(data[i]) not in string.ascii_letters:
                break

            buffer[ii] = chr(data[i])
            i += 1
            ii += 1

        self.Command = "".join(buffer)
        self.Type = KNOWN_CONTROL_COMMANDS.get(self.Command, "Unknown")
        self.IsDataConsumer = SPECIAL_DATA_CONSUMERS.get(self.Command, self.Type.startswith("Destination"))  # assume that only "Destination" control words consume data

        buffer_size = 0xFF - 1 - len(self.Command) - 1
        buffer = [""] * buffer_size
        ii = 0

        if (i < data_length) and (chr(data[i]) == "-") and (ii < buffer_size):
            buffer[ii] = chr(data[i])
            i += 1
            ii += 1

        while i < data_length:
            if ii >= buffer_size:  # buffer overflow case 2: parameter too long
                break

            if chr(data[i]) not in string.digits:
                break

            buffer[ii] = chr(data[i])
            i += 1
            ii += 1

        self.Parameter = "".join(buffer)

        # control command hook
        if self.Command == "fldinst":
            logger.warning("Found \"\\fldinst\" control word in the document.")

        return self
