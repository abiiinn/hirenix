import os
import urllib.request
import zipfile
import json
import librosa
import numpy as np
import wave
from vosk import Model, KaldiRecognizer

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vosk-model-small-en-us-0.15")

def ensure_vosk_model():
    if not os.path.exists(MODEL_DIR):
        print("Downloading lightweight Vosk model (40MB)...")
        url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        zip_path = MODEL_DIR + ".zip"
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(os.path.abspath(__file__)))
        os.remove(zip_path)
        print("Vosk model downloaded.")

def process_voice_interview(audio_path):
    """
    Returns (fluency_score, confidence_score, transcription)
    """
    ensure_vosk_model()
    
    # 1. Librosa: Analyze pauses for confidence score
    # High confidence = less awkward pausing
    try:
        y, sr = librosa.load(audio_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Detect non-silent intervals
        non_mute_intervals = librosa.effects.split(y, top_db=30)
        
        speaking_time = 0.0
        for interval in non_mute_intervals:
            speaking_time += (interval[1] - interval[0]) / sr
            
        silence_time = duration - speaking_time
        
        # Confidence score based on speaking vs silence
        # (Ideal max silence is maybe 25% of the clip)
        if duration > 0:
            speech_ratio = speaking_time / duration
            # Formula: scale 0.5 ratio to 50%, 0.8+ ratio to 100%
            confidence_score = min(max((speech_ratio - 0.3) * 1.5 * 100, 0), 100)
        else:
            confidence_score = 0.0
            
    except Exception as e:
        print(f"Librosa error: {e}")
        confidence_score = 0.0
        duration = 1.0
        
    # 2. Vosk: Transcription and Fluency (WPM)
    transcription = ""
    fluency_score = 0.0
    try:
        model = Model(MODEL_DIR)
        wf = wave.open(audio_path, "rb")
        
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            print("Audio file must be WAV format mono PCM.")
            return confidence_score, 0.0, ""
            
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)
        
        results = []
        text = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                part = json.loads(rec.Result())
                text += part.get("text", "") + " "
                
        part = json.loads(rec.FinalResult())
        text += part.get("text", "") + " "
        transcription = text.strip()
        
        word_count = len(transcription.split())
        
        # Average WPM conversational is ~130-150. Let's say 120 is 100% score
        if duration > 0:
            wpm = word_count / (duration / 60.0)
            if wpm >= 110:
                fluency_score = 100.0
            else:
                fluency_score = (wpm / 110.0) * 100.0
        
    except Exception as e:
        print(f"Vosk error: {e}")
        
    return round(fluency_score, 2), round(confidence_score, 2), transcription
