from collections.abc import Iterator

from pydantic import BaseModel


class Vec3(BaseModel):
    x: float
    y: float
    z: float

    def __iter__(self) -> Iterator[float]:  # type: ignore[IncompatibleMethodOverride]
        yield self.x
        yield self.y
        yield self.z

    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self.x
        if index == 1:
            return self.y
        if index == 2:
            return self.z
        raise IndexError("Index out of range for Vec3, valid indices are 0, 1, 2.")


class Quat(BaseModel):
    w: float
    x: float
    y: float
    z: float

    def __iter__(self) -> Iterator[float]:  # type: ignore[IncompatibleMethodOverride]
        yield self.w
        yield self.x
        yield self.y
        yield self.z

    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self.w
        if index == 1:
            return self.x
        if index == 2:
            return self.y
        if index == 3:
            return self.z
        raise IndexError("Index out of range for Quat, valid indices are 0, 1, 2, 3.")
