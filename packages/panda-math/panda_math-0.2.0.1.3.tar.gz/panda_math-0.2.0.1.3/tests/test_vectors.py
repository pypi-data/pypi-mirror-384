import unittest
import numpy as np
from panda_math import Vector2, Vector3, Vector4
from panda_math import Matrix


class TestVector2(unittest.TestCase):
    def setUp(self):
        self.v1 = Vector2(1, 2)
        self.v2 = Vector2(3, 4)
        self.v_zero = Vector2(0, 0)
        
    def test_initialization(self):
        # Test different initialization methods
        v1 = Vector2(1, 2)
        self.assertEqual(v1.x, 1)
        self.assertEqual(v1.y, 2)
        
        v2 = Vector2([3, 4])
        self.assertEqual(v2.x, 3)
        self.assertEqual(v2.y, 4)
        
        v3 = Vector2(5)  # Single value
        self.assertEqual(v3.x, 5)
        self.assertEqual(v3.y, 5)
        
        v4 = Vector2()  # Default
        self.assertEqual(v4.x, 0)
        self.assertEqual(v4.y, 0)
        
    def test_indexing(self):
        v = Vector2(1, 2)
        self.assertEqual(v[0], 1)
        self.assertEqual(v[1], 2)
        
        v[0] = 10
        v[1] = 20
        self.assertEqual(v.x, 10)
        self.assertEqual(v.y, 20)
        
        with self.assertRaises(IndexError):
            _ = v[2]
            
    def test_iteration(self):
        v = Vector2(1, 2)
        values = list(v)
        self.assertEqual(values, [1, 2])
        self.assertEqual(len(v), 2)
        
    def test_arithmetic_operations(self):
        # Addition
        result = self.v1 + self.v2
        self.assertEqual(result.x, 4)
        self.assertEqual(result.y, 6)
        
        # Scalar addition
        result = self.v1 + 5
        self.assertEqual(result.x, 6)
        self.assertEqual(result.y, 7)
        
        # Subtraction
        result = self.v2 - self.v1
        self.assertEqual(result.x, 2)
        self.assertEqual(result.y, 2)
        
        # Multiplication
        result = self.v1 * 3
        self.assertEqual(result.x, 3)
        self.assertEqual(result.y, 6)
        
        # Element-wise multiplication
        result = self.v1 * self.v2
        self.assertEqual(result.x, 3)
        self.assertEqual(result.y, 8)
        
        # Division
        result = self.v2 / 2
        self.assertEqual(result.x, 1.5)
        self.assertEqual(result.y, 2.0)
        
    def test_in_place_operations(self):
        v = Vector2(1, 2)
        v += Vector2(3, 4)
        self.assertEqual(v.x, 4)
        self.assertEqual(v.y, 6)
        
        v *= 2
        self.assertEqual(v.x, 8)
        self.assertEqual(v.y, 12)
        
    def test_comparison_operations(self):
        v1 = Vector2(1, 2)
        v2 = Vector2(1, 2)
        v3 = Vector2(3, 4)
        
        self.assertTrue(v1 == v2)
        self.assertFalse(v1 == v3)
        
        self.assertTrue(v1 < v3)
        self.assertTrue(v3 > v1)
        
    def test_magnitude_and_normalization(self):
        v = Vector2(3, 4)
        self.assertEqual(v.magnitude, 5.0)
        
        normalized = v.normalized
        self.assertAlmostEqual(normalized.magnitude, 1.0, places=10)
        self.assertAlmostEqual(normalized.x, 0.6, places=10)
        self.assertAlmostEqual(normalized.y, 0.8, places=10)
        
    def test_distance_and_dot_product(self):
        v1 = Vector2(0, 0)
        v2 = Vector2(3, 4)
        
        self.assertEqual(v1.distance_to(v2), 5.0)
        self.assertEqual(v1.dot(v2), 0)
        self.assertEqual(v2.dot(v2), 25)  # 3*3 + 4*4
    
    """
    def test_swizzling(self):
        v = Vector2(1, 2)
        
        # 2D swizzling
        xy = v.xy
        self.assertEqual(xy.x, 1)
        self.assertEqual(xy.y, 2)
        
        yx = v.yx
        self.assertEqual(yx.x, 2)
        self.assertEqual(yx.y, 1)
        
        # 3D swizzling
        xyz = v.xyx
        self.assertEqual(xyz.x, 1)
        self.assertEqual(xyz.y, 2)
        self.assertEqual(xyz.z, 1)
    """
        
    def test_matrix_multiplication(self):
        v = Vector2(1, 2)
        m = Matrix([[2, 0], [0, 3]])  # 2x2 scaling matrix
        
        result = v * m
        self.assertEqual(result.x, 2)
        self.assertEqual(result.y, 6)
        
    def test_conversions(self):
        v = Vector2(1, 2)
        
        # To list/tuple
        self.assertEqual(v.to_list(), [1, 2])
        self.assertEqual(v.to_tuple(), (1, 2))
        
        # To numpy
        np_array = v.to_numpy()
        np.testing.assert_array_equal(np_array, [1, 2])
        
        # From numpy
        v_from_np = Vector2.from_numpy(np.array([3, 4]))
        self.assertEqual(v_from_np.x, 3)
        self.assertEqual(v_from_np.y, 4)


