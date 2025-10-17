import numpy as np
from .CommonData import DataHandler, DataRecord

__all__ = [ "ColorData" ]
__reload_hook__ = [".CommonData"]

class ColorDataHandler(DataHandler):
    def __init__(self):
        super().__init__("ColorData")#:, record_type=ColorDataRecord)

    def __getitem__(self, item):
        if isinstance(item, int):
            item = list(self.data['Palettes'].keys())[item]
            return super().__getitem__(('Palettes', item))
        elif isinstance(item, str) and item not in self.data:
            for k,v in self.data.items():
                if item in v:
                    return super().__getitem__((k, item))
            else:
                raise KeyError(f"couldn't find `ColorData` spec {item}")
        else:
            return super().__getitem__(item)

ColorData=ColorDataHandler()
ColorData.__doc__ = """An instance of `ColorDataHandler` that can be used for looking up data on color palettes"""
ColorData.__name__ = "ColorData"