# -*- encoding: UTF-8 -*-


class Object:
    def __init__(self):
        self.GroupOpenPosition: int = None
        self.GroupClosePosition: int = None

        self.ProgID: str = None
        self.Data: bytes = None

    def __len__(self):
        if self.Data is None:
            return 0

        return len(self.Data)
