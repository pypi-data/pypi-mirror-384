from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MapDataType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MAP_INT8: _ClassVar[MapDataType]
    MAP_INT16: _ClassVar[MapDataType]
    MAP_INT32: _ClassVar[MapDataType]
    MAP_INT64: _ClassVar[MapDataType]
    MAP_UINT8: _ClassVar[MapDataType]
    MAP_UINT16: _ClassVar[MapDataType]
    MAP_UINT32: _ClassVar[MapDataType]
    MAP_UINT64: _ClassVar[MapDataType]
    MAP_FLOAT8: _ClassVar[MapDataType]
    MAP_FLOAT16: _ClassVar[MapDataType]
    MAP_FLOAT32: _ClassVar[MapDataType]
    MAP_FLOAT64: _ClassVar[MapDataType]

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

class BarcodeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BT_UNDEFINED: _ClassVar[BarcodeType]
    BT_AZTEC: _ClassVar[BarcodeType]
    BT_CODABAR: _ClassVar[BarcodeType]
    BT_CODE_32: _ClassVar[BarcodeType]
    BT_CODE_39: _ClassVar[BarcodeType]
    BT_CODE_93: _ClassVar[BarcodeType]
    BT_CODE_128: _ClassVar[BarcodeType]
    BT_DATABAR: _ClassVar[BarcodeType]
    BT_DATABAR_EXPANDED: _ClassVar[BarcodeType]
    BT_DATABAR_LIMITED: _ClassVar[BarcodeType]
    BT_DATAMATRIX: _ClassVar[BarcodeType]
    BT_EAN_8: _ClassVar[BarcodeType]
    BT_EAN_13: _ClassVar[BarcodeType]
    BT_EAN_13_WITH_ADDON_2: _ClassVar[BarcodeType]
    BT_EAN_13_WITH_ADDON_5: _ClassVar[BarcodeType]
    BT_GS1_DATAMATRIX: _ClassVar[BarcodeType]
    BT_GS1_128: _ClassVar[BarcodeType]
    BT_ISBT_128: _ClassVar[BarcodeType]
    BT_ITF: _ClassVar[BarcodeType]
    BT_ITF_14: _ClassVar[BarcodeType]
    BT_MAXICODE: _ClassVar[BarcodeType]
    BT_MICRO_QR_CODE: _ClassVar[BarcodeType]
    BT_MSI: _ClassVar[BarcodeType]
    BT_PDF417: _ClassVar[BarcodeType]
    BT_QR_CODE: _ClassVar[BarcodeType]
    BT_UPC_A: _ClassVar[BarcodeType]
    BT_UPC_A_WITH_ADDON_2: _ClassVar[BarcodeType]
    BT_UPC_A_WITH_ADDON_5: _ClassVar[BarcodeType]
    BT_UPC_E: _ClassVar[BarcodeType]
    BT_UPC_E_WITH_ADDON_2: _ClassVar[BarcodeType]
    BT_UPC_E_WITH_ADDON_5: _ClassVar[BarcodeType]

class ResultFieldType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RFT_REGULAR: _ClassVar[ResultFieldType]
    RFT_MODEL_SUMMARY: _ClassVar[ResultFieldType]
    RFT_DEBUG: _ClassVar[ResultFieldType]

class DeviceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNDEFINED: _ClassVar[DeviceType]
    CPU: _ClassVar[DeviceType]
    GPU: _ClassVar[DeviceType]
