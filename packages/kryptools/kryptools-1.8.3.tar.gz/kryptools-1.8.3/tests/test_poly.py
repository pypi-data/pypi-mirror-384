# pragma pylint: disable=C0114,C0116
import pytest  # pylint: disable=W0611
from math import prod  # pylint: disable=C0411
from random import sample, choices, randint, seed  # pylint: disable=C0411
from kryptools import Poly, PolyBinMult, lagrange_interpolation
from kryptools import Zmod, GF2, divisors, moebius_mu, Matrix, circulant
seed(0)
num_tests = 10

def test_Poly():
    assert  Poly([0]).weight() == 0
    assert  Poly([1]).weight() == 1
    assert  Poly([1]).degree() == 0
    p = Poly([2, 0, 2])
    q = Poly([1, 2, 3, 4])
    assert p.degree() == 2
    assert p.weight() == 2
    assert q.degree() == 3
    assert q.weight() == 4
    d, m = q.divmod(p)
    assert q * p == p.gcd(q) * p.lcm(q)
    assert d * p + m == q
    for _ in range(num_tests):
        p = Poly([randint(0,100) for _ in range(10)])
        q = Poly([randint(0,100) for _ in range(12)])
        x = randint(0,100)
        assert p(x) == sum((c * x**j for j, c in enumerate(p.coeff)), start=0)
        assert (p + q)(x) == p(x) + q(x)
        assert (p - q)(x) == p(x) - q(x)
        assert (p*q)(x) == p(x) * q(x)
    modulus = [-1] + 7 * [0] + [1]
    p = [ randint(0,9) for _ in range(8) ]
    q = [ randint(0,9) for _ in range(8) ]
    assert list(circulant(p) * Matrix(q)) == (Poly(p, modulus = modulus) * Poly(q, modulus = modulus)).coeff
    gf = Zmod(5)
    p = Poly([2, 0, 2], ring = gf)
    q = Poly([1, 2, 3, 4], ring = gf)
    d, m = q.divmod(p)
    assert d * p + m == q
    assert q * p == p.gcd(q) * p.lcm(q)
    for _ in range(num_tests):
        p = Poly(gf.random(10))
        q = Poly(gf.random(12))
        x = gf.random()
        assert p(x) == sum((c * x**j for j, c in enumerate(p.coeff)), start=gf(0))
        assert (p + q)(x) == p(x) + q(x)
        assert (p - q)(x) == p(x) - q(x)
        assert (p * q)(x) == p(x) * q(x)

    gf = GF2(8, modulus=0b100011011)
    p = Poly([2, 1, 1, 3], modulus=[1, 0, 0, 0, 1], ring=gf)
    q = p.inv()
    assert p * q == Poly([1], modulus=[1, 0, 0, 0, 1], ring=gf)
    for _ in range(num_tests):
        p = Poly(gf.random(10))
        q = Poly(gf.random(12))
        x = gf.random()
        assert p(x) == sum((c * x**j for j, c in enumerate(p.coeff)), start=gf(0))
        assert (p + q)(x) == p(x) + q(x)
        assert (p - q)(x) == p(x) - q(x)
        assert (p * q)(x) == p(x) * q(x)

    ring = Zmod(24)
    p = Poly([1, 3, 2, 1], ring = ring, modulus = [-1,0,0,0,0,1])
    assert p.inv() * p == Poly([ring(1)])

def test_rabin():
    for gf,t in [ [Zmod(7), 4], [GF2(4), 3]]:
        order = len(list(gf))
        count = 0
        for i in range(order**t):
            c = []
            while i:
                i, m = divmod(i, order)
                c.append(m)
            c += [0] * (t- len(c)) + [1]
            a = Poly(c, ring=gf)
            if a.rabin_test():
                count += 1
        assert count == sum( moebius_mu(d) * order ** (t // d) for d in divisors(t) ) // t

def test_factor():
    for gf, t in [ [Zmod(7), 14], [GF2(4), 9]]:
        one = Poly([gf(1)])
        for _ in range(20):
            p = one
            while p.degree() < 1:
                p = Poly(gf.random(t), ring =gf)
            factors = p.factor()
            assert prod([f**k for f,k in factors.items()], start = one) == p, p
            for fac in factors:
                assert fac.degree() == 0 or fac.rabin_test(), p

def test_lagrange():
    for gf in [ Zmod(2), Zmod(3), Zmod(5), Zmod(7), Zmod(23), GF2(4), GF2(6)]:
        allpoints = list(gf)
        l = len(allpoints)//2
        for _ in range(10):
            x_coordinates = sample(allpoints, l)
            y_coordinates = choices(allpoints, k = l)
            p = lagrange_interpolation(x_coordinates, y_coordinates)
            assert p.degree() <= len(x_coordinates) - 1
            for x, y in zip(x_coordinates, y_coordinates):
                assert p(x) == y

def test_PolyBinMult():
    m = 3
    c = [0, 1,0,1, 1,0,1, 1]
    p = PolyBinMult(c, m)
    def f(x:list) -> int:
        return (x[0] + x[2] + x[0] * x[1] + x[1] * x[2] + x[0] * x[1] * x[2]) % 2
    assert  list(p) == c
    assert  [ p[j] for j in range(len(p)) ] == c
    assert p
    assert 1 * p == p
    assert 2 * p == PolyBinMult([], m)
    assert not p + p
    assert p * p == p
    for x in range(2**m):
        x = [x >> l & 1 for l in range(m)]
    assert p(x) == f(x)
