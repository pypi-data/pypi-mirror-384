# Vector classes
from .vector import Vector2, Vector3, Vector4, Vector, IVector2, IVector3, IVector4

# Matrix class and constants
from .matrix import Matrix, IDENTITY_2D, IDENTITY_3D, IDENTITY_4D

# Convenient vector aliases (if they exist in vector.py)
from .vector import vec2, vec3, vec4, ivec2, ivec3, ivec4

# All transformation functions should be in either vector.py or matrix.py
# Update these imports based on where you actually placed the functions:

# If transformation functions are in matrix.py:
from .matrix import (
    # 2D transformations
    rotation_matrix_2d,
    scaling_matrix_2d,
    shear_matrix_2d,
    reflection_matrix_2d,
    transform_point_2d,
    # 3D transformations
    rotation_matrix_3d,
    rotation_matrix_3d_arbitrary,
    scaling_matrix_3d,
    shear_matrix_3d,
    reflection_matrix_3d,
    transform_point_3d,
    # 4D transformations
    translation_matrix_4d,
    scaling_matrix_4d,
    rotation_matrix_4d_x,
    rotation_matrix_4d_y,
    rotation_matrix_4d_z,
    transform_point_homogeneous,
    # Graphics
    perspective_projection_matrix,
    orthographic_projection_matrix,
    look_at_matrix,
    # Utilities
    interpolate_matrices,
)

# Public API
__all__ = [
    # Vector classes
    "Vector2",
    "IVector2",
    "Vector3",
    "IVector3",
    "Vector4",
    "IVector4",
    "Vector",
    # Matrix class
    "Matrix",
    # Identity matrices
    "IDENTITY_2D",
    "IDENTITY_3D",
    "IDENTITY_4D",
    # Vector aliases
    "vec2",
    "ivec2",
    "vec3",
    "ivec3",
    "vec4",
    "ivec4",
    # 2D transformations
    "rotation_matrix_2d",
    "scaling_matrix_2d",
    "shear_matrix_2d",
    "reflection_matrix_2d",
    "transform_point_2d",
    # 3D transformations
    "rotation_matrix_3d",
    "rotation_matrix_3d_arbitrary",
    "scaling_matrix_3d",
    "shear_matrix_3d",
    "reflection_matrix_3d",
    "transform_point_3d",
    # 4D transformations
    "translation_matrix_4d",
    "scaling_matrix_4d",
    "rotation_matrix_4d_x",
    "rotation_matrix_4d_y",
    "rotation_matrix_4d_z",
    "transform_point_homogeneous",
    # Graphics
    "perspective_projection_matrix",
    "orthographic_projection_matrix",
    "look_at_matrix",
    # Utilities
    "interpolate_matrices",
]
