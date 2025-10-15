"""
Linear algebra
"""

# pragma pylint: disable=C0302
from math import gcd, inf, sqrt
from numbers import Number
from fractions import Fraction
from .nt import egcd
from .Zmod import Zmod

class Matrix:
    """
    Matrix class.

    Example:

    To define a matrix use
    >>> Matrix([[1, 2], [3, 4]])
    [1, 2]
    [3, 4]
    """

    print_pre = "[ "
    print_post = " ]"
    print_sep = ", "

    def __init__(self, matrix: list|tuple, ring = None):
        if isinstance(matrix, BinaryMatrix):
            matrix = matrix.bitmatrix()
            ring = Zmod(2)
        elif not (isinstance(matrix, list|tuple) and matrix):
            raise ValueError("The given `matrix` must be a nonempty list.")
        elif not isinstance(matrix[0], list|tuple):
            matrix = [[x] for x in matrix]
        self.matrix = matrix  # the matrix as a list (rows) of lists (column entries)
        self.cols = len(matrix[0])  # number of columns
        self.rows = len(matrix)  # number of rows
        self.nonpivotcols = None  # set during rref
        self.pivotcols = None  # set during rref
        for i in range(1, self.rows):
            if len(matrix[i]) != self.cols:
                raise ValueError("All matrix rows must have equal length!")
        if ring:
            self.map(ring)

    def __repr__(self) -> str:
        out = [self.__class__.print_pre] * self.rows
        for j in range(self.cols):
            tmp = [""] * self.rows
            max_len = 0
            for i in range(self.rows):
                tmp[i] = str(self.matrix[i][j])
                max_len = max(max_len, len(tmp[i]))
            for i in range(self.rows):
                out[i] += " " * (max_len - len(tmp[i])) + tmp[i]
                if j < self.cols - 1:
                    out[i] += self.__class__.print_sep
        for i in range(self.rows):
            out[i] += self.__class__.print_post
        return '\n'.join(out)

    def _repr_mimebundle_(self, **kwargs):  # pylint: disable=W0613
        return {
            "text/plain": repr(self),
            "text/latex": "$\\displaystyle" + self.latex() + "$"
        }

    def latex(self) -> str:
        "Produce LaTeX code for the matrix."
        res = "\\begin{pmatrix}\n"
        for row in self.matrix:
            res += " & ".join(map(str, row)) + '\\\\\n'
        res = res[:-3] + '\n\\end{pmatrix}'
        return res

    def __len__(self):
        return self.cols * self.rows

    def __getitem__(self, item):
        if isinstance(item, tuple):
            i, j = item
            if isinstance(i, int) and isinstance(j, int):
                return self.matrix[i][j]
            if isinstance(i, int):
                rows = [i]
            elif isinstance(i, list):
                rows = i
            else:
                rows = range(self.rows)[i]
            if isinstance(j, int):
                cols = [j]
            elif isinstance(j, list):
                cols = i
            else:
                cols = range(self.cols)[j]
            return self.__class__([[self.matrix[i][j] for j in cols] for i in rows])
        if isinstance(item, int):
            i, j = divmod(item, self.cols)
            return self.matrix[i][j]
        return [self.matrix[k // self.cols][k % self.cols] for k in range(self.cols * self.rows)[item]]

    def __setitem__(self, item, value):
        if isinstance(item, tuple):
            i, j = item
            if isinstance(i, int) and isinstance(j, int):
                self.matrix[i][j] = value
                return
            if isinstance(i, int):
                rows = [i]
            elif isinstance(i, list):
                rows = i
            else:
                rows = range(self.rows)[i]
            if isinstance(j, int):
                cols = [j]
            elif isinstance(j, list):
                cols = j
            else:
                cols = range(self.cols)[j]
            for i, ii in zip(cols, range(len(cols))):
                for j, jj in zip(rows, range(len(rows))):
                    self.matrix[j][i] = value[jj, ii]
        elif isinstance(item, int):
            i, j = divmod(item, self.cols)
            self.matrix[i][j] = value
        else:
            for k in range(self.cols * self.rows)[item]:
                i, j = divmod(k, self.cols)
                self.matrix[i][j] = value[k]

    def __delitem__(self, item):
        if isinstance(item, tuple):
            i, j = item
            if isinstance(i, int):
                rows = [i]
            elif isinstance(i, list):
                rows = set(i)
            else:
                rows = range(self.rows)[i]
            if isinstance(j, int):
                cols = [j]
            elif isinstance(j, list):
                cols = set(j)
            else:
                cols = range(self.cols)[j]
            if len(cols) == self.cols:
                self.delete_rows(rows)
                return
            if len(rows) == self.rows:
                self.delete_columns(cols)
                return
        raise ValueError("Can only delete entire rows or entire columns!")

    def delete_rows(self, rows: int|list) -> None:
        "Deletes a row or a list of rows."
        if isinstance(rows, int):
            rows = [ rows ]
        rows = list(map(lambda x: x % self.rows, rows))
        rows = set(rows)
        if len(rows) >= self.rows:
            raise ValueError("Cannot delete all rows.")
        for i in sorted(rows, reverse = True):
            del self.matrix[i]
        self.rows -= len(rows)

    def delete_columns(self, cols: int|list) -> None:
        "Deletes a column or a list of columns."
        if isinstance(cols, int):
            cols = [ cols ]
        cols = list(map(lambda x: x % self.cols, cols))
        cols = set(cols)
        if len(cols) >= self.cols:
            raise ValueError("Cannot delete all columns.")
        for j in sorted(cols, reverse = True):
            for i in range(self.rows):
                del self.matrix[i][j]
        self.cols -= len(cols)

    def append_row(self, row: list|tuple, ring = None) -> None:
        "Append a row."
        if isinstance(row, self.__class__):
            row = row.matrix
        elif not isinstance(row, list|tuple):
            row = list(row)
        if not isinstance(row[0], list|tuple):
            row = [ row ]
        if len(row[0]) != self.cols:
            raise ValueError("Length does not match the number of columns.")
        if ring:
            for i, r in enumerate(row):
                row[i] =list(map(ring, r))
        self.matrix += row
        self.rows += len(row)

    def append_column(self, col: list|tuple, ring = None) -> None:
        "Append a column."
        if isinstance(col, self.__class__):
            col = col.matrix
        elif not isinstance(col, list|tuple):
            col = list(col)
        if len(col) != self.rows:
            raise ValueError("Length does not match the number of rows.")
        if isinstance(col[0], list|tuple):
            for i, c in enumerate(col):
                if ring:
                    self.matrix[i] += list(map(ring, c))
                else:
                    self.matrix[i] += c
            self.cols += len(col[0])
        else:
            for i, c in enumerate(col):
                if ring:
                    self.matrix[i].append(ring(c))
                else:
                    self.matrix[i].append(c)
            self.cols += 1

    def swap_columns(self, i: int, j: int) -> None:
        "Swap two columns."
        for k in range(self.rows):
            self.matrix[k][i], self.matrix[k][j] = self.matrix[k][j], self.matrix[k][i]

    def swap_rows(self, i: int, j: int) -> None:
        "Swap two rows."
        self.matrix[i], self.matrix[j] = self.matrix[j], self.matrix[i]

    def permute_columns(self, permutation: list) -> None:
        "Permute columns according to a list of new positions."
        if len(permutation) != self.cols:
            raise ValueError(f"The argument must be a list of indices of length {self.cols}.")
        for i in range(self.rows):
            self.matrix[i] = [ self.matrix[i][j] for j in permutation]

    def permute_rows(self, permutation: list) -> None:
        "Permute rows according to a list of new positions."
        if len(permutation) != self.rows:
            raise ValueError(f"The argument must be a list of indices of length {self.rows}.")
        self.matrix = [ self.matrix[i] for i in permutation]

    def scale_column(self, i: int, a: Number) -> None:
        "Scale a column."
        for k in range(self.rows):
            self.matrix[k][i] *= a

    def scale_row(self, i: int, a: Number) -> None:
        "Scale a row."
        for k in range(self.cols):
            self.matrix[i][k] *= a

    def addto_column(self, i: int, j: int, a: Number|None = None) -> None:
        "Add a multiple of the first column to the second."
        if a is None:
            for k in range(self.rows):
                self.matrix[k][i] += self.matrix[k][j]
        else:
            for k in range(self.rows):
                self.matrix[k][i] += a * self.matrix[k][j]

    def addto_row(self, i: int, j: int, a: Number|None = None) -> None:
        "Add a multiple of the first row to the second."
        if a is None:
            for k in range(self.cols):
                self.matrix[i][k] += self.matrix[j][k]
        else:
            for k in range(self.cols):
                self.matrix[i][k] += a * self.matrix[j][k]

    def maop_row(self, i: int, k: int, a: Number, b: Number, c: Number, d: Number) -> None:
        "Replaces the i,j and k,j entry by  by using an matrix column operation."
        for l in range(self.cols):
            self.matrix[i][l], self.matrix[k][l] = a * self.matrix[i][l] + b * self.matrix[k][l], c * self.matrix[i][l] + d * self.matrix[k][l]

    def maop_column(self, j: int, k: int, a: Number, b: Number, c: Number, d: Number) -> None:
        "Replaces the i,j and i,k entry by using an matrix column operation."
        for l in range(self.rows):
            self.matrix[l][j], self.matrix[l][k] = a * self.matrix[l][j] + b * self.matrix[l][k], c * self.matrix[l][j] + d * self.matrix[l][k]

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.rows != other.rows or self.cols != other.cols:
            return False
        return all(self[i] == other[i] for i in range(self.rows * self.cols))

    def __bool__(self):
        return any(bool(self[i]) for i in range(self.rows * self.cols))

    def map(self, func) -> None:
        "Apply a function to all elements in place."
        for row in self.matrix:
            row[:] = map(func, row)

    def applyfunc(self, func) -> "Matrix":
        "Apply a function to all elements."
        tmp = self[:, :]
        tmp.map(func)
        return tmp

    def _guess_zero(self):
        "Guess zero and one in the ring of the coefficients."
        zero = 0 * self.matrix[0][0]
        one = zero**0
        return zero, one

    def norm2(self) -> float:
        "Squared Frobenius/Euclidean norm."
        return sum(sum(abs(x)**2 for x in row) for row in self.matrix)

    def norm(self, p: int = 2) -> float:
        "p-norm of the matrix regarded as a vector."
        if p == 2:
            return sqrt(self.norm2())
        if p == 1:
            return sum(sum(abs(x) for x in row) for row in self.matrix)
        if p == inf:
            return max(max(abs(x) for x in row) for row in self.matrix)
        tmp = sum(sum(abs(x)**p for x in row) for row in self.matrix)
        return tmp**(1/p)

    def dot(self, other) -> int:
        "Dot product of two vectors."
        if self.rows == 1 and other.rows == 1 and self.cols == other.cols:
            return sum(x * y for x, y in zip(self.matrix[0], other.matrix[0]))
        if self.cols == 1 and other.cols == 1 and self.rows == other.rows:
            return sum(x[0] * y[0] for x, y in zip(self.matrix, other.matrix))
        return NotImplemented

    def transpose(self) -> "Matrix":
        "Transposed matrix."
        return Matrix([list(i) for i in zip(*self.matrix)])

    def multiply(self, other) -> "Matrix":
        "Matrix multiplication."
        if not isinstance(other, Matrix):
            return NotImplemented
        if self.cols != other.rows:
            raise NotImplementedError("Matrix dimensions do not match!")
        result = self.zeros(self.rows, other.cols)
        for i in range(self.rows):
            for j in range(other.cols):
                for k in range(other.rows):
                    result.matrix[i][j] += self.matrix[i][k] * other.matrix[k][j]
        if self.rows == 1 and other.cols == 1:
            return result.matrix[0][0]
        return result

    def __add__(self, other) -> "Matrix":
        if isinstance(other, Matrix):
            if other.cols != self.cols or other.rows != self.rows:
                raise NotImplementedError("Matrix dimensions do not match!")
            return self.__class__([[x1 + y1 for x1, y1 in zip(x, y)] for x, y in zip(self.matrix, other.matrix)])
        return NotImplemented

    def __sub__(self, other) -> "Matrix":
        if isinstance(other, Matrix):
            if other.cols != self.cols or other.rows != self.rows:
                raise NotImplementedError("Matrix dimensions do not match!")
            return self.__class__([[x1 - y1 for x1, y1 in zip(x, y)] for x, y in zip(self.matrix, other.matrix)])
        return NotImplemented

    def __neg__(self) -> "Matrix":
        return -1 * self

    def __pos__(self) -> "Matrix":
        return self

    def __mul__(self, other) -> "Matrix":
        if isinstance(other, Matrix):
            return self.multiply(other)
        if isinstance(other, Number) or type(other) is type(self.matrix[0][0]):
            return self.__class__([[item * other for item in row] for row in self.matrix])
        return NotImplemented

    def __rmul__(self, other) -> "Matrix":
        if isinstance(other, Number) or type(other) is type(self.matrix[0][0]):
            return self.__class__([[item * other for item in row] for row in self.matrix])
        return NotImplemented

    def rref(self, start: int = 0, drop_zero_rows: bool = False) -> "Matrix":
        "Compute the reduced echelon form."
        if hasattr(self.matrix[0][0], "ring") and not self.matrix[0][0].ring.is_field():
            # the matrix is over a ring (not a field)
            return self._rref_ring(start = start, drop_zero_rows = drop_zero_rows)
        one = self._guess_zero()[1]
        n, m = self.cols, self.rows
        R = [ self.matrix[i][:] for i in range(m) ]
        pivotcols = []
        nonpivotcols = []
        i = 0
        if start >= n:
            raise ValueError("Start value cannot be beyond the last column.")
        for j in range(start, n):
            if not R[i][j]:  # search for a nonzero entry in the present column
                for ii in range(i + 1, m):
                    if R[ii][j]:
                        R[i], R[ii] = R[ii], R[i]  # swap rows
                        break
                else:
                    nonpivotcols.append(j)
                    continue  # all entries are zero
            pivotcols.append(j)
            if R[i][j] != one:
                tmp = R[i][j]**-1
                for k in range(n):
                    R[i][k] *= tmp  # make the pivot one
            for ii in range(m):  # remove the column entries above/below the pivot
                if i == ii:
                    continue
                tmp = R[ii][j]
                for k in range(n):
                    R[ii][k] -= tmp * R[i][k]
            i += 1
            if i == m:
                break
        R = Matrix(R)
        R.pivotcols = pivotcols
        R.nonpivotcols = nonpivotcols + list(range(j+1, R.cols))
        # purge zero rows
        if drop_zero_rows:
            l = len(R.pivotcols)
            if not l:
                l = 1  # do not delete all rows
            del R.matrix[l:]
            R.rows = l
        return R

    def _rref_ring(self, start: int = 0, drop_zero_rows: bool = False) -> "Matrix":
        "Compute the reduced echelon form if the base ring is Z_n and no field."
        ring = self.matrix[0][0].ring
        M = self.applyfunc(int)
        done = start
        while done < M.cols:
            M = M.hrnf(start = start, drop_zero_rows = drop_zero_rows)
            done = M.cols
            for i, j in enumerate(M.pivotcols):
                if j < start:
                    continue
                pivot = M.matrix[i][j]
                if pivot >= ring.n:
                    done = min(j, done)
                    pivot %= ring.n
                if pivot:  # find the invertible part
                    g = gcd(pivot, ring.n)
                    while g > 1:
                        pivot //= g
                        g = gcd(pivot, ring.n)
                if pivot > 1:  # we can make the pivot smaller
                    done = min(j, done)
                    tmp = pow(pivot, -1, ring.n)
                    for k in range(j, M.cols):
                        M.matrix[i][k] *= tmp
            M.map(lambda x: x % ring.n)
        M.map(ring)
        return M


    def hrnf(self, start = 0, drop_zero_rows: bool = True) -> "Matrix":
        "Compute the Hermite row normal form."
        n, m = self.cols, self.rows
        if not isinstance(self.matrix[0][0], int):
            raise ValueError("Hermite normal form requires integer entries!")
        H = self[:,:]
        H.pivotcols = []
        H.nonpivotcols = []
        i = 0
        if start >= n:
            raise ValueError("Start value cannot be beyond the last column.")
        for j in range(start, n):
            i0 = i
            minimum = abs(H.matrix[i][j])  # search for the pivot in the present column
            for ii in range(i + 1, m):
                tmp = abs(H.matrix[ii][j])
                if tmp > 0 and (tmp < minimum or minimum == 0):
                    minimum = tmp
                    i0 = ii
            if minimum == 0:
                H.nonpivotcols.append(j)
                continue  # all entrjes are zero
            H.pivotcols.append(j)
            if i0 > i:
                H.swap_rows(i, i0)  # swap rows, to move the pivot in place
            if H.matrix[i][j] < 0:
                H.scale_row(i, -1)  # make the pivot positive
            for ii in range(i + 1, m):  # make the column entries below to the pivot zero
                if H.matrix[ii][j]:
                    g, x, y = egcd(H.matrix[i][j], H.matrix[ii][j], minimal = True)
                    xx = H.matrix[i][j] // g
                    yy = - H.matrix[ii][j] // g
                    H.maop_row(i, ii, x, y, yy, xx)
            for ii in range(i):  # reduce the column entries above to the pivot
                H.addto_row(ii, i, -(H.matrix[ii][j] // H.matrix[i][j]))
            i += 1
            if i >= m:
                break
        H.nonpivotcols += list(range(j+1, H.cols))
        # purge zero rows
        if drop_zero_rows:
            l = len(H.pivotcols)
            if not l:
                l = 1  # do not delete all rows
            del H.matrix[l:]
            H.rows = l
        return H

    def hnf(self, drop_zero_columns: bool = True) -> "Matrix":
        "Compute the Hermite normal form."
        n, m = self.cols, self.rows
        if not isinstance(self.matrix[0][0], int):
            raise ValueError("Hermite normal form requires integer entries!")
        H = self[:,:]
        j = n - 1
        for i in range(m-1,-1,-1):
            j0 = j
            minimum = abs(H.matrix[i][j])  # search for the pivot in the present row
            for jj in range(j):
                tmp = abs(H.matrix[i][jj])
                if tmp > 0 and (tmp < minimum or minimum == 0):
                    minimum = tmp
                    j0 = jj
            if minimum == 0:
                continue  # all entries are zero
            if j0 < j:
                H.swap_columns(j, j0)  # swap columns, to move the pivot in place
            if H.matrix[i][j] < 0:
                H.scale_column(j, -1)  # make the pivot positive
            for jj in range(j):  # make the row left to the pivot zero
                if H.matrix[i][jj]:
                    g, x, y = egcd(H.matrix[i][j], H.matrix[i][jj], minimal = True)
                    xx = H.matrix[i][j] // g
                    yy = - H.matrix[i][jj] // g
                    H.maop_column(j, jj, x, y, yy, xx)
            for jj in range(j + 1, n):  # reduce the row entries right to the pivot
                H.addto_column(jj, j, -(H.matrix[i][jj] // H.matrix[i][j]))
            j -= 1
            if j < 0:
                break
        if drop_zero_columns:
            while H.cols > 1 and all(not H.matrix[i][0] for i in range(m)):  # remove zero columns
                H = H[:, 1:]
        return H

    def snf(self, drop_zero_rows: bool = False, drop_zero_columns: bool = False, include_S: bool = True, include_T: bool = True) -> "Matrix":
        "Computes the Smith normal form D of a matrix A with integer coefficients together with invertible matrices S and T such that D = S * A * T."
        if not isinstance(self.matrix[0][0], int):
            raise ValueError("Smith normal form requires integer entries!")
        m, n = self.rows, self.cols
        A = self[:,:]
        if include_T:
            T = A.eye(n)
        if include_S:
            S = A.eye(m)
        for i in range(min(n,m)):
            minimum = abs(A.matrix[i][i])  # search for the pivot
            i0, j0 = i, i
            for ii in range(i, m):
                for jj in range(i, n):
                    tmp = abs(A.matrix[ii][jj])
                    if tmp > 0 and (tmp < minimum or minimum == 0):
                        minimum = tmp
                        i0, j0 = ii, jj
            if not minimum:
                break
            if j0 != i:  # swap columns, to move the pivot in place
                if include_T:
                    T.swap_columns(i, j0)
                A.swap_columns(i, j0)
            if i0 != i:  # swap rows, to move the pivot in place
                if include_S:
                    S.swap_rows(i, i0)
                A.swap_rows(i, i0)
            if A[i, i] < 0:  # make the pivot positive
                if include_S:
                    S.scale_row(i, -1)
                A.scale_row(i, -1)
            done = False
            while not done:
                for jj in range(i+1, n):
                    if A.matrix[i][jj] == 0:
                        continue
                    g, x, y = egcd(A.matrix[i][i], A.matrix[i][jj], minimal = True)
                    xx = A.matrix[i][i] // g
                    yy = A.matrix[i][jj] // g
                    if include_T:
                        T.maop_column(i, jj, x, y, -yy, xx)
                    A.maop_column(i, jj, x, y, -yy, xx)
                for ii in range(i+1, m):
                    if A.matrix[ii][i] == 0:
                        continue
                    g, x, y = egcd(A.matrix[i][i], A.matrix[ii][i], minimal = True)
                    xx = A.matrix[i][i] // g
                    yy = -A.matrix[ii][i] // g
                    if include_S:
                        S.maop_row(i, ii, x, y, yy, xx)
                    A.maop_row(i, ii, x, y, yy, xx)
                done = True
                for jj in range(i+1, n):
                    if A[i,jj] != 0:
                        done = False
                        break
        for l in range(min(n,m)-1, 0, -1):
            for i in range(l):
                if A.matrix[i][i] and A.matrix[i+1][i+1] % A.matrix[i][i]:
                    g, x, y = egcd(A.matrix[i][i], A.matrix[i+1][i+1], minimal = True)
                    aa= A.matrix[i][i] //g
                    bb = -A.matrix[i+1][i+1]//g
                    by = bb * y
                    if include_T:
                        T.addto_column(i, i+1)
                        T.addto_column(i+1, i, by)
                    A.addto_column(i, i+1)
                    A.addto_column(i+1, i, by)
                    if include_S:
                        S.maop_row(i, i+1, x, y, bb, aa)
                    A.maop_row(i, i+1, x, y, bb, aa)
        if drop_zero_rows or drop_zero_columns:
            for i in range(min(n,m)):
                if A[i,i] == 0:
                    break
            else:
                i += 1
            i = max(i, 1)
        if drop_zero_rows:
            if i < m:
                del A[i:, :]
                if include_S:
                    del S[i:, :]
        if drop_zero_columns:
            if i < n:
                del A[:, i:]
                if include_T:
                    del T[:, i:]
        if include_S and include_T:
            return A, S, T
        if include_S:
            return A, S
        if include_T:
            return A, T
        return A

    def left_standard_form(self) -> "Matrix":
        "Compute the left standard form."
        # reduced row echelon form
        M = self.rref(drop_zero_rows = True)
        # permute columns to get the identity on the left
        if M.pivotcols != list(range(min(M.rows, M.cols))):
            M.permute_columns(M.pivotcols + M.nonpivotcols)
        return M

    def kernel(self) -> "Matrix":
        "Compute a basis for the kernel."
        if hasattr(self.matrix[0][0], "ring") and not self.matrix[0][0].ring.is_field():
            ring = self.matrix[0][0].ring
            M = self.applyfunc(int)
            D, T = M.snf(include_S=False, drop_zero_rows=True)
            D.map(ring)
            T.map(ring)
            K = D.eye(D.cols)
            shift = 0
            for i in range(D.rows):
                g = gcd(int(D.matrix[i][i]), ring.n)
                if g == 1:
                    if shift == D.cols - 1:
                        K.matrix[i][i - shift] = ring(0)
                        break
                    K.delete_columns(i - shift)
                    shift += 1
                elif g < ring.n:
                    K.matrix[i][i-shift] = ring(ring.n // g)
            return T * K
        _, one = self._guess_zero()
        M = self.rref(drop_zero_rows = True)
        K = M.zeros(M.cols, max(1,len(M.nonpivotcols)))
        for k, j in enumerate(M.nonpivotcols):
            K[j, k] = one
            for l, i in enumerate(M.pivotcols):
                K[i, k] = - M[l, j]
        return K

    def det(self) -> int:
        "Compute the determinant."
        n, m = self.cols, self.rows
        if n != m:
            raise ValueError("Matrix must be square!")
        if hasattr(self.matrix[0][0], "ring") and not self.matrix[0][0].ring.is_field():
            # the matrix is over a ring (not a field)
            ring = self.matrix[0][0].ring
            R = [ list(map(lambda x: Fraction(int(x)), self.matrix[i])) for i in range(m) ]
            zero, one = ring(0), 1
        else:
            ring = None
            R = [ self.matrix[i][:] for i in range(m) ]
            zero, one = self._guess_zero()
        D = one
        i = 0
        for j in range(n):
            if not R[i][j]:  # search for a nonzero entry in the present column
                for ii in range(i+1, m):
                    if R[ii][j]:
                        D *= -one
                        R[i], R[ii] = R[ii], R[i]  # swap rows
                        break
                else:  # all entries are zero
                    return zero
            if R[i][j] != one:
                D *= R[i][j]
                tmp = R[i][j]**-1
                for k in range(n):
                    R[i][k] *= tmp  # make the pivot one
            for ii in range(i + 1, n):  # remove the column entries below the pivot
                if i == ii:
                    continue
                tmp = R[ii][j]
                for k in range(n):
                    R[ii][k] -= tmp * R[i][k]
            i += 1
        if ring:
            return ring(D)
        return D

    def rank(self) -> int:
        "Compute the rank."
        M = self.rref()
        return len(M.pivotcols)

    def nullity(self) -> int:
        "Compute the nullity."
        return self.cols - self.rank()

    def inv(self, left = False) -> "Matrix":
        "Compute the (left) inverse."
        if not left and self.rows != self.cols:
            raise ValueError("Matrix must be square!")
        zero, one = self._guess_zero()
        n = self.cols
        m = self.rows
        M = [ [] ] * m
        for i in range(m):
            tmp = [ zero ] * m
            tmp[i] = one
            M[i] = self.matrix[i][:] + tmp
        M = self.__class__(M).rref()
        if not left and M.pivotcols[self.cols - 1] != self.cols -1:
            raise ValueError("Matrix is not invertible!")
        if hasattr(self.matrix[0][0], "ring") and not self.matrix[0][0].ring.is_field():
            # the matrix is over a ring (not a field)
            for i, j in enumerate(M.pivotcols):
                if M.matrix[i][j] != one:
                    raise ValueError("Matrix is not invertible!")
        return M[:, n:]

    def solve(self, b: list|tuple) -> "Matrix":
        "Solve the linear system with given inhomogenous vector."
        if isinstance(b, list|tuple):
            b = self.__class__(b)
        if self.rows != b.rows or b.cols != 1:
            raise ValueError("Matrix dimensions do not match.")
        if hasattr(self.matrix[0][0], "ring") and not self.matrix[0][0].ring.is_field():
            # the matrix is over a ring (not a field)
            ring = self.matrix[0][0].ring
            A = self.applyfunc(int)
            D, S, T = A.snf()
            D.map(ring)
            S.map(ring)
            T.map(ring)
            b = S * b
            for i in range(min(A.rows, A.cols), A.rows):
                if b[i]:
                    return None
            y = [ ring(0) ] * A.cols
            for i in range(min(A.rows, A.cols)):
                y[i] = D[i,i].solve(b[i])
                if y[i] is None:
                    return None
            return T * Matrix(y)
        # the matrix is over a field
        A = self[:,:]
        A.append_column(b)
        A = A.rref(drop_zero_rows = True)
        if not any(A.matrix[-1][:-1]) and A.matrix[-1][-1]:
            return None  # Not solvable
        solution = self.zeros(self.cols, 1)
        for i, j in enumerate(A.pivotcols):
            solution[j] = A.matrix[i][-1]
        return solution

    def is_unimodular(self) -> bool:
        "Test if the matrix is unimodular."
        if self.rows != self.cols:
            return False

        def is_integer(i):
            if isinstance(i, int) or (isinstance(i, Fraction) and i.denominator == 1):
                return True
            return False
        return all(is_integer(i) for i in self) and self.det()**2 == 1

    def zeros(self, m: int = None, n: int = None) -> "Matrix":
        "Returns a zero matrix of the same dimension."
        if not m and not n:
            n, m = self.cols, self.rows
        elif not n:
            n = m
        if n < 1 or m < 1:
            raise ValueError(f"Matrix dimensions {m}x{n} must be positive!")
        zero = self._guess_zero()[0]
        return self.__class__([[zero for j in range(n)] for i in range(m)])

    def eye(self, m: int = None, n: int = None) -> "Matrix":
        "Returns an identity matrix of the same dimension."
        def delta(i, j):
            if i == j:
                return one
            return zero
        if not m and not n:
            n, m = self.cols, self.rows
        elif not n:
            n = m
        if n < 1 or m < 1:
            raise ValueError(f"Matrix dimensions {m}x{n} must be positive!")
        zero, one = self._guess_zero()
        return self.__class__([[delta(i, j) for j in range(n)] for i in range(m)])


def zeros(m: int, n: int = None, zero=0, ring=None) -> "Matrix":
    "Returns a zero matrix of the given dimension."
    if not n:
        n = m
    if n < 1 or m < 1:
        raise ValueError(f"Matrix dimensions {m}x{n} must be positive!")
    return Matrix([[zero for j in range(n)] for i in range(m)], ring=ring)


def eye(m: int, n: int = None, zero=0, one=1, ring=None) -> "Matrix":
    "Returns an identity matrix of the given dimension."
    def delta(i, j):
        if i == j:
            return one
        return zero
    if not n:
        n = m
    if n < 1 or m < 1:
        raise ValueError(f"Matrix dimensions {m}x{n} must be positive!")
    return Matrix([[delta(i, j) for j in range(n)] for i in range(m)], ring=ring)

def rotate(l: list, n: int) -> list:
    "Rotate a list cyclically n places to the left."
    n %= len(l)
    return l[n:] + l[:n]

def circulant(vector: list|tuple, m: int = None, ring=None) -> "Matrix":
    "Returns a circulant matrix from the given vector."
    if m is None:
        m = len(vector)
    vector = list(reversed(vector))
    return Matrix([rotate(vector, -n-1) for n in range(m)], ring=ring)

class BinaryMatrix:
    """
    Binary Matrix class.

    Example:

    To define a binary matrix use
    >>> BinaryMatrix([[0, 1], [1, 0]])
    [01]
    [10]
    """
    def __init__(self, matrix: list|tuple|Matrix, cols: int|None = None):
        if isinstance(matrix, Matrix):
            matrix = matrix.matrix
        elif not (isinstance(matrix, list|tuple) and matrix):
            raise ValueError("The given matrix must be a nonempty list.")
        if isinstance(matrix[0], list|tuple):  # list of lists
            if cols is None:
                cols = len(matrix[0])
            matrix = [ self.from_bits(map(bool, row)) for row in matrix]
        else:  # list of ints
            if not isinstance(matrix[0], int):
                raise ValueError("The given matrix must be a list of integers or bits.")
            if cols is None:
                cols = max(row.bit_length() for row in matrix)
                cols = max(1, cols)
        self.matrix = matrix  # matrix as a list (rows) of integers (columns bits)
        self.rows = len(self.matrix)  # number of rows
        self.cols = cols  # number of columns
        self.pivotcols = None  # set by rref
        self.nonpivotcols = None  # set by rref

    def __repr__(self):
        out = ''
        for row in self.matrix:
            out += "[" + format(row, f"0{self.cols}b") + "]\n"
        return out[:-1]

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.rows != other.rows or self.cols != other.cols:
            return False
        return self.matrix == other.matrix

    def __bool__(self):
        return any(bool(row != 0) for row in self.matrix)

    def __getitem__(self, item):
        if isinstance(item, tuple):
            i, j = item
            if isinstance(i, int) and isinstance(j, int):
                mask = 1 << self.cols - 1 - j
                if self.matrix[i] & mask:
                    return 1
                return 0
        raise NotImplementedError('Only getting single bits is supported.')

    def __setitem__(self, item, value):
        if isinstance(item, tuple):
            i, j = item
            if isinstance(i, int) and isinstance(j, int):
                if value:
                    mask = 1 << self.cols - 1 - j
                    self.matrix[i] |= mask
                else:
                    mask = ~(1 << self.cols - 1 - j)
                    self.matrix[i] &= mask
                return
        raise NotImplementedError('Only setting single bits is supported.')

    def __delitem__(self, item):
        if isinstance(item, tuple):
            i, j = item
            if isinstance(i, int):
                rows = [i]
            elif isinstance(i, list):
                rows = set(i)
            else:
                rows = range(self.rows)[i]
            if isinstance(j, int):
                cols = [j]
            elif isinstance(j, list):
                cols = set(j)
            else:
                cols = range(self.cols)[j]
            if len(cols) == self.cols:
                self.delete_rows(rows)
                return
            if len(rows) == self.rows:
                self.delete_columns(cols)
                return
        raise ValueError("Can only delete entire rows or entire columns!")

    def delete_rows(self, rows: int|list) -> None:
        "Deletes a row or a list of rows."
        if isinstance(rows, int):
            rows = [ rows ]
        rows = list(map(lambda x: x % self.rows, rows))
        rows = set(rows)
        if len(rows) >= self.rows:
            raise ValueError("Cannot delete all rows.")
        for i in sorted(rows, reverse = True):
            del self.matrix[i]
        self.rows -= len(rows)

    def delete_columns(self, cols: int|list) -> None:
        "Deletes a column or a list of columns."
        if isinstance(cols, int):
            cols = [ cols ]
        cols = list(map(lambda x: x % self.cols, cols))
        cols = set(cols)
        if len(cols) >= self.cols:
            raise ValueError("Cannot delete all columns.")
        cols = sorted(cols, reverse = True)
        l = 0
        while l < len(cols):
            end = cols[l] # end index
            while l < len(cols) - 1 and cols[l] == cols[l+1] + 1:
                l += 1
            j = cols[l] # start index
            k = end - j + 1 # range
            l += 1
            mask = (1 << self.cols - k - j) - 1
            for i in range(self.rows):
                low = self.matrix[i] & mask
                self.matrix[i] >>= k
                self.matrix[i] &= ~mask
                self.matrix[i] |= low
        self.cols -= len(cols)

    def __add__(self, other) -> "BinaryMatrix":
        if isinstance(other, self.__class__):
            if other.cols != self.cols or other.rows != self.rows:
                raise NotImplementedError("Matrix dimensions do not match!")
            return self.__class__([ x ^ y for x, y in zip(self.matrix, other.matrix)], cols = self.cols)
        return NotImplemented

    __sub__ = __add__

    def __pos__(self) -> "BinaryMatrix":
        return self

    __neg__ = __pos__

    def __mul__(self, other) -> "BinaryMatrix":
        if isinstance(other, self.__class__):
            return self.multiply(other)
        if isinstance(other, int):
            if other % 2:
                return self
            return self.zeros()
        return NotImplemented

    def __rmul__(self, other) -> "BinaryMatrix":
        if isinstance(other, int):
            if other % 2:
                return self
            return self.zeros()
        return NotImplemented

    def multiply(self, other) -> "BinaryMatrix":
        "Matrix multiplication."
        if self.cols != other.rows:
            raise NotImplementedError("Matrix dimensions do not match!")
        #raise NotImplementedError("Matrix multiplication not implemented!")
        mask = 2**(other.cols - 1)
        result = [0] * self.rows
        for _ in range(other.cols):
            b = 0
            for row in other.matrix:
                b <<= 1
                if row & mask:
                    b |= 1
            for i, row in enumerate(self.matrix):
                parity = 0
                tmp = row & b
                while tmp:
                    parity = ~parity
                    tmp = tmp & (tmp - 1)
                result[i] <<= 1
                if parity:
                    result[i] |= 1
            mask >>= 1
        if self.rows == 1 and other.cols == 1:
            return result[0]
        return self.__class__(result, cols = other.cols)

    def to_bits(self, n:int, length: int = None) -> list[int]:
        "Convert an integer to a list of bits"
        if length is None:
            length = n.bit_length()
        return [n >> i & 1 for i in range(length - 1, -1, -1)]

    def from_bits(self, b: list[int]) -> int:
        "Convert a list of bits to an integer."
        n = 0
        for bit in b:
            n <<= 1
            n += bit
        return n

    def bitmatrix(self) -> list[list]:
        "Return as a matrix (with rows given by the list of columns bits) of bits."
        return [ self.to_bits(row, self.cols) for row in self.matrix ]

    def add_column(self, col: list|int) -> None:
        "Add a column to the matrix."
        if isinstance(col, int):
            col = self.to_bits(col, self.rows)
        if len(col) != self.rows:
            raise ValueError("The length must equal the number of rows!")
        self.cols += 1
        for i, b in enumerate(col):
            self.matrix[i] <<= 1
            if b:
                self.matrix[i] |= 1

    def add_row(self, row: list|int) -> None:
        "Add a row to the matrix."
        if isinstance(row, list):
            if len(row) != self.cols:
                raise ValueError("The length must equal the number of columns!")
            row = self.from_bits(row)
        self.rows += 1
        self.matrix.append(row)

    def swap_columns(self, i: int, j: int) -> None:
        "Swap two columns."
        for k in range(self.rows):
            b = self.matrix[k]
            x = ((b >> i) ^ (b >> j)) & 1
            self.matrix[k] ^= ((x << i) | (x << j))

    def swap_rows(self, i: int, j: int) -> None:
        "Swap two rows."
        self.matrix[i], self.matrix[j] = self.matrix[j], self.matrix[i]

    def permute_columns(self, permutation: list) -> None:
        "Permute columns according to a list of new positions."
        if len(permutation) != self.cols:
            raise ValueError(f"The argument must be a list of indices of length {self.cols}.")
        for i, row in enumerate(self.matrix):
            bits = self.to_bits(row, self.cols)
            bits = [ bits[j] for j in permutation]
            self.matrix[i] = self.from_bits(bits)

    def permute_rows(self, permutation: list) -> None:
        "Permute rows according to a list of new positions."
        if len(permutation) != self.rows:
            raise ValueError(f"The argument must be a list of indices of length {self.rows}.")
        self.matrix = [ self.matrix[i] for i in permutation]

    def transpose(self) -> "BinaryMatrix":
        "Transposed matrix."
        return self.__class__([list(i) for i in zip(*self.bitmatrix())])

    def apply(self, x: int|list) -> int|list:
        "Applies the matrix to a vector given as list of bits or integer."
        if isinstance(x, list):
            if len(x) != self.cols:
                raise ValueError("The length must equal the number of columns!")
            as_list = True
            x = self.from_bits(x)
        else:
            as_list = False
        if x >= 2**self.cols:
            raise ValueError("The length is larger than the number of columns!")
        res = []
        for row in self.matrix:
            tmp = row & x
            parity = 0
            while tmp:
                parity = ~parity
                tmp = tmp & (tmp - 1)
            if parity:
                res.append(1)
            else:
                res.append(0)
        if as_list:
            return res
        return self.from_bits(res)

    def rref(self, start: int = 0, reduce: bool = True, drop_zero_rows: bool = False) -> "Matrix":
        "Row reduced echelon form."
        rref = [ None ] * self.cols  # store rows accoring to leading bit
        rows = self.matrix[:]  # copy
        zerorows = []  # we store zero rows here
        if start:
            startmask = (1 << (self.cols - start)) -1
        row = None
        while (rows or row is not None):
            if row is None:
                row = rows.pop()
            if start:
                lb = (row & startmask).bit_length() - 1 # leading bit
            else:
                lb = row.bit_length() - 1 # leading bit
            if lb == -1: # the row is zero
                zerorows.append(row)
                row = None
            elif rref[lb] is None:  # the row is new
                rref[lb] = row
                row = None
            else:  # reduce with the one we already have
                row ^= rref[lb]
        if reduce:  # clear out above pivots
            for i, row in enumerate(rref):
                if row is None:
                    continue
                mask = 1 << i
                for j in range(i+1,self.cols):
                    if rref[j] is None:
                        continue
                    if rref[j] & mask:
                        rref[j] ^= row
        pivotcols = []
        nonpivotcols = []
        for j, row in enumerate(reversed(rref)):  # remove nonexisting rows
            if row is None:
                if  j >= start:
                    nonpivotcols.append(j)
                continue
            pivotcols.append(j)
            rows.append(row)
        if not drop_zero_rows:
            rows += zerorows
        if not rows:
            rows = [ 0 ]
        rref = self.__class__(rows, cols = self.cols)
        rref.pivotcols = pivotcols
        rref.nonpivotcols = nonpivotcols
        return rref

    def left_standard_form(self) -> "BinaryMatrix":
        "Compute the left standard form."
        # reduced row echelon form
        M = self.rref(drop_zero_rows = True)
        # permute columns to get the identity on the left
        if M.pivotcols != list(range(min(M.rows, M.cols))):
            M.permute_columns(M.pivotcols + M.nonpivotcols)
        return M

    def det(self) -> int:
        "Compute the determinant."
        if self.rows != self.cols:
            raise ValueError("Matrix must be square!")
        if self.rows == 1:
            return self.matrix[0]
        M = self.rref(reduce = False, drop_zero_rows = True)
        if M.rows == M.cols:
            return 1
        return 0

    def rank(self) -> int:
        "Compute the rank."
        M = self.rref(drop_zero_rows = True)
        return len(M.pivotcols)

    def nullity(self) -> int:
        "Compute the nullity."
        return self.cols - self.rank()

    def kernel(self) -> "BinaryMatrix":
        "Compute a basis for the kernel."
        M = self.rref()
        K = M.zeros(M.cols, max(1,len(M.nonpivotcols)))
        for k, j in enumerate(M.nonpivotcols):
            K[j, k] = 1
            for l, i in enumerate(M.pivotcols):
                K[i, k] = M[l, j]
        return K

    def inv(self, left = False) -> "BinaryMatrix":
        "Compute the (left) inverse."
        if not left and self.rows != self.cols:
            raise ValueError("Matrix must be square!")
        M = self.matrix[:]
        for i in range(self.rows):
            M[i] <<= self.rows
            M[i] |= 1 << (self.rows - i -1)
        M = self.__class__(M, cols = self.cols + self.rows).rref()
        if not left and M.pivotcols[self.cols - 1] != self.cols -1:
            raise ValueError("Matrix is not invertible!")
        mask = 2**self.rows - 1
        for i in range(M.rows):
            M.matrix[i] &= mask
        M.cols = self.rows
        return M

    def solve(self, b: list|int) -> list|int:
        "Solve the linear system with given inhomogenous vector."
        as_list = True
        as_matrix = False
        if isinstance(b, int):
            as_list = False
        elif isinstance(b, self.__class__):
            if self.rows != b.rows or b.cols != 1:
                raise ValueError("Matrix dimensions do not match.")
            as_matrix = True
            b = b.matrix
        elif not isinstance(b, list):
            raise ValueError("The inhomogenous vector must be a list of bits or an integer.")
        A = self.__class__(self.matrix[:], self.cols)
        A.add_column(b)
        A = A.rref(drop_zero_rows = True)
        solution = [ 0 ] * self.cols
        if not A.pivotcols: # A is zero
            if as_list:
                return solution
            return 0
        if A.pivotcols[-1] >= self.cols:
            return None  # Not solvable
        for i in range(A.rows):
            solution[A.pivotcols[i]] = A.matrix[i] & 1
        if as_list:
            if as_matrix:
                return self.__class__(solution)
            return solution
        return self.from_bits(solution)

    def zeros(self, m: int = None, n: int = None) -> "BinaryMatrix":
        "Returns a zero matrix of the same dimension."
        if not m and not n:
            n, m = self.cols, self.rows
        elif not n:
            n = m
        if n < 1 or m < 1:
            raise ValueError(f"Matrix dimensions {m}x{n} must be positive!")
        return self.__class__([ 0 for i in range(m)], cols = n)

    def eye(self, m: int = None, n: int = None) -> "BinaryMatrix":
        "Returns an identity matrix of the same dimension."
        if not m and not n:
            n, m = self.cols, self.rows
        elif not n:
            n = m
        if n < 1 or m < 1:
            raise ValueError(f"Matrix dimensions {m}x{n} must be positive!")
        return self.__class__([ 1 << n - i - 1 for i in range(m)])
