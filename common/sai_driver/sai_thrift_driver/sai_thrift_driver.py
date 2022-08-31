from enum import Enum
from functools import wraps
from itertools import zip_longest
from json import dumps as json_dumps

from thrift.protocol import TBinaryProtocol
from thrift.transport import TSocket, TTransport

from sai import SaiObjType, SaiData
from sai_driver.sai_driver import SaiDriver
from sai_driver.sai_thrift_driver.sai_thrift_status import SaiStatus
from sai_object import SaiObject
from sai_thrift import sai_rpc, sai_adapter, ttypes, sai_headers
# noinspection PyPep8Naming
from sai_thrift.ttypes import sai_thrift_exception as SaiThriftException


def chunks(iterable, n, fillvalue=None):
    return zip_longest(*[iter(iterable)] * n, fillvalue=fillvalue)


class SaiThriftExceptionGroup(Exception):
    def __init__(self, msg, exceptions, *args, **kwargs):
        super().__init__(self, msg, *args, **kwargs)
        self.exceptions = exceptions


class ThriftValueError(ValueError):
    ...


def assert_status(method):
    @wraps(method)
    def method_wrapper(self, *args, do_assert=True, **kwargs):
        try:
            result = method(self, *args, **kwargs)
        except SaiThriftException as e:
            if do_assert:
                raise AssertionError from e
            else:
                return SaiStatus(e.status).name
        if do_assert and result is not None:
            return result
        else:
            return SaiStatus.SAI_STATUS_SUCCESS.name

    return method_wrapper


class SaiThriftDriver(SaiDriver):
    def __init__(self, driver_config):
        self.thrift_client, self.thrift_transport = self.start_thrift_client(driver_config)

    @staticmethod
    def start_thrift_client(driver_config):
        transport = TSocket.TSocket(driver_config.server, driver_config.port)
        transport = TTransport.TBufferedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        return sai_rpc.Client(protocol), transport

    def __enter__(self):
        self.thrift_transport.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.thrift_transport.close()

    # region CRUD
    @assert_status
    def create(self, obj_type, key=None, attrs=()):
        return self._operate('create', attrs=attrs, obj_type=obj_type, key=key)

    @assert_status
    def remove(self, oid=None, obj_type=None, key=None):
        return self._operate('remove', attrs=(), oid=oid, obj_type=obj_type, key=key)  # attrs are not needed on remove

    @assert_status
    def set(self, oid=None, obj_type=None, key=None, attrs=()):
        return self._operate_attributes('set', attrs=attrs, oid=oid, obj_type=obj_type, key=key)

    @assert_status
    def get(self, oid=None, obj_type=None, key=None, attrs=()):
        obj_type_name = self._get_obj_type_name(oid, obj_type)

        result = self._operate_attributes('get', attrs=attrs, oid=oid, obj_type=obj_type, key=key)

        # TODO rework, because seems Redis specific
        return SaiData(
            json_dumps(list(zip((attr for attr, _ in self._convert_attrs(attrs, obj_type_name)), result)))
        )

    # endregion CRUD

    def create_object(self, obj_type, key=None, attrs=()):
        return SaiObject(self, obj_type, key=key, attrs=attrs)

    @staticmethod
    def _form_obj_key(oid, obj_type_name, key):
        if key is not None:
            obj_key_t = getattr(ttypes, f'sai_thrift_{obj_type_name}_t')
            return {obj_type_name: obj_key_t(**key)}
        elif oid is not None:
            return {f"{obj_type_name}_oid": oid}
        else:
            return {}

    @staticmethod
    def get_object_type(oid):
        return SaiObjType((oid if isinstance(oid, int) else int(oid, 16)) >> 48)

    @classmethod
    def _get_obj_type_name(cls, oid=None, obj_type=None):
        if oid is not None:
            return cls.get_object_type(oid).name.lower()
        else:
            return obj_type.name.lower() if isinstance(obj_type, Enum) else str(obj_type)

    @staticmethod
    def _convert_attrs(attrs, obj_type_name: str):
        prefix = f'SAI_{obj_type_name.upper()}_ATTR_'
        for attr, value in chunks(attrs, 2):
            if hasattr(sai_headers, attr) and attr.startswith(prefix):
                result = attr[len(prefix):].lower(), value
                yield result

    def _operate(self, operation, attrs=(), oid=None, obj_type=None, key=None):
        if oid is not None and (obj_type is not None or key is not None):
            raise ValueError('Both oid and key/object type are specified')

        assert oid is None or (obj_type is None and key is None)
        obj_type_name = self._get_obj_type_name(oid, obj_type)

        sai_thrift_function = getattr(sai_adapter, f'sai_thrift_{operation}_{obj_type_name}')

        obj_key = self._form_obj_key(oid, obj_type_name, key)
        attr_kwargs = dict(self._convert_attrs(attrs, obj_type_name))
        return sai_thrift_function(self.thrift_client, **obj_key, **attr_kwargs)

    def _operate_attributes(self, operation, attrs=(), oid=None, obj_type=None, key=None):
        if oid is not None and (obj_type is not None or key is not None):
            raise ValueError('Both oid and key/object type are specified')
        obj_type_name = self._get_obj_type_name(oid, obj_type)

        # thrift functions operating one attribute a time
        exceptions = []
        result = []
        for attr, value in self._convert_attrs(attrs, obj_type_name):
            sai_thrift_function = getattr(sai_adapter, f'sai_thrift_{operation}_{obj_type_name}_attribute')
            try:
                result.append(sai_thrift_function(
                    self.thrift_client,
                    **self._form_obj_key(oid, obj_type_name, key),
                    **{attr: value}
                ))
            except SaiThriftException as e:
                exceptions.append(e)
                result.append(e)
        if exceptions:
            first_exc, *other_excs = exceptions
            cause = None
            if other_excs:
                cause = SaiThriftExceptionGroup(f'Bulk operation failed: {other_excs}', other_excs)
            raise first_exc from cause
        else:
            return result
