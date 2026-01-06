# Real-Time Audio Event Detection on Embedded Systems

A production-style real-time audio event detection system deployed on a Raspberry Pi, designed for continuous acoustic scene analysis under strict resource and latency constraints.

This project integrates **digital signal processing, deep learning, embedded systems, and adaptive control** to perform reliable 24/7 sound event monitoring on constrained hardware.

---

## 🔊 Problem Statement

Most audio ML demos operate offline or assume powerful hardware. In real-world environments, systems must:

- Process streaming audio continuously
- Operate under thermal and memory limits
- Avoid blocking on I/O or network calls
- Remain stable over long runtimes
- Adapt behavior dynamically based on system health

This project addresses these constraints explicitly.

---

## 🧠 System Overview

The system continuously captures live microphone audio, classifies acoustic events using a pretrained deep learning model, and triggers physical and remote alerts when relevant sounds are detected.

The pipeline is designed as a **resource-aware, adaptive, real-time system**, not a batch ML script.

---

## 🏗️ High-Level Architecture

Microphone (44.1 kHz)
↓
DSP Resampling (→ 16 kHz, anti-aliased)
↓
Deep Learning Inference (YAMNet)
↓
Temporal Aggregation (frame → clip)
↓
Semantic Decision Layer
↓
┌───────────────┬─────────────────┐
│ GPIO Buzzer │ SMS Notification │
└───────────────┴─────────────────┘
↑
Resource-Aware Adaptive Control Loop
(CPU Temp, RAM Usage, Inference Latency)


---

## ⚙️ Core Features

### 🎧 Real-Time Audio Processing
- Continuous microphone capture using PortAudio
- DSP-based resampling from **44.1 kHz → 16 kHz**
- Clipping and normalization for stable inference
- Variable window sizing (0.5–2.0 s) to balance latency and robustness

---

### 🧠 Acoustic Event Detection (ML)
- Uses **YAMNet** (pretrained on AudioSet)
- Full TensorFlow CPU runtime (not TFLite)
- Offline model loading (no runtime network dependency)
- Model warm-up performed at startup to stabilize inference latency
- Top-K semantic prediction with temporal averaging across frames

---

### 🧮 Temporal & Semantic Post-Processing
- Frame-level predictions aggregated into clip-level probabilities
- Semantic keyword grouping to handle label ambiguity
- Multiple alert classes supported simultaneously (siren, gunshot, glass, animals, etc.)
- Rule-based decision layer on top of probabilistic ML output

---

### 🔁 Adaptive Control & System Optimization
The system continuously monitors its own health and adapts behavior in real time:

- **CPU Temperature Monitoring**
- **RAM Usage Monitoring**
- **Rolling Inference Latency Tracking**

Based on these signals, the system dynamically:
- Adjusts audio window length
- Modifies processing cadence (sleep intervals)
- Switches between NORMAL / ACTIVE / HIGH / CRITICAL operating modes

This prevents:
- thermal throttling
- memory exhaustion
- long-term instability

---

### ⏱️ Non-Blocking, Real-Time Safe Design
- Hardware alerts (buzzer) executed in daemon threads
- Network operations (SMS) executed asynchronously
- Main audio + ML loop is never blocked by I/O
- Safe shutdown and cleanup on exit or failure

---

### 🚨 Alerting & Rate Limiting
- Physical alerts via GPIO buzzer
- Remote alerts via Twilio SMS
- Global cooldown to prevent alert storms
- Per-class cooldowns to avoid repeated notifications
- Designed for real-world usability, not demo behavior

---

### 🧯 Embedded-System Safety
- Explicit GPIO cleanup on startup and exit
- Defensive handling of sensor failures
- Bounded memory usage using rolling buffers (`deque`)
- Manual garbage collection after alert bursts
- Designed for unattended, long-running execution

---

## 🛠️ Technologies Used

- **Python**
- **TensorFlow (Full CPU Runtime)**
- **TensorFlow Hub (YAMNet)**
- **Digital Signal Processing**
- **Raspberry Pi (Embedded Linux)**
- **GPIO / Hardware Control**
- **PortAudio**
- **systemd (service deployment)**
- **Twilio API**

---

## 📈 Observed Runtime Characteristics (Raspberry Pi)

- Stable inference latency (~80–100 ms)
- CPU temperature maintained well below throttling thresholds
- Memory usage bounded during long runs
- Reliable operation in 24/7 mode

---

## 🚀 Deployment

- Designed to run as a **Linux systemd microservice**
- Automatically starts on boot
- Restarts on crash
- Logs system state and performance metrics continuously

---

## 🎯 Motivation & Research Direction

This project sits at the intersection of:
- **Auditory Scene Analysis**
- **Real-Time DSP**
- **Embedded Machine Learning**
- **Adaptive Systems**

Future directions include:
- Temporal voting / hysteresis for further false-positive reduction
- Confidence-based thresholds
- Custom acoustic datasets
- Lightweight temporal models (HMM / state machines)

---

## 📌 Status

Actively evolving.  
Built as a foundation for deeper exploration into real-time audio intelligence on embedded platforms.
