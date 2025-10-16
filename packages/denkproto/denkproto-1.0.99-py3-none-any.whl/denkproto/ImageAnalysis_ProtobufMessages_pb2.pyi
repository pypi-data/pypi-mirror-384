from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DataTypeEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNDEFINED_DT: _ClassVar[DataTypeEnum]
    STRING_DT: _ClassVar[DataTypeEnum]
    DOUBLE_DT: _ClassVar[DataTypeEnum]
    JSON_DT: _ClassVar[DataTypeEnum]
UNDEFINED_DT: DataTypeEnum
STRING_DT: DataTypeEnum
DOUBLE_DT: DataTypeEnum
JSON_DT: DataTypeEnum

class pb_ProtocolVersionDetection(_message.Message):
    __slots__ = ("protocol_version_major", "protocol_version_minor")
    PROTOCOL_VERSION_MAJOR_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_VERSION_MINOR_FIELD_NUMBER: _ClassVar[int]
    protocol_version_major: int
    protocol_version_minor: int
    def __init__(self, protocol_version_major: _Optional[int] = ..., protocol_version_minor: _Optional[int] = ...) -> None: ...

class pb_MessageHeader(_message.Message):
    __slots__ = ("message_type", "response", "message_counter", "size_message_body", "protocol_version_major", "protocol_version_minor", "timestamp_utc_ms", "error_code", "info_text", "int_values", "double_values", "string_values")
    class MessageType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNDEFINED: _ClassVar[pb_MessageHeader.MessageType]
        GETSTATUS: _ClassVar[pb_MessageHeader.MessageType]
        GETVERSION: _ClassVar[pb_MessageHeader.MessageType]
        INIT: _ClassVar[pb_MessageHeader.MessageType]
        GETPRESETS: _ClassVar[pb_MessageHeader.MessageType]
        GETPRESETINFO: _ClassVar[pb_MessageHeader.MessageType]
        SETCONFIG: _ClassVar[pb_MessageHeader.MessageType]
        REMOVECONFIG: _ClassVar[pb_MessageHeader.MessageType]
        GETCONFIGPARAMS: _ClassVar[pb_MessageHeader.MessageType]
        SETCONFIGPARAMS: _ClassVar[pb_MessageHeader.MessageType]
        ANALYZEIMAGE: _ClassVar[pb_MessageHeader.MessageType]
        IMAGERESULT: _ClassVar[pb_MessageHeader.MessageType]
        INFOMESSAGE: _ClassVar[pb_MessageHeader.MessageType]
        GETCONFIGFILE: _ClassVar[pb_MessageHeader.MessageType]
        SETCONFIGFILE: _ClassVar[pb_MessageHeader.MessageType]
        MODIFYCONFIGFILE: _ClassVar[pb_MessageHeader.MessageType]
        GETSTATISTICS: _ClassVar[pb_MessageHeader.MessageType]
        OPENDIRECTORYINBROWSER: _ClassVar[pb_MessageHeader.MessageType]
        OPENTASKINBROWSER: _ClassVar[pb_MessageHeader.MessageType]
    UNDEFINED: pb_MessageHeader.MessageType
    GETSTATUS: pb_MessageHeader.MessageType
    GETVERSION: pb_MessageHeader.MessageType
    INIT: pb_MessageHeader.MessageType
    GETPRESETS: pb_MessageHeader.MessageType
    GETPRESETINFO: pb_MessageHeader.MessageType
    SETCONFIG: pb_MessageHeader.MessageType
    REMOVECONFIG: pb_MessageHeader.MessageType
    GETCONFIGPARAMS: pb_MessageHeader.MessageType
    SETCONFIGPARAMS: pb_MessageHeader.MessageType
    ANALYZEIMAGE: pb_MessageHeader.MessageType
    IMAGERESULT: pb_MessageHeader.MessageType
    INFOMESSAGE: pb_MessageHeader.MessageType
    GETCONFIGFILE: pb_MessageHeader.MessageType
    SETCONFIGFILE: pb_MessageHeader.MessageType
    MODIFYCONFIGFILE: pb_MessageHeader.MessageType
    GETSTATISTICS: pb_MessageHeader.MessageType
    OPENDIRECTORYINBROWSER: pb_MessageHeader.MessageType
    OPENTASKINBROWSER: pb_MessageHeader.MessageType
    MESSAGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_COUNTER_FIELD_NUMBER: _ClassVar[int]
    SIZE_MESSAGE_BODY_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_VERSION_MAJOR_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_VERSION_MINOR_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_UTC_MS_FIELD_NUMBER: _ClassVar[int]
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    INFO_TEXT_FIELD_NUMBER: _ClassVar[int]
    INT_VALUES_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_VALUES_FIELD_NUMBER: _ClassVar[int]
    STRING_VALUES_FIELD_NUMBER: _ClassVar[int]
    message_type: pb_MessageHeader.MessageType
    response: bool
    message_counter: int
    size_message_body: int
    protocol_version_major: int
    protocol_version_minor: int
    timestamp_utc_ms: int
    error_code: int
    info_text: str
    int_values: _containers.RepeatedScalarFieldContainer[int]
    double_values: _containers.RepeatedScalarFieldContainer[float]
    string_values: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, message_type: _Optional[_Union[pb_MessageHeader.MessageType, str]] = ..., response: bool = ..., message_counter: _Optional[int] = ..., size_message_body: _Optional[int] = ..., protocol_version_major: _Optional[int] = ..., protocol_version_minor: _Optional[int] = ..., timestamp_utc_ms: _Optional[int] = ..., error_code: _Optional[int] = ..., info_text: _Optional[str] = ..., int_values: _Optional[_Iterable[int]] = ..., double_values: _Optional[_Iterable[float]] = ..., string_values: _Optional[_Iterable[str]] = ...) -> None: ...

