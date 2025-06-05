ip_mapping = {
    1: "192.168.8.150",
    2: "192.168.8.213",
    3: "192.168.8.120",
    4: "192.168.8.240",
    5: "192.168.8.146",
    6: "192.168.8.140",
    7: "192.168.8.126",
    8: "192.168.8.118",
    9: "192.168.8.194",
    10: "192.168.8.158",
    11: "192.168.8.211",
    12: "192.168.8.141",
    13: "192.168.8.157",
    14: "192.168.8.192",
    15: "192.168.8.186",
    16: "192.168.8.224",
    17: "192.168.8.232",
    18: "192.168.8.199",
    19: "192.168.8.218",
    20: "192.168.8.212"
}

def map_light_bulbs(bulbs):
    """Map the received light bulbs according to the ip_mapping."""
    mapped_bulbs = []
    for number, ip in ip_mapping.items():
        for bulb in bulbs:
            if bulb.ip == ip:
                mapped_bulbs.append((number, bulb))
                break
    return mapped_bulbs