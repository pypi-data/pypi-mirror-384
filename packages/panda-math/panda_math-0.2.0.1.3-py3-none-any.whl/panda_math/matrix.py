import numpy as np
from typing import (
    List,
    Union,
    Optional,
    Any,
    Iterator,
    TypeVar,
    Tuple,
    Callable,
    overload,
    Sequence,
)

# Import Vector only for type checking to avoid circular import at runtime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .vector import Vector2, Vector3, Vector4

M = TypeVar("M", bound="Matrix")

Number = Union[int, float]


class Matrix:
    def __init__(
        self,
        data: Union[np.ndarray, Sequence[Sequence[Number]], None] = None,
        rows: int = 2,
        cols: int = 2,
    ) -> None:
        self.data: List[List[Number]]
        self.rows: int
        self.cols: int

        if isinstance(data, np.ndarray) and data.ndim == 2:
            self.data = data.tolist()
            self.rows = len(self.data)
            self.cols = len(self.data[0]) if self.rows > 0 else 0

        elif isinstance(data, Sequence):
            # here, data is Sequence[Sequence[Number]]
            self.data = [list(v) for v in data]
            self.rows = len(self.data)
            self.cols = len(self.data[0]) if self.rows > 0 else 0

        elif data is None:
            self.rows = rows
            self.cols = cols
            self.data = [[0 for _ in range(cols)] for _ in range(rows)]

        else:
            raise ValueError("Either data or dimensions (rows, cols) must be provided")

        if self.rows > 0:
            for row in self.data:
                if len(row) != self.cols:
                    raise ValueError("All rows must have the same number of columns")

    def __str__(self) -> str:
        rows_str = []
        for row in self.data:
            rows_str.append(
                "["
                + ", ".join(
                    f"{val:.6g}" if isinstance(val, float) else str(val) for val in row
                )
                + "]"
            )
        return f"Matrix({self.rows}×{self.cols}):\n" + "\n".join(rows_str)

    def __repr__(self) -> str:
        return str(self)

    @overload
    def __getitem__(self, key: int) -> Sequence[Number]: ...
    
    @overload
    def __getitem__(self, key: Tuple[int, int]) -> Number: ...

    def __getitem__(self, key):
        if isinstance(key, tuple):
            i, j = key
            return self.data[i][j]
        elif isinstance(key, int):
            return self.data[key]
        else:
            raise TypeError("Invalid index type")

    @overload
    def __setitem__(self, key: int, value: Sequence[Number]): ...
    
    @overload
    def __setitem__(self, key: Tuple[int, int], value: Number): ...

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            i, j = key
            self.data[i][j] = value
        elif isinstance(key, int):
            self.data[key] = list(value)  # <- cast Sequence -> list internally
        else:
            raise TypeError("Invalid index type")

    def __iter__(self) -> Iterator[List[Number]]:
        return iter(self.data)

    def __len__(self) -> int:
        return self.rows

    def __add__(self, other: Union["Matrix", Number]) -> "Matrix":
        if isinstance(other, Matrix):
            if self.rows != other.rows or self.cols != other.cols:
                raise ValueError("Matrix dimensions do not match for addition")
            result = Matrix(rows=self.rows, cols=self.cols)
            for i in range(self.rows):
                for j in range(self.cols):
                    result[i, j] = self[i, j] + other[i, j]
            return result
        elif isinstance(other, (int, float)):
            result = Matrix(rows=self.rows, cols=self.cols)
            for i in range(self.rows):
                for j in range(self.cols):
                    result[i, j] = self[i, j] + other
            return result
        return NotImplemented

    def __radd__(self, other: Number) -> "Matrix":
        return self.__add__(other)

    def __sub__(self, other: Union["Matrix", Number]) -> "Matrix":
        if isinstance(other, Matrix):
            if self.rows != other.rows or self.cols != other.cols:
                raise ValueError("Matrix dimensions do not match for subtraction")
            result = Matrix(rows=self.rows, cols=self.cols)
            for i in range(self.rows):
                for j in range(self.cols):
                    result[i, j] = self[i, j] - other[i, j]
            return result
        elif isinstance(other, (int, float)):
            result = Matrix(rows=self.rows, cols=self.cols)
            for i in range(self.rows):
                for j in range(self.cols):
                    result[i, j] = self[i, j] - other
            return result
        return NotImplemented

    def __rsub__(self, other: Number) -> "Matrix":
        if isinstance(other, (int, float)):
            result = Matrix(rows=self.rows, cols=self.cols)
            for i in range(self.rows):
                for j in range(self.cols):
                    result[i, j] = other - self[i, j]
            return result
        return NotImplemented

    @overload
    def __mul__(self, other: "Matrix") -> "Matrix": ...
    @overload
    def __mul__(self, other: "Vector2") -> "Vector2": ...
    @overload
    def __mul__(self, other: "Vector3") -> "Vector3": ...
    @overload
    def __mul__(self, other: "Vector4") -> "Vector4": ...
    @overload
    def __mul__(self, other: Number) -> "Matrix": ...

    def __mul__(self, other):
        from .vector import Vector2, Vector3, Vector4

        if isinstance(other, Matrix):
            if self.cols != other.rows:
                raise ValueError(
                    f"Matrix dimensions incompatible for multiplication: {self.rows}×{self.cols} and {other.rows}×{other.cols}"
                )
            result = Matrix(rows=self.rows, cols=other.cols)
            for i in range(self.rows):
                for j in range(other.cols):
                    sum_val = 0
                    for k in range(self.cols):
                        sum_val += self[i, k] * other[k, j]
                    result[i, j] = sum_val
            return result
        elif isinstance(other, Vector2):
            if self.cols != 2:
                raise ValueError(
                    f"Cannot multiply Matrix({self.rows}×{self.cols}) with Vector2(2)"
                )
            result = [0.0] * self.rows
            for i in range(self.rows):
                result[i] = self[i, 0] * other.x + self[i, 1] * other.y
            if self.rows == 2:
                return Vector2(result[0], result[1])
            elif self.rows == 3:
                return Vector3(result[0], result[1], result[2])
            elif self.rows == 4:
                return Vector4(result[0], result[1], result[2], result[3])
            return result
        elif isinstance(other, Vector3):
            if self.cols != 3:
                raise ValueError(
                    f"Cannot multiply Matrix({self.rows}×{self.cols}) with Vector3(3)"
                )
            result = [0.0] * self.rows
            for i in range(self.rows):
                result[i] = (
                    self[i, 0] * other.x + self[i, 1] * other.y + self[i, 2] * other.z
                )
            if self.rows == 2:
                return Vector2(result[0], result[1])
            elif self.rows == 3:
                return Vector3(result[0], result[1], result[2])
            elif self.rows == 4:
                return Vector4(result[0], result[1], result[2], result[3])
            return result
        elif isinstance(other, Vector4):
            if self.cols != 4:
                raise ValueError(
                    f"Cannot multiply Matrix({self.rows}×{self.cols}) with Vector4(4)"
                )
            result = [0.0] * self.rows
            for i in range(self.rows):
                result[i] = (
                    self[i, 0] * other.x
                    + self[i, 1] * other.y
                    + self[i, 2] * other.z
                    + self[i, 3] * other.w
                )
            if self.rows == 2:
                return Vector2(result[0], result[1])
            elif self.rows == 3:
                return Vector3(result[0], result[1], result[2])
            elif self.rows == 4:
                return Vector4(result[0], result[1], result[2], result[3])
            return result
        elif isinstance(other, (int, float)):
            result = Matrix(rows=self.rows, cols=self.cols)
            for i in range(self.rows):
                for j in range(self.cols):
                    result[i, j] = self[i, j] * other
            return result
        return NotImplemented

    def __rmul__(self, other: Number) -> "Matrix":
        return self * other

    def __truediv__(self, other: Number) -> "Matrix":
        if isinstance(other, (int, float)):
            if other == 0:
                raise ZeroDivisionError("Division by zero")
            result = Matrix(rows=self.rows, cols=self.cols)
            for i in range(self.rows):
                for j in range(self.cols):
                    result[i, j] = self[i, j] / other
            return result
        return NotImplemented

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Matrix):
            return NotImplemented
        if self.rows != other.rows or self.cols != other.cols:
            return False
        for i in range(self.rows):
            for j in range(self.cols):
                if self[i, j] != other[i, j]:
                    return False
        return True

    def transpose(self) -> "Matrix":
        result = Matrix(rows=self.cols, cols=self.rows)
        for i in range(self.rows):
            for j in range(self.cols):
                result[j, i] = self[i, j]
        return result

    def determinant(self) -> float:
        if self.rows != self.cols:
            raise ValueError("Determinant only defined for square matrices")

        if self.rows == 1:
            return self[0, 0]
        elif self.rows == 2:
            return self[0, 0] * self[1, 1] - self[0, 1] * self[1, 0]
        elif self.rows == 3:
            # Manual calculation for 3x3 matrices
            a, b, c = self[0, 0], self[0, 1], self[0, 2]
            d, e, f = self[1, 0], self[1, 1], self[1, 2]
            g, h, i = self[2, 0], self[2, 1], self[2, 2]

            return (a * e * i + b * f * g + c * d * h) - (
                c * e * g + b * d * i + a * f * h
            )
        elif self.rows == 4:
            # Use cofactor expansion for 4x4
            det = 0
            for j in range(4):
                det += self[0, j] * self.cofactor(0, j)
            return det
        else:
            # For larger matrices, use numpy's determinant
            return float(np.linalg.det(self.to_numpy()))

    def cofactor(self, row: int, col: int) -> float:
        """Calculate the cofactor of the matrix element at (row, col)"""
        minor = self.minor(row, col)
        return (-1) ** (row + col) * minor.determinant()

    def minor(self, row: int, col: int) -> "Matrix":
        """Return the minor matrix by removing the specified row and column"""
        result = Matrix(rows=self.rows - 1, cols=self.cols - 1)
        r_idx = 0
        for i in range(self.rows):
            if i == row:
                continue
            c_idx = 0
            for j in range(self.cols):
                if j == col:
                    continue
                result[r_idx, c_idx] = self[i, j]
                c_idx += 1
            r_idx += 1
        return result

    def adjugate(self) -> "Matrix":
        """Calculate the adjugate (adjoint) matrix"""
        if self.rows != self.cols:
            raise ValueError("Adjugate only defined for square matrices")

        result = Matrix(rows=self.rows, cols=self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                result[i, j] = self.cofactor(j, i)  # Note: transpose of cofactor matrix
        return result

    def inverse(self) -> "Matrix":
        if self.rows != self.cols:
            raise ValueError("Inverse only defined for square matrices")

        det = self.determinant()
        if abs(det) < 1e-10:
            raise ValueError("Matrix is singular (determinant close to zero)")

        if self.rows == 1:
            result = Matrix(rows=1, cols=1)
            result[0, 0] = 1.0 / self[0, 0]
            return result
        elif self.rows == 2:
            result = Matrix(rows=2, cols=2)
            inv_det = 1.0 / det
            result[0, 0] = self[1, 1] * inv_det
            result[0, 1] = -self[0, 1] * inv_det
            result[1, 0] = -self[1, 0] * inv_det
            result[1, 1] = self[0, 0] * inv_det
            return result
        elif self.rows <= 4:
            # Use adjugate method for small matrices
            adj = self.adjugate()
            return adj * (1.0 / det)
        else:
            # Use numpy for larger matrices
            np_inv = np.linalg.inv(self.to_numpy())
            return Matrix(np_inv)

    def is_singular(self) -> bool:
        if self.rows != self.cols:
            return True
        try:
            det = self.determinant()
            return abs(det) < 1e-10
        except:
            return True

    def is_symmetric(self) -> bool:
        """Check if the matrix is symmetric (equal to its transpose)"""
        if self.rows != self.cols:
            return False

        for i in range(self.rows):
            for j in range(i + 1, self.cols):  # Only check upper triangle
                if abs(self[i, j] - self[j, i]) > 1e-10:
                    return False
        return True

    def is_orthogonal(self) -> bool:
        """Check if the matrix is orthogonal (its transpose equals its inverse)"""
        if self.rows != self.cols:
            return False

        # For an orthogonal matrix, M * M^T = I
        product = self * self.transpose()
        identity = Matrix.identity(self.rows)

        for i in range(self.rows):
            for j in range(self.cols):
                if abs(product[i, j] - identity[i, j]) > 1e-10:
                    return False
        return True

    def trace(self) -> float:
        """Calculate the trace (sum of diagonal elements)"""
        if self.rows != self.cols:
            raise ValueError("Trace only defined for square matrices")

        return sum(self[i, i] for i in range(self.rows))

    def row(self, i: int) -> Union[Sequence[Number], "Vector2", "Vector3", "Vector4"]:
        from .vector import Vector2, Vector3, Vector4

        if i < 0 or i >= self.rows:
            raise IndexError("Row index out of range")

        if self.cols == 2:
            return Vector2(self.data[i][0], self.data[i][1])
        elif self.cols == 3:
            return Vector3(self.data[i][0], self.data[i][1], self.data[i][2])
        elif self.cols == 4:
            return Vector4(
                self.data[i][0], self.data[i][1], self.data[i][2], self.data[i][3]
            )
        return self.data[i]

    def col(self, j: int) -> Union[List[Number], "Vector2", "Vector3", "Vector4"]:
        from .vector import Vector2, Vector3, Vector4

        if j < 0 or j >= self.cols:
            raise IndexError("Column index out of range")

        col_data = [self.data[i][j] for i in range(self.rows)]

        if self.rows == 2:
            return Vector2(col_data[0], col_data[1])
        elif self.rows == 3:
            return Vector3(col_data[0], col_data[1], col_data[2])
        elif self.rows == 4:
            return Vector4(col_data[0], col_data[1], col_data[2], col_data[3])
        return col_data

    def to_numpy(self) -> np.ndarray:
        return np.array(self.data)

    def to_bytes(self, format: str = "float32", order: str = "column"):
        """
        Convert the matrix to bytes suitable for OpenGL/moderngl uniforms.

        Args:
            format: Data format ('float32', 'float64', 'int32', 'uint32')
            order: Matrix storage order ('column' for OpenGL column-major, 'row' for row-major)

        Returns:
            bytes: The matrix data converted to bytes suitable for OpenGL uniforms

        Example:
            # For moderngl uniform buffer
            matrix_bytes = my_matrix.to_bytes('float32', 'column')
            uniform_buffer = ctx.buffer(matrix_bytes)

            # For shader uniform
            shader['u_transform'].write(my_matrix.to_bytes())
        """
        import struct

        if order == "column":
            # OpenGL expects column-major order
            flat_data = []
            for j in range(self.cols):
                for i in range(self.rows):
                    flat_data.append(float(self[i, j]))
        else:
            # Row-major order
            flat_data = []
            for i in range(self.rows):
                for j in range(self.cols):
                    flat_data.append(float(self[i, j]))

        # Pack the data based on format
        if format == "float32":
            pack_format = f"{len(flat_data)}f"
        elif format == "float64":
            pack_format = f"{len(flat_data)}d"
        elif format == "int32":
            pack_format = f"{len(flat_data)}i"
            flat_data = [int(x) for x in flat_data]
        elif format == "uint32":
            pack_format = f"{len(flat_data)}I"
            flat_data = [int(abs(x)) for x in flat_data]
        else:
            raise ValueError(
                f"Unsupported format: {format}. Use 'float32', 'float64', 'int32', or 'uint32'"
            )

        return struct.pack(pack_format, *flat_data)

    @classmethod
    def from_numpy(cls, array: np.ndarray) -> "Matrix":
        return cls(array)

    @classmethod
    def identity(cls, size: int) -> "Matrix":
        result = cls(rows=size, cols=size)
        for i in range(size):
            result[i, i] = 1
        return result

    @classmethod
    def from_rows(cls, *rows: Sequence[Number]) -> "Matrix":
        from .vector import Vector2, Vector3, Vector4

        if len(rows) == 0:
            return cls(rows=0, cols=0)

        processed_rows = []
        for row in rows:
            if isinstance(row, Vector2):
                processed_rows.append([row.x, row.y])
            elif isinstance(row, Vector3):
                processed_rows.append([row.x, row.y, row.z])
            elif isinstance(row, Vector4):
                processed_rows.append([row.x, row.y, row.z, row.w])
            else:
                processed_rows.append(list(row))

        return cls(processed_rows)

    @classmethod
    def from_cols(cls, *cols: Sequence[Number]) -> "Matrix":
        from .vector import Vector2, Vector3, Vector4

        if len(cols) == 0:
            return cls(rows=0, cols=0)

        # Determine the dimension of each column
        dimensions = []
        for col in cols:
            if isinstance(col, Vector2):
                dimensions.append(2)
            elif isinstance(col, Vector3):
                dimensions.append(3)
            elif isinstance(col, Vector4):
                dimensions.append(4)
            else:
                dimensions.append(len(col))

        if len(set(dimensions)) > 1:
            raise ValueError("All columns must have the same length")

        rows = dimensions[0]
        cols_count = len(cols)
        result = cls(rows=rows, cols=cols_count)

        for j, col in enumerate(cols):
            if isinstance(col, Vector2):
                result[0, j] = col.x
                result[1, j] = col.y
            elif isinstance(col, Vector3):
                result[0, j] = col.x
                result[1, j] = col.y
                result[2, j] = col.z
            elif isinstance(col, Vector4):
                result[0, j] = col.x
                result[1, j] = col.y
                result[2, j] = col.z
                result[3, j] = col.w
            else:
                for i, val in enumerate(col):
                    result[i, j] = val

        return result

    def apply(self, func: Callable[[float], float]) -> "Matrix":
        """Apply a function to each element of the matrix"""
        result = Matrix(rows=self.rows, cols=self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                result[i, j] = func(self[i, j])
        return result

    def row_echelon_form(self) -> "Matrix":
        """Transform the matrix to row echelon form using Gaussian elimination"""
        result = Matrix(data=self.data)  # Create a copy
        lead = 0

        for r in range(result.rows):
            if lead >= result.cols:
                break

            i = r
            while i < result.rows and result[i, lead] == 0:
                i += 1

            if i == result.rows:
                lead += 1
                continue

            # Swap rows i and r
            if i != r:
                result.data[i], result.data[r] = result.data[r], result.data[i]

            # Scale row r
            pivot = result[r, lead]
            if pivot != 0:
                for j in range(result.cols):
                    result[r, j] /= pivot

            # Eliminate other rows
            for i in range(result.rows):
                if i != r:
                    factor = result[i, lead]
                    for j in range(result.cols):
                        result[i, j] -= factor * result[r, j]

            lead += 1

        return result

    def reduced_row_echelon_form(self) -> "Matrix":
        """Transform the matrix to reduced row echelon form"""
        result = self.row_echelon_form()

        # Work from bottom up
        for r in range(result.rows - 1, -1, -1):
            # Find pivot column
            pivot_col = -1
            for j in range(result.cols):
                if result[r, j] == 1:
                    pivot_col = j
                    break

            if pivot_col == -1:
                continue

            # Zero out entries above the pivot
            for i in range(r):
                factor = result[i, pivot_col]
                for j in range(pivot_col, result.cols):
                    result[i, j] -= factor * result[r, j]

        return result

    def rank(self) -> int:
        """Calculate the rank of the matrix"""
        rref = self.reduced_row_echelon_form()
        rank = 0

        for i in range(rref.rows):
            if any(rref[i, j] != 0 for j in range(rref.cols)):
                rank += 1

        return rank

    def lu_decomposition(self) -> Tuple["Matrix", "Matrix"]:
        """
        Decompose the matrix into L and U matrices where:
        - L is lower triangular with ones on the diagonal
        - U is upper triangular
        - A = L * U

        Only works for square matrices.
        """
        if self.rows != self.cols:
            raise ValueError("LU decomposition only defined for square matrices")

        n = self.rows
        L = Matrix.identity(n)
        U = Matrix(rows=n, cols=n)

        for i in range(n):
            # Calculate U's row i
            for j in range(i, n):
                sum_val = 0
                for k in range(i):
                    sum_val += L[i, k] * U[k, j]
                U[i, j] = self[i, j] - sum_val

            # Calculate L's column i
            for j in range(i + 1, n):
                sum_val = 0
                for k in range(i):
                    sum_val += L[j, k] * U[k, i]
                if abs(U[i, i]) < 1e-10:
                    raise ValueError(
                        "Matrix is singular, LU decomposition not possible"
                    )
                L[j, i] = (self[j, i] - sum_val) / U[i, i]

        return L, U

    def eigenvectors(
        self, max_iterations: int = 100, tolerance: float = 1e-10
    ) -> Tuple[List[float], List["Matrix"]]:
        """
        Compute eigenvalues and eigenvectors using the power method.
        Returns (eigenvalues, eigenvectors)

        This is a simplified implementation that works well for small matrices.
        For larger or more complex matrices, use numpy's np.linalg.eig()

        Note: This method may not find all eigenvalues/eigenvectors.
        """
        if self.rows != self.cols:
            raise ValueError("Eigendecomposition only defined for square matrices")

        # For small matrices, use numpy directly
        if self.rows <= 4:
            eigenvalues, eigenvectors = np.linalg.eig(self.to_numpy())
            return (
                eigenvalues.tolist(),
                [Matrix([[v] for v in eigenvector]) for eigenvector in eigenvectors.T],
            )

        # Power iteration method for larger matrices (simplified)
        n = self.rows
        eigenvalues = []
        eigenvectors = []

        # This is a simplified approach that may not find all eigenvalues
        remaining_matrix = Matrix(self.data)

        for _ in range(min(n, 3)):  # Find up to min(n, 3) eigenvalues/vectors
            # Start with a random vector
            vector = Matrix([[np.random.random()] for _ in range(n)])

            # Normalize
            norm = np.sqrt(sum(v[0] ** 2 for v in vector.data))
            for i in range(n):
                vector[i, 0] /= norm

            # Power iteration
            for _ in range(max_iterations):
                new_vector = remaining_matrix * vector

                # Calculate eigenvalue estimate (Rayleigh quotient)
                eigenvalue = sum(
                    (remaining_matrix * vector)[i, 0] * vector[i, 0] for i in range(n)
                )

                # Normalize
                norm = np.sqrt(sum(v[0] ** 2 for v in new_vector.data))
                for i in range(n):
                    new_vector[i, 0] /= norm

                # Check convergence
                diff = sum((new_vector[i, 0] - vector[i, 0]) ** 2 for i in range(n))
                vector = new_vector

                if diff < tolerance:
                    break

            eigenvalues.append(eigenvalue)
            eigenvectors.append(vector)

            # Deflate the matrix (subtract the contribution of this eigenvalue/vector)
            outer_product = Matrix(rows=n, cols=n)
            for i in range(n):
                for j in range(n):
                    outer_product[i, j] = vector[i, 0] * vector[j, 0]

            remaining_matrix = remaining_matrix - eigenvalue * outer_product

        return eigenvalues, eigenvectors


def mat2(*args: Number) -> Matrix:
    """
    Create a 2x2 matrix from various inputs:
    - mat2() -> 2x2 identity matrix
    - mat2(scalar) -> 2x2 matrix with scalar on diagonal
    - mat2(a, b, c, d) -> [[a, b], [c, d]]
    - mat2([a, b, c, d]) -> [[a, b], [c, d]]
    - mat2([[a, b], [c, d]]) -> 2x2 matrix from nested list
    """
    if len(args) == 0:
        return Matrix.identity(2)
    elif len(args) == 1:
        arg = args[0]
        if isinstance(arg, (int, float)):
            return Matrix([[arg, 0], [0, arg]])
        elif isinstance(arg, (list, tuple)):
            if len(arg) == 4:
                return Matrix([[arg[0], arg[1]], [arg[2], arg[3]]])
            elif len(arg) == 2 and isinstance(arg[0], (list, tuple)):
                return Matrix(arg)
            else:
                raise ValueError("Invalid input for 2x2 matrix")
        else:
            raise ValueError("Invalid input type for 2x2 matrix")
    elif len(args) == 4:
        return Matrix([[args[0], args[1]], [args[2], args[3]]])
    else:
        raise ValueError("Invalid number of arguments for 2x2 matrix")


def mat3(*args: Number) -> Matrix:
    """
    Create a 3x3 matrix from various inputs:
    - mat3() -> 3x3 identity matrix
    - mat3(scalar) -> 3x3 matrix with scalar on diagonal
    - mat3(a, b, c, d, e, f, g, h, i) -> [[a, b, c], [d, e, f], [g, h, i]]
    - mat3([a, b, c, d, e, f, g, h, i]) -> 3x3 matrix from flat list
    - mat3([[a, b, c], [d, e, f], [g, h, i]]) -> 3x3 matrix from nested list
    """
    if len(args) == 0:
        return Matrix.identity(3)
    elif len(args) == 1:
        arg = args[0]
        if isinstance(arg, (int, float)):
            return Matrix([[arg, 0, 0], [0, arg, 0], [0, 0, arg]])
        elif isinstance(arg, (list, tuple)):
            if len(arg) == 9:
                return Matrix(
                    [
                        [arg[0], arg[1], arg[2]],
                        [arg[3], arg[4], arg[5]],
                        [arg[6], arg[7], arg[8]],
                    ]
                )
            elif len(arg) == 3 and isinstance(arg[0], (list, tuple)):
                return Matrix(arg)
            else:
                raise ValueError("Invalid input for 3x3 matrix")
        else:
            raise ValueError("Invalid input type for 3x3 matrix")
    elif len(args) == 9:
        return Matrix(
            [
                [args[0], args[1], args[2]],
                [args[3], args[4], args[5]],
                [args[6], args[7], args[8]],
            ]
        )
    else:
        raise ValueError("Invalid number of arguments for 3x3 matrix")


def mat4(*args: Number) -> Matrix:
    """
    Create a 4x4 matrix from various inputs:
    - mat4() -> 4x4 identity matrix
    - mat4(scalar) -> 4x4 matrix with scalar on diagonal
    - mat4(a, b, ..., p) -> 4x4 matrix from 16 values (row-major)
    - mat4([a, b, ..., p]) -> 4x4 matrix from flat list of 16 values
    - mat4([[a, b, c, d], [e, f, g, h], [i, j, k, l], [m, n, o, p]]) -> 4x4 matrix from nested list
    """
    if len(args) == 0:
        return Matrix.identity(4)
    elif len(args) == 1:
        arg = args[0]
        if isinstance(arg, (int, float)):
            return Matrix(
                [[arg, 0, 0, 0], [0, arg, 0, 0], [0, 0, arg, 0], [0, 0, 0, arg]]
            )
        elif isinstance(arg, (list, tuple)):
            if len(arg) == 16:
                return Matrix(
                    [
                        [arg[0], arg[1], arg[2], arg[3]],
                        [arg[4], arg[5], arg[6], arg[7]],
                        [arg[8], arg[9], arg[10], arg[11]],
                        [arg[12], arg[13], arg[14], arg[15]],
                    ]
                )
            elif len(arg) == 4 and isinstance(arg[0], (list, tuple)):
                return Matrix(arg)
            else:
                raise ValueError("Invalid input for 4x4 matrix")
        else:
            raise ValueError("Invalid input type for 4x4 matrix")
    elif len(args) == 16:
        return Matrix(
            [
                [args[0], args[1], args[2], args[3]],
                [args[4], args[5], args[6], args[7]],
                [args[8], args[9], args[10], args[11]],
                [args[12], args[13], args[14], args[15]],
            ]
        )
    else:
        raise ValueError("Invalid number of arguments for 4x4 matrix")


# 2D Transformation utility functions
def rotation_matrix_2d(angle_radians: float) -> Matrix:
    """Create a 2D rotation matrix"""
    cos_a = np.cos(angle_radians)
    sin_a = np.sin(angle_radians)
    return Matrix([[cos_a, -sin_a], [sin_a, cos_a]])


def scaling_matrix_2d(sx: float, sy: Optional[float] = None) -> Matrix:
    """Create a 2D scaling matrix"""
    if sy is None:
        sy = sx
    return Matrix([[sx, 0], [0, sy]])


def translation_vector_2d(tx: float, ty: float) -> "Vector2":
    """Create a 2D translation vector"""
    from .vector import Vector2

    return Vector2(tx, ty)


def transform_point_2d(
    point: Union[List[Number], "Vector2"],
    matrix: Matrix,
    translation: Optional["Vector2"] = None,
) -> Union[List[Number], "Vector2"]:
    """Transform a 2D point using a matrix and optional translation"""
    from .vector import Vector2

    if isinstance(point, list):
        if len(point) != 2:
            raise ValueError("Point must have 2 components")
        point_vec = Vector2(point[0], point[1])
        result = matrix * point_vec
        if translation:
            result += translation
        return [result.x, result.y]
    else:
        result = matrix * point
        if translation:
            result += translation
        return result


def shear_matrix_2d(shx: float = 0.0, shy: float = 0.0) -> Matrix:
    """Create a 2D shear matrix"""
    return Matrix([[1, shx], [shy, 1]])


def reflection_matrix_2d(axis: str = "x") -> Matrix:
    """
    Create a 2D reflection matrix.

    Parameters:
    - axis: 'x' for reflection across x-axis, 'y' for reflection across y-axis,
            'origin' for reflection through origin, or angle in radians for reflection across a line
    """
    if axis == "x":
        return Matrix([[1, 0], [0, -1]])
    elif axis == "y":
        return Matrix([[-1, 0], [0, 1]])
    elif axis == "origin":
        return Matrix([[-1, 0], [0, -1]])
    else:
        # Reflection across a line at the specified angle
        try:
            angle = float(axis)
            double_angle = 2 * angle
            cos_2a = np.cos(double_angle)
            sin_2a = np.sin(double_angle)
            return Matrix([[cos_2a, sin_2a], [sin_2a, -cos_2a]])
        except ValueError:
            raise ValueError(
                "Invalid axis value. Use 'x', 'y', 'origin', or an angle in radians."
            )


# 3D Transformation utility functions
def rotation_matrix_3d_x(angle_radians: float) -> Matrix:
    """Create a 3D rotation matrix around the x-axis"""
    cos_a = np.cos(angle_radians)
    sin_a = np.sin(angle_radians)
    return Matrix([[1, 0, 0], [0, cos_a, -sin_a], [0, sin_a, cos_a]])


def rotation_matrix_3d_y(angle_radians: float) -> Matrix:
    """Create a 3D rotation matrix around the y-axis"""
    cos_a = np.cos(angle_radians)
    sin_a = np.sin(angle_radians)
    return Matrix([[cos_a, 0, sin_a], [0, 1, 0], [-sin_a, 0, cos_a]])


def rotation_matrix_3d_z(angle_radians: float) -> Matrix:
    """Create a 3D rotation matrix around the z-axis"""
    cos_a = np.cos(angle_radians)
    sin_a = np.sin(angle_radians)
    return Matrix([[cos_a, -sin_a, 0], [sin_a, cos_a, 0], [0, 0, 1]])


def rotation_matrix_3d(axis: str, angle_radians: float) -> Matrix:
    """Create a 3D rotation matrix around specified axis ('x', 'y', or 'z')"""
    if axis == "x":
        return rotation_matrix_3d_x(angle_radians)
    elif axis == "y":
        return rotation_matrix_3d_y(angle_radians)
    elif axis == "z":
        return rotation_matrix_3d_z(angle_radians)
    else:
        raise ValueError("Axis must be 'x', 'y', or 'z'")


def rotation_matrix_3d_arbitrary(
    axis: Union[List[Number], "Vector3"], angle_radians: float
) -> Matrix:
    """Create a 3D rotation matrix around an arbitrary axis"""
    from .vector import Vector3

    if isinstance(axis, list):
        if len(axis) != 3:
            raise ValueError("Axis must have 3 components")
        axis = Vector3(axis[0], axis[1], axis[2])
    elif not isinstance(axis, Vector3):
        raise ValueError("Axis must be a Vector3 or list of 3 numbers")

    axis = axis.normalized
    x, y, z = axis.x, axis.y, axis.z
    c = np.cos(angle_radians)
    s = np.sin(angle_radians)
    t = 1 - c

    return Matrix(
        [
            [t * x * x + c, t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c],
        ]
    )


def scaling_matrix_3d(
    sx: float, sy: Optional[float] = None, sz: Optional[float] = None
) -> Matrix:
    """Create a 3D scaling matrix"""
    if sy is None:
        sy = sx
    if sz is None:
        sz = sx
    return Matrix([[sx, 0, 0], [0, sy, 0], [0, 0, sz]])


def translation_vector_3d(tx: float, ty: float, tz: float) -> "Vector3":
    """Create a 3D translation vector"""
    from .vector import Vector3

    return Vector3(tx, ty, tz)


def transform_point_3d(
    point: Union[List[Number], "Vector3"],
    matrix: Matrix,
    translation: Optional["Vector3"] = None,
) -> Union[List[Number], "Vector3"]:
    """Transform a 3D point using a matrix and optional translation"""
    from .vector import Vector3

    if isinstance(point, list):
        if len(point) != 3:
            raise ValueError("Point must have 3 components")
        point_vec = Vector3(point[0], point[1], point[2])
        result = matrix * point_vec
        if translation:
            result += translation
        return [result.x, result.y, result.z]
    else:
        result = matrix * point
        if translation:
            result += translation
        return result


def shear_matrix_3d(
    xy: float = 0.0,
    xz: float = 0.0,
    yx: float = 0.0,
    yz: float = 0.0,
    zx: float = 0.0,
    zy: float = 0.0,
) -> Matrix:
    """Create a 3D shear matrix"""
    return Matrix([[1, xy, xz], [yx, 1, yz], [zx, zy, 1]])


def reflection_matrix_3d(plane: str = "xy") -> Matrix:
    """
    Create a 3D reflection matrix.

    Parameters:
    - plane: 'xy', 'xz', 'yz' for reflection across the respective plane,
             'origin' for reflection through origin
    """
    if plane == "xy":
        return Matrix([[1, 0, 0], [0, 1, 0], [0, 0, -1]])
    elif plane == "xz":
        return Matrix([[1, 0, 0], [0, -1, 0], [0, 0, 1]])
    elif plane == "yz":
        return Matrix([[-1, 0, 0], [0, 1, 0], [0, 0, 1]])
    elif plane == "origin":
        return Matrix([[-1, 0, 0], [0, -1, 0], [0, 0, -1]])
    else:
        raise ValueError("Invalid plane value. Use 'xy', 'xz', 'yz', or 'origin'.")


# 4D transformations and utility functions
def translation_matrix_4d(tx: float, ty: float, tz: float) -> Matrix:
    """Create a 4D homogeneous transformation matrix for 3D translation"""
    return Matrix([[1, 0, 0, tx], [0, 1, 0, ty], [0, 0, 1, tz], [0, 0, 0, 1]])


def scaling_matrix_4d(
    sx: float, sy: Optional[float] = None, sz: Optional[float] = None
) -> Matrix:
    """Create a 4D homogeneous transformation matrix for 3D scaling"""
    if sy is None:
        sy = sx
    if sz is None:
        sz = sx
    return Matrix([[sx, 0, 0, 0], [0, sy, 0, 0], [0, 0, sz, 0], [0, 0, 0, 1]])


def rotation_matrix_4d_x(angle_radians: float) -> Matrix:
    """Create a 4D homogeneous transformation matrix for 3D rotation around x-axis"""
    cos_a = np.cos(angle_radians)
    sin_a = np.sin(angle_radians)
    return Matrix(
        [[1, 0, 0, 0], [0, cos_a, -sin_a, 0], [0, sin_a, cos_a, 0], [0, 0, 0, 1]]
    )


def rotation_matrix_4d_y(angle_radians: float) -> Matrix:
    """Create a 4D homogeneous transformation matrix for 3D rotation around y-axis"""
    cos_a = np.cos(angle_radians)
    sin_a = np.sin(angle_radians)
    return Matrix(
        [[cos_a, 0, sin_a, 0], [0, 1, 0, 0], [-sin_a, 0, cos_a, 0], [0, 0, 0, 1]]
    )


def rotation_matrix_4d_z(angle_radians: float) -> Matrix:
    """Create a 4D homogeneous transformation matrix for 3D rotation around z-axis"""
    cos_a = np.cos(angle_radians)
    sin_a = np.sin(angle_radians)
    return Matrix(
        [[cos_a, -sin_a, 0, 0], [sin_a, cos_a, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    )


def transform_point_homogeneous(
    point: Union[List[Number], "Vector4"], transform_matrix: Matrix
) -> Union[List[Number], "Vector4"]:
    """
    Transform a 3D point using a 4x4 homogeneous transformation matrix

    Args:
        point: Vector4 point to transform or list of 4 numbers (homogeneous coords)
        transform_matrix: 4x4 homogeneous transformation matrix

    Returns:
        Transformed Vector4 point or list of 4 numbers
    """
    from .vector import Vector3, Vector4

    if isinstance(point, list):
        if len(point) == 3:
            # Convert 3D point to homogeneous
            homogeneous_point = Vector4(point[0], point[1], point[2], 1.0)
        elif len(point) == 4:
            homogeneous_point = Vector4(point[0], point[1], point[2], point[3])
        else:
            raise ValueError("Point must have 3 or 4 components")

        # Apply transformation
        result = transform_matrix * homogeneous_point

        # Convert back to 3D (divide by w) or return 4D
        w = result.w
        if abs(w) < 1e-10:
            raise ValueError("Homogeneous coordinate w is too close to zero")

        if len(point) == 3:
            return [result.x / w, result.y / w, result.z / w]
        else:
            return [result.x, result.y, result.z, result.w]
    else:
        # Apply transformation
        result = transform_matrix * point
        return result


def perspective_projection_matrix(
    fov: float, aspect: float, near: float, far: float
) -> Matrix:
    """
    Create a perspective projection matrix

    Args:
        fov: Field of view in radians
        aspect: Aspect ratio (width/height)
        near: Near clipping plane distance
        far: Far clipping plane distance

    Returns:
        4x4 perspective projection matrix
    """
    tan_half_fov = np.tan(fov / 2)
    f = 1.0 / tan_half_fov

    return Matrix(
        [
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), (2 * far * near) / (near - far)],
            [0, 0, -1, 0],
        ]
    )


def orthographic_projection_matrix(
    left: float, right: float, bottom: float, top: float, near: float, far: float
) -> Matrix:
    """
    Create an orthographic projection matrix

    Args:
        left, right: Left and right clipping planes
        bottom, top: Bottom and top clipping planes
        near, far: Near and far clipping planes

    Returns:
        4x4 orthographic projection matrix
    """
    return Matrix(
        [
            [2 / (right - left), 0, 0, -(right + left) / (right - left)],
            [0, 2 / (top - bottom), 0, -(top + bottom) / (top - bottom)],
            [0, 0, 2 / (near - far), -(near + far) / (near - far)],
            [0, 0, 0, 1],
        ]
    )


def look_at_matrix(
    eye: Union[List[Number], "Vector3"],
    target: Union[List[Number], "Vector3"],
    up: Union[List[Number], "Vector3"],
) -> Matrix:
    """
    Create a view matrix that looks from 'eye' position toward 'target' position

    Args:
        eye: Camera position
        target: Point to look at
        up: Up direction

    Returns:
        4x4 view matrix
    """
    from .vector import Vector3

    # Convert lists to Vector3 if needed
    if isinstance(eye, list):
        if len(eye) != 3:
            raise ValueError("Eye position must have 3 components")
        eye = Vector3(eye[0], eye[1], eye[2])

    if isinstance(target, list):
        if len(target) != 3:
            raise ValueError("Target position must have 3 components")
        target = Vector3(target[0], target[1], target[2])

    if isinstance(up, list):
        if len(up) != 3:
            raise ValueError("Up vector must have 3 components")
        up = Vector3(up[0], up[1], up[2])

    # Forward direction
    forward = (target - eye).normalized

    # Right direction
    right = forward.cross(up).normalized

    # Corrected up direction
    new_up = right.cross(forward)

    # Create the rotation part of the view matrix
    rotation = Matrix(
        [
            [right.x, right.y, right.z, 0],
            [new_up.x, new_up.y, new_up.z, 0],
            [-forward.x, -forward.y, -forward.z, 0],
            [0, 0, 0, 1],
        ]
    )

    # Create the translation part
    translation = translation_matrix_4d(-eye.x, -eye.y, -eye.z)

    # Combine rotation and translation
    return rotation * translation


# Additional utility functions
def interpolate_matrices(matrix_a: Matrix, matrix_b: Matrix, t: float) -> Matrix:
    """
    Linearly interpolate between two matrices

    Args:
        matrix_a: First matrix
        matrix_b: Second matrix
        t: Interpolation factor (0 to 1)

    Returns:
        Interpolated matrix
    """
    if matrix_a.rows != matrix_b.rows or matrix_a.cols != matrix_b.cols:
        raise ValueError("Matrices must have the same dimensions for interpolation")

    result = Matrix(rows=matrix_a.rows, cols=matrix_a.cols)
    for i in range(matrix_a.rows):
        for j in range(matrix_a.cols):
            result[i, j] = matrix_a[i, j] * (1 - t) + matrix_b[i, j] * t

    return result


# Pre-defined matrices for common transformations
IDENTITY_2D = Matrix.identity(2)
IDENTITY_3D = Matrix.identity(3)
IDENTITY_4D = Matrix.identity(4)