MAP_INT8: MapDataType
MAP_INT16: MapDataType
MAP_INT32: MapDataType
MAP_INT64: MapDataType
MAP_UINT8: MapDataType
MAP_UINT16: MapDataType
MAP_UINT32: MapDataType
MAP_UINT64: MapDataType
MAP_FLOAT8: MapDataType
MAP_FLOAT16: MapDataType
MAP_FLOAT32: MapDataType
MAP_FLOAT64: MapDataType
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
BT_UNDEFINED: BarcodeType
BT_AZTEC: BarcodeType
BT_CODABAR: BarcodeType
BT_CODE_32: BarcodeType
BT_CODE_39: BarcodeType
BT_CODE_93: BarcodeType
BT_CODE_128: BarcodeType
BT_DATABAR: BarcodeType
BT_DATABAR_EXPANDED: BarcodeType
BT_DATABAR_LIMITED: BarcodeType
BT_DATAMATRIX: BarcodeType
BT_EAN_8: BarcodeType
BT_EAN_13: BarcodeType
BT_EAN_13_WITH_ADDON_2: BarcodeType
BT_EAN_13_WITH_ADDON_5: BarcodeType
BT_GS1_DATAMATRIX: BarcodeType
BT_GS1_128: BarcodeType
BT_ISBT_128: BarcodeType
BT_ITF: BarcodeType
BT_ITF_14: BarcodeType
BT_MAXICODE: BarcodeType
BT_MICRO_QR_CODE: BarcodeType
BT_MSI: BarcodeType
BT_PDF417: BarcodeType
BT_QR_CODE: BarcodeType
BT_UPC_A: BarcodeType
BT_UPC_A_WITH_ADDON_2: BarcodeType
BT_UPC_A_WITH_ADDON_5: BarcodeType
BT_UPC_E: BarcodeType
BT_UPC_E_WITH_ADDON_2: BarcodeType
BT_UPC_E_WITH_ADDON_5: BarcodeType
RFT_REGULAR: ResultFieldType
RFT_MODEL_SUMMARY: ResultFieldType
RFT_DEBUG: ResultFieldType
UNDEFINED: DeviceType
CPU: DeviceType
GPU: DeviceType

class DefectAddress(_message.Message):
    __slots__ = ("dataset_index", "model_id", "feature_index", "overlap_area", "overlap_ratio", "overlap_ratio_of_other", "feature_uid")
    DATASET_INDEX_FIELD_NUMBER: _ClassVar[int]
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    FEATURE_INDEX_FIELD_NUMBER: _ClassVar[int]
    OVERLAP_AREA_FIELD_NUMBER: _ClassVar[int]
    OVERLAP_RATIO_FIELD_NUMBER: _ClassVar[int]
    OVERLAP_RATIO_OF_OTHER_FIELD_NUMBER: _ClassVar[int]
    FEATURE_UID_FIELD_NUMBER: _ClassVar[int]
    dataset_index: int
    model_id: int
    feature_index: int
    overlap_area: float
    overlap_ratio: float
    overlap_ratio_of_other: float
    feature_uid: str
    def __init__(self, dataset_index: _Optional[int] = ..., model_id: _Optional[int] = ..., feature_index: _Optional[int] = ..., overlap_area: _Optional[float] = ..., overlap_ratio: _Optional[float] = ..., overlap_ratio_of_other: _Optional[float] = ..., feature_uid: _Optional[str] = ...) -> None: ...

class RowRLC(_message.Message):
    __slots__ = ("offset_x", "offset_y", "length")
    OFFSET_X_FIELD_NUMBER: _ClassVar[int]
    OFFSET_Y_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    offset_x: int
    offset_y: int
    length: int
    def __init__(self, offset_x: _Optional[int] = ..., offset_y: _Optional[int] = ..., length: _Optional[int] = ...) -> None: ...

class OcrCharacter(_message.Message):
    __slots__ = ("character", "probability", "ignored")
    CHARACTER_FIELD_NUMBER: _ClassVar[int]
    PROBABILITY_FIELD_NUMBER: _ClassVar[int]
    IGNORED_FIELD_NUMBER: _ClassVar[int]
    character: str
    probability: float
    ignored: bool
    def __init__(self, character: _Optional[str] = ..., probability: _Optional[float] = ..., ignored: bool = ...) -> None: ...

