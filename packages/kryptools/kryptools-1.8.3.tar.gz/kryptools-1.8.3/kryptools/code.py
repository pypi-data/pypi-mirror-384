"""
Linear codes
"""

from math import prod, comb
from random import sample
from .GF2 import GF2
from .poly import Poly, PolyBinMult
from .la import Matrix, BinaryMatrix, rotate


def left_standard_form(G: Matrix) -> (Matrix, Matrix):
    "Compute the left standard form of a generator matrix. Return the standard form and the pertmutation matrix."
    return G.left_standard_form()

def gen2pchk(G: Matrix) -> Matrix:
    "Compute the parity check matrix from a given generator matrix (and vice versa)."
    return G.kernel().transpose()

def hamming_dist(a: iter, b: iter):
    "Hamming distance of two iterables."
    if len(a) != len(b):
        raise ValueError("Both iteralbles must have equal length.")
    return sum(aa != bb for aa, bb in zip(a, b))

class BinaryCode():
    """
    Binary linear code.

    A code is constuced from a generator matrix (or a parity check matrix, if the option parity_check is set)
    Example:

    >>> G = BinaryMatrix([[1, 0, 0, 1, 0, 1, 1], [0, 1, 0, 1, 1, 0, 1], [0, 0, 1, 0, 1, 1, 1]])
    >>> bc = BinaryCode(G)
    
    To encode a list of letters (the length must be equal to the dimension k of the code):
    >>> bc.encode([0,1,0])
    [[0, 1, 0, 1, 1, 0, 1]

    Decoding uses a syndrome table which is only feasible for small codes:
    >>> bc.decode([0, 1, 0, 1, 1, 0, 1])
    [0, 1, 0]
    
    """

    def __init__(self, G: BinaryMatrix, systematic: bool = True, parity_check = False, minimum_distance = True):
        if isinstance(G, list):
            G = BinaryMatrix(G)
        elif isinstance(G, Matrix):
            G = BinaryMatrix(G.matrix)
        elif not isinstance(G, BinaryMatrix):
            raise ValueError("Cannot convert argument to a BinaryMatrix.")
        if parity_check:  # the parity check matrix was given
            H = G
            G = H.kernel().transpose()
            if systematic:
                G = G.left_standard_form()
                if G.pivotcols != list(range(G.rows)):
                    H.permute_columns(G.pivotcols + G.nonpivotcols)
            else:
                G.rref()
                if G.pivotcols == list(range(G.rows)):
                    systematic = True
        else:
            if systematic:
                G = G.left_standard_form()
                H = G.kernel().transpose()
            else:
                GG = G.rref()
                if GG.pivotcols == list(range(G.rows)) and GG == G:
                    systematic = True
                H = GG.kernel().transpose()
        self.systematic = systematic
        self.G = G  # generator matrix
        self.H = H  # parity check matrix
        self.n = G.cols  # lenght
        self.k = G.cols - self.H.rows  # dimension
        if not G or not H:
            raise ValueError("Code is trivial!")
        if G.rows != self.k:
            raise ValueError("Generator matrix contains linearly dependent rows!")
        if self.n < self.k:
            raise ValueError("Generator matrix contains more rows than columns!")
        self.Gt = G.transpose()  # transposed generator matrix
        if not systematic:
            self.Gi = self.Gt.inv(left=True)
            self.Gi.delete_rows(range(G.rows, G.cols))
        self.d = None  # minimum distance
        self.name = "linear"
        self.syndrome_table = None # syndrome table
        if minimum_distance:
            self.minimum_distance()

    def __repr__(self):
        out = f"Binary {self.name} "
        if self.systematic:
            out += "systematic "
        out += f"[{self.n}, {self.k}"
        if self.d is not None:
            out += f", {self.d}"
        return out + "] code."

    def encode(self, x: list|int) -> list|int:
        "Encode a given int or list."
        return self.Gt.apply(x)

    def decode(self, y: list|int) -> list|int:
        "Decode a given int or list."
        as_list = False
        if isinstance(y, list):
            as_list = True
            if len(y) != self.n:
                raise ValueError("Word length not equal code length.")
            y = self.G.from_bits(y)
        syndrome = self.H.apply(y)
        if syndrome:
            y ^= self.correct(syndrome)
        if self.systematic:
            y >>= self.n - self.k
        else:
            y = self.Gi.apply(y)
        if as_list:
            return self.G.to_bits(y, self.k)
        return y

    def is_decode(self, y: list|int, t: int|None = None) -> list|int:
        "Decode a given int or list using Information Set Decoding."
        as_list = True
        if isinstance(y, int):
            as_list = False
            y = self.G.to_bits(y, self.n)
        if t is None:
            t = self.correction_cap()
        found = False
        if not self.H.apply(y):
            xx = y[:self.k]
            found = True
        while not found:
            GG = []  # template to hold the selected columns
            yy = []  # template to hold the corresponding bits from y
            for j in sample(range(self.n), self.k):
                GG.append(self.Gt.matrix[j])
                yy.append(y[j])
            xx = BinaryMatrix(GG).solve(yy) # try to solve the selection
            if xx is None:  # no soluton
                continue
            xx = xx.matrix
            if hamming_dist(y, self.Gt.apply(xx)) <= t:  # check if the solution has at most t errors
                found = True
        if as_list:
            return xx
        return self.G.from_bits(xx)

    def build_syndrome_table(self, t: int|None = None) -> None:
        "Correct a given syndrome."
        if self.syndrome_table:
            return
        if t is None:
            t = self.correction_cap()
        self.syndrome_table = {0: 0}
        for i in range(1, t + 1):
            # Gosper's hack
            x = 2**i - 1
            while x < 2**self.n:
                self.syndrome_table[self.H.apply(x)] = x
                c = x & -x
                r = x + c
                x = (((r^x) >> 2) // c) | r

    def correct(self, syndrome: int) -> int:
        "Return the error for a given syndrome."
        self.build_syndrome_table()
        if syndrome in self.syndrome_table:
            return self.syndrome_table[syndrome]
        raise NotImplementedError("Error beyond correction capability.")

    def minimum_distance(self, d_lower = None) -> int:
        "Compute the minimal distance of a code using the Brouwer-Zimmermann algorithm."
        if self.d is not None:
            return self.d
        ranks = [ self.k ]
        Gammas = [ self.G ]
        start = self.k
        while start < self.n:
            GG = Gammas[-1].rref(start = start)
            r = len(GG.pivotcols)
            if not r:
                break
            ranks.append(r)
            GG.permute_columns(list(range(start))+GG.pivotcols+GG.nonpivotcols)
            if GG != Gammas[-1]:
                Gammas.append(GG)
            start = sum(ranks)
        d_ub = self.n  # upper bound on d
        for i in range(1, self.k + 1):
            d_lb = sum( (i+1) - (self.k-r) for r in ranks if self.k-r <= i )  # lower bound on d
            for GG in Gammas:
                GG = GG.transpose()
                x = 2**i - 1
                while x < 2**self.k:
                    d = 0
                    c = GG.apply(x)
                    while c:
                        c &= c - 1
                        d += 1
                    if d_lower and d <= d_lower:  # known lower bound
                        self.d = d
                        return d
                    d_ub = min(d_ub, d)
                    # Gosper's hack
                    c = x & -x
                    r = x + c
                    x = (((r^x) >> 2) // c) | r
            if d_lb >= d_ub:
                self.d = d_ub
                return d_ub
        # we must have d = d_ub at this point, but can we ever here?
        self.d = d_ub
        raise ValueError(f"Lower bound failed to reach upper bound: {d_lb} <= d = {d_ub}")

    def correction_cap(self) -> int:
        "Error correction capability of the code."
        d = self.minimum_distance()
        return (d - 1) // 2

class HammingCode(BinaryCode):
    """
    Binary Hamming code.

    Example:

    >>> hc = HammingCode(3)
    
    To encode a list of letters (the length must be equal to the dimension k of the code):
    >>> hc.encode([1, 1, 0, 1])
    [1, 1, 0, 1, 0, 0, 1]

    Decoding can correct one error:
    >>> bc.decode([1, 1, 1, 1, 0, 0, 1])
    [1, 1, 0, 1]
    
    """

    def __init__(self, h: int):
        H = []
        for i in range(1,2**h):
            H.append([int(d) for d in str(format(i, "0" + str(h) + "b"))])
        H = BinaryMatrix([list(i) for i in zip(*H)])  # transpose
        super().__init__(H, parity_check = True, minimum_distance = False)
        self.name = "Hamming"
        self.d = 3

    def correct(self, syndrome: int) -> int:
        "Return the error for a given syndrome."
        return 1 << (self.n - syndrome)  # for a Hamming code the syndrom gives the position of the error

class GolayCode(BinaryCode):
    """
    Binary Golay code.

    Example:

    >>> golay = GolayCode()
    
    To encode a list of letters (the length must be equal to the dimension k of the code):
    >>> bc.encode([1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1])
    [1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0]

    Decoding uses a syndrome table and can correct one error:
    >>> bc.decode([1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0])
    [1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1]
    
    """

    def __init__(self):
        G = [ [ bool(i==j) for i in range(12) ] for j in range(12) ]
        for n in range(11):
            G[n] += rotate([1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0], n)
        G[11] += [1] * 11
        G = BinaryMatrix(G)
        super().__init__(G, minimum_distance = False)
        self.name = "Golay"
        self.d = 7


class ReedMullerCode(BinaryCode):
    """
    Binary Reed-Muller code.

    Example:

    >>> rmc = ReedMullerCode(1, 2)
    
    To encode a list of letters (the length must be equal to the dimension k of the code):
    >>> rmc.encode([1, 1, 0])
    [0, 1, 0, 1]

    Decoding uses a syndrome table which is only feasible for small codes:
    >>> rmc.decode([0, 1, 0, 1])
    [1, 1, 0]
    
    """

    def __init__(self, s: int, m:int, systematic = False):
        self.s = s  # degree
        self.m = m  # number of variables
        if m <= s:
            raise ValueError("The degree must be smaller than the number of variables.")
        k = sum(comb(m,j) for j in range(s+1))
        G = []
        for j in range(k):
            poly = PolyBinMult([int(l == j) for l in range(k)], m)  # encode unit vector as a polynoials
            G.append([ poly([i >> l & 1 for l in range(m)]) for i in range(2**m-1,-1,-1) ])
        super().__init__(G, systematic = systematic, minimum_distance = False)
        self.d = 2**(m-s)
        self.name = f"Reed-Muller({s},{m})"

class GoppaCode(BinaryCode):
    """
    Binary irreducible Goppa code.

    Example:

    >>> gf = GF2(4) # base field GF(2^4)
    >>> g = Poly([2, 0, 0, 1], ring = gf) # irreducible Polynomial for the code
    >>> alpha = list(gf) # list of points from the base field (must not contain zeros of g)
    >>> goppa = GoppaCode(gf, g, alpha)
    
    To encode a list of bits (the length must be equal to the dimension k of the code)
    >>> goppa.encode([1, 0, 1, 1])
    [0, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1]

    Decoding still works if there are at most deg(g) errors:
    >>> goppa.decode([0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0])
    [1, 0, 1, 1]
    
    """

    def __init__(self, gf: GF2, g: Poly, alpha: list["GF2Point"], systematic: bool = True, minimum_distance = False):
        if not all(map(lambda x: x in gf, alpha)):
            raise ValueError("All elements of alpha must be from the Galois field!")
        if not g.rabin_test():
            raise ValueError("The polynomial g must be irreducible!")
        self.gf = gf  # underlying Galois field
        self.g = g  # polynomial
        # Compute the parity check matrix
        H = []
        one = gf.one()
        for x in alpha:
            H.append(int(Poly([-x, one], modulus = g).inv()))
        H = BinaryMatrix(H).transpose()
        super().__init__(H, systematic = systematic, parity_check = True, minimum_distance = minimum_distance)
        if systematic:
            permutation =  self.G.pivotcols + self.G.nonpivotcols
            if permutation != list(range(self.G.cols)):
                alpha = [ alpha[i] for i in permutation ]
        self.alpha = alpha # list of elements from gf
        self.name = "Goppa"

    def __repr__(self):
        parameters = f"{self.n}, {self.k}"
        if self.d is not None:
            parameters += f", {self.d}"
        return f"Binary irreducible Goppa [{parameters}] code over GF(2^{self.gf.degree}) with polynomial g(x) = {self.g}."

    def correct(self, syndrome: int) -> int:
        "Decode a given list of bits."
        zero = self.gf(0)
        one = self.gf.one()

        mask = self.gf.order - 1
        m = self.gf.degree
        ss = syndrome  # make a copy
        tmp = []
        while ss:
            tmp.append(ss & mask)
            ss >>= m
        s = Poly([ self.gf(i) for i in tmp], modulus = self.g) # syndrom polynomial
        v = (s.inv() - Poly([zero, one], modulus = self.g))**(self.gf.order ** self.g.degree() // 2)
        # determine error locator polynomial sigma(x) = a(x^2) + b(x^2) * x
        # find a and b by running EEA until b has the desired degree
        v.modulus = None
        r0, r1 = self.g, v
        y0, y1 = Poly([zero]), Poly([one])
        while 2 * r1.degree() > self.g.degree():
            q, r = r0.divmod(r1)
            r0, r1 = r1, r
            y0, y1 = y1, y0 - q * y1
        a, b = r1, y1
        sigma = a**2 + b**2 * Poly([zero, one])
        # find the error
        e = 0
        for i, x in enumerate(self.alpha):
            if not sigma(x):
                e += 1 << (self.n - i - 1)
        if self.H.apply(e) != syndrome:
            raise ValueError("Decoding failed!")
        return e

    def minimum_distance(self, d_lower = None) -> int:
        "Compute the minimal distance of a code using the Brouwer-Zimmermann algorithm."
        if d_lower is None:
            d_lower = 2 * self.g.degree() + 1  # known lower bound for the minimum distance
        return super().minimum_distance(d_lower)

class CyclicCode():
    """
    Cyclic code.

    Example:

    >>> n = 4 # length of the code
    >>> g = Poly([1, 1], ring = Zmod(2)) # generating polynomial for the code
    >>> cc = CyclicCode(n, g)
    
    To encode a list of letters (the length must be equal to the dimension k of the code):
    >>> cc.encode([0, 1, 0])
    [0, 1, 1, 0]

    Decoding is only implemented for code words:
    >>> cc.decode([0, 1, 1, 0])
    [0, 1, 0]
    
    """

    def __init__(self, n:int, g: Poly, systematic = True):
        if n < 2:
            raise ValueError(f"Code lenght {n} must be at least 2!")
        zero = 0 * g[0]
        if hasattr(zero, "ring"):  # Zmod
            gf = zero.ring
            order = gf.n
        elif hasattr(zero, "field"):  # GF2
            gf = zero.field
            order = gf.order
        elif hasattr(type(zero), "order"):  # galois
            gf = type(zero)
            order = gf.order
        else:
            raise ValueError("Unknown base field!")
        self.gf = gf  # base field
        self.order = order  # order of the base field
        one = zero**0
        modulus = Poly([-one] + [zero] * (n-1) + [one])
        self.modulus = modulus
        if modulus % g:
            raise ValueError(f"The polynomial g must be a factor of x^{n} - 1!")
        self.systematic = systematic
        self.n = n  # lenght
        self.k = n - g.degree()  # dimension
        self.g = g  # generating polynomial
        self.h = Poly(modulus) // g

    def __repr__(self):
        systematic = ""
        if self.systematic:
            systematic = "systematic "
        return f"Cyclic {systematic}[{self.n}, {self.k}] code over GF({self.order}) with generator polynomial g(x) = {self.g}."

    def encode(self, x: list|Poly) -> list|Poly:
        "Encode a given list or polynomial."
        as_list = False
        zero = 0 * self.g[0]
        if isinstance(x, list | tuple):
            as_list = True
            x = Poly(x, ring = self.gf)
        if x.degree() >= self.k:
            raise ValueError(f"Degree can be at most {self.k-1}.")
        if self.systematic:
            x.coeff = [zero] * self.g.degree() + x.coeff
            y = x - (x % self.g)
        else:
            y = self.g * x
        if as_list:
            return y.coeff + [zero] * (self.n - len(y.coeff))
        return y

    def decode(self, y: list|Poly) -> list|Poly:
        "Decode a given list or polynomial."
        as_list = False
        zero = 0 * self.g[0]
        if isinstance(y, list | tuple):
            as_list = True
            y = Poly(y, ring = self.gf)
        if y.degree() >= self.n:
            raise ValueError(f"Degree can be at most {self.n-1}.")
        x, r = y.divmod(self.g)
        if r:
            y = self.correct(y)
            x, r = y.divmod(self.g)
        if self.systematic:
            x.coeff = y.coeff[self.g.degree():]
        if as_list:
            return x.coeff + [zero] * (self.k - len(x.coeff))
        return x

    def correct(self, y: Poly) -> Poly:
        "Correct a given polynomial."
        raise NotImplementedError("Error correction not implemented.")

    def generator_matrix(self):
        "Return the generator matrix of the code."
        zero = 0 * self.g[0]
        G = Matrix([[zero] * j + self.g.coeff + [zero] * (self.k - j - 1 ) for j in range(self.k)])
        if self.systematic:
            G = G.rref(start = G.cols - G.rows)
        return G

    def check_matrix(self):
        "Return the parity check matrix of the code."
        zero = 0 * self.g[0]
        tmp = list(reversed(self.h.coeff))
        return Matrix([[zero] * j + tmp + [zero] * (self.n - self.k - j - 1 ) for j in range(self.n-self.k)])

class ReedSolomonCode(CyclicCode):
    """
    Reed-Solomon code.

    Example:

    >>> gf = Zmod(13) # Galois field
    >>> k = 3 # dimension of the code
    >>> rsc = ReedSolomonCode(k, gf)
    
    To encode a list of letters (the length must be equal to the dimension k of the code; conversion to the Galois field is done automatically):
    >>> rsc.encode([1, 2, 3])
    [6, 4, 5, 1, 8, 4, 2, 9, 2, 8, 9, 6]

    To decode use:
    >>> rsc.decode([1, 4, 4, 0, 8, 4, 2, 9, 2, 0, 9, 6])
    [1, 2, 3]
    
    """
    def __init__(self, k:int, gf, alpha = None):  # pylint: disable=W0231
        zero = gf(0)
        one = zero**0
        self.gf = gf
        if hasattr(gf, "n"):
            n = gf.n - 1  # Zmod
        else:
            n = gf.order - 1  # GF2|galois
        self.order = n + 1  # order of the base field
        self.n = n  # lenght
        self.k = k  # dimension
        if k >= n:
            raise ValueError(f"Code dimension k = {k} must be smaller than the code lenght n = {self.n}.")
        self.d = n - k + 1  # minimal distance
        self.modulus = Poly([-one] + [zero] * (n-1) + [one])
        if alpha is None:
            if hasattr(gf, "primitive_element"):
                alpha = gf.primitive_element  # galois
            else:
                alpha = gf.generator()  # Zmod|GF2
        self.alpha = alpha
        self.g = prod([Poly([-alpha**j, one]) for j in range(1,n-k+1)], start = one) # generating polynomial
        self.h = Poly(self.modulus) // self.g  # check polynomial
        self.systematic = None  # unused
        assert k == n - self.g.degree()
        assert self.g * self.h == self.modulus

    def __repr__(self):
        return f"Reed-Solomon [{self.n}, {self.k}, {self.d}] code over GF({self.n+1})."

    def encode(self, x: list|Poly) -> list|Poly:  # pylint: disable=W0221
        "Encode a given list or polynomial."
        as_list = False
        zero = 0 * self.g[0]
        if isinstance(x, list | tuple):
            as_list = True
            x = Poly(x, ring = self.gf)
        if x.degree() >= self.k:
            raise ValueError(f"Degree can be at most {self.k-1}.")
        y = [ x(self.alpha**j) for j in range(self.n) ]
        if as_list:
            return y + [zero] * (self.n - len(y))
        return Poly(y)

    def decode(self, y: list|Poly) -> list|Poly:  # pylint: disable=W0221
        "Decode a given list or polynomial."
        as_list = False
        zero = 0 * self.g[0]
        one = zero**0
        if isinstance(y, list | tuple):
            as_list = True
            y = Poly(y, ring = self.gf)
        if y.degree() >= self.n:
            raise ValueError(f"Degree can be at most {self.n-1}.")
        xx = [ -y(self.alpha**(-j)) for j in range(self.n) ]
        x = Poly(xx)
        if x.degree() >= self.k: # No codewort
            t = (self.n - self.k) // 2
            if not t:
                raise ValueError("This code cannot correct any errors.")
            A = Matrix([[ xx[j - l % self.n] for l in range(1, t+1) ] for j in range(self.k+t, self.k+2*t) ])
            b = [ -xx[self.k + t + l ] for l in range(t) ]
            lam = Poly([one] + list(A.solve(b)))
            lamp = lam.derivative()
            s = Poly([x[self.k + j] for j in range(self.n - self.k)])
            omega = s * lam
            omega = Poly(omega.coeff[:self.n - self.k])  # mod x^(n-k)
            # Chien search
            lam = lam.coeff
            alphai = [ self.alpha**i for i in range(len(lam)) ]
            for i in range(self.n):
                if not sum(lam, start = zero):
                    # Fornay
                    ali = self.alpha**i
                    y[i] -= ali**(self.k-1) * omega(ali) / lamp(ali)
                for j in range(len(lam)):  # pylint: disable=C0200
                    lam[j] *= alphai[j]
            x = Poly([ -y(self.alpha**(-j)) for j in range(self.n) ])
        if as_list:
            return x.coeff + [zero] * (self.k - len(x.coeff))
        return x

    def correct(self, y: Poly):
        "Correct a given polynomial."
        x = self.decode(y)
        return self.encode(x)

class BCHCode(CyclicCode):
    """
    Binary narrow sense primitive BCH code.

    Example:

    >>> n = 7 # lenght of the code
    >>> D = 2 # desired distance
    >>> bch = BCHCode(k, D)
    
    To encode a list of letters (the length must be equal to the dimension k of the code; conversion to the Galois field is done automatically):
    >>> bch.encode([0, 1, 0, 1])
    [0, 1, 1, 1, 0, 0, 1]

    To decode use:
    >>> bch.decode([0, 1, 1, 1, 0, 0, 1])
    [0, 1, 0, 1]
    
    """
    def __init__(self, n:int, D: int):
        m = n.bit_length()
        if 2**m - 1 != n:
            raise ValueError(f"The codelenght n={n} plus one must be a power of 2.")
        self.rsc = ReedSolomonCode(n - D + 1, GF2(m))
        # Compute the generator polynomial
        aj = self.rsc.alpha
        g = aj.minpoly()
        for _ in range(2,D):
            aj *= self.rsc.alpha
            mj = aj.minpoly()
            g = g.lcm(mj)
        g.map(GF2(1))
        super().__init__(n, g)

    def __repr__(self):
        return f"BCH [{self.n}, {self.k}] code over GF({self.order}) with generator polynomial g(x) = {self.g}."

    def correct(self, y: Poly):
        "Correct a given polynomial."
        y.map(self.rsc.gf)
        x = self.rsc.decode(y)
        y = self.rsc.encode(x)
        y.map(GF2(1))
        return y
