# -*- encoding: UTF-8 -*-


import abc


class IParseable(metaclass = abc.ABCMeta):
    @abc.abstractmethod
    def Parse(self, data: bytes, **kwargs):
        raise NotImplementedError
