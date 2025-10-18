#!/usr/bin/env python3
"""
Integration tests for vector and matrix classes working together
"""

import unittest
import math
import numpy as np
from panda_math.vector import Vector2, Vector3, Vector4
from panda_math.matrix import (
    Matrix, mat3, mat4,
    rotation_matrix_2d, scaling_matrix_2d, scaling_matrix_3d,
    rotation_matrix_3d_x, rotation_matrix_3d_y, rotation_matrix_3d_z,
    translation_matrix_4d, scaling_matrix_4d, rotation_matrix_4d_z,
    perspective_projection_matrix, look_at_matrix,
    transform_point_homogeneous
)


class TestVectorMatrixIntegration(unittest.TestCase):
    """Test vectors and matrices working together"""
    
    def test_2d_transformations(self):
        """Test 2D transformation pipeline"""
        # Create a point
        point = Vector2(1, 0)
        
        # Rotate 90 degrees
        rotation = rotation_matrix_2d(math.pi / 2)
        rotated = point * rotation
        
        self.assertAlmostEqual(rotated.x, 0, places=10)
        self.assertAlmostEqual(rotated.y, 1, places=10)
        
        # Scale by 2
        scale = scaling_matrix_2d(2)
        scaled = rotated * scale
        
        self.assertAlmostEqual(scaled.x, 0, places=10)
        self.assertAlmostEqual(scaled.y, 2, places=10)
        
        # Combined transformation
        combined = scale * rotation
        final = point * combined
        
        self.assertAlmostEqual(final.x, 0, places=10)
        self.assertAlmostEqual(final.y, 2, places=10)
    
    def test_3d_transformation_chain(self):
        """Test chaining 3D transformations"""
        point = Vector3(1, 0, 0)
        
        # Rotate around Y axis by 90 degrees (X -> -Z)
        rot_y = rotation_matrix_3d_y(math.pi / 2)
        
        # Then rotate around Z axis by 90 degrees (-Z -> -Y)
        rot_z = rotation_matrix_3d_z(math.pi / 2)
        
        # Apply transformations
        after_y = rot_y * point
        final = rot_z * after_y
        
        self.assertAlmostEqual(final.x, 0, places=10)
        self.assertAlmostEqual(final.y, -1, places=10)
        self.assertAlmostEqual(final.z, 0, places=10)
        
        # Same result with combined matrix
        combined = rot_z * rot_y
        final_combined = combined * point
        
        for i in range(3):
            self.assertAlmostEqual(final[i], final_combined[i], places=10)
    
    def test_homogeneous_coordinates(self):
        """Test 4D homogeneous coordinate transformations"""
        # 3D point in homogeneous coordinates
        point = Vector4(1, 2, 3, 1)
        
        # Create transformation matrix (translate by (5, 0, 0) then scale by 2)
        translation = translation_matrix_4d(5, 0, 0)
        scaling = scaling_matrix_4d(2)
        
        # Combined transformation
        transform = scaling * translation
        result = transform * point
        
        # Point (1, 2, 3) -> translate -> (6, 2, 3) -> scale -> (12, 4, 6)
        self.assertAlmostEqual(result.x, 12, places=10)
        self.assertAlmostEqual(result.y, 4, places=10)
        self.assertAlmostEqual(result.z, 6, places=10)
        self.assertAlmostEqual(result.w, 1, places=10)


