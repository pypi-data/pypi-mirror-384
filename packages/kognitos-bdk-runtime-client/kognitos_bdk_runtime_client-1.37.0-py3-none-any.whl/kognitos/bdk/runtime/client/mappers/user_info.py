# pylint: disable=no-name-in-module
from kognitos.bdk.runtime.client.proto.bdk.v1.responses.retrieve_user_info_pb2 import \
    RetrieveUserInfoResponse as ProtoUserInfoResponse

from ..user_info import UserInfo


def map_user_info(
    data: ProtoUserInfoResponse,
) -> UserInfo:
    user_info = data.user_info

    other_attributes = dict(user_info.other_attributes)

    return UserInfo(
        email=user_info.email or None,
        username=user_info.username or None,
        other_attributes=other_attributes,
    )
