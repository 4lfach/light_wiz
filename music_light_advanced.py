import asyncio
from pydub import AudioSegment
import simpleaudio
from pywizlight import PilotBuilder
from utils.constants import map_light_bulbs
import numpy as np
from utils.network_utils import find_light_bulbs

freq_ranges = [(0, 250), (251, 500), (501, 2000), (2001, 4000), (4001, 8000)]
CHUNK_MS = 1000
MUSIC_FILES = ["./music/test3.mp3"]
# MUSIC_FILES = ["./music/test0.mp3", "./music/test1.mp3", "./music/test2.mp3"]

power_color_mapping = {
    "Red": (255, 0, 0),
    "Yellow": (255, 255, 0),
    "Green": (0, 255, 0),
    "Blue": (0, 0, 255),
}

def calculate_power_level(power_db: float, lower_threshold: float, upper_threshold: float) -> int:
    """
    Normalize power_db between thresholds and convert to discrete level 0-4.
    """
    if upper_threshold == lower_threshold:
        return 4 if power_db >= lower_threshold else 0
    normalized = (power_db - lower_threshold) / (upper_threshold - lower_threshold)
    level = round(normalized * 4)
    return max(0, min(level, 4))

async def set_light_by_power_and_range(bulbs, power_db, freq_range, upper_threshold, lower_threshold):
    """
    Select bulbs by frequency range and set them based on power_db.
    """
    if power_db <= 0:
        # No power, turn off all in range
        return

    max_freq = freq_range[1]

    # Pre-sliced bulb groups for fixed indices (4 bulbs per range)
    range_bulbs_map = {
        250: bulbs[0:4],
        500: bulbs[4:8],
        2000: bulbs[8:12],
        4000: bulbs[12:16],
        8000: bulbs[16:20],
    }
    
    group = next((group for freq, group in range_bulbs_map.items() if max_freq <= freq), bulbs[16:20])
    # group is a list of tuples
    # Extract wizlight instances from tuples
    row_of_bulbs = [t[1] for t in group]
 
    # Collect all bulb commands in a list
    tasks = []
    power_lvl = calculate_power_level(power_db, lower_threshold, upper_threshold)

    if power_lvl >= 4:
        tasks.append(row_of_bulbs[0].turn_on(PilotBuilder(rgb=power_color_mapping["Red"])))
        tasks.append(row_of_bulbs[1].turn_on(PilotBuilder(rgb=power_color_mapping["Yellow"])))
        tasks.append(row_of_bulbs[2].turn_on(PilotBuilder(rgb=power_color_mapping["Green"])))
        tasks.append(row_of_bulbs[3].turn_on(PilotBuilder(rgb=power_color_mapping["Blue"])))
    elif power_lvl == 3:
        tasks.append(row_of_bulbs[0].turn_on(PilotBuilder(rgb=power_color_mapping["Red"])))
        tasks.append(row_of_bulbs[1].turn_on(PilotBuilder(rgb=power_color_mapping["Yellow"])))
        tasks.append(row_of_bulbs[2].turn_on(PilotBuilder(rgb=power_color_mapping["Green"])))
        tasks.append(row_of_bulbs[3].turn_off())
    elif power_lvl == 2:
        tasks.append(row_of_bulbs[0].turn_on(PilotBuilder(rgb=power_color_mapping["Red"])))
        tasks.append(row_of_bulbs[1].turn_on(PilotBuilder(rgb=power_color_mapping["Yellow"])))
        tasks.append(row_of_bulbs[2].turn_off())
        tasks.append(row_of_bulbs[3].turn_off())
    elif power_lvl == 1:
        tasks.append(row_of_bulbs[0].turn_on(PilotBuilder(rgb=power_color_mapping["Red"])))
        tasks.append(row_of_bulbs[1].turn_off())
        tasks.append(row_of_bulbs[2].turn_off())
        tasks.append(row_of_bulbs[3].turn_off())
    else:
        # All off
        for light in row_of_bulbs:
            tasks.append(light.turn_off())

    # Send all commands in a batch
    await asyncio.gather(*tasks)

def pre_calculate_power_mapping(audio_file):
    """
    Pre-calculate power in dB for each frequency range chunk by chunk.
    Returns:
        power_mapping {chunk_index: {freq_range: power_db}}
        upper_threshold (float)
        lower_threshold (float)
    """
    song = AudioSegment.from_mp3(audio_file)
    chunks = list(song[::CHUNK_MS])  # split into 1 second chunks
    power_mapping = {}
    all_power_values = []

    for i, chunk in enumerate(chunks):
        samples = np.array(chunk.get_array_of_samples())

        if chunk.channels == 2:
            samples = samples[::2]  # simplify stereo to mono

        fft_result = np.fft.fft(samples)
        freqs = np.fft.fftfreq(len(fft_result), d=1/song.frame_rate)

        power_values = {}
        for freq_range in freq_ranges:
            min_freq, max_freq = freq_range
            indices = np.where((freqs >= min_freq) & (freqs < max_freq))
            power = np.sum(np.abs(fft_result[indices]) ** 2)
            power_db = 10 * np.log10(power) if power > 0 else 0

            power_values[freq_range] = power_db
            all_power_values.append(power_db)

        power_mapping[i] = power_values

    all_power_values.sort()
    n = len(all_power_values)

    lower_index = max(0, int(n * 0.20) - 1)
    upper_index = min(n - 1, int(n * 0.80))

    lower_threshold = all_power_values[lower_index] if n > 0 else 0
    upper_threshold = all_power_values[upper_index] if n > 0 else 0

    return power_mapping, upper_threshold, lower_threshold

async def play_song(song):
    """
    Play song asynchronously, non-blocking.
    Returns the play object (simpleaudio.PlayObject).
    """
    play_obj = simpleaudio.play_buffer(
        song.raw_data,
        num_channels=song.channels,
        bytes_per_sample=song.sample_width,
        sample_rate=song.frame_rate
    )
    return play_obj

async def main():
    bulbs = await find_light_bulbs()
    if not bulbs:
        print("No bulbs found.")
        return
    
    mapped_bulbs = map_light_bulbs(bulbs)

    for song_path in MUSIC_FILES:
        power_mapping, upper_threshold, lower_threshold = pre_calculate_power_mapping(song_path)
        print(f"Pre-calculated power mapping for {len(power_mapping)} chunks.")
        print(f"Upper Threshold (lowest of highest 20%): {upper_threshold:.2f} dB")
        print(f"Lower Threshold (highest of lowest 20%): {lower_threshold:.2f} dB")

        song = AudioSegment.from_mp3(song_path)
        play_obj = await play_song(song)

        for chunk_index in range(len(power_mapping)):
            power_values = power_mapping[chunk_index]
            light_tasks = [
                set_light_by_power_and_range(mapped_bulbs, power_db, freq_range, upper_threshold, lower_threshold)
                for freq_range, power_db in power_values.items()
            ]
            # Run bulb updates concurrently per chunk
            await asyncio.gather(*light_tasks)
            await asyncio.sleep(CHUNK_MS / 1000)  # sync timing with music chunk duration

        play_obj.stop()  # Stop playback explicitly when done

    # Turn all bulbs off at end
    off_tasks = [bulb.turn_off() for bulb in bulbs]
    await asyncio.gather(*off_tasks)
    print("Show finished!")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()