class OcrCharacterPosition(_message.Message):
    __slots__ = ("ocr_character",)
    OCR_CHARACTER_FIELD_NUMBER: _ClassVar[int]
    ocr_character: _containers.RepeatedCompositeFieldContainer[OcrCharacter]
    def __init__(self, ocr_character: _Optional[_Iterable[_Union[OcrCharacter, _Mapping]]] = ...) -> None: ...

class Point(_message.Message):
    __slots__ = ("x", "y")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ...) -> None: ...

class PointInt(_message.Message):
    __slots__ = ("x", "y")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    x: int
    y: int
    def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ...) -> None: ...

class Contour(_message.Message):
    __slots__ = ("points",)
    POINTS_FIELD_NUMBER: _ClassVar[int]
    points: _containers.RepeatedCompositeFieldContainer[PointInt]
    def __init__(self, points: _Optional[_Iterable[_Union[PointInt, _Mapping]]] = ...) -> None: ...

class MinimalBoundingBox(_message.Message):
    __slots__ = ("center_x", "center_y", "width", "height", "angle")
    CENTER_X_FIELD_NUMBER: _ClassVar[int]
    CENTER_Y_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    ANGLE_FIELD_NUMBER: _ClassVar[int]
    center_x: float
    center_y: float
    width: float
    height: float
    angle: float
    def __init__(self, center_x: _Optional[float] = ..., center_y: _Optional[float] = ..., width: _Optional[float] = ..., height: _Optional[float] = ..., angle: _Optional[float] = ...) -> None: ...

class OrientedBoundingBox(_message.Message):
    __slots__ = ("center", "width", "height", "angle", "full_orientation")
    CENTER_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    ANGLE_FIELD_NUMBER: _ClassVar[int]
    FULL_ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    center: Point
    width: float
    height: float
    angle: float
    full_orientation: bool
    def __init__(self, center: _Optional[_Union[Point, _Mapping]] = ..., width: _Optional[float] = ..., height: _Optional[float] = ..., angle: _Optional[float] = ..., full_orientation: bool = ...) -> None: ...