class pb_Body_Init(_message.Message):
    __slots__ = ("init_hash_code",)
    INIT_HASH_CODE_FIELD_NUMBER: _ClassVar[int]
    init_hash_code: str
    def __init__(self, init_hash_code: _Optional[str] = ...) -> None: ...

class pb_Body_GetStatus_Response(_message.Message):
    __slots__ = ("init_hash_code", "init_timestamp_utc_ms", "configuration_sets", "images_in_process")
    class pb_ImageInProcess(_message.Message):
        __slots__ = ("serial_number_image", "configuration_set_name")
        SERIAL_NUMBER_IMAGE_FIELD_NUMBER: _ClassVar[int]
        CONFIGURATION_SET_NAME_FIELD_NUMBER: _ClassVar[int]
        serial_number_image: str
        configuration_set_name: str
        def __init__(self, serial_number_image: _Optional[str] = ..., configuration_set_name: _Optional[str] = ...) -> None: ...
    INIT_HASH_CODE_FIELD_NUMBER: _ClassVar[int]
    INIT_TIMESTAMP_UTC_MS_FIELD_NUMBER: _ClassVar[int]
    CONFIGURATION_SETS_FIELD_NUMBER: _ClassVar[int]
    IMAGES_IN_PROCESS_FIELD_NUMBER: _ClassVar[int]
    init_hash_code: str
    init_timestamp_utc_ms: int
    configuration_sets: _containers.RepeatedScalarFieldContainer[str]
    images_in_process: _containers.RepeatedCompositeFieldContainer[pb_Body_GetStatus_Response.pb_ImageInProcess]
    def __init__(self, init_hash_code: _Optional[str] = ..., init_timestamp_utc_ms: _Optional[int] = ..., configuration_sets: _Optional[_Iterable[str]] = ..., images_in_process: _Optional[_Iterable[_Union[pb_Body_GetStatus_Response.pb_ImageInProcess, _Mapping]]] = ...) -> None: ...

class pb_Body_GetVersion_Response(_message.Message):
    __slots__ = ("program_name", "program_version")
    PROGRAM_NAME_FIELD_NUMBER: _ClassVar[int]
    PROGRAM_VERSION_FIELD_NUMBER: _ClassVar[int]
    program_name: str
    program_version: str
    def __init__(self, program_name: _Optional[str] = ..., program_version: _Optional[str] = ...) -> None: ...

class pb_Body_GetPresets_Response(_message.Message):
    __slots__ = ("preset_name_list",)
    PRESET_NAME_LIST_FIELD_NUMBER: _ClassVar[int]
    preset_name_list: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, preset_name_list: _Optional[_Iterable[str]] = ...) -> None: ...

class pb_Body_GetPresetInfo(_message.Message):
    __slots__ = ("preset_name",)
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    preset_name: str
    def __init__(self, preset_name: _Optional[str] = ...) -> None: ...

