import pyaudio

pa = pyaudio.PyAudio()

print("Default Input Device:")
print(pa.get_default_input_device_info())

pa.terminate()