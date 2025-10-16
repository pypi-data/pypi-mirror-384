from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class FileType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    FT_MODEL: _ClassVar[FileType]
    FT_VIZIOTIX_KEY: _ClassVar[FileType]
    FT_ZXING_KEY: _ClassVar[FileType]

class CompressionMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NONE: _ClassVar[CompressionMethod]
    GZIP: _ClassVar[CompressionMethod]
    ZLIB: _ClassVar[CompressionMethod]
    LZMA: _ClassVar[CompressionMethod]
    BZ2: _ClassVar[CompressionMethod]

class DataType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SCALAR_INT: _ClassVar[DataType]
    SCALAR_FLOAT: _ClassVar[DataType]
    IMAGE_RAW_INT: _ClassVar[DataType]
    IMAGE_RAW_FLOAT: _ClassVar[DataType]
    IMAGE_PNG: _ClassVar[DataType]
    IMAGE_JPG: _ClassVar[DataType]
    IMAGE_TIF: _ClassVar[DataType]
    BOUNDING_BOX_LIST: _ClassVar[DataType]
    BOUNDING_BOX_LIST_SEGMENTATION: _ClassVar[DataType]
    BOUNDING_BOX_LIST_SEGMENTATION_HIGH_RES: _ClassVar[DataType]
    OPTICAL_CHARACTER_RECOGNITION: _ClassVar[DataType]
    BARCODES: _ClassVar[DataType]
    BOUNDING_BOX_LIST_HALF_ORIENTATION: _ClassVar[DataType]
    BOUNDING_BOX_LIST_FULL_ORIENTATION: _ClassVar[DataType]

class ModelType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    REGULAR: _ClassVar[ModelType]
    AREA_DEFINITION: _ClassVar[ModelType]

class ModelOutputType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TYPE_UNKNOWN: _ClassVar[ModelOutputType]
    TYPE_CLASSIFICATION: _ClassVar[ModelOutputType]
    TYPE_SEGMENTATION: _ClassVar[ModelOutputType]
    TYPE_INSTANCE_SEGMENTATION: _ClassVar[ModelOutputType]
    TYPE_OBJECT_DETECTION: _ClassVar[ModelOutputType]
    TYPE_ANOMALY_DETECTION: _ClassVar[ModelOutputType]
    TYPE_OPTICAL_CHARACTER_RECOGNITION: _ClassVar[ModelOutputType]
    TYPE_BARCODES: _ClassVar[ModelOutputType]
    TYPE_OBJECT_DETECTION_HALF_ORIENTATION: _ClassVar[ModelOutputType]
    TYPE_OBJECT_DETECTION_FULL_ORIENTATION: _ClassVar[ModelOutputType]
FT_MODEL: FileType
FT_VIZIOTIX_KEY: FileType
FT_ZXING_KEY: FileType
NONE: CompressionMethod
GZIP: CompressionMethod
ZLIB: CompressionMethod
LZMA: CompressionMethod
BZ2: CompressionMethod
SCALAR_INT: DataType
SCALAR_FLOAT: DataType
IMAGE_RAW_INT: DataType
IMAGE_RAW_FLOAT: DataType
IMAGE_PNG: DataType
IMAGE_JPG: DataType
IMAGE_TIF: DataType
BOUNDING_BOX_LIST: DataType
BOUNDING_BOX_LIST_SEGMENTATION: DataType
BOUNDING_BOX_LIST_SEGMENTATION_HIGH_RES: DataType
OPTICAL_CHARACTER_RECOGNITION: DataType
BARCODES: DataType
BOUNDING_BOX_LIST_HALF_ORIENTATION: DataType
BOUNDING_BOX_LIST_FULL_ORIENTATION: DataType
REGULAR: ModelType
AREA_DEFINITION: ModelType
TYPE_UNKNOWN: ModelOutputType
TYPE_CLASSIFICATION: ModelOutputType
TYPE_SEGMENTATION: ModelOutputType
TYPE_INSTANCE_SEGMENTATION: ModelOutputType
TYPE_OBJECT_DETECTION: ModelOutputType
TYPE_ANOMALY_DETECTION: ModelOutputType
TYPE_OPTICAL_CHARACTER_RECOGNITION: ModelOutputType
TYPE_BARCODES: ModelOutputType
TYPE_OBJECT_DETECTION_HALF_ORIENTATION: ModelOutputType
TYPE_OBJECT_DETECTION_FULL_ORIENTATION: ModelOutputType

