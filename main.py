import pyrealsense2 as rs
import numpy as np
import cv2
import easyocr
from ultralytics import YOLO
from pyneuphonic import Neuphonic, TTSConfig
from pyneuphonic.player import AudioPlayer
from queue import Queue
from threading import Thread
import time
import nltk
from nltk.corpus import words

# Download NLTK word corpus (only needs to be done once)
nltk.download('words')

# Initialize NLTK word set
english_words = set(words.words())

class TTSManager:
    def __init__(self, api_key):
        self.client = Neuphonic(api_key=api_key)
        self.sse = self.client.tts.SSEClient()
        self.tts_config = TTSConfig(
            speed=0.9,
            voice_id='8e9c4bc8-3979-48ab-8626-df53befc2090',
            lang_code='en',  # Replace with the desired language code
            model="neu_hq"
        )
        self.audio_queue = Queue()
        self.last_speech_time = {}
        self.min_speech_interval = 3  # Minimum seconds between announcements
        self.is_speaking = False

        # Start audio processing thread
        self.audio_thread = Thread(target=self._process_audio_queue, daemon=True)
        self.audio_thread.start()

    def _process_audio_queue(self):
        with AudioPlayer() as player:
            while True:
                if not self.audio_queue.empty() and not self.is_speaking:
                    print("TRYING TO PLAY")
                    text = self.audio_queue.get()
                    self.is_speaking = True
                    response = self.sse.send(text, tts_config=self.tts_config)
                    print("PLAYING!")
                    print(response)
                    player.play(response)

                    time.sleep(0.5)  # Short pause after speech
                    self.is_speaking = False
                    self.audio_queue.task_done()
                time.sleep(0.1)

    def should_announce(self, text):
        """Check if text should be announced based on timing constraints"""
        current_time = time.time()
        clean_text = text.strip().lower()  # Normalize text

        if clean_text not in self.last_speech_time:
            self.last_speech_time[clean_text] = current_time
            return True

        if current_time - self.last_speech_time[clean_text] >= self.min_speech_interval:
            self.last_speech_time[clean_text] = current_time
            return True

        return False

def is_actual_word(text):
    """Check if the detected text is an actual English word."""
    # Remove non-alphabetic characters and convert to lowercase
    clean_text = ''.join(filter(str.isalpha, text)).lower()
    if not clean_text:  # Skip empty strings
        return False

    print(clean_text)
    excluded_words = {'snack', 'bake', 'meat'}

    # Check if the word exists in the NLTK word corpus
    return clean_text in english_words

# Initialize components
model = YOLO("yolov8n.pt")
reader = easyocr.Reader(['en'])
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipeline.start(config)

# Initialize TTS system
tts_manager = TTSManager("b9320ad7de75d6dec35ff6f9671b6a0a61925e8e5fb3a5adc5e869cb2c1ff04f.02f607a9-2bd5-4cf4-9ad0-e7603fe1950d")

try:
    while True:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue

        frame = np.asanyarray(color_frame.get_data())
        results = model(frame)

        detected_texts = set()  # To avoid duplicate processing

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Process text region
                roi = frame[y1:y2, x1:x2]
                roi = cv2.resize(roi, (roi.shape[1] * 2, roi.shape[0] * 2), interpolation=cv2.INTER_CUBIC)
                result_text = reader.readtext(roi)

                for (bbox, text, prob) in result_text:
                    if prob > 0.5:
                        # Draw text on frame
                        cv2.putText(frame, text, (x1, y1 - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                        # Add to speech queue if needed
                        clean_text = text.strip().lower()
                        if clean_text not in detected_texts and is_actual_word(clean_text):
                            detected_texts.add(clean_text)
                            if tts_manager.should_announce(clean_text):
                                # Check if the queue is empty before adding new text
                                if tts_manager.audio_queue.empty():
                                    tts_manager.audio_queue.put(f"You are approaching the {text.lower()} aisle.")
                                    print("VALID SIGN DETECTED AND ADDED TO QUEUE")

        cv2.imshow("Signboard Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
