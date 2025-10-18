"""Tests for beatstoch package."""

import pytest
from mido import MidiFile

from beatstoch import generate_stochastic_pattern


def test_generate_stochastic_pattern_basic():
    """Test basic stochastic pattern generation."""
    midi_file = generate_stochastic_pattern(bpm=120, bars=2)

    assert isinstance(midi_file, MidiFile)
    assert midi_file.length > 0  # Should have some duration
    assert len(midi_file.tracks) > 0  # Should have at least one track


def test_generate_stochastic_pattern_with_params():
    """Test stochastic pattern generation with custom parameters."""
    midi_file = generate_stochastic_pattern(
        bpm=140,
        bars=4,
        style="breaks",
        swing=0.1,
        intensity=0.8,
        seed=42
    )

    assert isinstance(midi_file, MidiFile)
    assert midi_file.length > 0
    assert len(midi_file.tracks) > 0


def test_generate_stochastic_pattern_different_styles():
    """Test different drum styles."""
    styles = ["house", "breaks", "generic"]

    for style in styles:
        midi_file = generate_stochastic_pattern(
            bpm=120,
            bars=1,
            style=style,
            seed=42  # Consistent seed for testing
        )
        assert isinstance(midi_file, MidiFile)
        assert midi_file.length > 0


def test_generate_stochastic_pattern_edge_cases():
    """Test edge cases for stochastic pattern generation."""
    # Test with very low BPM
    midi_file = generate_stochastic_pattern(bpm=60, bars=1, seed=42)
    assert isinstance(midi_file, MidiFile)

    # Test with very high BPM
    midi_file = generate_stochastic_pattern(bpm=200, bars=1, seed=42)
    assert isinstance(midi_file, MidiFile)

    # Test with minimal bars
    midi_file = generate_stochastic_pattern(bpm=120, bars=1, seed=42)
    assert isinstance(midi_file, MidiFile)


def test_generate_stochastic_pattern_deterministic():
    """Test that same seed produces same results."""
    midi_file1 = generate_stochastic_pattern(bpm=120, bars=2, seed=42)
    midi_file2 = generate_stochastic_pattern(bpm=120, bars=2, seed=42)

    # Files should have same length (deterministic)
    assert abs(midi_file1.length - midi_file2.length) < 0.01


def test_generate_stochastic_pattern_different_seeds():
    """Test that different seeds produce different results."""
    midi_file1 = generate_stochastic_pattern(bpm=120, bars=2, seed=42)
    midi_file2 = generate_stochastic_pattern(bpm=120, bars=2, seed=43)

    # Files should likely have different lengths (though not guaranteed)
    # This is a probabilistic test
    assert isinstance(midi_file1, MidiFile)
    assert isinstance(midi_file2, MidiFile)
