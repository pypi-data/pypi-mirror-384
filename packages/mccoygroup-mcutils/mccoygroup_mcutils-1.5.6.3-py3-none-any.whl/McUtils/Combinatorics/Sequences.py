"""
Sequences lifted from finite difference weight calculation in
ZachLib to serve more general purposes
"""

import numpy as np, math
import itertools
from .. import Numputils as nput

__all__ = [
    "StirlingS1",
    "Binomial",
    "GammaBinomial",
    "Factorial",
    "prime_sieve",
    "prime_factorize",
    "prime_iter",
    "prime_list",
    "stable_factorial_ratio"
]

def StirlingS1(n):
    """Computes the Stirling numbers

    :param n:
    :type n:
    :return:
    :rtype:
    """
    stirlings = np.eye(n)
    for i in range(n):
        for j in range(i+1):
            stirlings[i, j] = (-1)**(i-j) *( (i-1)*abs(stirlings[i-1, j]) + abs(stirlings[i-1, j-1]))
    return stirlings

def Binomial(n, dtype=None):
    """
    Fast recursion to calculate all
    binomial coefficients up to binom(n, n)

    :param n:
    :type n:
    :return:
    :rtype:
    """
    if dtype is None:
        max_int = np.iinfo(np.dtype('uint64')).max
        if max_int > math.comb(n, n//2):
            dtype = 'uint64'
        else:
            dtype = object
    binomials = np.eye(n, dtype=dtype)
    binomials[:, 0] = 1
    for i in range(2, n):
        if i%2 == 0:
            k = i//2 + 1
        else:
            k = (i+1)//2
        for j in range(int(k)):
            binomials[i, j] = binomials[i, i-j] = binomials[i-1, j-1] + binomials[i-1, j]
    return binomials

def GammaBinomial(s, n):
    """Generalized binomial gamma function

    :param s:
    :type s:
    :param n:
    :type n:
    :return:
    :rtype:
    """
    g = math.gamma
    g1 = g(s+1)
    g2 = np.array([g(m+1)*g(s-m+1) for m in range(n)])
    g3 = g1/g2
    return g3

def Factorial(n):
    """I was hoping to do this in some built in way with numpy...but I guess it's not possible?
    looks like by default things don't vectorize and just call math.factorial

    :param n:
    :type n:
    :return:
    :rtype:
    """

    base = np.arange(n, dtype='uint64')
    base[0] = 1
    for i in range(1, n):
        base[i] = base[i]*base[i-1]
    return base


def _sieve_core(ints, k, max_its):
    sel = np.arange(ints.shape[0])
    counts = np.zeros(ints.shape[0], dtype=int)
    for i in range(max_its):
        mask = np.where(ints[sel,] % k == 0)
        if len(mask) == 0 or len(mask[0]) == 0:
            break

        sel = sel[mask[0],]
        counts[sel,] += 1
        ints[sel,] //= k
    return ints, counts
def prime_sieve(ints, k, max_its=None):
    ints = np.asanyarray(ints, dtype=int)
    smol = ints.ndim == 0
    if smol: ints = ints[np.newaxis]
    base_shape = ints.shape
    ints = ints.reshape(-1)

    if max_its is None:
        max_its = np.ceil(np.max(np.log(ints)/np.log(k))).astype(int)

    ints, counts = _sieve_core(ints, k, max_its)

    ints = ints.reshape(base_shape)
    counts = counts.reshape(base_shape)
    if smol:
        ints = ints[0]
        counts = counts[0]

    return ints, counts


def _prime_check(p2, prev_primes):
    return all(p2%pp > 0 for pp in prev_primes)

def prime_iter(primes=None):
    # we will very rarely exhaust these...
    if primes is None:
        primes = [2, 3, 5, 7, 11, 13, 17]
    else:
        primes = list(primes)
    for i in range(len(primes)):
        yield primes[:i+1]
    while True:
        p = primes[-1]
        for p2 in range(p+2, 2 * p, 2):
            if _prime_check(p2, primes[1:]):
                break
        else:
            raise ValueError("math broke")
        primes.append(p2)
        yield primes


def prime_list(n, base_primes=[], piter=prime_iter()):
    # gives a list up to the nth prime
    if n > len(base_primes):
        for p_list in piter:
            if len(p_list) > n:
                base_primes[:] = p_list
                break
    return base_primes[:n]

def prime_factorize(ints, primes=None):
    ints = np.array(ints, dtype=int)
    smol = ints.ndim == 0
    if smol: ints = ints[np.newaxis]
    base_shape = ints.shape
    ints = ints.reshape(-1)

    log_ints = np.log(ints)
    if primes is None:
        primes = prime_iter()

    sel = np.arange(ints.shape[0])
    max_prime = np.zeros(ints.shape[0], dtype=int)
    sel = sel[np.where(ints > 1)]
    count_list = []
    prime_list = []
    for p in primes:
        if isinstance(p, (int, np.integer)):
            prime_list.append(p)
        else:
            prime_list = p
            p = p[-1]

        max_its = np.ceil(np.max(log_ints/np.log(p))).astype(int)
        subints, subcounts = _sieve_core(ints[sel,], p, max_its)
        counts = np.zeros(ints.shape[0], dtype=int)
        counts[sel,] = subcounts
        count_list.append(counts)
        ints[sel,] = subints
        max_prime[sel,] += 1

        mask = np.where(subints > 1)
        if len(mask) == 0 or len(mask[0]) == 0:
            break
        sel = sel[mask]

    count_list = [c.reshape(base_shape) for c in count_list]
    if smol:
        count_list = [c[0] for c in count_list]

    return np.array(prime_list), count_list


def stable_factorial_ratio(num_terms, denom_terms, counts=None):
    if counts is None:
        num_terms, num_counts = np.unique(num_terms, return_counts=True)
        num_terms, counts_num = prime_factorize(num_terms)
        counts_num = np.tensordot(np.array(counts_num), num_counts, axes=[-1, 0])
        denom_terms, denom_counts = np.unique(denom_terms, return_counts=True)
        denom_terms, counts_denom = prime_factorize(denom_terms)
        counts_denom = np.tensordot(np.array(counts_denom), denom_counts, axes=[-1, 0])
    else:
        # we assume the primes are sorted
        counts_num, counts_denom = counts
        counts_num = np.asanyarray(counts_num)
        counts_denom = np.asanyarray(counts_denom)

    if len(num_terms) > len(denom_terms):
        primes = num_terms
        counts_denom = np.pad(counts_denom, [0, len(num_terms) - len(denom_terms)])
    elif len(num_terms) < len(denom_terms):
        primes = denom_terms
        counts_num = np.pad(counts_num, [0, len(denom_terms) - len(num_terms)])
    else:
        primes = num_terms

    exponent = counts_num - counts_denom
    if np.any(exponent < 0):
        exponent = exponent.astype(float)

    return np.prod(primes**exponent)