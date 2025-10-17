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

# region CartesianCoordinates

 # the region thing is just a PyCharm hack to collapse the boilerplate here... Could also have done 5000 files

cartesian_start_tag = FileStreamerTag(
    "Atomic Coordinates",
    follow_ups=("Nr  Atom  Charge", "\n\n")
)
cartesian_end_tag = "\n\n"

CartParser = StringParser(
    Repeating(
        (
            RegexPattern(
                [Integer, Named(Word, "Atoms"), Number],
                joiner=Whitespace,
                prefix=Optional(Whitespace),
                suffix=Whitespace
            ),
            Named(
                Repeating(
                    Capturing(Number),
                    min=3,
                    max=3,
                    prefix=Optional(Whitespace),
                    joiner = Whitespace
                ),
                "Coordinates", handler=StringParser.array_handler(dtype=float)
            )
        ),
        suffix=Optional(Newline)
    )
)

def strip_recursive(at_list):
    return [
        Integer.remove(s.strip()) if isinstance(s, str) else strip_recursive(s)
        for s in at_list
    ]
MOLPROCoords = namedtuple("MOLPROCoords", ["atoms", "coords"])
def cartesian_coordinates_parser(strs):
    strss = "\n\n".join(strs)

    parse = CartParser.parse_all(strss)
    coords = MOLPROCoords(
        strip_recursive(parse["Atoms"].array),
        parse["Coordinates"].array
    )

    return coords

Components["CartesianCoordinates"] = {
    "tag_start": cartesian_start_tag,
    "tag_end"  : cartesian_end_tag,
    "parser"   : cartesian_coordinates_parser,
    "mode"     : "List"
}



normal_modes_start_tag = FileStreamerTag(
    "Normal Modes",
)
normal_modes_end_tag = "Frequencies dumped"

MOLPRONormalModes = namedtuple("MOLPRONormalModes", ["freqs", "modes"])
def normal_modes_parser(strs):
    all_freqs = []
    all_modes = []
    for s in strs:
        blocks = s.split("\n\n")[1:]
        nrows = blocks[0].count("\n")

        subfreqs = []
        submodes = []
        for b in blocks:
            stuff = np.array(Number.findall(b)).astype(float).reshape(nrows, -1)
            subfreqs.append(stuff[0])
            submodes.append(stuff[3:])
        all_freqs.append(np.concatenate(subfreqs))
        all_modes.append(np.concatenate(submodes, axis=-1))


    return MOLPRONormalModes(all_freqs, all_modes)

Components["NormalModes"] = {
    "tag_start": normal_modes_start_tag,
    "tag_end"  : normal_modes_end_tag,
    "parser"   : normal_modes_parser,
    "mode"     : "List"
}

quadratic_terms_start_tag = FileStreamerTag(
    "Quadratic force constants:",
    follow_ups=["f_ij", "\n\n"]
)
quadratic_terms_end_tag = "\n\n"

def quadratic_terms_parser(qts):
    # qts = qts.split('\n\n')[-1]
    return [
        np.loadtxt(io.StringIO(qts), usecols=[1], dtype=int),
        np.loadtxt(io.StringIO(qts), usecols=[2], dtype=float)
    ]

Components["QuadraticTerms"] = {
    "tag_start": quadratic_terms_start_tag,
    "tag_end"  : quadratic_terms_end_tag,
    "parser"   : quadratic_terms_parser,
    "mode"     : "Single"
}


cubic_terms_start_tag = FileStreamerTag(
    "Cubic force constants:",
    follow_ups=["f_ijk", "\n\n"]
)
cubic_terms_end_tag = "\n\n"

def cubic_terms_parser(qts):
    # qts = qts.split('\n\n')[-1]
    return [
        np.loadtxt(io.StringIO(qts), usecols=[0, 1, 2], dtype=int),
        np.loadtxt(io.StringIO(qts), usecols=[3], dtype=float)
    ]

Components["CubicTerms"] = {
    "tag_start": cubic_terms_start_tag,
    "tag_end"  : cubic_terms_end_tag,
    "parser"   : cubic_terms_parser,
    "mode"     : "Single"
}


quartic_terms_start_tag = FileStreamerTag(
    "Quartic force constants:",
    follow_ups=["f_ijkl", "\n\n"]
)
quartic_terms_end_tag = "\n\n"

def quartic_terms_parser(qts):
    # qts = qts.split('\n\n')[-1]
    return [
        np.loadtxt(io.StringIO(qts), usecols=[0, 1, 2, 3], dtype=int),
        np.loadtxt(io.StringIO(qts), usecols=[4], dtype=float)
    ]

Components["QuarticTerms"] = {
    "tag_start": quartic_terms_start_tag,
    "tag_end"  : quartic_terms_end_tag,
    "parser"   : quartic_terms_parser,
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
