# -*- encoding: UTF-8 -*-


from neko.Common.Utilities.Logger import logger


class Threat:
    def __init__(self, location, type, information):
        self.Location: str = location
        self.Type: str = type
        self.Information: str = information

        logger.error(f"Threat \"{self.Type}\" detected at \"{self.Location}\".")
