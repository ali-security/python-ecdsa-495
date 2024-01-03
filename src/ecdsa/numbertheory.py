#! /usr/bin/env python
#
# Provide some simple capabilities from number theory.
#
# Version of 2008.11.14.
#
# Written in 2005 and 2006 by Peter Pearson and placed in the public domain.
# Revision history:
#   2008.11.14: Use pow(base, exponent, modulus) for modular_exp.
#               Make gcd and lcm accept arbitrarily many arguments.

from __future__ import division

import sys
from six import integer_types, PY2
from six.moves import reduce

try:
    xrange
except NameError:
    xrange = range
try:
    from gmpy2 import powmod, mpz

    GMPY2 = True
    GMPY = False
except ImportError:  # pragma: no branch
    GMPY2 = False
    try:
        from gmpy import mpz

        GMPY = True
    except ImportError:
        GMPY = False


if GMPY2 or GMPY:  # pragma: no branch
    integer_types = tuple(integer_types + (type(mpz(1)),))


import math
import warnings
from .util import bit_length


class Error(Exception):
    """Base class for exceptions in this module."""

    pass


class JacobiError(Error):
    pass


class SquareRootError(Error):
    pass


class NegativeExponentError(Error):
    pass


def modular_exp(base, exponent, modulus):  # pragma: no cover
    """Raise base to exponent, reducing by modulus"""
    # deprecated in 0.14
    warnings.warn(
        "Function is unused in library code. If you use this code, "
        "change to pow() builtin.",
        DeprecationWarning,
    )
    if exponent < 0:
        raise NegativeExponentError(
            "Negative exponents (%d) not allowed" % exponent
        )
    return pow(base, exponent, modulus)


def polynomial_reduce_mod(poly, polymod, p):
    """Reduce poly by polymod, integer arithmetic modulo p.

    Polynomials are represented as lists of coefficients
    of increasing powers of x."""

    # This module has been tested only by extensive use
    # in calculating modular square roots.

    # Just to make this easy, require a monic polynomial:
    assert polymod[-1] == 1

    assert len(polymod) > 1

    while len(poly) >= len(polymod):
        if poly[-1] != 0:
            for i in xrange(2, len(polymod) + 1):
                poly[-i] = (poly[-i] - poly[-1] * polymod[-i]) % p
        poly = poly[0:-1]

    return poly


def polynomial_multiply_mod(m1, m2, polymod, p):
    """Polynomial multiplication modulo a polynomial over ints mod p.

    Polynomials are represented as lists of coefficients
    of increasing powers of x."""

    # This is just a seat-of-the-pants implementation.

    # This module has been tested only by extensive use
    # in calculating modular square roots.

    # Initialize the product to zero:

    prod = (len(m1) + len(m2) - 1) * [0]

    # Add together all the cross-terms:

    for i in xrange(len(m1)):
        for j in xrange(len(m2)):
            prod[i + j] = (prod[i + j] + m1[i] * m2[j]) % p

    return polynomial_reduce_mod(prod, polymod, p)


def polynomial_exp_mod(base, exponent, polymod, p):
    """Polynomial exponentiation modulo a polynomial over ints mod p.

    Polynomials are represented as lists of coefficients
    of increasing powers of x."""

    # Based on the Handbook of Applied Cryptography, algorithm 2.227.

    # This module has been tested only by extensive use
    # in calculating modular square roots.

    assert exponent < p

    if exponent == 0:
        return [1]

    G = base
    k = exponent
    if k % 2 == 1:
        s = G
    else:
        s = [1]

    while k > 1:
        k = k // 2
        G = polynomial_multiply_mod(G, G, polymod, p)
        if k % 2 == 1:
            s = polynomial_multiply_mod(G, s, polymod, p)

    return s


def jacobi(a, n):
    """Jacobi symbol"""

    # Based on the Handbook of Applied Cryptography (HAC), algorithm 2.149.

    # This function has been tested by comparison with a small
    # table printed in HAC, and by extensive use in calculating
    # modular square roots.

    if not n >= 3:
        raise JacobiError("n must be larger than 2")
    if not n % 2 == 1:
        raise JacobiError("n must be odd")
    a = a % n
    if a == 0:
        return 0
    if a == 1:
        return 1
    a1, e = a, 0
    while a1 % 2 == 0:
        a1, e = a1 // 2, e + 1
    if e % 2 == 0 or n % 8 == 1 or n % 8 == 7:
        s = 1
    else:
        s = -1
    if a1 == 1:
        return s
    if n % 4 == 3 and a1 % 4 == 3:
        s = -s
    return s * jacobi(n % a1, a1)


