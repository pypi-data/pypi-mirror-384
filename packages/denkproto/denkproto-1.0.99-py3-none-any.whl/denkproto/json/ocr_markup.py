from typing import Optional, Any, List, TypeVar, Callable, Type, cast
from uuid import UUID


T = TypeVar("T")


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def to_float(x: Any) -> float:
    assert isinstance(x, (int, float))
    return x


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


class BoundingBox:
    """A bounding box with optional rotation information"""

    angle: Optional[float]
    """Optional rotation angle"""

    bottom_right_x: float
    bottom_right_y: float
    full_orientation: Optional[bool]
    """Optional full orientation flag"""

    top_left_x: float
    top_left_y: float

    def __init__(self, angle: Optional[float], bottom_right_x: float, bottom_right_y: float, full_orientation: Optional[bool], top_left_x: float, top_left_y: float) -> None:
        self.angle = angle
        self.bottom_right_x = bottom_right_x
        self.bottom_right_y = bottom_right_y
        self.full_orientation = full_orientation
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y

    @staticmethod
    def from_dict(obj: Any) -> 'BoundingBox':
        assert isinstance(obj, dict)
        angle = from_union([from_float, from_none], obj.get("angle"))
        bottom_right_x = from_float(obj.get("bottom_right_x"))
        bottom_right_y = from_float(obj.get("bottom_right_y"))
        full_orientation = from_union([from_bool, from_none], obj.get("full_orientation"))
        top_left_x = from_float(obj.get("top_left_x"))
        top_left_y = from_float(obj.get("top_left_y"))
        return BoundingBox(angle, bottom_right_x, bottom_right_y, full_orientation, top_left_x, top_left_y)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.angle is not None:
            result["angle"] = from_union([to_float, from_none], self.angle)
        result["bottom_right_x"] = to_float(self.bottom_right_x)
        result["bottom_right_y"] = to_float(self.bottom_right_y)
        if self.full_orientation is not None:
            result["full_orientation"] = from_union([from_bool, from_none], self.full_orientation)
        result["top_left_x"] = to_float(self.top_left_x)
        result["top_left_y"] = to_float(self.top_left_y)
        return result


class Point:
    x: float
    y: float

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    @staticmethod
    def from_dict(obj: Any) -> 'Point':
        assert isinstance(obj, dict)
        x = from_float(obj.get("x"))
        y = from_float(obj.get("y"))
        return Point(x, y)

    def to_dict(self) -> dict:
        result: dict = {}
        result["x"] = to_float(self.x)
        result["y"] = to_float(self.y)
        return result


class GeometrySchema:
    """A single closed loop (ring) of a polygon, defining either an outer boundary or a hole."""

    hierarchy: int
    """Nesting level: 0=outer, 1=hole in level 0, 2=poly in level 1 hole, etc. Even levels are
    filled areas, odd levels are holes.
    """
    points: List[Point]
    """Vertices of the ring."""

    def __init__(self, hierarchy: int, points: List[Point]) -> None:
        self.hierarchy = hierarchy
        self.points = points

    @staticmethod
    def from_dict(obj: Any) -> 'GeometrySchema':
        assert isinstance(obj, dict)
        hierarchy = from_int(obj.get("hierarchy"))
        points = from_list(Point.from_dict, obj.get("points"))
        return GeometrySchema(hierarchy, points)

    def to_dict(self) -> dict:
        result: dict = {}
        result["hierarchy"] = from_int(self.hierarchy)
        result["points"] = from_list(lambda x: to_class(Point, x), self.points)
        return result


class Polygon:
    """A polygon defined by one or more rings, allowing for holes and nested structures."""

    rings: List[GeometrySchema]
    """Array of polygon rings. The hierarchy field within each ring determines nesting and
    fill/hole status.
    """

    def __init__(self, rings: List[GeometrySchema]) -> None:
        self.rings = rings

    @staticmethod
    def from_dict(obj: Any) -> 'Polygon':
        assert isinstance(obj, dict)
        rings = from_list(GeometrySchema.from_dict, obj.get("rings"))
        return Polygon(rings)

    def to_dict(self) -> dict:
        result: dict = {}
        result["rings"] = from_list(lambda x: to_class(GeometrySchema, x), self.rings)
        return result


class Annotation:
    bounding_box: Optional[BoundingBox]
    id: UUID
    label_id: UUID
    polygon: Optional[Polygon]
    text: str

    def __init__(self, bounding_box: Optional[BoundingBox], id: UUID, label_id: UUID, polygon: Optional[Polygon], text: str) -> None:
        self.bounding_box = bounding_box
        self.id = id
        self.label_id = label_id
        self.polygon = polygon
        self.text = text

    @staticmethod
    def from_dict(obj: Any) -> 'Annotation':
        assert isinstance(obj, dict)
        bounding_box = from_union([BoundingBox.from_dict, from_none], obj.get("bounding_box"))
        id = UUID(obj.get("id"))
        label_id = UUID(obj.get("label_id"))
        polygon = from_union([Polygon.from_dict, from_none], obj.get("polygon"))
        text = from_str(obj.get("text"))
        return Annotation(bounding_box, id, label_id, polygon, text)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.bounding_box is not None:
            result["bounding_box"] = from_union([lambda x: to_class(BoundingBox, x), from_none], self.bounding_box)
        result["id"] = str(self.id)
        result["label_id"] = str(self.label_id)
        if self.polygon is not None:
            result["polygon"] = from_union([lambda x: to_class(Polygon, x), from_none], self.polygon)
        result["text"] = from_str(self.text)
        return result


class OcrMarkup:
    annotations: List[Annotation]
    average_object_widths: List[float]
    height: int
    width: int

    def __init__(self, annotations: List[Annotation], average_object_widths: List[float], height: int, width: int) -> None:
        self.annotations = annotations
        self.average_object_widths = average_object_widths
        self.height = height
        self.width = width

    @staticmethod
    def from_dict(obj: Any) -> 'OcrMarkup':
        assert isinstance(obj, dict)
        annotations = from_list(Annotation.from_dict, obj.get("annotations"))
        average_object_widths = from_list(from_float, obj.get("average_object_widths"))
        height = from_int(obj.get("height"))
        width = from_int(obj.get("width"))
        return OcrMarkup(annotations, average_object_widths, height, width)

    def to_dict(self) -> dict:
        result: dict = {}
        result["annotations"] = from_list(lambda x: to_class(Annotation, x), self.annotations)
        result["average_object_widths"] = from_list(to_float, self.average_object_widths)
        result["height"] = from_int(self.height)
        result["width"] = from_int(self.width)
        return result


def ocr_markup_from_dict(s: Any) -> OcrMarkup:
    return OcrMarkup.from_dict(s)


def ocr_markup_to_dict(x: OcrMarkup) -> Any:
    return to_class(OcrMarkup, x)
