from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ImageTypes(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    Raw: _ClassVar[ImageTypes]
    JPEG: _ClassVar[ImageTypes]
    PNG: _ClassVar[ImageTypes]

class ComputedPropertySubjects(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    COMPUTED_PROPERTY_SUBJECT_MEAN_GRAY_VALUE: _ClassVar[ComputedPropertySubjects]
Raw: ImageTypes
JPEG: ImageTypes
PNG: ImageTypes
COMPUTED_PROPERTY_SUBJECT_MEAN_GRAY_VALUE: ComputedPropertySubjects

class Image(_message.Message):
    __slots__ = ("id", "data", "height", "width", "channels", "filename", "imageType")
    ID_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    IMAGETYPE_FIELD_NUMBER: _ClassVar[int]
    id: str
    data: bytes
    height: int
    width: int
    channels: int
    filename: str
    imageType: ImageTypes
    def __init__(self, id: _Optional[str] = ..., data: _Optional[bytes] = ..., height: _Optional[int] = ..., width: _Optional[int] = ..., channels: _Optional[int] = ..., filename: _Optional[str] = ..., imageType: _Optional[_Union[ImageTypes, str]] = ...) -> None: ...

class FloatMapChannel(_message.Message):
    __slots__ = ("class_label_id", "data")
    CLASS_LABEL_ID_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    class_label_id: str
    data: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, class_label_id: _Optional[str] = ..., data: _Optional[_Iterable[float]] = ...) -> None: ...

class FloatMap(_message.Message):
    __slots__ = ("channels", "height", "width")
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    channels: _containers.RepeatedCompositeFieldContainer[FloatMapChannel]
    height: int
    width: int
    def __init__(self, channels: _Optional[_Iterable[_Union[FloatMapChannel, _Mapping]]] = ..., height: _Optional[int] = ..., width: _Optional[int] = ...) -> None: ...

class ClassificationPrediction(_message.Message):
    __slots__ = ("class_label_id", "score")
    CLASS_LABEL_ID_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    class_label_id: str
    score: float
    def __init__(self, class_label_id: _Optional[str] = ..., score: _Optional[float] = ...) -> None: ...

class BoundingBox(_message.Message):
    __slots__ = ("x1", "x2", "y1", "y2")
    X1_FIELD_NUMBER: _ClassVar[int]
    X2_FIELD_NUMBER: _ClassVar[int]
    Y1_FIELD_NUMBER: _ClassVar[int]
    Y2_FIELD_NUMBER: _ClassVar[int]
    x1: float
    x2: float
    y1: float
    y2: float
    def __init__(self, x1: _Optional[float] = ..., x2: _Optional[float] = ..., y1: _Optional[float] = ..., y2: _Optional[float] = ...) -> None: ...

class ObjectDetectionPrediction(_message.Message):
    __slots__ = ("class_label_id", "score", "box")
    CLASS_LABEL_ID_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    BOX_FIELD_NUMBER: _ClassVar[int]
    class_label_id: str
    score: float
    box: BoundingBox
    def __init__(self, class_label_id: _Optional[str] = ..., score: _Optional[float] = ..., box: _Optional[_Union[BoundingBox, _Mapping]] = ...) -> None: ...

class Point2d(_message.Message):
    __slots__ = ("x", "y")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ...) -> None: ...

class Contour(_message.Message):
    __slots__ = ("points",)
    POINTS_FIELD_NUMBER: _ClassVar[int]
    points: _containers.RepeatedCompositeFieldContainer[Point2d]
    def __init__(self, points: _Optional[_Iterable[_Union[Point2d, _Mapping]]] = ...) -> None: ...

class Polygon(_message.Message):
    __slots__ = ("outer", "holes")
    OUTER_FIELD_NUMBER: _ClassVar[int]
    HOLES_FIELD_NUMBER: _ClassVar[int]
    outer: Contour
    holes: _containers.RepeatedCompositeFieldContainer[Contour]
    def __init__(self, outer: _Optional[_Union[Contour, _Mapping]] = ..., holes: _Optional[_Iterable[_Union[Contour, _Mapping]]] = ...) -> None: ...