class pb_Body_GetPresetInfo_Response(_message.Message):
    __slots__ = ("preset_info",)
    class DirectionEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNDEFINED_DR: _ClassVar[pb_Body_GetPresetInfo_Response.DirectionEnum]
        IN_DR: _ClassVar[pb_Body_GetPresetInfo_Response.DirectionEnum]
        OUT_DR: _ClassVar[pb_Body_GetPresetInfo_Response.DirectionEnum]
        IN_OUT_DR: _ClassVar[pb_Body_GetPresetInfo_Response.DirectionEnum]
    UNDEFINED_DR: pb_Body_GetPresetInfo_Response.DirectionEnum
    IN_DR: pb_Body_GetPresetInfo_Response.DirectionEnum
    OUT_DR: pb_Body_GetPresetInfo_Response.DirectionEnum
    IN_OUT_DR: pb_Body_GetPresetInfo_Response.DirectionEnum
    class pb_AddInfoItem(_message.Message):
        __slots__ = ("name", "value")
        NAME_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        name: str
        value: str
        def __init__(self, name: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class pb_ParamInfoItem(_message.Message):
        __slots__ = ("param_name", "datatype", "direction")
        PARAM_NAME_FIELD_NUMBER: _ClassVar[int]
        DATATYPE_FIELD_NUMBER: _ClassVar[int]
        DIRECTION_FIELD_NUMBER: _ClassVar[int]
        param_name: str
        datatype: DataTypeEnum
        direction: pb_Body_GetPresetInfo_Response.DirectionEnum
        def __init__(self, param_name: _Optional[str] = ..., datatype: _Optional[_Union[DataTypeEnum, str]] = ..., direction: _Optional[_Union[pb_Body_GetPresetInfo_Response.DirectionEnum, str]] = ...) -> None: ...
    class pb_PresetItem(_message.Message):
        __slots__ = ("preset_name", "date", "version", "comment", "feature_types", "additional_infos", "param_list")
        PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
        DATE_FIELD_NUMBER: _ClassVar[int]
        VERSION_FIELD_NUMBER: _ClassVar[int]
        COMMENT_FIELD_NUMBER: _ClassVar[int]
        FEATURE_TYPES_FIELD_NUMBER: _ClassVar[int]
        ADDITIONAL_INFOS_FIELD_NUMBER: _ClassVar[int]
        PARAM_LIST_FIELD_NUMBER: _ClassVar[int]
        preset_name: str
        date: str
        version: str
        comment: str
        feature_types: _containers.RepeatedScalarFieldContainer[str]
        additional_infos: _containers.RepeatedCompositeFieldContainer[pb_Body_GetPresetInfo_Response.pb_AddInfoItem]
        param_list: _containers.RepeatedCompositeFieldContainer[pb_Body_GetPresetInfo_Response.pb_ParamInfoItem]
        def __init__(self, preset_name: _Optional[str] = ..., date: _Optional[str] = ..., version: _Optional[str] = ..., comment: _Optional[str] = ..., feature_types: _Optional[_Iterable[str]] = ..., additional_infos: _Optional[_Iterable[_Union[pb_Body_GetPresetInfo_Response.pb_AddInfoItem, _Mapping]]] = ..., param_list: _Optional[_Iterable[_Union[pb_Body_GetPresetInfo_Response.pb_ParamInfoItem, _Mapping]]] = ...) -> None: ...
    PRESET_INFO_FIELD_NUMBER: _ClassVar[int]
    preset_info: pb_Body_GetPresetInfo_Response.pb_PresetItem
    def __init__(self, preset_info: _Optional[_Union[pb_Body_GetPresetInfo_Response.pb_PresetItem, _Mapping]] = ...) -> None: ...

class pb_ConfigParam(_message.Message):
    __slots__ = ("param_name", "datatype", "val_string", "val_json", "val_double")
    PARAM_NAME_FIELD_NUMBER: _ClassVar[int]
    DATATYPE_FIELD_NUMBER: _ClassVar[int]
    VAL_STRING_FIELD_NUMBER: _ClassVar[int]
    VAL_JSON_FIELD_NUMBER: _ClassVar[int]
    VAL_DOUBLE_FIELD_NUMBER: _ClassVar[int]
    param_name: str
    datatype: DataTypeEnum
    val_string: str
    val_json: str
    val_double: float
    def __init__(self, param_name: _Optional[str] = ..., datatype: _Optional[_Union[DataTypeEnum, str]] = ..., val_string: _Optional[str] = ..., val_json: _Optional[str] = ..., val_double: _Optional[float] = ...) -> None: ...

class pb_Body_SetConfig(_message.Message):
    __slots__ = ("configset_name", "cell_info", "preset_name", "config_params")
    class pb_CellInfo(_message.Message):
        __slots__ = ("busbar_count", "busbar_orientation", "crystal_type")
        class pb_BusbarOrientationEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            UNDEFINED_BO: _ClassVar[pb_Body_SetConfig.pb_CellInfo.pb_BusbarOrientationEnum]
            HORIZONTAL_BO: _ClassVar[pb_Body_SetConfig.pb_CellInfo.pb_BusbarOrientationEnum]
            VERTICAL_BO: _ClassVar[pb_Body_SetConfig.pb_CellInfo.pb_BusbarOrientationEnum]
        UNDEFINED_BO: pb_Body_SetConfig.pb_CellInfo.pb_BusbarOrientationEnum
        HORIZONTAL_BO: pb_Body_SetConfig.pb_CellInfo.pb_BusbarOrientationEnum
        VERTICAL_BO: pb_Body_SetConfig.pb_CellInfo.pb_BusbarOrientationEnum
        class pb_CrystalTypeEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            UNDEFINED_CT: _ClassVar[pb_Body_SetConfig.pb_CellInfo.pb_CrystalTypeEnum]
            MONO_CT: _ClassVar[pb_Body_SetConfig.pb_CellInfo.pb_CrystalTypeEnum]
            POLY_CT: _ClassVar[pb_Body_SetConfig.pb_CellInfo.pb_CrystalTypeEnum]
        UNDEFINED_CT: pb_Body_SetConfig.pb_CellInfo.pb_CrystalTypeEnum
        MONO_CT: pb_Body_SetConfig.pb_CellInfo.pb_CrystalTypeEnum
        POLY_CT: pb_Body_SetConfig.pb_CellInfo.pb_CrystalTypeEnum
        BUSBAR_COUNT_FIELD_NUMBER: _ClassVar[int]
        BUSBAR_ORIENTATION_FIELD_NUMBER: _ClassVar[int]
        CRYSTAL_TYPE_FIELD_NUMBER: _ClassVar[int]
        busbar_count: int
        busbar_orientation: pb_Body_SetConfig.pb_CellInfo.pb_BusbarOrientationEnum
        crystal_type: pb_Body_SetConfig.pb_CellInfo.pb_CrystalTypeEnum
        def __init__(self, busbar_count: _Optional[int] = ..., busbar_orientation: _Optional[_Union[pb_Body_SetConfig.pb_CellInfo.pb_BusbarOrientationEnum, str]] = ..., crystal_type: _Optional[_Union[pb_Body_SetConfig.pb_CellInfo.pb_CrystalTypeEnum, str]] = ...) -> None: ...
    CONFIGSET_NAME_FIELD_NUMBER: _ClassVar[int]
    CELL_INFO_FIELD_NUMBER: _ClassVar[int]
    PRESET_NAME_FIELD_NUMBER: _ClassVar[int]
    CONFIG_PARAMS_FIELD_NUMBER: _ClassVar[int]
    configset_name: str
    cell_info: pb_Body_SetConfig.pb_CellInfo
    preset_name: str
    config_params: _containers.RepeatedCompositeFieldContainer[pb_ConfigParam]
    def __init__(self, configset_name: _Optional[str] = ..., cell_info: _Optional[_Union[pb_Body_SetConfig.pb_CellInfo, _Mapping]] = ..., preset_name: _Optional[str] = ..., config_params: _Optional[_Iterable[_Union[pb_ConfigParam, _Mapping]]] = ...) -> None: ...

class pb_Body_RemoveConfig(_message.Message):
    __slots__ = ("configset_name",)
    CONFIGSET_NAME_FIELD_NUMBER: _ClassVar[int]
    configset_name: str
    def __init__(self, configset_name: _Optional[str] = ...) -> None: ...

class pb_Body_GetConfigParams(_message.Message):
    __slots__ = ("configset_name", "param_name_list")
    CONFIGSET_NAME_FIELD_NUMBER: _ClassVar[int]
    PARAM_NAME_LIST_FIELD_NUMBER: _ClassVar[int]
    configset_name: str
    param_name_list: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, configset_name: _Optional[str] = ..., param_name_list: _Optional[_Iterable[str]] = ...) -> None: ...

