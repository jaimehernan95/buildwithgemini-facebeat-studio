import os
import math
import wave
import struct
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False


class AudioProcessor:
    """Audio processing and procedural track generator for FaceBeat-Studio."""

    EXPRESSION_TYPES = ["MouthOpen", "Smile", "BrowRaise"]

    @staticmethod
    def generate_sine_wave(freq: float, duration: float, sample_rate: int = 44100, volume: float = 0.5) -> np.ndarray:
        """Generate a basic sine wave with exponential decay envelope."""
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        envelope = np.exp(-3.0 * t / duration)
        return volume * envelope * np.sin(2 * np.pi * freq * t)

    @classmethod
    def synthesize_lofi_piano(cls, output_path: Path, duration_sec: float = 60.0, bpm: float = 85.0) -> None:
        """Synthesizes a relaxing, copyright-free Lo-Fi Piano progression with chords and vinyl warmth."""
        sr = 44100
        total_samples = int(duration_sec * sr)
        audio = np.zeros(total_samples, dtype=np.float32)

        # Chords progression (Frequencies in Hz): Cmaj7 -> Am7 -> Dm7 -> G7
        chords = [
            [261.63, 329.63, 392.00, 493.88],  # Cmaj7 (C4, E4, G4, B4)
            [220.00, 261.63, 329.63, 392.00],  # Am7 (A3, C4, E4, G4)
            [293.66, 349.23, 440.00, 523.25],  # Dm7 (D4, F4, A4, C5)
            [196.00, 246.94, 293.66, 349.23],  # G7 (G3, B3, D4, F4)
        ]

        beat_duration = 60.0 / bpm
        bar_duration = beat_duration * 4.0
        num_bars = int(math.ceil(duration_sec / bar_duration))

        for bar in range(num_bars):
            chord = chords[bar % len(chords)]
            start_sample = int(bar * bar_duration * sr)

            # Play chord notes with slight arpeggiation/humanization
            for note_idx, freq in enumerate(chord):
                offset_samples = int(note_idx * 0.04 * sr)
                note_start = start_sample + offset_samples
                note_duration = bar_duration * 0.95
                note_len = int(note_duration * sr)

                if note_start + note_len <= total_samples:
                    t = np.linspace(0, note_duration, note_len, endpoint=False)
                    # Warm bell-like piano harmonic blending
                    env = np.exp(-1.8 * t)
                    harmonic1 = 0.5 * np.sin(2 * np.pi * freq * t)
                    harmonic2 = 0.25 * np.sin(2 * np.pi * (freq * 2) * t)
                    harmonic3 = 0.1 * np.sin(2 * np.pi * (freq * 3) * t)
                    note_wave = env * (harmonic1 + harmonic2 + harmonic3)
                    audio[note_start : note_start + note_len] += note_wave * 0.35

            # Add gentle mellow bass root
            bass_freq = chord[0] / 2.0
            bass_len = int(bar_duration * 0.8 * sr)
            if start_sample + bass_len <= total_samples:
                tb = np.linspace(0, bar_duration * 0.8, bass_len, endpoint=False)
                bass_wave = 0.3 * np.sin(2 * np.pi * bass_freq * tb) * np.exp(-1.2 * tb)
                audio[start_sample : start_sample + bass_len] += bass_wave

        # Soft vinyl noise bed
        noise = (np.random.rand(total_samples) * 2 - 1) * 0.015
        audio += noise

        # Normalize and save
        cls._save_wav(output_path, audio, sr)

    @classmethod
    def synthesize_cyber_synth(cls, output_path: Path, duration_sec: float = 60.0, bpm: float = 128.0) -> None:
        """Synthesizes a high-energy copyright-safe Cyber Synth Beat with punchy kicks and leads."""
        sr = 44100
        total_samples = int(duration_sec * sr)
        audio = np.zeros(total_samples, dtype=np.float32)

        beat_duration = 60.0 / bpm
        num_beats = int(duration_sec / beat_duration)

        # Kick drum synthesis on every beat
        for b in range(num_beats):
            start = int(b * beat_duration * sr)
            kick_dur = 0.25
            kick_len = int(kick_dur * sr)
            if start + kick_len <= total_samples:
                t = np.linspace(0, kick_dur, kick_len, endpoint=False)
                # Pitch sweep from 150 Hz to 45 Hz
                freq_sweep = 150.0 * np.exp(-18.0 * t) + 45.0
                kick_env = np.exp(-9.0 * t)
                kick = 0.65 * kick_env * np.sin(2 * np.pi * freq_sweep * t)
                audio[start : start + kick_len] += kick

            # Snare on beats 2 and 4 (0-indexed: b % 4 == 1 or 3)
            if b % 2 == 1:
                snare_dur = 0.22
                snare_len = int(snare_dur * sr)
                if start + snare_len <= total_samples:
                    ts = np.linspace(0, snare_dur, snare_len, endpoint=False)
                    snare_env = np.exp(-14.0 * ts)
                    snare_noise = (np.random.rand(snare_len) * 2 - 1) * 0.45 * snare_env
                    snare_body = 0.25 * np.sin(2 * np.pi * 180.0 * ts) * snare_env
                    audio[start : start + snare_len] += snare_noise + snare_body

            # Hi-hat on offbeats
            offbeat_start = int((b + 0.5) * beat_duration * sr)
            hat_dur = 0.08
            hat_len = int(hat_dur * sr)
            if offbeat_start + hat_len <= total_samples:
                th = np.linspace(0, hat_dur, hat_len, endpoint=False)
                hat_env = np.exp(-35.0 * th)
                hat_noise = (np.random.rand(hat_len) * 2 - 1) * 0.25 * hat_env
                audio[offbeat_start : offbeat_start + hat_len] += hat_noise

        # Cyber synth arpeggio (Pentatonic minor: A4, C5, D5, E5, G5)
        arp_scale = [440.0, 523.25, 587.33, 659.25, 783.99, 880.0]
        step_dur = beat_duration / 2.0
        num_steps = int(duration_sec / step_dur)
        for s in range(num_steps):
            lead_start = int(s * step_dur * sr)
            lead_dur = step_dur * 0.8
            lead_len = int(lead_dur * sr)
            if lead_start + lead_len <= total_samples:
                freq = arp_scale[s % len(arp_scale)]
                tl = np.linspace(0, lead_dur, lead_len, endpoint=False)
                env = np.exp(-6.0 * tl)
                # Sawtooth-like bright synth timbre
                synth = (
                    0.25 * np.sin(2 * np.pi * freq * tl)
                    + 0.15 * np.sin(2 * np.pi * 2 * freq * tl)
                    + 0.08 * np.sin(2 * np.pi * 3 * freq * tl)
                ) * env
                audio[lead_start : lead_start + lead_len] += synth

        cls._save_wav(output_path, audio, sr)

    @classmethod
    def synthesize_funk_groove(cls, output_path: Path, duration_sec: float = 60.0, bpm: float = 110.0) -> None:
        """Synthesizes an upbeat funk acoustic rhythm loop."""
        sr = 44100
        total_samples = int(duration_sec * sr)
        audio = np.zeros(total_samples, dtype=np.float32)

        beat_duration = 60.0 / bpm
        num_beats = int(duration_sec / beat_duration)

        for b in range(num_beats):
            start = int(b * beat_duration * sr)
            # Syncopated groove kick on beats 0, 1.5, 2
            if b % 4 in (0, 2):
                dur = 0.2
                klen = int(dur * sr)
                if start + klen <= total_samples:
                    t = np.linspace(0, dur, klen, endpoint=False)
                    k = 0.6 * np.exp(-10.0 * t) * np.sin(2 * np.pi * (110.0 * np.exp(-15 * t) + 50) * t)
                    audio[start : start + klen] += k

            # Snare on 2 and 4
            if b % 4 in (1, 3):
                dur = 0.2
                slen = int(dur * sr)
                if start + slen <= total_samples:
                    t = np.linspace(0, dur, slen, endpoint=False)
                    s = (np.random.rand(slen) * 2 - 1) * 0.4 * np.exp(-12.0 * t)
                    audio[start : start + slen] += s

            # Funky guitar strum accents
            dur = 0.15
            glen = int(dur * sr)
            if start + glen <= total_samples:
                t = np.linspace(0, dur, glen, endpoint=False)
                chord_freqs = [330.0, 392.0, 493.88] if (b % 2 == 0) else [293.66, 369.99, 440.0]
                strum = sum(0.15 * np.sin(2 * np.pi * f * t) for f in chord_freqs) * np.exp(-8.0 * t)
                audio[start : start + glen] += strum

        cls._save_wav(output_path, audio, sr)

    @classmethod
    def synthesize_sfx(cls, output_path: Path, sfx_type: str = "hit") -> None:
        """Synthesizes short percussive hit or combo sound effects."""
        sr = 44100
        duration = 0.18
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        if sfx_type == "perfect":
            # Crisp chime (880 Hz + 1760 Hz)
            wave_data = 0.4 * np.sin(2 * np.pi * 880 * t) + 0.3 * np.sin(2 * np.pi * 1760 * t)
            wave_data *= np.exp(-12.0 * t)
        elif sfx_type == "great":
            # Warm chime (587 Hz)
            wave_data = 0.5 * np.sin(2 * np.pi * 587.33 * t) * np.exp(-14.0 * t)
        else:
            # Short pop
            wave_data = 0.5 * np.sin(2 * np.pi * 440 * t) * np.exp(-25.0 * t)
        cls._save_wav(output_path, wave_data, sr)

    @classmethod
    def ensure_default_audio_library(cls, audio_dir: Path) -> List[Dict[str, Any]]:
        """Ensures all default royalty-free tracks and SFX exist in the audio directory."""
        audio_dir.mkdir(parents=True, exist_ok=True)
        catalog = [
            {
                "id": "lofi_piano_chill",
                "title": "Lo-Fi Piano Sunset",
                "artist": "FaceBeat SafeStudio",
                "bpm": 85.0,
                "duration": 60.0,
                "type": "lofi",
                "filename": "lofi_piano_chill.wav",
                "is_safe": True,
                "license": "Royalty-Free / DMCA Protected Safe Track",
            },
            {
                "id": "cyber_synth_beat",
                "title": "Neon Grid Pulse",
                "artist": "FaceBeat SafeStudio",
                "bpm": 128.0,
                "duration": 60.0,
                "type": "synthwave",
                "filename": "cyber_synth_beat.wav",
                "is_safe": True,
                "license": "Royalty-Free / DMCA Protected Safe Track",
            },
            {
                "id": "funk_acoustic_groove",
                "title": "Midnight Coffee Funk",
                "artist": "FaceBeat SafeStudio",
                "bpm": 110.0,
                "duration": 60.0,
                "type": "groove",
                "filename": "funk_acoustic_groove.wav",
                "is_safe": True,
                "license": "Royalty-Free / DMCA Protected Safe Track",
            },
        ]

        # Generate audio files if missing or if legacy short version (<3MB)
        track1 = audio_dir / "lofi_piano_chill.wav"
        if not track1.exists() or track1.stat().st_size < 3_000_000:
            cls.synthesize_lofi_piano(track1, duration_sec=60.0, bpm=85.0)

        track2 = audio_dir / "cyber_synth_beat.wav"
        if not track2.exists() or track2.stat().st_size < 3_000_000:
            cls.synthesize_cyber_synth(track2, duration_sec=60.0, bpm=128.0)

        track3 = audio_dir / "funk_acoustic_groove.wav"
        if not track3.exists() or track3.stat().st_size < 3_000_000:
            cls.synthesize_funk_groove(track3, duration_sec=60.0, bpm=110.0)

        sfx_perfect = audio_dir / "sfx_perfect.wav"
        if not sfx_perfect.exists():
            cls.synthesize_sfx(sfx_perfect, "perfect")

        sfx_great = audio_dir / "sfx_great.wav"
        if not sfx_great.exists():
            cls.synthesize_sfx(sfx_great, "great")

        return catalog

    @classmethod
    def generate_procedural_beatmap(
        cls,
        bpm: int = 120,
        duration_sec: float = 60.0,
        difficulty: str = "normal",
    ) -> Dict[str, Any]:
        """Generates a synthetic beatmap for rhythm targets without requiring audio file analysis."""
        norm_diff = str(difficulty or "normal").lower()
        if norm_diff not in ("easy", "normal", "hard"):
            norm_diff = "normal"

        beat_step = {"easy": 1.0, "normal": 0.5, "hard": 0.25}.get(norm_diff, 0.5)
        beat_interval = (60.0 / bpm) * beat_step

        targets = []
        lanes = ["left", "center", "right"]
        current_time = 1.0
        target_id = 1

        while current_time < duration_sec - 0.5:
            expr = cls.EXPRESSION_TYPES[(target_id - 1) % len(cls.EXPRESSION_TYPES)]
            lane = lanes[(target_id - 1) % len(lanes)]
            targets.append({
                "id": target_id,
                "time_sec": round(current_time, 3),
                "time_ms": int(current_time * 1000),
                "expression": expr,
                "lane": lane,
                "points": 100,
            })
            target_id += 1
            current_time += beat_interval

        return {
            "bpm": bpm,
            "duration": round(duration_sec, 2),
            "total_targets": len(targets),
            "difficulty": norm_diff,
            "targets": targets,
        }

    @classmethod
    def analyze_audio(cls, file_path: Path, difficulty: str = "normal") -> Dict[str, Any]:
        """Analyzes an audio file, detects BPM, onsets, and produces a synchronized beatmap."""
        norm_diff = str(difficulty or "normal").lower()
        if norm_diff not in ("easy", "normal", "hard"):
            norm_diff = "normal"

        if not file_path or not file_path.exists() or file_path.stat().st_size < 100:
            # Return resilient fallback beatmap on missing or empty file
            return cls.generate_procedural_beatmap(bpm=120, duration_sec=15.0, difficulty=norm_diff)

        try:
            samples, sr = cls._read_wav(file_path)
            if len(samples) < int(sr * 0.5):  # Less than 0.5s audio
                return cls.generate_procedural_beatmap(bpm=120, duration_sec=15.0, difficulty=norm_diff)
        except Exception:
            return cls.generate_procedural_beatmap(bpm=120, duration_sec=15.0, difficulty=norm_diff)

        duration = len(samples) / float(sr)

        # Estimate energy envelope
        hop_length = int(sr * 0.02)  # 20ms frames
        num_frames = len(samples) // hop_length
        if num_frames < 10:
            return cls.generate_procedural_beatmap(bpm=120, duration_sec=max(5.0, duration), difficulty=norm_diff)

        energy = np.zeros(num_frames)
        for i in range(num_frames):
            frame = samples[i * hop_length : (i + 1) * hop_length]
            energy[i] = np.sqrt(np.mean(frame**2) + 1e-9)

        # Smooth envelope
        window = int(0.1 * sr / hop_length) or 1
        smoothed = np.convolve(energy, np.ones(window) / window, mode="same")

        # Spectral / energy onset peaks
        diff = np.diff(smoothed, prepend=smoothed[0])
        diff[diff < 0] = 0

        # Peak detection threshold based on difficulty
        threshold_factor = {"easy": 1.4, "normal": 1.0, "hard": 0.7}.get(norm_diff, 1.0)
        threshold = np.mean(diff) + threshold_factor * np.std(diff)

        # Detect beat positions
        min_peak_dist_sec = {"easy": 0.55, "normal": 0.35, "hard": 0.22}.get(norm_diff, 0.35)
        min_peak_dist_frames = max(1, int(min_peak_dist_sec / 0.02))

        peak_frames = []
        last_peak = -min_peak_dist_frames
        for f in range(1, num_frames - 1):
            if diff[f] > threshold and diff[f] > diff[f - 1] and diff[f] >= diff[f + 1]:
                if f - last_peak >= min_peak_dist_frames:
                    peak_frames.append(f)
                    last_peak = f

        # Ensure rich rhythmic targets across track duration
        min_targets_needed = max(24, int(duration * 0.6))
        if len(peak_frames) < min_targets_needed:
            # Generate rhythmic supplementary targets at 100-120 BPM
            beat_step = max(15, int((60.0 / 110.0) / 0.02))
            peak_frames = list(range(beat_step, num_frames - beat_step, beat_step))

        # Estimate BPM from inter-peak intervals
        intervals = np.diff(peak_frames) * 0.02
        if len(intervals) > 0:
            median_interval = float(np.median(intervals))
            estimated_bpm = round(60.0 / median_interval) if median_interval > 0.1 else 120
            # Clamp to sensible range
            while estimated_bpm < 70:
                estimated_bpm *= 2
            while estimated_bpm > 180:
                estimated_bpm = round(estimated_bpm / 2)
        else:
            estimated_bpm = 120

        # Construct target nodes mapped to facial expressions
        # Distribute targets evenly across MouthOpen, Smile, BrowRaise
        targets = []
        lanes = ["left", "center", "right"]

        for idx, pf in enumerate(peak_frames):
            time_sec = round(pf * 0.02, 3)
            if time_sec > duration - 0.5:
                break

            # Map expression dynamically based on energy & position
            expr = cls.EXPRESSION_TYPES[idx % len(cls.EXPRESSION_TYPES)]
            lane = lanes[idx % len(lanes)]

            targets.append({
                "id": idx + 1,
                "time_sec": time_sec,
                "time_ms": int(time_sec * 1000),
                "expression": expr,
                "lane": lane,
                "points": 100,
            })

        return {
            "bpm": estimated_bpm,
            "duration": round(duration, 2),
            "total_targets": len(targets),
            "difficulty": norm_diff,
            "targets": targets,
        }

    # Internal WAV helpers
    @staticmethod
    def _save_wav(path: Path, audio: np.ndarray, sample_rate: int) -> None:
        """Saves a normalized floating array as a 16-bit PCM WAV file."""
        # Normalize to prevent clipping
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val * 0.92

        int16_data = (audio * 32767).astype(np.int16)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(int16_data.tobytes())

    @staticmethod
    def _read_wav(path: Path) -> tuple[np.ndarray, int]:
        """Reads a WAV file into a normalized 1D float array and sample rate."""
        with wave.open(str(path), "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw_bytes = wf.readframes(n_frames)

            if sampwidth == 2:
                data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            elif sampwidth == 4:
                data = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
            else:
                data = np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

            if n_channels > 1:
                data = data.reshape(-1, n_channels).mean(axis=1)

            return data, framerate
