This project converts any MP3 audio file into readable sheet music using machine learning (Using Spotify's Basic Pitch)

## How it works

1. Basic-pitch (spotify) transcribes the audio to MIDI using a neural network
2. Harmonic filtering removes octave/fifth overtones that basic-pitch falsely detects
3. Beat quantization snaps note onset times to detected beat positions using librosa
4. Music21 converts the MIDI into a score with correct clefs and key signatures
5. MuseScore 4 opens the final sheet music automatically

#This will be improved upon in the coming versions
Demucs (Meta) stem seperation is supported for songs with vocals. set `keep_vocals=False` in `main.py` to use the instrumental stem only.

## Requirements
- Python 3.10 (required for basic-pitch compatibility)
- MuseScore 4

## Installation
```bash
python3.10 -m venv basicpitch-env
source basicpitch-env/bin/activate
pip install -r requirements.txt
```

## Usage
Set `mp3_path` in `main.py` to your audio file and run:
```bash
python main.py
```

## Known Limitations
- Works best on slow, monophonic piano recordings
- Harmonic overtones are partially filtered but not fully eliminated
- Triplet detection artifacts are a known basic-pitch limitation
- Tested on Mac M1 only
- 
## Tools Used
- [Basic-pitch](https://github.com/spotify/basic-pitch) — Spotify
- [Demucs](https://github.com/facebookresearch/demucs) — Meta
- [Music21](https://web.mit.edu/music21/) — MIT
- [Librosa](https://librosa.org/)
- [MuseScore 4](https://musescore.org/)
