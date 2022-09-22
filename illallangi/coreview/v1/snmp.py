from more_itertools import only
from pysnmp import hlapi


OIDs = {
    "sysName": "1.3.6.1.2.1.1.5.0",
    "ifEntry": "1.3.6.1.2.1.2.1.0",
    "ifAdminStatus": "1.3.6.1.2.1.2.2.1.7",
    "ifOperStatus": "1.3.6.1.2.1.2.2.1.8",
    "ifDescr": "1.3.6.1.2.1.2.2.1.2",
    "ifType": "1.3.6.1.2.1.2.2.1.3",
    "ifSpeed": "1.3.6.1.2.1.2.2.1.5",
    "ifHighSpeed": "1.3.6.1.2.1.31.1.1.1.15",
    "ifAlias": "1.3.6.1.2.1.31.1.1.1.18",
}

OID_Values = {
    "ifAdminStatus": {
        1: "up",
        2: "down",
        3: "testing",
    },
    "ifOperStatus": {
        1: "up",
        2: "down",
        3: "testing",
    },
    "ifType": {
        1: "other",
        2: "regular1822",
        3: "hdh1822",
        4: "ddn-x25",
        5: "rfc877-x25",
        6: "ethernet-csmacd",
        7: "iso88023-csmacd",
        8: "iso88024-tokenBus",
        9: "iso88025-tokenRing",
        10: "iso88026-man",
        11: "starLan",
        12: "proteon-10Mbit",
        13: "proteon-80Mbit",
        14: "hyperchannel",
        15: "fddi",
        16: "lapb",
        17: "sdlc",
        18: "ds1",
        19: "e1",
        20: "basicISDN",
        21: "primaryISDN",
        22: "propPointToPointSerial",
        23: "ppp",
        24: "softwareLoopback",
        25: "eon",
        26: "ethernet-3Mbit",
        27: "nsip",
        28: "slip",
        29: "ultra",
        30: "ds3",
        31: "sip",
        32: "frame-relay",
        53: "propVirtual",
    },
}


def get(
    target,
    oids,
    credentials,
    port=161,
    engine=hlapi.SnmpEngine(),
    context=hlapi.ContextData(),
):
    handler = hlapi.getCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        *construct_object_types(oids)
    )
    return fetch(handler, 1)[0]


def construct_object_types(list_of_oids):
    object_types = []
    for oid in list_of_oids:
        object_types.append(hlapi.ObjectType(hlapi.ObjectIdentity(oid)))
    return object_types


def cast(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return float(value)
        except (ValueError, TypeError):
            try:
                return str(value)
            except (ValueError, TypeError):
                pass
    return value


def fetch(handler, count):
    result = []
    for i in range(count):
        try:
            error_indication, error_status, error_index, var_binds = next(handler)
            if not error_indication and not error_status:
                items = {}
                for var_bind in var_binds:
                    items[str(var_bind[0])] = cast(var_bind[1])
                result.append(items)
            else:
                raise RuntimeError("Got SNMP error: {0}".format(error_indication))
        except StopIteration:
            break
    return result


def get_bulk(
    target,
    oids,
    credentials,
    count,
    start_from=0,
    port=161,
    engine=hlapi.SnmpEngine(),
    context=hlapi.ContextData(),
):
    handler = hlapi.bulkCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        start_from,
        count,
        *construct_object_types(oids)
    )
    return fetch(handler, count)


def get_bulk_auto(
    target,
    oids,
    credentials,
    count_oid,
    start_from=0,
    port=161,
    engine=hlapi.SnmpEngine(),
    context=hlapi.ContextData(),
):
    count = get(target, [count_oid], credentials, port, engine, context)[count_oid]
    return get_bulk(target, oids, credentials, count, start_from, port, engine, context)


def get_system(snmp_hostname, snmp_community):
    sysName = get(
        snmp_hostname, [OIDs["sysName"]], hlapi.CommunityData(snmp_community)
    )[OIDs["sysName"]]
    return {
        "sysName": sysName,
        "snmp": {
            "hostname": snmp_hostname,
            "community": snmp_community,
        },
    }


def get_interfaces(snmp_hostname, snmp_community):
    ifs = get_bulk_auto(
        snmp_hostname,
        [
            OIDs["ifDescr"],
            OIDs["ifOperStatus"],
            OIDs["ifAdminStatus"],
            OIDs["ifType"],
            OIDs["ifSpeed"],
            OIDs["ifHighSpeed"],
            OIDs["ifAlias"],
        ],
        hlapi.CommunityData(snmp_community),
        OIDs["ifEntry"],
    )

    return [
        {
            only(
                [nodeName for nodeName in OIDs if OID.startswith(OIDs[nodeName])],
                OID,
            ): OID_Values.get(
                only(
                    [nodeName for nodeName in OIDs if OID.startswith(OIDs[nodeName])],
                    OID,
                ),
                {},
            ).get(
                Value,
                Value,
            )
            for OID, Value in i.items()
        }
        for i in ifs
    ]
