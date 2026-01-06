import os
os.environ["GPIOZERO_PIN_FACTORY"] = "rpigpio"

import sounddevice as sd
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from scipy.signal import resample_poly
from twilio.rest import Client
import psutil, time, csv, threading, gc
from collections import deque

import RPi.GPIO as GPIO
from gpiozero import Buzzer

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()
time.sleep(0.3)

BUZZER_PIN = 18
buzzer = Buzzer(BUZZER_PIN)

def buzzer_alert(duration=10):
    def _beep():
        buzzer.on()
        time.sleep(duration)
        buzzer.off()
    threading.Thread(target=_beep, daemon=True).start()

def three_beeps():
    for _ in range(3):
        buzzer.on()
        time.sleep(0.3)
        buzzer.off()
        time.sleep(0.1)

GLOBAL_COOLDOWN = 30
last_global_alert = 0

TWILIO_ACCOUNT_SID = ""
TWILIO_AUTH_TOKEN  = ""
FROM_PHONE = ""
TO_PHONE   = ""
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

print("Loading YAMNet model")
LOCAL_YAMNET_DIR = "/home/pi/yamnet_local/"
model = hub.load(LOCAL_YAMNET_DIR)
class_map_path = os.path.join(LOCAL_YAMNET_DIR, "yamnet_class_map.csv")
with open(class_map_path, "r") as f:
    class_names = [row[2].lower() for row in csv.reader(f)][1:]
print(f"Model loaded offline with {len(class_names)} classes")

_dummy = np.zeros(16000, dtype=np.float32)
_ = model(_dummy)
print("YAMNet warmup complete.")

class Config:
    MIC_SR        = 44100
    TARGET_SR     = 16000
    CHUNK_DEFAULT = 1.0
    CHUNK_MIN     = 0.5
    CHUNK_MAX     = 2.0
    TEMP_HIGH     = 70
    TEMP_CRITICAL = 80
    RAM_HIGH      = 80
    RAM_CRITICAL  = 90
    ALERT_COOLDOWN = 60
    SLEEP_NORMAL   = 1.0
    SLEEP_FAST     = 0.1
    SLEEP_HIGH     = 2.0
    ALERT_KEYWORDS_SMS     = ["dog", "bark"]
    ALERT_KEYWORDS_GLASS   = ["glass", "shatter", "break"]
    ALERT_KEYWORDS_GUNSHOT = ["gunshot", "gun fire", "gun", "bang"]
    ALERT_KEYWORDS_SIREN   = ["siren", "emergency vehicle", "police car", "ambulance"]
    ALERT_KEYWORDS_HONK    = ["car horn", "honk", "vehicle horn"]
    ALERT_KEYWORDS_PIG     = ["pig", "oink", "snort"]
    ALERT_KEYWORDS_HORSE   = ["horse", "neigh", "whinny"]
    ALERT_KEYWORDS_LION    = ["lion", "roar"]

config = Config()

class PerfMon:
    def __init__(self):
        self.temp = deque(maxlen=10)
        self.ram = deque(maxlen=10)
        self.proc_time = deque(maxlen=10)
        self.last_alert = {
            "dog": 0, "glass": 0, "gunshot": 0, "siren": 0,
            "honk": 0, "pig": 0, "horse": 0, "lion": 0
        }

    def get_temp(self):
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                t = int(f.read()) / 1000
        except:
            t = 45.0
        self.temp.append(t)
        return t

    def get_ram(self):
        r = psutil.virtual_memory().percent
        self.ram.append(r)
        return r

    def log_proc(self, t):
        self.proc_time.append(t)

    def avg(self, arr):
        return np.mean(arr) if arr else 0

perf = PerfMon()

def classify_top5(audio, sr):
    start = time.time()
    if sr != config.TARGET_SR:
        audio = resample_poly(audio, config.TARGET_SR, sr)
    scores, _, _ = model(audio)
    preds = np.mean(scores.numpy(), axis=0)
    top5_idx = preds.argsort()[-5:][::-1]
    labels = [class_names[i] for i in top5_idx]
    perf.log_proc(time.time() - start)
    return labels

def send_sms(label):
    try:
        client.messages.create(
            body=f"Alert: {label.upper()} detected!",
            from_=FROM_PHONE,
            to=TO_PHONE
        )
        print(f"SMS sent: {label.upper()}")
    except Exception as e:
        print(f"SMS failed: {e}")

