# pragma pylint: disable=C0114,C0116
import pytest  # pylint: disable=W0611
from random import seed, randint  # pylint: disable=C0411
from fractions import Fraction  # pylint: disable=C0411
from kryptools import Matrix, gram_schmidt, random_unimodular_matrix
from kryptools import Zmod, sis_search, sis_lll, isis_search, isis_lll


def test_gram_schmidt():
    seed(0)
    for n in range(2, 5):
        for _ in range(10):
            found = False
            while not found:
                V = Matrix([[ randint(-10,10) for _ in range(n)] for _ in range(n) ], ring=Fraction)
                found = bool(V.rank() == n)
            Vs, M = gram_schmidt(V)
            assert V == Vs * M
            D = V.eye()
            for i in range(Vs.cols):
                assert Vs[:,i].dot(Vs[:,i]) == Vs[:,i].norm2()
                D[i,i] = Vs[:,i].dot(Vs[:,i])
            assert Vs.transpose() * Vs == D

def test_random_unimodular_matrix():
    for i in range(2, 5):
        U = random_unimodular_matrix(i)
        U.map(Fraction)
        assert U.det() in (-1, 1)

def test_sis():
    seed(0)
    for ring in Zmod(3), Zmod(4), Zmod(5), Zmod(6):
        for _ in range(25):
            A = Matrix([[ring.random() for _ in range(6)] for _ in range(3)])
            xs = sis_search(A)
            assert not A * xs
            x = sis_lll(A)
            assert not A * x
            assert x.norm() == xs.norm()
            b = Matrix([[ring.random()] for _ in range(3)])
            xs = isis_search(A, b)
            if xs is not None:
                assert A * xs == b
            x = isis_lll(A, b)
            if x is not None:
                assert A * x == b
            if xs is not None:
                assert xs.norm() <= x.norm() <= 1.5 * xs.norm()
