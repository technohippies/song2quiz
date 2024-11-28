# Song2Quiz2

[English](README.md) | [简体中文](README.zh-CN.md)

An advanced lyrics analysis and quiz generation system that leverages AI to provide deep semantic understanding of song lyrics.

## Features

- **Lyrics Analysis**
  - Semantic unit analysis for deep lyrical understanding
  - Vocabulary analysis with context-aware interpretation
  - Content warning system for sensitive material
  - Integration with Genius annotations

- **Quiz Generation**
  - Fill-in-the-blank exercises
  - Multiple choice translation
  - Word order exercises

## Documentation

Full documentation is available at our [Mintlify docs](./docs/).

## Requirements

- Python 3.12+
- Dependencies listed in `requirements.txt`
- API keys for:
  - Genius API
  - OpenRouter API
  - LRCLib API
  - Langfuse (optional, for monitoring)

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/song2quiz2.git
cd song2quiz2
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export GENIUS_API_KEY="your_key_here"
export OPENROUTER_API_KEY="your_key_here"
export LRCLIB_API_KEY="your_key_here"
```

4. Run the analysis pipeline:
```bash
python -m src.scripts.run_pipeline
```

## Project Structure

```
song2quiz2/
├── src/               # Source code
│   ├── flows/         # Prefect workflows
│   ├── services/      # External API integrations
│   ├── tasks/         # Individual task definitions
│   └── utils/         # Utility functions
├── tests/             # Test suite
├── docs/              # Documentation
└── data/              # Data storage
```

## Development

### Testing

Run the test suite:
```bash
pytest
```

### Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the LICENSE file for details.
