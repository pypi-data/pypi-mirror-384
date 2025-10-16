from uuid import UUID
from typing import Any, List, Optional, TypeVar, Callable, Type, cast
from enum import Enum


T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def to_float(x: Any) -> float:
    assert isinstance(x, (int, float))
    return x


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


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


class Image:
    blob_id: UUID
    height: int
    owned_by_group_id: UUID
    width: int

    def __init__(self, blob_id: UUID, height: int, owned_by_group_id: UUID, width: int) -> None:
        self.blob_id = blob_id
        self.height = height
        self.owned_by_group_id = owned_by_group_id
        self.width = width

    @staticmethod
    def from_dict(obj: Any) -> 'Image':
        assert isinstance(obj, dict)
        blob_id = UUID(obj.get("blob_id"))
        height = from_int(obj.get("height"))
        owned_by_group_id = UUID(obj.get("owned_by_group_id"))
        width = from_int(obj.get("width"))
        return Image(blob_id, height, owned_by_group_id, width)

    def to_dict(self) -> dict:
        result: dict = {}
        result["blob_id"] = str(self.blob_id)
        result["height"] = from_int(self.height)
        result["owned_by_group_id"] = str(self.owned_by_group_id)
        result["width"] = from_int(self.width)
        return result


class ClassLabelElement:
    id: UUID
    idx: int

    def __init__(self, id: UUID, idx: int) -> None:
        self.id = id
        self.idx = idx

    @staticmethod
    def from_dict(obj: Any) -> 'ClassLabelElement':
        assert isinstance(obj, dict)
        id = UUID(obj.get("id"))
        idx = from_int(obj.get("idx"))
        return ClassLabelElement(id, idx)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = str(self.id)
        result["idx"] = from_int(self.idx)
        return result


class NetworkExperiment:
    class_labels: List[ClassLabelElement]
    flavor: str
    network_typename: str

    def __init__(self, class_labels: List[ClassLabelElement], flavor: str, network_typename: str) -> None:
        self.class_labels = class_labels
        self.flavor = flavor
        self.network_typename = network_typename

    @staticmethod
    def from_dict(obj: Any) -> 'NetworkExperiment':
        assert isinstance(obj, dict)
        class_labels = from_list(ClassLabelElement.from_dict, obj.get("class_labels"))
        flavor = from_str(obj.get("flavor"))
        network_typename = from_str(obj.get("network_typename"))
        return NetworkExperiment(class_labels, flavor, network_typename)

    def to_dict(self) -> dict:
        result: dict = {}
        result["class_labels"] = from_list(lambda x: to_class(ClassLabelElement, x), self.class_labels)
        result["flavor"] = from_str(self.flavor)
        result["network_typename"] = from_str(self.network_typename)
        return result


class ClassificationMarkupAnnotation:
    id: UUID
    label_id: UUID
    value: float

    def __init__(self, id: UUID, label_id: UUID, value: float) -> None:
        self.id = id
        self.label_id = label_id
        self.value = value

    @staticmethod
    def from_dict(obj: Any) -> 'ClassificationMarkupAnnotation':
        assert isinstance(obj, dict)
        id = UUID(obj.get("id"))
        label_id = UUID(obj.get("label_id"))
        value = from_float(obj.get("value"))
        return ClassificationMarkupAnnotation(id, label_id, value)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = str(self.id)
        result["label_id"] = str(self.label_id)
        result["value"] = to_float(self.value)
        return result


class ClassificationMarkup:
    annotations: List[ClassificationMarkupAnnotation]
    height: int
    width: int

    def __init__(self, annotations: List[ClassificationMarkupAnnotation], height: int, width: int) -> None:
        self.annotations = annotations
        self.height = height
        self.width = width

    @staticmethod
    def from_dict(obj: Any) -> 'ClassificationMarkup':
        assert isinstance(obj, dict)
        annotations = from_list(ClassificationMarkupAnnotation.from_dict, obj.get("annotations"))
        height = from_int(obj.get("height"))
        width = from_int(obj.get("width"))
        return ClassificationMarkup(annotations, height, width)

    def to_dict(self) -> dict:
        result: dict = {}
        result["annotations"] = from_list(lambda x: to_class(ClassificationMarkupAnnotation, x), self.annotations)
        result["height"] = from_int(self.height)
        result["width"] = from_int(self.width)
        return result


