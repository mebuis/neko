# -*- encoding: UTF-8 -*-


class Group:
    def __init__(self):
        self.OpenPosition: int = None
        self.ClosePosition: int = None

        self.DataOwner: str = None
        self.HexDataOwner: str = None
        self.UC: int = 1
        self.SkipRemainingData: bool = False

        self.IsProcessed: bool = False

    def __lt__(self, other):
        if isinstance(other, Group):
            return self.OpenPosition < other.OpenPosition

        raise TypeError

    def __len__(self):
        if (self.OpenPosition is None) or (self.ClosePosition is None):
            return 0

        return self.ClosePosition - self.OpenPosition + 1

    def __str__(self):
        return f"Group [{self.OpenPosition}, {self.ClosePosition}] (Length = {len(self)})"

    def Open(self, i):
        self.OpenPosition = i
        return self

    def Close(self, i):
        self.ClosePosition = i
        return self

