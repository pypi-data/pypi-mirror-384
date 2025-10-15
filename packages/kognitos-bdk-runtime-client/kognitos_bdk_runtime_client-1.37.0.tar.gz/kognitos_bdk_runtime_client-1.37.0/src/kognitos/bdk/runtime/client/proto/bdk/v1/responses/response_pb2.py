"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v1.responses import discover_procedures_pb2 as bdk_dot_v1_dot_responses_dot_discover__procedures__pb2
from ....bdk.v1.responses import environment_information_pb2 as bdk_dot_v1_dot_responses_dot_environment__information__pb2
from ....bdk.v1.responses import error_pb2 as bdk_dot_v1_dot_responses_dot_error__pb2
from ....bdk.v1.responses import invoke_procedure_pb2 as bdk_dot_v1_dot_responses_dot_invoke__procedure__pb2
from ....bdk.v1.responses import promise_pb2 as bdk_dot_v1_dot_responses_dot_promise__pb2
from ....bdk.v1.responses import question_pb2 as bdk_dot_v1_dot_responses_dot_question__pb2
from ....bdk.v1.responses import retrieve_book_pb2 as bdk_dot_v1_dot_responses_dot_retrieve__book__pb2
from ....bdk.v1.responses import retrieve_book_procedures_pb2 as bdk_dot_v1_dot_responses_dot_retrieve__book__procedures__pb2
from ....bdk.v1.responses import retrieve_books_pb2 as bdk_dot_v1_dot_responses_dot_retrieve__books__pb2
from ....bdk.v1.responses import retrieve_discoverables_pb2 as bdk_dot_v1_dot_responses_dot_retrieve__discoverables__pb2
from ....bdk.v1.responses import retrieve_tags_pb2 as bdk_dot_v1_dot_responses_dot_retrieve__tags__pb2
from ....bdk.v1.responses import retrieve_user_info_pb2 as bdk_dot_v1_dot_responses_dot_retrieve__user__info__pb2
from ....bdk.v1.responses import test_connection_pb2 as bdk_dot_v1_dot_responses_dot_test__connection__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1fbdk/v1/responses/response.proto\x12\x06bdk.v1\x1a*bdk/v1/responses/discover_procedures.proto\x1a.bdk/v1/responses/environment_information.proto\x1a\x1cbdk/v1/responses/error.proto\x1a\'bdk/v1/responses/invoke_procedure.proto\x1a\x1ebdk/v1/responses/promise.proto\x1a\x1fbdk/v1/responses/question.proto\x1a$bdk/v1/responses/retrieve_book.proto\x1a/bdk/v1/responses/retrieve_book_procedures.proto\x1a%bdk/v1/responses/retrieve_books.proto\x1a-bdk/v1/responses/retrieve_discoverables.proto\x1a$bdk/v1/responses/retrieve_tags.proto\x1a)bdk/v1/responses/retrieve_user_info.proto\x1a&bdk/v1/responses/test_connection.proto"\xed\x07\n\x08Response\x12%\n\x05error\x18\x01 \x01(\x0b2\r.bdk.v1.ErrorH\x00R\x05error\x12a\n\x17environment_information\x18\x02 \x01(\x0b2&.bdk.v1.EnvironmentInformationResponseH\x00R\x16environmentInformation\x12H\n\x0fretrieved_books\x18\x03 \x01(\x0b2\x1d.bdk.v1.RetrieveBooksResponseH\x00R\x0eretrievedBooks\x12E\n\x0eretrieved_book\x18\x04 \x01(\x0b2\x1c.bdk.v1.RetrieveBookResponseH\x00R\rretrievedBook\x12[\n\x14retrieved_procedures\x18\x05 \x01(\x0b2&.bdk.v1.RetrieveBookProceduresResponseH\x00R\x13retrievedProcedures\x12M\n\x11tested_connection\x18\x06 \x01(\x0b2\x1e.bdk.v1.TestConnectionResponseH\x00R\x10testedConnection\x12N\n\x11invoked_procedure\x18\x07 \x01(\x0b2\x1f.bdk.v1.InvokeProcedureResponseH\x00R\x10invokedProcedure\x12Y\n\x15discovered_procedures\x18\x08 \x01(\x0b2".bdk.v1.DiscoverProceduresResponseH\x00R\x14discoveredProcedures\x126\n\x08question\x18\t \x01(\x0b2\x18.bdk.v1.QuestionResponseH\x00R\x08question\x12`\n\x17retrieved_discoverables\x18\n \x01(\x0b2%.bdk.v1.RetrieveDiscoverablesResponseH\x00R\x16retrievedDiscoverables\x12E\n\x0eretrieved_tags\x18\x0b \x01(\x0b2\x1c.bdk.v1.RetrieveTagsResponseH\x00R\rretrievedTags\x123\n\x07promise\x18\x0c \x01(\x0b2\x17.bdk.v1.PromiseResponseH\x00R\x07promise\x12?\n\tuser_info\x18\r \x01(\x0b2 .bdk.v1.RetrieveUserInfoResponseH\x00R\x08userInfoB\x18\n\x16response_discriminatorB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v1.responses.response_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_RESPONSE']._serialized_start = 566
    _globals['_RESPONSE']._serialized_end = 1571