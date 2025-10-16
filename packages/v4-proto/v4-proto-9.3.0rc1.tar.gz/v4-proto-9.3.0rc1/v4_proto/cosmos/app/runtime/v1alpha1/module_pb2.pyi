from v4_proto.cosmos.app.v1alpha1 import module_pb2 as _module_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Module(_message.Message):
    __slots__ = ("app_name", "begin_blockers", "end_blockers", "init_genesis", "export_genesis", "override_store_keys", "order_migrations", "precommiters", "prepare_check_staters")
    APP_NAME_FIELD_NUMBER: _ClassVar[int]
    BEGIN_BLOCKERS_FIELD_NUMBER: _ClassVar[int]
    END_BLOCKERS_FIELD_NUMBER: _ClassVar[int]
    INIT_GENESIS_FIELD_NUMBER: _ClassVar[int]
    EXPORT_GENESIS_FIELD_NUMBER: _ClassVar[int]
    OVERRIDE_STORE_KEYS_FIELD_NUMBER: _ClassVar[int]
    ORDER_MIGRATIONS_FIELD_NUMBER: _ClassVar[int]
    PRECOMMITERS_FIELD_NUMBER: _ClassVar[int]
    PREPARE_CHECK_STATERS_FIELD_NUMBER: _ClassVar[int]
    app_name: str
    begin_blockers: _containers.RepeatedScalarFieldContainer[str]
    end_blockers: _containers.RepeatedScalarFieldContainer[str]
    init_genesis: _containers.RepeatedScalarFieldContainer[str]
    export_genesis: _containers.RepeatedScalarFieldContainer[str]
    override_store_keys: _containers.RepeatedCompositeFieldContainer[StoreKeyConfig]
    order_migrations: _containers.RepeatedScalarFieldContainer[str]
    precommiters: _containers.RepeatedScalarFieldContainer[str]
    prepare_check_staters: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, app_name: _Optional[str] = ..., begin_blockers: _Optional[_Iterable[str]] = ..., end_blockers: _Optional[_Iterable[str]] = ..., init_genesis: _Optional[_Iterable[str]] = ..., export_genesis: _Optional[_Iterable[str]] = ..., override_store_keys: _Optional[_Iterable[_Union[StoreKeyConfig, _Mapping]]] = ..., order_migrations: _Optional[_Iterable[str]] = ..., precommiters: _Optional[_Iterable[str]] = ..., prepare_check_staters: _Optional[_Iterable[str]] = ...) -> None: ...

class StoreKeyConfig(_message.Message):
    __slots__ = ("module_name", "kv_store_key")
    MODULE_NAME_FIELD_NUMBER: _ClassVar[int]
    KV_STORE_KEY_FIELD_NUMBER: _ClassVar[int]
    module_name: str
    kv_store_key: str
    def __init__(self, module_name: _Optional[str] = ..., kv_store_key: _Optional[str] = ...) -> None: ...
