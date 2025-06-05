import asyncio
from pydub import AudioSegment
from pydub.playback import play
import simpleaudio
from pywizlight import wizlight, PilotBuilder

SONG_PATH = "./music/Nirvana.mp3"
LAMP_IP = "192.168.8.157"
CHUNK_MS = 100
MIN_BRIGHTNESS = 10  
MAX_BRIGHTNESS = 255

def rms_to_brightness(rms, max_rms):
    # Normalize RMS to brightness range
    norm = rms / max_rms if max_rms else 0
    brightness = int(MIN_BRIGHTNESS + (MAX_BRIGHTNESS - MIN_BRIGHTNESS) * norm)
    return min(max(brightness, MIN_BRIGHTNESS), MAX_BRIGHTNESS)

async def set_brightness(lamp, brightness):
    await lamp.turn_on(PilotBuilder(brightness=brightness))

async def music_lamp_show():        
    song = AudioSegment.from_mp3(SONG_PATH)
    chunks = list(song[::CHUNK_MS])
    max_rms = max(chunk.rms for chunk in chunks)

    lamp = wizlight(LAMP_IP)
    print(f"Connecting to lamp at {LAMP_IP} ...")
    await lamp.turn_on(PilotBuilder(brightness=MIN_BRIGHTNESS))

    print("Starting music and lamp show!")
    play_obj = simpleaudio.play_buffer(song.raw_data,
                                       num_channels=song.channels,
                                       bytes_per_sample=song.sample_width,
                                       sample_rate=song.frame_rate)

    # For each chunk, set lamp brightness
    for i, chunk in enumerate(chunks):
        brightness = rms_to_brightness(chunk.rms, max_rms)
        print(f'Chunk {i}, RMS={chunk.rms}, Brightness={brightness}')
        await set_brightness(lamp, brightness)
        await asyncio.sleep(CHUNK_MS / 1000.0)

        if not play_obj.is_playing():
            break
        
    await lamp.turn_off()
    print("Show finished!")

if __name__ == "__main__":
    asyncio.run(music_lamp_show())
