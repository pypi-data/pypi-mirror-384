"""
Polynomials
"""

from math import prod, comb
from numbers import Number
from random import randint
from itertools import combinations
from copy import copy
from .Zmod import Zmod
from .nt import crt

class Poly:
    """
    Represents a polynomial as a list of coefficients.

    Example:

    To define a polynomial as a list of coefficients use
    >>> Poly([1, 2, 3])
    3 x^2 + 2 x + 1
    """

    print_reversed = True  # print the terms in reversed order
    print_latex = False  # print in latex format
    print_x = "x"  # variable for printing
    print_pow = "^"  # you can change this to "**" if you want it python style

    def __init__(self, coeff: list, ring=None, modulus: list = None, cyclic: int = 0, check: bool = True):
        if not check:
            self.coeff = coeff
            self.modulus = modulus
            self.cyclic = cyclic
            return
        if ring:
            self.coeff = list(map(ring, coeff))
        else:
            self.coeff = list(coeff)
        if len(self.coeff) < 1:
            raise ValueError("The coefficient list must not be empty.")
        self.strip()
        self.modulus = None
        if isinstance(cyclic, int):
            if cyclic > 0:
                modulus = [-1] + [0] * (cyclic - 1) + [1]  # x^n - 1
            elif cyclic < 0:
                modulus = [1] + [0] * (-cyclic - 1) + [1]  # x^n + 1
        else:
            cyclic = 0
        self.cyclic = cyclic
        if modulus is None:
            return
        if ring:
            self.modulus = list(map(ring, modulus))
        else:
            self.modulus = list(modulus)
        if len(self.modulus) < 2:
            raise ValueError("The modulus must have degree at least one.")
        zero = self.coeff[0] * 0
        one = zero**0
        if self.modulus[-1] != one:
            try:
                tmp = one / self.modulus[-1]
            except Exception as exc:
                raise ValueError("Failed to make the modulus monic.") from exc
            for i in range(len(self.modulus)):  # pylint: disable=C0200
                self.modulus[i] *= tmp
        if all( c == zero for c in self.modulus[1:-1]):
            if self.modulus[0] == one:
                self.cyclic = 1 - len(self.modulus)
            elif self.modulus[0]**2 == one:
                self.cyclic = len(self.modulus) - 1
        self.mod()

    def __call__(self, x):
        result = 0 * self.coeff[0]
        if not type(x) == type(result):  # pylint: disable=C0123
            raise ValueError(
                "Evaluation point must be an element of the ring.")
        # Horner's method
        for c in reversed(self.coeff):
            result = result * x + c
        return result

    def __getitem__(self, item):
        if item >= len(self.coeff):
            return self.coeff[0] * 0
        return self.coeff[item]

    def __setitem__(self, item, value):
        if item >= len(self.coeff):
            zero = self.coeff[0] * 0
            self.coeff += [zero] * (item - len(self.coeff) + 1)
        self.coeff[item] = value

    def __iter__(self):
        yield from self.coeff

    def __len__(self):
        return len(self.coeff)

    def __hash__(self):
        return hash(tuple(self.coeff))

    def __repr__(self, latex=None):
        def prx(i: int) -> str:
            if i == 0:
                return ""
            if i == 1:
                return self.__class__.print_x
            if latex:
                if i < 10:
                    return self.__class__.print_x + "^" + str(i)
                return self.__class__.print_x + "^{" + str(i) + "}"
            return self.__class__.print_x + self.__class__.print_pow + str(i)

        if latex is None:
            latex = self.__class__.print_latex
        if not self:
            return str(self.coeff[0])
        one = self.coeff[0]**0
        plus = ""
        tmp = ""
        coef_range = range(len(self.coeff))
        if self.__class__.print_reversed:
            coef_range = reversed(coef_range)
        for i in coef_range:
            s = self.coeff[i]
            if not s:
                continue
            if not s - one and i != 0:
                tmp += plus + prx(i)
                plus = " + "
                continue
            try:
                if not s + one and i != 0:
                    if plus:
                        plus = " "
                    tmp += plus + "- " + prx(i)
                    plus = " + "
                    continue
            except:  # pylint: disable=W0702
                pass
            try:
                if plus and s < 0:
                    tmp += " - " + str(-s)
                    if i != 0:
                        tmp += " " + prx(i)
                    continue
            except:  # pylint: disable=W0702
                pass
            tmp += plus + str(s)
            if i != 0:
                tmp += " " + prx(i)
            plus = " + "
        return tmp.strip()

    def _repr_mimebundle_(self, **kwargs):  # pylint: disable=W0613
        return {
            "text/plain": repr(self),
            "text/latex": "$" + self.__repr__(latex=True) + "$"  # pylint: disable=C2801
        }

    def __int__(self):
        _, _, ring = self._guess_ring()
        if not ring:
            raise ValueError(
                "The polynomial does not seem to be over a known finite ring.")
        if hasattr(ring, 'n'):  # Zmod
            n = ring.n
        else:  # G2 or galois
            n = ring.order
        result = 0
        # Horner's method
        for c in reversed(self.coeff):
            result = result * n + int(c)
        return result

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return not bool(self - other)

    def __bool__(self):
        return bool(self.degree()) or bool(self.coeff[0])

    def strip(self) -> None:
        "Strip leading zeros."
        for i in range(len(self.coeff) - 1, 0, -1):
            if self.coeff[i]:
                break
            self.coeff.pop(i)

    def degree(self) -> int:
        "Return the degree."
        return len(self.coeff) - 1

    def weight(self) -> int:
        "Return the number of nonzero coefficients."
        return sum(map(bool,self.coeff))

    def map(self, func, modulus = True):
        "Apply a given function to all coefficients in place."
        self.coeff = list(map(func, self.coeff))
        self.strip()
        if modulus and self.modulus is not None:
            self.modulus = list(map(func, self.modulus))
            if self.modulus[-1] != self.coeff[0]**0:
                raise ValueError("The modulus is no longer monic.")
            if self.cyclic:
                zero = self.modulus[0] * 0
                self.cyclic = 0
                if abs(self.cyclic) > 1 and self.modulus[1] != zero:
                    return
                one = zero**0
                if self.modulus[0] == one:
                    self.cyclic = 1 - len(self.modulus)
                elif self.modulus[0]**2 == one:
                    self.cyclic = len(self.modulus) - 1

    def applyfunc(self, func, modulus = True) -> "Poly":
        "Apply a function to all coefficients."
        if modulus and self.modulus is not None:
            return self.__class__(list(map(func, self.coeff)), modulus = list(map(func, self.modulus)))
        return self.__class__(list(map(func, self.coeff)), modulus = self.modulus, cyclic = self.cyclic)

    def _check_type(self, other):
        return isinstance(other, int) or (isinstance(other, Number) and isinstance(self.coeff[0], Number)) or type(other) == type(self.coeff[0])  # pylint: disable=C0123

    def _guess_ring(self):
        zero = 0 * self.coeff[0]
        one = zero**0
        if hasattr(zero, "ring"):
            ring = zero.ring  # Zmod
        elif hasattr(zero, "field"):
            ring = zero.field  # GF2
        elif hasattr(type(zero), "order"):
            ring = type(zero)  # galois
        else:
            ring = None
        return zero, one, ring

    def _guess_field(self):
        zero, one, field = self._guess_ring()
        if not field:
            raise ValueError(
                "The polynomial does not seem to be over a known finite field.")
        if hasattr(field, 'n'):  # Zmod
            p = field.n
            q = field.n
            if not field.is_field():
                raise ValueError(
                    "The polynomial does not seem to be over a finite field.")
        else:  # G2 or galois
            p = field.characteristic
            q = field.order
        return field, zero, one, q, p

    def __add__(self, other: "Poly") -> "Poly":
        if not isinstance(other, self.__class__):
            if self._check_type(other):
                tmp = self.coeff[:]
                tmp[0] += other
                return self.__class__(tmp, modulus = self.modulus, check = False)
            return NotImplemented
        modulus = self.modulus
        cyclic = self.cyclic
        if modulus is None and other.modulus is not None:
            modulus = other.modulus
            cyclic = other.cyclic
        ls, lo = len(self.coeff), len(other.coeff)
        if ls < lo:
            ret = [s + o for s, o in zip(self.coeff, other.coeff)] + other.coeff[ls:]
        else:
            ret = [s + o for s, o in zip(self.coeff, other.coeff)] + self.coeff[lo:]
        ret = self.__class__(ret, modulus = modulus, cyclic = cyclic, check = False)
        ret.strip()
        return ret

    def __radd__(self, other: "Poly") -> "Poly":
        return self + other

    def __neg__(self) -> "Poly":
        return self.__class__([-s for s in self.coeff], modulus = self.modulus, cyclic = self.cyclic, check = False)

    def __pos__(self) -> "Poly":
        return self

    def __sub__(self, other: "Poly") -> "Poly":
        return self + (- other)

    def __rsub__(self, other: "Poly") -> "Poly":
        return (- self) + other

    def __mul__(self, other: "Poly") -> "Poly":
        if not isinstance(other, self.__class__):
            if self._check_type(other):
                if not other:
                    return self.__class__([other], modulus = self.modulus, cyclic = self.cyclic, check = False)
                return self.__class__([other * s for s in self.coeff], modulus = self.modulus, cyclic = self.cyclic, check = False)
            return NotImplemented
        zero = 0 * self.coeff[0]
        ls, lo = len(self.coeff), len(other.coeff)
        if self.cyclic or other.cyclic:
            if self.cyclic:
                cyclic = self.cyclic
                modulus = self.modulus
            else:
                cyclic = other.cyclic
                modulus = other.modulus
            n = abs(cyclic)
            if ls < lo:
                otherc = other.coeff + [zero] * (n - lo)
                selfc = self.coeff
            else:
                otherc = self.coeff + [zero] * (n - ls)
                selfc = other.coeff
                ls = lo
            if cyclic > 0:
                coeff = [ sum( (selfc[j] * otherc[(k-j) % n] for j in range(ls)), start = zero) for k in range(n)]
            else:
                coeff = [ sum( (selfc[j] * otherc[(k-j) % n] for j in range(min(k,ls))), start = zero) -
                          sum( (selfc[j] * otherc[(k-j) % n] for j in range(k,ls)), start = zero) for k in range(n)]
            ret = self.__class__(coeff, modulus = modulus, cyclic = cyclic, check = False)
            ret.strip()
            return ret
        coeff = [sum((self.coeff[j] * other.coeff[k - j] for j in range(max(0, k - lo + 1), min(ls, k + 1))), start=zero)
                     for k in range(ls + lo - 1)]
        modulus = self.modulus
        if not modulus and other.modulus:
            modulus = other.modulus
        ret = self.__class__(coeff, modulus = modulus, check = False)
        ret.mod()
        return ret

    def __rmul__(self, other) -> "Poly":
        return self * other

    def __truediv__(self, other) -> "Poly":
        if self._check_type(other):
            return self.__class__([s / other for s in self.coeff], modulus = self.modulus, cyclic = self.cyclic, check = False)
        if isinstance(other, self.__class__):
            if not other.modulus:
                raise NotImplementedError(
                    "Cannot invert polynomials without modulus.")
            return self * other.inv()
        return NotImplemented

    def __rtruediv__(self, other) -> "Poly":
        if not self.modulus:
            raise NotImplementedError(
                "Cannot invert polynomials without modulus.")
        return other * self.inv()

    def __pow__(self, j: int) -> "Poly":
        if not isinstance(j, int):
            return NotImplemented
        one = self.coeff[0]**0
        res = self.__class__([one], modulus = self.modulus, cyclic = self.cyclic, check = False)
        if j < 0:
            if not self.modulus:
                raise NotImplementedError(
                    "Cannot divide polynomials without modulus.")
            tmp = self.inv()
            j *= -1
        else:
            tmp = self
        while j > 0:
            # If j is odd, multiply
            if j & 1:
                res *= tmp
            # Now square
            j = j >> 1  # j= j//2
            tmp *= tmp
        return res

    def bits(self) -> list[int]:
        "List of bits of all coefficients."
        ring = self.coeff[0].__class__
        if not (hasattr(ring, 'bits') and callable(ring.bits)):
            raise NotImplementedError("Coefficients cannot be converted to bits.")
        out = []
        for c in reversed(self.coeff):
            out += c.bits()
        return out

    def max(self) -> int:
        "Maximum of the absolute value of all coefficients."
        return max(abs(c) for c in self.coeff)

    def sum(self) -> int:
        "Sum of the absolute value of all coefficients."
        return sum(abs(c) for c in self.coeff)

    def __floordiv__(self, other: "Poly") -> "Poly":
        return self.divmod(other)[0]

    def __mod__(self, other: "Poly") -> "Poly":
        return self.divmod(other)[1]

    def divmod(self, other: "Poly") -> ("Poly", "Poly"):
        "Polynom division with remainder."
        zero, one, ring = self._guess_ring()
        if isinstance(other, list):
            other = self.__class__(other, ring)
        elif not isinstance(other, self.__class__):
            raise NotImplementedError(f"Cannot divide {self} and {other}.")
        if not other:
            raise ValueError(f"{other} must be nonzero.")
        sd, od = self.degree(), other.degree()
        if sd < od:
            return self.__class__([zero], check = False), self
        div = [zero] * (sd - od + 1)
        lco = other.coeff[-1]
        if lco != one:
            try:
                tmp = one / lco
            except Exception as exc:
                raise ValueError("The leading coefficient of the divisor must be invertible.") from exc
            oth = [c * tmp for c in other.coeff]
            rem = [c * tmp for c in self.coeff]
        else:
            oth = other.coeff
            rem = [c * one for c in self.coeff]  # "* 1" is here to make sure we get a copy
        for i in range(sd - od + 1):
            tmp = rem[sd - i] * one  # "* 1" is here to make sure we get a copy
            div[sd - od - i] = tmp
            for j in range(od + 1):
                rem[sd - i - j] -= tmp * oth[od - j]
        if lco != one:
            rem = [c * lco for c in rem]
        return self.__class__(div), self.__class__(rem)

    def mod(self, other: "Poly" = None) -> None:
        "Reduce with respect to a given polynomial."
        one, ring = self._guess_ring()[1:]
        if other is None:
            if self.modulus is None or len(self.coeff) < len(self.modulus):
                return
            if self.cyclic:
                n = abs(self.cyclic)
                zero = self.coeff[0] * 0
                if self.cyclic > 0:
                    self.coeff = [ sum(self.coeff[i::n], start = zero) for i in range(n)]
                else:
                    even = [ sum(self.coeff[i::2*n], start = zero) for i in range(n)]
                    odd = [ sum(self.coeff[i+n::2*n], start = zero) for i in range(n)]
                    self.coeff = [ c1 - c2 for c1, c2 in zip(even, odd)]
                self.strip()
                return
            oth = self.modulus
        else:
            if isinstance(other, list):
                other = self.__class__(other, ring=ring)
            elif not isinstance(other, self.__class__):
                raise NotImplementedError(f"Cannot divide {self} and {other}.")
            if not other:
                raise NotImplementedError(f"{other} must be nonzero.")
            oth = other.coeff
            if len(self.coeff) < len(oth):
                return
            lco = oth[-1]
            if lco != one:
                tmp = one / lco
                oth = [c * tmp for c in oth]
        sd, od = len(self.coeff) - 1, len(oth) - 1
        for i in range(sd - od + 1):
            tmp = self.coeff[sd - i] * one  # "* 1" is here to make sure we get a copy
            for j in range(od + 1):
                self.coeff[sd - i - j] -= tmp * oth[od - j]
        for i in range(len(self.coeff) - 1, 0, -1):  # strip leading zeros
            if self.coeff[i]:
                break
            self.coeff.pop(i)

    def inv(self, other: "Poly" = None) -> "Poly":
        "Inverse modulo a given polynomial."
        if not other:
            other = self.modulus
        zero, one, ring = self._guess_ring()
        if isinstance(other, self.__class__):
            other = other.coeff
        elif not isinstance(other, list):
            raise NotImplementedError(
                f"{other} must be a list of coefficients or a polynomial.")
        other = self.__class__(other, ring=ring)
        if not other:
            raise NotImplementedError(f"{other} must be nonzero.")
        if ring is not None and hasattr(ring, 'n') and not ring.is_field():  # Zmod; no field
            inverse = [] # inverse in Z_{p^k} for all primefactors of n
            primefactors = [] # primefactors of n
            for p, k in ring.factor_n().items():
                primefactors.append(p**k)
                self_p = copy(self)
                Z_p = Zmod(p)
                Z_p.isfield = True
                self_p.map(Z_p)
                self_p_inv = self_p.inv()
                if k > 1:
                    self_p = copy(self)
                    self_p.map(Zmod(p**k))
                    self_p_inv.map(Zmod(p**k))
                    l = 1
                    while k > l:
                        self_p_inv = self_p_inv * (2 - self_p * self_p_inv)
                        l *=2
                inverse.append(self_p_inv)

            coeff = []
            for i in range(other.degree()):
                coeff.append(crt([int(inv[i]) for inv in inverse], primefactors))
            ret = self.__class__(coeff, ring=ring)
            ret.modulus = self.modulus
            return ret
        r0, r1 = other, self
        y0, y1 = self.__class__([zero], check = False), self.__class__([one], check = False)
        while r1:
            q, r = r0.divmod(r1)
            r0, r1 = r1, r
            y0, y1 = y1, y0 - q * y1
        if r0.degree() != 0:
            raise ValueError(f"{self} is not invertible mod {other}.")
        y0.modulus = self.modulus
        if r0.coeff[0] == one:
            return y0
        return y0 / r0.coeff[0]

    def gcd(self, other: "Poly") -> "Poly":
        "Greates common divisor with a given polynomial."
        if not isinstance(other, self.__class__):
            raise NotImplementedError(f"Cannot compute gcd: {other} must be a polynomial.")
        _, one, _ = self._guess_ring()
        if not self:
            if not other:
                return self.__class__([self.coeff[0]], check = False)
            tmp = other / other.coeff[-1]
            tmp.modulus = None
            return tmp
        r0, r1 = other, self
        while r1:
            r0, r1 = r1, r0.divmod(r1)[1]
        r0.modulus = None
        if r0.coeff[-1] == one:
            return r0
        return r0 / r0.coeff[-1]

    def lcm(self, other: "Poly") -> "Poly":
        "Least common multiple with a given polynomial."
        return self * other // self.gcd(other)

    def egcd(self, other: "Poly") -> ("Poly", "Poly", "Poly"):
        """Perform the extended Euclidean agorithm for polynomials. Returns gcd, x, y such that other * x + self * y = gcd."""
        zero, one, _ = self._guess_ring()
        if not isinstance(other, self.__class__):
            raise NotImplementedError(f"Cannot perform egcd: {other} must be a polynomial.")
        if not self:
            if not other:
                return self.__class__([zero], check = False), self.__class__([zero], check = False), self.__class__([zero], check = False)
            if other.coeff[-1] == one:
                return other, self.__class__([zero], check = False), self.__class__([one], check = False)
            return other / other.coeff[-1], __class__([zero], check = False), self.__class__([one / other.coeff[-1]], check = False)
        r0, r1 = other, self
        x0, x1 = self.__class__([one], check = False), self.__class__([zero], check = False)
        y0, y1 = x1, x0
        while r1:
            q, r = r0.divmod(r1)
            r0, r1 = r1, r
            x0, x1 = x1, x0 - x1 * q
            y0, y1 = y1, y0 - y1 * q
        lcr0 = r0.coeff[-1]
        if lcr0 == one:
            return r0, x0, y0
        return r0 / lcr0, x0 / lcr0, y0 / lcr0

    def derivative(self) -> "Poly":
        "Returns the formal derivative."
        l = len(self.coeff)
        if l == 1:
            tmp = 0 * self.coeff[0]
        else:
            tmp = [j * self.coeff[j] for j in range(1, l)]
        ret = self.__class__(tmp, modulus = self.modulus, check = False)
        ret.strip()
        return ret

    def reciprocal(self) -> "Poly":
        "Returns the reciprocal (reversed) polynomial."
        ret = self.__class__(reversed(self.coeff), modulus = self.modulus, check = False)
        ret.strip()
        return ret

    def square_free_factors(self) -> dict:
        "Determine the square free factors of a polynomial over a Galois field."
        _, zero, _, q, p = self._guess_field()
        pr = q // p  # x^pr will be the p'th root of x
        if self.degree() < 1:
            return {}
        if self.degree() == 1:
            return {self / self.coeff[-1]: 1}
        factors = {}
        w = self / self.coeff[-1]
        c = w.gcd(w.derivative())
        w = w // c

        # first we find all factors which are not a power of p
        i = 1
        while w.degree() > 0:
            y = w.gcd(c)
            fac = w // y
            if fac.degree() > 0:
                factors[fac] = i
            w = y
            c //= y
            i += 1
        # c is now a power of p
        if c.degree() > 0:
            # compute the p'th root of c
            d = c.degree() // p
            root = [zero] * (d + 1)
            while d >= 0:
                root[d] = c.coeff[d * p]**pr
                d -= 1
            # assert Poly(root)**p == c, root
            for fac, mult in self.__class__(root).square_free_factors().items():
                factors[fac] = p * mult
        return factors

    def is_square_free(self) -> bool:
        "Test if the polynomial over a Galois field is square free."
        multiplicities = self.square_free_factors().values()
        return len(multiplicities) == 1 and multiplicities[0] == 1

    def distinct_degree_factors(self, test: bool = False) -> bool | dict:
        "Factors the polynomial over a Galois field into distinct products of irredicible factors of the same degree."
        _, zero, one, q, _ = self._guess_field()
        if self.degree() < 1:
            raise ValueError("The polynomial must be non-constant.")
        factors = {}
        w = self
        x = self.__class__([zero, one], modulus = self.coeff, check = False)  # x
        b = x
        k = 1
        while k <= w.degree()//2:
            b **= q  # we compute x^{q^k} mod a recursively
            g = w.gcd(b - x)  # gcd with x^{q^k} - x
            if g.degree():
                if test:
                    return False
                factors[k] = g
                w = w // factors[k]
            k += 1
        if test:
            return True
        if w.degree() > 0:
            factors[w.degree()] = w
        return factors

    def rabin_test(self) -> bool:
        "Determine if a polynomial is irreducible over a Galois field using a Rabin test."
        return self.distinct_degree_factors(test=True)

    def is_irreducible(self) -> bool:
        "Test if the polynomial over a Galois field is irreducibel."
        if self.degree() == 0:
            return False
        return self.distinct_degree_factors(test=True)

    def equal_degree_factors(self, k: int) -> list:
        "Factors a square free product of irreducibel polynomials of degree `k` over a Galois field."
        field, _, one, q, p = self._guess_field()
        if hasattr(field, "degree"):
            degree = field.degree
        else:
            degree = 1
        d = self.degree()
        if not isinstance(k, int) or k < 1:
            raise ValueError(f"The degree {k} must be a positive integer.")
        if d < k or d % k:
            raise ValueError(
                f"The polynomial is no product of irreducibel polynomials of degree {k}.")
        r = d // k
        qk = (q**k - 1) // 2

        factors = [self]
        while len(factors) < r:
            g = self.__class__([field(randint(0, q-1)) for _ in range(d+1)], modulus = self.coeff)
            if p == 2:  # Gathen-Shoup
                h = g
                for _ in range(1, k):
                    g += h**q
                if degree > 1:
                    h = g
                    for _ in range(1, degree):
                        g += g**2
            else:  # Cantor–Zassenhaus
                g = g**qk - one
            factors2 = []  # list for the next round (to avoid the the new factors are tested a second time with the same g)
            for fac in factors:
                if fac.degree() == k:  # this one is already irreducible
                    factors2.append(fac)
                    continue
                gg = fac.gcd(g)
                if gg.degree() == 0 or gg.degree() == fac.degree():  # trivial factor
                    factors2.append(fac)
                    continue
                gg.modulus = None
                factors2.append(gg)
                factors2.append(fac // gg)
            factors = factors2
        return factors

    def factor(self) -> dict:
        "Factors a polynomials over a Galois field."
        if self.degree() < 1:
            return {self: 1}
        c = self.coeff[-1]
        one = c**0
        if c != one:
            factors = {self.__class__([c], check = False): 1}
        else:
            factors = {}
        for fac1, m in self.square_free_factors().items():
            for k, fac2 in fac1.distinct_degree_factors().items():
                if k == fac2.degree():  # irreducible
                    factors[fac2] = m
                else:
                    for fac3 in fac2.equal_degree_factors(k):
                        factors[fac3] = m
        return dict(sorted(factors.items(), key=lambda item: item[0].degree()))


class PolyBinMult():
    """
    Represents a binary multivariate polynomial as a list of monomials.

    Example:

    To define a polynomial in 3 variable by a list of coefficients use
    >>> PolyBinMult([0, 1,0,1, 1,0,1, 1], 3)
    x_0 + x_2 + x_0 x_1 + x_1 x_2 + x_0 x_1 x_2
    """

    print_latex = False  # print in latex format
    print_x = "x"  # variable for printing

    def __init__(self, c: list, m:int) -> list:
        if not isinstance(m, int) and c >= 0:
            raise ValueError("The number of variables must be a positive integer.")
        if not isinstance(c, list):
            raise ValueError("The argument must be a list of coefficients or a list of monomials.")
        self.m = m
        if not c or isinstance(c[0], tuple):
            self.monomials = c
            return
        self.monomials = []
        lc = len(c)
        i = 0
        for j in range(m + 1):
            for combination in combinations(range(m), j):
                if i< lc and c[i]:
                    self.monomials.append(combination)
                i += 1

    def __repr__(self, latex=None):
        def prx(i: int) -> str:
            if len(self.__class__.print_x) >= self.m:
                return self.__class__.print_x[i]
            if latex and i > 9:
                return self.__class__.print_x[0] + "_{" + str(i) + "}"
            return self.__class__.print_x[0] + "_" + str(i)

        if not self.monomials:
            return "0"
        if latex is None:
            latex = self.__class__.print_latex
        res = ""
        for monomial in self.monomials:
            for i in monomial:
                res += prx(i) + " "
            if monomial:
                res += "+ "
            else:
                res += "1 + "
        return res[:-3]

    def _repr_mimebundle_(self, **kwargs):  # pylint: disable=W0613
        return {
            "text/plain": repr(self),
            "text/latex": "$" + self.__repr__(latex=True) + "$"  # pylint: disable=C2801
        }

    def index2monomial(self, idx: int) -> tuple|None:
        "Convert an index to a monomial."
        if idx < 0:
            idx %= len(self)
        k = 0
        c = 1
        while idx >= c and k <= self.m:
            idx -= c
            k += 1
            c = comb(self.m, k)
        if k == self.m and idx > 0:
            raise ValueError("Index out of range.")
        return list(combinations(range(self.m), k))[idx]

    def __getitem__(self, item):
        monomial = self.index2monomial(item)
        if monomial in self.monomials:
            return 1
        return 0

    def __setitem__(self, item, value):
        monomial = self.index2monomial(item)
        if monomial in self.monomials:
            if not value:
                self.monomials.remvoe(monomial)
        else:
            if value:
                self.monomials.append(monomial)

    def __iter__(self):
        for j in range(self.m + 1):
            for combination in combinations(range(self.m), j):
                if combination in self.monomials:
                    yield 1
                else:
                    yield 0

    def __len__(self):
        return sum( comb(self.m,j) for j in range(self.m+1) )

    def __call__(self, x: list) -> int:
        "Evaluate a polynomial at a point."
        val = 0
        for monomial in self.monomials:
            val += prod(x[i] for i in monomial)
        return val % 2

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return not bool(self + other)

    def __bool__(self):
        return bool(self.monomials)

    def __add__(self, other) -> "PolyBinMult":
        if not isinstance(other, self.__class__):
            return NotImplemented
        if other.m != self.m:
            raise NotImplementedError("Number of variables do not match!")
        res = self.__class__(self.monomials[:], self.m)
        for monomial in other.monomials:
            if monomial in res.monomials:
                res.monomials.remove(monomial)
            else:
                res.monomials.append(monomial)
        return res

    __sub__ = __add__

    def __pos__(self) -> "PolyBinMult":
        return self

    __neg__ = __pos__

    def __mul__(self, other) -> "PolyBinMult":
        if isinstance(other, self.__class__):
            return self.multiply(other)
        if isinstance(other, int):
            if other % 2:
                return self
            return self.__class__([], self.m)
        return NotImplemented

    def __rmul__(self, other) -> "PolyBinMult":
        if isinstance(other, int):
            if other % 2:
                return self
            return self.__class__([], self.m)
        return NotImplemented

    def multiply(self, other) -> "PolyBinMult":
        "Polynomial Multiplication."
        res = []
        for monomials in self.monomials:
            for monomialo in other.monomials:
                monomialp = tuple(set(monomials + monomialo))
                if monomialp in res:
                    res.remove(monomialp)
                else:
                    res.append(monomialp)
        return self.__class__(res, self.m)

    def clean(self) -> None:
        "Clean up the internal list of monomials."
        self.monomials = list(map(tuple, map(set, self.monomials)))
        self.monomials.sort()

    def degree(self) -> int:
        "Degree of the polynomial."
        if not self.monomials:
            return 0
        return max(map(len, self.monomials))

def lagrange_interpolation(x_coordinates: list, y_coordinates: list) -> "Poly":
    "Compute the Lagrange interpolation polynomial from a given list of x and y values."
    l = len(x_coordinates)
    if l == 0 or l != len(y_coordinates):
        raise ValueError(
            'List of x and y values must be nonempty of equal length.')
    if l != len(set(x_coordinates)):
        raise ValueError('List of x values must not contain duplicate values.')
    # guess zero and one
    zero = 0 * x_coordinates[0]
    one = zero**0

    poly = Poly([zero])
    L_all = prod([Poly([-x, one]) for x in x_coordinates], start=one)

    for x, y in zip(x_coordinates, y_coordinates):
        L = L_all // Poly([-x, one])
        poly += (y /
                 prod([x - xx for xx in x_coordinates if xx != x], start=one)) * L
    return poly
