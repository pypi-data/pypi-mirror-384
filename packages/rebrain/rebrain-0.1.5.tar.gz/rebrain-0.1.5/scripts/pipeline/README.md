# Pipeline Documentation

Rebrain's 5-step synthesis pipeline transforms chat history into a structured persona.

---

## Quick Start

### UV Mode (Recommended)

```bash
# Run full pipeline
export GEMINI_API_KEY=your_key_here
uvx rebrain pipeline run --input conversations.json

# With options
uvx rebrain pipeline run --input conversations.json --max-conversations 1000
```

### Developer Mode (Bash CLI)

```bash
# Run all steps
./cli.sh all

# Or step by step
./cli.sh step1
./cli.sh step2
# ... etc
```

---

## Overview

```
Step 1: Transform & Filter → Clean conversations
Step 2: Extract & Cluster  → Insights (~100 clusters)
Step 3: Synthesize         → Learnings (~20 clusters)
Step 4: Synthesize         → Cognitions (~20 patterns)
Step 5: Build Persona      → User profile (3 sections)
```

---

## Step 1: Transform & Filter

**Script:** `01_transform_filter.py`

**What it does:**
- Loads raw ChatGPT JSON (mapping format)
- Converts to clean message array format
- Filters by date (configurable cutoff)
- Removes code blocks to reduce tokens
- Adds metadata (timestamps, token counts)

**Input:** `data/raw/conversations.json`  
**Output:** `data/preprocessed/conversations_clean.json`

**Configuration:**
```yaml
# config/pipeline.yaml
ingestion:
  date_cutoff_days: 180
  remove_code_blocks: true
  chunk_size_tokens: 2000
  chunk_overlap_percent: 0.125
```

**CLI:**
```bash
./cli.sh step1
./cli.sh step1 -i data/raw/my_convos.json -o data/test/clean.json
```

---

## Step 2: Extract & Cluster Insights

**Script:** `02_extract_cluster_observations.py`

**What it does:**
- **Extraction:** AI extracts ONE key observation per conversation
- **Privacy Filter:** Removes high-privacy content
- **Embedding:** Converts observations to vectors
- **Clustering:** K-Means with tolerance-based optimization

**Input:** `data/preprocessed/conversations_clean.json`  
**Output:** `data/observations/observations.json`

**Configuration:**
```yaml
observation_extraction:
  prompt_template: "observation_extraction"
  max_concurrent: 20
  batch_size: 40
  request_delay: 0.2

observation_embedding:
  batch_size: 100
  rate_delay: 1.0

observation_clustering:
  target_clusters: 100
  tolerance: 0.15
  optimize: true
```

**CLI:**
```bash
./cli.sh step2                    # Full: extract + cluster
./cli.sh step2 --skip-cluster     # Extract only (review before clustering)
./cli.sh step2 --cluster-only     # Re-cluster existing observations
```

**Key Features:**
- Privacy levels: `low`, `medium`, `high`
- Only processes `low` and `medium` privacy observations
- Clustering finds local optima within tolerance range

---

## Step 3: Synthesize & Cluster Learnings

**Script:** `03_synthesize_cluster_learnings.py`

**What it does:**
- Groups observations by cluster
- AI synthesizes each cluster → learning pattern
- Embeds learnings
- Clusters learnings into higher-level groups

**Input:** `data/observations/observations.json`  
**Output:** `data/learnings/learnings.json`

**Configuration:**
```yaml
learning_synthesis:
  prompt_template: "learning_synthesis"
  max_concurrent: 10
  batch_size: 20

learning_clustering:
  target_clusters: 20
  tolerance: 0.2
```

**CLI:**
```bash
./cli.sh step3
./cli.sh step3 --skip-cluster  # Synthesis only
./cli.sh step3 --cluster-only  # Re-cluster only
```

---

## Step 4: Synthesize Cognitions

**Script:** `04_synthesize_cognitions.py`

**What it does:**
- Groups learnings by cluster
- AI synthesizes each cluster → high-level cognition
- Categorizes by domain (technical, personal, professional)
- Assigns priority

**Input:** `data/learnings/learnings.json`  
**Output:** `data/cognitions/cognitions.json`

**Configuration:**
```yaml
cognition_synthesis:
  prompt_template: "cognition_synthesis"
  max_concurrent: 5
  batch_size: 10
```

**CLI:**
```bash
./cli.sh step4
```

