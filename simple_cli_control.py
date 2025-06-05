import asyncio
from pywizlight import wizlight, PilotBuilder, discovery
from utils.network_utils import find_light_bulbs
from utils.constants import map_light_bulbs  # Import the ip_mapping from utils.py

rainbow_colors = [
    (255, 0, 0),      # Red
    (255, 127, 0),    # Orange
    (255, 255, 0),    # Yellow
    (0, 255, 0),      # Green
    (0, 0, 255),      # Blue
    (148, 0, 211)     # Violet
]

async def start_terminal():
    print("Starting terminal...")
    
    bulbs = await find_light_bulbs()
    mapped_bulbs = map_light_bulbs(bulbs)

    await display_menu(mapped_bulbs)

async def display_menu(mapped_bulbs):
    while True:
        print("Menu:")
        print("Select a light bulb to control:")
        for number, bulb in mapped_bulbs:
            print(f"{number}. Light bulb {number} at {bulb.ip}")

        print("0. Exit")
        choice = int(input("Enter your choice: "))
        if choice == 0:
            return
        
        light_index = choice - 1
        if light_index < 0 or light_index >= len(mapped_bulbs):
            print("Invalid selection. Exiting.")
            continue
        
        print("Selected bulb:", mapped_bulbs[light_index][1].ip)

        await display_commands_light_bulb(mapped_bulbs[light_index][1])

async def display_commands_light_bulb(light_bulb):
    print("Commands:")
    print("1. Turn on")
    print("2. Turn off")
    print("3. Set color")
    print("4. Set brightness")
    print("5. Exit")

    command = input("Enter command number: ")
    
    if command == "1":
        await light_bulb.turn_on(PilotBuilder(brightness=1))
    elif command == "2":
        await light_bulb.turn_off()
    elif command == "3":
        await set_light_bulb_color(light_bulb)
    elif command == "4":
        await set_light_bulb_brightness(light_bulb)
    elif command == "5":
        print("Exiting.")
        return
    else:
        print("Invalid command.")

async def set_light_bulb_color(light_bulb):
    print("Write rgb color in format: r g b (e.g. 255 0 0 for red)")
    input_color = input("Enter color: ")
    selected_color = tuple(map(int, input_color.split()))

    await light_bulb.turn_on(PilotBuilder(rgb=selected_color, brightness=1))

async def set_light_bulb_brightness(light_bulb):
    brightness = int(input("Enter brightness: "))

    while brightness < 0 or brightness > 255:
        print("Brightness must be between 0 and 255.")
        brightness = int(input("Enter brightness: "))

    await light_bulb.turn_on(PilotBuilder(brightness=brightness))

async def main():
    await start_terminal()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