class FeatureField(_message.Message):
    __slots__ = ("label", "show", "color", "rect_x", "rect_y", "rect_w", "rect_h", "probability", "area", "length", "width", "mean_gray", "max_gray", "min_gray", "in_area", "overlaps_with", "rect_x_mm", "rect_y_mm", "rect_w_mm", "rect_h_mm", "row_rlc", "ocr_character_position", "minimal_bounding_box", "minimal_bounding_box_point", "write_protected_label", "barcode_type", "barcode_raw_bytes", "oriented_bounding_box", "oriented_bounding_box_point", "segmentation_mask", "segmentation_contours")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    SHOW_FIELD_NUMBER: _ClassVar[int]
    COLOR_FIELD_NUMBER: _ClassVar[int]
    RECT_X_FIELD_NUMBER: _ClassVar[int]
    RECT_Y_FIELD_NUMBER: _ClassVar[int]
    RECT_W_FIELD_NUMBER: _ClassVar[int]
    RECT_H_FIELD_NUMBER: _ClassVar[int]
    PROBABILITY_FIELD_NUMBER: _ClassVar[int]
    AREA_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    MEAN_GRAY_FIELD_NUMBER: _ClassVar[int]
    MAX_GRAY_FIELD_NUMBER: _ClassVar[int]
    MIN_GRAY_FIELD_NUMBER: _ClassVar[int]
    IN_AREA_FIELD_NUMBER: _ClassVar[int]
    OVERLAPS_WITH_FIELD_NUMBER: _ClassVar[int]
    RECT_X_MM_FIELD_NUMBER: _ClassVar[int]
    RECT_Y_MM_FIELD_NUMBER: _ClassVar[int]
    RECT_W_MM_FIELD_NUMBER: _ClassVar[int]
    RECT_H_MM_FIELD_NUMBER: _ClassVar[int]
    ROW_RLC_FIELD_NUMBER: _ClassVar[int]
    OCR_CHARACTER_POSITION_FIELD_NUMBER: _ClassVar[int]
    MINIMAL_BOUNDING_BOX_FIELD_NUMBER: _ClassVar[int]
    MINIMAL_BOUNDING_BOX_POINT_FIELD_NUMBER: _ClassVar[int]
    WRITE_PROTECTED_LABEL_FIELD_NUMBER: _ClassVar[int]
    BARCODE_TYPE_FIELD_NUMBER: _ClassVar[int]
    BARCODE_RAW_BYTES_FIELD_NUMBER: _ClassVar[int]
    ORIENTED_BOUNDING_BOX_FIELD_NUMBER: _ClassVar[int]
    ORIENTED_BOUNDING_BOX_POINT_FIELD_NUMBER: _ClassVar[int]
    SEGMENTATION_MASK_FIELD_NUMBER: _ClassVar[int]
    SEGMENTATION_CONTOURS_FIELD_NUMBER: _ClassVar[int]
    label: str
    show: bool
    color: _containers.RepeatedScalarFieldContainer[int]
    rect_x: int
    rect_y: int
    rect_w: int
    rect_h: int
    probability: float
    area: float
    length: float
    width: float
    mean_gray: float
    max_gray: float
    min_gray: float
    in_area: _containers.RepeatedScalarFieldContainer[int]
    overlaps_with: _containers.RepeatedCompositeFieldContainer[DefectAddress]
    rect_x_mm: float
    rect_y_mm: float
    rect_w_mm: float
    rect_h_mm: float
    row_rlc: _containers.RepeatedCompositeFieldContainer[RowRLC]
    ocr_character_position: _containers.RepeatedCompositeFieldContainer[OcrCharacterPosition]
    minimal_bounding_box: MinimalBoundingBox
    minimal_bounding_box_point: _containers.RepeatedCompositeFieldContainer[Point]
    write_protected_label: bool
    barcode_type: BarcodeType
    barcode_raw_bytes: bytes
    oriented_bounding_box: OrientedBoundingBox
    oriented_bounding_box_point: _containers.RepeatedCompositeFieldContainer[Point]
    segmentation_mask: bytes
    segmentation_contours: _containers.RepeatedCompositeFieldContainer[Contour]
    def __init__(self, label: _Optional[str] = ..., show: bool = ..., color: _Optional[_Iterable[int]] = ..., rect_x: _Optional[int] = ..., rect_y: _Optional[int] = ..., rect_w: _Optional[int] = ..., rect_h: _Optional[int] = ..., probability: _Optional[float] = ..., area: _Optional[float] = ..., length: _Optional[float] = ..., width: _Optional[float] = ..., mean_gray: _Optional[float] = ..., max_gray: _Optional[float] = ..., min_gray: _Optional[float] = ..., in_area: _Optional[_Iterable[int]] = ..., overlaps_with: _Optional[_Iterable[_Union[DefectAddress, _Mapping]]] = ..., rect_x_mm: _Optional[float] = ..., rect_y_mm: _Optional[float] = ..., rect_w_mm: _Optional[float] = ..., rect_h_mm: _Optional[float] = ..., row_rlc: _Optional[_Iterable[_Union[RowRLC, _Mapping]]] = ..., ocr_character_position: _Optional[_Iterable[_Union[OcrCharacterPosition, _Mapping]]] = ..., minimal_bounding_box: _Optional[_Union[MinimalBoundingBox, _Mapping]] = ..., minimal_bounding_box_point: _Optional[_Iterable[_Union[Point, _Mapping]]] = ..., write_protected_label: bool = ..., barcode_type: _Optional[_Union[BarcodeType, str]] = ..., barcode_raw_bytes: _Optional[bytes] = ..., oriented_bounding_box: _Optional[_Union[OrientedBoundingBox, _Mapping]] = ..., oriented_bounding_box_point: _Optional[_Iterable[_Union[Point, _Mapping]]] = ..., segmentation_mask: _Optional[bytes] = ..., segmentation_contours: _Optional[_Iterable[_Union[Contour, _Mapping]]] = ...) -> None: ...

