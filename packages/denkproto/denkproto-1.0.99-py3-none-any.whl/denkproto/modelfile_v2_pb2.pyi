import validate_pb2 as _validate_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ModelFile(_message.Message):
    __slots__ = ("protocol_version", "created_at", "file_info", "file_content", "class_labels", "inputs", "outputs")
    class Version(_message.Message):
        __slots__ = ("major", "minor", "patch")
        MAJOR_FIELD_NUMBER: _ClassVar[int]
        MINOR_FIELD_NUMBER: _ClassVar[int]
        PATCH_FIELD_NUMBER: _ClassVar[int]
        major: int
        minor: int
        patch: int
        def __init__(self, major: _Optional[int] = ..., minor: _Optional[int] = ..., patch: _Optional[int] = ...) -> None: ...
    class Content(_message.Message):
        __slots__ = ("byte_content", "hash_sha256", "compression_method", "encryption_method", "key_slots")
        class CompressionMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            CM_NONE: _ClassVar[ModelFile.Content.CompressionMethod]
        CM_NONE: ModelFile.Content.CompressionMethod
        class EncryptionMethod(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            EM_NONE: _ClassVar[ModelFile.Content.EncryptionMethod]
            EM_AES_GCM: _ClassVar[ModelFile.Content.EncryptionMethod]
        EM_NONE: ModelFile.Content.EncryptionMethod
        EM_AES_GCM: ModelFile.Content.EncryptionMethod
        class KeySlot(_message.Message):
            __slots__ = ("wrapped_key", "wrapping_method")
            WRAPPED_KEY_FIELD_NUMBER: _ClassVar[int]
            WRAPPING_METHOD_FIELD_NUMBER: _ClassVar[int]
            wrapped_key: bytes
            wrapping_method: ModelFile.Content.EncryptionMethod
            def __init__(self, wrapped_key: _Optional[bytes] = ..., wrapping_method: _Optional[_Union[ModelFile.Content.EncryptionMethod, str]] = ...) -> None: ...
        class KeySlotsEntry(_message.Message):
            __slots__ = ("key", "value")
            KEY_FIELD_NUMBER: _ClassVar[int]
            VALUE_FIELD_NUMBER: _ClassVar[int]
            key: str
            value: ModelFile.Content.KeySlot
            def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[ModelFile.Content.KeySlot, _Mapping]] = ...) -> None: ...
        BYTE_CONTENT_FIELD_NUMBER: _ClassVar[int]
        HASH_SHA256_FIELD_NUMBER: _ClassVar[int]
        COMPRESSION_METHOD_FIELD_NUMBER: _ClassVar[int]
        ENCRYPTION_METHOD_FIELD_NUMBER: _ClassVar[int]
        KEY_SLOTS_FIELD_NUMBER: _ClassVar[int]
        byte_content: bytes
        hash_sha256: bytes
        compression_method: ModelFile.Content.CompressionMethod
        encryption_method: ModelFile.Content.EncryptionMethod
        key_slots: _containers.MessageMap[str, ModelFile.Content.KeySlot]
        def __init__(self, byte_content: _Optional[bytes] = ..., hash_sha256: _Optional[bytes] = ..., compression_method: _Optional[_Union[ModelFile.Content.CompressionMethod, str]] = ..., encryption_method: _Optional[_Union[ModelFile.Content.EncryptionMethod, str]] = ..., key_slots: _Optional[_Mapping[str, ModelFile.Content.KeySlot]] = ...) -> None: ...
    class ClassLabel(_message.Message):
        __slots__ = ("class_label_id", "name", "short_name", "color")
        CLASS_LABEL_ID_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        SHORT_NAME_FIELD_NUMBER: _ClassVar[int]
        COLOR_FIELD_NUMBER: _ClassVar[int]
        class_label_id: str
        name: str
        short_name: str
        color: str
        def __init__(self, class_label_id: _Optional[str] = ..., name: _Optional[str] = ..., short_name: _Optional[str] = ..., color: _Optional[str] = ...) -> None: ...
    class ImageSize(_message.Message):
        __slots__ = ("width", "height", "channels")
        WIDTH_FIELD_NUMBER: _ClassVar[int]
        HEIGHT_FIELD_NUMBER: _ClassVar[int]
        CHANNELS_FIELD_NUMBER: _ClassVar[int]
        width: int
        height: int
        channels: int
        def __init__(self, width: _Optional[int] = ..., height: _Optional[int] = ..., channels: _Optional[int] = ...) -> None: ...
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
    class Input(_message.Message):
        __slots__ = ("input_name", "image_format")
        class ImageInputFormat(_message.Message):
            __slots__ = ("exact_image_size", "divisible_image_size", "region_of_interest")
            class ExactImageSizeRequirement(_message.Message):
                __slots__ = ("image_size",)
                IMAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
                image_size: ModelFile.ImageSize
                def __init__(self, image_size: _Optional[_Union[ModelFile.ImageSize, _Mapping]] = ...) -> None: ...
            class DivisibleImageSizeRequirement(_message.Message):
                __slots__ = ("image_size_divisors", "minimum_image_size", "suggested_image_size")
                IMAGE_SIZE_DIVISORS_FIELD_NUMBER: _ClassVar[int]
                MINIMUM_IMAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
                SUGGESTED_IMAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
                image_size_divisors: ModelFile.ImageSize
                minimum_image_size: ModelFile.ImageSize
                suggested_image_size: ModelFile.ImageSize
                def __init__(self, image_size_divisors: _Optional[_Union[ModelFile.ImageSize, _Mapping]] = ..., minimum_image_size: _Optional[_Union[ModelFile.ImageSize, _Mapping]] = ..., suggested_image_size: _Optional[_Union[ModelFile.ImageSize, _Mapping]] = ...) -> None: ...
            EXACT_IMAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
            DIVISIBLE_IMAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
            REGION_OF_INTEREST_FIELD_NUMBER: _ClassVar[int]
            exact_image_size: ModelFile.Input.ImageInputFormat.ExactImageSizeRequirement
            divisible_image_size: ModelFile.Input.ImageInputFormat.DivisibleImageSizeRequirement
            region_of_interest: ModelFile.RegionFromEdge
            def __init__(self, exact_image_size: _Optional[_Union[ModelFile.Input.ImageInputFormat.ExactImageSizeRequirement, _Mapping]] = ..., divisible_image_size: _Optional[_Union[ModelFile.Input.ImageInputFormat.DivisibleImageSizeRequirement, _Mapping]] = ..., region_of_interest: _Optional[_Union[ModelFile.RegionFromEdge, _Mapping]] = ...) -> None: ...
        INPUT_NAME_FIELD_NUMBER: _ClassVar[int]
        IMAGE_FORMAT_FIELD_NUMBER: _ClassVar[int]
        input_name: str
        image_format: ModelFile.Input.ImageInputFormat
        def __init__(self, input_name: _Optional[str] = ..., image_format: _Optional[_Union[ModelFile.Input.ImageInputFormat, _Mapping]] = ...) -> None: ...
    class Output(_message.Message):
        __slots__ = ("output_name", "scalar_format", "segmentation_maps_format", "bounding_boxes_format", "bounding_box_segmentations_format", "ocr_format")
        class ScalarOutputFormat(_message.Message):
            __slots__ = ()
            def __init__(self) -> None: ...
        class SegmentationMapsOutputFormat(_message.Message):
            __slots__ = ()
            def __init__(self) -> None: ...
        class BoundingBoxesOutputFormat(_message.Message):
            __slots__ = ("x1_offset", "y1_offset", "x2_offset", "y2_offset", "confidence_offset", "class_label_index_offset", "angle_offset")
            X1_OFFSET_FIELD_NUMBER: _ClassVar[int]
            Y1_OFFSET_FIELD_NUMBER: _ClassVar[int]
            X2_OFFSET_FIELD_NUMBER: _ClassVar[int]
            Y2_OFFSET_FIELD_NUMBER: _ClassVar[int]
            CONFIDENCE_OFFSET_FIELD_NUMBER: _ClassVar[int]
            CLASS_LABEL_INDEX_OFFSET_FIELD_NUMBER: _ClassVar[int]
            ANGLE_OFFSET_FIELD_NUMBER: _ClassVar[int]
            x1_offset: int
            y1_offset: int
            x2_offset: int
            y2_offset: int
            confidence_offset: int
            class_label_index_offset: int
            angle_offset: int
            def __init__(self, x1_offset: _Optional[int] = ..., y1_offset: _Optional[int] = ..., x2_offset: _Optional[int] = ..., y2_offset: _Optional[int] = ..., confidence_offset: _Optional[int] = ..., class_label_index_offset: _Optional[int] = ..., angle_offset: _Optional[int] = ...) -> None: ...
        class BoundingBoxSegmentationsOutputFormat(_message.Message):
            __slots__ = ("relative_to_bounding_box",)
            RELATIVE_TO_BOUNDING_BOX_FIELD_NUMBER: _ClassVar[int]
            relative_to_bounding_box: bool
            def __init__(self, relative_to_bounding_box: bool = ...) -> None: ...
        class OcrOutputFormat(_message.Message):
            __slots__ = ("characters", "character_restrictions")
            class OcrFormatRestrictionBlock(_message.Message):
                __slots__ = ("number_of_characters", "allowed_character_indexes")
                NUMBER_OF_CHARACTERS_FIELD_NUMBER: _ClassVar[int]
                ALLOWED_CHARACTER_INDEXES_FIELD_NUMBER: _ClassVar[int]
                number_of_characters: int
                allowed_character_indexes: _containers.RepeatedScalarFieldContainer[int]
                def __init__(self, number_of_characters: _Optional[int] = ..., allowed_character_indexes: _Optional[_Iterable[int]] = ...) -> None: ...
            class Character(_message.Message):
                __slots__ = ("utf8_representation", "character_type", "ignore")
                class CharacterType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
                    __slots__ = ()
                    CT_REGULAR: _ClassVar[ModelFile.Output.OcrOutputFormat.Character.CharacterType]
                    CT_START_OF_TEXT: _ClassVar[ModelFile.Output.OcrOutputFormat.Character.CharacterType]
                    CT_END_OF_TEXT: _ClassVar[ModelFile.Output.OcrOutputFormat.Character.CharacterType]
                    CT_PADDING: _ClassVar[ModelFile.Output.OcrOutputFormat.Character.CharacterType]
                CT_REGULAR: ModelFile.Output.OcrOutputFormat.Character.CharacterType
                CT_START_OF_TEXT: ModelFile.Output.OcrOutputFormat.Character.CharacterType
                CT_END_OF_TEXT: ModelFile.Output.OcrOutputFormat.Character.CharacterType
                CT_PADDING: ModelFile.Output.OcrOutputFormat.Character.CharacterType
                UTF8_REPRESENTATION_FIELD_NUMBER: _ClassVar[int]
                CHARACTER_TYPE_FIELD_NUMBER: _ClassVar[int]
                IGNORE_FIELD_NUMBER: _ClassVar[int]
                utf8_representation: bytes
                character_type: ModelFile.Output.OcrOutputFormat.Character.CharacterType
                ignore: bool
                def __init__(self, utf8_representation: _Optional[bytes] = ..., character_type: _Optional[_Union[ModelFile.Output.OcrOutputFormat.Character.CharacterType, str]] = ..., ignore: bool = ...) -> None: ...
            CHARACTERS_FIELD_NUMBER: _ClassVar[int]
            CHARACTER_RESTRICTIONS_FIELD_NUMBER: _ClassVar[int]
            characters: _containers.RepeatedCompositeFieldContainer[ModelFile.Output.OcrOutputFormat.Character]
            character_restrictions: ModelFile.Output.OcrOutputFormat.OcrFormatRestrictionBlock
            def __init__(self, characters: _Optional[_Iterable[_Union[ModelFile.Output.OcrOutputFormat.Character, _Mapping]]] = ..., character_restrictions: _Optional[_Union[ModelFile.Output.OcrOutputFormat.OcrFormatRestrictionBlock, _Mapping]] = ...) -> None: ...
        OUTPUT_NAME_FIELD_NUMBER: _ClassVar[int]
        SCALAR_FORMAT_FIELD_NUMBER: _ClassVar[int]
        SEGMENTATION_MAPS_FORMAT_FIELD_NUMBER: _ClassVar[int]
        BOUNDING_BOXES_FORMAT_FIELD_NUMBER: _ClassVar[int]
        BOUNDING_BOX_SEGMENTATIONS_FORMAT_FIELD_NUMBER: _ClassVar[int]
        OCR_FORMAT_FIELD_NUMBER: _ClassVar[int]
        output_name: str
        scalar_format: ModelFile.Output.ScalarOutputFormat
        segmentation_maps_format: ModelFile.Output.SegmentationMapsOutputFormat
        bounding_boxes_format: ModelFile.Output.BoundingBoxesOutputFormat
        bounding_box_segmentations_format: ModelFile.Output.BoundingBoxSegmentationsOutputFormat
        ocr_format: ModelFile.Output.OcrOutputFormat
        def __init__(self, output_name: _Optional[str] = ..., scalar_format: _Optional[_Union[ModelFile.Output.ScalarOutputFormat, _Mapping]] = ..., segmentation_maps_format: _Optional[_Union[ModelFile.Output.SegmentationMapsOutputFormat, _Mapping]] = ..., bounding_boxes_format: _Optional[_Union[ModelFile.Output.BoundingBoxesOutputFormat, _Mapping]] = ..., bounding_box_segmentations_format: _Optional[_Union[ModelFile.Output.BoundingBoxSegmentationsOutputFormat, _Mapping]] = ..., ocr_format: _Optional[_Union[ModelFile.Output.OcrOutputFormat, _Mapping]] = ...) -> None: ...
    class FileInfo(_message.Message):
        __slots__ = ("network_name", "network_id", "network_experiment_id", "network_snapshot_id", "network_type", "network_flavor", "network_version", "runtime_version", "precision", "minimum_libdenkflow_version")
        class NetworkType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            NT_UNKNOWN: _ClassVar[ModelFile.FileInfo.NetworkType]
            NT_CLASSIFICATION: _ClassVar[ModelFile.FileInfo.NetworkType]
            NT_SEGMENTATION: _ClassVar[ModelFile.FileInfo.NetworkType]
            NT_INSTANCE_SEGMENTATION: _ClassVar[ModelFile.FileInfo.NetworkType]
            NT_OBJECT_DETECTION: _ClassVar[ModelFile.FileInfo.NetworkType]
            NT_ANOMALY_DETECTION: _ClassVar[ModelFile.FileInfo.NetworkType]
            NT_OPTICAL_CHARACTER_RECOGNITION: _ClassVar[ModelFile.FileInfo.NetworkType]
        NT_UNKNOWN: ModelFile.FileInfo.NetworkType
        NT_CLASSIFICATION: ModelFile.FileInfo.NetworkType
        NT_SEGMENTATION: ModelFile.FileInfo.NetworkType
        NT_INSTANCE_SEGMENTATION: ModelFile.FileInfo.NetworkType
        NT_OBJECT_DETECTION: ModelFile.FileInfo.NetworkType
        NT_ANOMALY_DETECTION: ModelFile.FileInfo.NetworkType
        NT_OPTICAL_CHARACTER_RECOGNITION: ModelFile.FileInfo.NetworkType
        class Precision(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            P_UNDEFINED: _ClassVar[ModelFile.FileInfo.Precision]
            P_MIXED_PRECISION: _ClassVar[ModelFile.FileInfo.Precision]
            P_FP8: _ClassVar[ModelFile.FileInfo.Precision]
            P_FP16: _ClassVar[ModelFile.FileInfo.Precision]
            P_FP32: _ClassVar[ModelFile.FileInfo.Precision]
            P_FP64: _ClassVar[ModelFile.FileInfo.Precision]
            P_BF8: _ClassVar[ModelFile.FileInfo.Precision]
            P_BF16: _ClassVar[ModelFile.FileInfo.Precision]
            P_BF32: _ClassVar[ModelFile.FileInfo.Precision]
            P_BF64: _ClassVar[ModelFile.FileInfo.Precision]
            P_INT8: _ClassVar[ModelFile.FileInfo.Precision]
            P_INT16: _ClassVar[ModelFile.FileInfo.Precision]
            P_INT32: _ClassVar[ModelFile.FileInfo.Precision]
            P_INT64: _ClassVar[ModelFile.FileInfo.Precision]
            P_UINT8: _ClassVar[ModelFile.FileInfo.Precision]
            P_UINT16: _ClassVar[ModelFile.FileInfo.Precision]
            P_UINT32: _ClassVar[ModelFile.FileInfo.Precision]
            P_UINT64: _ClassVar[ModelFile.FileInfo.Precision]
        P_UNDEFINED: ModelFile.FileInfo.Precision
        P_MIXED_PRECISION: ModelFile.FileInfo.Precision
        P_FP8: ModelFile.FileInfo.Precision
        P_FP16: ModelFile.FileInfo.Precision
        P_FP32: ModelFile.FileInfo.Precision
        P_FP64: ModelFile.FileInfo.Precision
        P_BF8: ModelFile.FileInfo.Precision
        P_BF16: ModelFile.FileInfo.Precision
        P_BF32: ModelFile.FileInfo.Precision
        P_BF64: ModelFile.FileInfo.Precision
        P_INT8: ModelFile.FileInfo.Precision
        P_INT16: ModelFile.FileInfo.Precision
        P_INT32: ModelFile.FileInfo.Precision
        P_INT64: ModelFile.FileInfo.Precision
        P_UINT8: ModelFile.FileInfo.Precision
        P_UINT16: ModelFile.FileInfo.Precision
        P_UINT32: ModelFile.FileInfo.Precision
        P_UINT64: ModelFile.FileInfo.Precision
        NETWORK_NAME_FIELD_NUMBER: _ClassVar[int]
        NETWORK_ID_FIELD_NUMBER: _ClassVar[int]
        NETWORK_EXPERIMENT_ID_FIELD_NUMBER: _ClassVar[int]
        NETWORK_SNAPSHOT_ID_FIELD_NUMBER: _ClassVar[int]
        NETWORK_TYPE_FIELD_NUMBER: _ClassVar[int]
        NETWORK_FLAVOR_FIELD_NUMBER: _ClassVar[int]
        NETWORK_VERSION_FIELD_NUMBER: _ClassVar[int]
        RUNTIME_VERSION_FIELD_NUMBER: _ClassVar[int]
        PRECISION_FIELD_NUMBER: _ClassVar[int]
        MINIMUM_LIBDENKFLOW_VERSION_FIELD_NUMBER: _ClassVar[int]
        network_name: str
        network_id: str
        network_experiment_id: str
        network_snapshot_id: str
        network_type: ModelFile.FileInfo.NetworkType
        network_flavor: str
        network_version: ModelFile.Version
        runtime_version: ModelFile.Version
        precision: ModelFile.FileInfo.Precision
        minimum_libdenkflow_version: ModelFile.Version
        def __init__(self, network_name: _Optional[str] = ..., network_id: _Optional[str] = ..., network_experiment_id: _Optional[str] = ..., network_snapshot_id: _Optional[str] = ..., network_type: _Optional[_Union[ModelFile.FileInfo.NetworkType, str]] = ..., network_flavor: _Optional[str] = ..., network_version: _Optional[_Union[ModelFile.Version, _Mapping]] = ..., runtime_version: _Optional[_Union[ModelFile.Version, _Mapping]] = ..., precision: _Optional[_Union[ModelFile.FileInfo.Precision, str]] = ..., minimum_libdenkflow_version: _Optional[_Union[ModelFile.Version, _Mapping]] = ...) -> None: ...
    class FileContent(_message.Message):
        __slots__ = ("default_model", "tensorrt_model")
        class DefaultModel(_message.Message):
            __slots__ = ("model_data",)
            MODEL_DATA_FIELD_NUMBER: _ClassVar[int]
            model_data: ModelFile.Content
            def __init__(self, model_data: _Optional[_Union[ModelFile.Content, _Mapping]] = ...) -> None: ...
        class TensorRTModel(_message.Message):
            __slots__ = ("model_data", "calibration_cache", "calibration_flatbuffers")
            MODEL_DATA_FIELD_NUMBER: _ClassVar[int]
            CALIBRATION_CACHE_FIELD_NUMBER: _ClassVar[int]
            CALIBRATION_FLATBUFFERS_FIELD_NUMBER: _ClassVar[int]
            model_data: ModelFile.Content
            calibration_cache: ModelFile.Content
            calibration_flatbuffers: ModelFile.Content
            def __init__(self, model_data: _Optional[_Union[ModelFile.Content, _Mapping]] = ..., calibration_cache: _Optional[_Union[ModelFile.Content, _Mapping]] = ..., calibration_flatbuffers: _Optional[_Union[ModelFile.Content, _Mapping]] = ...) -> None: ...
        DEFAULT_MODEL_FIELD_NUMBER: _ClassVar[int]
        TENSORRT_MODEL_FIELD_NUMBER: _ClassVar[int]
        default_model: ModelFile.FileContent.DefaultModel
        tensorrt_model: ModelFile.FileContent.TensorRTModel
        def __init__(self, default_model: _Optional[_Union[ModelFile.FileContent.DefaultModel, _Mapping]] = ..., tensorrt_model: _Optional[_Union[ModelFile.FileContent.TensorRTModel, _Mapping]] = ...) -> None: ...
    PROTOCOL_VERSION_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    FILE_INFO_FIELD_NUMBER: _ClassVar[int]
    FILE_CONTENT_FIELD_NUMBER: _ClassVar[int]
    CLASS_LABELS_FIELD_NUMBER: _ClassVar[int]
    INPUTS_FIELD_NUMBER: _ClassVar[int]
    OUTPUTS_FIELD_NUMBER: _ClassVar[int]
    protocol_version: ModelFile.Version
    created_at: int
    file_info: ModelFile.FileInfo
    file_content: ModelFile.FileContent
    class_labels: _containers.RepeatedCompositeFieldContainer[ModelFile.ClassLabel]
    inputs: _containers.RepeatedCompositeFieldContainer[ModelFile.Input]
    outputs: _containers.RepeatedCompositeFieldContainer[ModelFile.Output]
    def __init__(self, protocol_version: _Optional[_Union[ModelFile.Version, _Mapping]] = ..., created_at: _Optional[int] = ..., file_info: _Optional[_Union[ModelFile.FileInfo, _Mapping]] = ..., file_content: _Optional[_Union[ModelFile.FileContent, _Mapping]] = ..., class_labels: _Optional[_Iterable[_Union[ModelFile.ClassLabel, _Mapping]]] = ..., inputs: _Optional[_Iterable[_Union[ModelFile.Input, _Mapping]]] = ..., outputs: _Optional[_Iterable[_Union[ModelFile.Output, _Mapping]]] = ...) -> None: ...
