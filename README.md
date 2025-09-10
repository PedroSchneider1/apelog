# Apelog 🐒
**Smart audio event detection and real-time editing**

Apelog is a software for **multiple audio event detection** and **real-time editing**.
It is designed to help analyze, detect, and process meaningful events from audio recordings, making editing workflows faster and smarter.

---

## 🚀 Features (WIP)

* Detect multiple types of audio events in real-time
* Visualize detected events
* Edit audio streams as they happen
* Export processed audio for further use

---

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/your-username/apelog.git
cd apelog

# (Optional) create a virtual environment
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows

# Install dependencies

```

---

## 📚 Usage

```bash
# Run Apelog
python main.py --input your_audio_file.wav
```

---

## 🎙️ Dependencies

Apelog depends on the following Python packages:

* `numpy` - numerical computations
* `scipy` - signal processing
* `librosa` - audio analysis
* `pyaudio` - microphone input and streaming
* `matplotlib` - visualization
* `soundfile` - reading/writing audio files
* `tensorflow` or `torch` - for ML-based event detection (optional)

You can install all dependencies with:

```bash
pip install numpy scipy librosa pyaudio matplotlib soundfile tensorflow
```

---

## ⚙️ How it works (High-level)

1. **Audio Input**: Load an audio file or capture from microphone.
2. **Event Detection**: Process the audio stream using event detection algorithms (e.g., amplitude peaks, feature extraction, machine learning models).
3. **Real-Time Editing**: Apply editing operations (e.g., trimming, marking, exporting segments) as events are detected.
4. **Output**: Save or stream the processed audio.

---

## 📌 Roadmap

* [ ] Add event classification
* [ ] Improve real-time editing tools
* [ ] Build GUI for visualization
* [ ] Optimize detection with ML models

---

## 🤝 Contributing

Contributions are welcome! Please open issues or submit pull requests to help improve Apelog.

---

## 📚 License

This project is licensed under the **MIT License**.

---

## ✍️ Authors

* **Pedro Schneider** - [LinkedIn](https://www.linkedin.com/in/pedroschneider1) | [GitHub](https://github.com/PedroSchneider1)
* **Gabriel Santana Dias** - [LinkedIn](https://www.linkedin.com/in/gabrielsantana013) | [GitHub](https://github.com/GabrielSantana013)
---
