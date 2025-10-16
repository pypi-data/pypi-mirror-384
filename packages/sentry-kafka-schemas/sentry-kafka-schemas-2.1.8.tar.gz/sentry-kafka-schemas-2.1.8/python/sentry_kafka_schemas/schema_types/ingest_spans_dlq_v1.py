from typing import Union, Literal, TypedDict, Required, List, Any, Dict


class SpanEvent(TypedDict, total=False):
    """ span_event. """

    event_id: "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUuid"
    """
    minLength: 32
    maxLength: 36
    """

    organization_id: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUint"]
    """
    minimum: 0

    Required property
    """

    project_id: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUint"]
    """
    minimum: 0

    Required property
    """

    key_id: "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUint"
    """ minimum: 0 """

    trace_id: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUuid"]
    """
    minLength: 32
    maxLength: 36

    Required property
    """

    span_id: Required[Union[str, None]]
    """
    The span ID is a unique identifier for a span within a trace. It is an 8 byte hexadecimal string.

    Required property
    """

    parent_span_id: Union[str, None]
    """ The parent span ID is the ID of the span that caused this span. It is an 8 byte hexadecimal string. """

    start_timestamp: Required[Union[str, Union[int, float], Dict[str, Any], List[Any], bool, None]]
    """
    UNIX timestamp in seconds with fractional part up to microsecond precision.

    $anyOf:
      - $ref: file://ingest-spans.v1.schema.json#/definitions/PositiveFloat
      - null

    Required property
    """

    end_timestamp: Required[Union[str, Union[int, float], Dict[str, Any], List[Any], bool, None]]
    """
    UNIX timestamp in seconds with fractional part up to microsecond precision.

    $anyOf:
      - $ref: file://ingest-spans.v1.schema.json#/definitions/PositiveFloat
      - null

    Required property
    """

    retention_days: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUint16"]
    """
    minimum: 0
    maximum: 65535

    Required property
    """

    downsampled_retention_days: "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUint16"
    """
    minimum: 0
    maximum: 65535
    """

    received: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsPositivefloat"]
    """
    minimum: 0

    Required property
    """

    name: Required[Union[str, None]]
    """ Required property """

    status: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsSpanstatus"]
    """
    Aggregation type: anyOf

    Required property
    """

    is_remote: Required[Union[bool, None]]
    """ Required property """

    kind: "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsSpankind"
    """ Aggregation type: anyOf """

    links: Union[List["SpanLink"], None]
    """
    items:
      $ref: file://ingest-spans.v1.schema.json#/definitions/SpanLink
      used: !!set
        $ref: null
    """

    attributes: "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributes"
    """
    additionalProperties:
      $ref: file://ingest-spans.v1.schema.json#/definitions/AttributeValue
      used: !!set
        $ref: null
    """

    _meta: Dict[str, Any]


SpanLink = Union["_SpanLinkObject", None]
"""
span_link.

additionalProperties: True
"""



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributes = Union[Dict[str, Union[None, "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueObject"]], None]
"""
additionalProperties:
  $ref: file://ingest-spans.v1.schema.json#/definitions/AttributeValue
  used: !!set
    $ref: null
"""



class _FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueObject(TypedDict, total=False):
    type: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueObjectType"]
    """
    Aggregation type: anyOf

    Required property
    """

    value: Required[Union[Union[int, float], None, str, bool, List[Any], Dict[str, Any]]]
    """ Required property """



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueObjectType = Union[None, "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueObjectTypeAnyof1"]
""" Aggregation type: anyOf """



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueObjectTypeAnyof1 = Union[Literal['boolean'], Literal['integer'], Literal['double'], Literal['string'], Literal['array'], Literal['object']]
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSATTRIBUTEVALUEOBJECTTYPEANYOF1_BOOLEAN: Literal['boolean'] = "boolean"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueObjectTypeAnyof1' enum"""
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSATTRIBUTEVALUEOBJECTTYPEANYOF1_INTEGER: Literal['integer'] = "integer"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueObjectTypeAnyof1' enum"""
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSATTRIBUTEVALUEOBJECTTYPEANYOF1_DOUBLE: Literal['double'] = "double"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueObjectTypeAnyof1' enum"""
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSATTRIBUTEVALUEOBJECTTYPEANYOF1_STRING: Literal['string'] = "string"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueObjectTypeAnyof1' enum"""
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSATTRIBUTEVALUEOBJECTTYPEANYOF1_ARRAY: Literal['array'] = "array"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueObjectTypeAnyof1' enum"""
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSATTRIBUTEVALUEOBJECTTYPEANYOF1_OBJECT: Literal['object'] = "object"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueObjectTypeAnyof1' enum"""



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsPositivefloat = Union[int, float]
""" minimum: 0 """



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsSpankind = Union[None, "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsSpankindAnyof1"]
""" Aggregation type: anyOf """



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsSpankindAnyof1 = Union[Literal['internal'], Literal['server'], Literal['client'], Literal['producer'], Literal['consumer']]
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSSPANKINDANYOF1_INTERNAL: Literal['internal'] = "internal"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsSpankindAnyof1' enum"""
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSSPANKINDANYOF1_SERVER: Literal['server'] = "server"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsSpankindAnyof1' enum"""
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSSPANKINDANYOF1_CLIENT: Literal['client'] = "client"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsSpankindAnyof1' enum"""
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSSPANKINDANYOF1_PRODUCER: Literal['producer'] = "producer"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsSpankindAnyof1' enum"""
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSSPANKINDANYOF1_CONSUMER: Literal['consumer'] = "consumer"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsSpankindAnyof1' enum"""



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsSpanstatus = Union["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsSpanstatusAnyof0", None]
""" Aggregation type: anyOf """



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsSpanstatusAnyof0 = Union[Literal['ok'], Literal['error']]
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSSPANSTATUSANYOF0_OK: Literal['ok'] = "ok"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsSpanstatusAnyof0' enum"""
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSSPANSTATUSANYOF0_ERROR: Literal['error'] = "error"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsSpanstatusAnyof0' enum"""



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUint = int
""" minimum: 0 """



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUint16 = int
"""
minimum: 0
maximum: 65535
"""



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUuid = Union[str, None]
"""
minLength: 32
maxLength: 36
"""



class _SpanLinkObject(TypedDict, total=False):
    trace_id: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUuid"]
    """
    minLength: 32
    maxLength: 36

    Required property
    """

    span_id: Required[Union[str, None]]
    """ Required property """

    attributes: "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributes"
    """
    additionalProperties:
      $ref: file://ingest-spans.v1.schema.json#/definitions/AttributeValue
      used: !!set
        $ref: null
    """

    sampled: Union[bool, None]
