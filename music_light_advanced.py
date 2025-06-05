import asyncio
from pydub import AudioSegment
import simpleaudio
from pywizlight import wizlight, PilotBuilder
from utils.constants import map_light_bulbs  # Import the ip_mapping from utils.py
import numpy as np
from utils.network_utils import find_light_bulbs

freq_ranges = [(0, 250), (251, 500), (501, 2000), (2001, 4000), (4001, 8000)]
CHUNK_MS = 1000
AUDIO_PATH = "./music/test10.mp3"

power_color_mapping = {
    "Red": (255, 0, 0),
    "Yellow": (255, 255, 0),
    "Green": (0, 255, 0),
    "Blue": (0, 0, 255),
}

async def set_light_by_power_and_range(bulbs, power, range, upper_threshold, lower_threshold):
    if power == 0:
        return
    
    row_of_bulbs = None
    range = range[1]
    # print(f"Frequency Range: {range} Hz, Power: {power:.2f} dB")

    if range <= 250:
        row_of_bulbs = bulbs[:4]
    elif range <= 500:
        row_of_bulbs = bulbs[4:8]
    elif range <= 2000:
        row_of_bulbs = bulbs[8:12]
    elif range <= 4000:
        row_of_bulbs = bulbs[12:16]
    else:
        row_of_bulbs = bulbs[16:20]

    await turn_on_bulbs(row_of_bulbs, power, upper_threshold, lower_threshold)

async def turn_on_bulbs(bulbs, power, upper_threshold, lower_threshold):
    wizlights = [bulb[1] for bulb in bulbs]
    
    if upper_threshold == lower_threshold:
        power_lvl = 0 if power < lower_threshold else 4
    else:
        normalized = (power - lower_threshold) / (upper_threshold - lower_threshold)
        # print(f"Normalized Power: {normalized:.2f}")
        power_lvl = int(round(normalized * 2))
        power_lvl = max(0, min(power_lvl, 4))  # Clamp between 0 and 4

    if power_lvl >= 4:
        await wizlights[0].turn_on(PilotBuilder(rgb=power_color_mapping["Red"]))
        await wizlights[1].turn_on(PilotBuilder(rgb=power_color_mapping["Yellow"]))
        await wizlights[2].turn_on(PilotBuilder(rgb=power_color_mapping["Green"]))
        await wizlights[3].turn_on(PilotBuilder(rgb=power_color_mapping["Blue"]))
    elif power_lvl >= 3:
        await wizlights[0].turn_on(PilotBuilder(rgb=power_color_mapping["Red"]))
        await wizlights[1].turn_on(PilotBuilder(rgb=power_color_mapping["Yellow"]))
        await wizlights[2].turn_on(PilotBuilder(rgb=power_color_mapping["Green"]))
        await wizlights[3].turn_off()           
    elif power_lvl >= 2:
        await wizlights[0].turn_on(PilotBuilder(rgb=power_color_mapping["Red"]))
        await wizlights[1].turn_on(PilotBuilder(rgb=power_color_mapping["Yellow"]))
        await wizlights[2].turn_off()
        await wizlights[3].turn_off()
    elif power_lvl >= 1:
        await wizlights[0].turn_on(PilotBuilder(rgb=power_color_mapping["Red"]))
        await wizlights[1].turn_off()
        await wizlights[2].turn_off()
        await wizlights[3].turn_off()
    else:
        await wizlights[0].turn_off()
        await wizlights[1].turn_off()
        await wizlights[2].turn_off()
        await wizlights[3].turn_off()

def pre_calculate_power_mapping(audio_file):
    song = AudioSegment.from_mp3(audio_file)
    chunks = list(song[::CHUNK_MS])  # 1000 ms chunks
    power_mapping = {}

    all_power_values = []

    for i, chunk in enumerate(chunks):
        samples = np.array(chunk.get_array_of_samples())
        if chunk.channels == 2:
            samples = samples[::2]  # Take only one channel for simplicity

        fft_result = np.fft.fft(samples)
        freqs = np.fft.fftfreq(len(fft_result), d=1/song.frame_rate)

        power_values = {}
        for range in freq_ranges:
            min_freq, max_freq = range
            indices = np.where((freqs >= min_freq) & (freqs < max_freq))
            power = np.sum(np.abs(fft_result[indices])**2)
            power_db = 10 * np.log10(power) if power > 0 else 0
            
            power_values[range] = power_db
            all_power_values.append(power_db)

        power_mapping[i] = power_values

    # Sort all power values to calculate thresholds
    all_power_values.sort()
    n = len(all_power_values)
    lower_index = max(0, int(n * 0.20) - 1)   # highest value of lowest 20%
    upper_index = min(n - 1, int(n * 0.80))  # lowest value of highest 20%

    lower_threshold = all_power_values[lower_index] if n > 0 else 0
    upper_threshold = all_power_values[upper_index] if n > 0 else 0

    return power_mapping, upper_threshold, lower_threshold

async def main():
    bulbs = await find_light_bulbs()

    if not bulbs:
        print("No bulbs found.")
        return
    
    mapped_bulbs = map_light_bulbs(bulbs)
    
    # Pre-calculate power mapping and thresholds
    power_mapping, upper_threshold, lower_threshold = pre_calculate_power_mapping(AUDIO_PATH)
    print(f"Pre-calculated power mapping for {len(power_mapping)} chunks.")
    print(f"Upper Threshold (lowest value of highest 20%): {upper_threshold:.2f} dB")
    print(f"Lower Threshold (highest value of lowest 20%): {lower_threshold:.2f} dB")

    song = AudioSegment.from_mp3(AUDIO_PATH)
    play_obj = simpleaudio.play_buffer(song.raw_data,
                                       num_channels=song.channels,
                                       bytes_per_sample=song.sample_width,
                                       sample_rate=song.frame_rate)

    for i, power_values in power_mapping.items():
        for range, power_db in power_values.items():
            await set_light_by_power_and_range(mapped_bulbs, power_db, range, upper_threshold, lower_threshold)

    for bulb in bulbs:
        await bulb.turn_off()
    print("Show finished!")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
