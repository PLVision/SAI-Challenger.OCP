import json
import os
import time

import pytest

from sai_data import SaiObjType, SaiData
from sai_abstractions import AbstractEntity
from sai_driver.sai_driver import SaiDriverBuilder

class Sai(AbstractEntity):
    # TODO: rename exec_params to setup_dict or so
    def __init__(self, exec_params):
        super().__init__(exec_params)
        self.driver = SaiDriverBuilder(exec_params["driver"])

        # what is it?
        self.alias = exec_params['alias']
        self.client_mode = not os.path.isfile("/usr/bin/redis-server")
        libsai = os.path.isfile("/usr/lib/libsai.so") or os.path.isfile("/usr/local/lib/libsai.so")
        self.libsaivs = exec_params["type"] == "vs" or (not self.client_mode and not libsai)
        self.run_traffic = exec_params["traffic"] and not self.libsaivs
        self.name = exec_params["asic"]
        self.target = exec_params["target"]
        self.sku = exec_params["sku"]
        self.asic_dir = exec_params["asic_dir"]

    def cleanup(self):
        return self.driver.cleanup()

    def set_loglevel(self, sai_api, loglevel):
        return self.driver.set_loglevel(sai_api, loglevel)

    # CRUD
    def create(self, obj_type, key = None, attrs = None):
        return self.driver.create(obj_type, key, attrs)

    def remove(self, oid = None, obj_type = None, key = None):
        return self.driver.remove(oid, obj_type, key)

    def set(self, oid = None, obj_type = None, key = None, attr = None):
        return self.driver.set(oid, obj_type, key, attr)

    def get(self, oid = None, obj_type = None, key = None, attrs = None, do_assert=True):
        return self.driver.get(oid, obj_type, key, attrs, do_assert)

    # BULK (TODO remove do_assert, "oid:" and handle oid
    def bulk_create(self, obj, keys, attrs, do_assert = True):
        return self.driver.bulk_create(obj, keys, attrs, do_assert)

    def bulk_remove(self, obj, keys, do_assert = True):
        return self.driver.bulk_remove(obj, keys, do_assert)

    def bulk_set(self, obj, keys, attrs, do_assert = True):
        return self.driver.bulk_set(obj, keys, attrs, do_assert)

    # Stats
    def get_stats(self, oid = None, obj_type = None, key = None, attrs = None):
        return self.driver.get_stats(oid, obj_type, key, attrs)

    def clear_stats(self, oid = None, obj_type = None, key = None, attrs = None):
        return self.driver.clear_stats(oid, obj_type, key, attrs)

    # Flush FDB
    def flush_fdb_entries(self, attrs=None):
        return self.driver.flush_fdb_entries(attrs)

    # Host interface
    def remote_iface_exists(self, iface):
        return self.driver.remote_iface_exists(iface)

    def remote_iface_is_up(self, iface):
        return self.driver.remote_iface_is_up(iface)

    def remote_iface_status_set(self, iface, status):
        return self.driver.remote_iface_status_set(iface, status)

    def remote_iface_agent_start(self, ifaces):
        return self.driver.remote_iface_agent_start(iface)

    def remote_iface_agent_stop(self):
        return self.driver.remote_iface_agent_stop()

    # Used in tests
    @staticmethod
    def get_meta(obj_type=None):
        try:
            path = "/etc/sai/sai.json"
            f = open(path, "r")
            sai_str = f.read()
            sai_json = json.loads(sai_str)
        except IOError:
            return None

        if obj_type is not None:
            if type(obj_type) == SaiObjType:
                obj_type = "SAI_OBJECT_TYPE_" + SaiObjType(obj_type).name
            else:
                assert type(obj_type) == str
                assert obj_type.startswith("SAI_OBJECT_TYPE_")

            for item in sai_json:
                if obj_type in item.values():
                    return item
            else:
                return None
        return sai_json

    @staticmethod
    def get_obj_attrs(sai_obj_type):
        meta = Sai.get_meta(sai_obj_type)
        if meta is None:
            return []
        return [(attr['name'], attr['properties']['type']) for attr in meta['attributes']]

    @staticmethod
    def get_obj_attr_type(sai_obj_type, sai_obj_attr):
        attrs = Sai.get_obj_attrs(sai_obj_type)
        for attr in attrs:
            if attr[0] == sai_obj_attr:
                return attr[1]
        return None

    def get_by_type(self, obj, attr, attr_type):
        # TODO: Check how to map these types into the struct or list
        unsupported_types = [
                                "sai_port_eye_values_list_t", "sai_prbs_rx_state_t",
                                "sai_port_err_status_list_t", "sai_fabric_port_reachability_t"
                            ]
        if attr_type == "sai_object_list_t":
            status, data = self.get(obj, [attr, "1:0x0"])
            if status == "SAI_STATUS_BUFFER_OVERFLOW":
                status, data = self.get(obj, [attr, self._make_list(data.uint32(), "0x0")])
        elif attr_type == "sai_s32_list_t" or attr_type == "sai_u32_list_t" or \
                attr_type == "sai_s16_list_t" or attr_type == "sai_u16_list_t" or\
                attr_type == "sai_s8_list_t" or attr_type == "sai_u8_list_t" or attr_type == "sai_vlan_list_t":
            status, data = self.get(obj, [attr, "1:0"])
            if status == "SAI_STATUS_BUFFER_OVERFLOW":
                status, data = self.get(obj, [attr, self._make_list(data.uint32(), "0")])
        elif attr_type == "sai_acl_capability_t":
            status, data = self.get(obj, [attr, self._make_acl_list(1)])
            if status == "SAI_STATUS_BUFFER_OVERFLOW":
                # extract number of actions supported for the stage
                # e.g. ["SAI_SWITCH_ATTR_ACL_STAGE_EGRESS","true:51"] -> 51
                length = int(data.to_json()[1].split(":")[1])
                status, data = self.get(obj, [attr, self._make_acl_list(length)])
        elif attr_type == "sai_acl_resource_list_t":
            status, data = self.get(obj, [attr, self._make_acl_resource_list(1)])
            if status == "SAI_STATUS_BUFFER_OVERFLOW":
                # extract number of actions supported for the stage
                # e.g. ['SAI_SWITCH_ATTR_AVAILABLE_ACL_TABLE', '{"count":10,"list":null}'] -> 10
                length = json.loads(data.to_json()[1])["count"]
                status, data = self.get(obj, [attr, self._make_acl_resource_list(length)])
        elif attr_type == "sai_map_list_t":
            status, data = self.get(obj, [attr, self._make_map_list(1)])
            if status == "SAI_STATUS_BUFFER_OVERFLOW":
                length = json.loads(data.to_json()[1])["count"]
                status, data = self.get(obj, [attr, self._make_map_list(length)])
        elif attr_type == "sai_system_port_config_list_t":
            status, data = self.get(obj, [attr, self._make_system_port_config_list(1)])
            if status == "SAI_STATUS_BUFFER_OVERFLOW":
                length = json.loads(data.to_json()[1])["count"]
                status, data = self.get(obj, [attr, self._make_system_port_config_list(length)])
        elif attr_type == "sai_object_id_t":
            status, data = self.get(obj, [attr, "0x0"])
        elif attr_type == "bool":
            status, data = self.get(obj, [attr, "true"])
        elif attr_type == "sai_mac_t":
            status, data = self.get(obj, [attr, "00:00:00:00:00:00"])
        elif attr_type == "sai_ip_address_t":
            status, data = self.get(obj, [attr, "0.0.0.0"])
        elif attr_type == "sai_ip4_t":
            status, data = self.get(obj, [attr, "0.0.0.0&mask:0.0.0.0"])
        elif attr_type == "sai_ip6_t":
            status, data = self.get(obj, [attr, "::0.0.0.0&mask:0:0:0:0:0:0:0:0"])
        elif attr_type == "sai_u32_range_t" or attr_type == "sai_s32_range_t":
            status, data = self.get(obj, [attr, "0,0"])
        elif attr_type in unsupported_types:
            status, data = "not supported", None
        elif attr_type.startswith("sai_") or attr_type == "" or attr_type == "char":
            status, data = self.get(obj, [attr, ""])
        else:
            assert False, f"Unsupported attribute type: get_by_type({obj}, {attr}, {attr_type})"
        return status, data

    def get_list(self, obj, attr, value):
        status, data = self.get(obj, [attr, "1:" + value], False)
        if status == "SAI_STATUS_BUFFER_OVERFLOW":
            in_data = self._make_list(data.uint32(), value)
            data = self.get(obj, [attr, in_data])
        else:
            assert status == 'SAI_STATUS_SUCCESS', f"get_list({obj}, {attr}, {value}) --> {status}"

        return data.to_list()

    def get_oids(self, obj_type=None):
        return self.driver.get_oids(obj_type)

    def assert_status_success(self, status, skip_not_supported=True, skip_not_implemented=True):
        if skip_not_supported:
            if status == "SAI_STATUS_NOT_SUPPORTED" or status == "SAI_STATUS_ATTR_NOT_SUPPORTED_0":
                pytest.skip("not supported")

        if skip_not_implemented:
            if status == "SAI_STATUS_NOT_IMPLEMENTED" or status == "SAI_STATUS_ATTR_NOT_IMPLEMENTED_0":
                pytest.skip("not implemented")

        assert status == "SAI_STATUS_SUCCESS"

    # Internal
    def _make_list(self, length, elem):
        return "{}:".format(length) + (elem + ",") * (length - 1) + elem

    def _make_acl_list(self, length):
        return f'false:{self.make_list(length, "0")}'

    def _make_acl_resource_list(self, length):
        attr_value = {
            "count": length,
            "list": [{"avail_num": "", "bind_point": "", "stage": ""}] * length
        }
        return json.dumps(attr_value).replace(" ", "")

    def _make_map_list(self, length):
        attr_value = {
            "count": length,
            "list": [{"key": 0, "value": 0}] * length
        }
        return json.dumps(attr_value).replace(" ", "")

    def _make_system_port_config_list(self, length):
        attr_value = {
            "count": length,
            "list": [{"port_id": "", "attached_switch_id": "", "attached_core_index": "",
                      "attached_core_port_index": "", "speed": "", "num_voq": ""}] * length
        }
        return json.dumps(attr_value).replace(" ", "")

    @staticmethod
    def __vid_to_type(vid):
        obj_type = int(vid[4:], 16) >> 48
        return "SAI_OBJECT_TYPE_" + SaiObjType(obj_type).name
