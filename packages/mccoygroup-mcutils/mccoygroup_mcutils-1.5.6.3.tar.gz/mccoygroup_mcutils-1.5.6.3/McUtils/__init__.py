"""
A growing package of assorted functionality that finds use across many different packages, but doesn't attempt to
provide a single unified interface for doing certain types of projects.

All of the McUtils packages stand mostly on their own, but there will be little calls into one another here and there,
especially pieces using `Numputils`

The more scientifically-focused `Psience` package makes significant use of `McUtils` as do various packages that have
been written over the years.
"""

__all__ = []

from . import Data
__all__ += ["Data"]
from . import Numputils
__all__ += ["Numputils"]
from . import ExternalPrograms
__all__ += ["ExternalPrograms"]
from . import Plots
__all__ += ["Plots"]
from . import Jupyter
__all__ += ["Jupyter"]
from . import Parsers
__all__ += ["Parsers"]
from . import Formatters
__all__ += ["Formatters"]
from . import Coordinerds
__all__ += ["Coordinerds"]
from . import Zachary
__all__ += ["Zachary"]
from . import GaussianInterface
__all__ += ["GaussianInterface"]
from . import Extensions
__all__ += ["Extensions"]
from . import Scaffolding
__all__ += ["Scaffolding"]
from . import Parallelizers
__all__ += ["Parallelizers"]
from . import Devutils
__all__ += ["Devutils"]
from . import Docs
__all__ += ["Docs"]
from . import Misc
__all__ += ["Misc"]