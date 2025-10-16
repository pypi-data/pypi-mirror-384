from uuid import UUID
from typing import Any, Dict, List, Optional, TypeVar, Callable, Type, cast
from enum import Enum


T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_dict(f: Callable[[Any], T], x: Any) -> Dict[str, T]:
    assert isinstance(x, dict)
    return { k: f(v) for (k, v) in x.items() }


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


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


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def to_float(x: Any) -> float:
    assert isinstance(x, (int, float))
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


class Config:
    metadata: Dict[str, Any]
    uses_validation_tiling: bool

    def __init__(self, metadata: Dict[str, Any], uses_validation_tiling: bool) -> None:
        self.metadata = metadata
        self.uses_validation_tiling = uses_validation_tiling

    @staticmethod
    def from_dict(obj: Any) -> 'Config':
        assert isinstance(obj, dict)
        metadata = from_dict(lambda x: x, obj.get("metadata"))
        uses_validation_tiling = from_bool(obj.get("uses_validation_tiling"))
        return Config(metadata, uses_validation_tiling)

    def to_dict(self) -> dict:
        result: dict = {}
        result["metadata"] = from_dict(lambda x: x, self.metadata)
        result["uses_validation_tiling"] = from_bool(self.uses_validation_tiling)
        return result


class OcrCharacterRestrictionPreset:
    characters: str
    value: str

    def __init__(self, characters: str, value: str) -> None:
        self.characters = characters
        self.value = value

    @staticmethod
    def from_dict(obj: Any) -> 'OcrCharacterRestrictionPreset':
        assert isinstance(obj, dict)
        characters = from_str(obj.get("characters"))
        value = from_str(obj.get("value"))
        return OcrCharacterRestrictionPreset(characters, value)

    def to_dict(self) -> dict:
        result: dict = {}
        result["characters"] = from_str(self.characters)
        result["value"] = from_str(self.value)
        return result


class OcrCharacterRestrictionElement:
    allowed_characters: str
    index: int
    number_of_characters: int
    ocr_character_restriction_preset: OcrCharacterRestrictionPreset

    def __init__(self, allowed_characters: str, index: int, number_of_characters: int, ocr_character_restriction_preset: OcrCharacterRestrictionPreset) -> None:
        self.allowed_characters = allowed_characters
        self.index = index
        self.number_of_characters = number_of_characters
        self.ocr_character_restriction_preset = ocr_character_restriction_preset

    @staticmethod
    def from_dict(obj: Any) -> 'OcrCharacterRestrictionElement':
        assert isinstance(obj, dict)
        allowed_characters = from_str(obj.get("allowed_characters"))
        index = from_int(obj.get("index"))
        number_of_characters = from_int(obj.get("number_of_characters"))
        ocr_character_restriction_preset = OcrCharacterRestrictionPreset.from_dict(obj.get("ocr_character_restriction_preset"))
        return OcrCharacterRestrictionElement(allowed_characters, index, number_of_characters, ocr_character_restriction_preset)

    def to_dict(self) -> dict:
        result: dict = {}
        result["allowed_characters"] = from_str(self.allowed_characters)
        result["index"] = from_int(self.index)
        result["number_of_characters"] = from_int(self.number_of_characters)
        result["ocr_character_restriction_preset"] = to_class(OcrCharacterRestrictionPreset, self.ocr_character_restriction_preset)
        return result