class pb_Body_GetConfigParams_Response(_message.Message):
    __slots__ = ("configset_name", "config_params")
    CONFIGSET_NAME_FIELD_NUMBER: _ClassVar[int]
    CONFIG_PARAMS_FIELD_NUMBER: _ClassVar[int]
    configset_name: str
    config_params: _containers.RepeatedCompositeFieldContainer[pb_ConfigParam]
    def __init__(self, configset_name: _Optional[str] = ..., config_params: _Optional[_Iterable[_Union[pb_ConfigParam, _Mapping]]] = ...) -> None: ...

class pb_Body_SetConfigParams(_message.Message):
    __slots__ = ("configset_name", "config_params")
    CONFIGSET_NAME_FIELD_NUMBER: _ClassVar[int]
    CONFIG_PARAMS_FIELD_NUMBER: _ClassVar[int]
    configset_name: str
    config_params: _containers.RepeatedCompositeFieldContainer[pb_ConfigParam]
    def __init__(self, configset_name: _Optional[str] = ..., config_params: _Optional[_Iterable[_Union[pb_ConfigParam, _Mapping]]] = ...) -> None: ...

class pb_ImageData(_message.Message):
    __slots__ = ("image_file_format", "image_data", "width", "height", "bitdepth")
    class pb_FileFormatEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNDEFINED_FF: _ClassVar[pb_ImageData.pb_FileFormatEnum]
        PNG_FF: _ClassVar[pb_ImageData.pb_FileFormatEnum]
        JPG_FF: _ClassVar[pb_ImageData.pb_FileFormatEnum]
        RAW_FF: _ClassVar[pb_ImageData.pb_FileFormatEnum]
        BYTES: _ClassVar[pb_ImageData.pb_FileFormatEnum]
        TIF_FF: _ClassVar[pb_ImageData.pb_FileFormatEnum]
    UNDEFINED_FF: pb_ImageData.pb_FileFormatEnum
    PNG_FF: pb_ImageData.pb_FileFormatEnum
    JPG_FF: pb_ImageData.pb_FileFormatEnum
    RAW_FF: pb_ImageData.pb_FileFormatEnum
    BYTES: pb_ImageData.pb_FileFormatEnum
    TIF_FF: pb_ImageData.pb_FileFormatEnum
    IMAGE_FILE_FORMAT_FIELD_NUMBER: _ClassVar[int]
    IMAGE_DATA_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    BITDEPTH_FIELD_NUMBER: _ClassVar[int]
    image_file_format: pb_ImageData.pb_FileFormatEnum
    image_data: bytes
    width: int
    height: int
    bitdepth: int
    def __init__(self, image_file_format: _Optional[_Union[pb_ImageData.pb_FileFormatEnum, str]] = ..., image_data: _Optional[bytes] = ..., width: _Optional[int] = ..., height: _Optional[int] = ..., bitdepth: _Optional[int] = ...) -> None: ...

class pb_MultiImages(_message.Message):
    __slots__ = ("name", "image")
    NAME_FIELD_NUMBER: _ClassVar[int]
    IMAGE_FIELD_NUMBER: _ClassVar[int]
    name: str
    image: pb_ImageData
    def __init__(self, name: _Optional[str] = ..., image: _Optional[_Union[pb_ImageData, _Mapping]] = ...) -> None: ...

