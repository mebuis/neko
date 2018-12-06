# -*- encoding: UTF-8 -*-


import string

from neko.Common import Threat
from neko.Common.CLSID import CLSID_NULL, LOW_RISK_LEVEL_OBJECTS, HIGH_RISK_LEVEL_OBJECTS
from neko.Common.DataStructures.OLE1 import LengthPrefixedByteArray
from neko.Common.DataStructures.OLE2 import OLEStream, SOAPMoniker, CompositeMoniker, FileMoniker, UrlMoniker
from neko.Parsers.CFBFParser import CFBFParser
from neko.Parsers.CFBFParser.DataStructures import DirectorySectorEntry


class CFBFScanner:
    def __init__(self):
        from neko import Dispatcher
        self.Dispatcher: Dispatcher = None
        self.Parser: CFBFParser = None

        self.Flags = set()

    def Scan(self, **kwargs):
        self.Dispatcher = kwargs["dispatcher"]
        self.Parser = kwargs["parser"]

        self.CheckDirectoryEntries()
        self.CheckOLEStreams()

        return self

    def CheckDirectoryEntries(self):
        self.CheckDirectoryEntryNames()
        self.CheckDirectoryEntryCLSIDs()

    def CheckOLEStreams(self):
        for entry in self.Parser.DirectoryEntries.values():
            entry_name = entry.ObjectName.lower()
            if entry_name != "\\x01ole":
                continue

            olestream = OLEStream().Parse(entry.StreamData)

            relative_moniker_stream = olestream.RelativeMonikerStream
            absolute_moniker_stream = olestream.AbsoluteMonikerStream
            if str(relative_moniker_stream.CLSID) != CLSID_NULL:
                outer_moniker_stream = relative_moniker_stream
            elif str(absolute_moniker_stream.CLSID) != CLSID_NULL:
                outer_moniker_stream = absolute_moniker_stream
            else:
                continue

            outer_moniker = outer_moniker_stream.Moniker

            if isinstance(outer_moniker, SOAPMoniker):
                self.Dispatcher.ThreatList.append(
                    Threat(
                        location = self.Dispatcher.Label,
                        type = "FOUND_SOAP_MONIKER",
                        information = {
                            "url": str(outer_moniker.Url).strip(string.whitespace + "\x00")[5:]  # wsdl=
                        }
                    )
                )

            elif isinstance(outer_moniker, CompositeMoniker):
                for inner_moniker_stream in outer_moniker.MonikerArray:
                    inner_moniker = inner_moniker_stream.Moniker
                    if isinstance(inner_moniker, FileMoniker):
                        self.Dispatcher.ThreatList.append(
                            Threat(
                                location = self.Dispatcher.Label,
                                type = "FOUND_COMPOSITED_FILE_MONIKER",
                                information = {
                                    "ansi_path": str(inner_moniker.AnsiPath).strip(string.whitespace + "\x00"),
                                    "unicode_path": str(inner_moniker.UnicodePath).strip(string.whitespace + "\x00")
                                }
                            )
                        )
                    elif isinstance(inner_moniker, UrlMoniker):
                        self.Dispatcher.ThreatList.append(
                            Threat(
                                location = self.Dispatcher.Label,
                                type = "FOUND_COMPOSITED_URL_MONIKER",
                                information = {
                                    "url": str(inner_moniker.Url).strip(string.whitespace + "\x00")
                                }
                            )
                        )

            elif isinstance(outer_moniker, FileMoniker):
                self.Dispatcher.ThreatList.append(
                    Threat(
                        location = self.Dispatcher.Label,
                        type = "FOUND_FILE_MONIKER",
                        information = {
                            "ansi_path": str(outer_moniker.AnsiPath).strip(string.whitespace + "\x00"),
                            "unicode_path": str(outer_moniker.UnicodePath).strip(string.whitespace + "\x00")
                        }
                    )
                )

            elif isinstance(outer_moniker, UrlMoniker):
                self.Dispatcher.ThreatList.append(
                    Threat(
                        location = self.Dispatcher.Label,
                        type = "FOUND_URL_MONIKER",
                        information = {
                            "url": str(outer_moniker.Url).strip(string.whitespace + "\x00")
                        }
                    )
                )

    def CheckDirectoryEntryNames(self):
        for entry in self.Parser.DirectoryEntries.values():
            entry_name = entry.ObjectName.lower()  # stream names are case-insensitive

            if ("MACRO" not in self.Flags) and (entry_name in frozenset(["_vba_project", "dir", "_srp_0", "projectlk", "projectwm", "project"])):
                self.Dispatcher.ThreatList.append(
                    Threat(
                        location = self.Dispatcher.Label,
                        type = "FOUND_MACRO",
                        information = {}
                    )
                )
                self.Flags.add("MACRO")

            if ("OCX" not in self.Flags) and (entry_name in frozenset(["\\x03ocxname"])):
                self.Dispatcher.ThreatList.append(
                    Threat(
                        location = self.Dispatcher.Label,
                        type = "FOUND_OLE_CONTROL_EXTENSION",
                        information = {}
                    )
                )
                self.Flags.add("OCX")

            if ("ENCRYPTED_PACKAGE" not in self.Flags) and (entry_name in frozenset(["encryptedpackage"])):
                self.Dispatcher.ThreatList.append(
                    Threat(
                        location = self.Dispatcher.Label,
                        type = "FOUND_ENCRYPTED_PACKAGE",
                        information = {}
                    )
                )
                self.Flags.add("ENCRYPTED_PACKAGE")

    def CheckDirectoryEntryCLSIDs(self):
        for entry in self.Parser.DirectoryEntries.values():
            if entry.ObjectType.Value == DirectorySectorEntry.STREAM_OBJECT:
                continue

            clsid = str(entry.CLSID)
            if clsid == CLSID_NULL:
                continue  # unknown handler

            elif clsid in LOW_RISK_LEVEL_OBJECTS:
                if clsid not in self.Flags:
                    self.Dispatcher.ThreatList.append(
                        Threat(
                            location = self.Dispatcher.Label,
                            type = "FOUND_LOW_RISK_LEVEL_OBJECT",
                            information = {
                                "type": LOW_RISK_LEVEL_OBJECTS[clsid],
                                "clsid": clsid
                            }
                        )
                    )
                    self.Flags.add(clsid)

            elif clsid in HIGH_RISK_LEVEL_OBJECTS:
                if clsid not in self.Flags:
                    self.Dispatcher.ThreatList.append(
                        Threat(
                            location = self.Dispatcher.Label,
                            type = "FOUND_HIGH_RISK_LEVEL_OBJECT",
                            information = {
                                "type": HIGH_RISK_LEVEL_OBJECTS[clsid],
                                "clsid": clsid
                            }
                        )
                    )
                    self.Flags.add(clsid)

                    if HIGH_RISK_LEVEL_OBJECTS[clsid] == "OLE Package Object":
                        for child_entry_id in entry.ChildList:
                            child_entry = self.Parser.DirectoryEntries[child_entry_id]

                            if child_entry.ObjectName.lower() == "\\x01ole10native":
                                package_data = LengthPrefixedByteArray().Parse(child_entry.StreamData).Data
                            elif child_entry.StreamData:
                                package_data = child_entry.StreamData
                            else:
                                package_data = None

                            if package_data and package_data.startswith(b"\x02\x00"):
                                from neko import Dispatcher
                                dispatcher = Dispatcher(label = f"{self.Dispatcher.Label} -> Directory Entry #{entry.EntryID}")
                                dispatcher.Dispatch(package_data)
                                self.Dispatcher.ChildDispatchers.append(dispatcher)

            else:
                if clsid not in self.Flags:
                    self.Dispatcher.ThreatList.append(
                        Threat(
                            location = self.Dispatcher.Label,
                            type = "FOUND_UNKNOWN_OBJECT",
                            information = {
                                "clsid": clsid
                            }
                        )
                    )
                    self.Flags.add(clsid)
