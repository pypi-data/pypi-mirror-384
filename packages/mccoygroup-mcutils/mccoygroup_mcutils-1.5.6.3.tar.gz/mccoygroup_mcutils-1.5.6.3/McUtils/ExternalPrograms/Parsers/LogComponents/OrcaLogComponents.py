"""
This lists the types of readers and things available to the GaussianLogReader
"""
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
    """CARTESIAN COORDINATES (ANGSTROEM)""",
    follow_ups="---------------------------------"
)
cartesian_end_tag = "\n\n"

CartParser = StringParser(
    Repeating(
        (
            Named(
                Word, "Atoms",
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
        s.strip() if isinstance(s, str) else strip_recursive(s)
        for s in at_list
    ]
OrcaCoords = namedtuple("OrcaCoords", ["atoms", "coords"])
def cartesian_coordinates_parser(strs):
    strss = "\n\n".join(strs)

    parse = CartParser.parse_all(strss)
    coords = OrcaCoords(
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


cartesian_au_start_tag = FileStreamerTag(
    """CARTESIAN COORDINATES (A.U.)""",
    follow_ups="X           Y           Z"
)
cartesian_end_tag = "\n\n"

CartAUParser = StringParser(
    Repeating(
        (
           Named(
                Integer, "AtNos",
                prefix=Optional(Whitespace),
                suffix=Whitespace
            ),
            Named(
                Word, "Atoms",
                prefix=Optional(Whitespace),
                suffix=Whitespace
            ),
           Named(
                Number, "ZA",
                prefix=Optional(Whitespace),
                suffix=Whitespace
            ),
           Named(
                Integer, "Frag",
                prefix=Optional(Whitespace),
                suffix=Whitespace
            ),
           Named(
                Number, "Mass",
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

OrcaAUCoords = namedtuple("OrcaAUCoords", ["atoms", "masses", "coords"])
def cartesian_au_coordinates_parser(strs):
    strss = "\n\n".join(strs)

    parse = CartAUParser.parse_all(strss)
    coords = OrcaAUCoords(
        strip_recursive(parse["Atoms"].array),
        parse["Mass"].array,
        parse["Coordinates"].array
    )

    return coords

Components["CartesianAUCoordinates"] = {
    "tag_start": cartesian_au_start_tag,
    "tag_end"  : cartesian_end_tag,
    "parser"   : cartesian_au_coordinates_parser,
    "mode"     : "List"
}


freqs_start_tag = FileStreamerTag(
    """VIBRATIONAL FREQUENCIES""",
    follow_ups="-----------------------"
)
freqs_end_tag = "\n\n\n"

FreqsParser = StringParser(
    Repeating(
        (
            Named(
                Integer, "Mode",
            ),
            ":",
            Whitespace,
            Named(
                Number, "Freqs"
            )
        ),
        suffix=Optional(Newline)
    )
)

def freqs_parser(freq_str):

    parse = FreqsParser.parse_all(freq_str)
    # coords = (
    #     strip_recursive(parse["Atoms"].array),
    #     parse["Freqs"].array
    # )

    return parse["Freqs"].array.flatten()

Components["VibrationalFrequencies"] = {
    "tag_start": freqs_start_tag,
    "tag_end"  : freqs_end_tag,
    "parser"   : freqs_parser,
    "mode"     : "Single"
}

OrcaMatrixParser = StringParser(
    Repeating(
        (
            Whitespace,
            Integer,
            Whitespace,
            Repeating(
                Capturing(Number),
                min=1,
                max=6,
                prefix=Optional(Whitespace),
                joiner=Whitespace
            ),
        ),
        handler=StringParser.array_handler(dtype=float),
        suffix=Optional(Newline)
    )
)

def parse_orca_matrix(orca_mat):

    parse = np.concatenate(
        [
            p.value[:, 1:]
            for p in OrcaMatrixParser.parse_iter(orca_mat)
        ],
        axis=1
    )
    # coords = (
    #     strip_recursive(parse["Atoms"].array),
    #     parse["Freqs"].array
    # )

    return parse

nms_start_tag = FileStreamerTag(
    """NORMAL MODES""",
    follow_ups="------------"
)
nms_end_tag = "\n\n\n"

Components["NormalModes"] = {
    "tag_start": nms_start_tag,
    "tag_end"  : nms_end_tag,
    "parser"   : parse_orca_matrix,
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
