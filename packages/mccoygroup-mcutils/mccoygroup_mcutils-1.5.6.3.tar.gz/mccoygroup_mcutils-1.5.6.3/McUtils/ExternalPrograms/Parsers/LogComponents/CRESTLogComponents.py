"""
This lists the types of readers and things available to the GaussianLogReader
"""
import io

import numpy as np

from ....Parsers import *
from collections import namedtuple, OrderedDict

########################################################################################################################
#
#                                           OrcaLogComponents
#
# region OrcaLogComponents
Components = OrderedDict()  # we'll register on this bit by bit
# each registration should look like:

# Components["Name"] = {
#     "description" : string, # used for docmenting what we have
#     "tag_start"   : start_tag, # starting delimeter for a block
#     "tag_end"     : end_tag, # ending delimiter for a block None means apply the parser upon tag_start
#     "parser"      : parser, # function that'll parse the returned list of blocks (for "List") or block (for "Single")
#     "mode"        : mode # "List" or "Single"
# }

########################################################################################################################
#
#                                           CartesianCoordinates
#
input_start_tag = FileStreamerTag(
    """ Command line input:""",
)
input_end_tag = "----------------"
def parse_command_line(inp_str):
    return inp_str

Components["CommandLine"] = {
    "tag_start": input_start_tag,
    "tag_end"  : input_end_tag,
    "parser"   : parse_command_line,
    "mode"     : "Single"
}

calc_start_tag = FileStreamerTag(
    """Calculation info""",
    follow_ups=("----------------",)
)
calc_end_tag = "----------------"
def parse_command_line(inp_str):
    return inp_str

Components["CalculationInfo"] = {
    "tag_start": calc_start_tag,
    "tag_end"  : calc_end_tag,
    "parser"   : parse_command_line,
    "mode"     : "Single"
}

# region CartesianCoordinates

 # the region thing is just a PyCharm hack to collapse the boilerplate here... Could also have done 5000 files

cartesian_start_tag = FileStreamerTag(
    """Input structure:"""
)
cartesian_end_tag = "\n\n"

CRESTCoords = namedtuple("CRESTCoords", ["atoms", "coords"])
def cartesian_coordinates_parser(cart):
    coords = np.array(Number.findall(cart)).astype(float)
    atoms = Word.findall(cart)
    return CRESTCoords(
        atoms,
        coords.reshape(-1, 3)
    )

Components["InputStructure"] = {
    "tag_start": cartesian_start_tag,
    "tag_end"  : cartesian_end_tag,
    "parser"   : cartesian_coordinates_parser,
    "mode"     : "Single"
}


final_opt_info_start = "Final Geometry Optimization"
final_opt_info_end = "--------------------------"
def parse_opt_info(opt_block):
    return opt_block

Components["FinalOptInfo"] = {
    "tag_start": final_opt_info_start,
    "tag_end"  : final_opt_info_end,
    "parser"   : parse_opt_info,
    "mode"     : "Single"
}


final_ensemble_info = FileStreamerTag(
    "Final Ensemble Information",
    follow_ups=("--------------------------",)
)
final_ensemble_info_end = "-------"
EnsembleInfo = namedtuple('EnsembleInfo', ['relative_energies', 'total_energies', 'weights', 'report'])
def parse_ensemble_info(opt_block:str):
    header, engs = opt_block.split("Erel/kcal", 1)
    engs, footer = engs.rsplit('T /K', 1)
    report = header + 'T /K' + footer
    ensemble = np.loadtxt(io.StringIO(engs), skiprows=1, usecols=[1, 2, 3])
    return EnsembleInfo(
        *ensemble.T,
        report
    )

Components["FinalEnsembleInfo"] = {
    "tag_start": final_ensemble_info,
    "tag_end"  : final_opt_info_end,
    "parser"   : parse_ensemble_info,
    "mode"     : "Single"
}


########################################################################################################################
#
#                                           Defaults
#
# region Defaults
Defaults = (
)
# endregion

########################################################################################################################
#
#                                           Ordering
#
# region Ordering
# defines the ordering in the log file
glk = ( # this must be sorted by what appears when

)
list_type = { k:-1 for k in Components if Components[k]["mode"] == "List" }
Ordering = { k:i for i, k in enumerate([k for k in glk if k not in list_type]) }
Ordering.update(list_type)
del glk
del list_type
# endregion

__components__ = Components
__ordering__ = Ordering
__defaults__ = Defaults
