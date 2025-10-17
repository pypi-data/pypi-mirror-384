# Memory Graph Data Schema

AI-ready reference for Rebrain memory hierarchy and data structures.

---

## Hierarchy

```
Conversations (raw chat exports)
    ↓ extract
Insights (one per conversation)
    ↓ cluster + synthesize
Learnings (patterns from insight clusters)
    ↓ cluster + synthesize
Cognitions (high-level principles from learning clusters)
    ↓ synthesize
Persona (3 text sections for system prompts)
```

---

## Schema: Cognitions

**File:** `data/cognitions/cognitions.json`

**Structure:**
```json
{
  "cognitions": [
    {
      "id": "cognition_001",
      "content": "2-3 paragraphs explaining a fundamental principle",
      "domains": ["technical", "professional"],
      "stability": "stable",
      "priority": "core",
      "keywords": ["efficiency", "pragmatism", "control"],
      "source_learning_ids": ["learning_001", "learning_002"],
      "cluster_id": "0",
      "first_observed": "2024-04-01T...",
      "last_observed": "2025-10-12T...",
      "source_learning_count": 3
    }
  ],
  "synthesis": {
    "model": "gemini-2.5-flash-lite",
    "prompt_template": "cognition_synthesis",
    "total_learnings": 22,
    "total_cognitions": 22
  }
}
```

**Fields:**
- `content`: Main cognition text (150-250 tokens)
- `domains`: `["technical" | "professional" | "personal" | "cross-domain"]`
- `stability`: `"stable" | "evolving" | "emerging"`
- `priority`: `"core" | "important" | "peripheral"`
- `keywords`: 5-10 abstract conceptual terms
- `source_learning_ids`: Provenance tracking
- `cluster_id`: K-Means cluster assignment
- `first_observed`/`last_observed`: Temporal span
- `source_learning_count`: How many learnings synthesized

---

## Schema: Learnings

**File:** `data/learnings/learnings.json`

**Structure:**
```json
{
  "learnings": [
    {
      "id": "learning_001",
      "content": "2-3 paragraphs explaining a pattern",
      "entities": ["Docker", "CI/CD", "AWS"],
      "category": "technical",
      "confidence": "high",
      "tags": ["workflow-optimization", "automation"],
      "source_insight_ids": ["insight_001", "insight_002"],
      "cluster_id": "0",
      "embedding": [0.123, -0.456, ...],
      "first_observed": "2024-04-01T...",
      "last_observed": "2025-10-12T...",
      "source_insight_count": 12
    }
  ],
  "clusters": [
    {
      "id": "0",
      "size": 3,
      "silhouette_score": 0.45,
      "member_ids": ["learning_001", "learning_002", "learning_003"]
    }
  ],
  "synthesis": {...},
  "embedding": {...},
  "clustering": {...}
}
```

**Fields:**
- `content`: Synthesized learning pattern (150-250 tokens)
- `entities`: Relevant concepts, projects, frameworks
- `category`: `"technical" | "professional" | "personal" | "cross-domain"`
- `confidence`: `"high"` (9+ insights) | `"medium"` (4-8) | `"low"` (1-3)
- `tags`: 3-8 abstract tags (lowercase-kebab-case)
- `source_insight_ids`: Which insights were synthesized
- `cluster_id`: K-Means cluster assignment
- `embedding`: 768-dim vector from gemini-embedding-001
- `source_insight_count`: Number of insights in cluster

---

## Schema: Persona

**File:** `data/persona/persona.json`

**Structure:**
```json
{
  "generated_at": "2025-10-12T18:17:12.227268",
  "source_cognitions": 22,
  "model": "gemini-2.5-flash",
  "persona": {
    "personal_profile": "Who the user is: worldview, values, interests, reasoning style, core traits. 1-2 paragraphs.",
    "communication_preferences": "How AI should communicate: tone, depth, what to emphasize/avoid. 1 paragraph.",
    "professional_profile": "Professional orientation, expertise, working philosophy, objectives, projects. 1-2 paragraphs."
  }
}
```

**Fields:**
- `generated_at`: ISO timestamp
- `source_cognitions`: How many cognitions were synthesized
- `model`: Which Gemini model was used
- `persona`: Three plain text sections
  - `personal_profile`: ~130-160 tokens
  - `communication_preferences`: ~130-160 tokens
  - `professional_profile`: ~130-160 tokens

**Total:** ~400-500 tokens, ready for direct injection into system prompts.

---

## Usage for AI Systems

### Loading Persona
```python
import json

with open('data/persona/persona.json') as f:
    data = json.load(f)
    persona = data['persona']

# Inject into system prompt
system_prompt = f"""
You are an AI assistant. Here is information about the user:

{persona['personal_profile']}

{persona['communication_preferences']}

{persona['professional_profile']}
"""
```

### Querying Cognitions
```python
with open('data/cognitions/cognitions.json') as f:
    cognitions = json.load(f)['cognitions']

# Filter by domain
technical = [c for c in cognitions if 'technical' in c['domains']]

# Filter by priority
core_cognitions = [c for c in cognitions if c['priority'] == 'core']

# Search keywords
efficiency_focused = [c for c in cognitions if 'efficiency' in c['keywords']]
```

### Traversing Hierarchy
```python
# Cognition → Learnings → Insights
cognition = cognitions[0]
learning_ids = cognition['source_learning_ids']

with open('data/learnings/learnings.json') as f:
    learnings = json.load(f)['learnings']
    
source_learnings = [l for l in learnings if l['id'] in learning_ids]

# Continue to insights if needed
insight_ids = [i for l in source_learnings for i in l['source_insight_ids']]
```

---

## Notes

- All timestamps are ISO 8601 format
- All IDs follow pattern: `{type}_{number}` (e.g., `learning_042`)
- Embeddings are 768-dimensional float arrays
- Clusters use 0-indexed integer IDs
- Privacy filtering happens at insight level (only low/medium processed)
- Provenance is tracked at every level for full lineage

