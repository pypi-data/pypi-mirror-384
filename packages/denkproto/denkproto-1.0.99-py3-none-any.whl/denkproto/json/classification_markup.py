from uuid import UUID
from typing import Any, List, TypeVar, Callable, Type, cast


T = TypeVar("T")


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def to_float(x: Any) -> float:
    assert isinstance(x, (int, float))
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


class Annotation:
    id: UUID
    label_id: UUID
    value: float

    def __init__(self, id: UUID, label_id: UUID, value: float) -> None:
        self.id = id
        self.label_id = label_id
        self.value = value

    @staticmethod
    def from_dict(obj: Any) -> 'Annotation':
        assert isinstance(obj, dict)
        id = UUID(obj.get("id"))
        label_id = UUID(obj.get("label_id"))
        value = from_float(obj.get("value"))
        return Annotation(id, label_id, value)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = str(self.id)
        result["label_id"] = str(self.label_id)
        result["value"] = to_float(self.value)
        return result


class ClassificationMarkup:
    annotations: List[Annotation]
    height: int
    width: int

    def __init__(self, annotations: List[Annotation], height: int, width: int) -> None:
        self.annotations = annotations
        self.height = height
        self.width = width

    @staticmethod
    def from_dict(obj: Any) -> 'ClassificationMarkup':
        assert isinstance(obj, dict)
        annotations = from_list(Annotation.from_dict, obj.get("annotations"))
        height = from_int(obj.get("height"))
        width = from_int(obj.get("width"))
        return ClassificationMarkup(annotations, height, width)

    def to_dict(self) -> dict:
        result: dict = {}
        result["annotations"] = from_list(lambda x: to_class(Annotation, x), self.annotations)
        result["height"] = from_int(self.height)
        result["width"] = from_int(self.width)
        return result


def classification_markup_from_dict(s: Any) -> ClassificationMarkup:
    return ClassificationMarkup.from_dict(s)


def classification_markup_to_dict(x: ClassificationMarkup) -> Any:
    return to_class(ClassificationMarkup, x)
