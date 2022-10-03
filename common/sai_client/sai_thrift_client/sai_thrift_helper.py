from sai_thrift import ttypes
from sai_client.sai_thrift_client.sai_thrift_utils import *

def convert_attributes_to_thrift(attributes):
    """
    [ "SAI_SWITCH_ATTR_PORT_LIST", "2:0x0,0x0" ] => { "port_list": sai_thrift_object_list_t(count=2, idlist=[0x0, 0x0]) }
    """
    for name, value in chunks(attributes, 2):
        yield convert_attribute_name_to_thrift(name), convert_value_to_thrift(value, get_attribute_type(name))

def convert_key_to_thrift(object_type, key = None):
    """
    Converts dictionary 'key' to the thrift key entry according to 'object_type':
    "vip_entry", { "switch_id": 0x0, "vip": "192.168.0.1" } => { "vip_entry": sai_thrift_vip_entry_t(switch_id = 0x0, vip = sai_ip_address_t("192.168.0.1"...)) }
    """
    if key is None:
        return {}

    key_t = getattr(ttypes, f'sai_thrift_{object_type}_t')
    return { object_type: key_t(**convert_key_values_to_thrift(object_type, key)) }

def convert_attributes_from_thrift(attributes):
    """
    TODO:
    [ ("SAI_SWITCH_ATTR_PORT_LIST", sai_thrift_object_list_t(...)), ("port_list", sai_thrift_object_list_t(...)) ] => [ "SAI_SWITCH_ATTR_PORT_LIST", "2:0x0,0x0" }
    """
    result_attrs = []
    for name, value in (attributes or {}).items():
        if not name.startswith('SAI'):
            continue
        result_attrs.append(name)
        result_attrs.append(convert_value_from_thrift(value, get_attribute_type(name)))

    return result_attrs