class MapField(_message.Message):
    __slots__ = ("label", "show", "color", "datatype", "image_w", "image_h", "image_c", "start_position", "end_position")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    SHOW_FIELD_NUMBER: _ClassVar[int]
    COLOR_FIELD_NUMBER: _ClassVar[int]
    DATATYPE_FIELD_NUMBER: _ClassVar[int]
    IMAGE_W_FIELD_NUMBER: _ClassVar[int]
    IMAGE_H_FIELD_NUMBER: _ClassVar[int]
    IMAGE_C_FIELD_NUMBER: _ClassVar[int]
    START_POSITION_FIELD_NUMBER: _ClassVar[int]
    END_POSITION_FIELD_NUMBER: _ClassVar[int]
    label: str
    show: bool
    color: _containers.RepeatedScalarFieldContainer[int]
    datatype: MapDataType
    image_w: int
    image_h: int
    image_c: int
    start_position: int
    end_position: int
    def __init__(self, label: _Optional[str] = ..., show: bool = ..., color: _Optional[_Iterable[int]] = ..., datatype: _Optional[_Union[MapDataType, str]] = ..., image_w: _Optional[int] = ..., image_h: _Optional[int] = ..., image_c: _Optional[int] = ..., start_position: _Optional[int] = ..., end_position: _Optional[int] = ...) -> None: ...

class ResultField(_message.Message):
    __slots__ = ("model_label", "model_tag", "model_id", "classifier", "evaluation_time_ms", "post_processing_time_ms", "result_map", "feature", "tenant", "tenant_id", "onnx_version_major", "onnx_version_minor", "feature_uid", "result_field_type")
    MODEL_LABEL_FIELD_NUMBER: _ClassVar[int]
    MODEL_TAG_FIELD_NUMBER: _ClassVar[int]
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    CLASSIFIER_FIELD_NUMBER: _ClassVar[int]
    EVALUATION_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    POST_PROCESSING_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    RESULT_MAP_FIELD_NUMBER: _ClassVar[int]
    FEATURE_FIELD_NUMBER: _ClassVar[int]
    TENANT_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    ONNX_VERSION_MAJOR_FIELD_NUMBER: _ClassVar[int]
    ONNX_VERSION_MINOR_FIELD_NUMBER: _ClassVar[int]
    FEATURE_UID_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_TYPE_FIELD_NUMBER: _ClassVar[int]
    model_label: str
    model_tag: str
    model_id: int
    classifier: float
    evaluation_time_ms: float
    post_processing_time_ms: float
    result_map: _containers.RepeatedCompositeFieldContainer[MapField]
    feature: _containers.RepeatedCompositeFieldContainer[FeatureField]
    tenant: str
    tenant_id: str
    onnx_version_major: int
    onnx_version_minor: int
    feature_uid: str
    result_field_type: ResultFieldType
    def __init__(self, model_label: _Optional[str] = ..., model_tag: _Optional[str] = ..., model_id: _Optional[int] = ..., classifier: _Optional[float] = ..., evaluation_time_ms: _Optional[float] = ..., post_processing_time_ms: _Optional[float] = ..., result_map: _Optional[_Iterable[_Union[MapField, _Mapping]]] = ..., feature: _Optional[_Iterable[_Union[FeatureField, _Mapping]]] = ..., tenant: _Optional[str] = ..., tenant_id: _Optional[str] = ..., onnx_version_major: _Optional[int] = ..., onnx_version_minor: _Optional[int] = ..., feature_uid: _Optional[str] = ..., result_field_type: _Optional[_Union[ResultFieldType, str]] = ...) -> None: ...

