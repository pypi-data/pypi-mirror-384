import unittest
import numpy as np
import math
from panda_math.matrix import (
    Matrix,
    mat2,
    mat3,
    mat4,
    rotation_matrix_2d,
    scaling_matrix_2d,
    translation_vector_2d,
    rotation_matrix_3d_x,
    rotation_matrix_3d_y,
    rotation_matrix_3d_z,
    rotation_matrix_3d,
    rotation_matrix_3d_arbitrary,
    scaling_matrix_3d,
    translation_vector_3d,
    translation_matrix_4d,
    scaling_matrix_4d,
    rotation_matrix_4d_x,
    rotation_matrix_4d_y,
    rotation_matrix_4d_z,
    perspective_projection_matrix,
    orthographic_projection_matrix,
    look_at_matrix,
    interpolate_matrices,
)
from panda_math.vector import Vector2, Vector3, Vector4


class TestMatrixBasics(unittest.TestCase):
    def test_matrix_creation(self):
        # From nested list
        m1 = Matrix([[1, 2], [3, 4]])
        self.assertEqual(m1[0, 0], 1)
        self.assertEqual(m1[0, 1], 2)
        self.assertEqual(m1[1, 0], 3)
        self.assertEqual(m1[1, 1], 4)

        # From dimensions
        m2 = Matrix(rows=3, cols=2)
        self.assertEqual(m2.rows, 3)
        self.assertEqual(m2.cols, 2)

        # From numpy array
        np_array = np.array([[1, 2, 3], [4, 5, 6]])
        m3 = Matrix(np_array)
        self.assertEqual(m3[0, 2], 3)
        self.assertEqual(m3[1, 1], 5)

    def test_matrix_indexing(self):
        m = Matrix([[1, 2, 3], [4, 5, 6]])

        # Single element access
        self.assertEqual(m[0, 1], 2)
        self.assertEqual(m[1, 2], 6)

        # Row access
        row = m[1]
        self.assertEqual(row, [4, 5, 6])

        # Setting values
        m[0, 0] = 10
        self.assertEqual(m[0, 0], 10)

        # Setting row
        m[1] = [7, 8, 9]
        self.assertEqual(m[1, 1], 8)

    def test_matrix_properties(self):
        m = Matrix([[1, 2, 3], [4, 5, 6]])
        self.assertEqual(len(m), 2)  # number of rows
        self.assertEqual(m.rows, 2)
        self.assertEqual(m.cols, 3)

        # Iteration
        rows = list(m)
        self.assertEqual(rows, [[1, 2, 3], [4, 5, 6]])


class TestMatrixArithmetic(unittest.TestCase):
    def setUp(self):
        self.m1 = Matrix([[1, 2], [3, 4]])
        self.m2 = Matrix([[5, 6], [7, 8]])

    def test_addition(self):
        result = self.m1 + self.m2
        self.assertEqual(result[0, 0], 6)
        self.assertEqual(result[0, 1], 8)
        self.assertEqual(result[1, 0], 10)
        self.assertEqual(result[1, 1], 12)

        # Scalar addition
        result = self.m1 + 5
        self.assertEqual(result[0, 0], 6)
        self.assertEqual(result[1, 1], 9)

    def test_subtraction(self):
        result = self.m2 - self.m1
        self.assertEqual(result[0, 0], 4)
        self.assertEqual(result[1, 1], 4)

        # Scalar subtraction
        result = self.m1 - 1
        self.assertEqual(result[0, 0], 0)
        self.assertEqual(result[1, 1], 3)

    def test_multiplication(self):
        # Matrix multiplication
        result = self.m1 * self.m2
        # [[1*5+2*7, 1*6+2*8], [3*5+4*7, 3*6+4*8]]
        # [[19, 22], [43, 50]]
        self.assertEqual(result[0, 0], 19)
        self.assertEqual(result[0, 1], 22)
        self.assertEqual(result[1, 0], 43)
        self.assertEqual(result[1, 1], 50)

        # Scalar multiplication
        result = self.m1 * 2
        self.assertEqual(result[0, 0], 2)
        self.assertEqual(result[1, 1], 8)

    def test_matrix_vector_multiplication(self):
        m = Matrix([[2, 0], [0, 3]])
        v = Vector2(1, 2)

        result = v * m
        self.assertEqual(result.x, 2)
        self.assertEqual(result.y, 6)

        # 3D case
        m3 = Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 2]])
        v3 = Vector3(1, 2, 3)

        result = v3 * m3
        self.assertEqual(result.x, 1)
        self.assertEqual(result.y, 2)
        self.assertEqual(result.z, 6)

    def test_division(self):
        result = self.m1 / 2
        self.assertEqual(result[0, 0], 0.5)
        self.assertEqual(result[1, 1], 2.0)


