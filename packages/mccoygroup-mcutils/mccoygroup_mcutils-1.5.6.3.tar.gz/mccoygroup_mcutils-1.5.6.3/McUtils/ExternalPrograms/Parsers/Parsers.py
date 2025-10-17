
import importlib
from ...Parsers import FileStreamReader, FileStreamCheckPoint, FileStreamReaderException

__all__ = [
    "ElectronicStructureLogReader"
]

class ElectronicStructureLogReader(FileStreamReader):
    """
    Implements a stream based reader for a generic electronic structure .log file.
    This is inherits from the `FileStreamReader` base, and takes a two pronged approach to getting data.
    First, a block is found in a log file based on a pair of tags.
    Next, a function (usually based on a `StringParser`) is applied to this data to convert it into a usable data format.
    The goal is to move toward wrapping all returned data in a `QuantityArray` so as to include data type information, too.
    """

    components_name = None
    components_package = ".LogComponents"
    _comps = None
    @classmethod
    def load_components(cls):
        if cls._comps is None:
            pkg_root = cls.components_package
            if pkg_root.startswith('.'):
                pkg_root = cls.__module__.rsplit('.', 1)[0] + cls.components_package
            cls._comps = importlib.import_module(pkg_root + '.' + cls.components_name)
        return cls._comps
    @property
    def registered_components(self):
        return self.load_components().__components__
    @property
    def default_keys(self):
        return self.load_components().__defaults__
    @property
    def default_ordering(self):
        return self.load_components().__ordering__

    def parse(self, keys, num=None, reset=False):
        """The main function we'll actually use. Parses bits out of a .log file.

        :param keys: the keys we'd like to read from the log file
        :type keys: str or list(str)
        :param num: for keys with multiple entries, the number of entries to pull
        :type num: int or None
        :return: the data pulled from the log file, strung together as a `dict` and keyed by the _keys_
        :rtype: dict
        """
        # if keys is None:
        #     keys = self.get_default_keys()
        # important for ensuring correctness of what we pull
        if isinstance(keys, str):
            keys = (keys,)
        keys = sorted(keys,
                      key = lambda k: (
                          -1 if (self.registered_components[k]["mode"] == "List") else (
                              self.default_ordering[k] if k in self.default_ordering else 0
                          )
                      )
                      )

        res = {}
        if reset:
            with FileStreamCheckPoint(self):
                for k in keys:
                    comp = self.registered_components[k]
                    res[k] = self.parse_key_block(**comp, num=num)
        else:
            for k in keys:
                comp = self.registered_components[k]
                try:
                    res[k] = self.parse_key_block(**comp, num=num)
                except:
                    raise FileStreamReaderException("failed to parse block for key '{}'".format(k))
        return res

    # job_default_keys = {
    #     "opt":{
    #         "p": ("StandardCartesianCoordinates", "OptimizedScanEnergies", "OptimizedDipoleMoments"),
    #         "_": ("StandardCartesianCoordinates", "OptimizedScanEnergies")
    #     },
    #     "popt": {
    #         "p": ("StandardCartesianCoordinates", "OptimizedScanEnergies", "OptimizedDipoleMoments"),
    #         "_": ("StandardCartesianCoordinates", "OptimizedScanEnergies")
    #     },
    #     "scan": ("StandardCartesianCoordinates", "ScanEnergies")
    # }
    # def get_default_keys(self):
    #     """
    #     Tries to get the default keys one might be expected to want depending on the type of job as determined from the Header
    #     Currently only supports 'opt', 'scan', and 'popt' as job types.
    #
    #     :return: key listing
    #     :rtype: tuple(str)
    #     """
    #     header = self.parse("Header", reset=True)["Header"]
    #
    #     header_low = {k.lower() for k in header.job}
    #     for k in self.job_default_keys:
    #         if k in header_low:
    #             sub = self.job_default_keys[k]
    #             if isinstance(sub, dict):
    #                 for k in sub:
    #                     if k in header_low:
    #                         defs = sub[k]
    #                         break
    #                 else:
    #                     defs = sub["_"]
    #             else:
    #                 defs = sub
    #             break
    #     else:
    #         raise FileStreamReaderException("unclear what default keys should be used if not a scan and not a popt")
    #
    #     return ("Header", ) + tuple(defs) + ("Footer",)

    @classmethod
    def read_props(cls, file, keys):
        with cls(file) as reader:
            parse = reader.parse(keys)
        if isinstance(keys, str):
            parse = parse[keys]
        return parse