**Output Fields:**
- `content`: Main cognition text
- `domains`: Categories (e.g., technical, personal)
- `priority`: high/medium/low
- `source_learning_ids`: Provenance tracking

---

## Step 5: Build Persona

**Script:** `05_build_persona.py`

**What it does:**
- Aggregates all cognitions
- AI synthesizes into 3 plain text sections
- Outputs JSON + Markdown

**Input:** `data/cognitions/cognitions.json`  
**Output:**
- `data/persona/persona.json` (structured)
- `data/persona/persona.md` (human-readable)

**Configuration:**
```yaml
# Model specified in prompt template
# rebrain/prompts/templates/persona_synthesis.yaml
metadata:
  model_recommendation: "gemini-2.5-flash"
```

**CLI:**
```bash
./cli.sh step5
```

**Output Sections:**
1. **Personal Profile:** Who the user is (values, worldview)
2. **Communication Preferences:** How AI should communicate
3. **Professional Profile:** Skills, expertise, projects

---

## CLI Commands

### Full Pipeline
```bash
./cli.sh all  # Runs steps 1-5
```

### Status Check
```bash
./cli.sh status  # Shows what's been generated
```

### Clean Outputs
```bash
./cli.sh clean --all        # Remove all outputs
./cli.sh clean --observations   # Remove observations only
./cli.sh clean --learnings  # Remove learnings only
```

### Help
```bash
./cli.sh help
```

---

## Configuration Tips

### Model Selection

**Default (`.env`):**
```bash
GEMINI_MODEL=gemini-2.5-flash-lite  # Fast & cheap
```

**Per-Task Override (prompt template):**
```yaml
# rebrain/prompts/templates/persona_synthesis.yaml
metadata:
  model_recommendation: "gemini-2.5-flash"  # Higher quality
```

Hierarchy: Prompt Template > .env > Hardcoded Default

### Clustering Optimization

```yaml
learning_clustering:
  target_clusters: 20
  tolerance: 0.2  # Search 16, 18, 20, 22, 24 clusters
  optimize: true
```

Finds the cluster count with best silhouette score within tolerance.

### Rate Limiting

```yaml
insight_extraction:
  max_concurrent: 20      # Parallel requests
  batch_size: 40          # Items per batch
  request_delay: 0.2      # Seconds between request starts
  max_retries: 3
  retry_delays: [20, 40, 60]  # Exponential backoff
```

---

## Troubleshooting

**Rate Limit Errors (429):**
- Reduce `max_concurrent` or increase `request_delay`
- Check your Gemini API quota

**Out of Memory:**
- Reduce `batch_size` in embedding config
- Process fewer conversations (increase `date_cutoff_days`)

**Poor Clustering:**
- Adjust `target_clusters` and `tolerance`
- Try `--cluster-only` to re-cluster without re-extracting

**Personal Data in Output:**
- Check `.gitignore` includes `data/persona/`, `data/observations/`, etc.
- Never commit `data/` folders (except structure)

---

## Advanced Usage

### Custom Input/Output Paths

```bash
./cli.sh step1 -i data/raw/test.json -o data/test/clean.json
./cli.sh step2 -i data/test/clean.json -o data/test/observations.json
```

### Re-run from Specific Step

```bash
# Re-cluster observations without re-extracting
./cli.sh step2 --cluster-only

# Re-synthesize learnings with different prompt
# 1. Edit rebrain/prompts/templates/learning_synthesis.yaml
# 2. Delete data/learnings/learnings.json
# 3. Run:
./cli.sh step3
```

### Test Single Conversation

```python
# Edit 01_transform_filter.py to limit conversations
conversations = conversations[:1]  # Process only first conversation
```

---

## Performance

**Typical Runtime (651 conversations, 10 days cutoff):**
- Step 1: ~5s (no AI)
- Step 2: ~60-90s (AI extraction + clustering)
- Step 3: ~20-30s (AI synthesis + clustering)
- Step 4: ~10-15s (AI synthesis)
- Step 5: ~5-10s (AI synthesis)

**Total:** ~2-3 minutes for full pipeline

**Cost:** ~$0.10-0.20 per full run (Gemini Flash Lite)

---

**See Also:**
- `config/README.md` - Configuration details
- `MODEL_OVERRIDE_PATTERN.md` - Model selection strategy
- `PERSONA_BUILDER_REFACTOR.md` - Persona design

