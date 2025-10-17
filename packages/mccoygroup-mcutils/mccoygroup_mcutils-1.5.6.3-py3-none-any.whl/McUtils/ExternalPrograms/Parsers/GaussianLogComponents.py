"""
This lists the types of readers and things available to the GaussianLogReader
"""
import io

import numpy as np

from ...Parsers import *
from collections import namedtuple, OrderedDict

########################################################################################################################
#
#                                           GaussianLogComponents
#
# region GaussianLogComponents
GaussianLogComponents = OrderedDict()  # we'll register on this bit by bit
# each registration should look like:

# GaussianLogComponents["Name"] = {
#     "description" : string, # used for docmenting what we have
#     "tag_start"   : start_tag, # starting delimeter for a block
#     "tag_end"     : end_tag, # ending delimiter for a block None means apply the parser upon tag_start
#     "parser"      : parser, # function that'll parse the returned list of blocks (for "List") or block (for "Single")
#     "mode"        : mode # "List" or "Single"
# }

########################################################################################################################
#
#                                           Header
#

tag_start = "******************************************"
tag_end   = FileStreamerTag(
    """ --------""",
    follow_ups = (""" -----""",)
)

HeaderPercentBlockParser = StringParser(
    NonCapturing(
        ("%", Capturing(Word, dtype=str), "=", Capturing((Word, Optional(Any), Word), dtype=str) ),
        dtype=str
    )
)
HeaderHashBlockLine = RegexPattern((
    Capturing(Optional((Word, "="), dtype=str)),
    Capturing(Repeating(Alternatives((WordCharacter, "\(", "\)", "\/", "\-")), dtype=str))
    ))
HeaderHashBlockLineParser = StringParser(HeaderHashBlockLine)
HeaderHashBlockParser = StringParser(
    RegexPattern((
        "#",
         Optional(Whitespace),
         Repeating(
             Named(
                Repeating(HeaderHashBlockLine),
                "Command",
                suffix=Optional(Whitespace),
                dtype=str,
                default=""
             )
        )
    ))
)

def header_parser(header):
    # regex = HeaderHashBlockParser.regex #type: RegexPattern
    header_percent_data = HeaderPercentBlockParser.parse_all(header)
    runtime_options = {}
    for k, v in header_percent_data.array:
        runtime_options[k] = v

    header_hash_data = HeaderHashBlockParser.parse_all(header)
    all_keys=" ".join(header_hash_data["Command"].array.flatten())
    raw_data = HeaderHashBlockLineParser.parse_all(all_keys).array

    job_options = {}
    for k, v in raw_data:
        if k.endswith("="):
            job_options[k.strip("=").lower()] = v.strip("()").split(",")
        else:
            job_options[v] = []

    return namedtuple("HeaderData", ["config", 'job'])(runtime_options, job_options)

mode = "Single"

GaussianLogComponents["Header"] = {
    "tag_start": tag_start,
    "tag_end"  : tag_end,
    "parser"   : header_parser,
    "mode"     : mode
}

########################################################################################################################
#
#                                           InputZMatrix
#

# region InputZMatrix
tag_start = "Z-matrix:"
tag_end   = """ 
"""

def parser(zmat):
    return zmat

mode = "Single"

GaussianLogComponents["InputZMatrix"] = {
    "tag_start": tag_start,
    "tag_end"  : tag_end,
    "parser"   : parser,
    "mode"     : mode
}

# endregion

########################################################################################################################
#
#                                           CartesianCoordinates
#

# region CartesianCoordinates

 # the region thing is just a PyCharm hack to collapse the boilerplate here... Could also have done 5000 files

cart_delim = """ --------------------------------------------------------------"""
cartesian_start_tag = FileStreamerTag(
    """Center     Atomic      Atomic             Coordinates (Angstroms)""",
    follow_ups= cart_delim
)
cartesian_end_tag = cart_delim

CartParser = StringParser(
    Repeating(
        (
            Named(
                Repeating(
                    Capturing(Integer),
                    min=3, max=3,
                    prefix=Optional(Whitespace),
                    suffix=Whitespace
                ),
                "GaussianStuff", handler=StringParser.array_handler(dtype=int)
            ),
            Named(
                Repeating(
                    Capturing(Number),
                    min = 3,
                    max = 3,
                    prefix=Optional(Whitespace),
                    joiner = Whitespace
                ),
                "Coordinates", handler=StringParser.array_handler(dtype=float)
            )
        ),
        suffix = Optional(Newline)
    )
)

# raise Exception(CartParser.regex)

label_pattern = RegexPattern([" ", Integer, " "])
def cartesian_coordinates_parser(strs, label_pattern=label_pattern):
    # strss = "\n\n".join(strs)

    # dummy atoms come and go...so we need to loop, annoyingly

    int_data = [
        np.array(label_pattern.findall(s)).astype(int).reshape(-1, 3)
        for s in strs
    ]

    coords = [
        np.array(Number.findall(s)).astype(float).reshape(-1, 3)
        for s in strs
    ]

    coords = (
        int_data,
        coords
    )

    return coords

