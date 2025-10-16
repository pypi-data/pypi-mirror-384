# pragma pylint: disable=C0114,C0116
import pytest  # pylint: disable=W0611
from math import gcd  # pylint: disable=C0411
from random import randint, seed  # pylint: disable=C0411
from fractions import Fraction  # pylint: disable=C0411
from itertools import product  # pylint: disable=C0411
from kryptools import Matrix, Zmod, GF2, eye, circulant, BinaryMatrix


def test_Matrix():
    M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 12]])
    Z = M.zeros()
    assert M
    assert M == M + Z
    assert not Z
    Z[0] = 1
    assert Z
    assert Z != Z.zeros()
    assert circulant([ 1, 0, 0]) == eye(3)
    assert len(M) == 3 * 3
    assert M[0] == 1
    assert M[:] == [1, 2, 3, 4, 5, 6, 7, 8, 12]
    assert 2 * M - M == M
    M.map(Fraction)
    assert M.det() == -9
    assert M.rank() == 3
    Mi = M.inv()
    assert M * Mi == M.eye()
    M = Matrix([[1, 2, 3], [1, 2, 3], [7, 8, 12]], ring = Fraction)
    with pytest.raises(ValueError):
        Mi = M.inv()
    assert M.det() == 0
    assert M.rank() == 2

    Z_11 = Zmod(11)
    assert 2 * M - M == M
    M = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 12]], ring=Z_11)
    Mi = M.inv()
    assert M * Mi == M.eye()

def test_Matrix2():
    num_tests = 100
    seed(0)
    for ring in Zmod(7), Zmod(8), Zmod(10):
        for m,n in ((3, 5), (5, 3), (3, 3)):
            for _ in range(num_tests):
                A = Matrix([[ring.random() for _ in range(m)] for _ in range(n)])
                b = Matrix([ring.random() for _ in range(n)])
                AA = A.applyfunc(lambda x: Fraction(int(x)))
                if n == m:
                    d = A.det()
                    assert d == ring(AA.det())
                    if gcd(d.x, ring.n) == 1:
                        assert A.inv() * A == A.eye()
                    else:
                        with pytest.raises(ValueError):
                            A.inv()
                x = A.solve(b)
                if x is not None:
                    assert A * x == b
                else:
                    if n == m:
                        assert gcd(d.x, ring.n) != 1
                xx = Matrix([ring.random() for _ in range(m)])
                b = A * xx
                x = A.solve(b)
                assert A * x == b

def test_hnf():
    num_tests = 5
    seed(0)
    for m,n in ((3, 5), (5, 3), (3, 3)):
        for _ in range(num_tests):
            A = Matrix([[randint(-10,10) for _ in range(m)] for _ in range(n)])
            H = A.transpose()
            H.permute_columns(range(H.cols-1,-1,-1))
            H = H.hrnf(drop_zero_rows = True)
            H.permute_columns(range(H.cols-1,-1,-1))
            H = H.transpose()
            H.permute_columns(range(H.cols-1,-1,-1))
            assert H == A.hnf()

def test_solve():
    seed(0)
    for gf in Zmod(2), Zmod(7), GF2(1), GF2(8):
        for m,n in ((3, 5), (5, 3), (3, 3)):
            for _ in range(25):
                A = Matrix([[gf.random() for _ in range(n)] for _ in range(m)])
                b = Matrix([gf.random() for _ in range(m)])
                x = A.solve(b)
                if x is not None:
                    assert A *x == b
                else:
                    AA = A[:, :]
                    AA.append_column(b)
                    assert AA.rank() > A.rank()
    for ring in Zmod(4), Zmod(6):
        for m,n in ((3, 4), (4, 3), (3, 3)):
            for _ in range(25):
                A = Matrix([[ring.random() for _ in range(n)] for _ in range(m)])
                b = Matrix([ring.random() for _ in range(m)])
                x = A.solve(b)
                if x is not None:
                    assert A *x == b
                else:
                    for x in product(ring, repeat = A.cols):
                        x = Matrix(x)
                        assert A * x != b

def test_kernel():
    seed(0)
    for gf in Zmod(2), Zmod(7), GF2(1), GF2(8):
        for m,n in ((3, 5), (5, 3), (3, 3)):
            for _ in range(25):
                A = Matrix([[gf.random() for _ in range(n)] for _ in range(m)])
                K = A.kernel()
                assert not A * K
                assert K.rows == A.cols
                if K:
                    assert K.cols == A.nullity()
                else:
                    assert K.cols == 1
    for ring in Zmod(4), Zmod(6):
        for m,n in ((3, 4), (4, 3), (3, 3)):
            for _ in range(25):
                A = Matrix([[ring.random() for _ in range(n)] for _ in range(m)])
                K = A.kernel()
                assert not A * K
                kernel = []
                for a in product(ring, repeat = K.cols):
                    a = K * Matrix(a)
                    a.map(int)
                    a = list(a)
                    if a not in kernel:
                        kernel.append(a)
                kernel.sort()
                kernel2 = []
                for a in product(ring, repeat = A.cols):
                    a = Matrix(a)
                    if not A * a:
                        a.map(int)
                        a = list(a)
                        kernel2.append(a)
                kernel2.sort()
                assert kernel2 == kernel

def test_BinaryMatrix():
    num_tests = 100
    Z_2 = Zmod(2)
    seed(0)
    n = 5

    for _ in range(num_tests):
        m = randint(n-1,n+1)
        mat1 = BinaryMatrix([randint(0,2**n-1) for _ in range(m)], cols = n)
        mat2 = BinaryMatrix([randint(0,2**n-1) for _ in range(m)], cols = n)
        mat3 = BinaryMatrix([randint(0,2**m-1) for _ in range(n)], cols = n)
        Mat1 = Matrix(mat1)
        Mat2 = Matrix(mat2)
        Mat3 = Matrix(mat3)
        assert BinaryMatrix(Mat1 + Mat2) == mat1 + mat2
        assert BinaryMatrix(Mat1 - Mat2) == mat1 + mat2
        assert BinaryMatrix(Mat1 * Mat3) == mat1 * mat3
        Mat1.swap_columns(0,n-1)
        mat1.swap_columns(0,n-1)
        assert BinaryMatrix(Mat1) == mat1
        Mat1.swap_rows(0,m-1)
        mat1.swap_rows(0,m-1)
        assert BinaryMatrix(Mat1) == mat1

    for _ in range(num_tests):
        m = randint(n-1,n+1)
        mat = BinaryMatrix([randint(0,2**n-1) for _ in range(m)], cols = n)
        b = [randint(0,1) for _ in range(m)]
        x = [randint(0,1) for _ in range(n)]
        Mat = Matrix(mat)
        X = Matrix(x, ring = Z_2)
        assert BinaryMatrix(Mat.rref()) == mat.rref()
        assert BinaryMatrix(Mat.kernel()) == mat.kernel()
        assert BinaryMatrix(Mat.transpose()) == mat.transpose()
        if m == n:
            d = mat.det()
            assert int(Mat.det()) == d
            if d:
                assert BinaryMatrix(Mat.inv()) == mat.inv()
        assert Mat.rank() == mat.rank()
        sol = mat.solve(b)
        Sol = Mat.solve(Z_2(b))
        assert (sol is None and Sol is None) or list(Sol.applyfunc(int)) == sol
        if mat.rows == 1:
            assert int(Mat * X) == mat.apply(x)[0]
        else:
            assert list((Mat * X).applyfunc(int)) == mat.apply(x)
