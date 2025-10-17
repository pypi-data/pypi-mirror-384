"""
Utilities for writing parsers of structured text.
An entirely standalone package which is used extensively by `GaussianInterface`.
Three main threads are handled:

1. A `FileStreamer` interface which allows for efficient searching for blocks of text
   in large files with no pattern matching
2. A `Regex` interface that provides declarative tools for building and manipulating a regular expression
   as a python tree
3. A `StringParser`/`StructuredTypeArray` interface that takes the `Regex` tools and allows for automatic
   construction of complicated `NumPy`-backed arrays from the parsed data. Generally works well but the
   problem is complicated and there are no doubt many unhandled edge cases.
   This is used extensively with (1.) to provide efficient parsing of data from Gaussian `.log` files by
   using a streamer to match chunks and a parser to extract data from the matched chunks.
"""

__all__ = []
from .FileStreamer import *; from .FileStreamer import __all__ as exposed
__all__ += exposed
from .StringParser import *; from .StringParser import __all__ as exposed
__all__ += exposed
from .RegexPatterns import *; from .RegexPatterns import __all__ as exposed
__all__ += exposed
from .StructuredType import *; from .StructuredType import __all__ as exposed
__all__ += exposed
from .Parsers import *; from .Parsers import __all__ as exposed
__all__ += exposed
from .XYZParser import *; from .XYZParser import __all__ as exposed
__all__ += exposed