class TestGraphicsPipeline(unittest.TestCase):
    """Test typical 3D graphics transformations"""
    
    def test_model_view_projection(self):
        """Test the classic MVP transformation pipeline"""
        # Model vertex
        vertex = Vector3(1, 1, 0)
        
        # Model matrix (rotate around Z by 45 degrees)
        model = rotation_matrix_4d_z(math.pi / 4)
        
        # View matrix (camera at (0, 0, 5) looking at origin)
        view = look_at_matrix(
            Vector3(0, 0, 5),  # eye
            Vector3(0, 0, 0),  # target
            Vector3(0, 1, 0)   # up
        )
        
        # Projection matrix
        projection = perspective_projection_matrix(
            math.pi / 4,  # 45 degree FOV
            16.0/9.0,     # aspect ratio
            0.1,          # near
            100.0         # far
        )
        
        # Transform vertex through pipeline
        # Convert to homogeneous coordinates
        vertex_h = Vector4(vertex.x, vertex.y, vertex.z, 1.0)
        
        # Apply transformations
        world_pos = model * vertex_h
        view_pos = view * world_pos
        clip_pos = projection * view_pos
        
        # The vertex should be transformed without errors
        self.assertIsInstance(clip_pos, Vector4)
        
        # Combined MVP matrix
        mvp = projection * view * model
        clip_pos_combined = mvp * vertex_h
        
        # Results should be the same
        for i in range(4):
            self.assertAlmostEqual(clip_pos[i], clip_pos_combined[i], places=10)
    
    def test_vertex_batch_processing(self):
        """Test processing multiple vertices"""
        # Create a triangle
        vertices = [
            Vector3(-1, -1, 0),
            Vector3(1, -1, 0),
            Vector3(0, 1, 0)
        ]
        
        # Transformation matrix (scale by 2)
        transform = scaling_matrix_4d(2)
        
        # Process all vertices
        transformed = []
        for vertex in vertices:
            # Convert to homogeneous and transform
            vertex_h = Vector4(vertex.x, vertex.y, vertex.z, 1.0)
            result = transform * vertex_h
            # Convert back to 3D
            transformed.append(Vector3(result.x, result.y, result.z))
        
        # Check results
        expected = [
            Vector3(-2, -2, 0),
            Vector3(2, -2, 0),
            Vector3(0, 2, 0)
        ]
        
        for i, (actual, exp) in enumerate(zip(transformed, expected)):
            self.assertAlmostEqual(actual.x, exp.x, places=10)
            self.assertAlmostEqual(actual.y, exp.y, places=10)
            self.assertAlmostEqual(actual.z, exp.z, places=10)


class TestPhysicsIntegration(unittest.TestCase):
    """Test vector/matrix operations for physics simulations"""
    
    def test_rigid_body_transformation(self):
        """Test rigid body position and rotation"""
        # Object vertices (a simple cube corner)
        local_vertices = [
            Vector3(0, 0, 0),
            Vector3(1, 0, 0),
            Vector3(0, 1, 0),
            Vector3(0, 0, 1)
        ]
        
        # Object transform (45 degree rotation around Y, translate by (2, 1, 0))
        rotation = rotation_matrix_3d_y(math.pi / 4)
        position = Vector3(2, 1, 0)
        
        # Transform vertices to world space
        world_vertices = []
        for vertex in local_vertices:
            # Apply rotation then translation
            rotated = rotation * vertex
            world_pos = rotated + position
            world_vertices.append(world_pos)
        
        # First vertex should be at the object position
        self.assertAlmostEqual(world_vertices[0].x, 2, places=10)
        self.assertAlmostEqual(world_vertices[0].y, 1, places=10)
        self.assertAlmostEqual(world_vertices[0].z, 0, places=10)
        
        # Second vertex (1,0,0) rotated 45 degrees around Y should be at (√2/2, 0, √2/2)
        expected_x = math.sqrt(2) / 2 + 2  # plus translation
        expected_z = math.sqrt(2) / 2 + 0
        
        self.assertAlmostEqual(world_vertices[1].x, expected_x, places=10)
        self.assertAlmostEqual(world_vertices[1].y, 1, places=10)
        self.assertAlmostEqual(world_vertices[1].z, expected_z, places=10)
    
    def test_collision_detection_helpers(self):
        """Test vector operations used in collision detection"""
        # Two points
        p1 = Vector3(0, 0, 0)
        p2 = Vector3(3, 4, 0)
        
        # Distance
        distance = p1.distance_to(p2)
        self.assertEqual(distance, 5.0)  # 3-4-5 triangle
        
        # Direction vector
        direction = (p2 - p1).normalized
        self.assertAlmostEqual(direction.magnitude, 1.0, places=10)
        self.assertAlmostEqual(direction.x, 0.6, places=10)
        self.assertAlmostEqual(direction.y, 0.8, places=10)
        
        # Dot product for angle calculation
        v1 = Vector3(1, 0, 0)
        v2 = Vector3(0, 1, 0)
        dot = v1.dot(v2)
        self.assertEqual(dot, 0)  # Perpendicular vectors
        
        # Cross product for normal calculation
        normal = v1.cross(v2)
        self.assertEqual(normal.x, 0)
        self.assertEqual(normal.y, 0)
        self.assertEqual(normal.z, 1)


