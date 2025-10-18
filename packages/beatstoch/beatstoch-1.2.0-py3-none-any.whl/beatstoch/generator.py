# filename: beatstoch/generator.py
import random
import math
from typing import List, Tuple, Optional

import numpy as np
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo

# General MIDI drum note numbers
DRUMS = {
    "kick": 36,
    "snare": 38,
    "closed_hat": 42,
    "open_hat": 46,
    "ride": 51,
    "clap": 39,
    "tom_low": 41,
    "tom_mid": 45,
    "tom_high": 48,
}

# Psychoacoustic constants based on research
GOLDEN_RATIO = 1.618033988749
GROOVE_TIMING_MS = (20, 30)  # Human-preferred microtiming range
PREDICTABILITY_RATIO = 0.85  # 85% predictable, 15% surprise
FRACTAL_DEPTH = 3  # Fractal recursion depth for natural complexity


def _triangular(mean: float, spread: float) -> float:
    return np.random.triangular(-spread, 0.0, spread) + mean


def _clip_velocity(val: float, lo: int = 1, hi: int = 127) -> int:
    return max(lo, min(hi, int(round(val))))


def _fibonacci_probabilities(steps: int, base_prob: float = 0.3) -> List[float]:
    """Generate probabilities using Fibonacci sequence for natural rhythm patterns."""
    fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
    probs = []

    for i in range(steps):
        # Use Fibonacci ratios for probability modulation
        fib_idx = i % len(fib)
        fib_ratio = fib[fib_idx] / fib[(fib_idx + 1) % len(fib)]
        prob = base_prob * (0.5 + 0.5 * fib_ratio)
        probs.append(min(1.0, prob))

    return probs


def _golden_ratio_timing(steps: int, bpm: float) -> List[float]:
    """Generate timing offsets based on golden ratio for pleasing rhythm."""
    base_timing = 60.0 / bpm  # seconds per beat
    offsets = []

    for i in range(steps):
        # Golden ratio creates pleasing mathematical relationships
        golden_offset = (i * GOLDEN_RATIO) % 1.0
        # Convert to milliseconds for microtiming
        ms_offset = golden_offset * base_timing * 1000
        # Keep within human-preferred groove range
        clamped_offset = max(GROOVE_TIMING_MS[0],
                           min(GROOVE_TIMING_MS[1], ms_offset))
        offsets.append(clamped_offset / 1000.0)  # Convert back to seconds

    return offsets


def _fractal_pattern(length: int, complexity: float) -> List[float]:
    """Generate fractal-based pattern for natural complexity."""
    # Use depth based on length to ensure we get the right number of items
    depth = max(1, int(math.log2(length)) + 1)

    pattern = []
    for _ in range(length):
        # Each position gets a fractal-influenced value
        base_val = random.random()
        detail = sum(random.random() * (0.5 ** (d + 1)) for d in range(depth))
        pattern.append((base_val + detail * complexity) / (1 + complexity))

    return [min(1.0, max(0.0, p)) for p in pattern]


def _natural_velocity_curve(steps: int, base_velocity: Tuple[int, int]) -> List[int]:
    """Generate natural velocity variation using sine wave curves."""
    lo, hi = base_velocity
    velocities = []

    for i in range(steps):
        # Use multiple sine waves for natural variation
        primary = math.sin(i * 0.5) * 0.3  # Main curve
        secondary = math.sin(i * 0.23) * 0.15  # Secondary variation
        tertiary = math.sin(i * 0.77) * 0.1   # High frequency detail

        # Combine waves for natural feel
        combined = primary + secondary + tertiary
        normalized = (combined + 1.0) / 2.0  # Normalize to 0-1

        # Apply to velocity range
        velocity = lo + (hi - lo) * normalized
        velocities.append(_clip_velocity(velocity, lo, hi))

    return velocities


def _psychoacoustic_balance(probs: List[float], predictability: float = PREDICTABILITY_RATIO) -> List[float]:
    """Balance predictability vs surprise for optimal human preference."""
    balanced = []

    for prob in probs:
        # Add controlled randomness while maintaining overall predictability
        if random.random() < predictability:
            # Use original probability (predictable)
            balanced.append(prob)
        else:
            # Add surprise element within reasonable bounds
            surprise_factor = random.uniform(0.1, 0.4)
            if random.random() < 0.5:
                # Increase probability for syncopation
                balanced.append(min(1.0, prob * (1 + surprise_factor)))
            else:
                # Decrease probability for rests
                balanced.append(max(0.0, prob * (1 - surprise_factor)))

    return balanced


