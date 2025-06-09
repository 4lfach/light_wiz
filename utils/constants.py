SONG_PATH = "./music/Nirvana.mp3"
CHUNK_MS = 100
MIN_BRIGHTNESS = 10  
MAX_BRIGHTNESS = 255
NUMBER_OF_BULBS = 20

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
    asyncio.run(main())
