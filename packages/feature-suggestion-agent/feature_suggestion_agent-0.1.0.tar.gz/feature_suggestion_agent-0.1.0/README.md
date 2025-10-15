# Feature Suggestion Agent

The **Feature Suggestion Agent** is an intelligent agent that uses LLMs (Large Language Models) to automatically generate and suggest features for machine learning tasks. It can produce feature definitions, formulas, reasoning, and SQL queries for dataset transformation.

## Features

- Accepts dataset metadata, target information, and modeling approach.
- Generates new feature suggestions using an LLM.
- Provides:
  - Feature name (`title`)
  - Columns used (`columns_involved`)
  - Calculation logic (`formula_logic`)
  - Reasoning for usefulness
  - SQL to create the feature
  - Aggregation/grouping info for window or group operations
- Parses LLM responses into validated Pydantic models.

---

## 📦 Installation

### Prerequisites
- Python 3.11+
- Git
- [**uv**](https://docs.astral.sh/uv/getting-started/installation/) – A fast Python package and environment manager.
    -   For a quick setup on macOS/Linux, you can use:
        ```bash
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/stepfnAI/feature_suggestion_agent.git
   cd feature_suggestion_agent/
   git checkout review
   ```

2. **Set up the virtual environment and install dependencies**
   This command creates a `.venv` folder in the current directory and installs all required packages.
    ```bash
    uv sync --extra dev
    source .venv/bin/activate
    ```

3. **Clone and install the `sfn_blueprint` dependency:**
    The agent requires the `sfn_blueprint` library. The following commands clone it into a sibling directory and install it in editable mode.
    
   ```bash
   cd ..
   git clone https://github.com/stepfnAI/sfn_blueprint.git
   cd sfn_blueprint
   git switch dev
   uv pip install -e .
   cd ../feature_suggestion_agent
   ```

4. **Set up environment variables**
   ```bash   
   # Optional: Configure LLM provider (default: openai)
   export LLM_PROVIDER="your_llm_provider"
   
   # Optional: Configure LLM model (default: gpt-4.1-mini)
   export LLM_MODEL="your_llm_model"
   
   # Required: Your LLM API key (Note: If LLM provider is opeani then 'export OPENAI_API_KEY', if it antropic 'export ANTROPIC_API_KEY', use this accordingly as per LLM provider )
   export OPENAI_API_KEY="your_llm_api_key"
   ```

## 🛠️ Usage

### Basic Usage
```bash
python examples/basic_usage.py
```

## 🧪 Testing
Run the test file:
```bash
pytest -v -s tests/test1.py
```
## 🏗️ Architecture

The Target Synthesis Agent is built with a modular architecture:

- **Core Components**:
  - `agent.py`: Base agent implementation
  - `models.py`: Data models and schemas
  - `constants.py`: prompts
  - `config.py`: model configurations


- **Dependencies**:
  - `sfn-blueprint`: Core framework and utilities
  - `pydantic`: Data validation
  

## 🤝 Contributing

## 📝 License

[Add your license information here]

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact
puneet@stepfunction.ai