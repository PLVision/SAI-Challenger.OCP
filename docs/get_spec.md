# Specification for GET operation

In order to achieve a maximum level of abstraction GET operation must return a string representation of the value.

#### SAI types  with examples:

##### Boolean:

`booldata` => "true", "false"

##### Strings:

`chardata` => "value"

##### Integers:
`s8`, `u8`, `s16`, `u16`, `s32`, `u32`, `s64`, `u64`, `ptr` => "1000"

##### OID:
`oid` => "0x10001"

##### IP:
`ipaddr` => "192.168.0.1", "2001::1"
`ip4` => "192.168.0.1"
`ip6` => "2001::1"
`ipaddrlist` => "2:192.168.0.1,192.168.0.2"
`ipprefix` => "192.168.0.0/24", "2001::/64"

##### MAC:

`mac` => 00:CC:CC:CC:CC:00

##### Ranges:

`s32range`, `u32range` => "100-200"
`u16rangelist` => "2:100-200,300-400"

##### RX status:

`rx_status` => "0;100"

#### Lists:

Lists format: "size:comma_separated_values":

##### Integer lists:

`s8list`, `u8list`, `s16list`, `u16list`, `s32list`, `u32list` => "2:10,20"

##### Object lists:

`objlist`, `vlanlist` => "3:0x1001,0x1002,0x1003"

#### Other types:

**TODO**: Specification for other types should be added when we are ready to test them. I suggest looking at redis format to cover these.

_aclaction, aclcapability, aclfield, aclresource, authkey, encrypt_key, latchstatus, macsecauthkey, macsecsak, macsecsalt, maplist, porterror, porteyevalues, portlanelatchstatuslist, qosmap, reachability, segmentlist, sysportconfig, sysportconfiglist, tlvlist_

