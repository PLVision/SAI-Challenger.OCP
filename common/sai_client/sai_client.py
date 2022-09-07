class SaiClient:
    def __init__(self, driver_config):
        raise NotImplementedError

    def cleanup(self):
        raise NotImplementedError

    def set_loglevel(self, sai_api, loglevel):
        raise NotImplementedError

    # CRUD
    def create(self, obj_type, *, key=None, attrs=None):
        raise NotImplementedError

    def remove(self, *, oid=None, obj_type=None, key=None):
        raise NotImplementedError

    def set(self, *, oid=None, obj_type=None, key=None, attr=None):
        raise NotImplementedError

    def get(self, *, oid=None, obj_type=None, key=None, attrs=None):
        raise NotImplementedError

    # Stats
    def get_stats(self, oid=None, obj_type=None, key=None, attrs=None):
        raise NotImplementedError

    def clear_stats(self, oid=None, obj_type=None, key=None, attrs=None):
        raise NotImplementedError

    # Flush FDB
    def flush_fdb_entries(self, attrs=None):
        raise NotImplementedError

    # BULK
    def bulk_create(self, obj_type, keys=None, attrs=None):
        raise NotImplementedError

    def bulk_remove(self, oids=None, obj_type=None, keys=None):
        raise NotImplementedError

    def bulk_set(self, oids=None, obj_type=None, keys=None, attrs=None):
        raise NotImplementedError

    # Host interface
    def remote_iface_exists(self, iface):
        raise NotImplementedError

    def remote_iface_is_up(self, iface):
        raise NotImplementedError

    def remote_iface_status_set(self, iface, status):
        raise NotImplementedError

    def remote_iface_agent_start(self, ifaces):
        raise NotImplementedError

    def remote_iface_agent_stop(self):
        raise NotImplementedError

    @staticmethod
    def build(params) -> 'SaiClient':
        if params["type"] == "redis":
            from sai_client.sai_redis_client.sai_redis_client import SaiRedisClient
            sai_client = SaiRedisClient(params["config"])
        elif params["type"] == "thrift":
            from sai_client.sai_thrift_client.sai_thrift_client import SaiThriftClient
            sai_client = SaiThriftClient(params["config"])
        else:
            raise RuntimeError("Appropriate driver wasn't found")
        return sai_client