class RegionFromEdge(_message.Message):
    __slots__ = ("left", "right", "top", "bottom")
    LEFT_FIELD_NUMBER: _ClassVar[int]
    RIGHT_FIELD_NUMBER: _ClassVar[int]
    TOP_FIELD_NUMBER: _ClassVar[int]
    BOTTOM_FIELD_NUMBER: _ClassVar[int]
    left: float
    right: float
    top: float
    bottom: float
    def __init__(self, left: _Optional[float] = ..., right: _Optional[float] = ..., top: _Optional[float] = ..., bottom: _Optional[float] = ...) -> None: ...

class FeatureClass(_message.Message):
    __slots__ = ("feature_uid", "feature_name", "color", "feature_tag")
    FEATURE_UID_FIELD_NUMBER: _ClassVar[int]
    FEATURE_NAME_FIELD_NUMBER: _ClassVar[int]
    COLOR_FIELD_NUMBER: _ClassVar[int]
    FEATURE_TAG_FIELD_NUMBER: _ClassVar[int]
    feature_uid: str
    feature_name: str
    color: _containers.RepeatedScalarFieldContainer[int]
    feature_tag: str
    def __init__(self, feature_uid: _Optional[str] = ..., feature_name: _Optional[str] = ..., color: _Optional[_Iterable[int]] = ..., feature_tag: _Optional[str] = ...) -> None: ...

class InputField(_message.Message):
    __slots__ = ("label", "datatype", "image_w", "image_h", "image_c", "region_of_interest", "training_image_w", "training_image_h", "training_image_c", "moving_window")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    DATATYPE_FIELD_NUMBER: _ClassVar[int]
    IMAGE_W_FIELD_NUMBER: _ClassVar[int]
    IMAGE_H_FIELD_NUMBER: _ClassVar[int]
    IMAGE_C_FIELD_NUMBER: _ClassVar[int]
    REGION_OF_INTEREST_FIELD_NUMBER: _ClassVar[int]
    TRAINING_IMAGE_W_FIELD_NUMBER: _ClassVar[int]
    TRAINING_IMAGE_H_FIELD_NUMBER: _ClassVar[int]
    TRAINING_IMAGE_C_FIELD_NUMBER: _ClassVar[int]
    MOVING_WINDOW_FIELD_NUMBER: _ClassVar[int]
    label: str
    datatype: DataType
    image_w: int
    image_h: int
    image_c: int
    region_of_interest: _containers.RepeatedCompositeFieldContainer[RegionFromEdge]
    training_image_w: int
    training_image_h: int
    training_image_c: int
    moving_window: bool
    def __init__(self, label: _Optional[str] = ..., datatype: _Optional[_Union[DataType, str]] = ..., image_w: _Optional[int] = ..., image_h: _Optional[int] = ..., image_c: _Optional[int] = ..., region_of_interest: _Optional[_Iterable[_Union[RegionFromEdge, _Mapping]]] = ..., training_image_w: _Optional[int] = ..., training_image_h: _Optional[int] = ..., training_image_c: _Optional[int] = ..., moving_window: bool = ...) -> None: ...

class OcrFormatRestrictionBlock(_message.Message):
    __slots__ = ("number_of_characters", "allowed_characters")
    NUMBER_OF_CHARACTERS_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_CHARACTERS_FIELD_NUMBER: _ClassVar[int]
    number_of_characters: int
    allowed_characters: bytes
    def __init__(self, number_of_characters: _Optional[int] = ..., allowed_characters: _Optional[bytes] = ...) -> None: ...

