# ReBrain Workflows

Complete workflow examples for different user types.

---

## Workflow 1: Simple User (UV Only)

**Goal:** Process conversations and use with Claude Desktop

### One-Time Setup

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Get API key from: https://aistudio.google.com/app/apikey
export GEMINI_API_KEY=your_key_here
```

### Process Conversations

```bash
# Create project
mkdir my-rebrain
cd my-rebrain

# Copy your ChatGPT export
cp ~/Downloads/conversations.json .

# Process (takes ~2-3 minutes)
uvx rebrain pipeline run --input conversations.json

# Results at:
# - data/persona/persona.md         (human-readable)
# - data/cognitions/cognitions.json (structured)
# - data/learnings/learnings.json   (detailed patterns)
```

### Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rebrain": {
      "command": "uvx",
      "args": ["--from", "rebrain", "rebrain-mcp"],
      "cwd": "/Users/you/my-rebrain"
    }
  }
}
```

Restart Claude Desktop. Done!

### Update After New Conversations

```bash
# Export new conversations.json from ChatGPT
# Replace old file

# Reprocess
export GEMINI_API_KEY=your_key_here
uvx rebrain pipeline run --input conversations.json

# Reload database
uvx rebrain load --force

# Restart Claude Desktop (or Cursor reloads automatically)
```

**Cost:** ~$0.10-0.20 per run, then free forever.

---

## Workflow 2: Developer (Git + Virtual Environment)

**Goal:** Contribute to project, iterate on pipeline

### Initial Setup

```bash
# Clone
git clone https://github.com/yasinsb/rebrain.git
cd rebrain

# Setup environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements_dev.txt

# Configure
cp env.template .env
# Edit .env: GEMINI_API_KEY=your_key_here

# Add test data
cp ~/path/to/conversations.json data/raw/
```

### Development Workflow

```bash
# Run individual steps
cd scripts/pipeline

# Step 1: Transform
./cli.sh step1 -i ../../data/raw/conversations.json

# Step 2: Extract observations
./cli.sh step2

# Review observations
cat ../../data/observations/observations.json | jq '.observations[0]'

# Step 3: Synthesize learnings
./cli.sh step3

# Step 4: Synthesize cognitions
./cli.sh step4

# Step 5: Build persona
./cli.sh step5

# Load into memg-core
cd ../..
python scripts/load_memg.py

# Test MCP server locally
python -m integrations.mcp.server --port 9999
# Or
uvx rebrain mcp --port 9999
```

### Testing Changes

```bash
# Run tests
pytest

# Test with small dataset
./cli.sh step1 -i test_data.json -o test_output.json

# Check status
uvx rebrain status
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/improve-clustering

# Make changes
# ...

# Test
./cli.sh all
pytest

# Commit
git add .
git commit -m "Improve clustering algorithm"
git push origin feature/improve-clustering
```

---

## Workflow 3: Expert (Docker Production)

**Goal:** Deploy multi-user MCP server

### Setup

```bash
cd integrations/mcp

# Create custom schema
cp rebrain/rebrain.yaml production_schema.yaml
# Edit as needed

# Start server
./cli.sh production_schema.yaml --port 8228

# Verify
curl http://localhost:8228/health
```

### Load Data for Multiple Users

```bash
# User 1
python ../../scripts/load_memg.py \
  --cognitions /path/to/user1/cognitions.json \
  --learnings /path/to/user1/learnings.json \
  --user-id user1 \
  --copy-to .

# User 2
python ../../scripts/load_memg.py \
  --cognitions /path/to/user2/cognitions.json \
  --learnings /path/to/user2/learnings.json \
  --user-id user2 \
  --copy-to .

# Restart server to pick up changes
./cli.sh production_schema.yaml --stop
./cli.sh production_schema.yaml --port 8228
```

### Backup & Restore

```bash
# Backup
./cli.sh production_schema.yaml --backup

# Restore (if needed)
./cli.sh production_schema.yaml --stop
cd production_schema_8228/
tar -xzf ../backups/backup_2024-01-15.tar.gz
cd ..
./cli.sh production_schema.yaml --port 8228
```

### Monitoring

```bash
# Check logs
docker-compose --project-name memg-mcp-8228 logs -f

# Check database size
du -sh production_schema_8228/db/

# Test query
curl -X POST http://localhost:8228/mcp/search \
  -H "Content-Type: application/json" \
  -d '{"query": "python best practices", "user_id": "user1"}'
```

---

## Workflow 4: Power User (Multiple Projects)

**Goal:** Manage memories for different contexts

### Project Structure

```
~/rebrain-work/
  ├── data/
  └── conversations_work.json

~/rebrain-personal/
  ├── data/
  └── conversations_personal.json

~/rebrain-research/
  ├── data/
  └── conversations_research.json
```

### Process Each Project

