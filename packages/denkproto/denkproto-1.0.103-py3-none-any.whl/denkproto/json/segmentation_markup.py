from enum import Enum
from typing import Any, List, Optional, TypeVar, Callable, Type, cast
from uuid import UUID


T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def to_float(x: Any) -> float:
    assert isinstance(x, (int, float))
    return x


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


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


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


class AnnotationType(Enum):
    IGNORE = "IGNORE"
    NEGATIVE = "NEGATIVE"
    POSITIVE = "POSITIVE"
    ROI = "ROI"


class CircleAnnotation:
    center_x: float
    center_y: float
    radius: float

    def __init__(self, center_x: float, center_y: float, radius: float) -> None:
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius

    @staticmethod
    def from_dict(obj: Any) -> 'CircleAnnotation':
        assert isinstance(obj, dict)
        center_x = from_float(obj.get("center_x"))
        center_y = from_float(obj.get("center_y"))
        radius = from_float(obj.get("radius"))
        return CircleAnnotation(center_x, center_y, radius)

    def to_dict(self) -> dict:
        result: dict = {}
        result["center_x"] = to_float(self.center_x)
        result["center_y"] = to_float(self.center_y)
        result["radius"] = to_float(self.radius)
        return result


class MagicwandAnnotationPoint:
    x: float
    y: float

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    @staticmethod
    def from_dict(obj: Any) -> 'MagicwandAnnotationPoint':
        assert isinstance(obj, dict)
        x = from_float(obj.get("x"))
        y = from_float(obj.get("y"))
        return MagicwandAnnotationPoint(x, y)

    def to_dict(self) -> dict:
        result: dict = {}
        result["x"] = to_float(self.x)
        result["y"] = to_float(self.y)
        return result


class MagicwandAnnotation:
    bottom_right_x: float
    bottom_right_y: float
    center_x: float
    center_y: float
    data_url: str
    points: List[MagicwandAnnotationPoint]
    threshold: int
    top_left_x: float
    top_left_y: float

    def __init__(self, bottom_right_x: float, bottom_right_y: float, center_x: float, center_y: float, data_url: str, points: List[MagicwandAnnotationPoint], threshold: int, top_left_x: float, top_left_y: float) -> None:
        self.bottom_right_x = bottom_right_x
        self.bottom_right_y = bottom_right_y
        self.center_x = center_x
        self.center_y = center_y
        self.data_url = data_url
        self.points = points
        self.threshold = threshold
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y

    @staticmethod
    def from_dict(obj: Any) -> 'MagicwandAnnotation':
        assert isinstance(obj, dict)
        bottom_right_x = from_float(obj.get("bottom_right_x"))
        bottom_right_y = from_float(obj.get("bottom_right_y"))
        center_x = from_float(obj.get("center_x"))
        center_y = from_float(obj.get("center_y"))
        data_url = from_str(obj.get("dataURL"))
        points = from_list(MagicwandAnnotationPoint.from_dict, obj.get("points"))
        threshold = from_int(obj.get("threshold"))
        top_left_x = from_float(obj.get("top_left_x"))
        top_left_y = from_float(obj.get("top_left_y"))
        return MagicwandAnnotation(bottom_right_x, bottom_right_y, center_x, center_y, data_url, points, threshold, top_left_x, top_left_y)

    def to_dict(self) -> dict:
        result: dict = {}
        result["bottom_right_x"] = to_float(self.bottom_right_x)
        result["bottom_right_y"] = to_float(self.bottom_right_y)
        result["center_x"] = to_float(self.center_x)
        result["center_y"] = to_float(self.center_y)
        result["dataURL"] = from_str(self.data_url)
        result["points"] = from_list(lambda x: to_class(MagicwandAnnotationPoint, x), self.points)
        result["threshold"] = from_int(self.threshold)
        result["top_left_x"] = to_float(self.top_left_x)
        result["top_left_y"] = to_float(self.top_left_y)
        return result


class PenAnnotationPoint:
    x: float
    y: float

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    @staticmethod
    def from_dict(obj: Any) -> 'PenAnnotationPoint':
        assert isinstance(obj, dict)
        x = from_float(obj.get("x"))
        y = from_float(obj.get("y"))
        return PenAnnotationPoint(x, y)

    def to_dict(self) -> dict:
        result: dict = {}
        result["x"] = to_float(self.x)
        result["y"] = to_float(self.y)
        return result