class AnnotationType(Enum):
    IGNORE = "IGNORE"
    NEGATIVE = "NEGATIVE"
    POSITIVE = "POSITIVE"
    ROI = "ROI"


class ObjectDetectionMarkupAnnotation:
    angle: Optional[float]
    annotation_type: AnnotationType
    average_width: float
    bottom_right_x: float
    bottom_right_y: float
    full_orientation: Optional[bool]
    id: UUID
    label_id: UUID
    top_left_x: float
    top_left_y: float

    def __init__(self, angle: Optional[float], annotation_type: AnnotationType, average_width: float, bottom_right_x: float, bottom_right_y: float, full_orientation: Optional[bool], id: UUID, label_id: UUID, top_left_x: float, top_left_y: float) -> None:
        self.angle = angle
        self.annotation_type = annotation_type
        self.average_width = average_width
        self.bottom_right_x = bottom_right_x
        self.bottom_right_y = bottom_right_y
        self.full_orientation = full_orientation
        self.id = id
        self.label_id = label_id
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y

    @staticmethod
    def from_dict(obj: Any) -> 'ObjectDetectionMarkupAnnotation':
        assert isinstance(obj, dict)
        angle = from_union([from_float, from_none], obj.get("angle"))
        annotation_type = AnnotationType(obj.get("annotation_type"))
        average_width = from_float(obj.get("average_width"))
        bottom_right_x = from_float(obj.get("bottom_right_x"))
        bottom_right_y = from_float(obj.get("bottom_right_y"))
        full_orientation = from_union([from_bool, from_none], obj.get("full_orientation"))
        id = UUID(obj.get("id"))
        label_id = UUID(obj.get("label_id"))
        top_left_x = from_float(obj.get("top_left_x"))
        top_left_y = from_float(obj.get("top_left_y"))
        return ObjectDetectionMarkupAnnotation(angle, annotation_type, average_width, bottom_right_x, bottom_right_y, full_orientation, id, label_id, top_left_x, top_left_y)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.angle is not None:
            result["angle"] = from_union([to_float, from_none], self.angle)
        result["annotation_type"] = to_enum(AnnotationType, self.annotation_type)
        result["average_width"] = to_float(self.average_width)
        result["bottom_right_x"] = to_float(self.bottom_right_x)
        result["bottom_right_y"] = to_float(self.bottom_right_y)
        if self.full_orientation is not None:
            result["full_orientation"] = from_union([from_bool, from_none], self.full_orientation)
        result["id"] = str(self.id)
        result["label_id"] = str(self.label_id)
        result["top_left_x"] = to_float(self.top_left_x)
        result["top_left_y"] = to_float(self.top_left_y)
        return result


class ObjectDetectionMarkup:
    annotations: List[ObjectDetectionMarkupAnnotation]
    height: int
    width: int

    def __init__(self, annotations: List[ObjectDetectionMarkupAnnotation], height: int, width: int) -> None:
        self.annotations = annotations
        self.height = height
        self.width = width

    @staticmethod
    def from_dict(obj: Any) -> 'ObjectDetectionMarkup':
        assert isinstance(obj, dict)
        annotations = from_list(ObjectDetectionMarkupAnnotation.from_dict, obj.get("annotations"))
        height = from_int(obj.get("height"))
        width = from_int(obj.get("width"))
        return ObjectDetectionMarkup(annotations, height, width)

    def to_dict(self) -> dict:
        result: dict = {}
        result["annotations"] = from_list(lambda x: to_class(ObjectDetectionMarkupAnnotation, x), self.annotations)
        result["height"] = from_int(self.height)
        result["width"] = from_int(self.width)
        return result


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


class OcrMarkupAnnotation:
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
    def from_dict(obj: Any) -> 'OcrMarkupAnnotation':
        assert isinstance(obj, dict)
        bounding_box = from_union([BoundingBox.from_dict, from_none], obj.get("bounding_box"))
        id = UUID(obj.get("id"))
        label_id = UUID(obj.get("label_id"))
        polygon = from_union([Polygon.from_dict, from_none], obj.get("polygon"))
        text = from_str(obj.get("text"))
        return OcrMarkupAnnotation(bounding_box, id, label_id, polygon, text)

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