GaussianLogComponents["CartesianCoordinates"] = {
    "tag_start": cartesian_start_tag,
    "tag_end"  : cartesian_end_tag,
    "parser"   : cartesian_coordinates_parser,
    "mode"     : "List"
}
GaussianLogComponents["ZMatCartesianCoordinates"] = {
    "tag_start": FileStreamerTag('''Z-Matrix orientation:''', follow_ups = (cart_delim, cart_delim)),
    "tag_end"  : cartesian_end_tag,
    "parser"   : cartesian_coordinates_parser,
    "mode"     : "List"
}
GaussianLogComponents["StandardCartesianCoordinates"] = {
    "tag_start": FileStreamerTag('''Standard orientation:''', follow_ups = (cart_delim, cart_delim)),
    "tag_end"  : cartesian_end_tag,
    "parser"   : cartesian_coordinates_parser,
    "mode"     : "List"
}
GaussianLogComponents["InputCartesianCoordinates"] = {
    "tag_start": FileStreamerTag('''Input orientation:''', follow_ups = (cart_delim, cart_delim)),
    "tag_end"  : cartesian_end_tag,
    "parser"   : cartesian_coordinates_parser,
    "mode"     : "List"
}

def header_cartesian_parser(carts):
    xyz = carts.strip().split("\n", 1)[1]#.strip()
    atoms = [
        line.split(None, 1)[0]
        for line in io.StringIO(xyz)
    ]
    coords = np.array(Number.findall(xyz)).astype(float).reshape(-1, 3)
    return atoms, coords
GaussianLogComponents["HeaderCartesianCoordinates"] = {
    "tag_start": 'Symbolic Z-matrix:',
    "tag_end"  : "\n\n",
    "parser"   : header_cartesian_parser,
    "mode"     : "Single"
}
# endregion

########################################################################################################################
#
#                                           ZMatrices
#

# region ZMatrices
tag_start = """Z-MATRIX (ANGSTROMS AND DEGREES)
   CD    Cent   Atom    N1       Length/X        N2       Alpha/Y        N3        Beta/Z          J
 ---------------------------------------------------------------------------------------------------"""
tag_end   = " ---------------------------------------------------------------------"

ZMatParser = StringParser(
    Repeating(
        (
            Named(
                Repeating(Capturing(PositiveInteger), min=1, max=2, prefix=Optional(Whitespace), suffix=Whitespace),
                "GaussianInts"
            ),
            Named(
                Capturing(AtomName),
                "AtomNames",
                suffix=Whitespace
            ),
            Named(
                Repeating(
                    (
                        Capturing(PositiveInteger),
                        Capturing(Number),
                        Parenthesized(PositiveInteger, prefix=Whitespace)
                    ),
                    min = None,
                    max = 3,
                    prefix=Optional(Whitespace),
                    joiner = Whitespace,
                ),
                "Coordinates"
            )
        ),
        suffix = Optional(RegexPattern((
            Optional((Whitespace, PositiveInteger)),
            Optional(Newline)
        )))
    )
)

def parser(strs):

    strss = '\n\n'.join(strs)
    fak = ZMatParser.parse_all(strss)
    coords = [
        (
            fak["GaussianInts", 0],
            fak["AtomNames", 0]
        ),
        fak["Coordinates", 0, 0],
        fak["Coordinates", 1]
        ]

    return coords
mode = "List"

GaussianLogComponents["ZMatrices"] = {
    "tag_start": tag_start,
    "tag_end"  : tag_end,
    "parser"   : parser,
    "mode"     : mode
}

# endregion

########################################################################################################################
#
#                                           OptimizationParameters
#

# region OptimizationParameters

tag_start  = "Optimization "
tag_end    = """                        !
 ------------------------------------------------------------------------
"""


def parser(pars):
    """Parses a optimizatioon parameters block"""
    did_opts = [ "Non-Optimized" not in par for par in pars]
    return did_opts, pars


mode = "List"

GaussianLogComponents["OptimizationParameters"] = {
    "tag_start": tag_start,
    "tag_end"  : tag_end,
    "parser"   : parser,
    "mode"     : mode
}

# endregion

########################################################################################################################
#
#                                           MullikenCharges
#

#region MullikenCharges
tag_start = "Mulliken charges:"
tag_end   = "Sum of Mulliken charges"


def parser(charges):
    """Parses a Mulliken charges block"""
    return charges
mode = "List"

GaussianLogComponents["MullikenCharges"] = {
    "tag_start": tag_start,
    "tag_end"  : tag_end,
    "parser"   : parser,
    "mode"     : mode
}

# endregion

########################################################################################################################
#
#                                           MultipoleMoments
#

#region MultipoleMoments
tag_start  = "Dipole moment ("
tag_end    = " N-N="


def parser(moms):
    """Parses a multipole moments block"""
    return moms


mode = "List"