class pb_AdditionalData(_message.Message):
    __slots__ = ("numeric_values", "string_values")
    class pb_NumericValue(_message.Message):
        __slots__ = ("name", "unit", "value")
        NAME_FIELD_NUMBER: _ClassVar[int]
        UNIT_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        name: str
        unit: str
        value: float
        def __init__(self, name: _Optional[str] = ..., unit: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    class pb_StringValue(_message.Message):
        __slots__ = ("name", "value")
        NAME_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        name: str
        value: str
        def __init__(self, name: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NUMERIC_VALUES_FIELD_NUMBER: _ClassVar[int]
    STRING_VALUES_FIELD_NUMBER: _ClassVar[int]
    numeric_values: _containers.RepeatedCompositeFieldContainer[pb_AdditionalData.pb_NumericValue]
    string_values: _containers.RepeatedCompositeFieldContainer[pb_AdditionalData.pb_StringValue]
    def __init__(self, numeric_values: _Optional[_Iterable[_Union[pb_AdditionalData.pb_NumericValue, _Mapping]]] = ..., string_values: _Optional[_Iterable[_Union[pb_AdditionalData.pb_StringValue, _Mapping]]] = ...) -> None: ...

class pb_Body_AnalyzeImage(_message.Message):
    __slots__ = ("serial_number_image", "configset_name", "image", "additional_data", "multi_images", "upload_options")
    class pb_DENK_UploadSettings(_message.Message):
        __slots__ = ("upload_path", "upload_annotations", "compression_option", "task_name")
        UPLOAD_PATH_FIELD_NUMBER: _ClassVar[int]
        UPLOAD_ANNOTATIONS_FIELD_NUMBER: _ClassVar[int]
        COMPRESSION_OPTION_FIELD_NUMBER: _ClassVar[int]
        TASK_NAME_FIELD_NUMBER: _ClassVar[int]
        upload_path: str
        upload_annotations: bool
        compression_option: int
        task_name: str
        def __init__(self, upload_path: _Optional[str] = ..., upload_annotations: bool = ..., compression_option: _Optional[int] = ..., task_name: _Optional[str] = ...) -> None: ...
    SERIAL_NUMBER_IMAGE_FIELD_NUMBER: _ClassVar[int]
    CONFIGSET_NAME_FIELD_NUMBER: _ClassVar[int]
    IMAGE_FIELD_NUMBER: _ClassVar[int]
    ADDITIONAL_DATA_FIELD_NUMBER: _ClassVar[int]
    MULTI_IMAGES_FIELD_NUMBER: _ClassVar[int]
    UPLOAD_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    serial_number_image: str
    configset_name: str
    image: pb_ImageData
    additional_data: pb_AdditionalData
    multi_images: _containers.RepeatedCompositeFieldContainer[pb_MultiImages]
    upload_options: pb_Body_AnalyzeImage.pb_DENK_UploadSettings
    def __init__(self, serial_number_image: _Optional[str] = ..., configset_name: _Optional[str] = ..., image: _Optional[_Union[pb_ImageData, _Mapping]] = ..., additional_data: _Optional[_Union[pb_AdditionalData, _Mapping]] = ..., multi_images: _Optional[_Iterable[_Union[pb_MultiImages, _Mapping]]] = ..., upload_options: _Optional[_Union[pb_Body_AnalyzeImage.pb_DENK_UploadSettings, _Mapping]] = ...) -> None: ...

class pb_Body_ImageResult(_message.Message):
    __slots__ = ("serial_number_image", "configset_name", "features", "image_classification", "image_plain", "image_overlaid", "multi_images_plain", "multi_images_overlaid")
    class pb_Rect(_message.Message):
        __slots__ = ("x_pos", "y_pos", "width", "height")
        X_POS_FIELD_NUMBER: _ClassVar[int]
        Y_POS_FIELD_NUMBER: _ClassVar[int]
        WIDTH_FIELD_NUMBER: _ClassVar[int]
        HEIGHT_FIELD_NUMBER: _ClassVar[int]
        x_pos: float
        y_pos: float
        width: float
        height: float
        def __init__(self, x_pos: _Optional[float] = ..., y_pos: _Optional[float] = ..., width: _Optional[float] = ..., height: _Optional[float] = ...) -> None: ...
    class pb_DENK_Point(_message.Message):
        __slots__ = ("x", "y")
        X_FIELD_NUMBER: _ClassVar[int]
        Y_FIELD_NUMBER: _ClassVar[int]
        x: float
        y: float
        def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ...) -> None: ...
    class pb_DENK_MinimalBoundingBox(_message.Message):
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
    class pb_DENK_OcrCharacter(_message.Message):
        __slots__ = ("character", "probability")
        CHARACTER_FIELD_NUMBER: _ClassVar[int]
        PROBABILITY_FIELD_NUMBER: _ClassVar[int]
        character: str
        probability: float
        def __init__(self, character: _Optional[str] = ..., probability: _Optional[float] = ...) -> None: ...
    class pb_DENK_OcrCharacterPosition(_message.Message):
        __slots__ = ("ocr_character",)
        OCR_CHARACTER_FIELD_NUMBER: _ClassVar[int]
        ocr_character: _containers.RepeatedCompositeFieldContainer[pb_Body_ImageResult.pb_DENK_OcrCharacter]
        def __init__(self, ocr_character: _Optional[_Iterable[_Union[pb_Body_ImageResult.pb_DENK_OcrCharacter, _Mapping]]] = ...) -> None: ...
    class pb_DENK_PointInt(_message.Message):
        __slots__ = ("x", "y")
        X_FIELD_NUMBER: _ClassVar[int]
        Y_FIELD_NUMBER: _ClassVar[int]
        x: int
        y: int
        def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ...) -> None: ...
    class pb_DENK_Contour(_message.Message):
        __slots__ = ("points",)
        POINTS_FIELD_NUMBER: _ClassVar[int]
        points: _containers.RepeatedCompositeFieldContainer[pb_Body_ImageResult.pb_DENK_PointInt]
        def __init__(self, points: _Optional[_Iterable[_Union[pb_Body_ImageResult.pb_DENK_PointInt, _Mapping]]] = ...) -> None: ...
    class pb_Feature(_message.Message):
        __slots__ = ("feature_type_name", "feature_infos", "multi_image_names", "section", "filtered_out", "classifier")
        class pb_FeatureInfo(_message.Message):
            __slots__ = ("outline_rect_px", "probability", "length", "area", "angle", "number", "average", "maximum", "minimum", "area_edge", "area_length", "avggrayvalue", "maxgrayvalue", "mingrayvalue", "id", "related_ids", "width", "outline_rect_mm", "uid", "related_uids", "minimal_bounding_box", "minimal_bounding_box_point", "ocr_text", "ocr_character_position", "segmentation_mask", "segmentation_contours")
            OUTLINE_RECT_PX_FIELD_NUMBER: _ClassVar[int]
            PROBABILITY_FIELD_NUMBER: _ClassVar[int]
            LENGTH_FIELD_NUMBER: _ClassVar[int]
            AREA_FIELD_NUMBER: _ClassVar[int]
            ANGLE_FIELD_NUMBER: _ClassVar[int]
            NUMBER_FIELD_NUMBER: _ClassVar[int]
            AVERAGE_FIELD_NUMBER: _ClassVar[int]
            MAXIMUM_FIELD_NUMBER: _ClassVar[int]
            MINIMUM_FIELD_NUMBER: _ClassVar[int]
            AREA_EDGE_FIELD_NUMBER: _ClassVar[int]
            AREA_LENGTH_FIELD_NUMBER: _ClassVar[int]
            AVGGRAYVALUE_FIELD_NUMBER: _ClassVar[int]
            MAXGRAYVALUE_FIELD_NUMBER: _ClassVar[int]
            MINGRAYVALUE_FIELD_NUMBER: _ClassVar[int]
            ID_FIELD_NUMBER: _ClassVar[int]
            RELATED_IDS_FIELD_NUMBER: _ClassVar[int]
            WIDTH_FIELD_NUMBER: _ClassVar[int]
            OUTLINE_RECT_MM_FIELD_NUMBER: _ClassVar[int]
            UID_FIELD_NUMBER: _ClassVar[int]
            RELATED_UIDS_FIELD_NUMBER: _ClassVar[int]
            MINIMAL_BOUNDING_BOX_FIELD_NUMBER: _ClassVar[int]
            MINIMAL_BOUNDING_BOX_POINT_FIELD_NUMBER: _ClassVar[int]
            OCR_TEXT_FIELD_NUMBER: _ClassVar[int]
            OCR_CHARACTER_POSITION_FIELD_NUMBER: _ClassVar[int]
            SEGMENTATION_MASK_FIELD_NUMBER: _ClassVar[int]
            SEGMENTATION_CONTOURS_FIELD_NUMBER: _ClassVar[int]
            outline_rect_px: pb_Body_ImageResult.pb_Rect
            probability: float
            length: float
            area: float
            angle: float
            number: float
            average: float
            maximum: float
            minimum: float
            area_edge: float
            area_length: float
            avggrayvalue: float
            maxgrayvalue: float
            mingrayvalue: float
            id: int
            related_ids: _containers.RepeatedScalarFieldContainer[int]
            width: float
            outline_rect_mm: pb_Body_ImageResult.pb_Rect
            uid: str
            related_uids: _containers.RepeatedScalarFieldContainer[str]
            minimal_bounding_box: pb_Body_ImageResult.pb_DENK_MinimalBoundingBox
            minimal_bounding_box_point: _containers.RepeatedCompositeFieldContainer[pb_Body_ImageResult.pb_DENK_Point]
            ocr_text: str
            ocr_character_position: _containers.RepeatedCompositeFieldContainer[pb_Body_ImageResult.pb_DENK_OcrCharacterPosition]
            segmentation_mask: bytes
            segmentation_contours: _containers.RepeatedCompositeFieldContainer[pb_Body_ImageResult.pb_DENK_Contour]
            def __init__(self, outline_rect_px: _Optional[_Union[pb_Body_ImageResult.pb_Rect, _Mapping]] = ..., probability: _Optional[float] = ..., length: _Optional[float] = ..., area: _Optional[float] = ..., angle: _Optional[float] = ..., number: _Optional[float] = ..., average: _Optional[float] = ..., maximum: _Optional[float] = ..., minimum: _Optional[float] = ..., area_edge: _Optional[float] = ..., area_length: _Optional[float] = ..., avggrayvalue: _Optional[float] = ..., maxgrayvalue: _Optional[float] = ..., mingrayvalue: _Optional[float] = ..., id: _Optional[int] = ..., related_ids: _Optional[_Iterable[int]] = ..., width: _Optional[float] = ..., outline_rect_mm: _Optional[_Union[pb_Body_ImageResult.pb_Rect, _Mapping]] = ..., uid: _Optional[str] = ..., related_uids: _Optional[_Iterable[str]] = ..., minimal_bounding_box: _Optional[_Union[pb_Body_ImageResult.pb_DENK_MinimalBoundingBox, _Mapping]] = ..., minimal_bounding_box_point: _Optional[_Iterable[_Union[pb_Body_ImageResult.pb_DENK_Point, _Mapping]]] = ..., ocr_text: _Optional[str] = ..., ocr_character_position: _Optional[_Iterable[_Union[pb_Body_ImageResult.pb_DENK_OcrCharacterPosition, _Mapping]]] = ..., segmentation_mask: _Optional[bytes] = ..., segmentation_contours: _Optional[_Iterable[_Union[pb_Body_ImageResult.pb_DENK_Contour, _Mapping]]] = ...) -> None: ...
        FEATURE_TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
        FEATURE_INFOS_FIELD_NUMBER: _ClassVar[int]
        MULTI_IMAGE_NAMES_FIELD_NUMBER: _ClassVar[int]
        SECTION_FIELD_NUMBER: _ClassVar[int]
        FILTERED_OUT_FIELD_NUMBER: _ClassVar[int]
        CLASSIFIER_FIELD_NUMBER: _ClassVar[int]
        feature_type_name: str
        feature_infos: _containers.RepeatedCompositeFieldContainer[pb_Body_ImageResult.pb_Feature.pb_FeatureInfo]
        multi_image_names: _containers.RepeatedScalarFieldContainer[str]
        section: _containers.RepeatedScalarFieldContainer[str]
        filtered_out: bool
        classifier: float
        def __init__(self, feature_type_name: _Optional[str] = ..., feature_infos: _Optional[_Iterable[_Union[pb_Body_ImageResult.pb_Feature.pb_FeatureInfo, _Mapping]]] = ..., multi_image_names: _Optional[_Iterable[str]] = ..., section: _Optional[_Iterable[str]] = ..., filtered_out: bool = ..., classifier: _Optional[float] = ...) -> None: ...
    class pb_ImageClassification(_message.Message):
        __slots__ = ("image_class_name", "image_quality_class", "image_quality_code", "image_quality_score", "image_ok_score", "image_avggrayvalue", "image_maxgrayvalue", "image_mingrayvalue")
        class pb_ImageQualityEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            UNDEFINED_QUALITY: _ClassVar[pb_Body_ImageResult.pb_ImageClassification.pb_ImageQualityEnum]
            NO_ISSUE_QUALITY: _ClassVar[pb_Body_ImageResult.pb_ImageClassification.pb_ImageQualityEnum]
            MINOR_ISSUE_QUALITY: _ClassVar[pb_Body_ImageResult.pb_ImageClassification.pb_ImageQualityEnum]
            MAJOR_ISSUE_QUALITY: _ClassVar[pb_Body_ImageResult.pb_ImageClassification.pb_ImageQualityEnum]
        UNDEFINED_QUALITY: pb_Body_ImageResult.pb_ImageClassification.pb_ImageQualityEnum
        NO_ISSUE_QUALITY: pb_Body_ImageResult.pb_ImageClassification.pb_ImageQualityEnum
        MINOR_ISSUE_QUALITY: pb_Body_ImageResult.pb_ImageClassification.pb_ImageQualityEnum
        MAJOR_ISSUE_QUALITY: pb_Body_ImageResult.pb_ImageClassification.pb_ImageQualityEnum
        IMAGE_CLASS_NAME_FIELD_NUMBER: _ClassVar[int]
        IMAGE_QUALITY_CLASS_FIELD_NUMBER: _ClassVar[int]
        IMAGE_QUALITY_CODE_FIELD_NUMBER: _ClassVar[int]
        IMAGE_QUALITY_SCORE_FIELD_NUMBER: _ClassVar[int]
        IMAGE_OK_SCORE_FIELD_NUMBER: _ClassVar[int]
        IMAGE_AVGGRAYVALUE_FIELD_NUMBER: _ClassVar[int]
        IMAGE_MAXGRAYVALUE_FIELD_NUMBER: _ClassVar[int]
        IMAGE_MINGRAYVALUE_FIELD_NUMBER: _ClassVar[int]
        image_class_name: str
        image_quality_class: pb_Body_ImageResult.pb_ImageClassification.pb_ImageQualityEnum
        image_quality_code: str
        image_quality_score: float
        image_ok_score: float
        image_avggrayvalue: float
        image_maxgrayvalue: float
        image_mingrayvalue: float
        def __init__(self, image_class_name: _Optional[str] = ..., image_quality_class: _Optional[_Union[pb_Body_ImageResult.pb_ImageClassification.pb_ImageQualityEnum, str]] = ..., image_quality_code: _Optional[str] = ..., image_quality_score: _Optional[float] = ..., image_ok_score: _Optional[float] = ..., image_avggrayvalue: _Optional[float] = ..., image_maxgrayvalue: _Optional[float] = ..., image_mingrayvalue: _Optional[float] = ...) -> None: ...
    SERIAL_NUMBER_IMAGE_FIELD_NUMBER: _ClassVar[int]
    CONFIGSET_NAME_FIELD_NUMBER: _ClassVar[int]
    FEATURES_FIELD_NUMBER: _ClassVar[int]
    IMAGE_CLASSIFICATION_FIELD_NUMBER: _ClassVar[int]
    IMAGE_PLAIN_FIELD_NUMBER: _ClassVar[int]
    IMAGE_OVERLAID_FIELD_NUMBER: _ClassVar[int]
    MULTI_IMAGES_PLAIN_FIELD_NUMBER: _ClassVar[int]
    MULTI_IMAGES_OVERLAID_FIELD_NUMBER: _ClassVar[int]
    serial_number_image: str
    configset_name: str
    features: _containers.RepeatedCompositeFieldContainer[pb_Body_ImageResult.pb_Feature]
    image_classification: pb_Body_ImageResult.pb_ImageClassification
    image_plain: pb_ImageData
    image_overlaid: pb_ImageData
    multi_images_plain: _containers.RepeatedCompositeFieldContainer[pb_MultiImages]
    multi_images_overlaid: _containers.RepeatedCompositeFieldContainer[pb_MultiImages]
    def __init__(self, serial_number_image: _Optional[str] = ..., configset_name: _Optional[str] = ..., features: _Optional[_Iterable[_Union[pb_Body_ImageResult.pb_Feature, _Mapping]]] = ..., image_classification: _Optional[_Union[pb_Body_ImageResult.pb_ImageClassification, _Mapping]] = ..., image_plain: _Optional[_Union[pb_ImageData, _Mapping]] = ..., image_overlaid: _Optional[_Union[pb_ImageData, _Mapping]] = ..., multi_images_plain: _Optional[_Iterable[_Union[pb_MultiImages, _Mapping]]] = ..., multi_images_overlaid: _Optional[_Iterable[_Union[pb_MultiImages, _Mapping]]] = ...) -> None: ...

