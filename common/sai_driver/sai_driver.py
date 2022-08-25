
class Driver():
    def __init__(self, driver_config):
        raise NotImplementedError
    def cleanup():
        raise NotImplementedError
    def set_loglevel(self, sai_api, loglevel):
        raise NotImplementedError
    def create(self, obj, attrs, do_assert = True):
        raise NotImplementedError
    def remove(self, obj, do_assert = True):
        raise NotImplementedError
    def set(self, obj, attr, do_assert = True):
        raise NotImplementedError
    def get(self, obj, attrs, do_assert = True):
        raise NotImplementedError
    def bulk_create(self, obj, keys, attrs, do_assert = True):
        raise NotImplementedError
    def bulk_remove(self, obj, keys, do_assert = True):
        raise NotImplementedError
    def bulk_set(self, obj, keys, attrs, do_assert = True):
        raise NotImplementedError
    @staticmethod
    def vid_to_type(vid):
        obj_type = int(vid[4:], 16) >> 48
        return "SAI_OBJECT_TYPE_" + SaiObjType(obj_type).name
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