GaussianLogComponents["MultipoleMoments"] = {
    "tag_start": tag_start,
    "tag_end"  : tag_end,
    "parser"   : parser,
    "mode"     : mode
}

# endregion

########################################################################################################################
#
#                                           DipoleMoments
#

# region DipoleMoments
tag_start  = "Dipole moment ("
tag_end    = "Quadrupole moment ("

dips_parser = StringParser(
    RegexPattern(
        (
            "X=", Capturing(Number),
            "Y=", Capturing(Number),
            "Z=", Capturing(Number)
        ),
        joiner=Whitespace,
        dtype=(float, (3,))
    )
)
def parser(moms):
    """Parses a multipole moments block"""

    res = dips_parser.parse_all("\n".join(moms))
    return res.array

mode = "List"
GaussianLogComponents["DipoleMoments"] = {
    "tag_start" : tag_start,
    "tag_end"   : tag_end,
    "parser"    : parser,
    "mode"      : mode
}

# endregion

########################################################################################################################
#
#                                           OptimizedDipoleMoments
#

# region DipoleMoments
tag_start  = " Dipole        ="
tag_end    = " Optimization"


def convert_D_number(a, **kw):
    import numpy as np
    return np.array([float(s.replace("D", "E")) for s in a])
DNumberPattern = RegexPattern((Number, "D", Integer), dtype=float)
OptimizedDipolesParser = StringParser(
    RegexPattern(
        (
            "Dipole", "=",
            Repeating(
                Capturing(DNumberPattern, handler=convert_D_number),
                min=3,
                max=3,
                suffix=Optional(Whitespace)
            )
        ),
        joiner=Whitespace
    )
)

def parser(mom):
    """Parses dipole block, but only saves the dipole of the optimized structure"""
    import numpy as np

    mom = "Dipole  =" + mom
    # print(">>>>>", mom)
    grps = OptimizedDipolesParser.parse_iter(mom)
    match = None
    for match in grps:
        pass

    if match is None:
        return np.array([])
    return match.value.array
    # else:
    #     grp = match.value
    #     dip_list = [x.replace("D", "E") for x in grp]
    #     dip_array = np.asarray(dip_list)
    #     return dip_array.astype("float64")

mode       = "List"
parse_mode = "Single"

GaussianLogComponents["OptimizedDipoleMoments"] = {
    "tag_start" : tag_start,
    "tag_end"   : tag_end,
    "parser"    : parser,
    "mode"      : mode,
    "parse_mode": parse_mode
}

# endregion

########################################################################################################################
#
#                                           ScanEnergies
#

# region ScanEnergies

tag_start = """ Summary of the potential surface scan:"""
tag_end = """Normal termination of"""

# Number = '(?:[\\+\\-])?\\d*\\.\\d+'
# block_pattern = "\s*"+Number+"\s*"+Number+"\s*"+Number+"\s*"+Number+"\s*"+Number
# block_re = re.compile(block_pattern)

ScanEnergiesParser = StringParser(
    RegexPattern(
        (
            Named(
                Repeating(Capturing(Word), prefix=Whitespace),
                "Keys",
                suffix=NonCapturing([Whitespace, Newline])
            ),
            Named(
                Repeating(
                    Repeating(
                        Alternatives([PositiveInteger, Number], dtype=float),
                        prefix=Whitespace
                        ),
                    suffix=Newline
                ),
                "Coords",
                prefix=Newline,
                handler=StringParser.array_handler(dtype=float)
            ),
        ),
        joiner=NonCapturing(Repeating([Whitespace, Repeating(["-"])]))
    )
)

def parser(block):
    """Parses the scan summary block"""
    import re

    if block is None:
        raise KeyError("key '{}' not in .log file".format('ScanEnergies'))

    r = ScanEnergiesParser.regex # type: RegexPattern
    parse=ScanEnergiesParser.parse(block)
    
    return namedtuple("ScanEnergies", ["coords", "energies"])(
        parse["Keys"].array,
        parse["Coords"].array
    )

mode = "Single"

GaussianLogComponents["ScanEnergies"] = {
    "tag_start": tag_start,
    "tag_end"  : tag_end,
    "parser"   : parser,
    "mode"     : mode
}

# endregion

########################################################################################################################
#
#                                           OptimizedScanEnergies
#

# region OptimizedScanEnergies

tag_start = """ Summary of Optimized Potential Surface Scan"""
tag_end = FileStreamerTag(
    tag_alternatives = (
        """ Largest change from initial coordinates is atom """,
        """-"""*25
    )
)

eigsPattern = RegexPattern(
    (
        "Eigenvalues --",
        Repeating(Capturing(Number), suffix=Optional(Whitespace))
    ),
    joiner=Whitespace
)

coordsPattern = RegexPattern(
    (
        Capturing(VariableName),
        Repeating(Capturing(Number), suffix=Optional(Whitespace))
    ),
    prefix=Whitespace,
    joiner=Whitespace
)

