import json
import os
import time
from enum import Enum

import pytest

from sai_abstractions import AbstractEntity

class SaiObjType(Enum):
    PORT                     =  1
    LAG                      =  2
    VIRTUAL_ROUTER           =  3
    NEXT_HOP                 =  4
    NEXT_HOP_GROUP           =  5
    ROUTER_INTERFACE         =  6
    ACL_TABLE                =  7
    ACL_ENTRY                =  8
    ACL_COUNTER              =  9
    ACL_RANGE                = 10
    ACL_TABLE_GROUP          = 11
    ACL_TABLE_GROUP_MEMBER   = 12
    HOSTIF                   = 13
    MIRROR_SESSION           = 14
    SAMPLEPACKET             = 15
    STP                      = 16
    HOSTIF_TRAP_GROUP        = 17
    POLICER                  = 18
    WRED                     = 19
    QOS_MAP                  = 20
    QUEUE                    = 21
    SCHEDULER                = 22
    SCHEDULER_GROUP          = 23
    BUFFER_POOL              = 24
    BUFFER_PROFILE           = 25
    INGRESS_PRIORITY_GROUP   = 26
    LAG_MEMBER               = 27
    HASH                     = 28
    UDF                      = 29
    UDF_MATCH                = 30
    UDF_GROUP                = 31
    FDB_ENTRY                = 32
    SWITCH                   = 33
    HOSTIF_TRAP              = 34
    HOSTIF_TABLE_ENTRY       = 35
    NEIGHBOR_ENTRY           = 36
    ROUTE_ENTRY              = 37
    VLAN                     = 38
    VLAN_MEMBER              = 39
    HOSTIF_PACKET            = 40
    TUNNEL_MAP               = 41
    TUNNEL                   = 42
    TUNNEL_TERM_TABLE_ENTRY  = 43
    FDB_FLUSH                = 44
    NEXT_HOP_GROUP_MEMBER    = 45
    STP_PORT                 = 46
    RPF_GROUP                = 47
    RPF_GROUP_MEMBER         = 48
    L2MC_GROUP               = 49
    L2MC_GROUP_MEMBER        = 50
    IPMC_GROUP               = 51
    IPMC_GROUP_MEMBER        = 52
    L2MC_ENTRY               = 53
    IPMC_ENTRY               = 54
    MCAST_FDB_ENTRY          = 55
    HOSTIF_USER_DEFINED_TRAP = 56
    BRIDGE                   = 57
    BRIDGE_PORT              = 58
    TUNNEL_MAP_ENTRY         = 59
    TAM                      = 60
    SRV6_SIDLIST             = 61
    PORT_POOL                = 62
    INSEG_ENTRY              = 63
    DTEL                     = 64
    DTEL_QUEUE_REPORT        = 65
    DTEL_INT_SESSION         = 66
    DTEL_REPORT_SESSION      = 67
    DTEL_EVENT               = 68
    BFD_SESSION              = 69
    ISOLATION_GROUP          = 70
    ISOLATION_GROUP_MEMBER   = 71
    TAM_MATH_FUNC            = 72
    TAM_REPORT               = 73
    TAM_EVENT_THRESHOLD      = 74
    TAM_TEL_TYPE             = 75
    TAM_TRANSPORT            = 76
    TAM_TELEMETRY            = 77
    TAM_COLLECTOR            = 78
    TAM_EVENT_ACTION         = 79
    TAM_EVENT                = 80
    NAT_ZONE_COUNTER         = 81
    NAT_ENTRY                = 82
    TAM_INT                  = 83
    COUNTER                  = 84
    DEBUG_COUNTER            = 85
    PORT_CONNECTOR           = 86
    PORT_SERDES              = 87
    MACSEC                   = 88
    MACSEC_PORT              = 89
    MACSEC_FLOW              = 90
    MACSEC_SC                = 91
    MACSEC_SA                = 92
    SYSTEM_PORT              = 93
    FINE_GRAINED_HASH_FIELD  = 94
    SWITCH_TUNNEL            = 95
    MY_SID_ENTRY             = 96
    MY_MAC                   = 97
    NEXT_HOP_GROUP_MAP       = 98
    IPSEC                    = 99
    IPSEC_PORT               = 100
    IPSEC_SA                 = 101


