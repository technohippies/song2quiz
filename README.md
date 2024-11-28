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
  - Langfuse (for monitoring)
  - Prefect Cloud (optional, for cloud execution)

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/technohippies/song2quiz2.git
cd song2quiz2
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (copy .env.example to .env and fill in your keys):
```bash
cp .env.example .env
# Edit .env with your API keys:
# - GENIUS_API_KEY
# - OPENROUTER_API_KEY
# - LRCLIB_API_KEY
# - LANGFUSE_PUBLIC_KEY
# - LANGFUSE_SECRET_KEY
# - LANGFUSE_HOST
```

4. Configure Prefect (optional for cloud execution):
```bash
# For local execution only:
prefect server start

# For Prefect Cloud:
prefect cloud login
```

5. Run the analysis pipeline:
```bash
# Local execution
python -m src.scripts.run_pipeline

# Cloud execution
prefect deploy -n song2quiz
prefect worker start -p song2quiz-pool
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
