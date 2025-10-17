# Rebrain Setup Guide

Quick setup instructions for the rebrain project.

## Prerequisites

- Python 3.10 or higher
- Gemini API key from Google AI Studio

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone git@github.com:yasinsb/rebrain.git
   cd rebrain
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   # Core dependencies
   pip install -r requirements.txt
   
   # Development dependencies (includes Jupyter)
   pip install -r requirements_dev.txt
   ```

4. **Configure environment**:
   ```bash
   # Create .env file from template
   cp env.template .env
   
   # Edit .env and add your API key:
   # GEMINI_API_KEY=your_actual_api_key_here
   ```

## Project Structure

```
rebrain/
├── config/              # Configuration and schema
│   ├── schema.yaml     # memg-core memory types definition
│   └── settings.py     # Application settings
│
├── rebrain/            # Main package
│   ├── ingestion/      # Stage 1: Load & chunk
│   ├── synthesis/      # Stage 2: Embed & cluster
│   ├── persona/        # Stage 3: Build self-model
│   ├── retrieval/      # Stage 4: Query interface
│   └── utils/          # Common utilities
│
├── agents/             # Google ADK agents
├── data/              # Data storage (raw/processed/exports)
├── notebooks/         # Jupyter notebooks for exploration
├── scripts/           # Pipeline scripts
└── tests/             # Test suite
```

## Running the Pipeline

### Option 1: Script (when ready)
```bash
python scripts/run_pipeline.py --input data/raw/chat_export.jsonl
```

### Option 2: Python REPL
```python
from rebrain.ingestion import parse_chatgpt_conversation, Conversation
from rebrain.schemas import Observation, Learning, Cognition

# Your code here...
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rebrain
```

## Code Quality

```bash
# Format code
black rebrain/ tests/

# Lint code
ruff rebrain/ tests/

# Type check
mypy rebrain/
```

## Next Steps

1. **Configure API keys** in `.env`
2. **Prepare data**: Place chat exports in `data/raw/`
3. **Run ingestion**: Start with Stage 1 (chunking and annotation)
4. **Iterate**: Build and test incrementally

## Development Notes

- The project uses memg-core for dual storage (Qdrant + Kuzu)
- Schema is defined in `config/schema.yaml` with custom memory types
- Each stage has TODOs for full implementation
- Agent integration via Google ADK is pending

## Troubleshooting

### Import Errors
- Make sure virtual environment is activated: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Run validation: `python scripts/validate_setup.py`

### API Errors
- Verify `GEMINI_API_KEY` in `.env`
- Check API quota and limits
- Ensure you're using the new `google-genai` (v1.42.0) package

### Dependency Conflicts
- Use the provided `.venv` or create a fresh virtual environment
- All dependencies are pinned to tested versions
- If issues persist, delete `.venv` and reinstall

## Resources

- **Technical Guide**: See `TECHNICAL_GUIDE_V0.md`
- **Project Overview**: See `.cursor/rules/rebrain-project-overview.mdc`
- **Memory Relations**: See `.cursor/rules/memory-relations.mdc`