class PenAnnotation:
    bottom_right_x: float
    bottom_right_y: float
    data_url: str
    points: List[PenAnnotationPoint]
    thickness: float
    top_left_x: float
    top_left_y: float

    def __init__(self, bottom_right_x: float, bottom_right_y: float, data_url: str, points: List[PenAnnotationPoint], thickness: float, top_left_x: float, top_left_y: float) -> None:
        self.bottom_right_x = bottom_right_x
        self.bottom_right_y = bottom_right_y
        self.data_url = data_url
        self.points = points
        self.thickness = thickness
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y

    @staticmethod
    def from_dict(obj: Any) -> 'PenAnnotation':
        assert isinstance(obj, dict)
        bottom_right_x = from_float(obj.get("bottom_right_x"))
        bottom_right_y = from_float(obj.get("bottom_right_y"))
        data_url = from_str(obj.get("dataURL"))
        points = from_list(PenAnnotationPoint.from_dict, obj.get("points"))
        thickness = from_float(obj.get("thickness"))
        top_left_x = from_float(obj.get("top_left_x"))
        top_left_y = from_float(obj.get("top_left_y"))
        return PenAnnotation(bottom_right_x, bottom_right_y, data_url, points, thickness, top_left_x, top_left_y)

    def to_dict(self) -> dict:
        result: dict = {}
        result["bottom_right_x"] = to_float(self.bottom_right_x)
        result["bottom_right_y"] = to_float(self.bottom_right_y)
        result["dataURL"] = from_str(self.data_url)
        result["points"] = from_list(lambda x: to_class(PenAnnotationPoint, x), self.points)
        result["thickness"] = to_float(self.thickness)
        result["top_left_x"] = to_float(self.top_left_x)
        result["top_left_y"] = to_float(self.top_left_y)
        return result


class PixelAnnotation:
    blob_id: UUID
    bottom_right_x: float
    bottom_right_y: float
    top_left_x: float
    top_left_y: float

    def __init__(self, blob_id: UUID, bottom_right_x: float, bottom_right_y: float, top_left_x: float, top_left_y: float) -> None:
        self.blob_id = blob_id
        self.bottom_right_x = bottom_right_x
        self.bottom_right_y = bottom_right_y
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y

    @staticmethod
    def from_dict(obj: Any) -> 'PixelAnnotation':
        assert isinstance(obj, dict)
        blob_id = UUID(obj.get("blob_id"))
        bottom_right_x = from_float(obj.get("bottom_right_x"))
        bottom_right_y = from_float(obj.get("bottom_right_y"))
        top_left_x = from_float(obj.get("top_left_x"))
        top_left_y = from_float(obj.get("top_left_y"))
        return PixelAnnotation(blob_id, bottom_right_x, bottom_right_y, top_left_x, top_left_y)

    def to_dict(self) -> dict:
        result: dict = {}
        result["blob_id"] = str(self.blob_id)
        result["bottom_right_x"] = to_float(self.bottom_right_x)
        result["bottom_right_y"] = to_float(self.bottom_right_y)
        result["top_left_x"] = to_float(self.top_left_x)
        result["top_left_y"] = to_float(self.top_left_y)
        return result


class RingPoint:
    x: float
    y: float

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    @staticmethod
    def from_dict(obj: Any) -> 'RingPoint':
        assert isinstance(obj, dict)
        x = from_float(obj.get("x"))
        y = from_float(obj.get("y"))
        return RingPoint(x, y)

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
    points: List[RingPoint]
    """Vertices of the ring."""

    def __init__(self, hierarchy: int, points: List[RingPoint]) -> None:
        self.hierarchy = hierarchy
        self.points = points

    @staticmethod
    def from_dict(obj: Any) -> 'GeometrySchema':
        assert isinstance(obj, dict)
        hierarchy = from_int(obj.get("hierarchy"))
        points = from_list(RingPoint.from_dict, obj.get("points"))
        return GeometrySchema(hierarchy, points)

    def to_dict(self) -> dict:
        result: dict = {}
        result["hierarchy"] = from_int(self.hierarchy)
        result["points"] = from_list(lambda x: to_class(RingPoint, x), self.points)
        return result


class PolygonAnnotation:
    """A polygon defined by one or more rings, allowing for holes and nested structures."""

    rings: List[GeometrySchema]
    """Array of polygon rings. The hierarchy field within each ring determines nesting and
    fill/hole status.
    """

    def __init__(self, rings: List[GeometrySchema]) -> None:
        self.rings = rings

    @staticmethod
    def from_dict(obj: Any) -> 'PolygonAnnotation':
        assert isinstance(obj, dict)
        rings = from_list(GeometrySchema.from_dict, obj.get("rings"))
        return PolygonAnnotation(rings)

    def to_dict(self) -> dict:
        result: dict = {}
        result["rings"] = from_list(lambda x: to_class(GeometrySchema, x), self.rings)
        return result