class OutputField(_message.Message):
    __slots__ = ("label", "datatype", "color", "image_w", "image_h", "image_c", "classes", "max_queries", "charset", "charset_filter", "ocr_format_restrictions")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    DATATYPE_FIELD_NUMBER: _ClassVar[int]
    COLOR_FIELD_NUMBER: _ClassVar[int]
    IMAGE_W_FIELD_NUMBER: _ClassVar[int]
    IMAGE_H_FIELD_NUMBER: _ClassVar[int]
    IMAGE_C_FIELD_NUMBER: _ClassVar[int]
    CLASSES_FIELD_NUMBER: _ClassVar[int]
    MAX_QUERIES_FIELD_NUMBER: _ClassVar[int]
    CHARSET_FIELD_NUMBER: _ClassVar[int]
    CHARSET_FILTER_FIELD_NUMBER: _ClassVar[int]
    OCR_FORMAT_RESTRICTIONS_FIELD_NUMBER: _ClassVar[int]
    label: str
    datatype: DataType
    color: _containers.RepeatedScalarFieldContainer[int]
    image_w: int
    image_h: int
    image_c: int
    classes: _containers.RepeatedCompositeFieldContainer[FeatureClass]
    max_queries: int
    charset: bytes
    charset_filter: bytes
    ocr_format_restrictions: _containers.RepeatedCompositeFieldContainer[OcrFormatRestrictionBlock]
    def __init__(self, label: _Optional[str] = ..., datatype: _Optional[_Union[DataType, str]] = ..., color: _Optional[_Iterable[int]] = ..., image_w: _Optional[int] = ..., image_h: _Optional[int] = ..., image_c: _Optional[int] = ..., classes: _Optional[_Iterable[_Union[FeatureClass, _Mapping]]] = ..., max_queries: _Optional[int] = ..., charset: _Optional[bytes] = ..., charset_filter: _Optional[bytes] = ..., ocr_format_restrictions: _Optional[_Iterable[_Union[OcrFormatRestrictionBlock, _Mapping]]] = ...) -> None: ...

class ModelFile(_message.Message):
    __slots__ = ("protocol_version", "model", "compression_method", "model_hash_blake2b", "input", "output", "tenant", "model_label", "model_tag", "model_id", "creation_timestamp", "tenant_id", "onnx_version_major", "onnx_version_minor", "model_uid", "model_timestamp", "model_type", "model_output_type", "file_type", "key")
    PROTOCOL_VERSION_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    COMPRESSION_METHOD_FIELD_NUMBER: _ClassVar[int]
    MODEL_HASH_BLAKE2B_FIELD_NUMBER: _ClassVar[int]
    INPUT_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    TENANT_FIELD_NUMBER: _ClassVar[int]
    MODEL_LABEL_FIELD_NUMBER: _ClassVar[int]
    MODEL_TAG_FIELD_NUMBER: _ClassVar[int]
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    CREATION_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    ONNX_VERSION_MAJOR_FIELD_NUMBER: _ClassVar[int]
    ONNX_VERSION_MINOR_FIELD_NUMBER: _ClassVar[int]
    MODEL_UID_FIELD_NUMBER: _ClassVar[int]
    MODEL_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    MODEL_TYPE_FIELD_NUMBER: _ClassVar[int]
    MODEL_OUTPUT_TYPE_FIELD_NUMBER: _ClassVar[int]
    FILE_TYPE_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    protocol_version: str
    model: bytes
    compression_method: CompressionMethod
    model_hash_blake2b: str
    input: _containers.RepeatedCompositeFieldContainer[InputField]
    output: _containers.RepeatedCompositeFieldContainer[OutputField]
    tenant: str
    model_label: str
    model_tag: str
    model_id: int
    creation_timestamp: int
    tenant_id: str
    onnx_version_major: int
    onnx_version_minor: int
    model_uid: str
    model_timestamp: int
    model_type: ModelType
    model_output_type: ModelOutputType
    file_type: FileType
    key: str
    def __init__(self, protocol_version: _Optional[str] = ..., model: _Optional[bytes] = ..., compression_method: _Optional[_Union[CompressionMethod, str]] = ..., model_hash_blake2b: _Optional[str] = ..., input: _Optional[_Iterable[_Union[InputField, _Mapping]]] = ..., output: _Optional[_Iterable[_Union[OutputField, _Mapping]]] = ..., tenant: _Optional[str] = ..., model_label: _Optional[str] = ..., model_tag: _Optional[str] = ..., model_id: _Optional[int] = ..., creation_timestamp: _Optional[int] = ..., tenant_id: _Optional[str] = ..., onnx_version_major: _Optional[int] = ..., onnx_version_minor: _Optional[int] = ..., model_uid: _Optional[str] = ..., model_timestamp: _Optional[int] = ..., model_type: _Optional[_Union[ModelType, str]] = ..., model_output_type: _Optional[_Union[ModelOutputType, str]] = ..., file_type: _Optional[_Union[FileType, str]] = ..., key: _Optional[str] = ...) -> None: ...