def generate_stochastic_pattern(
    bpm: float,
    bars: int = 4,
    meter: Tuple[int, int] = (4, 4),
    steps_per_beat: int = 4,
    swing: float = 0.12,
    intensity: float = 0.9,
    seed: int = 42,
    style: str = "house",
    groove_intensity: float = 0.7,  # New parameter for psychoacoustic groove
) -> MidiFile:
    random.seed(seed)
    np.random.seed(seed)

    beats_per_bar = meter[0]
    steps_per_bar = beats_per_bar * steps_per_beat

    mid = MidiFile(ticks_per_beat=480)
    track = MidiTrack()
    mid.tracks.append(track)
    track.append(Message("program_change", program=0, time=0))
    tempo = bpm2tempo(bpm)
    track.append(MetaMessage("set_tempo", tempo=tempo, time=0))

    # Generate psychoacoustic patterns for each style
    if style == "house":
        # House: Golden ratio four-on-the-floor with fractal hats
        kick_base = _fibonacci_probabilities(steps_per_bar, 0.25)
        kick_probs = [0.98 if (i % steps_per_beat == 0) else p * 0.2 for i, p in enumerate(kick_base)]

        snare_base = _fibonacci_probabilities(steps_per_bar, 0.2)
        snare_probs = [0.95 if (i % (2 * steps_per_beat) == steps_per_beat) else p * 0.15
                      for i, p in enumerate(snare_base)]

        hat_fractal = _fractal_pattern(steps_per_bar, 0.6)
        hat_probs = [p * 0.9 if (i % (steps_per_beat // 2) != 0) else p * 0.7
                    for i, p in enumerate(hat_fractal)]

        instruments = [
            ("kick", kick_probs, (100, 127), 0.002, _natural_velocity_curve),
            ("snare", snare_probs, (95, 120), 0.003, _natural_velocity_curve),
            ("closed_hat", hat_probs, (65, 100), 0.001, _natural_velocity_curve),
            ("open_hat", _fractal_pattern(steps_per_bar, 0.4), (75, 100), 0.004, _natural_velocity_curve),
        ]
    elif style == "breaks":
        # Breaks: Syncopated with golden ratio timing and fractal complexity
        kick_fractal = _fractal_pattern(steps_per_bar, 0.7)
        kick_probs = [0.90 if i in (0, 6, 8, 14) else p * 0.4 for i, p in enumerate(kick_fractal)]

        snare_fractal = _fractal_pattern(steps_per_bar, 0.5)
        snare_probs = [0.92 if i in (4, 12) else p * 0.35 for i, p in enumerate(snare_fractal)]

        hat_probs = _fractal_pattern(steps_per_bar, 0.8)

        instruments = [
            ("kick", kick_probs, (95, 125), 0.003, _natural_velocity_curve),
            ("snare", snare_probs, (95, 125), 0.004, _natural_velocity_curve),
            ("closed_hat", hat_probs, (60, 100), 0.002, _natural_velocity_curve),
            ("open_hat", _fractal_pattern(steps_per_bar, 0.6), (75, 105), 0.005, _natural_velocity_curve),
        ]
    else:
        # Generic: Balanced backbeat with natural variation
        kick_fib = _fibonacci_probabilities(steps_per_bar, 0.22)
        kick_probs = [0.95 if (i % steps_per_beat == 0) else p * 0.25 for i, p in enumerate(kick_fib)]

        snare_fib = _fibonacci_probabilities(steps_per_bar, 0.18)
        snare_probs = [0.90 if (i % (2 * steps_per_beat) == steps_per_beat) else p * 0.25
                      for i, p in enumerate(snare_fib)]

        hat_fractal = _fractal_pattern(steps_per_bar, 0.5)
        hat_probs = [p * 0.8 for p in hat_fractal]

        instruments = [
            ("kick", kick_probs, (90, 120), 0.002, _natural_velocity_curve),
            ("snare", snare_probs, (90, 120), 0.003, _natural_velocity_curve),
            ("closed_hat", hat_probs, (65, 100), 0.001, _natural_velocity_curve),
        ]

    # Apply psychoacoustic balancing and intensity scaling
    for idx, (name, probs, vel_rng, jitter, vel_func) in enumerate(instruments):
        # Balance predictability vs surprise
        balanced_probs = _psychoacoustic_balance(probs, PREDICTABILITY_RATIO)
        # Apply intensity and groove effects
        scaled_probs = [max(0.0, min(1.0, p * intensity * (0.8 + 0.4 * groove_intensity)))
                       for p in balanced_probs]
        instruments[idx] = (name, scaled_probs, vel_rng, jitter, vel_func)

    def _step_to_ticks(step_idx: int, jitter_sec: float, golden_offset: float) -> int:
        base_beats = step_idx / steps_per_beat
        base_ticks = int(round(mid.ticks_per_beat * base_beats))

        # Apply swing
        if steps_per_beat % 2 == 0:
            eighth_step = steps_per_beat // 2
            if (step_idx % eighth_step) == (eighth_step - 1):
                swing_ticks = int(round(mid.ticks_per_beat * (0.5 * swing)))
                base_ticks += swing_ticks

        # Apply golden ratio microtiming for groove
        groove_ticks = int(round(mid.ticks_per_beat * golden_offset))
        base_ticks += groove_ticks

        # Apply traditional jitter
        sec_per_beat = tempo / 1_000_000.0
        ticks_per_sec = mid.ticks_per_beat / sec_per_beat
        jitter_ticks = int(round(jitter_sec * ticks_per_sec))
        return base_ticks + jitter_ticks

    events: List[Tuple[int, str, int]] = []
    # Generate golden ratio timing offsets for the entire pattern
    golden_offsets = _golden_ratio_timing(steps_per_bar * bars, bpm)

    for bar in range(bars):
        bar_offset_steps = bar * steps_per_bar
        for name, probs, vel_rng, jitter, vel_func in instruments:
            lo, hi = vel_rng
            # Generate natural velocity curve for this instrument
            vel_curve = vel_func(steps_per_bar, vel_rng)

            for s in range(steps_per_bar):
                if random.random() < probs[s]:
                    # Use natural velocity curve instead of random triangular
                    vel = _clip_velocity(vel_curve[s] * intensity, lo, hi)

                    # Use golden ratio timing for psychoacoustic groove
                    offset_idx = (bar_offset_steps + s) % len(golden_offsets)
                    golden_offset = golden_offsets[offset_idx] * groove_intensity

                    jitter_sec = _triangular(0.0, jitter)
                    abs_step = bar_offset_steps + s
                    tick = _step_to_ticks(abs_step, jitter_sec, golden_offset)
                    events.append((tick, name, vel))

    events.sort(key=lambda x: x[0])

    last_tick = 0
    for tick, name, vel in events:
        delta = tick - last_tick
        note = DRUMS.get(name, DRUMS["closed_hat"])
        track.append(
            Message("note_on", channel=9, note=note, velocity=vel, time=max(0, delta))
        )
        track.append(Message("note_off", channel=9, note=note, velocity=0, time=60))
        last_tick = tick + 60

    return mid


from .bpm import fetch_bpm_from_bpmdatabase


def generate_from_song(
    song_title: str,
    artist: Optional[str] = None,
    bars: int = 8,
    style: str = "house",
    steps_per_beat: int = 4,
    swing: float = 0.10,
    intensity: float = 0.9,
    groove_intensity: float = 0.7,
    seed: Optional[int] = None,
    fallback_bpm: Optional[float] = None,
    verbose: bool = False,
) -> Tuple[MidiFile, float]:
    bpm = fetch_bpm_from_bpmdatabase(song_title, artist, verbose=verbose)
    if bpm is None:
        if fallback_bpm is None:
            raise RuntimeError("BPM lookup failed and no fallback BPM provided.")
        bpm = fallback_bpm

    if seed is None:
        seed_str = f"{song_title}|{artist or ''}|{int(bpm)}"
        seed = abs(hash(seed_str)) % (2**31)

    mid = generate_stochastic_pattern(
        bpm=bpm,
        bars=bars,
        meter=(4, 4),
        steps_per_beat=steps_per_beat,
        swing=swing,
        intensity=intensity,
        groove_intensity=groove_intensity,
        seed=seed,
        style=style,
    )
    return mid, bpm
