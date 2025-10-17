
import numpy as np
from collections import namedtuple
from .Parsers import ElectronicStructureLogReader
from ...Parsers import FileStreamReader, Number, RegexPattern, Integer, Word

__all__ = [
    "MOLPROLogReader"
]


class MOLPROLogReader(ElectronicStructureLogReader):
    components_name = "MOLPROLogComponents"