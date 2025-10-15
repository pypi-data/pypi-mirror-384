# pragma pylint: disable=C0114,C0116
import pytest  # pylint: disable=W0611
from random import randint, seed  # pylint: disable=C0411
from kryptools import Zmod, GF2, Poly, Matrix
from kryptools import gen2pchk, GoppaCode, CyclicCode, ReedSolomonCode, BCHCode

seed(0)
Z_2 = Zmod(2)

def Hamming2(h: int) -> Matrix:
    "Parity check matrix for the binary Hamming code."
    out = []
    for i in range(1,2**h):
        out.append([int(d) for d in str(format(i, "0" + str(h) + "b"))])
    return Matrix(out, ring = Z_2).transpose()


def test_gen2pchk():
    for h in range(2,6):
        H = Hamming2(h)
        G = gen2pchk(H)
        assert not H * G.transpose()

num_tests = 10

def test_Goppa():
    for gf, t in [ [GF2(4), 3],  [GF2(6), 4]]:
        found = False
        while not found:
            c = [randint(0,gf.order-1) for _ in range(t)] + [1]
            g = Poly(c, ring = gf)
            found = g.rabin_test()
        alpha = list(gf)

        goppa = GoppaCode(gf, g, alpha)
        assert not goppa.H * goppa.G.transpose()
        for _ in range(num_tests):
            x = [ randint(0,1) for _ in range(goppa.G.rows) ]
            y = goppa.encode(x)
            for _ in range(t):
                i = randint(0, goppa.G.cols-1)
                y[i] = 1- y[i]
            assert goppa.decode(y) == x

def test_Cyclic():
    for gf, n, g in [ [Zmod(2), 4, [1, 1]],  [Zmod(3), 4, [-1, 1]], [Zmod(11), 5, [4, 6, 1]] ]:
        g = Poly(g, ring = gf)
        cc = CyclicCode(n, g)
        G = cc.generator_matrix()
        H = cc.check_matrix()
        assert not H * G.transpose()
        H2 = gen2pchk(G)
        assert H2.rows == H.rows
        assert not H2 * G.transpose()
        for _ in range(num_tests):
            x = [ gf(randint(0, cc.order-1)) for _ in range(cc.k) ]
            y = cc.encode(x)
            assert cc.decode(y) == x

def test_ReedSolomon():
    for gf, k in [ [Zmod(13), 3],  [GF2(6), 4]]:
        rsc = ReedSolomonCode(k, gf)
        G = rsc.generator_matrix()
        H = rsc.check_matrix()
        assert not H * G.transpose()
        H2 = gen2pchk(G)
        assert H2.rows == H.rows
        assert not H2 * G.transpose()
        t = (rsc.n - rsc.k) // 2
        for _ in range(num_tests):
            x = [ gf(randint(0, rsc.n)) for _ in range(rsc.k) ]
            y = rsc.encode(x)
            for _ in range(t):
                i = randint(0, rsc.n-1)
                y[i] += gf(1)
            assert rsc.decode(y) == x

def test_BCH():
    gf = GF2(1)
    for n, D in [ [7, 3],  [15, 5]]:
        bch = BCHCode(n, D)
        G = bch.generator_matrix()
        H = bch.check_matrix()
        assert not H * G.transpose()
        H2 = gen2pchk(G)
        assert H2.rows == H.rows
        assert not H2 * G.transpose()
        t = (D - 1) // 2
        for _ in range(num_tests):
            x = [ gf(randint(0, 1)) for _ in range(bch.k) ]
            y = bch.encode(x)
            for _ in range(t):
                i = randint(0, bch.n-1)
                y[i] += gf(1)
            assert bch.decode(y) == x