def send_sms_async(label):
    threading.Thread(target=send_sms, args=(label,), daemon=True).start()

class AdaptiveMgr:
    def __init__(self):
        self.chunk = config.CHUNK_DEFAULT
        self.sleep = config.SLEEP_NORMAL

    def adjust(self, suspected=False):
        t = perf.get_temp()
        r = perf.get_ram()
        level = "NORMAL"
        if t >= config.TEMP_CRITICAL or r >= config.RAM_CRITICAL:
            self.chunk = config.CHUNK_MIN
            self.sleep = config.SLEEP_HIGH
            level = "CRITICAL"
        elif t >= config.TEMP_HIGH or r >= config.RAM_HIGH:
            self.chunk = max(config.CHUNK_MIN, self.chunk * 0.8)
            self.sleep = min(config.SLEEP_HIGH, self.sleep * 1.3)
            level = "HIGH"
        elif suspected:
            self.chunk = config.CHUNK_DEFAULT
            self.sleep = config.SLEEP_FAST
            level = "ACTIVE"
        else:
            self.chunk = min(config.CHUNK_MAX, self.chunk * 1.05)
            self.sleep = config.SLEEP_NORMAL
        print(f"[SYS] {level} | Temp={t:.1f}°C | RAM={r:.1f}% | Win={self.chunk:.2f}s | Sleep={self.sleep:.2f}s | Lat={perf.avg(perf.proc_time)*1000:.1f}ms")
        return self.chunk, self.sleep

adaptive = AdaptiveMgr()

def detect_and_alert(top5):
    global last_global_alert
    now = time.time()
    detected = False

    if now - last_global_alert < GLOBAL_COOLDOWN:
        return False

    def check_alert(keyword_group, key_name, alert_msg):
        nonlocal detected
        global last_global_alert
        if any(k in l for l in top5 for k in keyword_group):
            if now - perf.last_alert[key_name] > config.ALERT_COOLDOWN:
                buzzer_alert()
                send_sms_async(alert_msg)
                perf.last_alert[key_name] = now
                last_global_alert = now
                detected = True

    check_alert(config.ALERT_KEYWORDS_SMS,   "dog",     "Dog Bark")
    check_alert(config.ALERT_KEYWORDS_GLASS, "glass",   "Glass Breaking")
    check_alert(config.ALERT_KEYWORDS_GUNSHOT, "gunshot", "Gunshot")
    check_alert(config.ALERT_KEYWORDS_SIREN,   "siren",   "Siren")
    check_alert(config.ALERT_KEYWORDS_HONK,    "honk",    "Vehicle Horn")
    check_alert(config.ALERT_KEYWORDS_PIG,     "pig",     "Pig/Oink")
    check_alert(config.ALERT_KEYWORDS_HORSE,   "horse",   "Horse Neigh")
    check_alert(config.ALERT_KEYWORDS_LION,    "lion",    "Lion Roar")

    return detected

def get_input_device():
    for i, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0:
            return i, dev
    return None, None

mic_id, device_info = None, None
for _ in range(10):
    mic_id, device_info = get_input_device()
    if mic_id is not None:
        break
    time.sleep(1)

if mic_id is None:
    raise RuntimeError("No microphone found.")

print(f"Using mic: {device_info['name']} ({mic_id}) at {config.MIC_SR} Hz")

three_beeps()

try:
    while True:
        chunk, sleep = adaptive.adjust()
        audio = sd.rec(
            int(chunk * config.MIC_SR),
            samplerate=config.MIC_SR,
            channels=1,
            dtype='float32',
            device=mic_id
        )
        sd.wait()
        audio = np.squeeze(audio)
        audio = np.clip(audio, -1.0, 1.0)
        top5 = classify_top5(audio, config.MIC_SR)
        print(f"Top5: {top5}")
        suspected = detect_and_alert(top5)
        adaptive.adjust(suspected)
        if suspected:
            gc.collect()
        time.sleep(sleep)

except KeyboardInterrupt:
    buzzer.off()
    sd.stop()

except Exception as e:
    print(f"Error: {e}")
    buzzer.off()
    sd.stop()

finally:
    buzzer.off()
    print("Goodbye")