class SaiData:
    def __init__(self, data):
        self.data = data

    def raw(self):
        return self.data

    def to_json(self):
        return json.loads(self.data)

    def oid(self, idx = 1):
        value = self.to_json()[idx]
        if "oid:" in value:
            return value
        return "oid:0x0"

    def to_list(self, idx = 1):
        value = self.to_json()[idx]
        idx = value.index(":") + 1
        return value[idx:].split(",")

    def oids(self, idx = 1):
        value = self.to_list(idx)
        if len(value) > 0:
            if "oid:" in value[0]:
                return value
        return []

    def counters(self):
        i = 0
        cntrs_dict = {}
        value = self.to_json()
        while i < len(value):
            cntrs_dict[value[i]] = int(value[i + 1])
            i = i + 2
        return cntrs_dict

    def value(self):
        return self.to_json()[1]

    def uint32(self):
        return int(self.value())


class Sai(AbstractEntity):

    attempts = 40

    # TODO: rename exec_params to setup_dict or so
    def __init__(self, exec_params):
        super().__init__(exec_params)
        self.alias = exec_params['alias']
        self.loglevel = exec_params["loglevel"]
        self.driver = SaiRedisDriver(exec_params["driver"]) #BuildDriver(exec_params["driver"])
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

    def create(self, obj, attrs, do_assert = True):
        return self.driver.create(obj, attrs, do_assert)

    def remove(self, obj, do_assert = True):
        return self.driver.remove(obj, do_assert)

    def set(self, obj, attr, do_assert = True):
        return self.driver.set(obj, attr, do_assert)

    def get(self, obj, attrs, do_assert = True):
        return self.driver.get(obj, attrs, do_assert)

    def bulk_create(self, obj, keys, attrs, do_assert = True):
        return self.driver.bulk_create(obj, keys, attrs, do_assert)

    def bulk_remove(self, obj, keys, do_assert = True):
        return self.driver.bulk_remove(obj, keys, do_assert)

    def bulk_set(self, obj, keys, attrs, do_assert = True):
        return self.driver.bulk_set(obj, keys, attrs, do_assert)

    def get_by_type(self, obj, attr, attr_type, do_assert = True):
        # TODO: Check how to map these types into the struct or list
        unsupported_types = [
                                "sai_port_eye_values_list_t", "sai_prbs_rx_state_t",
                                "sai_port_err_status_list_t", "sai_fabric_port_reachability_t"
                            ]
        if attr_type == "sai_object_list_t":
            status, data = self.get(obj, [attr, "1:oid:0x0"], do_assert)
            if status == "SAI_STATUS_BUFFER_OVERFLOW":
                status, data = self.get(obj, [attr, self.make_list(data.uint32(), "oid:0x0")], do_assert)
        elif attr_type == "sai_s32_list_t" or attr_type == "sai_u32_list_t" or \
                attr_type == "sai_s16_list_t" or attr_type == "sai_u16_list_t" or\
                attr_type == "sai_s8_list_t" or attr_type == "sai_u8_list_t" or attr_type == "sai_vlan_list_t":
            status, data = self.get(obj, [attr, "1:0"], do_assert)
            if status == "SAI_STATUS_BUFFER_OVERFLOW":
                status, data = self.get(obj, [attr, self.make_list(data.uint32(), "0")], do_assert)
        elif attr_type == "sai_acl_capability_t":
            status, data = self.get(obj, [attr, self.make_acl_list(1)], do_assert)
            if status == "SAI_STATUS_BUFFER_OVERFLOW":
                # extract number of actions supported for the stage
                # e.g. ["SAI_SWITCH_ATTR_ACL_STAGE_EGRESS","true:51"] -> 51
                length = int(data.to_json()[1].split(":")[1])
                status, data = self.get(obj, [attr, self.make_acl_list(length)], do_assert)
        elif attr_type == "sai_acl_resource_list_t":
            status, data = self.get(obj, [attr, self.make_acl_resource_list(1)], do_assert)
            if status == "SAI_STATUS_BUFFER_OVERFLOW":
                # extract number of actions supported for the stage
                # e.g. ['SAI_SWITCH_ATTR_AVAILABLE_ACL_TABLE', '{"count":10,"list":null}'] -> 10
                length = json.loads(data.to_json()[1])["count"]
                status, data = self.get(obj, [attr, self.make_acl_resource_list(length)], do_assert)
        elif attr_type == "sai_map_list_t":
            status, data = self.get(obj, [attr, self.make_map_list(1)], do_assert)
            if status == "SAI_STATUS_BUFFER_OVERFLOW":
                length = json.loads(data.to_json()[1])["count"]
                status, data = self.get(obj, [attr, self.make_map_list(length)], do_assert)
        elif attr_type == "sai_system_port_config_list_t":
            status, data = self.get(obj, [attr, self.make_system_port_config_list(1)], do_assert)
            if status == "SAI_STATUS_BUFFER_OVERFLOW":
                length = json.loads(data.to_json()[1])["count"]
                status, data = self.get(obj, [attr, self.make_system_port_config_list(length)], do_assert)
        elif attr_type == "sai_object_id_t":
            status, data = self.get(obj, [attr, "oid:0x0"], do_assert)
        elif attr_type == "bool":
            status, data = self.get(obj, [attr, "true"], do_assert)
        elif attr_type == "sai_mac_t":
            status, data = self.get(obj, [attr, "00:00:00:00:00:00"], do_assert)
        elif attr_type == "sai_ip_address_t":
            status, data = self.get(obj, [attr, "0.0.0.0"], do_assert)
        elif attr_type == "sai_ip4_t":
            status, data = self.get(obj, [attr, "0.0.0.0&mask:0.0.0.0"], do_assert)
        elif attr_type == "sai_ip6_t":
            status, data = self.get(obj, [attr, "::0.0.0.0&mask:0:0:0:0:0:0:0:0"], do_assert)
        elif attr_type == "sai_u32_range_t" or attr_type == "sai_s32_range_t":
            status, data = self.get(obj, [attr, "0,0"], do_assert)
        elif attr_type in unsupported_types:
            status, data = "not supported", None
        elif attr_type.startswith("sai_") or attr_type == "" or attr_type == "char":
            status, data = self.get(obj, [attr, ""], do_assert)
        else:
            assert False, f"Unsupported attribute type: get_by_type({obj}, {attr}, {attr_type})"
        return status, data

    def get_list(self, obj, attr, value):
        status, data = self.get(obj, [attr, "1:" + value], False)
        if status == "SAI_STATUS_BUFFER_OVERFLOW":
            in_data = self.make_list(data.uint32(), value)
            data = self.get(obj, [attr, in_data])
        else:
            assert status == 'SAI_STATUS_SUCCESS', f"get_list({obj}, {attr}, {value}) --> {status}"

        return data.to_list()

    def get_oids(self, obj_type=None):
        return self.driver.get_oids(obj_type)

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

    def assert_status_success(self, status, skip_not_supported=True, skip_not_implemented=True):
        if skip_not_supported:
            if status == "SAI_STATUS_NOT_SUPPORTED" or status == "SAI_STATUS_ATTR_NOT_SUPPORTED_0":
                pytest.skip("not supported")

        if skip_not_implemented:
            if status == "SAI_STATUS_NOT_IMPLEMENTED" or status == "SAI_STATUS_ATTR_NOT_IMPLEMENTED_0":
                pytest.skip("not implemented")

        assert status == "SAI_STATUS_SUCCESS"

    def assert_status_success(self, status, skip_not_supported=True, skip_not_implemented=True):
        if skip_not_supported:
            if status == "SAI_STATUS_NOT_SUPPORTED" or status == "SAI_STATUS_ATTR_NOT_SUPPORTED_0":
                pytest.skip("not supported")

        if skip_not_implemented:
            if status == "SAI_STATUS_NOT_IMPLEMENTED" or status == "SAI_STATUS_ATTR_NOT_IMPLEMENTED_0":
                pytest.skip("not implemented")

        assert status == "SAI_STATUS_SUCCESS"

    def make_list(self, length, elem):
        return "{}:".format(length) + (elem + ",") * (length - 1) + elem

    def make_acl_list(self, length):
        return f'false:{self.make_list(length, "0")}'

    def make_acl_resource_list(self, length):
        attr_value = {
            "count": length,
            "list": [{"avail_num": "", "bind_point": "", "stage": ""}] * length
        }
        return json.dumps(attr_value).replace(" ", "")

    def make_map_list(self, length):
        attr_value = {
            "count": length,
            "list": [{"key": 0, "value": 0}] * length
        }
        return json.dumps(attr_value).replace(" ", "")

    def make_system_port_config_list(self, length):
        attr_value = {
            "count": length,
            "list": [{"port_id": "", "attached_switch_id": "", "attached_core_index": "",
                      "attached_core_port_index": "", "speed": "", "num_voq": ""}] * length
        }
        return json.dumps(attr_value).replace(" ", "")

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

