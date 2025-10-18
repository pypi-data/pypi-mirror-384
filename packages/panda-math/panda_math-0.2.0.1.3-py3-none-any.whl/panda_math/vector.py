from __future__ import annotations
import numpy as np
from typing import (
    List,
    Tuple,
    Union,
    Iterator,
    Iterable,
    TypeVar,
    Generic,
    Any,
    TYPE_CHECKING,
    Type,
    Sequence,
)
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .matrix import Matrix

T = TypeVar("T", bound="Vector")
NumT = TypeVar("NumT", int, float)

Number = Union[int, float]


class Vector(Generic[T], Sequence[float], ABC):
    """Base class for all vector implementations"""

    @classmethod
    @abstractmethod
    def _dimension(cls) -> int:
        pass

    @classmethod
    @abstractmethod
    def _vector_type(cls) -> Type:
        pass

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(str(x) for x in self)})"

    def __repr__(self) -> str:
        return str(self)

    def __iter__(self) -> Iterator[float]:
        raise NotImplementedError("Subclasses must implement __iter__")

    def __len__(self) -> int:
        raise NotImplementedError("Subclasses must implement __len__")

    def __getitem__(self, index: int) -> float:
        raise NotImplementedError("Subclasses must implement __getitem__")

    def __contains__(self, item) -> bool:
        raise NotImplementedError("Subclasses must implement __contains__")

    def to_list(self) -> List[float]:
        return list(self)

    def to_tuple(self) -> Tuple[float, ...]:
        return tuple(self)

    def to_numpy(self) -> np.ndarray:
        return np.array(list(self))

    def to_bytes(self) -> bytes:
        """Convert vector to bytes for GLSL shader uniforms (little-endian float32)"""
        import struct

        return struct.pack(f"<{len(self)}f", *self)

    def _get_component(self, char: str) -> float:
        components = vars(self)
        for key in components.keys():
            if key[1] == char:
                return components[key]
        raise ValueError(f"Invalid swizzle character: {char}")

    def _set_component(self, char: str, value: float):
        components = vars(self)
        for key in list(components.keys()):
            if key[1] == char:
                return setattr(self, key, float(value))
        raise ValueError(f"Invalid swizzle character: {char}")

    @classmethod
    def from_numpy(cls: Type[T], array: np.ndarray) -> T:
        if len(array) < cls._dimension():
            raise ValueError(f"Array must have at least {cls._dimension()} elements")
        return cls(*array[: cls._dimension()])

    @property
    def magnitude(self) -> float:
        return np.sqrt(sum(x**2 for x in self))

    def normalize(self: T) -> T:
        mag = self.magnitude
        if mag == 0:
            return self
        cls: Type[T] = type(self)
        return cls(*(x / mag for x in self))

    @property
    def normalized(self: T) -> T:
        return self.normalize()

    def distance_to(self, other: T) -> float:
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Can only calculate distance to another {self.__class__.__name__}"
            )
        return np.sqrt(sum((a - b) ** 2 for a, b in zip(self, other)))

    def dot(self, other: T) -> float:
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Can only calculate dot product with another {self.__class__.__name__}"
            )
        return sum(a * b for a, b in zip(self, other))

    def reverse(self: T) -> T:
        cls: Type[T] = type(self)
        return cls(*(-x for x in self))

    @property
    def reversed(self: T) -> T:
        return self.reverse()