OptScanPat = StringParser(
    RegexPattern(
        (
            Named(eigsPattern,
                  "Eigenvalues"
                  #parser=lambda t: np.array(Number.findall(t), 'float')
                  ),
            Named(Repeating(coordsPattern, suffix=Optional(Newline)), "Coordinates")
        ),
        joiner=Newline
    )
)

# Gaussian16 started subtracting any uniform shift off of the energies
# we'd like to get it back

eigsShift = RegexPattern(
    (
        "add",
        Whitespace,
        Named(Number, "Shift")
    ),
    joiner=Whitespace
)

EigsShiftPat = StringParser(eigsShift)

def parser(pars):
    """Parses the scan summary block and returns only the energies"""
    from collections import OrderedDict
    import numpy as np

    if pars is None:
        return None

    try:
        shift = EigsShiftPat.parse(pars)["Shift"]
        #TODO: might need to make this _not_ be a `StructuredTypeArray` at some point, but seems fine for now
    except StringParserException:
        shift = 0
    par_data = OptScanPat.parse_all(pars)
    energies_array = np.concatenate(par_data["Eigenvalues"]).flatten()\
    # when there isn't a value, for shape reasons we get extra nans
    energies_array = energies_array[np.logical_not(np.isnan(energies_array))] + shift
    coords = OrderedDict()
    cdz = [a.array for a in par_data["Coordinates"].array]
    for coord_names, coord_values in zip(*cdz):
        for k, v in zip(coord_names, coord_values):
            if k not in coords:
                coords[k] = [v]
            else:
                coords[k].append(v)
    for k in coords:
        coords[k] = np.concatenate(coords[k]).flatten()
        coords[k] = coords[k][np.logical_not(np.isnan(coords[k]))]

    return namedtuple("OptimizedScanEnergies", ["energies", "coords"])(
        energies_array,
        coords
    )

mode = "Single"

GaussianLogComponents["OptimizedScanEnergies"] = {
    "tag_start": tag_start,
    "tag_end"  : tag_end,
    "parser"   : parser,
    "mode"     : mode
}


def parse_scf_energies(energy_blocks):
    return np.array(Number.findall(" ".join(energy_blocks))).astype('float')

GaussianLogComponents["SCFEnergies"] = {
    "tag_start": "SCF Done:  E(",
    "tag_end"  : " A.U. ",
    "parser"   : parse_scf_energies,
    "mode"     : "List"
}


tag_start = FileStreamerTag(
    """/l202.exe""",
    follow_ups=("Standard orientation: ",)
)
tag_end = FileStreamerTag(
    "SCF Done:  E(",
    follow_ups=(" A.U. ",)
)

SCFEnergyPattern = StringParser(
    RegexPattern((
        "SCF Done:  E\(", Repeating(Any), "\) =",
        Whitespace,
        Named(Number, "energy")
    ))
)

def parse_scf_block_coordinate_energies(energy_blocks):
    cart_bits = [
        e.split('Rotational constants', 1)[0] for e in energy_blocks
    ]
    carts = cartesian_coordinates_parser(cart_bits)
    scf_bits = ["SCF Done"+e.rsplit("SCF Done", 1)[-1] for e in energy_blocks]
    energies = SCFEnergyPattern.parse_all("\n\n".join(scf_bits))
    return {
        "coords":carts,
        "energies":energies['energy'].array
    }

GaussianLogComponents["SCFCoordinatesEnergies"] = {
    "tag_start": tag_start,
    "tag_end"  : tag_end,
    "parser"   : parse_scf_block_coordinate_energies,
    "mode"     : "List"
}

# endregion

########################################################################################################################
#
#                                           X-Matrix
#

# region X-Matrix

tag_start = FileStreamerTag(
    """Total Anharmonic X Matrix (in cm^-1)""",
    follow_ups=("""-"""*25,)
)
tag_end = FileStreamerTag(
    tag_alternatives = (
        """ ================================================== """,
        """-"""*25
    )
)

def parser(pars):
    """Parses the X matrix block and returns stuff --> huge pain in the ass function"""
    import numpy as np

    energies = np.array([x.replace("D", "E") for x in DNumberPattern.findall(pars)])
    l = len(energies)
    n = int( (-1 + np.sqrt(1 + 8*l))/2 )
    X = np.empty((n, n))
    # gaussian returns the data as blocks of 5 columns in the lower-triangle, annoyingly,
    # so we need to rearrange the indices so that they are sorted to make this work
    i, j = np.tril_indices_from(X)
    energies_taken = 0
    blocks = int(np.ceil(n/5))
    for b in range(blocks):
        sel = np.where((b*5-1 < j) * (j < (b+1)*5))[0]
        e_new=energies_taken+len(sel)
        e = energies[energies_taken:e_new]
        energies_taken=e_new
        ii = i[sel]
        jj = j[sel]
        X[ii, jj] = e
        X[jj, ii] = e

    return X

mode = "Single"

GaussianLogComponents["XMatrix"] = {
    "tag_start": tag_start,
    "tag_end"  : tag_end,
    "parser"   : parser,
    "mode"     : mode
}