class InstanceSegmentationPrediction(_message.Message):
    __slots__ = ("class_label_id", "score", "box", "polygons", "mask")
    CLASS_LABEL_ID_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    BOX_FIELD_NUMBER: _ClassVar[int]
    POLYGONS_FIELD_NUMBER: _ClassVar[int]
    MASK_FIELD_NUMBER: _ClassVar[int]
    class_label_id: str
    score: float
    box: BoundingBox
    polygons: _containers.RepeatedCompositeFieldContainer[Polygon]
    mask: FloatMap
    def __init__(self, class_label_id: _Optional[str] = ..., score: _Optional[float] = ..., box: _Optional[_Union[BoundingBox, _Mapping]] = ..., polygons: _Optional[_Iterable[_Union[Polygon, _Mapping]]] = ..., mask: _Optional[_Union[FloatMap, _Mapping]] = ...) -> None: ...

class OCRPrediction(_message.Message):
    __slots__ = ("class_label_id", "polygon", "score", "text", "char_scores")
    CLASS_LABEL_ID_FIELD_NUMBER: _ClassVar[int]
    POLYGON_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    CHAR_SCORES_FIELD_NUMBER: _ClassVar[int]
    class_label_id: str
    polygon: Polygon
    score: float
    text: bytes
    char_scores: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, class_label_id: _Optional[str] = ..., polygon: _Optional[_Union[Polygon, _Mapping]] = ..., score: _Optional[float] = ..., text: _Optional[bytes] = ..., char_scores: _Optional[_Iterable[float]] = ...) -> None: ...

class CodePrediction(_message.Message):
    __slots__ = ("class_label_id", "polygon", "code_type", "text")
    CLASS_LABEL_ID_FIELD_NUMBER: _ClassVar[int]
    POLYGON_FIELD_NUMBER: _ClassVar[int]
    CODE_TYPE_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    class_label_id: str
    polygon: Polygon
    code_type: str
    text: bytes
    def __init__(self, class_label_id: _Optional[str] = ..., polygon: _Optional[_Union[Polygon, _Mapping]] = ..., code_type: _Optional[str] = ..., text: _Optional[bytes] = ...) -> None: ...

class ComputedPropertyValue(_message.Message):
    __slots__ = ("_int64", "_double", "_string")
    _INT64_FIELD_NUMBER: _ClassVar[int]
    _DOUBLE_FIELD_NUMBER: _ClassVar[int]
    _STRING_FIELD_NUMBER: _ClassVar[int]
    _int64: int
    _double: float
    _string: str
    def __init__(self, _int64: _Optional[int] = ..., _double: _Optional[float] = ..., _string: _Optional[str] = ...) -> None: ...

class ComputedProperty(_message.Message):
    __slots__ = ("subject", "value")
    SUBJECT_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    subject: ComputedPropertySubjects
    value: ComputedPropertyValue
    def __init__(self, subject: _Optional[_Union[ComputedPropertySubjects, str]] = ..., value: _Optional[_Union[ComputedPropertyValue, _Mapping]] = ...) -> None: ...

class Prediction(_message.Message):
    __slots__ = ("classification", "object_detection", "instance_segmentation", "ocr", "code", "segmentation", "anomaly_detection", "computed_properties")
    CLASSIFICATION_FIELD_NUMBER: _ClassVar[int]
    OBJECT_DETECTION_FIELD_NUMBER: _ClassVar[int]
    INSTANCE_SEGMENTATION_FIELD_NUMBER: _ClassVar[int]
    OCR_FIELD_NUMBER: _ClassVar[int]
    CODE_FIELD_NUMBER: _ClassVar[int]
    SEGMENTATION_FIELD_NUMBER: _ClassVar[int]
    ANOMALY_DETECTION_FIELD_NUMBER: _ClassVar[int]
    COMPUTED_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    classification: ClassificationPrediction
    object_detection: ObjectDetectionPrediction
    instance_segmentation: InstanceSegmentationPrediction
    ocr: OCRPrediction
    code: CodePrediction
    segmentation: FloatMap
    anomaly_detection: FloatMap
    computed_properties: _containers.RepeatedCompositeFieldContainer[ComputedProperty]
    def __init__(self, classification: _Optional[_Union[ClassificationPrediction, _Mapping]] = ..., object_detection: _Optional[_Union[ObjectDetectionPrediction, _Mapping]] = ..., instance_segmentation: _Optional[_Union[InstanceSegmentationPrediction, _Mapping]] = ..., ocr: _Optional[_Union[OCRPrediction, _Mapping]] = ..., code: _Optional[_Union[CodePrediction, _Mapping]] = ..., segmentation: _Optional[_Union[FloatMap, _Mapping]] = ..., anomaly_detection: _Optional[_Union[FloatMap, _Mapping]] = ..., computed_properties: _Optional[_Iterable[_Union[ComputedProperty, _Mapping]]] = ...) -> None: ...

