import json

from sai import Sai, SaiData, SaiObjType
from sai_dataplane import SaiHostifDataPlane


class SaiDpu(Sai):

    def __init__(self, exec_params):
        super().__init__(exec_params)
        print("__INIT__")
        self.oid = "oid:0x0"
        self.dot1q_br_oid = "oid:0x0"
        self.default_vlan_oid = "oid:0x0"
        self.default_vlan_id = "0"
        self.cpu_port = 0
        self.port_oids = []
        self.dot1q_bp_oids = []

    def init(self, attr):
        print("INIT")
        sw_attr = attr.copy()
        sw_attr.append("SAI_SWITCH_ATTR_INIT_SWITCH")
        sw_attr.append("true")
        sw_attr.append("SAI_SWITCH_ATTR_TYPE")
        sw_attr.append("SAI_SWITCH_TYPE_NPU")

        self.oid = self.create(SaiObjType.SWITCH, sw_attr)
        self.rec2vid[self.oid] = self.oid

        print(self.oid)

        # Default VLAN
        self.default_vlan_oid = self.get(self.oid, ["SAI_SWITCH_ATTR_DEFAULT_VLAN_ID", "oid:0x0"]).oid()
        assert (self.default_vlan_oid != "oid:0x0")

        self.default_vlan_id = self.get(self.default_vlan_oid, ["SAI_VLAN_ATTR_VLAN_ID", ""]).to_json()[1]
        assert (self.default_vlan_id != "0")

        # Ports
        port_num = self.get(self.oid, ["SAI_SWITCH_ATTR_NUMBER_OF_ACTIVE_PORTS", ""]).uint32()
        if port_num > 0:
            self.port_oids = self.get(self.oid,
                                     ["SAI_SWITCH_ATTR_PORT_LIST", self.make_list(port_num, "oid:0x0")]).oids()

            # Default .1Q bridge
            self.dot1q_br_oid = self.get(self.oid, ["SAI_SWITCH_ATTR_DEFAULT_1Q_BRIDGE_ID", "oid:0x0"]).oid()
            assert (self.dot1q_br_oid != "oid:0x0")

            # .1Q bridge ports
            status, data = self.get(self.dot1q_br_oid, ["SAI_BRIDGE_ATTR_PORT_LIST", "1:oid:0x0"], False)
            bport_num = data.uint32()
            assert (status == "SAI_STATUS_BUFFER_OVERFLOW")
            assert (bport_num > 0)

            self.dot1q_bp_oids = self.get(self.dot1q_br_oid,
                                         ["SAI_BRIDGE_ATTR_PORT_LIST", self.make_list(bport_num, "oid:0x0")]).oids()
            assert (bport_num == len(self.dot1q_bp_oids))
        
        #Cpu port
        # self.cpu_port = self.get(self.oid, ["SAI_SWITCH_ATTR_CPU_PORT", ""]).oid()


    def cleanup(self):
        super().cleanup()
        self.port_oids.clear()
        self.dot1q_bp_oids.clear()

    def reset(self):
        self.cleanup()
        self.init([])