class TestVector3(unittest.TestCase):
    def setUp(self):
        self.v1 = Vector3(1, 2, 3)
        self.v2 = Vector3(4, 5, 6)
        
    def test_initialization(self):
        v = Vector3(1, 2, 3)
        self.assertEqual(v.x, 1)
        self.assertEqual(v.y, 2)
        self.assertEqual(v.z, 3)
        
    def test_cross_product(self):
        # Standard basis vectors
        i = Vector3(1, 0, 0)
        j = Vector3(0, 1, 0)
        k = Vector3(0, 0, 1)
        
        # i × j = k
        result = i.cross(j)
        self.assertEqual(result.x, 0)
        self.assertEqual(result.y, 0)
        self.assertEqual(result.z, 1)
        
        # j × k = i
        result = j.cross(k)
        self.assertEqual(result.x, 1)
        self.assertEqual(result.y, 0)
        self.assertEqual(result.z, 0)
        
    def test_arithmetic_operations(self):
        result = self.v1 + self.v2
        self.assertEqual(result.x, 5)
        self.assertEqual(result.y, 7)
        self.assertEqual(result.z, 9)
        
        result = self.v1 * 2
        self.assertEqual(result.x, 2)
        self.assertEqual(result.y, 4)
        self.assertEqual(result.z, 6)
        
    def test_magnitude(self):
        v = Vector3(2, 3, 6)
        expected_magnitude = np.sqrt(4 + 9 + 36)
        self.assertAlmostEqual(v.magnitude, expected_magnitude, places=10)
    
    """
    def test_swizzling(self):
        v = Vector3(1, 2, 3)
        
        # 2D swizzling
        xy = v.xy
        self.assertEqual(xy.x, 1)
        self.assertEqual(xy.y, 2)
        
        # 3D swizzling
        zyx = v.zyx
        self.assertEqual(zyx.x, 3)
        self.assertEqual(zyx.y, 2)
        self.assertEqual(zyx.z, 1)
    """

class TestVector4(unittest.TestCase):
    def setUp(self):
        self.v1 = Vector4(1, 2, 3, 4)
        self.v2 = Vector4(5, 6, 7, 8)
        
    def test_initialization(self):
        v = Vector4(1, 2, 3, 4)
        self.assertEqual(v.x, 1)
        self.assertEqual(v.y, 2)
        self.assertEqual(v.z, 3)
        self.assertEqual(v.w, 4)
        
    def test_arithmetic_operations(self):
        result = self.v1 + self.v2
        self.assertEqual(result.x, 6)
        self.assertEqual(result.y, 8)
        self.assertEqual(result.z, 10)
        self.assertEqual(result.w, 12)
        
    def test_indexing(self):
        v = Vector4(1, 2, 3, 4)
        self.assertEqual(v[0], 1)
        self.assertEqual(v[1], 2)
        self.assertEqual(v[2], 3)
        self.assertEqual(v[3], 4)
        
        with self.assertRaises(IndexError):
            _ = v[4]


class TestVectorConversions(unittest.TestCase):
    def test_vec2_to_vec3(self):
        v2 = Vector2(1, 2)
        v3 = Vector3(v2, 5)
        self.assertEqual(v3.x, 1)
        self.assertEqual(v3.y, 2)
        self.assertEqual(v3.z, 5)
        
    def test_vec3_to_vec2(self):
        v3 = Vector3(1, 2, 3)
        v2 = Vector2(v3)
        self.assertEqual(v2.x, 1)
        self.assertEqual(v2.y, 2)
        
    def test_vec4_to_vec3(self):
        v4 = Vector4(1, 2, 3, 4)
        v3 = Vector3(v4)
        self.assertEqual(v3.x, 1)
        self.assertEqual(v3.y, 2)
        self.assertEqual(v3.z, 3)


class TestVectorEdgeCases(unittest.TestCase):
    def test_zero_vector_normalization(self):
        zero_vec = Vector2(0, 0)
        normalized = zero_vec.normalized
        self.assertEqual(normalized.x, 0)
        self.assertEqual(normalized.y, 0)
        
    def test_division_by_zero(self):
        v = Vector2(1, 2)
        with self.assertRaises(ZeroDivisionError):
            _ = v / 0
            
    def test_invalid_swizzling(self):
        v = Vector2(1, 2)
        with self.assertRaises(AttributeError):
            _ = v.invalid_attr


if __name__ == '__main__':
    unittest.main(verbosity=2)