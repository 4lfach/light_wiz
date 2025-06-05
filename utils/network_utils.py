import asyncio
import re
from pywizlight import discovery, wizlight, PilotBuilder

async def find_light_bulbs():
    print("Looking for bulbs...")

    bulbs = await discovery.discover_lights(broadcast_space="192.168.8.255")
    print(f"Found bulbs: {bulbs}")
    return bulbs


async def get_ip_mac_map_filtered(prefix="cc"):
    # Run arp -a asynchronously
    proc = await asyncio.create_subprocess_shell(
        "arp -a",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"Error running arp command: {stderr.decode().strip()}")

    output = stdout.decode()

    # Regex to match IP and MAC addresses with 'dynamic' type
    pattern = re.compile(
        r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:-]{17})\s+dynamic'
    )

    ip_mac_map = {}
    for match in pattern.finditer(output):
        ip = match.group(1)
        mac = match.group(2)
        if mac.lower().startswith(prefix.lower()):
            ip_mac_map[ip] = mac

    return ip_mac_map
