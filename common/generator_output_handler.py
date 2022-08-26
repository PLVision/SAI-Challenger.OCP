from sai_npu import SaiNpu

class GeneratorOutputHandler():
    def __init__(self, exec_params):
        self.objects_db = {}
        self.sai_implementation = SaiNpu(exec_params)

        # $SWITCH_ID is predefined
        self.objects_db["$SWITCH_ID"] = sai_implementation.get_switch_id()

    @staticmethod
    def create_object_key(object_type, key):
        # Return something like that:
        # oid only: 'SAI_OBJECT_TYPE_SWITCH'
        # with key: 'SAI_OBJECT_TYPE_FDB_ENTRY:{"bvid": "oid:0x260000000005c7", "mac": "00:11:11:11:11:11", "switch_id": "oid:0x21000000000000"}'
        if type(key) is str:
            return object_type
        return object_type + json.dumps(key)

    def populate_from_db(self, list_or_dict):
        # Loop over all attributes and change all that start with '$' to OIDs from DB:
        # list_or_dict["switch_id"] == "$SWITCH_OID"    -> list_or_dict["switch_id"] == "oid:0x21000000000000"
        # list_or_dict[1] == "$SWITCH_OID"              -> list_or_dict[1] == "oid:0x21000000000000"
        # Need to be done for both 'command["key"]' and 'command["attributes"]'
        if type(list_or_dict) is dict:
            for item in list_or_dict.items():
                if item[1].startswith("$"):
                    list_or_dict[item[0]) = self.object_db[item[1]]
        if type(list_or_dict) is list:
            for idx, item in enumerate(list_or_dict):
                if item.startswith("$"):
                    list_or_dict[idx] = self.object_db(item)

    def process_command(self, command):
        '''
        Command examples:
            {
                "action" : "create",
                "type" : "OBJECT_TYPE_VIP_ENTRY",
                "key" : {
                    "switch_id" : "$SWITCH_ID",
                    "vip" : "192.168.0.1"
                },
                "attributes" : [ "SAI_VIP_ENTRY_ATTR_ACTION", "SAI_VIP_ENTRY_ACTION_ACCEPT" ]
            }

            {
                "action" : "create",
                "type" : "SAI_OBJECT_TYPE_DASH_ACL_GROUP",
                "key": "$acl_in_1",
                "attributes" : [ "SAI_DASH_ACL_GROUP_ATTR_IP_ADDR_FAMILY", "SAI_IP_ADDR_FAMILY_IPV4" ]
            },
        '''
        populate_from_db(command["attributes"])
        populate_from_db(command["key"])

        object_key = create_object_key(command["type"], command["key"])

        if command["action"] == "create":
            if type(key) is str: # Store to the DB
                self.object_db[key] = sai_implementation.create(object_key, attributes)
            else:
                sai_implementation.create(object_key, attributes)

        if command["action"] == "remove":
            sai_implementation.remove(object_key)
            if type(key) is str: # remove from the DB
                del object_db[key]
