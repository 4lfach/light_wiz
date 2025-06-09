import asyncio
import re
from pywizlight import discovery, wizlight, PilotBuilder

import asyncio

from utils.constants import NUMBER_OF_BULBS

async def find_light_bulbs():
    print("Starting to look for bulbs...")
    
    while True:
        try:
            bulbs = await asyncio.wait_for(
                discovery.discover_lights(broadcast_space="192.168.8.255"),
                timeout=10
            )
            if len(bulbs) != NUMBER_OF_BULBS:
                print(f"Found {len(bulbs)} bulbs, expected {NUMBER_OF_BULBS}. Retrying...")
                await asyncio.sleep(1)
                continue
        except asyncio.TimeoutError:
            print("Timed out waiting for bulbs, retrying...")
            continue
        
        if bulbs:
            for bulb in bulbs:
                await bulb.turn_on(PilotBuilder(brightness=1))
            await asyncio.sleep(1)
            for bulb in bulbs:
                await bulb.turn_off()
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