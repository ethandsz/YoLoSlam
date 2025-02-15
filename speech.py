import pyaudio
import wave
import speech_recognition as sr

# Recording settings (matching your mic's capabilities)
FORMAT = pyaudio.paInt16  # S16_LE
CHANNELS = 1              # Stereo (as required by hardware)
RATE = 44100              # Supported sample rate
CHUNK = 1024              # Buffer size
OUTPUT_FILE = "output.wav"

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Open the microphone stream
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, input_device_index=0,
                    frames_per_buffer=CHUNK)

print("Recording... Press Ctrl+C to stop.")

frames = []
try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
except KeyboardInterrupt:
    print("Recording stopped.")
    stream.stop_stream()
    stream.close()
    audio.terminate()

# Save recording
with wave.open(OUTPUT_FILE, 'wb') as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))

print(f"Saved recording as {OUTPUT_FILE}")

# Function to transcribe the recorded audio
def transcribe_audio(file_path):
    # Initialize recognizer
    recognizer = sr.Recognizer()

    # Open the WAV file and process it
    with sr.AudioFile(file_path) as source:
        print("Processing audio...")
        audio = recognizer.record(source)

    try:
        # Using Google's speech recognition to transcribe the audio
        print("Transcribing audio...")
        transcription = recognizer.recognize_google(audio)
        print("Transcription: " + transcription)
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand the audio.")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")

# Call the transcription function
transcribe_audio(OUTPUT_FILE)

 