class TestMatrixOperations(unittest.TestCase):
    def test_transpose(self):
        m = Matrix([[1, 2, 3], [4, 5, 6]])
        t = m.transpose()

        self.assertEqual(t.rows, 3)
        self.assertEqual(t.cols, 2)
        self.assertEqual(t[0, 0], 1)
        self.assertEqual(t[0, 1], 4)
        self.assertEqual(t[2, 1], 6)

    def test_determinant(self):
        # 2x2 determinant
        m2 = Matrix([[1, 2], [3, 4]])
        det = m2.determinant()
        self.assertEqual(det, -2)  # 1*4 - 2*3

        # 3x3 determinant
        m3 = Matrix([[1, 2, 3], [0, 1, 4], [5, 6, 0]])
        det = m3.determinant()
        self.assertEqual(det, 1)  # Known determinant

    def test_inverse(self):
        # 2x2 inverse
        m = Matrix([[1, 2], [3, 4]])
        inv = m.inverse()

        # Check that m * inv = identity
        product = m * inv
        identity = Matrix.identity(2)

        for i in range(2):
            for j in range(2):
                self.assertAlmostEqual(product[i, j], identity[i, j], places=10)

    def test_identity_matrix(self):
        identity = Matrix.identity(3)

        self.assertEqual(identity[0, 0], 1)
        self.assertEqual(identity[1, 1], 1)
        self.assertEqual(identity[2, 2], 1)
        self.assertEqual(identity[0, 1], 0)

    def test_trace(self):
        m = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        trace = m.trace()
        self.assertEqual(trace, 15)  # 1 + 5 + 9

    def test_rank(self):
        # Full rank matrix
        m1 = Matrix([[1, 0], [0, 1]])
        self.assertEqual(m1.rank(), 2)

        # Reduced rank matrix
        m2 = Matrix([[1, 2], [2, 4]])  # Second row = 2 * first row
        self.assertEqual(m2.rank(), 1)


class TestMatrixFactory(unittest.TestCase):
    def test_mat2_factory(self):
        # Identity
        m1 = mat2()
        self.assertEqual(m1[0, 0], 1)
        self.assertEqual(m1[1, 1], 1)
        self.assertEqual(m1[0, 1], 0)

        # Scalar diagonal
        m2 = mat2(5)
        self.assertEqual(m2[0, 0], 5)
        self.assertEqual(m2[1, 1], 5)

        # From values
        m3 = mat2(1, 2, 3, 4)
        self.assertEqual(m3[0, 0], 1)
        self.assertEqual(m3[0, 1], 2)
        self.assertEqual(m3[1, 0], 3)
        self.assertEqual(m3[1, 1], 4)

    def test_mat3_factory(self):
        m = mat3()
        self.assertEqual(m.rows, 3)
        self.assertEqual(m.cols, 3)

        # From 9 values
        m2 = mat3(1, 2, 3, 4, 5, 6, 7, 8, 9)
        self.assertEqual(m2[0, 2], 3)
        self.assertEqual(m2[2, 1], 8)

    def test_mat4_factory(self):
        m = mat4()
        self.assertEqual(m.rows, 4)
        self.assertEqual(m.cols, 4)


