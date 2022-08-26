class SaiDriver():
    def __init__(self, driver_config):
        raise NotImplementedError
    def cleanup(self):
        raise NotImplementedError
    def set_loglevel(self, sai_api, loglevel):
        raise NotImplementedError

    # CRUD
    def create(self, obj, attrs, do_assert = True):
        raise NotImplementedError
    def remove(self, obj, do_assert = True):
        raise NotImplementedError
    def set(self, obj, attr, do_assert = True):
        raise NotImplementedError
    def get(self, obj, attrs, do_assert = True):
        raise NotImplementedError

    # Stats
    def get_stats(self, obj, attrs, do_assert = True):
        raise NotImplementedError
    def clear_stats(self, obj, attrs, do_assert = True):
        raise NotImplementedError

    # Flush FDB
    def flush_fdb_entries(self, attrs = None):
        raise NotImplementedError

    # BULK
    def bulk_create(self, obj, keys, attrs, do_assert = True):
        raise NotImplementedError
    def bulk_remove(self, obj, keys, do_assert = True):
        raise NotImplementedError
    def bulk_set(self, obj, keys, attrs, do_assert = True):
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