class RectangleAnnotation:
    bottom_right_x: float
    bottom_right_y: float
    top_left_x: float
    top_left_y: float

    def __init__(self, bottom_right_x: float, bottom_right_y: float, top_left_x: float, top_left_y: float) -> None:
        self.bottom_right_x = bottom_right_x
        self.bottom_right_y = bottom_right_y
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y

    @staticmethod
    def from_dict(obj: Any) -> 'RectangleAnnotation':
        assert isinstance(obj, dict)
        bottom_right_x = from_float(obj.get("bottom_right_x"))
        bottom_right_y = from_float(obj.get("bottom_right_y"))
        top_left_x = from_float(obj.get("top_left_x"))
        top_left_y = from_float(obj.get("top_left_y"))
        return RectangleAnnotation(bottom_right_x, bottom_right_y, top_left_x, top_left_y)

    def to_dict(self) -> dict:
        result: dict = {}
        result["bottom_right_x"] = to_float(self.bottom_right_x)
        result["bottom_right_y"] = to_float(self.bottom_right_y)
        result["top_left_x"] = to_float(self.top_left_x)
        result["top_left_y"] = to_float(self.top_left_y)
        return result


class SausageAnnotationPoint:
    x: float
    y: float

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    @staticmethod
    def from_dict(obj: Any) -> 'SausageAnnotationPoint':
        assert isinstance(obj, dict)
        x = from_float(obj.get("x"))
        y = from_float(obj.get("y"))
        return SausageAnnotationPoint(x, y)

    def to_dict(self) -> dict:
        result: dict = {}
        result["x"] = to_float(self.x)
        result["y"] = to_float(self.y)
        return result


class SausageAnnotation:
    bottom_right_x: float
    bottom_right_y: float
    data_url: str
    points: List[SausageAnnotationPoint]
    radius: float
    top_left_x: float
    top_left_y: float

    def __init__(self, bottom_right_x: float, bottom_right_y: float, data_url: str, points: List[SausageAnnotationPoint], radius: float, top_left_x: float, top_left_y: float) -> None:
        self.bottom_right_x = bottom_right_x
        self.bottom_right_y = bottom_right_y
        self.data_url = data_url
        self.points = points
        self.radius = radius
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y

    @staticmethod
    def from_dict(obj: Any) -> 'SausageAnnotation':
        assert isinstance(obj, dict)
        bottom_right_x = from_float(obj.get("bottom_right_x"))
        bottom_right_y = from_float(obj.get("bottom_right_y"))
        data_url = from_str(obj.get("dataURL"))
        points = from_list(SausageAnnotationPoint.from_dict, obj.get("points"))
        radius = from_float(obj.get("radius"))
        top_left_x = from_float(obj.get("top_left_x"))
        top_left_y = from_float(obj.get("top_left_y"))
        return SausageAnnotation(bottom_right_x, bottom_right_y, data_url, points, radius, top_left_x, top_left_y)

    def to_dict(self) -> dict:
        result: dict = {}
        result["bottom_right_x"] = to_float(self.bottom_right_x)
        result["bottom_right_y"] = to_float(self.bottom_right_y)
        result["dataURL"] = from_str(self.data_url)
        result["points"] = from_list(lambda x: to_class(SausageAnnotationPoint, x), self.points)
        result["radius"] = to_float(self.radius)
        result["top_left_x"] = to_float(self.top_left_x)
        result["top_left_y"] = to_float(self.top_left_y)
        return result