class OCRMarkup:
    annotations: List[OcrMarkupAnnotation]
    average_object_widths: List[float]
    height: int
    width: int

    def __init__(self, annotations: List[OcrMarkupAnnotation], average_object_widths: List[float], height: int, width: int) -> None:
        self.annotations = annotations
        self.average_object_widths = average_object_widths
        self.height = height
        self.width = width

    @staticmethod
    def from_dict(obj: Any) -> 'OCRMarkup':
        assert isinstance(obj, dict)
        annotations = from_list(OcrMarkupAnnotation.from_dict, obj.get("annotations"))
        average_object_widths = from_list(from_float, obj.get("average_object_widths"))
        height = from_int(obj.get("height"))
        width = from_int(obj.get("width"))
        return OCRMarkup(annotations, average_object_widths, height, width)

    def to_dict(self) -> dict:
        result: dict = {}
        result["annotations"] = from_list(lambda x: to_class(OcrMarkupAnnotation, x), self.annotations)
        result["average_object_widths"] = from_list(to_float, self.average_object_widths)
        result["height"] = from_int(self.height)
        result["width"] = from_int(self.width)
        return result


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


class SegmentationMarkupAnnotation:
    annotation_type: AnnotationType
    average_width: float
    circle_annotation: Optional[CircleAnnotation]
    id: UUID
    label_id: UUID
    magicwand_annotation: Optional[MagicwandAnnotation]
    pen_annotation: Optional[PenAnnotation]
    pixel_annotation: Optional[PixelAnnotation]
    polygon_annotation: Optional[Polygon]
    rectangle_annotation: Optional[RectangleAnnotation]
    sausage_annotation: Optional[SausageAnnotation]

    def __init__(self, annotation_type: AnnotationType, average_width: float, circle_annotation: Optional[CircleAnnotation], id: UUID, label_id: UUID, magicwand_annotation: Optional[MagicwandAnnotation], pen_annotation: Optional[PenAnnotation], pixel_annotation: Optional[PixelAnnotation], polygon_annotation: Optional[Polygon], rectangle_annotation: Optional[RectangleAnnotation], sausage_annotation: Optional[SausageAnnotation]) -> None:
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
    def from_dict(obj: Any) -> 'SegmentationMarkupAnnotation':
        assert isinstance(obj, dict)
        annotation_type = AnnotationType(obj.get("annotation_type"))
        average_width = from_float(obj.get("average_width"))
        circle_annotation = from_union([CircleAnnotation.from_dict, from_none], obj.get("circle_annotation"))
        id = UUID(obj.get("id"))
        label_id = UUID(obj.get("label_id"))
        magicwand_annotation = from_union([MagicwandAnnotation.from_dict, from_none], obj.get("magicwand_annotation"))
        pen_annotation = from_union([PenAnnotation.from_dict, from_none], obj.get("pen_annotation"))
        pixel_annotation = from_union([PixelAnnotation.from_dict, from_none], obj.get("pixel_annotation"))
        polygon_annotation = from_union([Polygon.from_dict, from_none], obj.get("polygon_annotation"))
        rectangle_annotation = from_union([RectangleAnnotation.from_dict, from_none], obj.get("rectangle_annotation"))
        sausage_annotation = from_union([SausageAnnotation.from_dict, from_none], obj.get("sausage_annotation"))
        return SegmentationMarkupAnnotation(annotation_type, average_width, circle_annotation, id, label_id, magicwand_annotation, pen_annotation, pixel_annotation, polygon_annotation, rectangle_annotation, sausage_annotation)

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
            result["polygon_annotation"] = from_union([lambda x: to_class(Polygon, x), from_none], self.polygon_annotation)
        if self.rectangle_annotation is not None:
            result["rectangle_annotation"] = from_union([lambda x: to_class(RectangleAnnotation, x), from_none], self.rectangle_annotation)
        if self.sausage_annotation is not None:
            result["sausage_annotation"] = from_union([lambda x: to_class(SausageAnnotation, x), from_none], self.sausage_annotation)
        return result


