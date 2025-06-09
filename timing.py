import asyncio
import time
from pywizlight import PilotBuilder
from utils.network_utils import find_light_bulbs

REPETITIONS = 20
PERIOD = 3  # seconds
TOTAL_BULBS = 20

async def toggle_bulb(bulb, bulb_id, repetitions=REPETITIONS, period=PERIOD):
    durations = []
    for i in range(repetitions):
        start = time.perf_counter()
        await bulb.turn_on(PilotBuilder(brightness=1))
        await bulb.turn_off()
        end = time.perf_counter()
        duration = end - start
        durations.append(duration)
        print(f"Bulb {bulb_id} - Cycle {i+1} took {duration:.4f} seconds")
        await asyncio.sleep(max(0, period - 0.1))
    mean_duration = sum(durations) / len(durations)
    print(f"Bulb {bulb_id} - Mean toggle time: {mean_duration:.4f} seconds\n")
    return mean_duration

async def main():
    bulbs = await find_light_bulbs()

    print(f"Starting toggle timing test on {len(bulbs)} bulbs...")
    all_mean_times = []

    # Create a list of tasks for all bulbs
    tasks = []
    for idx, bulb in enumerate(bulbs, start=1):
        print(f"Testing bulb {idx} with id {bulb.ip}...")
        tasks.append(toggle_bulb(bulb, idx))

    # Run all tasks concurrently
    all_mean_times = await asyncio.gather(*tasks)

    overall_mean = sum(all_mean_times) / len(all_mean_times) if all_mean_times else 0
    print(f"=== Overall mean toggle execution time across all bulbs: {overall_mean:.4f} seconds ===")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
