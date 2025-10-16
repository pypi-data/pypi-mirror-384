import enum

import rdflib

from .error import TypeException
from .semantics import Namespaces


class Datatype(enum.Enum):
    BOOLEAN = 0
    INTEGER = 1
    FLOAT = 2
    STRING = 3
    TIME = 4
    ENUM = 5

    @classmethod
    def from_string(cls, datatype: str):
        if datatype in ["bool", "boolean"]:
            return cls.BOOLEAN
        if datatype in ["int", "integer"]:
            return cls.INTEGER
        if datatype in ["float", "double"]:
            return cls.FLOAT
        if datatype in ["string"]:
            return cls.STRING
        if datatype in ["time"]:
            return cls.TIME
        if datatype in ["enum"]:
            return cls.ENUM
        raise TypeException("Unknown type descriptor: {}".format(datatype))

    def to_string(self, legacy_mode: bool = False) -> str:
        if legacy_mode:
            return ["bool", "int", "double", "string", "time", "enum"][self.value]
        return ["boolean", "int", "float", "string", "time", "enum"][self.value]

    def to_semantic(self):
        return [rdflib.XSD.boolean, rdflib.XSD.integer, rdflib.XSD.float, rdflib.XSD.string, rdflib.XSD.dateTime, rdflib.XSD.string][self.value]