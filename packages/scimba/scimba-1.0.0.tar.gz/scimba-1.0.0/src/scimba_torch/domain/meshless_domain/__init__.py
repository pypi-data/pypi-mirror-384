"""Meshless domains."""

from .domain_1d import Point1D, Segment1D
from .domain_2d import ArcCircle2D, Circle2D, Disk2D, Polygon2D, Segment2D, Square2D
from .domain_3d import (
    Cube3D,
    Cylinder3D,
    Disk3D,
    Sphere3D,
    Square3D,
    SurfaceTorus3D,
    Torus3D,
    TorusFrom2DVolume,
)
from .domain_nd import HypercubeND

__all__ = [
    "Segment1D",
    "Point1D",
    "ArcCircle2D",
    "Circle2D",
    "Disk2D",
    "Polygon2D",
    "Segment2D",
    "Square2D",
    "Cube3D",
    "Cylinder3D",
    "Disk3D",
    "Sphere3D",
    "Square3D",
    "SurfaceTorus3D",
    "Torus3D",
    "TorusFrom2DVolume",
    "HypercubeND",
]