class Annotation:
    annotation_type: AnnotationType
    average_width: float
    circle_annotation: Optional[CircleAnnotation]
    id: UUID
    label_id: UUID
    magicwand_annotation: Optional[MagicwandAnnotation]
    pen_annotation: Optional[PenAnnotation]
    pixel_annotation: Optional[PixelAnnotation]
    polygon_annotation: Optional[PolygonAnnotation]
    rectangle_annotation: Optional[RectangleAnnotation]
    sausage_annotation: Optional[SausageAnnotation]

    def __init__(self, annotation_type: AnnotationType, average_width: float, circle_annotation: Optional[CircleAnnotation], id: UUID, label_id: UUID, magicwand_annotation: Optional[MagicwandAnnotation], pen_annotation: Optional[PenAnnotation], pixel_annotation: Optional[PixelAnnotation], polygon_annotation: Optional[PolygonAnnotation], rectangle_annotation: Optional[RectangleAnnotation], sausage_annotation: Optional[SausageAnnotation]) -> None:
        self.annotation_type = annotation_type
        self.average_width = average_width
        self.circle_annotation = circle_annotation
        self.id = id
        self.label_id = label_id
        self.magicwand_annotation = magicwand_annotation
        self.pen_annotation = pen_annotation
        self.pixel_annotation = pixel_annotation
        self.polygon_annotation = polygon_annotation
        self.rectangle_annotation = rectangle_annotation
        self.sausage_annotation = sausage_annotation

    @staticmethod
    def from_dict(obj: Any) -> 'Annotation':
        assert isinstance(obj, dict)
        annotation_type = AnnotationType(obj.get("annotation_type"))
        average_width = from_float(obj.get("average_width"))
        circle_annotation = from_union([CircleAnnotation.from_dict, from_none], obj.get("circle_annotation"))
        id = UUID(obj.get("id"))
        label_id = UUID(obj.get("label_id"))
        magicwand_annotation = from_union([MagicwandAnnotation.from_dict, from_none], obj.get("magicwand_annotation"))
        pen_annotation = from_union([PenAnnotation.from_dict, from_none], obj.get("pen_annotation"))
        pixel_annotation = from_union([PixelAnnotation.from_dict, from_none], obj.get("pixel_annotation"))
        polygon_annotation = from_union([PolygonAnnotation.from_dict, from_none], obj.get("polygon_annotation"))
        rectangle_annotation = from_union([RectangleAnnotation.from_dict, from_none], obj.get("rectangle_annotation"))
        sausage_annotation = from_union([SausageAnnotation.from_dict, from_none], obj.get("sausage_annotation"))
        return Annotation(annotation_type, average_width, circle_annotation, id, label_id, magicwand_annotation, pen_annotation, pixel_annotation, polygon_annotation, rectangle_annotation, sausage_annotation)

    def to_dict(self) -> dict:
        result: dict = {}
        result["annotation_type"] = to_enum(AnnotationType, self.annotation_type)
        result["average_width"] = to_float(self.average_width)
        if self.circle_annotation is not None:
            result["circle_annotation"] = from_union([lambda x: to_class(CircleAnnotation, x), from_none], self.circle_annotation)
        result["id"] = str(self.id)
        result["label_id"] = str(self.label_id)
        if self.magicwand_annotation is not None:
            result["magicwand_annotation"] = from_union([lambda x: to_class(MagicwandAnnotation, x), from_none], self.magicwand_annotation)
        if self.pen_annotation is not None:
            result["pen_annotation"] = from_union([lambda x: to_class(PenAnnotation, x), from_none], self.pen_annotation)
        if self.pixel_annotation is not None:
            result["pixel_annotation"] = from_union([lambda x: to_class(PixelAnnotation, x), from_none], self.pixel_annotation)
        if self.polygon_annotation is not None:
            result["polygon_annotation"] = from_union([lambda x: to_class(PolygonAnnotation, x), from_none], self.polygon_annotation)
        if self.rectangle_annotation is not None:
            result["rectangle_annotation"] = from_union([lambda x: to_class(RectangleAnnotation, x), from_none], self.rectangle_annotation)
        if self.sausage_annotation is not None:
            result["sausage_annotation"] = from_union([lambda x: to_class(SausageAnnotation, x), from_none], self.sausage_annotation)
        return result


class SegmentationMarkup:
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
    def from_dict(obj: Any) -> 'SegmentationMarkup':
        assert isinstance(obj, dict)
        annotations = from_list(Annotation.from_dict, obj.get("annotations"))
        average_object_widths = from_list(from_float, obj.get("average_object_widths"))
        height = from_int(obj.get("height"))
        width = from_int(obj.get("width"))
        return SegmentationMarkup(annotations, average_object_widths, height, width)

    def to_dict(self) -> dict:
        result: dict = {}
        result["annotations"] = from_list(lambda x: to_class(Annotation, x), self.annotations)
        result["average_object_widths"] = from_list(to_float, self.average_object_widths)
        result["height"] = from_int(self.height)
        result["width"] = from_int(self.width)
        return result


def segmentation_markup_from_dict(s: Any) -> SegmentationMarkup:
    return SegmentationMarkup.from_dict(s)


def segmentation_markup_to_dict(x: SegmentationMarkup) -> Any:
    return to_class(SegmentationMarkup, x)
