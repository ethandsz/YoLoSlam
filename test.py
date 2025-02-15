import pyaudio

audio = pyaudio.PyAudio()
device_index = None
 
for i in range(audio.get_device_count()):
    dev = audio.get_device_info_by_index(i)
    if "pulse" in dev["name"].lower():
        device_index = i
        break
 
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, input_device_index=device_index, frames_per_buffer=CHUNK)
audio = pyaudio.PyAudio()
device_index = None
 
for i in range(audio.get_device_count()):
    dev = audio.get_device_info_by_index(i)
    if "pulse" in dev["name"].lower():
        device_index = i
        break
 
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, input_device_index=device_index, frames_per_buffer=CHUNK)