class Predictions(_message.Message):
    __slots__ = ("predictions",)
    PREDICTIONS_FIELD_NUMBER: _ClassVar[int]
    predictions: _containers.RepeatedCompositeFieldContainer[Prediction]
    def __init__(self, predictions: _Optional[_Iterable[_Union[Prediction, _Mapping]]] = ...) -> None: ...

class Result(_message.Message):
    __slots__ = ("grade", "name", "color")
    GRADE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    COLOR_FIELD_NUMBER: _ClassVar[int]
    grade: int
    name: str
    color: str
    def __init__(self, grade: _Optional[int] = ..., name: _Optional[str] = ..., color: _Optional[str] = ...) -> None: ...

class ClassLabel(_message.Message):
    __slots__ = ("id", "network_id", "index", "name", "color")
    ID_FIELD_NUMBER: _ClassVar[int]
    NETWORK_ID_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    COLOR_FIELD_NUMBER: _ClassVar[int]
    id: str
    network_id: str
    index: int
    name: str
    color: str
    def __init__(self, id: _Optional[str] = ..., network_id: _Optional[str] = ..., index: _Optional[int] = ..., name: _Optional[str] = ..., color: _Optional[str] = ...) -> None: ...

class DENKbuffer(_message.Message):
    __slots__ = ("id", "project_id", "created_by_user_id", "owned_by_group_id", "created_at", "pipeline_config", "port_names", "class_labels", "triggers", "images", "predictions", "results", "tags")
    class PortNamesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class ClassLabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: ClassLabel
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[ClassLabel, _Mapping]] = ...) -> None: ...
    class TriggersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _timestamp_pb2.Timestamp
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
    class ImagesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Image
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Image, _Mapping]] = ...) -> None: ...
    class PredictionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Predictions
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Predictions, _Mapping]] = ...) -> None: ...
    class ResultsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Result
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Result, _Mapping]] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    CREATED_BY_USER_ID_FIELD_NUMBER: _ClassVar[int]
    OWNED_BY_GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_CONFIG_FIELD_NUMBER: _ClassVar[int]
    PORT_NAMES_FIELD_NUMBER: _ClassVar[int]
    CLASS_LABELS_FIELD_NUMBER: _ClassVar[int]
    TRIGGERS_FIELD_NUMBER: _ClassVar[int]
    IMAGES_FIELD_NUMBER: _ClassVar[int]
    PREDICTIONS_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    id: str
    project_id: str
    created_by_user_id: str
    owned_by_group_id: str
    created_at: _timestamp_pb2.Timestamp
    pipeline_config: str
    port_names: _containers.ScalarMap[str, str]
    class_labels: _containers.MessageMap[str, ClassLabel]
    triggers: _containers.MessageMap[str, _timestamp_pb2.Timestamp]
    images: _containers.MessageMap[str, Image]
    predictions: _containers.MessageMap[str, Predictions]
    results: _containers.MessageMap[str, Result]
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[str] = ..., project_id: _Optional[str] = ..., created_by_user_id: _Optional[str] = ..., owned_by_group_id: _Optional[str] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., pipeline_config: _Optional[str] = ..., port_names: _Optional[_Mapping[str, str]] = ..., class_labels: _Optional[_Mapping[str, ClassLabel]] = ..., triggers: _Optional[_Mapping[str, _timestamp_pb2.Timestamp]] = ..., images: _Optional[_Mapping[str, Image]] = ..., predictions: _Optional[_Mapping[str, Predictions]] = ..., results: _Optional[_Mapping[str, Result]] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...
