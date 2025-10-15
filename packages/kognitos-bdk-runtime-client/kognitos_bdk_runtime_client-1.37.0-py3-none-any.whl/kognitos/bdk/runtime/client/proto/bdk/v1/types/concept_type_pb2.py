"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v1.types import noun_phrase_pb2 as bdk_dot_v1_dot_types_dot_noun__phrase__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1fbdk/v1/types/concept_type.proto\x12\x06bdk.v1\x1a\x1ebdk/v1/types/noun_phrase.proto"@\n\x13ConceptOptionalType\x12)\n\x05inner\x18\x01 \x01(\x0b2\x13.bdk.v1.ConceptTypeR\x05inner"A\n\x14ConceptSensitiveType\x12)\n\x05inner\x18\x01 \x01(\x0b2\x13.bdk.v1.ConceptTypeR\x05inner"<\n\x0fConceptListType\x12)\n\x05inner\x18\x01 \x01(\x0b2\x13.bdk.v1.ConceptTypeR\x05inner"?\n\x10ConceptUnionType\x12+\n\x06inners\x18\x01 \x03(\x0b2\x13.bdk.v1.ConceptTypeR\x06inners"\xb1\x01\n\x15ConceptDictionaryType\x12%\n\x04is_a\x18\x01 \x03(\x0b2\x12.bdk.v1.NounPhraseR\x03isA\x12:\n\x06fields\x18\x02 \x03(\x0b2".bdk.v1.ConceptDictionaryTypeFieldR\x06fields\x12%\n\x0bdescription\x18\x03 \x01(\tH\x00R\x0bdescription\x88\x01\x01B\x0e\n\x0c_description"\x90\x01\n\x1aConceptDictionaryTypeField\x12\x10\n\x03key\x18\x01 \x01(\tR\x03key\x12)\n\x05value\x18\x02 \x01(\x0b2\x13.bdk.v1.ConceptTypeR\x05value\x12%\n\x0bdescription\x18\x03 \x01(\tH\x00R\x0bdescription\x88\x01\x01B\x0e\n\x0c_description"\x83\x01\n\x10ConceptTableType\x128\n\x07columns\x18\x01 \x03(\x0b2\x1e.bdk.v1.ConceptTableTypeColumnR\x07columns\x12%\n\x0bdescription\x18\x02 \x01(\tH\x00R\x0bdescription\x88\x01\x01B\x0e\n\x0c_description"\x8c\x01\n\x16ConceptTableTypeColumn\x12\x10\n\x03key\x18\x01 \x01(\tR\x03key\x12)\n\x05value\x18\x02 \x01(\x0b2\x13.bdk.v1.ConceptTypeR\x05value\x12%\n\x0bdescription\x18\x03 \x01(\tH\x00R\x0bdescription\x88\x01\x01B\x0e\n\x0c_description"q\n\x11ConceptOpaqueType\x12%\n\x04is_a\x18\x01 \x03(\x0b2\x12.bdk.v1.NounPhraseR\x03isA\x12%\n\x0bdescription\x18\x02 \x01(\tH\x00R\x0bdescription\x88\x01\x01B\x0e\n\x0c_description"\x10\n\x0eConceptAnyType"\x11\n\x0fConceptSelfType"\x97\x01\n\x15ConceptEnumTypeMember\x12\x12\n\x04name\x18\x01 \x01(\tR\x04name\x123\n\x0bnoun_phrase\x18\x02 \x01(\x0b2\x12.bdk.v1.NounPhraseR\nnounPhrase\x12%\n\x0bdescription\x18\x03 \x01(\tH\x00R\x0bdescription\x88\x01\x01B\x0e\n\x0c_description"\xa8\x01\n\x0fConceptEnumType\x12%\n\x04is_a\x18\x01 \x03(\x0b2\x12.bdk.v1.NounPhraseR\x03isA\x127\n\x07members\x18\x02 \x03(\x0b2\x1d.bdk.v1.ConceptEnumTypeMemberR\x07members\x12%\n\x0bdescription\x18\x03 \x01(\tH\x00R\x0bdescription\x88\x01\x01B\x0e\n\x0c_description"\xcf\x05\n\x0bConceptType\x12<\n\x0bscalar_type\x18\x01 \x01(\x0e2\x19.bdk.v1.ConceptScalarTypeH\x00R\nscalarType\x12B\n\roptional_type\x18\x02 \x01(\x0b2\x1b.bdk.v1.ConceptOptionalTypeH\x00R\x0coptionalType\x126\n\tlist_type\x18\x03 \x01(\x0b2\x17.bdk.v1.ConceptListTypeH\x00R\x08listType\x12H\n\x0fdictionary_type\x18\x04 \x01(\x0b2\x1d.bdk.v1.ConceptDictionaryTypeH\x00R\x0edictionaryType\x129\n\ntable_type\x18\x05 \x01(\x0b2\x18.bdk.v1.ConceptTableTypeH\x00R\ttableType\x12<\n\x0bopaque_type\x18\x06 \x01(\x0b2\x19.bdk.v1.ConceptOpaqueTypeH\x00R\nopaqueType\x123\n\x08any_type\x18\x07 \x01(\x0b2\x16.bdk.v1.ConceptAnyTypeH\x00R\x07anyType\x129\n\nunion_type\x18\x08 \x01(\x0b2\x18.bdk.v1.ConceptUnionTypeH\x00R\tunionType\x126\n\tself_type\x18\t \x01(\x0b2\x17.bdk.v1.ConceptSelfTypeH\x00R\x08selfType\x12E\n\x0esensitive_type\x18\n \x01(\x0b2\x1c.bdk.v1.ConceptSensitiveTypeH\x00R\rsensitiveType\x126\n\tenum_type\x18\x0b \x01(\x0b2\x17.bdk.v1.ConceptEnumTypeH\x00R\x08enumTypeB\x1c\n\x1aconcept_type_discriminator*\x95\x02\n\x11ConceptScalarType\x12\x1f\n\x1bConceptScalarTypeConceptual\x10\x00\x12\x19\n\x15ConceptScalarTypeText\x10\x01\x12\x1b\n\x17ConceptScalarTypeNumber\x10\x02\x12\x1c\n\x18ConceptScalarTypeBoolean\x10\x03\x12\x1d\n\x19ConceptScalarTypeDatetime\x10\x04\x12\x19\n\x15ConceptScalarTypeDate\x10\x05\x12\x19\n\x15ConceptScalarTypeTime\x10\x06\x12\x19\n\x15ConceptScalarTypeFile\x10\x07\x12\x19\n\x15ConceptScalarTypeUUID\x10\x08B\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v1.types.concept_type_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_CONCEPTSCALARTYPE']._serialized_start = 2139
    _globals['_CONCEPTSCALARTYPE']._serialized_end = 2416
    _globals['_CONCEPTOPTIONALTYPE']._serialized_start = 75
    _globals['_CONCEPTOPTIONALTYPE']._serialized_end = 139
    _globals['_CONCEPTSENSITIVETYPE']._serialized_start = 141
    _globals['_CONCEPTSENSITIVETYPE']._serialized_end = 206
    _globals['_CONCEPTLISTTYPE']._serialized_start = 208
    _globals['_CONCEPTLISTTYPE']._serialized_end = 268
    _globals['_CONCEPTUNIONTYPE']._serialized_start = 270
    _globals['_CONCEPTUNIONTYPE']._serialized_end = 333
    _globals['_CONCEPTDICTIONARYTYPE']._serialized_start = 336
    _globals['_CONCEPTDICTIONARYTYPE']._serialized_end = 513
    _globals['_CONCEPTDICTIONARYTYPEFIELD']._serialized_start = 516
    _globals['_CONCEPTDICTIONARYTYPEFIELD']._serialized_end = 660
    _globals['_CONCEPTTABLETYPE']._serialized_start = 663
    _globals['_CONCEPTTABLETYPE']._serialized_end = 794
    _globals['_CONCEPTTABLETYPECOLUMN']._serialized_start = 797
    _globals['_CONCEPTTABLETYPECOLUMN']._serialized_end = 937
    _globals['_CONCEPTOPAQUETYPE']._serialized_start = 939
    _globals['_CONCEPTOPAQUETYPE']._serialized_end = 1052
    _globals['_CONCEPTANYTYPE']._serialized_start = 1054
    _globals['_CONCEPTANYTYPE']._serialized_end = 1070
    _globals['_CONCEPTSELFTYPE']._serialized_start = 1072
    _globals['_CONCEPTSELFTYPE']._serialized_end = 1089
    _globals['_CONCEPTENUMTYPEMEMBER']._serialized_start = 1092
    _globals['_CONCEPTENUMTYPEMEMBER']._serialized_end = 1243
    _globals['_CONCEPTENUMTYPE']._serialized_start = 1246
    _globals['_CONCEPTENUMTYPE']._serialized_end = 1414
    _globals['_CONCEPTTYPE']._serialized_start = 1417
    _globals['_CONCEPTTYPE']._serialized_end = 2136