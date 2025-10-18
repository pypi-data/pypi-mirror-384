import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IqlResult:
    name: str
    query: str

    def arrow(self):
        raise NotImplementedError("Not Implemented")

    def df(self):
        raise NotImplementedError("Not Implemented")

    def native(self):
        """Returns whatever the internal representation"""
        raise NotImplementedError("Not Implemented")


@dataclass
class IqlResultData(IqlResult):
    name: str
    query: str
    _data: object

    def native(self):
        """Returns whatever the internal representation"""
        return self._data

    def arrow(self):
        raise NotImplementedError("Not Implemented")

    def df(self):
        raise NotImplementedError("Not Implemented")