class Vector2(Vector["Vector2"]):
    @classmethod
    def _dimension(cls) -> int:
        return 2

    @classmethod
    def _vector_type(cls) -> Type:
        return float

    def __init__(self, *args):
        self._x: float
        self._y: float

        # Flatten all arguments into a list of scalars
        flattened = []
        for arg in args:
            if isinstance(arg, (Vector, Iterable)) and not isinstance(
                arg, (str, bytes)
            ):
                flattened.extend(arg)
            elif isinstance(arg, Number):
                flattened.append(arg)
            else:
                raise TypeError(f"Invalid argument type for Vector2: {type(arg)}")

        if len(flattened) == 0:
            self._x = self._y = self._vector_type()(0)
        elif len(flattened) == 1:
            self._x = self._y = self._vector_type()(flattened[0])
        elif len(flattened) >= 2:
            self._x, self._y = map(self._vector_type(), flattened[:2])
        else:
            raise TypeError("Invalid arguments for Vector2")

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def xy(self) -> "Vector2":
        return self.__class__(self._x, self._y)

    @x.setter
    def x(self, value: float):
        self._x = value

    @y.setter
    def y(self, value: float):
        self._y = value

    @xy.setter
    def xy(self, values: Iterable):
        values = list(values)
        if len(values) != 2:
            raise ValueError(f"Vector2 requires exactly 2 values, got {len(values)}")
        self._x, self._y = values

    def __getattr__(
        self, name: str
    ) -> Union[float, "Vector2", "Vector3", "Vector4", Tuple[float, ...]]:
        try:
            attributes = tuple(self._get_component(char) for char in name)
            length = len(attributes)
            if length == 1:
                return attributes[0]
            types = {2: Vector2, 3: Vector3, 4: Vector4}
            return types.get(length, tuple)(attributes)
        except:
            pass
        if len(attributes) == 0:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )
        else:
            return attributes

    def __setattr__(self, name: str, value: float) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        for char in name:
            try:
                self._set_component(char, value)
            except:
                object.__setattr__(self, char, value)

    def __iter__(self) -> Iterator[float]:
        yield self._x
        yield self._y

    def __len__(self) -> int:
        return 2

    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self._x
        elif index == 1:
            return self._y
        else:
            raise IndexError("Vector2 index out of range")

    def __setitem__(self, index: int, value: float):
        if index == 0:
            self._x = value
        elif index == 1:
            self._y = value
        else:
            raise IndexError("Vector2 index out of range")

    def __add__(self, other: Union["Vector2", Number]) -> "Vector2":
        if isinstance(other, Vector2):
            return self.__class__(self._x + other.x, self._y + other.y)
        elif isinstance(other, Number):
            return self.__class__(self._x + other, self._y + other)
        return NotImplemented

    def __radd__(self, other: Number) -> "Vector2":
        if isinstance(other, Number):
            return self.__class__(self._x + other, self._y + other)
        return NotImplemented

    def __sub__(self, other: Union["Vector2", Number]) -> "Vector2":
        if isinstance(other, Vector2):
            return self.__class__(self._x - other.x, self._y - other.y)
        elif isinstance(other, Number):
            return self.__class__(self._x - other, self._y - other)
        return NotImplemented

    def __rsub__(self, other: Number) -> "Vector2":
        if isinstance(other, Number):
            return self.__class__(other - self._x, other - self._y)
        return NotImplemented

    def __mul__(
        self, other: Union["Vector2", float, int, "Matrix"]
    ) -> Union["Vector2", Any]:
        from .matrix import Matrix

        if isinstance(other, Number):
            return self.__class__(self._x * other, self._y * other)
        elif isinstance(other, Vector2):
            return self.__class__(self._x * other.x, self._y * other.y)
        elif isinstance(other, Matrix):
            if other.cols != 2:
                raise ValueError(
                    f"Cannot multiply Vector2 with Matrix({other.rows}×{other.cols})"
                )
            result = [0.0] * other.rows
            for i in range(other.rows):
                for j in range(other.cols):
                    if j == 0:
                        result[i] += self._x * other.data[i][j]
                    else:
                        result[i] += self._y * other.data[i][j]
            if len(result) == 2:
                return self.__class__(result[0], result[1])
            return result
        return NotImplemented

    def __rmul__(self, other: Number) -> "Vector2":
        if isinstance(other, Number):
            return self.__class__(self._x * other, self._y * other)
        return NotImplemented

    def __truediv__(self, other: Union["Vector2", Number]) -> "Vector2":
        if isinstance(other, Number):
            return self.__class__(self._x / other, self._y / other)
        elif isinstance(other, Vector2):
            return self.__class__(self._x / other.x, self._y / other.y)
        return NotImplemented

    def __rtruediv__(self, other: Number) -> "Vector2":
        if isinstance(other, Number):
            return self.__class__(other / self._x, other / self._y)
        return NotImplemented

    def __floordiv__(self, other: Union["Vector2", Number]) -> "Vector2":
        if isinstance(other, Number):
            return self.__class__(self._x // other, self._y // other)
        elif isinstance(other, Vector2):
            return self.__class__(self._x // other.x, self._y // other.y)
        return NotImplemented

    def __rfloordiv__(self, other: Number) -> "Vector2":
        if isinstance(other, Number):
            return self.__class__(other // self._x, other // self._y)
        return NotImplemented

    def __mod__(self, other: Union["Vector2", Number]) -> "Vector2":
        if isinstance(other, Number):
            return self.__class__(self._x % other, self._y % other)
        elif isinstance(other, Vector2):
            return self.__class__(self._x % other.x, self._y % other.y)
        return NotImplemented

    def __rmod__(self, other: Number) -> "Vector2":
        if isinstance(other, Number):
            return self.__class__(other % self._x, other % self._y)
        return NotImplemented

    def __pow__(self, other: Union["Vector2", Number]) -> "Vector2":
        if isinstance(other, Number):
            return self.__class__(self._x**other, self._y**other)
        elif isinstance(other, Vector2):
            return self.__class__(self._x**other.x, self._y**other.y)
        return NotImplemented

    def __rpow__(self, other: Number) -> "Vector2":
        if isinstance(other, Number):
            return self.__class__(other**self._x, other**self._y)
        return NotImplemented

    def __iadd__(self, other: Union["Vector2", Number]) -> "Vector2":
        if isinstance(other, Vector2):
            self._x += other.x
            self._y += other.y
        elif isinstance(other, Number):
            self._x += other
            self._y += other
        else:
            return NotImplemented
        return self

    def __isub__(self, other: Union["Vector2", Number]) -> "Vector2":
        if isinstance(other, Vector2):
            self._x -= other.x
            self._y -= other.y
        elif isinstance(other, Number):
            self._x -= other
            self._y -= other
        else:
            return NotImplemented
        return self

    def __imul__(self, other: Union["Vector2", Number]) -> "Vector2":
        if isinstance(other, Number):
            self._x *= other
            self._y *= other
        elif isinstance(other, Vector2):
            self._x *= other.x
            self._y *= other.y
        else:
            return NotImplemented
        return self

    def __itruediv__(self, other: Union["Vector2", Number]) -> "Vector2":
        if isinstance(other, Number):
            self._x /= other
            self._y /= other
        elif isinstance(other, Vector2):
            self._x /= other.x
            self._y /= other.y
        else:
            return NotImplemented
        return self

    def __ifloordiv__(self, other: Union["Vector2", Number]) -> "Vector2":
        if isinstance(other, Number):
            self._x //= other
            self._y //= other
        elif isinstance(other, Vector2):
            self._x //= other.x
            self._y //= other.y
        else:
            return NotImplemented
        return self

    def __imod__(self, other: Union["Vector2", Number]) -> "Vector2":
        if isinstance(other, Number):
            self._x %= other
            self._y %= other
        elif isinstance(other, Vector2):
            self._x %= other.x
            self._y %= other.y
        else:
            return NotImplemented
        return self

    def __ipow__(self, other: Union["Vector2", Number]) -> "Vector2":
        if isinstance(other, Number):
            self._x **= other
            self._y **= other
        elif isinstance(other, Vector2):
            self._x **= other.x
            self._y **= other.y
        else:
            return NotImplemented
        return self

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Vector2):
            return self._x == other.x and self._y == other.y
        return NotImplemented

    def __lt__(self, other: Union["Vector2", Number]) -> bool:
        if isinstance(other, Vector2):
            return self._x < other.x and self._y < other.y
        elif isinstance(other, Number):
            return self._x < other and self._y < other
        return NotImplemented

    def __gt__(self, other: Union["Vector2", Number]) -> bool:
        if isinstance(other, Vector2):
            return self._x > other.x and self._y > other.y
        elif isinstance(other, Number):
            return self._x > other and self._y > other
        return NotImplemented

    def __le__(self, other: Union["Vector2", Number]) -> bool:
        if isinstance(other, Vector2):
            return self._x <= other.x and self._y <= other.y
        elif isinstance(other, Number):
            return self._x <= other and self._y <= other
        return NotImplemented

    def __ge__(self, other: Union["Vector2", Number]) -> bool:
        if isinstance(other, Vector2):
            return self._x >= other.x and self._y >= other.y
        elif isinstance(other, Number):
            return self._x >= other and self._y >= other
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self._x, self._y))