class Summary(_message.Message):
    __slots__ = ("image_class", "class_code", "most_relevant_defect", "relevant_defects_json", "feature_table_json")
    IMAGE_CLASS_FIELD_NUMBER: _ClassVar[int]
    CLASS_CODE_FIELD_NUMBER: _ClassVar[int]
    MOST_RELEVANT_DEFECT_FIELD_NUMBER: _ClassVar[int]
    RELEVANT_DEFECTS_JSON_FIELD_NUMBER: _ClassVar[int]
    FEATURE_TABLE_JSON_FIELD_NUMBER: _ClassVar[int]
    image_class: int
    class_code: str
    most_relevant_defect: str
    relevant_defects_json: str
    feature_table_json: str
    def __init__(self, image_class: _Optional[int] = ..., class_code: _Optional[str] = ..., most_relevant_defect: _Optional[str] = ..., relevant_defects_json: _Optional[str] = ..., feature_table_json: _Optional[str] = ...) -> None: ...

class FeatureInfo(_message.Message):
    __slots__ = ("feature_uid", "feature_name")
    FEATURE_UID_FIELD_NUMBER: _ClassVar[int]
    FEATURE_NAME_FIELD_NUMBER: _ClassVar[int]
    feature_uid: str
    feature_name: str
    def __init__(self, feature_uid: _Optional[str] = ..., feature_name: _Optional[str] = ...) -> None: ...

class ModelInfo(_message.Message):
    __slots__ = ("model_uid", "model_name", "features", "tenant", "tenant_uid", "onnx_version_major", "onnx_version_minor", "model_type", "model_output_type")
    MODEL_UID_FIELD_NUMBER: _ClassVar[int]
    MODEL_NAME_FIELD_NUMBER: _ClassVar[int]
    FEATURES_FIELD_NUMBER: _ClassVar[int]
    TENANT_FIELD_NUMBER: _ClassVar[int]
    TENANT_UID_FIELD_NUMBER: _ClassVar[int]
    ONNX_VERSION_MAJOR_FIELD_NUMBER: _ClassVar[int]
    ONNX_VERSION_MINOR_FIELD_NUMBER: _ClassVar[int]
    MODEL_TYPE_FIELD_NUMBER: _ClassVar[int]
    MODEL_OUTPUT_TYPE_FIELD_NUMBER: _ClassVar[int]
    model_uid: str
    model_name: str
    features: _containers.RepeatedCompositeFieldContainer[FeatureInfo]
    tenant: str
    tenant_uid: str
    onnx_version_major: int
    onnx_version_minor: int
    model_type: ModelType
    model_output_type: ModelOutputType
    def __init__(self, model_uid: _Optional[str] = ..., model_name: _Optional[str] = ..., features: _Optional[_Iterable[_Union[FeatureInfo, _Mapping]]] = ..., tenant: _Optional[str] = ..., tenant_uid: _Optional[str] = ..., onnx_version_major: _Optional[int] = ..., onnx_version_minor: _Optional[int] = ..., model_type: _Optional[_Union[ModelType, str]] = ..., model_output_type: _Optional[_Union[ModelOutputType, str]] = ...) -> None: ...

