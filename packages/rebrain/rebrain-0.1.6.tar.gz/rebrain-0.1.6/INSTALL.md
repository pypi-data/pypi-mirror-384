# ReBrain Installation Guide

Complete installation instructions for all user types.

---

## For Non-Technical Users (Recommended)

**Using UV - Zero Setup Required**

### 1. Install UV (One-Time)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv

# Verify installation
uv --version
```

### 2. Get Your API Key

Get a free Google GenAI API key from: https://aistudio.google.com/app/apikey

### 3. Export Your ChatGPT Data

1. Go to ChatGPT Settings → Data Controls → Export Data
2. Wait for email with download link
3. Download and extract `conversations.json`

### 4. Run ReBrain

```bash
# Create project directory
mkdir my-rebrain
cd my-rebrain
mv ~/Downloads/conversations.json .

# Set API key
export GEMINI_API_KEY=your_key_here

# Process conversations (takes ~2-3 minutes)
uvx rebrain pipeline run --input conversations.json

# Start MCP server for Claude/Cursor
uvx rebrain mcp
```

That's it! No Python installation, no virtual environments, no pip dependencies.

---

## For Developers

**Using Python Virtual Environment**

### 1. Prerequisites

- Python 3.10 or higher
- Git

### 2. Clone Repository

```bash
git clone https://github.com/yasinsb/rebrain.git
cd rebrain
```

### 3. Setup Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements_dev.txt
```

### 4. Configure

```bash
# Copy environment template
cp env.template .env

# Edit .env and add your API key
# GEMINI_API_KEY=your_key_here
```

### 5. Run Pipeline

```bash
# Using bash CLI (developer mode)
cd scripts/pipeline
./cli.sh all

# Or using UV (user mode)
uvx rebrain pipeline run --input conversations.json

# Or step by step
./cli.sh step1
./cli.sh step2
./cli.sh step3
./cli.sh step4
./cli.sh step5
```

### 6. Load into MCP Database

```bash
# Load JSONs into memg-core
python scripts/load_memg.py

# Or using UV
uvx rebrain load
```

---

## For Experts

**Using Docker (Production/Multi-User)**

### 1. Prerequisites

- Docker Desktop
- Docker Compose

### 2. Setup MCP Server

```bash
cd integrations/mcp

# Copy your YAML schema
cp rebrain/rebrain.yaml path/to/your/schema.yaml

# Run server
./cli.sh your_schema.yaml --port 8228

# Check health
curl http://localhost:8228/health
```

### 3. Configure for Multiple Users

See `integrations/mcp/README.md` for advanced Docker deployment options.

---

## Verification

### Check Installation

```bash
# UV mode
uvx rebrain status

# Developer mode
python -m rebrain.cli status
```

### Test Pipeline

```bash
# Small test with 10 conversations
uvx rebrain pipeline run --input conversations.json --max-conversations 10
```

### Test MCP Server

```bash
# Start in stdio mode (for testing)
uvx rebrain mcp

# Or HTTP mode
uvx rebrain mcp --port 9999

# Test endpoint
curl http://localhost:9999/health
```

---

## Integration with Claude Desktop / Cursor

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

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

### Cursor

Edit `.cursor/mcp.json` in your project:

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

If running as persistent HTTP server:

```json
{
  "mcpServers": {
    "rebrain": {
      "url": "http://localhost:9999/mcp"
    }
  }
}
```

---

## Troubleshooting

### API Key Not Found

```bash
# Check if set
echo $GEMINI_API_KEY

# Set in current shell
export GEMINI_API_KEY=your_key_here

# Or add to .env file
echo "GEMINI_API_KEY=your_key_here" > .env
```

### UV Command Not Found

```bash
# Reinstall UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload shell
source ~/.bashrc  # or ~/.zshrc
```

### Pipeline Fails

```bash
# Continue from specific step
uvx rebrain pipeline run --continue step3

# Or check status
uvx rebrain status
```

### MCP Server Won't Start

```bash
# Check if data exists
ls -la data/cognitions/cognitions.json
ls -la data/learnings/learnings.json

# Force reload
uvx rebrain mcp --force-reload

# Or specify data path
uvx rebrain mcp --data-path /full/path/to/data
```

### Permission Issues

```bash
# Ensure data directory is writable
chmod -R u+w data/
```

---

## Uninstallation

### UV Installation

```bash
# Remove UV tool installation
uv tool uninstall rebrain

# UV cache (optional)
rm -rf ~/.cache/uv
```

### Developer Installation

```bash
# Just delete the repository
cd ..
rm -rf rebrain/
```

### Docker Installation

```bash
cd integrations/mcp
./cli.sh your_schema.yaml --stop
docker-compose --project-name memg-mcp-8228 down -v
```

---

## Next Steps

- Read `README.md` for feature overview
- See `docs/WORKFLOWS.md` for usage examples
- Check `scripts/pipeline/README.md` for pipeline details
- View `integrations/mcp/README.md` for MCP server options

---

**Need Help?**

- GitHub Issues: https://github.com/yasinsb/rebrain/issues
- Documentation: https://github.com/yasinsb/rebrain

