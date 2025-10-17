
import numpy as np
from collections import namedtuple
from .Parsers import ElectronicStructureLogReader
from ...Parsers import FileStreamReader, Number, RegexPattern, Integer, Word

__all__ = [
    "OrcaLogReader",
    "OrcaHessReader"
]


class OrcaLogReader(ElectronicStructureLogReader):
    components_name = "OrcaLogComponents"


class OrcaHessReader(FileStreamReader):

    def __init__(self, file, **kwargs):
        super().__init__(file, **kwargs)
        self._num_atoms = None

    ENumber = RegexPattern((Number, "E", Integer), "ENumber", dtype=float)
    matrix_types = {
        'normal_modes':ENumber,
    }
    array_types = {
        'vibrational_frequencies': Number,
        'dipole_derivatives': ENumber,
        'ir_spectrum': Number
    }
    @classmethod
    def get_special_handlers(cls):
        return {
            'atoms': cls.parse_atoms
            # 'ir_spectrum':cls.parse_ir
        }
    @classmethod
    def handle_orca_block(cls, tag, data:str):
        special_handler = cls.get_special_handlers().get(tag)
        if special_handler is not None:
            return special_handler(data)

        matrix_dtype = cls.matrix_types.get(tag)
        if matrix_dtype is not None:
            return cls.parse_matrix(data, data_pattern=matrix_dtype)

        array_type = cls.array_types.get(tag)
        if array_type is not None:
            return cls.parse_array(data, data_pattern=array_type)

        num_lines = data.count("\n")
        if num_lines == 1:
            return float(data.strip())

        header, rem = data.split("\n", 1)
        try:
            num_data = float(header)
        except TypeError:
            return data

        if num_data == num_lines - 1:
            return cls.parse_array(rem)
        else:
            return cls.parse_matrix(data)

    @classmethod
    def parse_matrix(cls, data, col_blocks=5, data_pattern=None):
        header, rem = data.split("\n", 1)
        header = header.split()
        if len(header) == 1:
            nrows = ncols = header[0]
        else:
            nrows, ncols = header
        del header

        nrows = int(nrows)
        ncols = int(ncols)
        if data_pattern is None:
            data_pattern = cls.ENumber
        nums = np.array(data_pattern.findall(data)).astype(float)
        if len(nums) != (nrows * ncols):
            raise ValueError(f"mismatch between number of elements {len(nums)} and matrix size ({nrows}x{ncols})")
        block_size = nrows * col_blocks
        nblocks = ncols // col_blocks
        arr = np.empty((nrows, ncols))
        for i in range(nblocks):
            start = block_size*i
            end = block_size*(i+1)
            col_offset = col_blocks * i
            arr[:, col_offset:col_offset + col_blocks] = nums[start:end].reshape(nrows, col_blocks)
        if ncols % col_blocks != 0:
            start = block_size*nblocks
            col_offset = ncols % col_blocks
            arr[:, -col_offset:] = nums[start:].reshape(nrows, col_offset)

        return arr

    @classmethod
    def parse_array(cls, data, data_pattern=None):
        header, rem = data.split("\n", 1)
        header = int(header.split()[0])
        if data_pattern is None:
            data_pattern = cls.ENumber
        nums = np.array(data_pattern.findall(data)).astype(float)
        res = nums.reshape(header, -1)
        if res.shape[1] == 1:
            res = res.flatten()
        return res

    OrcaCoords = namedtuple("OrcaCoords", ["atoms", "mass", "coords"])
    @classmethod
    def parse_atoms(cls, data):
        base_data = cls.parse_array(data, Number)
        atoms = Word.findall(data)
        return cls.OrcaCoords(
            atoms,
            base_data[:, 0],
            base_data[:, 1:]
        )

    def get_next_block(self):
        block = self.get_tagged_block("$", "\n\n")
        if block is None: return None
        tag, rem = block.split("\n", 1)
        return tag, rem

    def parse(self, tags=None, excludes=None):
        res = {}
        block = self.get_next_block()
        while block is not None:
            tag, data = block
            match = True
            if excludes is not None:
                match = tag not in tags
            if tags is not None:
                match = tag in tags
            if match:
                res[tag] = self.handle_orca_block(tag, data)
            block = self.get_next_block()

        return res

