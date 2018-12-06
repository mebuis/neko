# -*- encoding: UTF-8 -*-


import binascii
import copy
import re
from typing import List, Dict

from neko.Common.Interfaces import IDebuggable, IParseable
from neko.Common.Utilities.Logger import logger
from .DataStructures import ControlCommand, Group, Object
from .Database import HEX_DATA_CONSUMERS


class RTFParser(IParseable, IDebuggable):
    def __init__(self):
        self.Text: bytes = b""
        self.Overlay: bytes = b""

        self.ControlCommands: Dict[int, ControlCommand] = dict()
        self.Groups: Dict[int, Group] = dict()

        self.ObjectGroups: List[Group] = list()
        self.Objects: List[Object] = list()

        self.ParserState = None

    def MakeCache(self, data: bytes):
        data_length = len(data)

        i = 0
        depth = 0
        skip_remaining_data_if_next_control_word_is_unknown_type = False
        stack: List[Group] = list()

        BRACES_AND_BACKSLASHES = re.compile(rb"[\\{}]")

        while i < data_length:
            match = BRACES_AND_BACKSLASHES.search(memoryview(data)[i:])
            if match is None:
                break
            i += match.span()[0]

            try:
                if chr(data[i]) == "\\":  # parsing control commands
                    control_command = ControlCommand().Parse(data[i:i + 0xFF], skip_remaining_data = stack[-1].SkipRemainingData)
                    self.ControlCommands[i] = control_command
                    i += len(control_command)

                    if control_command.Command == "*":
                        skip_remaining_data_if_next_control_word_is_unknown_type = True
                    elif control_command.IsDataConsumer:
                        stack[-1].DataOwner = control_command.Command
                        if control_command.Command in HEX_DATA_CONSUMERS:
                            stack[-1].HexDataOwner = control_command.Command
                        else:
                            stack[-1].HexDataOwner = None
                    elif (control_command.Type == "Unknown") and (skip_remaining_data_if_next_control_word_is_unknown_type):
                        stack[-1].SkipRemainingData = True
                    elif control_command.Command == "bin":
                        binary_data_length = ControlCommand.ToInt32(control_command.Parameter)
                        if binary_data_length > 0:
                            if chr(data[i]) == " ":  # only one leading space character is allowed
                                control_command.DataLength += 1
                                i += 1

                            assert i + binary_data_length < data_length

                            control_command.Data = data[i:i + binary_data_length]
                            control_command.DataLength += binary_data_length
                            i += binary_data_length
                    elif control_command.Command == "uc":
                        try:
                            uc = int(control_command.Parameter)
                            if 0 < uc < 31682:  # the value 31682 is based on testing, may change in the future versions
                                stack[-1].UC = uc
                            else:
                                stack[-1].UC = 0
                        except ValueError:
                            stack[-1].UC = 0
                    elif (control_command.Command == "u") and (not stack[-1].SkipRemainingData) and (stack[-1].HexDataOwner is None):
                        uc = stack[-1].UC
                        if (uc > 0) and (control_command.Data is None):
                            control_command.Data = b""
                        while uc > 0:
                            if chr(data[i]) != "\\":
                                control_command.Data += chr(data[i]).encode("ascii")
                                control_command.DataLength += 1
                                i += 1
                            else:  # control commands will be treated as one character
                                _control_command = ControlCommand().Parse(data[i:i + 0xFF])
                                control_command.Data += str(_control_command).encode("ascii")
                                control_command.DataLength += len(_control_command)
                                i += len(_control_command)

                            uc -= 1

                    if control_command.Command != "*":
                        skip_remaining_data_if_next_control_word_is_unknown_type = False

                    if control_command.Command == "object":
                        self.ObjectGroups.append(stack[-1])

                elif chr(data[i]) == "{":  # group opens
                    depth += 1
                    group = Group().Open(i)
                    if len(stack) > 0:  # inherit the properties
                        group.UC = stack[-1].UC
                        group.DataOwner = stack[-1].DataOwner
                        group.HexDataOwner = stack[-1].HexDataOwner
                    stack.append(group)
                    i += 1

                elif chr(data[i]) == "}":  # group closes
                    depth -= 1
                    stack[-1].Close(i)
                    group = stack.pop()
                    self.Groups[group.OpenPosition] = group
                    self.Groups[group.ClosePosition] = group
                    i += 1

                    if depth == 0:
                        self.Text = data[:i]
                        self.Overlay = data[i:].strip()  # strip CRLFs
                        break

            except IndexError:
                break

        for group in self.Groups.values():  # reset the states(these states should not be cached)
            group.DataOwner = None
            group.HexDataOwner = None
            group.UC = 1
            group.SkipRemainingData = False
            group.IsProcessed = False

    def DumpObjects(self, data: bytes):
        self.MakeCache(data)
        data = self.Text

        BRACES_AND_BACKSLASHES = re.compile(rb"[\\{}]")

        for group in sorted(self.ObjectGroups):
            if group.IsProcessed:
                continue

            if len(group) == 0:  # incomplete groups
                continue

            current_object = Object()
            current_object.GroupOpenPosition = group.OpenPosition
            current_object.GroupClosePosition = group.ClosePosition

            stack: List[Group] = list()
            skip_remaining_data_if_next_control_word_is_unknown_type = False

            buffer_size = len(group)
            buffer = list(b"" for _ in range(buffer_size))
            ii = 0

            head = tail = group.OpenPosition
            while head < group.ClosePosition:
                match = BRACES_AND_BACKSLASHES.search(memoryview(data)[head:group.ClosePosition + 1])
                if match is None:
                    break
                head += match.span()[0]

                try:
                    if len(stack) > 0:
                        parsing_objdata = (stack[-1].DataOwner == stack[-1].HexDataOwner == "objdata")
                        parsing_objclass = (stack[-1].DataOwner == "objclass")
                    else:
                        parsing_objdata = False
                        parsing_objclass = False

                    if parsing_objdata:
                        buffer[ii] = re.sub(rb"[^a-fA-F0-9]", b"", data[tail:head])
                        ii += 1

                    if parsing_objclass:
                        if current_object.ProgID is None:
                            current_object.ProgID = b""

                        current_object.ProgID += re.sub(rb"\s", b"", data[tail:head])

                    if chr(data[head]) == "\\":
                        control_command = self.ControlCommands[head]

                        if control_command.Command == "*":
                            skip_remaining_data_if_next_control_word_is_unknown_type = True

                        if parsing_objdata:
                            if (control_command.Command == "bin") and (control_command.DataLength > 0):
                                parsed_objdata = b"".join(buffer)

                                buffer = list(b"" for _ in range(buffer_size))
                                ii = 0
                                buffer[ii] = parsed_objdata[:len(parsed_objdata) // 2 * 2]
                                ii += 1
                                buffer[ii] = binascii.hexlify(control_command.Data)
                                ii += 1

                                if len(parsed_objdata) % 2 == 1:  # one nibble waiting to be completed
                                    buffer[ii] = parsed_objdata[-1:]
                                    ii += 1
                            elif control_command.Command == "'":
                                parsed_objdata = b"".join(buffer)

                                buffer = list(b"" for _ in range(buffer_size))
                                ii = 0
                                buffer[ii] = parsed_objdata[:len(parsed_objdata) // 2 * 2]  # discard the nibble due to buffer re-use
                                ii += 1

                        if parsing_objclass:
                            if (control_command.Command == "'") and (control_command.Parameter):
                                current_object.ProgID += binascii.unhexlify(control_command.Parameter.encode("ascii"))

                        if control_command.IsDataConsumer:
                            stack[-1].DataOwner = control_command.Command
                            if control_command.Command in HEX_DATA_CONSUMERS:
                                stack[-1].HexDataOwner = control_command.Command
                            else:
                                stack[-1].HexDataOwner = None

                        if control_command.Command in HEX_DATA_CONSUMERS:
                            if control_command.Command != "objdata":
                                parsed_objdata = b"".join(buffer)
                                if len(parsed_objdata) >= 2:
                                    current_object.Data = binascii.unhexlify(parsed_objdata[:len(parsed_objdata) // 2 * 2])
                                    self.Objects.append(copy.deepcopy(current_object))  # make a copy of parsed object data

                            buffer = list(b"" for _ in range(buffer_size))  # the hex buffer pointer is replaced, so just discard the former buffer
                            ii = 0

                        if (control_command.Type == "Unknown") and (skip_remaining_data_if_next_control_word_is_unknown_type):
                            tail = head = stack[-1].ClosePosition
                            skip_remaining_data_if_next_control_word_is_unknown_type = False
                            continue

                        if control_command.Command != "*":
                            skip_remaining_data_if_next_control_word_is_unknown_type = False

                        head += len(control_command)

                    elif chr(data[head]) == "{":
                        if len(stack) > 0:  # inherit the properties
                            self.Groups[head].DataOwner = stack[-1].DataOwner
                            self.Groups[head].HexDataOwner = stack[-1].HexDataOwner
                        stack.append(self.Groups[head])
                        head += 1

                    elif chr(data[head]) == "}":
                        stack[-1].IsProcessed = True
                        stack.pop()
                        head += 1

                    tail = head

                except IndexError:
                    break

            parsed_objdata = b"".join(buffer)
            if len(parsed_objdata) >= 2:
                current_object.Data = binascii.unhexlify(parsed_objdata[:len(parsed_objdata) // 2 * 2])
                self.Objects.append(copy.deepcopy(current_object))

        self.ParserState = True

        return self

    def Parse(self, data: bytes, **kwargs):
        try:
            self.DumpObjects(data)
        except AssertionError as e:
            self.ParserState = False
            logger.critical(e)

        return self

    def ShowDebugInformation(self, **kwargs):
        logger.debug("---------- RTF PARSER ----------")
        logger.debug(f"Parser State: {'Uninitialized' if (self.ParserState is None) else (str(self.ParserState))}")

        if self.ParserState:
            logger.debug(f"Found {len(self.ObjectGroups)} groups containing \"\\object\".")
            logger.debug(f"Successfully parsed {len(self.Objects)} objects.")

            for i, _object in enumerate(self.Objects):
                progid = "None" if (_object.ProgID is None) else (_object.ProgID.decode("ascii"))
                logger.debug(f"Object #{i + 1}: From Group [{_object.GroupOpenPosition}, {_object.GroupClosePosition}] ({len(_object.Data)} bytes), ProgID = {progid}")

        return self.ParserState
