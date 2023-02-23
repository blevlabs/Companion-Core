# Import the necessary libraries
import threading
import time
from collections import deque
import datetime

import speech_recognition as sr
import torch
import whisper
from flask import Flask, jsonify
from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding

embedding_model = PretrainedSpeakerEmbedding(
    "speechbrain/spkrec-xvect-voxceleb",
    device=torch.device("cpu" if torch.cuda.is_available() else "cpu"))
from pyannote.audio import Audio
from pyannote.core import Segment
import wave
import contextlib
from ctypes import *

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
from sklearn.cluster import AgglomerativeClustering
import numpy as np

# Create a Flask app
app = Flask(__name__)

# Create a recognizer object
# init parameters
num_speakers = 2  # @param {type:"integer"}
language = 'English'  # @param ['any', 'English']

model_size = 'medium'  # @param ['tiny', 'base', 'small', 'medium', 'large']
whisper_model = whisper.load_model(model_size)
speaker_path = "/home/blabs/Companion-Core/dynamic-system/core/resources/audio/speaker.wav"


def time(secs):
    return datetime.timedelta(seconds=round(secs))


# Define a function that continuously listens to the microphone and updates the latest speech recognition results
def listen_for_speech():
    r = sr.Recognizer()
    available_microphones = sr.Microphone.list_working_microphones()
    # switch the key/value pairs
    available_microphones = {v: k for k, v in available_microphones.items()}
    # print(available_microphones)
    # print("Connecting to microphone...",available_microphones["USB PnP Audio Device: Audio (hw:2,0)"])
    while True:
        # Listen for speech from the microphone
        print("Listening...")
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source)
            data = audio.get_wav_data()
        # write to file
        with open(speaker_path, "wb") as f:
            f.write(data)
            f.close()
        # Use the recognizer to perform speech recognition
        try:
            print("Recognizing...")
            text = whisper_model.transcribe(speaker_path)
            try:
                if text["segments"][0]["no_speech_prob"] > 0.65:
                    continue
            except:
                continue
            segments = text["segments"]
            if len(segments) <= 1:
                # current time in datetime formatted
                curtime = datetime.datetime.now().strftime("%H:%M:%S")
                app.latest_speech = {"text": "Speaker 0: " + text["text"], "timestamp": curtime}
                print(app.latest_speech)
                # Add the speech recognition results to the buffer
                app.speech_buffer.append(app.latest_speech)

                # Make sure the buffer doesn't overflow
                if len(app.speech_buffer) > app.buffer_size:
                    app.speech_buffer.popleft()
                continue
            with contextlib.closing(wave.open(speaker_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
            audio = Audio()

            def segment_embedding(segment):
                start = segment["start"]
                # Whisper overshoots the end timestamp in the last segment
                end = min(duration, segment["end"])
                clip = Segment(start, end)
                waveform, sample_rate = audio.crop(speaker_path, clip)
                return embedding_model(waveform[None])

            embeddings = np.zeros(shape=(len(segments), 192))
            for i, segment in enumerate(segments):
                embeddings[i] = segment_embedding(segment)

            embeddings = np.nan_to_num(embeddings)
            clustering = AgglomerativeClustering(num_speakers).fit(embeddings)
            current_speak_data = []
            labels = clustering.labels_
            for i in range(len(segments)):
                segments[i]["speaker"] = 'SPEAKER ' + str(labels[i] + 1)
            for (i, segment) in enumerate(segments):
                speech_data = "\n" + segment["speaker"] + ' ' + str(time(segment["start"])) + ": " + segment["text"][1:] + ' '
                speech_data = speech_data.strip("\n")
                current_speak_data.append(speech_data)
            # Update the latest speech recognition results
            curtime = datetime.datetime.now().strftime("%H:%M:%S")
            app.latest_speech = {"text": current_speak_data, "timestamp": curtime}
            print(app.latest_speech)
            # Add the speech recognition results to the buffer
            app.speech_buffer.append(app.latest_speech)

            # Make sure the buffer doesn't overflow
            if len(app.speech_buffer) > app.buffer_size:
                app.speech_buffer.popleft()
        except sr.UnknownValueError as e:
            print("Could not understand audio")
            app.latest_speech = {"error": "Could not understand audio"}
        except sr.RequestError as e:
            print(f"Error: {e}")
            app.latest_speech = {"error": e}


@app.route("/health", methods=['POST'])
def health():
    return jsonify({"status": "OK"})


# Define a route that accepts incoming requests and returns the latest speech recognition results
@app.route("/speech", methods=['POST'])
def speech():
    # Return the latest speech recognition results
    return jsonify(app.latest_speech)


# Define a route that accepts incoming requests and returns the historical speech recognition results
@app.route("/speech/history", methods=['POST'])
def speech_history():
    # Return the historical speech recognition results
    return jsonify(list(app.speech_buffer))


# Start the Flask app and the listening thread
if __name__ == "__main__":
    curtime = datetime.datetime.now().strftime("%H:%M:%S")
    # Initialize the latest speech recognition results and the speech buffer
    app.latest_speech = {"text": "", "timestamp": curtime}
    app.speech_buffer = deque()
    app.buffer_size = 100

    # Start the listening thread
    threading.Thread(target=listen_for_speech).start()
    # Start the Flask app
    app.run(port=5000)
    # check if thread is alive
