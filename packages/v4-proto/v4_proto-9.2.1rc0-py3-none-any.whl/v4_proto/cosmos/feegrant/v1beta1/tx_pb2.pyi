from google.protobuf import any_pb2 as _any_pb2
from v4_proto.cosmos_proto import cosmos_pb2 as _cosmos_pb2
from v4_proto.cosmos.msg.v1 import msg_pb2 as _msg_pb2
from v4_proto.amino import amino_pb2 as _amino_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MsgGrantAllowance(_message.Message):
    __slots__ = ("granter", "grantee", "allowance")
    GRANTER_FIELD_NUMBER: _ClassVar[int]
    GRANTEE_FIELD_NUMBER: _ClassVar[int]
    ALLOWANCE_FIELD_NUMBER: _ClassVar[int]
    granter: str
    grantee: str
    allowance: _any_pb2.Any
    def __init__(self, granter: _Optional[str] = ..., grantee: _Optional[str] = ..., allowance: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...

class MsgGrantAllowanceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MsgRevokeAllowance(_message.Message):
    __slots__ = ("granter", "grantee")
    GRANTER_FIELD_NUMBER: _ClassVar[int]
    GRANTEE_FIELD_NUMBER: _ClassVar[int]
    granter: str
    grantee: str
    def __init__(self, granter: _Optional[str] = ..., grantee: _Optional[str] = ...) -> None: ...

class MsgRevokeAllowanceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MsgPruneAllowances(_message.Message):
    __slots__ = ("pruner",)
    PRUNER_FIELD_NUMBER: _ClassVar[int]
    pruner: str
    def __init__(self, pruner: _Optional[str] = ...) -> None: ...

class MsgPruneAllowancesResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