class TestTransformations2D(unittest.TestCase):
    def test_rotation_2d(self):
        # 90 degree rotation
        angle = math.pi / 2
        rot = rotation_matrix_2d(angle)

        # Test rotating (1, 0) should give (0, 1)
        v = Vector2(1, 0)
        result = v * rot
        self.assertAlmostEqual(result.x, 0, places=10)
        self.assertAlmostEqual(result.y, 1, places=10)

    def test_scaling_2d(self):
        scale = scaling_matrix_2d(2, 3)

        v = Vector2(1, 1)
        result = v * scale
        self.assertEqual(result.x, 2)
        self.assertEqual(result.y, 3)

        # Uniform scaling
        scale_uniform = scaling_matrix_2d(2)
        result = v * scale_uniform
        self.assertEqual(result.x, 2)
        self.assertEqual(result.y, 2)

    def test_translation_2d(self):
        trans = translation_vector_2d(5, 3)
        self.assertEqual(trans.x, 5)
        self.assertEqual(trans.y, 3)


class TestTransformations3D(unittest.TestCase):
    def test_rotation_3d_x(self):
        # 90 degree rotation around X-axis
        rot = rotation_matrix_3d_x(math.pi / 2)

        # (0, 1, 0) -> (0, 0, 1)
        v = Vector3(0, 1, 0)
        result = v * rot
        self.assertAlmostEqual(result.x, 0, places=10)
        self.assertAlmostEqual(result.y, 0, places=10)
        self.assertAlmostEqual(result.z, 1, places=10)

    def test_rotation_3d_y(self):
        # 90 degree rotation around Y-axis
        rot = rotation_matrix_3d_y(math.pi / 2)

        # (1, 0, 0) -> (0, 0, -1)
        v = Vector3(1, 0, 0)
        result = v * rot
        self.assertAlmostEqual(result.x, 0, places=10)
        self.assertAlmostEqual(result.y, 0, places=10)
        self.assertAlmostEqual(result.z, -1, places=10)

    def test_rotation_3d_z(self):
        # 90 degree rotation around Z-axis
        rot = rotation_matrix_3d_z(math.pi / 2)

        # (1, 0, 0) -> (0, 1, 0)
        v = Vector3(1, 0, 0)
        result = v * rot
        self.assertAlmostEqual(result.x, 0, places=10)
        self.assertAlmostEqual(result.y, 1, places=10)
        self.assertAlmostEqual(result.z, 0, places=10)

    def test_arbitrary_axis_rotation(self):
        # Rotation around Z-axis should match rotation_3d_z
        axis = Vector3(0, 0, 1)
        angle = math.pi / 4  # 45 degrees

        rot1 = rotation_matrix_3d_arbitrary(axis, angle)
        rot2 = rotation_matrix_3d_z(angle)

        # Should be approximately equal
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(rot1[i, j], rot2[i, j], places=10)


class TestTransformations4D(unittest.TestCase):
    def test_translation_matrix_4d(self):
        trans = translation_matrix_4d(1, 2, 3)

        # Test translating point (0, 0, 0, 1)
        point = Vector4(0, 0, 0, 1)
        result = point * trans

        self.assertEqual(result.x, 1)
        self.assertEqual(result.y, 2)
        self.assertEqual(result.z, 3)
        self.assertEqual(result.w, 1)

    def test_scaling_matrix_4d(self):
        scale = scaling_matrix_4d(2, 3, 4)

        point = Vector4(1, 1, 1, 1)
        result = point * point

        self.assertEqual(result.x, 2)
        self.assertEqual(result.y, 3)
        self.assertEqual(result.z, 4)
        self.assertEqual(result.w, 1)