class TestNumericalStability(unittest.TestCase):
    """Test numerical stability and precision"""
    
    def test_repeated_transformations(self):
        """Test that repeated transformations maintain stability"""
        vector = Vector3(1, 0, 0)
        
        # Apply small rotations repeatedly
        small_rotation = rotation_matrix_3d_z(0.01)  # ~0.57 degrees
        
        current = vector
        for _ in range(628):  # Should be close to full rotation (2π radians)
            current = small_rotation * current
        
        # After ~full rotation, should be back near original
        self.assertAlmostEqual(current.x, vector.x, places=2)
        self.assertAlmostEqual(current.y, vector.y, places=2)
        self.assertAlmostEqual(current.z, vector.z, places=10)
    
    def test_orthogonal_matrix_properties(self):
        """Test that rotation matrices maintain orthogonality"""
        angle = math.pi / 7  # Non-standard angle
        rotation = rotation_matrix_3d_x(angle)
        
        # Check that it's orthogonal (R * R^T = I)
        self.assertTrue(rotation.is_orthogonal())
        
        # Check that determinant is 1
        det = rotation.determinant()
        self.assertAlmostEqual(det, 1.0, places=10)
    
    def test_matrix_inverse_precision(self):
        """Test precision of matrix inversion"""
        # Create a well-conditioned matrix
        m = Matrix([
            [2, 1, 0],
            [1, 2, 1],
            [0, 1, 2]
        ])
        
        # Compute inverse
        inv = m.inverse()
        
        # Check that M * M^-1 = I
        product = m * inv
        identity = Matrix.identity(3)
        
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(product[i, j], identity[i, j], places=12)


class TestPerformanceCharacteristics(unittest.TestCase):
    """Test performance characteristics (basic timing, not strict benchmarks)"""
    
    def test_large_matrix_operations(self):
        """Test operations on larger matrices complete successfully"""
        # Create larger matrices
        size = 50
        m1 = Matrix(rows=size, cols=size)
        m2 = Matrix.identity(size)
        
        # Fill with some data
        for i in range(size):
            for j in range(size):
                m1[i, j] = (i + j) % 10
        
        # Test basic operations complete
        result_add = m1 + m2
        result_mul = m1 * m2
        
        self.assertEqual(result_add.rows, size)
        self.assertEqual(result_mul.rows, size)
    
    def test_vector_batch_operations(self):
        """Test operations on many vectors"""
        # Create many vectors
        vectors = [Vector3(i, i+1, i+2) for i in range(1000)]
        
        # Apply transformation to all
        transform = scaling_matrix_3d(2)
        transformed = [transform * v for v in vectors]
        
        # Check a few results
        self.assertEqual(len(transformed), 1000)
        self.assertEqual(transformed[0].x, 0)  # 2 * 0
        self.assertEqual(transformed[1].x, 2)  # 2 * 1
        self.assertEqual(transformed[999].x, 1998)  # 2 * 999


if __name__ == '__main__':
    unittest.main(verbosity=2)