```bash
# Work project
cd ~/rebrain-work
export GEMINI_API_KEY=your_key_here
uvx rebrain pipeline run --input conversations_work.json

# Personal project
cd ~/rebrain-personal
uvx rebrain pipeline run --input conversations_personal.json

# Research project
cd ~/rebrain-research
uvx rebrain pipeline run --input conversations_research.json
```

### Configure Multiple MCP Servers

```json
{
  "mcpServers": {
    "rebrain-work": {
      "command": "uvx",
      "args": ["--from", "rebrain", "rebrain-mcp"],
      "cwd": "/Users/you/rebrain-work"
    },
    "rebrain-personal": {
      "command": "uvx",
      "args": ["--from", "rebrain", "rebrain-mcp"],
      "cwd": "/Users/you/rebrain-personal"
    }
  }
}
```

Or use HTTP mode with different ports:

```bash
# Terminal 1
cd ~/rebrain-work
uvx rebrain mcp --port 9001

# Terminal 2
cd ~/rebrain-personal
uvx rebrain mcp --port 9002
```

```json
{
  "mcpServers": {
    "rebrain-work": {
      "url": "http://localhost:9001/mcp"
    },
    "rebrain-personal": {
      "url": "http://localhost:9002/mcp"
    }
  }
}
```

### Merge Projects (Optional)

```bash
# Create merged project
mkdir ~/rebrain-merged
cd ~/rebrain-merged

# Combine JSONs
jq -s '{"conversations": [.[].conversations[]] | unique_by(.id)}' \
  ~/rebrain-work/data/raw/conversations.json \
  ~/rebrain-personal/data/raw/conversations.json \
  > conversations_merged.json

# Process merged
export GEMINI_API_KEY=your_key_here
uvx rebrain pipeline run --input conversations_merged.json --max-conversations 2000
```

---

## Workflow 5: Continuous Updates

**Goal:** Keep memories fresh with regular updates

### Automation Script

```bash
#!/bin/bash
# update_rebrain.sh

set -e

REBRAIN_DIR="$HOME/rebrain"
CONV_FILE="conversations.json"

echo "🔄 Updating ReBrain memories..."

# Download latest conversations
# (use your ChatGPT export automation here)
cp ~/Downloads/conversations.json "$REBRAIN_DIR/$CONV_FILE"

# Process
cd "$REBRAIN_DIR"
export GEMINI_API_KEY=$(cat ~/.rebrain_api_key)
uvx rebrain pipeline run --input "$CONV_FILE"

# Reload database
uvx rebrain load --force

echo "✅ Update complete!"
echo "💡 Restart Claude Desktop to use fresh memories"
```

### Schedule Weekly Updates

```bash
# Add to crontab
crontab -e

# Run every Sunday at 2 AM
0 2 * * 0 /path/to/update_rebrain.sh >> ~/rebrain/update.log 2>&1
```

---

## Workflow 6: Testing & Development

**Goal:** Test pipeline changes without affecting production

### Test Environment

```bash
# Create test directory
mkdir rebrain-test
cd rebrain-test

# Use small sample
jq '.conversations[0:10]' ~/rebrain/data/raw/conversations.json > test_convos.json

# Test pipeline
export GEMINI_API_KEY=your_key_here
uvx rebrain pipeline run --input test_convos.json --max-conversations 10

# Check results
uvx rebrain status
cat data/persona/persona.md
```

### A/B Testing

```bash
# Version A: Current settings
cd rebrain-v1
uvx rebrain pipeline run --input conversations.json
mv data data-v1

# Version B: Different settings
# (edit config/pipeline.yaml)
uvx rebrain pipeline run --input conversations.json
mv data data-v2

# Compare
diff -u data-v1/persona/persona.md data-v2/persona/persona.md
```

---

## Tips & Best Practices

### Cost Optimization

- Use `--max-conversations 1000` to limit processing
- Start with small samples: `--max-conversations 10`
- Reprocess only when you have significant new data (100+ conversations)

### Data Management

- Keep original `conversations.json` backed up
- Version your persona: `cp data/persona/persona.md persona_v1.md`
- Use `.gitignore` to prevent committing personal data

### Performance

- First run: ~2-3 minutes for 1000 conversations
- MCP startup: <1 second (uses existing database)
- Updates: Only reprocess when needed

### Troubleshooting

```bash
# Check status
uvx rebrain status

# View logs
tail -f ~/.rebrain/logs/pipeline.log

# Test API key
python -c "import os; print(os.getenv('GEMINI_API_KEY'))"

# Force fresh start
rm -rf data/memory_db
uvx rebrain pipeline run --input conversations.json
```

---

## Next Steps

- Read [INSTALL.md](../INSTALL.md) for installation details
- See [scripts/pipeline/README.md](../scripts/pipeline/README.md) for pipeline configuration
- Check [integrations/mcp/README.md](../integrations/mcp/README.md) for MCP server options

