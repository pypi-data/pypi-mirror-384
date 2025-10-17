"""
Type definitions for image generation data structures.
"""

from typing import Optional, List, Union
from pydantic import BaseModel, Field


class CircleSize(BaseModel):
    radius: Optional[float] = None
    diameter: Optional[float] = None


class RectangleSize(BaseModel):
    width: float
    height: float


class SquareSize(BaseModel):
    side: Optional[float] = None
    diagonal: Optional[float] = None
    show_side_label: Optional[bool] = True
    show_diagonal_label: Optional[bool] = False


class TriangleSize(BaseModel):
    base_side: Optional[float] = None  # Bottom side of triangle
    left_side: Optional[float] = None  # Left side of triangle
    right_side: Optional[float] = None  # Right side of triangle
    
    angle_base_left: Optional[float] = None  # Angle at bottom-left vertex
    angle_left_right: Optional[float] = None  # Angle at top vertex (between left and right sides)
    angle_right_base: Optional[float] = None  # Angle at bottom-right vertex
    
    triangle_type: Optional[str] = None  # 'equilateral', 'isosceles', 'right'
    height: Optional[float] = None
    
    show_base_label: Optional[bool] = True
    show_left_label: Optional[bool] = True
    show_right_label: Optional[bool] = True
    show_height_label: Optional[bool] = False


class EllipseSize(BaseModel):
    width: float
    height: float
    angle: Optional[float] = 0


class PolygonSize(BaseModel):
    radius: float
    sides: int
    rotation: Optional[float] = 0


class Shape2D(BaseModel):
    type: str = Field(..., description="Shape type: circle, rectangle, square, triangle, ellipse, polygon")
    center: List[float] = Field(default=[0.0, 0.0], description="Center coordinates [x, y]")
    color: str = Field(default="blue", description="Fill color")
    label: Optional[str] = Field(default="", description="Optional label text")
    units: Optional[str] = Field(default="cm", description="Measurement units")
    
    # Size can be different types based on shape
    size: Union[CircleSize, RectangleSize, SquareSize, TriangleSize, EllipseSize, PolygonSize, float, List[float]]


# 3D Shape models
class CubeDimensions(BaseModel):
    side: Optional[float] = None
    volume: Optional[float] = None
    show_side: Optional[bool] = True
    show_volume: Optional[bool] = False

class CuboidDimensions(BaseModel):
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    show_length: Optional[bool] = True
    show_width: Optional[bool] = True
    show_height: Optional[bool] = True

class SphereDimensions(BaseModel):
    radius: Optional[float] = None

class CylinderDimensions(BaseModel):
    radius: Optional[float] = None
    height: Optional[float] = None

class ConeDimensions(BaseModel):
    radius: Optional[float] = None
    height: Optional[float] = None
    slant_height: Optional[float] = None

class PyramidDimensions(BaseModel):
    base_side: Optional[float] = None
    base_area: Optional[float] = None
    height: Optional[float] = None
    slant_height: Optional[float] = None

class TriangularPrismDimensions(BaseModel):
    base_side: Optional[float] = None
    height: Optional[float] = None
    base_area: Optional[float] = None

class Shape3DData(BaseModel):
    shape_type: str = Field(..., description="Shape type: cube, cuboid, sphere, cylinder, cone, pyramid, triangular_prism")
    dimensions: Union[CubeDimensions, CuboidDimensions, SphereDimensions, CylinderDimensions, ConeDimensions, PyramidDimensions, TriangularPrismDimensions]
    title: Optional[str] = Field(default=None, description="Optional title for the image")
    show_labels: bool = Field(default=True, description="Whether to show dimension labels")
    color: str = Field(default="lightblue", description="Shape color")
    units: Optional[str] = Field(default=None, description="Measurement units")

class Shapes2DData(BaseModel):
    shapes: List[Shape2D] = Field(..., description="List of 2D shapes to generate")
    title: Optional[str] = Field(default=None, description="Optional title for the image")
    show_measurements: bool = Field(default=True, description="Whether to show dimension measurements")
    show_labels: bool = Field(default=False, description="Whether to show shape labels")