# Table Categorization Agent

An LLM-driven agent that analyzes data tables and categorizes them based on domain schemas. This agent identifies entities, attributes, and relationships from data and maps them to domain concepts.

## Features

- **LLM-Driven Analysis**: Uses advanced language models to understand table descriptions and content.
- **Domain Schema Integration**: Maps tables to domain entities using JSON schema definitions.
- **Metadata-based Categorization**: Categorizes tables based on their descriptions and metadata.

## Installation
### Prerequisites
- Git access to required repositories
- [uv](https://docs.astral.sh/uv/getting-started/installation/) – package & environment manager  
  Please refer to the official installation guide for the most up-to-date instructions.  
  For quick setup on macOS/Linux, you can currently use:  
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- OpenAI API key


### Step-by-Step Installation

1. **Clone the main repository:**
   ```bash
   git clone https://github.com/stepfnAI/table_categorization_agent.git
   cd table_categorization_agent
   git switch dev
   uv sync --extra dev
   source .venv/bin/activate
   cd ../
   ```

2. **Install blueprint:** 
   ```bash
   git clone https://github.com/stepfnAI/sfn_blueprint.git
   cd sfn_blueprint
   git switch dev
   uv pip install -e .
   cd ../table_categorization_agent
   ```

3. **Configure environment:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## Configuration

You can configure the agent in two ways: using a `.env` file for project-specific settings or by exporting environment variables for more dynamic, shell-level control. Settings loaded via `export` will take precedence over those in a `.env` file.

### Available Settings

The following table details the configuration options available:

| Environment Variable        | Description                                  | Default      |
| --------------------------- | -------------------------------------------- | ------------ |
| `OPENAI_API_KEY or ANTHROPIC_API_KEY`            | **(Required)** Your OpenAI API key.          | *None*       |
| `TABLE_AI_PROVIDER`   | The AI provider to use for table categorization.     | `openai`     |
| `TABLE_MODEL`         | The specific AI model to use.        | `gpt-4o`     |
| `TABLE_TEMPERATURE`               | AI model temperature (e.g., `0.0` to `2.0`). | `0.3`        |
| `TABLE_MAX_TOKENS`                | Maximum tokens for the AI response.          | `4000`       |

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
TABLE_AI_PROVIDER="anthropic"

# Use a different model from the new provider
TABLE_MODEL="claude-3-haiku-20240307"

# Use a higher temperature for potentially more descriptive responses
TABLE_TEMPERATURE=0.7```
```


## Testing

The agent uses `pytest` for testing.

### Running All Tests

```bash
# Run all tests
pytest
```

### Running a Single Test File

To run a specific test file, provide the path to the file:

```bash
# Example: Run the main API test
pytest tests/test_agent_new_api.py
```

```bash
# Example: Run the new feature test
pytest tests/test_agent_new_feature.py
```

The tests are located in the `tests/` directory. The main test files for the agent's API are `tests/test_agent_new_api.py` and `tests/test_agent_new_feature.py`.




## Quick Start

To see a quick demonstration, run the provided example script from the root of the project directory. This will execute the agent with pre-defined metadata and print the result.

```bash
python example/basic_usage.py
```


Here's how to use the agent to categorize tables based on their descriptions:

```python
from table_categorization_agent import TableCategorizationAgent

# 1. Initialize the agent
agent = TableCategorizationAgent()

# 2. Define descriptions for your tables
table_descriptions = {
    "table1": "This table stores borrower profile information, including personal details, contact information, identification numbers, and credit-related attributes. Each row represents a unique borrower record used for managing borrower data.",
    "table2": "This table records loan modification details, including references to borrower and loan IDs, modification attributes, updated terms, and approval information. Each row represents a specific modification event for a loan.",
    "table3": "This table captures loan payment transactions, including breakdowns of principal, interest, insurance, and tax components. Each row represents a transaction with associated loan reference, payment details, and status."
}

# 3. Define your task
# You need a domain schema file 
task_data = {
    "domain_schema": "path/to/your/domain_schema.json",
    "tables_metadata": table_descriptions
}

# 4. Execute the task
# This will make a call to an LLM. Ensure you have the necessary API keys configured.
output = agent.execute_task(task_data)

# 5. Print the result
print(output)
```

## Domain Schema Format

The agent works with domain schemas in JSON format that define entities, attributes, and relationships:

```json
{
  "entities": [
    {
      "iri": ":Borrower_Profile",
      "label": "Borrower Profile",
      "attributes": [
        {
          "iri": ":BorrowerId",
          "label": "BorrowerId",
          "range": [":UUID"]
        }
      ]
    }
  ]
}
```


## Prompt Management

All prompts used by this agent are centralized in `src/table_categorization_agent/constants.py` for easy review and modification.

## Contributing

1.  Fork the repository
2.  Create a feature branch
3.  Make your changes
4.  Add tests
5.  Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For support and questions:
- Email: rajesh@stepfunction.ai
- Issues: https://github.com/stepfnAI/table-categorization-agent/issues