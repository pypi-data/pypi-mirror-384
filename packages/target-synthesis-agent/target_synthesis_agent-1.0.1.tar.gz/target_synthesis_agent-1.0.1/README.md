# Target Synthesis Agent

An intelligent AI-powered agent for generating and synthesizing target variables for machine learning tasks. This tool analyzes data characteristics and business context to create optimal target variables for various ML applications.

## 🚀 Features

- **AI-Powered Analysis**: Leverages advanced LLM models to analyze data and business context
- **Multiple Data Sources**: Works with both SQL databases and pandas DataFrames
- **Customizable Workflows**: Supports various ML approaches and synthesis strategies
- **Comprehensive Testing**: Includes a complete test suite for reliability
- **Extensible Architecture**: Easy to extend with custom components and integrations

## 📦 Installation

### Prerequisites
- Python 3.10+
- Git
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/stepfnAI/target_synthesis_agent.git
   cd target_synthesis_agent/
   git checkout review
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
   cd ../target_synthesis_agent
   ```

4. **Set up environment variables**
   ```bash   
   # Optional: Configure LLM provider (default: openai)
   export LLM_PROVIDER="your_llm_provider"
   
   # Optional: Configure LLM model (default: gpt-4)
   export LLM_MODEL="your_llm_model"
   
   # Required: Your LLM API key
   export LLM_API_KEY="your_llm_api_key"
   ```

## 🛠️ Usage

### Basic SQL Usage
```bash
python examples/sql_basic_usage.py
```

## 🧪 Testing

Run the complete test suite:
```bash
pytest test/ -s
```

Or run individual test files:
```bash
pytest test/conftest.py -s
pytest test/test_agent.py -s
pytest test/test_sql_agent.py -s
pytest test/test_utils.py -s
```

## 🏗️ Architecture

The Target Synthesis Agent is built with a modular architecture:

- **Core Components**:
  - `sql_agent.py`: Main SQL-based implementation
  - `agent.py`: Base agent implementation
  - `models.py`: Data models and schemas
  - `utils.py`: Utility functions and helpers
  - `constants.py`: Configuration and prompts

- **Dependencies**:
  - `sfn-blueprint`: Core framework and utilities
  - `pandas`: Data manipulation
  - `sqlalchemy`: Database interactions
  - `scikit-learn`: ML utilities

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

For questions or support, please contact [support@stepfunction.ai](mailto:support@stepfunction.ai)

## 🙏 Acknowledgments

- Built with ❤️ by StepFunction AI
- Uses [sfn-blueprint](https://github.com/stepfnAI/sfn_blueprint) for core functionality
- Inspired by modern MLOps best practices