# -*- encoding: UTF-8 -*-


import binascii
import json
import string
import traceback
import zipfile
import zlib
from io import BytesIO
from typing import List, Dict, Any

from neko.Common import Threat
from neko.Common.DataStructures.OLE1 import OLE1Package
from neko.Common.Utilities import MD5, SHA256
from neko.Common.Utilities.Logger import logger
from neko.Configuration import DEBUG
from neko.Parsers.CFBFParser import CFBFParser
from neko.Parsers.RTFParser import RTFParser
from neko.Scanners.CFBFScanner import CFBFScanner
from neko.Scanners.RTFScanner import RTFScanner


class Dispatcher:
    results: Dict[int or str, Dict[str, Any]] = None
    i: int = None
    checked_files: set = None

    def __init__(self, label, is_root_dispatcher = False):
        self.Data: bytes = None
        self.DataType: str = None

        self.Label = label
        self.IsRootDispatcher = is_root_dispatcher
        if self.IsRootDispatcher:
            Dispatcher.results = dict()
            Dispatcher.i = 1
            Dispatcher.checked_files = set()

        self.ThreatList: List[Threat] = list()
        self.ChildDispatchers: List[Dispatcher] = list()

    @staticmethod
    def DetectDataType(data: bytes):
        data_header = data[:10]

        if data_header.startswith(b"\x02\x00"):
            return "OLE1Package"

        if data_header.startswith(b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"):
            return "CFBF"
        if data_header.startswith(b"{\\rt"):
            return "RTF"
        if data_header.startswith(b"PK\x03\x04"):
            return "PKZip"

        if data_header.startswith(b"MZ"):
            return "PE"

        if data_header.startswith(b"JFIF"):
            return "JPEG"
        if data_header.startswith(b"\x89PNG"):
            return "PNG"
        if data_header.startswith(b"GIF"):
            return "GIF"

        if data_header.lower().startswith(b"<?xml"):
            return "XML"

        return "Unknown"

    def Dispatch(self, data: bytes):
        self.Data = data
        self.DataType = Dispatcher.DetectDataType(data)

        sha256 = SHA256(data)
        if sha256 not in Dispatcher.checked_files:
            Dispatcher.checked_files.add(sha256)
        else:
            return  # skip checked files

        if self.DataType in ["XML"]:  # currently unsupported, be quiet
            return

        logger.info(f"Dispatching \"{self.Label}\" (Type: {self.DataType}) ...")
        if self.DataType == "Unknown":
            logger.info(f"File Header: {binascii.hexlify(data[:10]).upper()}")

        try:
            if self.DataType == "OLE1Package":
                ole1package = OLE1Package().Parse(data)
                if ole1package.Data:  # extract package data
                    self.ThreatList.append(
                        Threat(
                            location = self.Label,
                            type = "FOUND_OLE1_PACKAGE",
                            information = {
                                "ansi_label": str(ole1package.LabelA).strip(string.whitespace + "\x00"),
                                "unicode_label": str(ole1package.LabelW).strip(string.whitespace + "\x00"),
                                "md5": MD5(ole1package.Data),
                                "sha256": SHA256(ole1package.Data),
                                "data": binascii.hexlify(ole1package.Data).decode("ascii")
                            }
                        )
                    )

                    dispatcher = Dispatcher(label = f"{self.Label} -> OLE1 Package Object")
                    dispatcher.Dispatch(ole1package.Data)  # dispatch package data
                    self.ChildDispatchers.append(dispatcher)

            elif self.DataType == "CFBF":
                parser = CFBFParser().Parse(data)
                if DEBUG:
                    parser.ShowDebugInformation()
                scanner = CFBFScanner()
                scanner.Scan(dispatcher = self, parser = parser)

            elif self.DataType == "RTF":
                parser = RTFParser().Parse(data)
                if DEBUG:
                    parser.ShowDebugInformation()
                scanner = RTFScanner()
                scanner.Scan(dispatcher = self, parser = parser)

            elif self.DataType == "PKZip":
                try:
                    zip_file = zipfile.ZipFile(BytesIO(data))
                except zipfile.BadZipFile:
                    logger.error("Archive file corrupted.")
                    raise

                for file_name in zip_file.namelist():  # extract and dispatch files
                    if file_name.endswith("/"):  # folders
                        continue
                    dispatcher = Dispatcher(label = f"{self.Label} -> {file_name}")
                    try:
                        file_content = zip_file.read(file_name)
                        dispatcher.Dispatch(file_content)
                        self.ChildDispatchers.append(dispatcher)
                    except (zipfile.BadZipFile, zlib.error):
                        logger.error(f"Failed to extract {file_name}. Please extract it manually.")
                        continue

            elif self.DataType == "PE":
                logger.warning(f"Found PE file at {self.Label}.")

        except Exception as e:
            logger.critical(f"Unexpected Error: {traceback.format_exc()}.")
            logger.critical(f"Failed to parse {self.Label}.")

    def GenerateJsonResult(self):
        for threat in self.ThreatList:
            Dispatcher.results[Dispatcher.i] = dict()
            Dispatcher.results[Dispatcher.i]["location"] = threat.Location
            Dispatcher.results[Dispatcher.i]["type"] = threat.Type
            Dispatcher.results[Dispatcher.i]["information"] = threat.Information
            Dispatcher.i += 1

        for child_dispatcher in self.ChildDispatchers:
            child_dispatcher.GenerateJsonResult()

        Dispatcher.results["count"] = Dispatcher.i - 1

        return json.dumps(Dispatcher.results, indent = 4)