# endregion


tag_start =  "Job cpu time"
tag_end = "Normal termination"

def parser(block, start=tag_start):
    return " " + start + block

mode = "Single"

GaussianLogComponents["Footer"] = {
    "tag_start": tag_start,
    "tag_end"  : tag_end,
    "parser"   : parser,
    "mode"     : mode
}

# endregion

tag_start = """FrcOut:"""
tag_end = """MW cartesian velocity:"""

CartesianBlockTags = ["Cartesian coordinates: (bohr)", "MW cartesian"]
def parse_aimd_coords(blocks):
    big_block = "\n".join(blocks)
    comps = np.char.replace(DNumberPattern.findall(big_block), "D", "E").astype(float)
    return comps.reshape((len(blocks), -1, 3)) # easy as that since XYZ?

ValueBlockTags = ["FrcOut",
                  FileStreamerTag(
                      """Final forces over variables""",
                      follow_ups=("Leave Link",)
                  )]
def convert_D_number(a, **kw):
    import numpy as np
    converted = np.char.replace(a, 'D', 'E')
    return converted.astype(float)
DNumberPattern = RegexPattern((Number, "D", Integer), dtype=float)
EnergyBlockPattern = StringParser(
        RegexPattern(
            (
                "Energy=", Named(DNumberPattern, 'E', handler=convert_D_number)
            )
        )
)
ForceBlockTags = ["force vector number 2", "After rot"]
def parse_grad(block):
    comps = np.array([x.replace("D", "E") for x in DNumberPattern.findall(block)])
    return comps.astype(float) #.reshape((-1, 3)) # easy as that since XYZ? -> even easier...
def parse_weird_mat(pars): # identical to X-matrix parser...
    """Parses the Hessian matrix block and returns stuff --> huge pain in the ass function"""
    import numpy as np

    energies = np.array([x.replace("D", "E") for x in DNumberPattern.findall(pars)])
    l = len(energies)
    n = int( (-1 + np.sqrt(1 + 8*l))/2 )
    X = np.empty((n, n))
    # gaussian returns the data as blocks of 5 columns in the lower-triangle, annoyingly,
    # so we need to rearrange the indices so that they are sorted to make this work
    i, j = np.tril_indices_from(X)
    energies_taken = 0
    blocks = int(np.ceil(n/5))
    for b in range(blocks):
        sel = np.where((b*5-1 < j) * (j < (b+1)*5))[0]
        e_new=energies_taken+len(sel)
        e = energies[energies_taken:e_new]
        energies_taken=e_new
        ii = i[sel]
        jj = j[sel]
        X[ii, jj] = e
        X[jj, ii] = e

    return X
HessianBlockTags = ["Force constants in Cartesian coordinates:", "Final forces"]


def convert_D_number_block(a, **kw):
    import numpy as np
    convertable = np.char.replace(a.view('U15').reshape(a.shape[0], -1), 'D', 'E')
    return convertable.astype(float)
DNumberPattern = RegexPattern((Number, "D", Integer), dtype=float)
DipoleBlockPattern = StringParser(
        RegexPattern(
            (
                "Dipole", Whitespace, "=",
                    Named(Repeating(DNumberPattern, min=3, max=3), 'D', handler=convert_D_number_block),
            )
        )
)

def parse_aimd_values_blocks(blocks):
    big_block = "\n".join(blocks)

    energies = EnergyBlockPattern.parse_all(big_block)['E'].array
    # if energies[-1] == energies[-2]:
    #     if blocks[-1] == blocks[-2]:
    #         big_block = "\n".join(blocks[:-1]) # there's an extra copy
    #     energies = energies[:-1]

    # dips = DipoleBlockPattern.parse_all(big_block)['D'].array
    with StringStreamReader(big_block) as subparser:
        grad = np.array(subparser.parse_key_block(
            ForceBlockTags[0],
            ForceBlockTags[1],
            parser=lambda hstack: [parse_grad(h) for h in hstack],
            mode='List'
        ))

        hesses = np.array(subparser.parse_key_block(
            HessianBlockTags[0],
            HessianBlockTags[1],
            parser=lambda hstack:[parse_weird_mat(h) for h in hstack],
            mode='List'
        ))

    return namedtuple("AIMDValues", ['energies', 'gradients', 'hessians'])(
        energies=energies, gradients=grad, hessians=hesses#, dipoles=dips
    )

def parser(blocks):
    big_block = "FrcOut:\n".join([""] + [b.split('FrcOut:')[-1] for b in blocks]) # we can get two energy prints to one coords

    with StringStreamReader(big_block) as subparser:
        coords = subparser.parse_key_block(
            CartesianBlockTags[0],
            CartesianBlockTags[1],
            parser=parse_aimd_coords,
            mode='List'
        )

        vals = subparser.parse_key_block(
            ValueBlockTags[0],
            ValueBlockTags[1],
            parser=parse_aimd_values_blocks,
            mode='List'
        )

    return namedtuple("AIMDTrajectory", ['coords', 'vals'])(
        coords=coords,
        vals=vals
    )