class pb_Body_InfoMessage(_message.Message):
    __slots__ = ("info_type", "numeric_code", "info_text")
    class pb_InfoTypeEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNDEFINED_IT: _ClassVar[pb_Body_InfoMessage.pb_InfoTypeEnum]
        DEBUG_IT: _ClassVar[pb_Body_InfoMessage.pb_InfoTypeEnum]
        INFO_IT: _ClassVar[pb_Body_InfoMessage.pb_InfoTypeEnum]
        WARNING_IT: _ClassVar[pb_Body_InfoMessage.pb_InfoTypeEnum]
        ERROR_IT: _ClassVar[pb_Body_InfoMessage.pb_InfoTypeEnum]
    UNDEFINED_IT: pb_Body_InfoMessage.pb_InfoTypeEnum
    DEBUG_IT: pb_Body_InfoMessage.pb_InfoTypeEnum
    INFO_IT: pb_Body_InfoMessage.pb_InfoTypeEnum
    WARNING_IT: pb_Body_InfoMessage.pb_InfoTypeEnum
    ERROR_IT: pb_Body_InfoMessage.pb_InfoTypeEnum
    INFO_TYPE_FIELD_NUMBER: _ClassVar[int]
    NUMERIC_CODE_FIELD_NUMBER: _ClassVar[int]
    INFO_TEXT_FIELD_NUMBER: _ClassVar[int]
    info_type: pb_Body_InfoMessage.pb_InfoTypeEnum
    numeric_code: int
    info_text: str
    def __init__(self, info_type: _Optional[_Union[pb_Body_InfoMessage.pb_InfoTypeEnum, str]] = ..., numeric_code: _Optional[int] = ..., info_text: _Optional[str] = ...) -> None: ...

