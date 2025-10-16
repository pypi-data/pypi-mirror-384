from enum import Enum
from typing import Optional, Any, List, TypeVar, Type, Callable, cast
from uuid import UUID


T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


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


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class AnnotationType(Enum):
    IGNORE = "IGNORE"
    NEGATIVE = "NEGATIVE"
    POSITIVE = "POSITIVE"
    ROI = "ROI"


class Annotation:
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
    def from_dict(obj: Any) -> 'Annotation':
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
        return Annotation(angle, annotation_type, average_width, bottom_right_x, bottom_right_y, full_orientation, id, label_id, top_left_x, top_left_y)

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
    annotations: List[Annotation]
    height: int
    width: int

    def __init__(self, annotations: List[Annotation], height: int, width: int) -> None:
        self.annotations = annotations
        self.height = height
        self.width = width

    @staticmethod
    def from_dict(obj: Any) -> 'ObjectDetectionMarkup':
        assert isinstance(obj, dict)
        annotations = from_list(Annotation.from_dict, obj.get("annotations"))
        height = from_int(obj.get("height"))
        width = from_int(obj.get("width"))
        return ObjectDetectionMarkup(annotations, height, width)

    def to_dict(self) -> dict:
        result: dict = {}
        result["annotations"] = from_list(lambda x: to_class(Annotation, x), self.annotations)
        result["height"] = from_int(self.height)
        result["width"] = from_int(self.width)
        return result


def object_detection_markup_from_dict(s: Any) -> ObjectDetectionMarkup:
    return ObjectDetectionMarkup.from_dict(s)


def object_detection_markup_to_dict(x: ObjectDetectionMarkup) -> Any:
    return to_class(ObjectDetectionMarkup, x)