mode = "List"
GaussianLogComponents["AIMDTrajectory"] = {
    "tag_start": tag_start,
    "tag_end"  : tag_end,
    "parser"   : parser,
    "mode"     : mode
}

force_block_tags = (
    'Forces (Hartrees/Bohr)',
    'Cartesian Forces:'
)

ForceParser = StringParser(
    Repeating(
        (
            Named(
                Repeating(
                    Capturing(Integer),
                    min=2, max=2,
                    prefix=Optional(Whitespace),
                    suffix=Whitespace
                ),
                "GaussianStuff", handler=StringParser.array_handler(dtype=int)
            ),
            Named(
                Repeating(
                    Capturing(Number),
                    min = 3,
                    max = 3,
                    prefix=Optional(Whitespace),
                    joiner = Whitespace
                ),
                "Forces", handler=StringParser.array_handler(dtype=float)
            )
        ),
        suffix = Optional(Newline)
    )
)

def parse_force_list(strs):

    strss = "\n\n".join(strs)

    parse = ForceParser.parse_all(strss)

    coords = (
        parse["GaussianStuff", 0],
        parse["Forces"].array
    )

    return coords

mode = "List"
GaussianLogComponents["Gradients"] = {
    "tag_start": force_block_tags[0],
    "tag_end"  : force_block_tags[1],
    "parser"   : parse_force_list,
    "mode"     : mode
}


def parse_hessian_list(hessias):
    return [parse_weird_mat(h) for h in hessias]

mode = "List"
GaussianLogComponents["Hessians"] = {
    "tag_start": HessianBlockTags[0],
    "tag_end"  : HessianBlockTags[1],
    "parser"   : parse_hessian_list,
    "mode"     : mode
}


cubic_block_tags = (
    'Final third derivatives:',
    'Diagonal'
)
label_pattern = RegexPattern([" ", PositiveInteger, " "])
def parse_cubic_mat(pars, label_pattern=label_pattern): # identical to X-matrix parser...
    """Parses the Hessian matrix block and returns stuff --> huge pain in the ass function"""
    import numpy as np

    energies = np.array([x.replace("D", "E") for x in DNumberPattern.findall(pars)])
    l = np.max(np.array(label_pattern.findall(pars)).astype(int))
    n = int( (-1 + np.sqrt(1 + 8*l))/2 )
    k = len(energies) // l
    X = np.empty((n, n, k))
    # gaussian returns the data as blocks of 5 columns in the lower-triangle, annoyingly,
    # so we need to rearrange the indices so that they are sorted to make this work
    i, j = np.tril_indices(n)
    energies_taken = 0
    blocks = int(np.ceil(k/5))
    for b in range(blocks):
        bs = b * 5
        be = min((b+1) * 5, k)
        e_new=energies_taken+l*(be-bs)
        e = energies[energies_taken:e_new]
        energies_taken=e_new
        X[i, j, bs:be] = e.reshape(-1, be-bs)
        X[j, i, bs:be] = e.reshape(-1, be-bs)

    return X

def parse_cubics_list(hessias):
    return [parse_cubic_mat(h) for h in hessias]

mode = "List"
GaussianLogComponents["CubicDerivs"] = {
    "tag_start": cubic_block_tags[0],
    "tag_end"  : cubic_block_tags[1],
    "parser"   : parse_cubics_list,
    "mode"     : mode
}

quartic_block_tags = (
    'nuclear 4th derivatives',
    'Numerical'
)
def parse_quartics_list(hessias):
    return [parse_cubic_mat(h) for h in hessias]

mode = "List"
GaussianLogComponents["QuarticDerivs"] = {
    "tag_start": quartic_block_tags[0],
    "tag_end"  : quartic_block_tags[1],
    "parser"   : parse_quartics_list,
    "mode"     : mode
}


tag_start = """Harmonic frequencies (cm**-1)"""
tag_end = """

"""

normal_mode_block = RegexPattern(
    (
        Named(Repeating((Whitespace, Integer), min=1, max=3), "label"),
        Named(Repeating((Whitespace, Word), min=1, max=3), "symmetry"),
        Named(("Frequencies --", Repeating((Whitespace, Number), min=1, max=3)), "freqs"),
        Named(("Red. masses --", Repeating((Whitespace, Number), min=1, max=3)), "masses"),
        Named(("Frc consts  --", Repeating((Whitespace, Number), min=1, max=3)), "fcs"),
        Named(("IR Inten    --", Repeating((Whitespace, Number), min=1, max=3)), "ir_ints"),
        RegexPattern(("Atom  AN", Repeating((Whitespace, "X      Y      Z"), min=1, max=3))),
        Named(
            Repeating(
                (Whitespace, Integer, Whitespace, Integer, Repeating((Whitespace, Number), min=3, max=9), Newline)
            ),
            "displacements"
        )
    ),
    joiner=RegexPattern((Newline, Whitespace))
)


