"""
A place to store all utilities related to combinatorics.
Currently only contains a subpackage for working with permutations.
That package is used in the `BasisReps` work in `Psience`.

It handles both integer partitions and unique permutations.
It

Might be worth extending to handle more lattice-path stuff.

:examples:
Get all partitions of `3`

```python
IntegerPartitioner.partitions(3)
```

Count the number of partitions up to 10

```python
IntegerPartitioner.count_partitions(10)
```

Count the number of partitions of `4` of length exactly `2`
with minimum component between `2` and `4`

```python
IntegerPartitioner.count_exact_length_partitions_in_range(4, 4, 2, 2)
```

Get all unique permutations of the first integer partition of 10

```python
lens, parts = IntegerPartitioner.partitions(10, pad=True, return_lens=True)
perms = UniquePermutations(parts[0]).permutations()
```

Get all 9D state vectors and indices for states with up to 4 quanta of excitation

```python
SymmetricGroupGenerator(9).get_terms([1, 2, 3, 4])
```
"""

__all__ = []
from .Permutations import *; from .Permutations import __all__ as exposed
__all__ += exposed
from .Sequences import *; from .Sequences import __all__ as exposed
__all__ += exposed
from .YoungTableaux import *; from .YoungTableaux import __all__ as exposed
__all__ += exposed