class SaiDriver():
    def __init__(self, driver_config):
        raise NotImplementedError
    def cleanup(self):
        raise NotImplementedError
    def set_loglevel(self, sai_api, loglevel):
        raise NotImplementedError

    # CRUD
    def create(self, obj_type, key = None, attrs = None):
        raise NotImplementedError
    def remove(self, oid = None, obj_type = None, key = None):
        raise NotImplementedError
    def set(self, oid = None, obj_type = None, key = None, attr = None):
        raise NotImplementedError
    def get(self, oid = None, obj_type = None, key = None, attrs = None):
        raise NotImplementedError

    # Stats
    def get_stats(self, oid = None, obj_type = None, key = None, attrs = None):
        raise NotImplementedError
    def clear_stats(self, oid = None, obj_type = None, key = None, attrs = None):
        raise NotImplementedError

    # Flush FDB
    def flush_fdb_entries(self, attrs = None):
        raise NotImplementedError

    # BULK
    def bulk_create(self, obj_type, keys = None, attrs = None):
        raise NotImplementedError
    def bulk_remove(self, oids = None, obj_type = None, keys = None):
        raise NotImplementedError
    def bulk_set(self, oids = None, obj_type = None, keys = None, attrs = None):
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

def SaiDriverBuilder(params):
    driver = None
    if params["type"] == "redis":
        from sai_driver.sai_redis_driver.sai_redis_driver import SaiRedisDriver
        driver = SaiRedisDriver(params["config"])
    elif params["type"] == "thrift":
        from sai_thrift_driver import SaiThriftDriver
        driver = SaiThriftDirver(params["config"])
    return driver