class Results(_message.Message):
    __slots__ = ("output", "original_image_w", "original_image_h", "original_image_c", "original_image_w_mm", "original_image_h_mm", "original_image_c_mm", "mean_gray_active_area", "result_summary", "min_gray_active_area", "max_gray_active_area", "available_models")
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_IMAGE_W_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_IMAGE_H_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_IMAGE_C_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_IMAGE_W_MM_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_IMAGE_H_MM_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_IMAGE_C_MM_FIELD_NUMBER: _ClassVar[int]
    MEAN_GRAY_ACTIVE_AREA_FIELD_NUMBER: _ClassVar[int]
    RESULT_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    MIN_GRAY_ACTIVE_AREA_FIELD_NUMBER: _ClassVar[int]
    MAX_GRAY_ACTIVE_AREA_FIELD_NUMBER: _ClassVar[int]
    AVAILABLE_MODELS_FIELD_NUMBER: _ClassVar[int]
    output: _containers.RepeatedCompositeFieldContainer[ResultField]
    original_image_w: int
    original_image_h: int
    original_image_c: int
    original_image_w_mm: float
    original_image_h_mm: float
    original_image_c_mm: float
    mean_gray_active_area: float
    result_summary: Summary
    min_gray_active_area: float
    max_gray_active_area: float
    available_models: _containers.RepeatedCompositeFieldContainer[ModelInfo]
    def __init__(self, output: _Optional[_Iterable[_Union[ResultField, _Mapping]]] = ..., original_image_w: _Optional[int] = ..., original_image_h: _Optional[int] = ..., original_image_c: _Optional[int] = ..., original_image_w_mm: _Optional[float] = ..., original_image_h_mm: _Optional[float] = ..., original_image_c_mm: _Optional[float] = ..., mean_gray_active_area: _Optional[float] = ..., result_summary: _Optional[_Union[Summary, _Mapping]] = ..., min_gray_active_area: _Optional[float] = ..., max_gray_active_area: _Optional[float] = ..., available_models: _Optional[_Iterable[_Union[ModelInfo, _Mapping]]] = ...) -> None: ...

class ModelOptions(_message.Message):
    __slots__ = ("deactivated", "minSegmentationThreshold", "minGrayValue", "maxGrayValue", "maxMeanGrayValue", "minProbability", "minLength", "minWidth", "minHeight", "minArea", "minImageClassifier", "deepGrayLevel", "priority", "onlyBoundingBoxes")
    DEACTIVATED_FIELD_NUMBER: _ClassVar[int]
    MINSEGMENTATIONTHRESHOLD_FIELD_NUMBER: _ClassVar[int]
    MINGRAYVALUE_FIELD_NUMBER: _ClassVar[int]
    MAXGRAYVALUE_FIELD_NUMBER: _ClassVar[int]
    MAXMEANGRAYVALUE_FIELD_NUMBER: _ClassVar[int]
    MINPROBABILITY_FIELD_NUMBER: _ClassVar[int]
    MINLENGTH_FIELD_NUMBER: _ClassVar[int]
    MINWIDTH_FIELD_NUMBER: _ClassVar[int]
    MINHEIGHT_FIELD_NUMBER: _ClassVar[int]
    MINAREA_FIELD_NUMBER: _ClassVar[int]
    MINIMAGECLASSIFIER_FIELD_NUMBER: _ClassVar[int]
    DEEPGRAYLEVEL_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    ONLYBOUNDINGBOXES_FIELD_NUMBER: _ClassVar[int]
    deactivated: bool
    minSegmentationThreshold: float
    minGrayValue: float
    maxGrayValue: float
    maxMeanGrayValue: float
    minProbability: float
    minLength: float
    minWidth: float
    minHeight: float
    minArea: float
    minImageClassifier: float
    deepGrayLevel: float
    priority: int
    onlyBoundingBoxes: bool
    def __init__(self, deactivated: bool = ..., minSegmentationThreshold: _Optional[float] = ..., minGrayValue: _Optional[float] = ..., maxGrayValue: _Optional[float] = ..., maxMeanGrayValue: _Optional[float] = ..., minProbability: _Optional[float] = ..., minLength: _Optional[float] = ..., minWidth: _Optional[float] = ..., minHeight: _Optional[float] = ..., minArea: _Optional[float] = ..., minImageClassifier: _Optional[float] = ..., deepGrayLevel: _Optional[float] = ..., priority: _Optional[int] = ..., onlyBoundingBoxes: bool = ...) -> None: ...

