# Data Enrichment Agent

The Data Enrichment Agent is a Python-based tool that automatically generates and applies feature engineering transformations to enhance your datasets. It analyzes the structure and content of your data, then uses a Large Language Model (LLM) to suggest and create meaningful new features for machine learning and analytics.

## Features

- **Automated Feature Engineering**: Generate new features using LLM-powered suggestions
- **Intelligent Data Profiling**: Automatic analysis of input data characteristics
- **Multiple Data Formats**: Support for CSV, Excel, JSON, and Parquet files
- **Configurable Parameters**: Customize enrichment behavior and thresholds
- **Production-Ready**: Type hints, logging, and error handling throughout
- **Extensible**: Built on a modular framework that allows for easy extension

## Feature Engineering Capabilities

The agent can generate various types of features:

1. **Time-Based Features**
   - Date part extraction
   - Time differences
   - Business day calculations

2. **Numeric Transformations**
   - Polynomial features
   - Binning and discretization
   - Mathematical transformations

3. **Categorical Encodings**
   - One-hot encoding
   - Frequency encoding
   - Target encoding

4. **Interaction Features**
   - Arithmetic combinations
   - Ratio features
   - Conditional features

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) – package & environment manager  
  For quick setup on macOS/Linux:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- [Git](https://git-scm.com/)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/stepfnAI/data_enrichment_agent.git
   cd data_enrichment_agent
   git switch dev
   ```

2. **Set up the virtual environment and install dependencies**
   ```bash
   uv venv --python=3.10 venv
   source venv/bin/activate
   uv pip install -e ".[dev]"
   ```

3. **Clone and install the blueprint dependency**
   ```bash
   cd ..
   git clone https://github.com/stepfnAI/sfn_blueprint.git
   cd sfn_blueprint
   git switch dev
   uv pip install -e .
   cd ../data_enrichment_agent
   ```

4. **export the environment variables**
   ```bash
   export OPENAI_API_KEY="your_openai_api_key"
   ```

## Architecture

The Data Enrichment Agent is built with a modular architecture:

```
data_enrichment_agent/
├── agent.py           # Main agent implementation
├── models.py          # Pydantic models for data structures
├── utils.py           # Helper functions and utilities
├── config.py          # Configuration management
├── constants.py       # Constants and templates
└── cli.py             # Command-line interface
```

## Configuration

The agent can be configured using the `EnrichmentConfig` class. Here are the available configuration options:

```python
from data_enrichment_agent.models import EnrichmentConfig

config = EnrichmentConfig(
    model_name="gpt-4.1-mini",  # LLM model to use
    model_temperature=0.1,      # Temperature for LLM responses
    model_max_tokens=2000,      # Maximum tokens for LLM responses
    ai_provider="openai",       # AI provider to use
    ai_task_type="feature_suggestions_generator", # Task type for AI requests
    
```

## Basic Usage

```python examples/basic_usage.py```

## Testing

Run the test suite using pytest:

```bash
# Run all tests
pytest tests/ -s

# Run specific test
pytest tests/test_agent.py -s

# Run with coverage report
pytest --cov=data_enrichment_agent tests/ -s
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Commit your changes (`git commit -m 'Add some amazing feature'`)
3. Push to the branch (`git push origin feature/amazing-feature`)


