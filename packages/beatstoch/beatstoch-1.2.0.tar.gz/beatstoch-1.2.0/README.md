# beatstoch

**BPM-aware stochastic drum MIDI generator** - Create dynamic, probabilistic drum patterns that adapt to any song's BPM.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/james-see/beatstoch/workflows/Release%20and%20Publish/badge.svg)](https://github.com/james-see/beatstoch/actions)
[![uv](https://img.shields.io/badge/built%20with-uv-purple.svg)](https://github.com/astral-sh/uv)
[![GitHub stars](https://img.shields.io/github/stars/james-see/beatstoch.svg?style=social&label=Star)](https://github.com/james-see/beatstoch)

## Features

- **BPM Database Integration**: Automatically looks up song BPM from [BPM Database](https://www.bpmdatabase.com/)
- **Psychoacoustic Algorithm**: Research-based rhythms using golden ratio, Fibonacci sequences, and fractal complexity
- **Multiple Styles**: House, breaks, and generic drum patterns with natural human feel
- **Stochastic Generation**: Creates varied, probabilistic drum patterns with optimal predictability vs surprise balance
- **Golden Ratio Microtiming**: Microtiming variations (20-30ms) for authentic groove perception
- **Natural Velocity Curves**: Sine wave-based dynamics for expressive, human-like drum hits
- **Fractal Pattern Complexity**: Multi-level fractal generation for organic rhythmic complexity
- **MIDI Export**: Generates standard MIDI files compatible with any DAW
- **CLI & Library**: Use as a command-line tool or Python library

## Installation

### Using uv (recommended)
```bash
git clone https://github.com/james-see/beatstoch.git
cd beatstoch
uv sync
```

### Using pip
```bash
pip install mido numpy requests beautifulsoup4
```

## Quick Start

### Command Line Interface

Generate drum patterns from song titles:
```bash
# Generate 8 bars of house-style drums for "1979" by Smashing Pumpkins
uv run beatstoch generate "1979" --artist "Smashing Pumpkins" --bars 8

# Generate breaks-style pattern at 127 BPM
uv run beatstoch generate-bpm 127 --bars 4 --style breaks

# Enable verbose logging to see BPM lookup process
uv run beatstoch generate "Billie Jean" --artist "Michael Jackson" --verbose
```

### Python Library

```python
from beatstoch import generate_from_song, generate_stochastic_pattern

# Generate from song lookup
mid, bpm = generate_from_song(
    "1979",
    artist="Smashing Pumpkins",
    bars=8,
    style="house",
    swing=0.1,
    intensity=0.9,
    groove_intensity=0.8
)
mid.save(f"stoch_1979_{int(bpm)}bpm.mid")
print(f"Generated pattern at {bpm} BPM")

# Generate with explicit BPM
mid2 = generate_stochastic_pattern(
    bpm=127,
    bars=4,
    style="breaks",
    seed=123,
    steps_per_beat=4,
    swing=0.12,
    groove_intensity=0.7
)
mid2.save("stoch_127_breaks.mid")
```

## Command Line Options

### `generate` command (song lookup)
- `title`: Song title (required)
- `--artist`: Artist name (optional, improves BPM lookup accuracy)
- `--bars`: Number of bars to generate (default: 8)
- `--style`: Drum style - `house`, `breaks`, or `generic` (default: house)
- `--steps-per-beat`: Resolution (default: 4)
- `--swing`: Swing amount 0.0-1.0 (default: 0.10)
- `--intensity`: Pattern density 0.0-1.0 (default: 0.9)
- `--groove-intensity`: Psychoacoustic groove strength 0.0-1.0 (default: 0.7)
- `--seed`: Random seed for reproducible patterns
- `--fallback-bpm`: BPM to use if lookup fails
- `--verbose`: Show BPM lookup details

### `generate-bpm` command (explicit BPM)
- `bpm`: Target BPM (required)
- `--bars`: Number of bars (default: 8)
- `--style`: Drum style - `house`, `breaks`, or `generic` (default: house)
- `--steps-per-beat`: Resolution (default: 4)
- `--swing`: Swing amount (default: 0.10)
- `--intensity`: Pattern density (default: 0.9)
- `--groove-intensity`: Psychoacoustic groove strength 0.0-1.0 (default: 0.7)
- `--seed`: Random seed

## Drum Styles

### House
Classic four-on-the-floor kick pattern enhanced with golden ratio timing and fractal hi-hat complexity. Features natural velocity curves and microtiming groove for authentic dance music feel.

### Breaks
Syncopated breakbeat patterns using fractal complexity and Fibonacci probability distributions. Golden ratio microtiming creates the authentic "human feel" groove prized by breakbeat producers.

### Generic
Balanced backbeat pattern with psychoacoustic optimization. Combines predictable structure (85% predictability) with controlled surprise elements for engaging, natural-sounding rhythms suitable for any genre.

## Output

Generated MIDI files are saved with descriptive names:
- `stoch_[artist]_[title]_[bpm]bpm.mid` (from song lookup)
- `stoch_[bpm]bpm.mid` (from explicit BPM)

Files are compatible with all major DAWs and MIDI software.

## Requirements

- Python 3.9+ (tested on 3.9-3.14)
- Internet connection (for BPM database lookup)
- MIDI-compatible software (for playback/editing)

## Dependencies

- [mido](https://github.com/mido/mido) - MIDI file handling
- [numpy](https://numpy.org/) - Numerical computations
- [requests](https://requests.readthedocs.io/) - HTTP requests
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing

## Release Instructions

### Automated Releases (Recommended)

The project includes GitHub Actions that automatically create releases when version tags are pushed.

**To create a new release:**

1. **Update version** in `pyproject.toml` and `src/beatstoch/__init__.py` (if exists)

2. **Update CHANGELOG.md** with new features and fixes

3. **Create and push a version tag:**
   ```bash
   # Ensure you're on main branch and up to date
   git checkout main
   git pull origin main

   # Create annotated tag
   VERSION="1.0.0"
   git tag -a "v${VERSION}" -m "Release version ${VERSION}"

   # Push tag to trigger automated release
   git push origin "v${VERSION}"
   ```

4. **Automated workflow will:**
   - Run tests
   - Build the package
   - Create a GitHub release with distribution files
   - Deploy documentation to GitHub Pages
   - Publish to PyPI (if PYPI_API_TOKEN is configured)

### Manual PyPI Publishing

If automation isn't set up or fails:

1. **Build distributions:**
   ```bash
   uv build
   ```

2. **Upload to PyPI:**
   ```bash
   uv publish
   ```

3. **Verify installation:**
   ```bash
   pip install beatstoch
   beatstoch --help
   ```

### PyPI Setup

1. **Get PyPI API token** from [PyPI Account Settings](https://pypi.org/manage/account/)
2. **Add to GitHub Secrets:** Go to repository Settings > Secrets and variables > Actions
3. **Add `PYPI_API_TOKEN`** with your PyPI API token value

## Documentation

Documentation is automatically built and deployed to GitHub Pages using MkDocs.

- **Live Documentation:** [https://james-see.github.io/beatstoch/](https://james-see.github.io/beatstoch/)
- **Build locally:** `mkdocs serve` (requires MkDocs installation)

## Development

### Setup
```bash
git clone https://github.com/james-see/beatstoch.git
cd beatstoch
uv sync
```

### Testing
```bash
# Run all tests
uv run python -m pytest

# Test with coverage
uv run python -m pytest --cov=src/beatstoch

# Test CLI functionality
uv run beatstoch generate-bpm 120 --bars 2
```

### Building Documentation
```bash
# Install MkDocs
pip install mkdocs mkdocs-material

# Preview locally
mkdocs serve

# Deploy to GitHub Pages
mkdocs gh-deploy
```

## License

This project is released into the public domain under the [Unlicense](https://unlicense.org/).

[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](http://unlicense.org/)

## Contributing

1. Fork the repository at [https://github.com/james-see/beatstoch](https://github.com/james-see/beatstoch)
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run the test suite: `uv run python -m pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## Support

- 📖 [Documentation](https://james-see.github.io/beatstoch/)
- 🐛 [Issue Tracker](https://github.com/james-see/beatstoch/issues)
- 💬 [Discussions](https://github.com/james-see/beatstoch/discussions)
- 📧 [GitHub Repository](https://github.com/james-see/beatstoch)

---

*Generated drum patterns are for educational and creative purposes. Always respect music copyrights and licensing.*
