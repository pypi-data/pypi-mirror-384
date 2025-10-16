
from enum import IntEnum


class CADError(IntEnum):
    __errors__ = {}

    @property
    def message(self):
        return self.__errors__[self]

    def __str__(self):
        return self.message
