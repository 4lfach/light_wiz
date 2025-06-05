import asyncio

from pywizlight import wizlight, PilotBuilder, discovery
from utils.network_utils import find_light_bulbs
import time

async def main():
    print("Starting program...")
    init_color = (255, 0, 0)  # Start with red color
    
    light_bulbs = await find_light_bulbs()
    bulb = light_bulbs[0]  # Select the first bulb for demonstration

    print(f"Controlling bulb at {bulb.ip}")
    await run_animation(bulb, init_color, color_change = 5)

async def run_animation(bulb, init_color, color_change):
    color = init_color
    await bulb.turn_on(PilotBuilder(rgb=init_color))
    while True:
        color = updatelightColorByHue(color, color_change)
        await bulb.turn_on(PilotBuilder(rgb=color))

def updatelightColorByHue(color, color_change):
    # increase green value first
    r = color[0]
    g = color[1]
    b = color[2]

    if(r == 255 and g < 255 and b == 0):
        g += color_change
        if(g > 255):
            g = 255
    elif(r == 0 and g == 255 and b < 255):
        b += color_change
        if(b > 255):
            b = 255
    elif(r <= 255 and g == 255 and b == 0):
        r -= color_change
        if(r < 0):
            r = 0
    elif (r < 255 and g == 0 and b == 255):
        r += color_change
        if(r > 255):
            r = 255
    elif( r == 0 and g <= 255 and b == 255):
        g -= color_change
        if(g < 0):
            g = 0
    elif (r == 255 and g == 0 and b <= 255):
        b -= color_change
        if(b < 0):
            b = 0
    return (r, g, b)
    
loop = asyncio.get_event_loop()
loop.run_until_complete(main())