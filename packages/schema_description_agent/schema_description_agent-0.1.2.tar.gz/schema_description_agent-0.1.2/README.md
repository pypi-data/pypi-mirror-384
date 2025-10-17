# Schema Description Agent

The Schema Description Agent is a Python-based tool that automatically generates descriptions for tables and their columns. It analyzes the structure and content of a data file, and then uses a Large Language Model (LLM) to produce accurate and concise documentation.

## Features

- **Statistical Analysis:** Automatically calculates key statistics for each column, such as row count, column count, duplicate rows, missing cells, and more.
- **AI-Powered Descriptions:** Leverages LLMs to generate human-readable descriptions for tables and columns based on the statistical analysis.
- **Configurable:** Easily configure the AI provider, model, and other parameters.
- **Extensible:** Built on a modular framework (`sfn_blueprint`) that allows for easy extension and integration.

## Installation

**Prerequisites**


- [uv](https://docs.astral.sh/uv/getting-started/installation/) – package & environment manager  
  Please refer to the official installation guide for the most up-to-date instructions.  
  For quick setup on macOS/Linux, you can currently use:  
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- [Git](https://git-scm.com/)  

**Steps**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/stepfnAI/schema_description_agent.git
    cd schema_description_agent
    git switch dev
    ```

2.  **Create virtual environment and install dependencies:**
    ```bash
    uv sync --extra dev
    source .venv/bin/activate
    ```

3.  **Clone and install the blueprint dependency:**
    The agent requires the `sfn_blueprint` library. Clone it into a sibling directory.
    ```bash
    cd ../
    git clone https://github.com/stepfnAI/sfn_blueprint.git
    cd sfn_blueprint
    git switch dev
    uv pip install -e .
    ```

4.  **Return to the agent directory:**
    ```bash
    cd ../schema_description_agent
    ```

5.  ** set environment variables:**
    ```bash
    export OPENAI_API_KEY='your_openai_api_key'
    ```

## Configuration

You can configure the agent in two ways: using a `.env` file for project-specific settings or by exporting environment variables for more dynamic, shell-level control. Settings loaded via `export` will take precedence over those in a `.env` file.

### Available Settings

The following table details the configuration options available:

| Environment Variable        | Description                                  | Default      |
| --------------------------- | -------------------------------------------- | ------------ |
| `OPENAI_API_KEY or ANTHROPIC_API_KEY`            | **(Required)** Your OpenAI API key.          | *None*       |
| `ai_provider_schema_description`   | The AI provider to use for generating schema descriptions.     | `openai`     |
| `model_name_schema_description`         | The specific AI model to use for schema descriptions.        | `gpt-4o`     |
| `temperature_schema_description`               | AI model temperature (e.g., `0.0` to `2.0`). | `0.3`        |
| `max_tokens_schema_description`                | Maximum tokens for the AI response.          | `4000`       |

### Method 1: Using a `.env` File (Recommended)

For consistent configuration within your project, create a file named `.env` in the root directory and add your settings. This method is ideal for storing API keys and project-wide defaults.

1.  Create a file named `.env` in the root of your project.
2.  Add the key-value pairs for the settings you wish to override.

#### Example `.env` file:

```dotenv
# .env

# --- Required Settings ---
# Provide the API key for the provider you select below.
# For this example, we are using Anthropic.
ANTHROPIC_API_KEY="sk-your-anthropic-api-key-here"

# --- Optional Overrides for the Schema Description Agent ---
# Switch the AI provider to Anthropic
AI_PROVIDER_SCHEMA_DESCRIPTION="anthropic"

# Use a different model from the new provider
MODEL_NAME_SCHEMA_DESCRIPTION="claude-3-haiku-20240307"

# Use a higher temperature for potentially more descriptive responses
TEMPERATURE_SCHEMA_DESCRIPTION=0.7```
```


## Testing

To run the tests, use the following command from the root of the `schema_description_agent` directory:

```bash
# Run all tests
pytest tests/ -s

# test agent    
pytest tests/test_agent.py -s

# test agent with sample data
pytest tests/test_agent_with_data.py -s
```

## Usage

Here is a simple example of how to use the agent:

```bash
python examples/basic_usage.py
```



```python
from schema_description_agent import SchemaDescriptionAgent, SchemaDescriptionConfig

# Create a custom configuration
config = SchemaDescriptionConfig(
    ai_provider_schema_description="anthropic",
    model_name_schema_description="claude-3-opus-20240229",
    temperature_schema_description=0.5
)

# Create an instance of the agent with the custom configuration
agent = SchemaDescriptionAgent(config=config)
```