def parse_nms_modes(label, symmetries, freqs, masses, fcs, ir_ints, _, disps):
    freqs = [float(x) for x in freqs[len('Frequencies --'):].split()]  # since len max 3, probably fastest way
    masses = [float(x) for x in masses[len('Red. masses --'):].split()]  # since len max 3, probably fastest way
    disps = StringParser.array_handler(dtype=float)(disps)[:, 2:]
    disps = np.moveaxis(disps.reshape(disps.shape[0], 3, -1), 1, -1).reshape(-1, 3)
    return freqs, masses, disps


def parse_nms_block(block):
    bits = normal_mode_block.findall(block)
    freqs = [None] * len(bits)
    masses = [None] * len(bits)
    disps = [None] * len(bits)
    for i, bit in enumerate(bits):
        f, m, d = parse_nms_modes(*bit)
        freqs[i] = f
        masses[i] = m
        disps[i] = d

    return np.concatenate(freqs), np.concatenate(masses), np.concatenate(disps, axis=1)


def parse(blocks):
    return [parse_nms_block(b) for b in blocks]


mode = "List"
GaussianLogComponents["NormalModes"] = {
    "tag_start": tag_start,
    "tag_end": tag_end,
    "parser": parse,
    "mode": mode
}
# mode = "List"
# GaussianLogComponents["AIMDCoordinates"] = {
#     "tag_start": tag_start,
#     "tag_end"  : tag_end,
#     "parser"   : parser,
#     "mode"     : mode
# }

tag_start = "Excitation energies and oscillator strengths:"
tag_end = "SavETr:"

def parse_excited_states(blocks:str):
    states = []
    if blocks is not None:
        blocks = blocks.strip().split(":")[1:]
        for b in blocks:
            lines = b.split("\n")
            info = lines[0]
            bits = info.strip().rsplit(maxsplit=6)
            if len(bits) < 7: break
            symmetry, energy, _, _, _, fspec, sspec = bits
            _, osc = fspec.split("=")
            _, ov = sspec.split("=")

            state = {
                "Energy": float(energy),
                "Overlap": float(ov),
                "Symmetry": symmetry,
                "Transitions": {}
            }
            for l in lines[1:]:
                l = l.strip()
                if '->' in l:
                    start, end = l.split('->')
                    end, energy = end.split()
                    state['Transitions'][(int(start), int(end))] = float(energy)
            states.append(state)
            if b.endswith('SavETr'): break

    return states

mode = "Single"
GaussianLogComponents["ExcitedStates"] = {
    "tag_start": tag_start,
    "tag_end": tag_end,
    "parser": parse_excited_states,
    "mode": mode
}

tag_start = "Zeta(I,J)"
tag_end = "Num. of Coriolis"

def parse_coriolis(blocks):
    if blocks is not None:
        blocks = blocks.rsplit("\n", 1)[0]
        cors = np.loadtxt(io.StringIO(blocks), skiprows=1, usecols=[1, 2, 3])
        ax = np.loadtxt(io.StringIO(blocks), skiprows=1, usecols=[0], dtype=str)
        ar = np.zeros((len(ax), 1), dtype=float)
        for i, a in enumerate(ax):
            if a == 'y':
                ar[i, 0] = 1
            elif a == 'z':
                ar[i, 0] = 2
        return np.concatenate([ar, cors], axis=1)

mode = "Single"
GaussianLogComponents["CoriolisTerms"] = {
    "tag_start": tag_start,
    "tag_end": tag_end,
    "parser": parse_coriolis,
    "mode": mode
}


tag_start = "K(I,J)"
tag_end = "Num. of 2nd derivatives"

def parse_quadratics(blocks):
    blocks = blocks.rsplit("\n", 1)[0]
    return np.loadtxt(io.StringIO(blocks), skiprows=1, usecols=[0, 1, 2])

mode = "Single"
GaussianLogComponents["QuadraticTerms"] = {
    "tag_start": tag_start,
    "tag_end": tag_end,
    "parser": parse_quadratics,
    "mode": mode
}

tag_start = "K(I,J,K)"
tag_end = "Num. of 3rd derivatives"

def parse_cubics(blocks):
    blocks = blocks.rsplit("\n", 1)[0]
    return np.loadtxt(io.StringIO(blocks), skiprows=1, usecols=[0, 1, 2, 3])

mode = "Single"
GaussianLogComponents["CubicTerms"] = {
    "tag_start": tag_start,
    "tag_end": tag_end,
    "parser": parse_cubics,
    "mode": mode
}

tag_start = "K(I,J,K,L)"
tag_end = "Num. of 4th derivatives"

def parse_quartics(blocks):
    blocks = blocks.rsplit("\n", 1)[0]
    return np.loadtxt(io.StringIO(blocks), skiprows=1, usecols=[0, 1, 2, 3, 4])

mode = "Single"
GaussianLogComponents["QuarticTerms"] = {
    "tag_start": tag_start,
    "tag_end": tag_end,
    "parser": parse_quartics,
    "mode": mode
}

