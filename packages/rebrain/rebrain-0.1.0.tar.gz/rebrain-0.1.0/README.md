# 🧠 Rebrain

**Transform chat history into structured, personalized AI memory.**

Rebrain processes your ChatGPT conversations through a 5-step pipeline, extracting observations, synthesizing learnings and cognitions, then building a user persona for hyper-personalized AI interactions.

---

## 🚀 Quick Start (Recommended)

**Using UV - Zero Setup Required**

```bash
# 1. Install UV (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Set your API key
export GEMINI_API_KEY=your_key_here

# 3. Process your conversations
uvx rebrain pipeline run --input conversations.json

# 4. Start MCP server for Claude/Cursor
uvx rebrain mcp
```

**That's it!** No Python installation, no virtual environments, no dependencies to manage.

See [INSTALL.md](INSTALL.md) for detailed installation options.

---

## 🎯 For Developers

```bash
# Clone and setup
git clone https://github.com/genovoai/rebrain.git
cd rebrain
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env.template .env  # Add your GEMINI_API_KEY

# Run pipeline (bash CLI)
scripts/pipeline/cli.sh all

# Or step by step
scripts/pipeline/cli.sh step1  # Transform & filter
scripts/pipeline/cli.sh step2  # Extract & cluster observations
scripts/pipeline/cli.sh step3  # Synthesize learnings
scripts/pipeline/cli.sh step4  # Synthesize cognitions
scripts/pipeline/cli.sh step5  # Build persona

# Load into memg-core
python scripts/load_memg.py
```

**Output:** `data/persona/persona.md` - ready for system prompts!

---

## 🤖 MCP Integration (Claude Desktop / Cursor)

### Direct Mode (Recommended)

Add to `~/.cursor/mcp.json` or Claude Desktop config:

```json
{
  "mcpServers": {
    "rebrain": {
      "command": "uvx",
      "args": ["--from", "rebrain", "rebrain-mcp"],
      "cwd": "/path/to/your/rebrain/project"
    }
  }
}
```

### HTTP Mode (Shared Server)

```bash
# Start persistent server
uvx rebrain mcp --port 9999
```

```json
{
  "mcpServers": {
    "rebrain": {
      "url": "http://localhost:9999/mcp"
    }
  }
}
```

**Benefits:**
- 💰 **Process once (~$0.10-0.20), query forever for free** (local memg-core)
- ⚡ **Instant restarts** - database persists, no reprocessing
- 🔒 **100% local** - no ongoing API costs, no cloud lock-in

---

## Quick Start (Legacy)

### 1. Setup

```bash
git clone <repo-url>
cd rebrain

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp env.template .env
# Edit .env: add GEMINI_API_KEY
```

### 2. Prepare Data

Export your ChatGPT conversations and place the JSON file at:
```
data/raw/conversations.json
```

### 3. Run Pipeline

```bash
# Full pipeline (5 steps)
scripts/pipeline/cli.sh all

# Or run individual steps
scripts/pipeline/cli.sh step1
scripts/pipeline/cli.sh step2
# ... etc
```

### 4. Check Results

```bash
# View pipeline status
scripts/pipeline/cli.sh status

# Read your persona
cat data/persona/persona.md
```

---

## Pipeline Overview

Rebrain uses a 5-stage synthesis pipeline:

```
Raw Conversations (JSON export)
    ↓ Step 1: Transform & Filter
Clean Conversations (date filtered, code removed)
    ↓ Step 2: Extract & Cluster Observations (AI + K-Means)
Clustered Observations (~100 clusters)
    ↓ Step 3: Synthesize Learnings (AI + K-Means)
Clustered Learnings (~20 clusters)
    ↓ Step 4: Synthesize Cognitions (AI)
High-Level Cognitions (~20 patterns)
    ↓ Step 5: Build Persona (AI)
User Persona (3 plain text sections)
```

**Key Features:**
- **Privacy-First:** Category-specific filtering at observation extraction
- **Adaptive Clustering:** Finds local optima with tolerance-based K-Means
- **Flexible Models:** Override per-task via prompt template metadata
- **Provenance Tracking:** Full lineage from conversation → observation → learning → cognition
- **Dual Output:** JSON (structured) + Markdown (human-readable)

---

## Configuration

All pipeline parameters live in `config/pipeline.yaml`:

```yaml
ingestion:
  date_cutoff_days: 180
  remove_code_blocks: true

insight_extraction:
  max_concurrent: 20
  batch_size: 40

learning_clustering:
  target_clusters: 20
  tolerance: 0.2
```

Model selection via prompt templates:
```yaml
# rebrain/prompts/templates/persona_synthesis.yaml
metadata:
  model_recommendation: "gemini-2.5-flash"
```

See `config/README.md` for details.

---

## CLI Usage

```bash
# Check what's been generated
./cli.sh status

# Run individual steps
./cli.sh step1 -i data/raw/my_convos.json
./cli.sh step2 --cluster-only  # Re-cluster existing insights
./cli.sh step3

# Clean outputs
./cli.sh clean --all

# Full help
./cli.sh help
```

See `scripts/pipeline/README.md` for details.

---

## Project Structure

```
rebrain/
├── rebrain/              # Core library
│   ├── core/            # GenAI client
│   ├── ingestion/       # Data loading & chunking
│   ├── operations/      # Embedder, clusterer, synthesizer
│   ├── prompts/         # Prompt templates (YAML)
│   ├── retrieval/       # Query interface (future)
│   └── schemas/         # Pydantic models
├── config/              # Pipeline configuration
├── scripts/pipeline/    # 5-step pipeline + CLI
├── data/               # Raw → processed → persona
└── notebooks/          # Exploration & testing
```

---

## Output

### Persona (Step 5)

**JSON** (`data/persona/persona.json`):
```json
{
  "model": "gemini-2.5-flash",
  "persona": {
    "personal_profile": "...",
    "communication_preferences": "...",
    "professional_profile": "..."
  }
}
```

**Markdown** (`data/persona/persona.md`):
```markdown
# User Persona Information for AI

## Personal Profile
...

## Communication Preferences
...

## Professional Profile
...
```

Copy-paste ready for system prompts!

---

## Development

```bash
# Install dev dependencies
pip install -r requirements_dev.txt

# Run with custom config
python scripts/pipeline/01_transform_filter.py --input data/raw/test.json

# Check specific step
python scripts/pipeline/02_extract_cluster_insights.py --skip-cluster
```

---

## Documentation

- **Pipeline Details:** `scripts/pipeline/README.md`
- **Configuration:** `config/README.md`
- **Data Structure:** `data/README.md`
- **Model Override Pattern:** `MODEL_OVERRIDE_PATTERN.md`
- **Persona Builder:** `PERSONA_BUILDER_REFACTOR.md`

---

## License

MIT License - see LICENSE file

---

**Built by GenovoAI** - AI-enhanced memory systems