def square_root_mod_prime(a, p):
    """Modular square root of a, mod p, p prime."""

    # Based on the Handbook of Applied Cryptography, algorithms 3.34 to 3.39.

    # This module has been tested for all values in [0,p-1] for
    # every prime p from 3 to 1229.

    assert 0 <= a < p
    assert 1 < p

    if a == 0:
        return 0
    if p == 2:
        return a

    jac = jacobi(a, p)
    if jac == -1:
        raise SquareRootError("%d has no square root modulo %d" % (a, p))

    if p % 4 == 3:
        return pow(a, (p + 1) // 4, p)

    if p % 8 == 5:
        d = pow(a, (p - 1) // 4, p)
        if d == 1:
            return pow(a, (p + 3) // 8, p)
        assert d == p - 1
        return (2 * a * pow(4 * a, (p - 5) // 8, p)) % p

    if PY2:
        # xrange on python2 can take integers representable as C long only
        range_top = min(0x7FFFFFFF, p)
    else:
        range_top = p
    for b in xrange(2, range_top):  # pragma: no branch
        if jacobi(b * b - 4 * a, p) == -1:
            f = (a, -b, 1)
            ff = polynomial_exp_mod((0, 1), (p + 1) // 2, f, p)
            if ff[1]:
                raise SquareRootError("p is not prime")
            return ff[0]
    # just an assertion
    raise RuntimeError("No b found.")  # pragma: no cover


# because all the inverse_mod code is arch/environment specific, and coveralls
# expects it to execute equal number of times, we need to waive it by
# adding the "no branch" pragma to all branches
if GMPY2:  # pragma: no branch

    def inverse_mod(a, m):
        """Inverse of a mod m."""
        if a == 0:  # pragma: no branch
            return 0
        return powmod(a, -1, m)

elif GMPY:  # pragma: no branch

    def inverse_mod(a, m):
        """Inverse of a mod m."""
        # while libgmp does support inverses modulo, it is accessible
        # only using the native `pow()` function, and `pow()` in gmpy sanity
        # checks the parameters before passing them on to underlying
        # implementation
        if a == 0:  # pragma: no branch
            return 0
        a = mpz(a)
        m = mpz(m)

        lm, hm = mpz(1), mpz(0)
        low, high = a % m, m
        while low > 1:  # pragma: no branch
            r = high // low
            lm, low, hm, high = hm - lm * r, high - low * r, lm, low

        return lm % m

elif sys.version_info >= (3, 8):  # pragma: no branch

    def inverse_mod(a, m):
        """Inverse of a mod m."""
        if a == 0:  # pragma: no branch
            return 0
        return pow(a, -1, m)

else:  # pragma: no branch

    def inverse_mod(a, m):
        """Inverse of a mod m."""

        if a == 0:  # pragma: no branch
            return 0

        lm, hm = 1, 0
        low, high = a % m, m
        while low > 1:  # pragma: no branch
            r = high // low
            lm, low, hm, high = hm - lm * r, high - low * r, lm, low

        return lm % m


try:
    gcd2 = math.gcd
except AttributeError:

    def gcd2(a, b):
        """Greatest common divisor using Euclid's algorithm."""
        while a:
            a, b = b % a, a
        return b


def gcd(*a):
    """Greatest common divisor.

    Usage: gcd([ 2, 4, 6 ])
    or:    gcd(2, 4, 6)
    """

    if len(a) > 1:
        return reduce(gcd2, a)
    if hasattr(a[0], "__iter__"):
        return reduce(gcd2, a[0])
    return a[0]


def lcm2(a, b):
    """Least common multiple of two integers."""

    return (a * b) // gcd(a, b)


def lcm(*a):
    """Least common multiple.

    Usage: lcm([ 3, 4, 5 ])
    or:    lcm(3, 4, 5)
    """

    if len(a) > 1:
        return reduce(lcm2, a)
    if hasattr(a[0], "__iter__"):
        return reduce(lcm2, a[0])
    return a[0]


def factorization(n):
    """Decompose n into a list of (prime,exponent) pairs."""

    assert isinstance(n, integer_types)

    if n < 2:
        return []

    result = []

    # Test the small primes:

    for d in smallprimes:
        if d > n:
            break
        q, r = divmod(n, d)
        if r == 0:
            count = 1
            while d <= n:  # pragma: no branch
                n = q
                q, r = divmod(n, d)
                if r != 0:
                    break
                count = count + 1
            result.append((d, count))

    # If n is still greater than the last of our small primes,
    # it may require further work:

    if n > smallprimes[-1]:
        if is_prime(n):  # If what's left is prime, it's easy:
            result.append((n, 1))
        else:  # Ugh. Search stupidly for a divisor:
            d = smallprimes[-1]
            while 1:
                d = d + 2  # Try the next divisor.
                q, r = divmod(n, d)
                if q < d:  # n < d*d means we're done, n = 1 or prime.
                    break
                if r == 0:  # d divides n. How many times?
                    count = 1
                    n = q
                    # As long as d might still divide n,
                    while d <= n:  # pragma: no branch
                        q, r = divmod(n, d)  # see if it does.
                        if r != 0:
                            break
                        n = q  # It does. Reduce n, increase count.
                        count = count + 1
                    result.append((d, count))
            if n > 1:
                result.append((n, 1))

    return result


def phi(n):  # pragma: no cover
    """Return the Euler totient function of n."""
    # deprecated in 0.14
    warnings.warn(
        "Function is unused by library code. If you use this code, "
        "please open an issue in "
        "https://github.com/tlsfuzzer/python-ecdsa",
        DeprecationWarning,
    )

    assert isinstance(n, integer_types)

    if n < 3:
        return 1

    result = 1
    ff = factorization(n)
    for f in ff:
        e = f[1]
        if e > 1:
            result = result * f[0] ** (e - 1) * (f[0] - 1)
        else:
            result = result * (f[0] - 1)
    return result


def carmichael(n):  # pragma: no cover
    """Return Carmichael function of n.

    Carmichael(n) is the smallest integer x such that
    m**x = 1 mod n for all m relatively prime to n.
    """
    # deprecated in 0.14
    warnings.warn(
        "Function is unused by library code. If you use this code, "
        "please open an issue in "
        "https://github.com/tlsfuzzer/python-ecdsa",
        DeprecationWarning,
    )

    return carmichael_of_factorized(factorization(n))


def carmichael_of_factorized(f_list):  # pragma: no cover
    """Return the Carmichael function of a number that is
    represented as a list of (prime,exponent) pairs.
    """
    # deprecated in 0.14
    warnings.warn(
        "Function is unused by library code. If you use this code, "
        "please open an issue in "
        "https://github.com/tlsfuzzer/python-ecdsa",
        DeprecationWarning,
    )

    if len(f_list) < 1:
        return 1

    result = carmichael_of_ppower(f_list[0])
    for i in xrange(1, len(f_list)):
        result = lcm(result, carmichael_of_ppower(f_list[i]))

    return result


def carmichael_of_ppower(pp):  # pragma: no cover
    """Carmichael function of the given power of the given prime."""
    # deprecated in 0.14
    warnings.warn(
        "Function is unused by library code. If you use this code, "
        "please open an issue in "
        "https://github.com/tlsfuzzer/python-ecdsa",
        DeprecationWarning,
    )

    p, a = pp
    if p == 2 and a > 2:
        return 2 ** (a - 2)
    else:
        return (p - 1) * p ** (a - 1)


def order_mod(x, m):  # pragma: no cover
    """Return the order of x in the multiplicative group mod m."""
    # deprecated in 0.14
    warnings.warn(
        "Function is unused by library code. If you use this code, "
        "please open an issue in "
        "https://github.com/tlsfuzzer/python-ecdsa",
        DeprecationWarning,
    )

    # Warning: this implementation is not very clever, and will
    # take a long time if m is very large.

    if m <= 1:
        return 0

    assert gcd(x, m) == 1

    z = x
    result = 1
    while z != 1:
        z = (z * x) % m
        result = result + 1
    return result


def largest_factor_relatively_prime(a, b):  # pragma: no cover
    """Return the largest factor of a relatively prime to b."""
    # deprecated in 0.14
    warnings.warn(
        "Function is unused by library code. If you use this code, "
        "please open an issue in "
        "https://github.com/tlsfuzzer/python-ecdsa",
        DeprecationWarning,
    )

    while 1:
        d = gcd(a, b)
        if d <= 1:
            break
        b = d
        while 1:
            q, r = divmod(a, d)
            if r > 0:
                break
            a = q
    return a


def kinda_order_mod(x, m):  # pragma: no cover
    """Return the order of x in the multiplicative group mod m',
    where m' is the largest factor of m relatively prime to x.
    """
    # deprecated in 0.14
    warnings.warn(
        "Function is unused by library code. If you use this code, "
        "please open an issue in "
        "https://github.com/tlsfuzzer/python-ecdsa",
        DeprecationWarning,
    )

    return order_mod(x, largest_factor_relatively_prime(m, x))


def is_prime(n):
    """Return True if x is prime, False otherwise.

    We use the Miller-Rabin test, as given in Menezes et al. p. 138.
    This test is not exact: there are composite values n for which
    it returns True.

    In testing the odd numbers from 10000001 to 19999999,
    about 66 composites got past the first test,
    5 got past the second test, and none got past the third.
    Since factors of 2, 3, 5, 7, and 11 were detected during
    preliminary screening, the number of numbers tested by
    Miller-Rabin was (19999999 - 10000001)*(2/3)*(4/5)*(6/7)
    = 4.57 million.
    """

    # (This is used to study the risk of false positives:)
    global miller_rabin_test_count

    miller_rabin_test_count = 0

    if n <= smallprimes[-1]:
        if n in smallprimes:
            return True
        else:
            return False
    # 2310 = 2 * 3 * 5 * 7 * 11
    if gcd(n, 2310) != 1:
        return False

    # Choose a number of iterations sufficient to reduce the
    # probability of accepting a composite below 2**-80
    # (from Menezes et al. Table 4.4):

    t = 40
    n_bits = 1 + bit_length(n)
    for k, tt in (
        (100, 27),
        (150, 18),
        (200, 15),
        (250, 12),
        (300, 9),
        (350, 8),
        (400, 7),
        (450, 6),
        (550, 5),
        (650, 4),
        (850, 3),
        (1300, 2),
    ):
        if n_bits < k:
            break
        t = tt

    # Run the test t times:

    s = 0
    r = n - 1
    while (r % 2) == 0:
        s = s + 1
        r = r // 2
    for i in xrange(t):
        a = smallprimes[i]
        y = pow(a, r, n)
        if y != 1 and y != n - 1:
            j = 1
            while j <= s - 1 and y != n - 1:
                y = pow(y, 2, n)
                if y == 1:
                    miller_rabin_test_count = i + 1
                    return False
                j = j + 1
            if y != n - 1:
                miller_rabin_test_count = i + 1
                return False
    return True


def next_prime(starting_value):
    """Return the smallest prime larger than the starting value."""

    if starting_value < 2:
        return 2
    result = (starting_value + 1) | 1
    while not is_prime(result):
        result = result + 2
    return result


smallprimes = [
    2,
    3,
    5,
    7,
    11,
    13,
    17,
    19,
    23,
    29,
    31,
    37,
    41,
    43,
    47,
    53,
    59,
    61,
    67,
    71,
    73,
    79,
    83,
    89,
    97,
    101,
    103,
    107,
    109,
    113,
    127,
    131,
    137,
    139,
    149,
    151,
    157,
    163,
    167,
    173,
    179,
    181,
    191,
    193,
    197,
    199,
    211,
    223,
    227,
    229,
    233,
    239,
    241,
    251,
    257,
    263,
    269,
    271,
    277,
    281,
    283,
    293,
    307,
    311,
    313,
    317,
    331,
    337,
    347,
    349,
    353,
    359,
    367,
    373,
    379,
    383,
    389,
    397,
    401,
    409,
    419,
    421,
    431,
    433,
    439,
    443,
    449,
    457,
    461,
    463,
    467,
    479,
    487,
    491,
    499,
    503,
    509,
    521,
    523,
    541,
    547,
    557,
    563,
    569,
    571,
    577,
    587,
    593,
    599,
    601,
    607,
    613,
    617,
    619,
    631,
    641,
    643,
    647,
    653,
    659,
    661,
    673,
    677,
    683,
    691,
    701,
    709,
    719,
    727,
    733,
    739,
    743,
    751,
    757,
    761,
    769,
    773,
    787,
    797,
    809,
    811,
    821,
    823,
    827,
    829,
    839,
    853,
    857,
    859,
    863,
    877,
    881,
    883,
    887,
    907,
    911,
    919,
    929,
    937,
    941,
    947,
    953,
    967,
    971,
    977,
    983,
    991,
    997,
    1009,
    1013,
    1019,
    1021,
    1031,
    1033,
    1039,
    1049,
    1051,
    1061,
    1063,
    1069,
    1087,
    1091,
    1093,
    1097,
    1103,
    1109,
    1117,
    1123,
    1129,
    1151,
    1153,
    1163,
    1171,
    1181,
    1187,
    1193,
    1201,
    1213,
    1217,
    1223,
    1229,
]

miller_rabin_test_count = 0
