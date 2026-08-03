from pathlib import Path
import math, struct, wave

NOTES = {
    'G3': 196.00, 'A3': 220.00, 'B3': 246.94, 'C4': 261.63, 'D4': 293.66, 'E4': 329.63,
    'Cs4': 277.18, 'D4': 293.66, 'Ds4': 311.13, 'E4': 329.63,
    'F4': 349.23, 'Fs4': 369.99, 'G4': 392.00, 'Gs4': 415.30, 'A4': 440.00, 'As4': 466.16, 'B4': 493.88,
    'C5': 523.25, 'Cs5': 554.37, 'D5': 587.33, 'Ds5': 622.25, 'E5': 659.25, 'F5': 698.46, 'Fs5': 739.99,
    'G5': 783.99, 'Gs5': 830.61, 'A5': 880.00, 'As5': 932.33, 'B5': 987.77,
}
OUT = Path('assets/audio')
OUT.mkdir(parents=True, exist_ok=True)
rate = 22050
seconds = 0.45
for name, frequency in NOTES.items():
    path = OUT / f'{name}.wav'
    with wave.open(str(path), 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        frames = []
        total = int(rate * seconds)
        for i in range(total):
            t = i / rate
            envelope = max(0.0, 1.0 - i / total)
            sample = 0.32 * envelope * (
                math.sin(2 * math.pi * frequency * t)
                + 0.22 * math.sin(4 * math.pi * frequency * t)
            )
            frames.append(struct.pack('<h', int(max(-1, min(1, sample)) * 32767)))
        wav.writeframes(b''.join(frames))
print(f'Generated {len(NOTES)} original WAV notes.')
