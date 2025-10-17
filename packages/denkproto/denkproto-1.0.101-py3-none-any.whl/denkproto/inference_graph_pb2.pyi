import modelfile_v2_pb2 as _modelfile_v2_pb2
import validate_pb2 as _validate_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExecutionProvider(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CPU: _ClassVar[ExecutionProvider]
    CUDA: _ClassVar[ExecutionProvider]
    DIRECTML: _ClassVar[ExecutionProvider]
    TENSORRT: _ClassVar[ExecutionProvider]
CPU: ExecutionProvider
CUDA: ExecutionProvider
DIRECTML: ExecutionProvider
TENSORRT: ExecutionProvider

class ModelSource(_message.Message):
    __slots__ = ("from_proto", "from_network_id", "from_network_experiment_id")
    FROM_PROTO_FIELD_NUMBER: _ClassVar[int]
    FROM_NETWORK_ID_FIELD_NUMBER: _ClassVar[int]
    FROM_NETWORK_EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
    from_proto: _modelfile_v2_pb2.ModelFile
    from_network_id: str
    from_network_experiment_id: str
    def __init__(self, from_proto: _Optional[_Union[_modelfile_v2_pb2.ModelFile, _Mapping]] = ..., from_network_id: _Optional[str] = ..., from_network_experiment_id: _Optional[str] = ...) -> None: ...

class SessionInfo(_message.Message):
    __slots__ = ("execution_provider", "device_id")
    EXECUTION_PROVIDER_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    execution_provider: ExecutionProvider
    device_id: int
    def __init__(self, execution_provider: _Optional[_Union[ExecutionProvider, str]] = ..., device_id: _Optional[int] = ...) -> None: ...

class ConstTensorNode(_message.Message):
    __slots__ = ("name", "shape", "uint64_data", "int64_data", "float64_data", "output_port_name")
    class Uint64Array(_message.Message):
        __slots__ = ("data",)
        DATA_FIELD_NUMBER: _ClassVar[int]
        data: _containers.RepeatedScalarFieldContainer[int]
        def __init__(self, data: _Optional[_Iterable[int]] = ...) -> None: ...
    class Int64Array(_message.Message):
        __slots__ = ("data",)
        DATA_FIELD_NUMBER: _ClassVar[int]
        data: _containers.RepeatedScalarFieldContainer[int]
        def __init__(self, data: _Optional[_Iterable[int]] = ...) -> None: ...
    class Float64Array(_message.Message):
        __slots__ = ("data",)
        DATA_FIELD_NUMBER: _ClassVar[int]
        data: _containers.RepeatedScalarFieldContainer[float]
        def __init__(self, data: _Optional[_Iterable[float]] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    UINT64_DATA_FIELD_NUMBER: _ClassVar[int]
    INT64_DATA_FIELD_NUMBER: _ClassVar[int]
    FLOAT64_DATA_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_PORT_NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    shape: _containers.RepeatedScalarFieldContainer[int]
    uint64_data: ConstTensorNode.Uint64Array
    int64_data: ConstTensorNode.Int64Array
    float64_data: ConstTensorNode.Float64Array
    output_port_name: str
    def __init__(self, name: _Optional[str] = ..., shape: _Optional[_Iterable[int]] = ..., uint64_data: _Optional[_Union[ConstTensorNode.Uint64Array, _Mapping]] = ..., int64_data: _Optional[_Union[ConstTensorNode.Int64Array, _Mapping]] = ..., float64_data: _Optional[_Union[ConstTensorNode.Float64Array, _Mapping]] = ..., output_port_name: _Optional[str] = ...) -> None: ...

class ImageResizeNode(_message.Message):
    __slots__ = ("name", "input_size", "input_image", "output_port_name", "session_info")
    NAME_FIELD_NUMBER: _ClassVar[int]
    INPUT_SIZE_FIELD_NUMBER: _ClassVar[int]
    INPUT_IMAGE_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_PORT_NAME_FIELD_NUMBER: _ClassVar[int]
    SESSION_INFO_FIELD_NUMBER: _ClassVar[int]
    name: str
    input_size: str
    input_image: str
    output_port_name: str
    session_info: SessionInfo
    def __init__(self, name: _Optional[str] = ..., input_size: _Optional[str] = ..., input_image: _Optional[str] = ..., output_port_name: _Optional[str] = ..., session_info: _Optional[_Union[SessionInfo, _Mapping]] = ...) -> None: ...

class ImagePatchesNode(_message.Message):
    __slots__ = ("name", "input_image", "input_bounding_boxes", "input_target_size", "output_port_name", "session_info")
    class TargetSizeSource(_message.Message):
        __slots__ = ("topic", "size")
        class ImageSize(_message.Message):
            __slots__ = ("height", "width")
            HEIGHT_FIELD_NUMBER: _ClassVar[int]
            WIDTH_FIELD_NUMBER: _ClassVar[int]
            height: int
            width: int
            def __init__(self, height: _Optional[int] = ..., width: _Optional[int] = ...) -> None: ...
        TOPIC_FIELD_NUMBER: _ClassVar[int]
        SIZE_FIELD_NUMBER: _ClassVar[int]
        topic: str
        size: ImagePatchesNode.TargetSizeSource.ImageSize
        def __init__(self, topic: _Optional[str] = ..., size: _Optional[_Union[ImagePatchesNode.TargetSizeSource.ImageSize, _Mapping]] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    INPUT_IMAGE_FIELD_NUMBER: _ClassVar[int]
    INPUT_BOUNDING_BOXES_FIELD_NUMBER: _ClassVar[int]
    INPUT_TARGET_SIZE_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_PORT_NAME_FIELD_NUMBER: _ClassVar[int]
    SESSION_INFO_FIELD_NUMBER: _ClassVar[int]
    name: str
    input_image: str
    input_bounding_boxes: str
    input_target_size: ImagePatchesNode.TargetSizeSource
    output_port_name: str
    session_info: SessionInfo
    def __init__(self, name: _Optional[str] = ..., input_image: _Optional[str] = ..., input_bounding_boxes: _Optional[str] = ..., input_target_size: _Optional[_Union[ImagePatchesNode.TargetSizeSource, _Mapping]] = ..., output_port_name: _Optional[str] = ..., session_info: _Optional[_Union[SessionInfo, _Mapping]] = ...) -> None: ...

class VirtualCameraNode(_message.Message):
    __slots__ = ("name", "path", "output_port_name")
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_PORT_NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    path: str
    output_port_name: str
    def __init__(self, name: _Optional[str] = ..., path: _Optional[str] = ..., output_port_name: _Optional[str] = ...) -> None: ...

class ImageClassificationNode(_message.Message):
    __slots__ = ("name", "input_image", "model_source", "output_port_name", "session_info")
    NAME_FIELD_NUMBER: _ClassVar[int]
    INPUT_IMAGE_FIELD_NUMBER: _ClassVar[int]
    MODEL_SOURCE_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_PORT_NAME_FIELD_NUMBER: _ClassVar[int]
    SESSION_INFO_FIELD_NUMBER: _ClassVar[int]
    name: str
    input_image: str
    model_source: ModelSource
    output_port_name: str
    session_info: SessionInfo
    def __init__(self, name: _Optional[str] = ..., input_image: _Optional[str] = ..., model_source: _Optional[_Union[ModelSource, _Mapping]] = ..., output_port_name: _Optional[str] = ..., session_info: _Optional[_Union[SessionInfo, _Mapping]] = ...) -> None: ...

class ImageObjectDetectionNode(_message.Message):
    __slots__ = ("name", "input_image", "model_source", "scale_bounding_boxes", "output_port_name", "session_info")
    NAME_FIELD_NUMBER: _ClassVar[int]
    INPUT_IMAGE_FIELD_NUMBER: _ClassVar[int]
    MODEL_SOURCE_FIELD_NUMBER: _ClassVar[int]
    SCALE_BOUNDING_BOXES_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_PORT_NAME_FIELD_NUMBER: _ClassVar[int]
    SESSION_INFO_FIELD_NUMBER: _ClassVar[int]
    name: str
    input_image: str
    model_source: ModelSource
    scale_bounding_boxes: bool
    output_port_name: str
    session_info: SessionInfo
    def __init__(self, name: _Optional[str] = ..., input_image: _Optional[str] = ..., model_source: _Optional[_Union[ModelSource, _Mapping]] = ..., scale_bounding_boxes: bool = ..., output_port_name: _Optional[str] = ..., session_info: _Optional[_Union[SessionInfo, _Mapping]] = ...) -> None: ...

class ImageOcrNode(_message.Message):
    __slots__ = ("name", "input_image", "model_source", "output_port_name", "session_info")
    NAME_FIELD_NUMBER: _ClassVar[int]
    INPUT_IMAGE_FIELD_NUMBER: _ClassVar[int]
    MODEL_SOURCE_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_PORT_NAME_FIELD_NUMBER: _ClassVar[int]
    SESSION_INFO_FIELD_NUMBER: _ClassVar[int]
    name: str
    input_image: str
    model_source: ModelSource
    output_port_name: str
    session_info: SessionInfo
    def __init__(self, name: _Optional[str] = ..., input_image: _Optional[str] = ..., model_source: _Optional[_Union[ModelSource, _Mapping]] = ..., output_port_name: _Optional[str] = ..., session_info: _Optional[_Union[SessionInfo, _Mapping]] = ...) -> None: ...

class ImageSegmentationNode(_message.Message):
    __slots__ = ("name", "input_image", "model_source", "output_port_name", "session_info")
    NAME_FIELD_NUMBER: _ClassVar[int]
    INPUT_IMAGE_FIELD_NUMBER: _ClassVar[int]
    MODEL_SOURCE_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_PORT_NAME_FIELD_NUMBER: _ClassVar[int]
    SESSION_INFO_FIELD_NUMBER: _ClassVar[int]
    name: str
    input_image: str
    model_source: ModelSource
    output_port_name: str
    session_info: SessionInfo
    def __init__(self, name: _Optional[str] = ..., input_image: _Optional[str] = ..., model_source: _Optional[_Union[ModelSource, _Mapping]] = ..., output_port_name: _Optional[str] = ..., session_info: _Optional[_Union[SessionInfo, _Mapping]] = ...) -> None: ...

class ImageInstanceSegmentationNode(_message.Message):
    __slots__ = ("name", "input_image", "model_source", "output_bounding_boxes", "output_segmentations", "session_info")
    NAME_FIELD_NUMBER: _ClassVar[int]
    INPUT_IMAGE_FIELD_NUMBER: _ClassVar[int]
    MODEL_SOURCE_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_BOUNDING_BOXES_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_SEGMENTATIONS_FIELD_NUMBER: _ClassVar[int]
    SESSION_INFO_FIELD_NUMBER: _ClassVar[int]
    name: str
    input_image: str
    model_source: ModelSource
    output_bounding_boxes: str
    output_segmentations: str
    session_info: SessionInfo
    def __init__(self, name: _Optional[str] = ..., input_image: _Optional[str] = ..., model_source: _Optional[_Union[ModelSource, _Mapping]] = ..., output_bounding_boxes: _Optional[str] = ..., output_segmentations: _Optional[str] = ..., session_info: _Optional[_Union[SessionInfo, _Mapping]] = ...) -> None: ...

class ImageAnomalyDetectionNode(_message.Message):
    __slots__ = ("name", "input_image", "model_source", "output_anomaly_scores", "output_segmentations", "session_info")
    NAME_FIELD_NUMBER: _ClassVar[int]
    INPUT_IMAGE_FIELD_NUMBER: _ClassVar[int]
    MODEL_SOURCE_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_ANOMALY_SCORES_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_SEGMENTATIONS_FIELD_NUMBER: _ClassVar[int]
    SESSION_INFO_FIELD_NUMBER: _ClassVar[int]
    name: str
    input_image: str
    model_source: ModelSource
    output_anomaly_scores: str
    output_segmentations: str
    session_info: SessionInfo
    def __init__(self, name: _Optional[str] = ..., input_image: _Optional[str] = ..., model_source: _Optional[_Union[ModelSource, _Mapping]] = ..., output_anomaly_scores: _Optional[str] = ..., output_segmentations: _Optional[str] = ..., session_info: _Optional[_Union[SessionInfo, _Mapping]] = ...) -> None: ...

class BoundingBoxFilterNode(_message.Message):
    __slots__ = ("name", "input_bounding_boxes", "output_port_name", "input_score_threshold", "input_iou_threshold", "session_info")
    class ThresholdSource(_message.Message):
        __slots__ = ("topic", "value")
        TOPIC_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        topic: str
        value: float
        def __init__(self, topic: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    INPUT_BOUNDING_BOXES_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_PORT_NAME_FIELD_NUMBER: _ClassVar[int]
    INPUT_SCORE_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    INPUT_IOU_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    SESSION_INFO_FIELD_NUMBER: _ClassVar[int]
    name: str
    input_bounding_boxes: str
    output_port_name: str
    input_score_threshold: BoundingBoxFilterNode.ThresholdSource
    input_iou_threshold: BoundingBoxFilterNode.ThresholdSource
    session_info: SessionInfo
    def __init__(self, name: _Optional[str] = ..., input_bounding_boxes: _Optional[str] = ..., output_port_name: _Optional[str] = ..., input_score_threshold: _Optional[_Union[BoundingBoxFilterNode.ThresholdSource, _Mapping]] = ..., input_iou_threshold: _Optional[_Union[BoundingBoxFilterNode.ThresholdSource, _Mapping]] = ..., session_info: _Optional[_Union[SessionInfo, _Mapping]] = ...) -> None: ...

class Node(_message.Message):
    __slots__ = ("const_tensor_node", "image_resize_node", "image_patches_node", "virtual_camera_node", "image_classification_node", "image_object_detection_node", "image_ocr_node", "bounding_box_filter_node", "image_segmentation_node", "image_instance_segmentation_node", "image_anomaly_detection_node")
    CONST_TENSOR_NODE_FIELD_NUMBER: _ClassVar[int]
    IMAGE_RESIZE_NODE_FIELD_NUMBER: _ClassVar[int]
    IMAGE_PATCHES_NODE_FIELD_NUMBER: _ClassVar[int]
    VIRTUAL_CAMERA_NODE_FIELD_NUMBER: _ClassVar[int]
    IMAGE_CLASSIFICATION_NODE_FIELD_NUMBER: _ClassVar[int]
    IMAGE_OBJECT_DETECTION_NODE_FIELD_NUMBER: _ClassVar[int]
    IMAGE_OCR_NODE_FIELD_NUMBER: _ClassVar[int]
    BOUNDING_BOX_FILTER_NODE_FIELD_NUMBER: _ClassVar[int]
    IMAGE_SEGMENTATION_NODE_FIELD_NUMBER: _ClassVar[int]
    IMAGE_INSTANCE_SEGMENTATION_NODE_FIELD_NUMBER: _ClassVar[int]
    IMAGE_ANOMALY_DETECTION_NODE_FIELD_NUMBER: _ClassVar[int]
    const_tensor_node: ConstTensorNode
    image_resize_node: ImageResizeNode
    image_patches_node: ImagePatchesNode
    virtual_camera_node: VirtualCameraNode
    image_classification_node: ImageClassificationNode
    image_object_detection_node: ImageObjectDetectionNode
    image_ocr_node: ImageOcrNode
    bounding_box_filter_node: BoundingBoxFilterNode
    image_segmentation_node: ImageSegmentationNode
    image_instance_segmentation_node: ImageInstanceSegmentationNode
    image_anomaly_detection_node: ImageAnomalyDetectionNode
    def __init__(self, const_tensor_node: _Optional[_Union[ConstTensorNode, _Mapping]] = ..., image_resize_node: _Optional[_Union[ImageResizeNode, _Mapping]] = ..., image_patches_node: _Optional[_Union[ImagePatchesNode, _Mapping]] = ..., virtual_camera_node: _Optional[_Union[VirtualCameraNode, _Mapping]] = ..., image_classification_node: _Optional[_Union[ImageClassificationNode, _Mapping]] = ..., image_object_detection_node: _Optional[_Union[ImageObjectDetectionNode, _Mapping]] = ..., image_ocr_node: _Optional[_Union[ImageOcrNode, _Mapping]] = ..., bounding_box_filter_node: _Optional[_Union[BoundingBoxFilterNode, _Mapping]] = ..., image_segmentation_node: _Optional[_Union[ImageSegmentationNode, _Mapping]] = ..., image_instance_segmentation_node: _Optional[_Union[ImageInstanceSegmentationNode, _Mapping]] = ..., image_anomaly_detection_node: _Optional[_Union[ImageAnomalyDetectionNode, _Mapping]] = ...) -> None: ...

class Graph(_message.Message):
    __slots__ = ("nodes", "created_at", "license_id")
    NODES_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    LICENSE_ID_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[Node]
    created_at: int
    license_id: str
    def __init__(self, nodes: _Optional[_Iterable[_Union[Node, _Mapping]]] = ..., created_at: _Optional[int] = ..., license_id: _Optional[str] = ...) -> None: ...