class TestProjectionMatrices(unittest.TestCase):
    def test_perspective_projection(self):
        fov = math.pi / 4  # 45 degrees
        aspect = 16.0 / 9.0
        near = 0.1
        far = 100.0

        proj = perspective_projection_matrix(fov, aspect, near, far)
        self.assertEqual(proj.rows, 4)
        self.assertEqual(proj.cols, 4)

    def test_orthographic_projection(self):
        proj = orthographic_projection_matrix(-1, 1, -1, 1, 0.1, 100)
        self.assertEqual(proj.rows, 4)
        self.assertEqual(proj.cols, 4)

    def test_look_at_matrix(self):
        eye = Vector3(0, 0, 5)
        target = Vector3(0, 0, 0)
        up = Vector3(0, 1, 0)

        view = look_at_matrix(eye, target, up)
        self.assertEqual(view.rows, 4)
        self.assertEqual(view.cols, 4)


class TestMatrixUtilities(unittest.TestCase):
    def test_from_rows(self):
        v1 = Vector2(1, 2)
        v2 = Vector2(3, 4)

        m = Matrix.from_rows(v1, v2)
        self.assertEqual(m[0, 0], 1)
        self.assertEqual(m[0, 1], 2)
        self.assertEqual(m[1, 0], 3)
        self.assertEqual(m[1, 1], 4)

    def test_from_cols(self):
        v1 = Vector3(1, 2, 3)
        v2 = Vector3(4, 5, 6)

        m = Matrix.from_cols(v1, v2)
        self.assertEqual(m[0, 0], 1)  # v1.x
        self.assertEqual(m[1, 0], 2)  # v1.y
        self.assertEqual(m[2, 0], 3)  # v1.z
        self.assertEqual(m[0, 1], 4)  # v2.x

    def test_row_and_col_access(self):
        m = Matrix([[1, 2, 3], [4, 5, 6]])

        row = m.row(1)
        self.assertEqual(row[0], 4)
        self.assertEqual(row[1], 5)
        self.assertEqual(row[2], 6)

        col = m.col(1)
        self.assertEqual(col[0], 2)
        self.assertEqual(col[1], 5)

    def test_apply_function(self):
        m = Matrix([[1, 2], [3, 4]])
        squared = m.apply(lambda x: x**2)

        self.assertEqual(squared[0, 0], 1)
        self.assertEqual(squared[0, 1], 4)
        self.assertEqual(squared[1, 0], 9)
        self.assertEqual(squared[1, 1], 16)

    def test_interpolate_matrices(self):
        m1 = Matrix([[0, 0], [0, 0]])
        m2 = Matrix([[2, 4], [6, 8]])

        # 50% interpolation
        result = interpolate_matrices(m1, m2, 0.5)
        self.assertEqual(result[0, 0], 1)
        self.assertEqual(result[0, 1], 2)
        self.assertEqual(result[1, 0], 3)
        self.assertEqual(result[1, 1], 4)


class TestMatrixEdgeCases(unittest.TestCase):
    def test_singular_matrix(self):
        # Singular matrix (determinant = 0)
        singular = Matrix([[1, 2], [2, 4]])

        self.assertTrue(singular.is_singular())

        with self.assertRaises(ValueError):
            singular.inverse()

    def test_dimension_mismatch(self):
        m1 = Matrix([[1, 2]])  # 1x2
        m2 = Matrix([[1, 2, 3]])  # 1x3

        with self.assertRaises(ValueError):
            _ = m1 + m2  # Can't add different dimensions

        with self.assertRaises(ValueError):
            _ = m1 * m2  # Can't multiply 1x2 * 1x3

    def test_invalid_matrix_vector_multiplication(self):
        m = Matrix([[1, 2, 3]])  # 1x3 matrix
        v = Vector2(1, 2)  # 2D vector

        with self.assertRaises(ValueError):
            _ = m * v  # Can't multiply 1x3 matrix with 2D vector


if __name__ == "__main__":
    unittest.main(verbosity=2)