class IVector2(Vector2):
    """Integer Vector2 implementation"""

    @classmethod
    def _vector_type(cls) -> Type:
        return int

    def __init__(self, *args):
        self._x: int
        self._y: int

        flattened = []
        for arg in args:
            if isinstance(arg, (Vector, Iterable)) and not isinstance(
                arg, (str, bytes)
            ):
                flattened.extend(arg)
            elif isinstance(arg, Number):
                flattened.append(arg)
            else:
                raise TypeError(f"Invalid argument type for IVector2: {type(arg)}")

        if len(flattened) == 0:
            self._x = self._y = self._vector_type()(0)
        elif len(flattened) == 1:
            self._x = self._y = self._vector_type()(flattened[0])
        else:
            self._x, self._y = map(self._vector_type(), flattened[:2])

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, value: int):
        self._x = value

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, value: int):
        self._y = value


class Vector3(Vector["Vector3"]):
    @classmethod
    def _dimension(cls) -> int:
        return 3

    @classmethod
    def _vector_type(cls) -> Type:
        return float

    def __init__(self, *args):
        self._x: float
        self._y: float
        self._z: float

        # Flatten all arguments into a list of scalars
        flattened = []
        for arg in args:
            if isinstance(arg, (Vector, Iterable)) and not isinstance(
                arg, (str, bytes)
            ):
                flattened.extend(arg)
            elif isinstance(arg, Number):
                flattened.append(arg)
            else:
                raise TypeError(f"Invalid argument type for Vector3: {type(arg)}")

        if len(flattened) == 0:
            self._x = self._y = self._z = self._vector_type()(0)
        elif len(flattened) == 1:
            self._x = self._y = self._z = self._vector_type()(flattened[0])
        elif len(flattened) >= 3:
            self._x, self._y, self._z = map(self._vector_type(), flattened[:3])
        else:
            raise TypeError("Invalid arguments for Vector3")

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def z(self) -> float:
        return self._z

    @property
    def xyz(self) -> "Vector3":
        return self.__class__(self._x, self._y, self._z)

    @x.setter
    def x(self, value: float):
        self._x = value

    @y.setter
    def y(self, value: float):
        self._y = value

    @z.setter
    def z(self, value: float):
        self._z = value

    @xyz.setter
    def xyz(self, values: Iterable):
        values = list(values)
        if len(values) != 3:
            raise ValueError(f"Vector3 requires exactly 3 values, got {len(values)}")
        self._x, self._y, self._z = values

    def __getattr__(
        self, name: str
    ) -> Union[float, "Vector2", "Vector3", "Vector4", Tuple[float, ...]]:
        try:
            attributes = tuple(self._get_component(char) for char in name)
            length = len(attributes)
            if length == 1:
                return attributes[0]
            types = {2: Vector2, 3: Vector3, 4: Vector4}
            return types.get(length, tuple)(attributes)
        except:
            pass
        if len(attributes) == 0:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )
        else:
            return attributes

    def __setattr__(self, name: str, value: float) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        for char in name:
            try:
                self._set_component(char, value)
            except:
                object.__setattr__(self, char, value)

    def __iter__(self) -> Iterator[float]:
        yield self._x
        yield self._y
        yield self._z

    def __len__(self) -> int:
        return 3

    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self._x
        elif index == 1:
            return self._y
        elif index == 2:
            return self._z
        else:
            raise IndexError("Vector3 index out of range")

    def __setitem__(self, index: int, value: float):
        if index == 0:
            self._x = value
        elif index == 1:
            self._y = value
        elif index == 2:
            self._z = value
        else:
            raise IndexError("Vector3 index out of range")

    def __add__(self, other: Union["Vector3", Number]) -> "Vector3":
        if isinstance(other, Vector3):
            return self.__class__(
                self._x + other.x, self._y + other.y, self._z + other.z
            )
        elif isinstance(other, Number):
            return self.__class__(self._x + other, self._y + other, self._z + other)
        return NotImplemented

    def __radd__(self, other: Number) -> "Vector3":
        if isinstance(other, Number):
            return self.__class__(self._x + other, self._y + other, self._z + other)
        return NotImplemented

    def __sub__(self, other: Union["Vector3", Number]) -> "Vector3":
        if isinstance(other, Vector3):
            return self.__class__(
                self._x - other.x, self._y - other.y, self._z - other.z
            )
        elif isinstance(other, Number):
            return self.__class__(self._x - other, self._y - other, self._z - other)
        return NotImplemented

    def __rsub__(self, other: Number) -> "Vector3":
        if isinstance(other, Number):
            return self.__class__(other - self._x, other - self._y, other - self._z)
        return NotImplemented

    def __mul__(
        self, other: Union["Vector3", float, int, "Matrix"]
    ) -> Union["Vector3", Any]:
        from .matrix import Matrix

        if isinstance(other, Number):
            return self.__class__(self._x * other, self._y * other, self._z * other)
        elif isinstance(other, Vector3):
            return self.__class__(
                self._x * other.x, self._y * other.y, self._z * other.z
            )
        elif isinstance(other, Matrix):
            if other.cols != 3:
                raise ValueError(
                    f"Cannot multiply Vector3 with Matrix({other.rows}×{other.cols})"
                )
            result = [0.0] * other.rows
            for i in range(other.rows):
                for j in range(other.cols):
                    if j == 0:
                        result[i] += self._x * other.data[i][j]
                    elif j == 1:
                        result[i] += self._y * other.data[i][j]
                    else:
                        result[i] += self._z * other.data[i][j]
            if len(result) == 3:
                return self.__class__(result[0], result[1], result[2])
            return result
        return NotImplemented

    def __rmul__(self, other: Number) -> "Vector3":
        if isinstance(other, Number):
            return self.__class__(self._x * other, self._y * other, self._z * other)
        return NotImplemented

    def __truediv__(self, other: Union["Vector3", Number]) -> "Vector3":
        if isinstance(other, Number):
            return self.__class__(self._x / other, self._y / other, self._z / other)
        elif isinstance(other, Vector3):
            return self.__class__(
                self._x / other.x, self._y / other.y, self._z / other.z
            )
        return NotImplemented

    def __rtruediv__(self, other: Number) -> "Vector3":
        if isinstance(other, Number):
            return self.__class__(other / self._x, other / self._y, other / self._z)
        return NotImplemented

    def __floordiv__(self, other: Union["Vector3", Number]) -> "Vector3":
        if isinstance(other, Number):
            return self.__class__(self._x // other, self._y // other, self._z // other)
        elif isinstance(other, Vector3):
            return self.__class__(
                self._x // other.x, self._y // other.y, self._z // other.z
            )
        return NotImplemented

    def __rfloordiv__(self, other: Number) -> "Vector3":
        if isinstance(other, Number):
            return self.__class__(other // self._x, other // self._y, other // self._z)
        return NotImplemented

    def __mod__(self, other: Union["Vector3", Number]) -> "Vector3":
        if isinstance(other, Number):
            return self.__class__(self._x % other, self._y % other, self._z % other)
        elif isinstance(other, Vector3):
            return self.__class__(
                self._x % other.x, self._y % other.y, self._z % other.z
            )
        return NotImplemented

    def __rmod__(self, other: Number) -> "Vector3":
        if isinstance(other, Number):
            return self.__class__(other % self._x, other % self._y, other % self._z)
        return NotImplemented

    def __pow__(self, other: Union["Vector3", Number]) -> "Vector3":
        if isinstance(other, Number):
            return self.__class__(self._x**other, self._y**other, self._z**other)
        elif isinstance(other, Vector3):
            return self.__class__(self._x**other.x, self._y**other.y, self._z**other.z)
        return NotImplemented

    def __rpow__(self, other: Number) -> "Vector3":
        if isinstance(other, Number):
            return self.__class__(other**self._x, other**self._y, other**self._z)
        return NotImplemented

    def __iadd__(self, other: Union["Vector3", Number]) -> "Vector3":
        if isinstance(other, Vector3):
            self._x += other.x
            self._y += other.y
            self._z += other.z
        elif isinstance(other, Number):
            self._x += other
            self._y += other
            self._z += other
        else:
            return NotImplemented
        return self

    def __isub__(self, other: Union["Vector3", Number]) -> "Vector3":
        if isinstance(other, Vector3):
            self._x -= other.x
            self._y -= other.y
            self._z -= other.z
        elif isinstance(other, Number):
            self._x -= other
            self._y -= other
            self._z -= other
        else:
            return NotImplemented
        return self

    def __imul__(self, other: Union["Vector3", Number]) -> "Vector3":
        if isinstance(other, Number):
            factor = float(other)
            self._x *= factor
            self._y *= factor
            self._z *= factor
        elif isinstance(other, Vector3):
            self._x *= other.x
            self._y *= other.y
            self._z *= other.z
        else:
            return NotImplemented
        return self

    def __itruediv__(self, other: Union["Vector3", Number]) -> "Vector3":
        if isinstance(other, Number):
            self._x /= other
            self._y /= other
            self._z /= other
        elif isinstance(other, Vector3):
            self._x /= other.x
            self._y /= other.y
            self._z /= other.z
        else:
            return NotImplemented
        return self

    def __ifloordiv__(self, other: Union["Vector3", Number]) -> "Vector3":
        if isinstance(other, Number):
            self._x //= other
            self._y //= other
            self._z //= other
        elif isinstance(other, Vector3):
            self._x //= other.x
            self._y //= other.y
            self._z //= other.z
        else:
            return NotImplemented
        return self

    def __imod__(self, other: Union["Vector3", Number]) -> "Vector3":
        if isinstance(other, Number):
            self._x %= other
            self._y %= other
            self._z %= other
        elif isinstance(other, Vector3):
            self._x %= other.x
            self._y %= other.y
            self._z %= other.z
        else:
            return NotImplemented
        return self

    def __ipow__(self, other: Union["Vector3", Number]) -> "Vector3":
        if isinstance(other, Number):
            self._x **= other
            self._y **= other
            self._z **= other
        elif isinstance(other, Vector3):
            self._x **= other.x
            self._y **= other.y
            self._z **= other.z
        else:
            return NotImplemented
        return self

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Vector3):
            return self._x == other.x and self._y == other.y and self._z == other.z
        return NotImplemented

    def __lt__(self, other: Union["Vector3", Number]) -> bool:
        if isinstance(other, Vector3):
            return self._x < other.x and self._y < other.y and self._z < other.z
        elif isinstance(other, Number):
            return self._x < other and self._y < other and self._z < other
        return NotImplemented

    def __gt__(self, other: Union["Vector3", Number]) -> bool:
        if isinstance(other, Vector3):
            return self._x > other.x and self._y > other.y and self._z > other.z
        elif isinstance(other, Number):
            return self._x > other and self._y > other and self._z > other
        return NotImplemented

    def __le__(self, other: Union["Vector3", Number]) -> bool:
        if isinstance(other, Vector3):
            return self._x <= other.x and self._y <= other.y and self._z <= other.z
        elif isinstance(other, Number):
            return self._x <= other and self._y <= other and self._z <= other
        return NotImplemented

    def __ge__(self, other: Union["Vector3", Number]) -> bool:
        if isinstance(other, Vector3):
            return self._x >= other.x and self._y >= other.y and self._z >= other.z
        elif isinstance(other, Number):
            return self._x >= other and self._y >= other and self._z >= other
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self._x, self._y, self._z))

    def cross(self, other: "Vector3") -> "Vector3":
        """Calculate the cross product with another Vector3"""
        if not isinstance(other, Vector3):
            raise TypeError("Can only calculate cross product with another Vector3")
        return self.__class__(
            self._y * other.z - self._z * other.y,
            self._z * other.x - self._x * other.z,
            self._x * other.y - self._y * other.x,
        )


