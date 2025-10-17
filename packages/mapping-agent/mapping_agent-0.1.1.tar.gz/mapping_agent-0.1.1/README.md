# Mapping Agent

LLM-driven intelligent attribute-to-column mapping agent for domain schema validation and refinement.

---

## 🌟 Features

- **Intelligent Entity Mapping** – Uses LLM reasoning to map entities from a domain schema to columns across multiple tables.  
- **Confidence Scoring** – Provides confidence scores for each mapping.  
- **Transformation Suggestions** – Suggests data transformations for better alignment.  
- **Context-Aware Analysis** – Generates column profiles (types, nulls, uniqueness, distributions) to improve mapping accuracy.  

---

## 🚀 Quick Start

### Installation

**Prerequisites**

- [uv](https://docs.astral.sh/uv/getting-started/installation/) – package & environment manager  
  Please refer to the official installation guide for the most up-to-date instructions.  
  For quick setup on macOS/Linux, you can currently use:  
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- [Git](https://git-scm.com/)  

**Steps**

1. **Clone the repository**  
   ```bash
   git clone https://github.com/stepfnAI/mapping_agent.git
   cd mapping_agent
   git switch dev
   ```

2. **Install dependencies**  
   ```bash
   uv sync --extra dev
   ```

3. **Activate the virtual environment**  
   ```bash
   source .venv/bin/activate
   ```

4. **Clone and install the blueprint dependency**  
   ```bash
   cd ../
   git clone https://github.com/stepfnAI/sfn_blueprint.git
   cd sfn_blueprint
   git switch dev
   uv pip install -e .
   ```

5. **Return to Mapping Agent**  
   ```bash
   cd ../mapping_agent/
   ```

6. **Set environment variables**  
   The agent requires an API key (e.g., OpenAI).  
   ```bash
   export LLM_PROVIDER="your-llm-provider"   #"openai/anthropic"
   export LLM_MODEL="your-llm-model"         #"gpt-4.1-mini"
   export LLM_API_KEY="your-api-key-here"    
   ```

---

### Basic Usage

Example: Mapping the **Borrower Profile** entity to columns across two CSV files.

```
python examples/basic_usage.py
```

---

## 🧪 Testing

Run the test suite with [pytest](https://docs.pytest.org/):

```bash
# Run all tests
pytest tests/ -s

# Run with coverage
pytest tests/test_models.py
pytest tests/test_utils.py
pytest tests/test_agent_integration.py
```

---

## 📝 Prompt Management

Prompts are centralized in  
`src/mapping_agent/constants.py`.

- **`format_mapping_prompt_with_system_prompt`** constructs structured prompts with a system message.  
- Ensures the LLM consistently acts as a *data mapping expert*.  
- Easy to extend or fine-tune reasoning strategies in one place.  

---

## 🤝 Contributing

Contributions are welcome!  
Please see the **Contributing Guide** before submitting a PR.

---

## 📄 License

Licensed under the **MIT License**. See [LICENSE](./LICENSE) for details.