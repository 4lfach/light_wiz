import asyncio
from utils.network_utils import find_light_bulbs
from pywizlight import PilotBuilder

# Desired bulb order, by IP
lights_ip_arrangement = [
    "192.168.8.150", "192.168.8.194", "192.168.8.211",
    "192.168.8.126", "192.168.8.157", "192.168.8.131"
]

async def main():
    print("Starting program...")

    # Discover available bulbs
    discovered_bulbs = await find_light_bulbs()
    if not discovered_bulbs:
        print("No light bulbs found.")
        return

    bulb_by_ip = {str(bulb.ip): bulb for bulb in discovered_bulbs}

    ordered_bulbs = []
    for ip in lights_ip_arrangement:
        bulb = bulb_by_ip.get(ip)
        if bulb is not None:
            ordered_bulbs.append(bulb)
        else:
            print(f"Warning: Bulb with IP {ip} not found among discovered bulbs!")

    if not ordered_bulbs:
        print("No bulbs matched the desired IP arrangement.")
        return

    await run_animation(ordered_bulbs, init_color=(255, 0, 0), speed=0.1)

async def run_animation(bulbs, init_color, speed=1):
    num_bulbs = len(bulbs)

    for bulb in bulbs:
        await bulb.turn_off()
        
    await bulbs[0].turn_on(PilotBuilder(brightness=1, rgb=init_color))

    print("Starting animation in 3 seconds...")
    await asyncio.sleep(3)

    current = 0
    while True:
        await asyncio.sleep(speed)
        await bulbs[current].turn_off()

        next_bulb = (current + 1) % num_bulbs

        await bulbs[next_bulb].turn_on(PilotBuilder(brightness=1, rgb=init_color))

        current = next_bulb

if __name__ == "__main__":
    asyncio.run(main())