class pb_Body_GetConfigFile_Response(_message.Message):
    __slots__ = ("config_file_name", "config_content_json", "available_config_files", "current_default_file")
    CONFIG_FILE_NAME_FIELD_NUMBER: _ClassVar[int]
    CONFIG_CONTENT_JSON_FIELD_NUMBER: _ClassVar[int]
    AVAILABLE_CONFIG_FILES_FIELD_NUMBER: _ClassVar[int]
    CURRENT_DEFAULT_FILE_FIELD_NUMBER: _ClassVar[int]
    config_file_name: str
    config_content_json: str
    available_config_files: _containers.RepeatedScalarFieldContainer[str]
    current_default_file: str
    def __init__(self, config_file_name: _Optional[str] = ..., config_content_json: _Optional[str] = ..., available_config_files: _Optional[_Iterable[str]] = ..., current_default_file: _Optional[str] = ...) -> None: ...

class pb_Body_SetConfigFile(_message.Message):
    __slots__ = ("new_config_file_name", "set_as_default")
    NEW_CONFIG_FILE_NAME_FIELD_NUMBER: _ClassVar[int]
    SET_AS_DEFAULT_FIELD_NUMBER: _ClassVar[int]
    new_config_file_name: str
    set_as_default: bool
    def __init__(self, new_config_file_name: _Optional[str] = ..., set_as_default: bool = ...) -> None: ...

class pb_Body_ModifyConfigFile(_message.Message):
    __slots__ = ("config_file_name", "config_content_json")
    CONFIG_FILE_NAME_FIELD_NUMBER: _ClassVar[int]
    CONFIG_CONTENT_JSON_FIELD_NUMBER: _ClassVar[int]
    config_file_name: str
    config_content_json: str
    def __init__(self, config_file_name: _Optional[str] = ..., config_content_json: _Optional[str] = ...) -> None: ...

class pb_Body_GetStatistics_Response(_message.Message):
    __slots__ = ("statistics_csv",)
    STATISTICS_CSV_FIELD_NUMBER: _ClassVar[int]
    statistics_csv: str
    def __init__(self, statistics_csv: _Optional[str] = ...) -> None: ...

class pb_Body_OpenDirectoryInBrowser(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: str
    def __init__(self, path: _Optional[str] = ...) -> None: ...

class pb_Body_OpenTaskInBrowser(_message.Message):
    __slots__ = ("task_name",)
    TASK_NAME_FIELD_NUMBER: _ClassVar[int]
    task_name: str
    def __init__(self, task_name: _Optional[str] = ...) -> None: ...
