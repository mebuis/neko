# -*- encoding: UTF-8 -*-


import abc


class IDebuggable(metaclass = abc.ABCMeta):
    @abc.abstractmethod
    def ShowDebugInformation(self, **kwargs):
        raise NotImplementedError