class IVector3(Vector3):
    """Integer Vector3 implementation"""

    @classmethod
    def _vector_type(cls) -> Type:
        return int

    def __init__(self, *args):
        self._x: int
        self._y: int
        self._z: int

        # Flatten all arguments into a list of scalars
        flattened = []
        for arg in args:
            if isinstance(arg, (Vector, Iterable)) and not isinstance(
                arg, (str, bytes)
            ):
                flattened.extend(arg)
            elif isinstance(arg, Number):
                flattened.append(arg)
            else:
                raise TypeError(f"Invalid argument type for IVector3: {type(arg)}")

        if len(flattened) == 0:
            self._x = self._y = self._z = self._vector_type()(0)
        elif len(flattened) == 1:
            self._x = self._y = self._z = self._vector_type()(flattened[0])
        elif len(flattened) >= 3:
            self._x, self._y, self._z = map(self._vector_type(), flattened[:3])
        else:
            raise TypeError("Invalid arguments for IVector3")


class Vector4(Vector["Vector4"]):

    @classmethod
    def _dimension(cls) -> int:
        return 4

    @classmethod
    def _vector_type(cls) -> Type:
        return float

    def __init__(self, *args):
        self._x: float
        self._y: float
        self._z: float
        self._w: float

        # Flatten all arguments into a list of scalars
        flattened = []
        for arg in args:
            if isinstance(arg, (Vector, Iterable)) and not isinstance(
                arg, (str, bytes)
            ):
                flattened.extend(arg)
            elif isinstance(arg, Number):
                flattened.append(arg)
            else:
                raise TypeError(f"Invalid argument type for Vector4: {type(arg)}")

        if len(flattened) == 0:
            self._x = self._y = self._z = self._w = self._vector_type()(0)
        elif len(flattened) == 1:
            self._x = self._y = self._z = self._w = self._vector_type()(flattened[0])
        elif len(flattened) >= 4:
            self._x, self._y, self._z, self._w = map(self._vector_type(), flattened[:4])
        else:
            raise TypeError("Invalid arguments for Vector4")

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def z(self) -> float:
        return self._z

    @property
    def w(self) -> float:
        return self._w

    @property
    def xyzw(self) -> "Vector4":
        return Vector4(self._x, self._y, self._z, self._w)

    @x.setter
    def x(self, value: float):
        self._x = value

    @y.setter
    def y(self, value: float):
        self._y = value

    @z.setter
    def z(self, value: float):
        self._z = value

    @w.setter
    def w(self, value: float):
        self._w = value

    @xyzw.setter
    def xyzw(self, values: Iterable):
        values = list(values)
        if len(values) != 4:
            raise ValueError(f"Vector4 requires exactly 4 values, got {len(values)}")
        self._x, self._y, self._z, self._w = values

    def __getattr__(
        self, name: str
    ) -> Union[float, Vector2, Vector3, Vector4, Tuple[float, ...]]:
        try:
            attributes = tuple(self._get_component(char) for char in name)
            length = len(attributes)
            if length == 1:
                return attributes[0]
            types = {2: Vector2, 3: Vector3, 4: Vector4}
            return types.get(length, tuple)(attributes)
        except:
            pass
        if len(attributes) == 0:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )
        else:
            return attributes

    def __setattr__(self, name: str, value: float) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        for char in name:
            try:
                self._set_component(char, value)
            except:
                object.__setattr__(self, char, value)

    def __iter__(self) -> Iterator[float]:
        yield self._x
        yield self._y
        yield self._z
        yield self._w

    def __len__(self) -> int:
        return 4

    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self._x
        elif index == 1:
            return self._y
        elif index == 2:
            return self._z
        elif index == 3:
            return self._w
        else:
            raise IndexError("Vector4 index out of range")

    def __setitem__(self, index: int, value: float):
        if index == 0:
            self._x = value
        elif index == 1:
            self._y = value
        elif index == 2:
            self._z = value
        elif index == 3:
            self._w = value
        else:
            raise IndexError("Vector4 index out of range")

    def __add__(self, other: Union["Vector4", Number]) -> "Vector4":
        if isinstance(other, Vector4):
            return Vector4(
                self._x + other.x,
                self._y + other.y,
                self._z + other.z,
                self._w + other.w,
            )
        elif isinstance(other, Number):
            return Vector4(
                self._x + other, self._y + other, self._z + other, self._w + other
            )
        return NotImplemented

    def __radd__(self, other: Number) -> "Vector4":
        if isinstance(other, Number):
            return Vector4(
                self._x + other, self._y + other, self._z + other, self._w + other
            )
        return NotImplemented

    def __sub__(self, other: Union["Vector4", Number]) -> "Vector4":
        if isinstance(other, Vector4):
            return Vector4(
                self._x - other.x,
                self._y - other.y,
                self._z - other.z,
                self._w - other.w,
            )
        elif isinstance(other, Number):
            return Vector4(
                self._x - other, self._y - other, self._z - other, self._w - other
            )
        return NotImplemented

    def __rsub__(self, other: Number) -> "Vector4":
        if isinstance(other, Number):
            return Vector4(
                other - self._x, other - self._y, other - self._z, other - self._w
            )
        return NotImplemented

    def __mul__(
        self, other: Union["Vector4", float, int, "Matrix"]
    ) -> Union["Vector4", Any]:
        from .matrix import (
            Matrix,
        )  # runtime import inside method to avoid circular import

        if isinstance(other, Number):
            return Vector4(
                self._x * other, self._y * other, self._z * other, self._w * other
            )
        elif isinstance(other, Vector4):
            return Vector4(
                self._x * other.x,
                self._y * other.y,
                self._z * other.z,
                self._w * other.w,
            )
        elif isinstance(other, Matrix):
            if other.cols != 4:
                raise ValueError(
                    f"Cannot multiply Vector4 with Matrix({other.rows}×{other.cols})"
                )
            result = [0.0] * other.rows
            for i in range(other.rows):
                for j in range(other.cols):
                    if j == 0:
                        result[i] += self._x * other.data[i][j]
                    elif j == 1:
                        result[i] += self._y * other.data[i][j]
                    elif j == 2:
                        result[i] += self._z * other.data[i][j]
                    else:
                        result[i] += self._w * other.data[i][j]
            if len(result) == 4:
                return Vector4(result[0], result[1], result[2], result[3])
            return result
        return NotImplemented

    def __rmul__(self, other: Number) -> "Vector4":
        if isinstance(other, Number):
            return Vector4(
                self._x * other, self._y * other, self._z * other, self._w * other
            )
        return NotImplemented

    def __truediv__(self, other: Union["Vector4", Number]) -> "Vector4":
        if isinstance(other, Number):
            return Vector4(
                self._x / other, self._y / other, self._z / other, self._w / other
            )
        elif isinstance(other, Vector4):
            return Vector4(
                self._x / other.x,
                self._y / other.y,
                self._z / other.z,
                self._w / other.w,
            )
        return NotImplemented

    def __rtruediv__(self, other: Number) -> "Vector4":
        if isinstance(other, Number):
            return Vector4(
                other / self._x, other / self._y, other / self._z, other / self._w
            )
        return NotImplemented

    def __floordiv__(self, other: Union["Vector4", Number]) -> "Vector4":
        if isinstance(other, Number):
            return Vector4(
                self._x // other, self._y // other, self._z // other, self._w // other
            )
        elif isinstance(other, Vector4):
            return Vector4(
                self._x // other.x,
                self._y // other.y,
                self._z // other.z,
                self._w // other.w,
            )
        return NotImplemented

    def __rfloordiv__(self, other: Number) -> "Vector4":
        if isinstance(other, Number):
            return Vector4(
                other // self._x, other // self._y, other // self._z, other // self._w
            )
        return NotImplemented

    def __mod__(self, other: Union["Vector4", Number]) -> "Vector4":
        if isinstance(other, Number):
            return Vector4(
                self._x % other, self._y % other, self._z % other, self._w % other
            )
        elif isinstance(other, Vector4):
            return Vector4(
                self._x % other.x,
                self._y % other.y,
                self._z % other.z,
                self._w % other.w,
            )
        return NotImplemented

    def __rmod__(self, other: Number) -> "Vector4":
        if isinstance(other, Number):
            return Vector4(
                other % self._x, other % self._y, other % self._z, other % self._w
            )
        return NotImplemented

    def __pow__(self, other: Union["Vector4", Number]) -> "Vector4":
        if isinstance(other, Number):
            return Vector4(
                self._x**other, self._y**other, self._z**other, self._w**other
            )
        elif isinstance(other, Vector4):
            return Vector4(
                self._x**other.x, self._y**other.y, self._z**other.z, self._w**other.w
            )
        return NotImplemented

    def __rpow__(self, other: Number) -> "Vector4":
        if isinstance(other, Number):
            return Vector4(
                other**self._x, other**self._y, other**self._z, other**self._w
            )
        return NotImplemented

    # In-place operations
    def __iadd__(self, other: Union["Vector4", Number]) -> "Vector4":
        if isinstance(other, Vector4):
            self._x += other.x
            self._y += other.y
            self._z += other.z
            self._w += other.w
        elif isinstance(other, Number):
            self._x += other
            self._y += other
            self._z += other
            self._w += other
        else:
            return NotImplemented
        return self

    def __isub__(self, other: Union["Vector4", Number]) -> "Vector4":
        if isinstance(other, Vector4):
            self._x -= other.x
            self._y -= other.y
            self._z -= other.z
            self._w -= other.w
        elif isinstance(other, Number):
            self._x -= other
            self._y -= other
            self._z -= other
            self._w -= other
        else:
            return NotImplemented
        return self

    def __imul__(self, other: Union["Vector4", Number]) -> "Vector4":
        if isinstance(other, Number):
            self._x *= other
            self._y *= other
            self._z *= other
            self._w *= other
        elif isinstance(other, Vector4):
            self._x *= other.x
            self._y *= other.y
            self._z *= other.z
            self._w *= other.w
        else:
            return NotImplemented
        return self

    def __itruediv__(self, other: Union["Vector4", Number]) -> "Vector4":
        if isinstance(other, Number):
            self._x /= other
            self._y /= other
            self._z /= other
            self._w /= other
        elif isinstance(other, Vector4):
            self._x /= other.x
            self._y /= other.y
            self._z /= other.z
            self._w /= other.w
        else:
            return NotImplemented
        return self

    def __ifloordiv__(self, other: Union["Vector4", Number]) -> "Vector4":
        if isinstance(other, Number):
            self._x //= other
            self._y //= other
            self._z //= other
            self._w //= other
        elif isinstance(other, Vector4):
            self._x //= other.x
            self._y //= other.y
            self._z //= other.z
            self._w //= other.w
        else:
            return NotImplemented
        return self

    def __imod__(self, other: Union["Vector4", Number]) -> "Vector4":
        if isinstance(other, Number):
            self._x %= other
            self._y %= other
            self._z %= other
            self._w %= other
        elif isinstance(other, Vector4):
            self._x %= other.x
            self._y %= other.y
            self._z %= other.z
            self._w %= other.w
        else:
            return NotImplemented
        return self

    def __ipow__(self, other: Union["Vector4", Number]) -> "Vector4":
        if isinstance(other, Number):
            self._x **= other
            self._y **= other
            self._z **= other
            self._w **= other
        elif isinstance(other, Vector4):
            self._x **= other.x
            self._y **= other.y
            self._z **= other.z
            self._w **= other.w
        else:
            return NotImplemented
        return self

    # Comparison
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Vector4):
            return (
                self._x == other.x
                and self._y == other.y
                and self._z == other.z
                and self._w == other.w
            )
        return NotImplemented

    def __lt__(self, other: Union["Vector4", Number]) -> bool:
        if isinstance(other, Vector4):
            return (
                self._x < other.x
                and self._y < other.y
                and self._z < other.z
                and self._w < other.w
            )
        elif isinstance(other, Number):
            return (
                self._x < other
                and self._y < other
                and self._z < other
                and self._w < other
            )
        return NotImplemented

    def __gt__(self, other: Union["Vector4", Number]) -> bool:
        if isinstance(other, Vector4):
            return (
                self._x > other.x
                and self._y > other.y
                and self._z > other.z
                and self._w > other.w
            )
        elif isinstance(other, Number):
            return (
                self._x > other
                and self._y > other
                and self._z > other
                and self._w > other
            )
        return NotImplemented

    def __le__(self, other: Union["Vector4", Number]) -> bool:
        if isinstance(other, Vector4):
            return (
                self._x <= other.x
                and self._y <= other.y
                and self._z <= other.z
                and self._w <= other.w
            )
        elif isinstance(other, Number):
            return (
                self._x <= other
                and self._y <= other
                and self._z <= other
                and self._w <= other
            )
        return NotImplemented

    def __ge__(self, other: Union["Vector4", Number]) -> bool:
        if isinstance(other, Vector4):
            return (
                self._x >= other.x
                and self._y >= other.y
                and self._z >= other.z
                and self._w >= other.w
            )
        elif isinstance(other, Number):
            return (
                self._x >= other
                and self._y >= other
                and self._z >= other
                and self._w >= other
            )
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self._x, self._y, self._z, self._w))