class Blob:
    id: UUID
    owned_by_group_id: UUID

    def __init__(self, id: UUID, owned_by_group_id: UUID) -> None:
        self.id = id
        self.owned_by_group_id = owned_by_group_id

    @staticmethod
    def from_dict(obj: Any) -> 'Blob':
        assert isinstance(obj, dict)
        id = UUID(obj.get("id"))
        owned_by_group_id = UUID(obj.get("owned_by_group_id"))
        return Blob(id, owned_by_group_id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = str(self.id)
        result["owned_by_group_id"] = str(self.owned_by_group_id)
        return result


class SegmentationMapClassLabel:
    id: UUID
    idx: int

    def __init__(self, id: UUID, idx: int) -> None:
        self.id = id
        self.idx = idx

    @staticmethod
    def from_dict(obj: Any) -> 'SegmentationMapClassLabel':
        assert isinstance(obj, dict)
        id = UUID(obj.get("id"))
        idx = from_int(obj.get("idx"))
        return SegmentationMapClassLabel(id, idx)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = str(self.id)
        result["idx"] = from_int(self.idx)
        return result


class SegmentationMap:
    blob: Blob
    class_label: SegmentationMapClassLabel

    def __init__(self, blob: Blob, class_label: SegmentationMapClassLabel) -> None:
        self.blob = blob
        self.class_label = class_label

    @staticmethod
    def from_dict(obj: Any) -> 'SegmentationMap':
        assert isinstance(obj, dict)
        blob = Blob.from_dict(obj.get("blob"))
        class_label = SegmentationMapClassLabel.from_dict(obj.get("class_label"))
        return SegmentationMap(blob, class_label)

    def to_dict(self) -> dict:
        result: dict = {}
        result["blob"] = to_class(Blob, self.blob)
        result["class_label"] = to_class(SegmentationMapClassLabel, self.class_label)
        return result


class SegmentationMarkup:
    annotations: Optional[List[SegmentationMarkupAnnotation]]
    average_object_widths: Optional[List[float]]
    height: Optional[int]
    width: Optional[int]
    segmentation_maps: Optional[List[SegmentationMap]]

    def __init__(self, annotations: Optional[List[SegmentationMarkupAnnotation]], average_object_widths: Optional[List[float]], height: Optional[int], width: Optional[int], segmentation_maps: Optional[List[SegmentationMap]]) -> None:
        self.annotations = annotations
        self.average_object_widths = average_object_widths
        self.height = height
        self.width = width
        self.segmentation_maps = segmentation_maps

    @staticmethod
    def from_dict(obj: Any) -> 'SegmentationMarkup':
        assert isinstance(obj, dict)
        annotations = from_union([lambda x: from_list(SegmentationMarkupAnnotation.from_dict, x), from_none], obj.get("annotations"))
        average_object_widths = from_union([lambda x: from_list(from_float, x), from_none], obj.get("average_object_widths"))
        height = from_union([from_int, from_none], obj.get("height"))
        width = from_union([from_int, from_none], obj.get("width"))
        segmentation_maps = from_union([lambda x: from_list(SegmentationMap.from_dict, x), from_none], obj.get("segmentation_maps"))
        return SegmentationMarkup(annotations, average_object_widths, height, width, segmentation_maps)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.annotations is not None:
            result["annotations"] = from_union([lambda x: from_list(lambda x: to_class(SegmentationMarkupAnnotation, x), x), from_none], self.annotations)
        if self.average_object_widths is not None:
            result["average_object_widths"] = from_union([lambda x: from_list(to_float, x), from_none], self.average_object_widths)
        if self.height is not None:
            result["height"] = from_union([from_int, from_none], self.height)
        if self.width is not None:
            result["width"] = from_union([from_int, from_none], self.width)
        if self.segmentation_maps is not None:
            result["segmentation_maps"] = from_union([lambda x: from_list(lambda x: to_class(SegmentationMap, x), x), from_none], self.segmentation_maps)
        return result


class Source:
    classification_markup: Optional[ClassificationMarkup]
    object_detection_markup: Optional[ObjectDetectionMarkup]
    ocr_markup: Optional[OCRMarkup]
    segmentation_markup: Optional[SegmentationMarkup]

    def __init__(self, classification_markup: Optional[ClassificationMarkup], object_detection_markup: Optional[ObjectDetectionMarkup], ocr_markup: Optional[OCRMarkup], segmentation_markup: Optional[SegmentationMarkup]) -> None:
        self.classification_markup = classification_markup
        self.object_detection_markup = object_detection_markup
        self.ocr_markup = ocr_markup
        self.segmentation_markup = segmentation_markup

    @staticmethod
    def from_dict(obj: Any) -> 'Source':
        assert isinstance(obj, dict)
        classification_markup = from_union([ClassificationMarkup.from_dict, from_none], obj.get("classification_markup"))
        object_detection_markup = from_union([ObjectDetectionMarkup.from_dict, from_none], obj.get("object_detection_markup"))
        ocr_markup = from_union([OCRMarkup.from_dict, from_none], obj.get("ocr_markup"))
        segmentation_markup = from_union([SegmentationMarkup.from_dict, from_none], obj.get("segmentation_markup"))
        return Source(classification_markup, object_detection_markup, ocr_markup, segmentation_markup)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.classification_markup is not None:
            result["classification_markup"] = from_union([lambda x: to_class(ClassificationMarkup, x), from_none], self.classification_markup)
        if self.object_detection_markup is not None:
            result["object_detection_markup"] = from_union([lambda x: to_class(ObjectDetectionMarkup, x), from_none], self.object_detection_markup)
        if self.ocr_markup is not None:
            result["ocr_markup"] = from_union([lambda x: to_class(OCRMarkup, x), from_none], self.ocr_markup)
        if self.segmentation_markup is not None:
            result["segmentation_markup"] = from_union([lambda x: to_class(SegmentationMarkup, x), from_none], self.segmentation_markup)
        return result


class AnnotationComparerRequest:
    created_by_user_id: UUID
    hasura_url: str
    id: UUID
    image: Image
    network_experiment: NetworkExperiment
    owned_by_group_id: UUID
    source: Source
    target: Source
    user1_id: Optional[UUID]
    user2_id: Optional[UUID]

    def __init__(self, created_by_user_id: UUID, hasura_url: str, id: UUID, image: Image, network_experiment: NetworkExperiment, owned_by_group_id: UUID, source: Source, target: Source, user1_id: Optional[UUID], user2_id: Optional[UUID]) -> None:
        self.created_by_user_id = created_by_user_id
        self.hasura_url = hasura_url
        self.id = id
        self.image = image
        self.network_experiment = network_experiment
        self.owned_by_group_id = owned_by_group_id
        self.source = source
        self.target = target
        self.user1_id = user1_id
        self.user2_id = user2_id

    @staticmethod
    def from_dict(obj: Any) -> 'AnnotationComparerRequest':
        assert isinstance(obj, dict)
        created_by_user_id = UUID(obj.get("created_by_user_id"))
        hasura_url = from_str(obj.get("hasura_url"))
        id = UUID(obj.get("id"))
        image = Image.from_dict(obj.get("image"))
        network_experiment = NetworkExperiment.from_dict(obj.get("network_experiment"))
        owned_by_group_id = UUID(obj.get("owned_by_group_id"))
        source = Source.from_dict(obj.get("source"))
        target = Source.from_dict(obj.get("target"))
        user1_id = from_union([from_none, lambda x: UUID(x)], obj.get("user1_id"))
        user2_id = from_union([from_none, lambda x: UUID(x)], obj.get("user2_id"))
        return AnnotationComparerRequest(created_by_user_id, hasura_url, id, image, network_experiment, owned_by_group_id, source, target, user1_id, user2_id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["created_by_user_id"] = str(self.created_by_user_id)
        result["hasura_url"] = from_str(self.hasura_url)
        result["id"] = str(self.id)
        result["image"] = to_class(Image, self.image)
        result["network_experiment"] = to_class(NetworkExperiment, self.network_experiment)
        result["owned_by_group_id"] = str(self.owned_by_group_id)
        result["source"] = to_class(Source, self.source)
        result["target"] = to_class(Source, self.target)
        if self.user1_id is not None:
            result["user1_id"] = from_union([from_none, lambda x: str(x)], self.user1_id)
        if self.user2_id is not None:
            result["user2_id"] = from_union([from_none, lambda x: str(x)], self.user2_id)
        return result


def annotation_comparer_request_from_dict(s: Any) -> AnnotationComparerRequest:
    return AnnotationComparerRequest.from_dict(s)


def annotation_comparer_request_to_dict(x: AnnotationComparerRequest) -> Any:
    return to_class(AnnotationComparerRequest, x)