class Onnx:
    blob_id: UUID
    owned_by_group_id: UUID

    def __init__(self, blob_id: UUID, owned_by_group_id: UUID) -> None:
        self.blob_id = blob_id
        self.owned_by_group_id = owned_by_group_id

    @staticmethod
    def from_dict(obj: Any) -> 'Onnx':
        assert isinstance(obj, dict)
        blob_id = UUID(obj.get("blob_id"))
        owned_by_group_id = UUID(obj.get("owned_by_group_id"))
        return Onnx(blob_id, owned_by_group_id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["blob_id"] = str(self.blob_id)
        result["owned_by_group_id"] = str(self.owned_by_group_id)
        return result


class Snapshot:
    onnx: Onnx
    pytorch: Onnx

    def __init__(self, onnx: Onnx, pytorch: Onnx) -> None:
        self.onnx = onnx
        self.pytorch = pytorch

    @staticmethod
    def from_dict(obj: Any) -> 'Snapshot':
        assert isinstance(obj, dict)
        onnx = Onnx.from_dict(obj.get("onnx"))
        pytorch = Onnx.from_dict(obj.get("pytorch"))
        return Snapshot(onnx, pytorch)

    def to_dict(self) -> dict:
        result: dict = {}
        result["onnx"] = to_class(Onnx, self.onnx)
        result["pytorch"] = to_class(Onnx, self.pytorch)
        return result


class NetworkExperiment:
    class_labels: List[ClassLabelElement]
    config: Config
    flavor: str
    id: UUID
    network_typename: str
    ocr_character_restrictions: Optional[List[OcrCharacterRestrictionElement]]
    """Only present for OCR prediction requests"""

    snapshot: Snapshot

    def __init__(self, class_labels: List[ClassLabelElement], config: Config, flavor: str, id: UUID, network_typename: str, ocr_character_restrictions: Optional[List[OcrCharacterRestrictionElement]], snapshot: Snapshot) -> None:
        self.class_labels = class_labels
        self.config = config
        self.flavor = flavor
        self.id = id
        self.network_typename = network_typename
        self.ocr_character_restrictions = ocr_character_restrictions
        self.snapshot = snapshot

    @staticmethod
    def from_dict(obj: Any) -> 'NetworkExperiment':
        assert isinstance(obj, dict)
        class_labels = from_list(ClassLabelElement.from_dict, obj.get("class_labels"))
        config = Config.from_dict(obj.get("config"))
        flavor = from_str(obj.get("flavor"))
        id = UUID(obj.get("id"))
        network_typename = from_str(obj.get("network_typename"))
        ocr_character_restrictions = from_union([lambda x: from_list(OcrCharacterRestrictionElement.from_dict, x), from_none], obj.get("ocr_character_restrictions"))
        snapshot = Snapshot.from_dict(obj.get("snapshot"))
        return NetworkExperiment(class_labels, config, flavor, id, network_typename, ocr_character_restrictions, snapshot)

    def to_dict(self) -> dict:
        result: dict = {}
        result["class_labels"] = from_list(lambda x: to_class(ClassLabelElement, x), self.class_labels)
        result["config"] = to_class(Config, self.config)
        result["flavor"] = from_str(self.flavor)
        result["id"] = str(self.id)
        result["network_typename"] = from_str(self.network_typename)
        if self.ocr_character_restrictions is not None:
            result["ocr_character_restrictions"] = from_union([lambda x: from_list(lambda x: to_class(OcrCharacterRestrictionElement, x), x), from_none], self.ocr_character_restrictions)
        result["snapshot"] = to_class(Snapshot, self.snapshot)
        return result


class AnnotationType(Enum):
    IGNORE = "IGNORE"
    NEGATIVE = "NEGATIVE"
    POSITIVE = "POSITIVE"
    ROI = "ROI"


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


class ObjectElement:
    annotation_type: AnnotationType
    average_width: float
    bounding_box: Optional[BoundingBox]
    id: UUID
    label_id: UUID
    polygon: Optional[Polygon]

    def __init__(self, annotation_type: AnnotationType, average_width: float, bounding_box: Optional[BoundingBox], id: UUID, label_id: UUID, polygon: Optional[Polygon]) -> None:
        self.annotation_type = annotation_type
        self.average_width = average_width
        self.bounding_box = bounding_box
        self.id = id
        self.label_id = label_id
        self.polygon = polygon

    @staticmethod
    def from_dict(obj: Any) -> 'ObjectElement':
        assert isinstance(obj, dict)
        annotation_type = AnnotationType(obj.get("annotation_type"))
        average_width = from_float(obj.get("average_width"))
        bounding_box = from_union([BoundingBox.from_dict, from_none], obj.get("bounding_box"))
        id = UUID(obj.get("id"))
        label_id = UUID(obj.get("label_id"))
        polygon = from_union([Polygon.from_dict, from_none], obj.get("polygon"))
        return ObjectElement(annotation_type, average_width, bounding_box, id, label_id, polygon)

    def to_dict(self) -> dict:
        result: dict = {}
        result["annotation_type"] = to_enum(AnnotationType, self.annotation_type)
        result["average_width"] = to_float(self.average_width)
        if self.bounding_box is not None:
            result["bounding_box"] = from_union([lambda x: to_class(BoundingBox, x), from_none], self.bounding_box)
        result["id"] = str(self.id)
        result["label_id"] = str(self.label_id)
        if self.polygon is not None:
            result["polygon"] = from_union([lambda x: to_class(Polygon, x), from_none], self.polygon)
        return result


class RequestType(Enum):
    """Discriminator field to identify the type of prediction request"""

    OCR = "ocr"
    STANDARD = "standard"


class PredictionRequest:
    created_by_user_id: UUID
    hasura_url: str
    id: UUID
    image: Image
    network_experiment: NetworkExperiment
    objects: Optional[List[ObjectElement]]
    """Only present for OCR prediction requests"""

    owned_by_group_id: UUID
    prediction_priority: int
    request_classification_interpretation: Optional[bool]
    """Only present for standard prediction requests"""

    request_type: RequestType
    """Discriminator field to identify the type of prediction request"""

    def __init__(self, created_by_user_id: UUID, hasura_url: str, id: UUID, image: Image, network_experiment: NetworkExperiment, objects: Optional[List[ObjectElement]], owned_by_group_id: UUID, prediction_priority: int, request_classification_interpretation: Optional[bool], request_type: RequestType) -> None:
        self.created_by_user_id = created_by_user_id
        self.hasura_url = hasura_url
        self.id = id
        self.image = image
        self.network_experiment = network_experiment
        self.objects = objects
        self.owned_by_group_id = owned_by_group_id
        self.prediction_priority = prediction_priority
        self.request_classification_interpretation = request_classification_interpretation
        self.request_type = request_type

    @staticmethod
    def from_dict(obj: Any) -> 'PredictionRequest':
        assert isinstance(obj, dict)
        created_by_user_id = UUID(obj.get("created_by_user_id"))
        hasura_url = from_str(obj.get("hasura_url"))
        id = UUID(obj.get("id"))
        image = Image.from_dict(obj.get("image"))
        network_experiment = NetworkExperiment.from_dict(obj.get("network_experiment"))
        objects = from_union([lambda x: from_list(ObjectElement.from_dict, x), from_none], obj.get("objects"))
        owned_by_group_id = UUID(obj.get("owned_by_group_id"))
        prediction_priority = from_int(obj.get("prediction_priority"))
        request_classification_interpretation = from_union([from_bool, from_none], obj.get("request_classification_interpretation"))
        request_type = RequestType(obj.get("request_type"))
        return PredictionRequest(created_by_user_id, hasura_url, id, image, network_experiment, objects, owned_by_group_id, prediction_priority, request_classification_interpretation, request_type)

    def to_dict(self) -> dict:
        result: dict = {}
        result["created_by_user_id"] = str(self.created_by_user_id)
        result["hasura_url"] = from_str(self.hasura_url)
        result["id"] = str(self.id)
        result["image"] = to_class(Image, self.image)
        result["network_experiment"] = to_class(NetworkExperiment, self.network_experiment)
        if self.objects is not None:
            result["objects"] = from_union([lambda x: from_list(lambda x: to_class(ObjectElement, x), x), from_none], self.objects)
        result["owned_by_group_id"] = str(self.owned_by_group_id)
        result["prediction_priority"] = from_int(self.prediction_priority)
        if self.request_classification_interpretation is not None:
            result["request_classification_interpretation"] = from_union([from_bool, from_none], self.request_classification_interpretation)
        result["request_type"] = to_enum(RequestType, self.request_type)
        return result


def prediction_request_from_dict(s: Any) -> PredictionRequest:
    return PredictionRequest.from_dict(s)


def prediction_request_to_dict(x: PredictionRequest) -> Any:
    return to_class(PredictionRequest, x)
