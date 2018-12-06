# -*- encoding: UTF-8 -*-


import binascii

from neko.Common import Threat
from neko.Common.DataStructures.OLE1 import OLE1Object
from neko.Common.Utilities.Logger import logger
from neko.Parsers.RTFParser import RTFParser


class RTFScanner:
    def __init__(self):
        from neko import Dispatcher
        self.Dispatcher: Dispatcher = None
        self.Parser: RTFParser = None

        self.Flags = set()  # reserved for future use

    def Scan(self, **kwargs):
        self.Dispatcher = kwargs["dispatcher"]
        self.Parser = kwargs["parser"]

        self.CheckOverlay()
        self.CheckOLEObjects()

        return self

    def CheckOverlay(self):
        if self.Parser.Overlay:
            self.Dispatcher.ThreatList.append(
                Threat(
                    location = self.Dispatcher.Label,
                    type = "FOUND_RTF_OVERLAY_DATA",
                    information = {
                        "data": binascii.hexlify(self.Parser.Overlay).decode("ascii")
                    }
                )
            )

    def CheckOLEObjects(self):
        if len(self.Parser.Objects) == 0:
            return

        linked_object_count = 0
        embedded_object_count = 0

        for _object in self.Parser.Objects:
            ole1object = OLE1Object()
            ole1object.Parse(_object.Data)

            format_id = ole1object.ObjectHeader.FormatID.Value
            if format_id == OLE1Object.OLE1_NULL or format_id == OLE1Object.OLE1_PRESENTATION_OBJECT:
                continue
            elif ole1object.ObjectHeader.FormatID.Value == OLE1Object.OLE1_LINKED_OBJECT:
                linked_object_count += 1
            elif ole1object.ObjectHeader.FormatID.Value == OLE1Object.OLE1_EMBEDDED_OBJECT:
                embedded_object_count += 1
                from neko import Dispatcher
                dispatcher = Dispatcher(label = f"{self.Dispatcher.Label} -> Embedded Object #{embedded_object_count}")
                dispatcher.Dispatch(ole1object.ObjectBody.NativeData.Data)
                self.Dispatcher.ChildDispatchers.append(dispatcher)

                self.Dispatcher.ThreatList.append(
                    Threat(
                        location = self.Dispatcher.Label,
                        type = "FOUND_OLE1_EMBEDDED_OBJECT",
                        information = {
                            "data": binascii.hexlify(ole1object.ObjectBody.NativeData.Data).decode("ascii")
                        }
                    )
                )
            else:
                logger.warning(f"Unexpected OLE1 object type detected: {format_id}.")

        if linked_object_count > 0:
            self.Dispatcher.ThreatList.append(
                Threat(
                    location = self.Dispatcher.Label,
                    type = "FOUND_OLE1_LINKED_OBJECTS",
                    information = {
                        "count": linked_object_count
                    }
                )
            )

        if embedded_object_count > 0:
            self.Dispatcher.ThreatList.append(
                Threat(
                    location = self.Dispatcher.Label,
                    type = "FOUND_OLE1_EMBEDDED_OBJECTS",
                    information = {
                        "count": embedded_object_count
                    }
                )
            )
