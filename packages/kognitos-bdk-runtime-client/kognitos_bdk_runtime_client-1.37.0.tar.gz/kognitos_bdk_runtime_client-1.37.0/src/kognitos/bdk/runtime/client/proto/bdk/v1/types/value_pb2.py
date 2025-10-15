"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v1.types import concept_type_pb2 as bdk_dot_v1_dot_types_dot_concept__type__pb2
from ....bdk.v1.types import date_pb2 as bdk_dot_v1_dot_types_dot_date__pb2
from ....bdk.v1.types import noun_phrase_pb2 as bdk_dot_v1_dot_types_dot_noun__phrase__pb2
from ....bdk.v1.types import time_pb2 as bdk_dot_v1_dot_types_dot_time__pb2
from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x18bdk/v1/types/value.proto\x12\x06bdk.v1\x1a\x1fbdk/v1/types/concept_type.proto\x1a\x17bdk/v1/types/date.proto\x1a\x1ebdk/v1/types/noun_phrase.proto\x1a\x17bdk/v1/types/time.proto\x1a\x1cgoogle/protobuf/struct.proto\x1a\x1fgoogle/protobuf/timestamp.proto"\x8e\x06\n\x05Value\x12;\n\nnull_value\x18\x01 \x01(\x0e2\x1a.google.protobuf.NullValueH\x00R\tnullValue\x12?\n\x10conceptual_value\x18\x02 \x01(\x0b2\x12.bdk.v1.NounPhraseH\x00R\x0fconceptualValue\x12\x1f\n\ntext_value\x18\x03 \x01(\tH\x00R\ttextValue\x12#\n\x0cnumber_value\x18\x04 \x01(\x01H\x00R\x0bnumberValue\x12%\n\rboolean_value\x18\x05 \x01(\x08H\x00R\x0cbooleanValue\x12C\n\x0edatetime_value\x18\x06 \x01(\x0b2\x1a.google.protobuf.TimestampH\x00R\rdatetimeValue\x12-\n\ndate_value\x18\x07 \x01(\x0b2\x0c.bdk.v1.DateH\x00R\tdateValue\x12-\n\ntime_value\x18\x08 \x01(\x0b2\x0c.bdk.v1.TimeH\x00R\ttimeValue\x122\n\nfile_value\x18\t \x01(\x0b2\x11.bdk.v1.FileValueH\x00R\tfileValue\x12D\n\x10dictionary_value\x18\n \x01(\x0b2\x17.bdk.v1.DictionaryValueH\x00R\x0fdictionaryValue\x122\n\nlist_value\x18\x0b \x01(\x0b2\x11.bdk.v1.ListValueH\x00R\tlistValue\x128\n\x0copaque_value\x18\x0c \x01(\x0b2\x13.bdk.v1.OpaqueValueH\x00R\x0bopaqueValue\x125\n\x0btable_value\x18\r \x01(\x0b2\x12.bdk.v1.TableValueH\x00R\ntableValue\x12A\n\x0fsensitive_value\x18\x0e \x01(\x0b2\x16.bdk.v1.SensitiveValueH\x00R\x0esensitiveValueB\x15\n\x13value_discriminator"n\n\x0fDictionaryValue\x124\n\x06fields\x18\x01 \x03(\x0b2\x1c.bdk.v1.DictionaryValueFieldR\x06fields\x12%\n\x04is_a\x18\x02 \x03(\x0b2\x12.bdk.v1.NounPhraseR\x03isA"M\n\x14DictionaryValueField\x12\x10\n\x03key\x18\x01 \x01(\tR\x03key\x12#\n\x05value\x18\x02 \x01(\x0b2\r.bdk.v1.ValueR\x05value"2\n\tListValue\x12%\n\x06values\x18\x01 \x03(\x0b2\r.bdk.v1.ValueR\x06values"^\n\tFileValue\x12\x18\n\x06remote\x18\x01 \x01(\tH\x00R\x06remote\x12&\n\x06inline\x18\x02 \x01(\x0b2\x0c.bdk.v1.FileH\x00R\x06inlineB\x0f\n\rinline_remote"=\n\x04File\x12\x1b\n\tfile_name\x18\x01 \x01(\tR\x08fileName\x12\x18\n\x07content\x18\x02 \x01(\x0cR\x07content"N\n\x0bOpaqueValue\x12\x18\n\x07content\x18\x01 \x01(\x0cR\x07content\x12%\n\x04is_a\x18\x02 \x03(\x0b2\x12.bdk.v1.NounPhraseR\x03isA"5\n\x0eSensitiveValue\x12#\n\x05value\x18\x01 \x01(\x0b2\r.bdk.v1.ValueR\x05value"`\n\nTableValue\x12\x18\n\x06remote\x18\x01 \x01(\tH\x00R\x06remote\x12\'\n\x06inline\x18\x02 \x01(\x0b2\r.bdk.v1.TableH\x00R\x06inlineB\x0f\n\rinline_remote"1\n\x05Table\x12(\n\x07columns\x18\x01 \x03(\x0b2\x0e.bdk.v1.ColumnR\x07columns"C\n\x06Column\x12%\n\x06values\x18\x01 \x03(\x0b2\r.bdk.v1.ValueR\x06values\x12\x12\n\x04name\x18\x02 \x01(\tR\x04nameB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v1.types.value_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_VALUE']._serialized_start = 215
    _globals['_VALUE']._serialized_end = 997
    _globals['_DICTIONARYVALUE']._serialized_start = 999
    _globals['_DICTIONARYVALUE']._serialized_end = 1109
    _globals['_DICTIONARYVALUEFIELD']._serialized_start = 1111
    _globals['_DICTIONARYVALUEFIELD']._serialized_end = 1188
    _globals['_LISTVALUE']._serialized_start = 1190
    _globals['_LISTVALUE']._serialized_end = 1240
    _globals['_FILEVALUE']._serialized_start = 1242
    _globals['_FILEVALUE']._serialized_end = 1336
    _globals['_FILE']._serialized_start = 1338
    _globals['_FILE']._serialized_end = 1399
    _globals['_OPAQUEVALUE']._serialized_start = 1401
    _globals['_OPAQUEVALUE']._serialized_end = 1479
    _globals['_SENSITIVEVALUE']._serialized_start = 1481
    _globals['_SENSITIVEVALUE']._serialized_end = 1534
    _globals['_TABLEVALUE']._serialized_start = 1536
    _globals['_TABLEVALUE']._serialized_end = 1632
    _globals['_TABLE']._serialized_start = 1634
    _globals['_TABLE']._serialized_end = 1683
    _globals['_COLUMN']._serialized_start = 1685
    _globals['_COLUMN']._serialized_end = 1752