tag_start = "1\\"
tag_end = FileStreamerTag(
    ("\\\\@", "\\\n \\@", "\\\\\n @"),
    # follow_ups = (""" -----""",)
)

def skip_report_header(stuff):
    if stuff[0] in {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}:
        return skip_report_header(stuff[1:])
    return stuff

num_pattern = Alternatives([
    Integer,
    Number,
    IntBaseNumber,
    (Number, "e", Integer)
])

scan_spec = namedtuple('scan_spec', ['value', 'steps', 'amount'])
def parse_reports(blocks,
                  endline_pattern=RegexPattern([Newline, Whitespace]),
                  num_pattern=num_pattern,
                  numblock_pattern=Repeating(num_pattern, suffix=Optional(","))
                  ):
    bits = []
    for b in blocks:
        b = endline_pattern.remove(b)
        res = {}
        subblocks = b.split('\\\\')
        info = subblocks[0]
        stuff = info.split("\\")
        stuff = skip_report_header(stuff)
        if stuff[0].startswith('GINC-'):
            res['node'] = stuff[0][5:]
            stuff = stuff[1:]
        elif not Word.match(stuff[0]):
            res['node'] = stuff[0]
            stuff = stuff[1:]

        for k in ['job', 'level_of_theory', 'basis', 'formula', 'user', 'date']:
            res[k] = stuff[0]
            stuff = stuff[1:]

        res['route'] = subblocks[1]
        res['description'] = subblocks[2]
        res['molecule'] = subblocks[3].replace('\\', '\n')
        res['results'] = []
        for block in subblocks[4:]:
            if block == '@': continue
            for chunk in block.split('\\'):
                defs = chunk.split('=')
                if len(defs) == 1:
                    v = defs[0]
                    if len(v.strip()) == 0: continue
                    if numblock_pattern.fullmatch(v):
                        v = np.array(v.split(',')).astype(float)
                    res['results'].append(v)
                elif len(defs) == 2:
                    v = defs[1]
                    if ",s," in v:
                        v = v.split(",")
                        v = scan_spec(float(v[0]), int(v[2]), float(v[3]))
                    elif num_pattern.fullmatch(v):
                        v = float(v)
                    elif numblock_pattern.fullmatch(v):
                        v = np.array(v.split(',')).astype(float)
                    res[defs[0]] = v
                elif len(chunk.strip()) > 0:
                    res['results'].append(chunk)

        if res['job'] == 'Freq':
            if len(res['results']) > 2:
                fc_scaling = 6 * len(res['results'][0])
                cq_scaling = len(res['results'][2])
                if cq_scaling % fc_scaling == 0:
                    fcs, grad, higher = res['results'][:3]
                    res['results'] = res['results'][3:]
                    res['PotentialDeriv'] = [
                        grad,
                        fcs,
                        higher
                    ]
                else:
                    fcs, grad = res['results'][:2]
                    res['results'] = res['results'][2:]
                    res['PotentialDeriv'] = [
                        grad, fcs
                    ]
            else:
                fcs, grad = res['results'][:2]
                res['results'] = res['results'][2:]
                res['PotentialDeriv'] = [
                    grad, fcs
                ]

        bits.append(res)

    return bits

def tag_validator(block):
    return "\n\n" not in block

mode = "List"
GaussianLogComponents["Reports"] = {
    "tag_start": tag_start,
    "tag_end": tag_end,
    'validator': tag_validator,
    "parser": parse_reports,
    "mode": mode
}

########################################################################################################################
#
#                                           GaussianLogDefaults
#
# region GaussianLogDefaults
GaussianLogDefaults = (
    "StartDateTime",
    "InputZMatrix",
    "ScanTable",
    "Blurb",
    "ComputerTimeElapsed",
    "EndDateTime"
)
# endregion

########################################################################################################################
#
#                                           GaussianLogOrdering
#
# region GaussianLogOrdering
# defines the ordering in a GaussianLog file
glk = ( # this must be sorted by what appears when
    "Header",
    "StartDateTime",
    "CartesianCoordinates",
    "ZMatCartesianCoordinates",
    "StandardCartesianCoordinates",
    "CartesianCoordinateVectors",
    "MullikenCharges",
    "MultipoleMoments",
    "DipoleMoments",
    "OptimizedDipoleMoments",
    "QuadrupoleMoments",
    "OctapoleMoments",
    "HexadecapoleMoments",
    "IntermediateEnergies",
    "InputZMatrix",
    "InputZMatrixVariables",
    "ZMatrices",
    "ScanEnergies",
    "OptimizedScanEnergies",
    "OptimizationScan",
    "Blurb",
    "Footer"
)
list_type = { k:-1 for k in GaussianLogComponents if GaussianLogComponents[k]["mode"] == "List" }
GaussianLogOrdering = { k:i for i, k in enumerate([k for k in glk if k not in list_type]) }
GaussianLogOrdering.update(list_type)
del glk
del list_type
# endregion
