# 🎙️ Real-Time Audio Event Detection on Embedded Systems

> A production-grade acoustic monitoring system deployed on Raspberry Pi — continuous sound event classification under strict resource and latency constraints.

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-CPU-FF6F00?style=flat-square&logo=tensorflow&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi-C51A4A?style=flat-square&logo=raspberry-pi&logoColor=white)
![Deployment](https://img.shields.io/badge/Deployment-systemd-0078D4?style=flat-square&logo=linux&logoColor=white)
![Status](https://img.shields.io/badge/Status-Actively%20Evolving-brightgreen?style=flat-square)

---

## Overview

Most audio ML demos run offline or assume powerful hardware. This project is different.

It is a **resource-aware, adaptive, real-time system** — not a batch ML script — built to run 24/7 on a constrained embedded platform. It captures live microphone audio, classifies acoustic events using a pretrained deep learning model, and triggers physical and remote alerts when relevant sounds are detected, all while actively managing its own thermal and memory footprint.

---

## Architecture

```
Microphone (44.1 kHz)
        │
        ▼
DSP Resampling → 16 kHz, anti-aliased
        │
        ▼
Deep Learning Inference (YAMNet / TensorFlow)
        │
        ▼
Temporal Aggregation  ──  frame → clip probabilities
        │
        ▼
Semantic Decision Layer
        │
   ┌────┴────────────────┐
   ▼                     ▼
GPIO Buzzer         SMS via Twilio
   └────┬────────────────┘
        │
        ▼
Resource-Aware Adaptive Control Loop
  (CPU Temp · RAM Usage · Inference Latency)
```

---

## Features

### 🎧 Real-Time Audio Processing
- Continuous microphone capture via **PortAudio**
- DSP-based resampling from 44.1 kHz → 16 kHz with anti-aliasing
- Clipping and normalization for stable inference
- Variable window sizing (0.5–2.0 s) to balance latency and robustness

### 🧠 Acoustic Event Detection
- **YAMNet** pretrained on AudioSet — no custom training required
- Full **TensorFlow CPU runtime** (not TFLite) for maximum compatibility
- Offline model loading — no runtime network dependency
- Model warm-up at startup to stabilize inference latency
- Top-K semantic prediction with temporal averaging across frames

### 🧮 Temporal & Semantic Post-Processing
- Frame-level predictions aggregated into clip-level probabilities
- Semantic keyword grouping to handle AudioSet label ambiguity
- Multiple simultaneous alert classes (siren, gunshot, glass break, animals, etc.)
- Rule-based decision layer on top of probabilistic ML output

### 🔁 Adaptive Control Loop
The system continuously monitors its own health and adapts in real time:

| Signal | Response |
|---|---|
| CPU Temperature rising | Increase window length, reduce processing cadence |
| RAM usage climbing | Trigger manual GC, reduce buffer sizes |
| Inference latency spike | Switch to ACTIVE / HIGH / CRITICAL operating mode |

This prevents thermal throttling, memory exhaustion, and long-term instability without requiring manual intervention.

### ⏱️ Non-Blocking, Real-Time Safe Design
- Hardware alerts (GPIO buzzer) executed in **daemon threads**
- Network operations (Twilio SMS) executed **asynchronously**
- Main audio + ML loop is never blocked by I/O

### 🚨 Alerting & Rate Limiting
- Physical alerts via **GPIO buzzer**
- Remote alerts via **Twilio SMS**
- Global cooldown to prevent alert storms
- Per-class cooldowns to avoid repeated notifications for the same event

### 🧯 Embedded Safety
- Explicit GPIO cleanup on startup and exit
- Defensive handling of sensor read failures
- Bounded memory via rolling `deque` buffers
- Manual garbage collection after alert bursts
- Designed for **unattended, long-running execution**

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.9+ |
| ML Model | YAMNet via TensorFlow Hub |
| Runtime | TensorFlow (Full CPU) |
| Audio Capture | PortAudio |
| DSP | Custom resampling pipeline |
| Hardware | Raspberry Pi (Embedded Linux) |
| GPIO | RPi.GPIO |
| Alerting | Twilio SMS API |
| Deployment | systemd microservice |

---

## Observed Runtime Characteristics

Measured on Raspberry Pi under continuous 24/7 operation:

- **Inference latency**: ~80–100 ms (stable)
- **CPU temperature**: maintained well below throttling thresholds
- **Memory usage**: bounded during long runs via rolling buffer design
- **Uptime**: reliable in unattended 24/7 mode

---

## Deployment

The system is designed to run as a **Linux systemd microservice**:

```bash
# Copy service file
sudo cp audio-monitor.service /etc/systemd/system/

# Enable and start
sudo systemctl enable audio-monitor
sudo systemctl start audio-monitor

# View logs
journalctl -u audio-monitor -f
```

The service automatically starts on boot and restarts on crash. System state and performance metrics are logged continuously.

---

## Project Scope

This project sits at the intersection of four research areas:

- **Auditory Scene Analysis** — semantic understanding of real-world acoustic environments
- **Real-Time DSP** — streaming signal processing under strict latency budgets
- **Embedded Machine Learning** — deploying deep learning on constrained hardware
- **Adaptive Systems** — runtime self-monitoring and dynamic resource management

---

## Roadmap

- [ ] Temporal voting / hysteresis for false-positive reduction
- [ ] Confidence-based adaptive thresholds
- [ ] Custom acoustic dataset collection and fine-tuning
- [ ] Lightweight temporal models (HMM / state machines)
- [ ] TFLite migration for reduced inference latency
- [ ] Web dashboard for remote monitoring

---

## Status

**Actively evolving.** Built as a foundation for deeper exploration into real-time audio intelligence on embedded platforms.

---

## License

MIT