class IVector4(Vector4):
    """Integer Vector3 implementation"""

    @classmethod
    def _vector_type(cls) -> Type:
        return int

    def __init__(self, *args):
        self._x: int
        self._y: int
        self._z: int
        self._w: int

        # Flatten all arguments into a list of scalars
        flattened = []
        for arg in args:
            if isinstance(arg, (Vector, Iterable)) and not isinstance(
                arg, (str, bytes)
            ):
                flattened.extend(arg)
            elif isinstance(arg, Number):
                flattened.append(arg)
            else:
                raise TypeError(f"Invalid argument type for IVector4: {type(arg)}")

        if len(flattened) == 0:
            self._x = self._y = self._z = self._w = self._vector_type()(0)
        elif len(flattened) == 1:
            self._x = self._y = self._z = self._w = self._vector_type()(flattened[0])
        elif len(flattened) >= 4:
            self._x, self._y, self._z, self._w = map(self._vector_type(), flattened[:4])
        else:
            raise TypeError("Invalid arguments for IVector4")


# Provide convenient aliases
Vec2 = Vector2
vec2 = Vector2
Vec3 = Vector3
vec3 = Vector3
Vec4 = Vector4
vec4 = Vector4

IVec2 = IVector2
ivec2 = IVector2
IVec3 = IVector3
ivec3 = IVector3
IVec4 = IVector4
ivec4 = IVector4