class OptionContainer(_message.Message):
    __slots__ = ("options", "divisor_w", "divisor_h", "batch_size", "network_img_prescaling_w", "network_img_prescaling_h", "network_img_prescaling_c", "border_w", "border_h", "border_w_r", "border_h_b", "cells_w", "cells_h")
    class OptionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: ModelOptions
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[ModelOptions, _Mapping]] = ...) -> None: ...
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    DIVISOR_W_FIELD_NUMBER: _ClassVar[int]
    DIVISOR_H_FIELD_NUMBER: _ClassVar[int]
    BATCH_SIZE_FIELD_NUMBER: _ClassVar[int]
    NETWORK_IMG_PRESCALING_W_FIELD_NUMBER: _ClassVar[int]
    NETWORK_IMG_PRESCALING_H_FIELD_NUMBER: _ClassVar[int]
    NETWORK_IMG_PRESCALING_C_FIELD_NUMBER: _ClassVar[int]
    BORDER_W_FIELD_NUMBER: _ClassVar[int]
    BORDER_H_FIELD_NUMBER: _ClassVar[int]
    BORDER_W_R_FIELD_NUMBER: _ClassVar[int]
    BORDER_H_B_FIELD_NUMBER: _ClassVar[int]
    CELLS_W_FIELD_NUMBER: _ClassVar[int]
    CELLS_H_FIELD_NUMBER: _ClassVar[int]
    options: _containers.MessageMap[int, ModelOptions]
    divisor_w: int
    divisor_h: int
    batch_size: int
    network_img_prescaling_w: int
    network_img_prescaling_h: int
    network_img_prescaling_c: int
    border_w: int
    border_h: int
    border_w_r: int
    border_h_b: int
    cells_w: int
    cells_h: int
    def __init__(self, options: _Optional[_Mapping[int, ModelOptions]] = ..., divisor_w: _Optional[int] = ..., divisor_h: _Optional[int] = ..., batch_size: _Optional[int] = ..., network_img_prescaling_w: _Optional[int] = ..., network_img_prescaling_h: _Optional[int] = ..., network_img_prescaling_c: _Optional[int] = ..., border_w: _Optional[int] = ..., border_h: _Optional[int] = ..., border_w_r: _Optional[int] = ..., border_h_b: _Optional[int] = ..., cells_w: _Optional[int] = ..., cells_h: _Optional[int] = ...) -> None: ...

class Device(_message.Message):
    __slots__ = ("device_id", "type", "name", "memory_size", "integrated", "cuda_uuid", "cuda_compute_capability_major", "cuda_compute_capability_minor")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    MEMORY_SIZE_FIELD_NUMBER: _ClassVar[int]
    INTEGRATED_FIELD_NUMBER: _ClassVar[int]
    CUDA_UUID_FIELD_NUMBER: _ClassVar[int]
    CUDA_COMPUTE_CAPABILITY_MAJOR_FIELD_NUMBER: _ClassVar[int]
    CUDA_COMPUTE_CAPABILITY_MINOR_FIELD_NUMBER: _ClassVar[int]
    device_id: int
    type: DeviceType
    name: str
    memory_size: int
    integrated: bool
    cuda_uuid: str
    cuda_compute_capability_major: int
    cuda_compute_capability_minor: int
    def __init__(self, device_id: _Optional[int] = ..., type: _Optional[_Union[DeviceType, str]] = ..., name: _Optional[str] = ..., memory_size: _Optional[int] = ..., integrated: bool = ..., cuda_uuid: _Optional[str] = ..., cuda_compute_capability_major: _Optional[int] = ..., cuda_compute_capability_minor: _Optional[int] = ...) -> None: ...

class DeviceInformation(_message.Message):
    __slots__ = ("device",)
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    device: _containers.RepeatedCompositeFieldContainer[Device]
    def __init__(self, device: _Optional[_Iterable[_Union[Device, _Mapping]]] = ...) -> None: ...
