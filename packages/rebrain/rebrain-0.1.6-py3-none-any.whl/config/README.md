# Configuration System

Rebrain uses a clean separation between **secrets** (`.env`) and **pipeline parameters** (`pipeline.yaml`).

---

## Quick Reference

### `.env` - Secrets Only
```bash
GEMINI_API_KEY=your_key_here

# Model defaults (optional - can be overridden by prompts)
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_DIMENSION=768

# Paths
DATA_PATH=./data
STORAGE_PATH=./storage
```

### `pipeline.yaml` - All Pipeline Parameters
```yaml
ingestion:
  date_cutoff_days: 180
  remove_code_blocks: true

observation_extraction:
  max_concurrent: 20
  batch_size: 40

learning_clustering:
  target_clusters: 20
  tolerance: 0.2
```

---

## Configuration Files

### `loader.py`

Central configuration loader that combines secrets from `.env` and parameters from `pipeline.yaml`.

**Usage:**
```python
from config.loader import get_config

secrets, config = get_config()

# Access secrets
api_key = secrets.gemini_api_key
model = secrets.gemini_model  # Optional, defaults to gemini-2.5-flash-lite

# Access pipeline config
cutoff_days = config.ingestion.date_cutoff_days
max_concurrent = config.observation_extraction.max_concurrent
```

### `settings.py`

Legacy settings file, now minimal. Only loads secrets from `.env`.

**Deprecated Usage:**
```python
from config.settings import settings

api_key = settings.gemini_api_key
```

**Prefer:** Use `get_config()` from `loader.py` instead.

### `pipeline.yaml`

Main pipeline configuration. Organized by stage.

**Structure:**
```yaml
# Stage 1: Ingestion & Preprocessing
ingestion:
  date_cutoff_days: 180
  remove_code_blocks: true
  chunk_size_tokens: 2000
  chunk_overlap_percent: 0.125

# Stage 2: Observation Extraction
observation_extraction:
  prompt_template: "observation_extraction"
  max_concurrent: 20
  batch_size: 40
  request_delay: 0.2
  max_retries: 3

# Stage 2b: Observation Embedding
observation_embedding:
  batch_size: 100
  rate_delay: 1.0

# Stage 2c: Observation Clustering
observation_clustering:
  target_clusters: 100
  tolerance: 0.15
  optimize: true

# Stage 3: Learning Synthesis
learning_synthesis:
  prompt_template: "learning_synthesis"
  max_concurrent: 10
  batch_size: 20

# Stage 3b: Learning Embedding
learning_embedding:
  batch_size: 100
  rate_delay: 1.0

# Stage 3c: Learning Clustering
learning_clustering:
  target_clusters: 20
  tolerance: 0.2
  optimize: true

# Stage 4: Cognition Synthesis
cognition_synthesis:
  prompt_template: "cognition_synthesis"
  max_concurrent: 5
  batch_size: 10
```

---

## Model Selection

Models are selected via a 3-tier system:

```
1. Prompt Template metadata (highest priority)
   ↓ if not specified
2. .env GEMINI_MODEL
   ↓ if not specified
3. Hardcoded default: "gemini-2.5-flash-lite"
```

### Example: Per-Task Override

**Prompt Template** (`rebrain/prompts/templates/persona_synthesis.yaml`):
```yaml
metadata:
  model_recommendation: "gemini-2.5-flash"
```

This overrides the `.env` default for persona synthesis only.

See `MODEL_OVERRIDE_PATTERN.md` for details.

---

## Configuration Parameters

### Ingestion (`config.ingestion`)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date_cutoff_days` | int | 180 | Only process conversations from last N days |
| `remove_code_blocks` | bool | true | Strip code blocks to reduce tokens |
| `chunk_size_tokens` | int | 2000 | Max tokens per chunk |
| `chunk_overlap_percent` | float | 0.125 | Overlap between chunks (12.5%) |

### Observation Extraction (`config.observation_extraction`)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt_template` | str | "observation_extraction" | Prompt template name |
| `max_concurrent` | int | 20 | Parallel API requests |
| `batch_size` | int | 40 | Items per batch |
| `request_delay` | float | 0.2 | Seconds between request starts |
| `max_retries` | int | 3 | Retry attempts on failure |
| `retry_delays` | list | [20, 40, 60] | Exponential backoff delays (seconds) |

### Clustering (`config.observation_clustering`, `config.learning_clustering`)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target_clusters` | int | varies | Desired number of clusters |
| `tolerance` | float | 0.15-0.2 | Search range (±tolerance * target) |
| `optimize` | bool | true | Find local optima within tolerance |
| `max_samples` | int | 5 | Test points within tolerance range |
| `metric` | str | "silhouette" | Clustering quality metric |

**Example:**
```yaml
learning_clustering:
  target_clusters: 20
  tolerance: 0.2
  optimize: true
```
Searches: 16, 18, 20, 22, 24 clusters → picks best silhouette score.

---

## Validation

The loader validates configuration at startup:

```python
# config/loader.py
class PipelineConfig(BaseModel):
    ingestion: IngestionConfig
    observation_extraction: ObservationExtractionConfig
    # ... etc
```

**If validation fails:**
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for ObservationExtractionConfig
max_concurrent
  Input should be a valid integer [type=int_type]
```

Fix: Check `pipeline.yaml` for typos or invalid values.

---

## Environment Overrides

You can override specific parameters via environment variables:

```bash
# Override cluster count temporarily
INSIGHT_CLUSTERING_TARGET_CLUSTERS=150 python scripts/pipeline/02_extract_cluster_insights.py
```

(Not currently implemented, but can be added via Pydantic's `env_nested_delimiter`.)

---

## Adding New Parameters

### 1. Update `pipeline.yaml`

```yaml
observation_extraction:
  new_parameter: 42
```

### 2. Update Config Model

```python
# config/loader.py
class ObservationExtractionConfig(BaseModel):
    # ... existing fields ...
    new_parameter: int
```

### 3. Use in Code

```python
from config.loader import get_config

secrets, config = get_config()
value = config.observation_extraction.new_parameter
```

---

## Best Practices

### ✅ DO

- Put API keys in `.env`
- Put all tunable parameters in `pipeline.yaml`
- Use `get_config()` for accessing configuration
- Document new parameters in this README
- Use type hints in config models

### ❌ DON'T

- Hardcode cluster counts in scripts
- Put API keys in YAML files
- Commit `.env` to git
- Mix secrets and parameters
- Use `settings.py` for new code (use `loader.py`)

---

## Migration Notes

**Old Code:**
```python
from config.settings import settings

batch_size = settings.embedding_batch_size  # Which embedding?
```

**New Code:**
```python
from config.loader import get_config

secrets, config = get_config()
batch_size = config.observation_embedding.batch_size  # Clear!
```

---

## File Organization

```
config/
├── README.md           # This file
├── settings.py         # Legacy secrets loader (minimal)
├── loader.py           # New: unified config loader
├── pipeline.yaml       # Main pipeline configuration
└── schema.yaml         # memg-core schema (separate)
```

---

**See Also:**
- `MODEL_OVERRIDE_PATTERN.md` - Model selection strategy
- `scripts/pipeline/README.md` - Parameter usage in pipeline
- `env.template` - Example environment file
