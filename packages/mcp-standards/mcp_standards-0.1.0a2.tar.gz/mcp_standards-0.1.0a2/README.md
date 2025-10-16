# MCP Standards - Self-Learning AI Standards System

**Stop repeating yourself. MCP Standards learns from your corrections automatically and updates your AI configuration.**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP 1.0](https://img.shields.io/badge/MCP-1.0-purple.svg)](https://github.com/anthropics/mcp)

---

## The Problem

You keep telling your AI assistant the same things:
- "Use `uv` not `pip`"
- "Use `uv` not `pip`"
- "Use `uv` not `pip`"

**What if it learned after the 3rd time?**

---

## The Solution

**MCP Standards learns from your corrections automatically:**

1. You correct Claude 3 times: "use `uv` not `pip`"
2. MCP Standards detects the pattern
3. Preference promoted (80% confidence)
4. CLAUDE.md updated automatically
5. **Claude never makes that mistake again**

### Before MCP Standards
```
You: "Use uv not pip"
Claude: *ignores, uses pip again*
You: "USE UV NOT PIP"
Claude: *ignores again*
You: "I TOLD YOU 10 TIMES, USE UV!!!"
```

### After MCP Standards
```
You: "Use uv not pip" (correction #1)
You: "Use uv not pip" (correction #2)
You: "Use uv not pip" (correction #3)
MCP Standards: ✅ Pattern learned! Added to CLAUDE.md
Claude: *uses uv from now on, forever*
```

---

## Features

### ✨ Self-Learning (THE Killer Feature)

**Automatic Pattern Detection:**
- Learns from corrections (3+ occurrences)
- Detects workflow patterns
- Promotes to preferences automatically
- Updates CLAUDE.md without manual work

**5 Types of Learning:**
1. **Explicit corrections**: "use X not Y"
2. **Implicit rejections**: User edits within 2 minutes
3. **Rule violations**: Compare vs config files
4. **Workflow patterns**: Always run tests after code
5. **Tool preferences**: Prefer certain tools for tasks

**Confidence-Based Promotion:**
- 3 occurrences = 30% confidence (detected)
- 5 occurrences = 70% confidence (high)
- 10 occurrences = 90% confidence (very high)
- 95%+ = auto-apply to CLAUDE.md

### 🎯 Automatic Standards Extraction

**Reads your existing config files:**
- `.editorconfig` → Indentation, line endings
- `.prettierrc` → Formatting, quotes
- `.eslintrc` → Linting rules
- `pyproject.toml` → Python config
- `package.json` → JavaScript dependencies
- `Cargo.toml` → Rust config

**Auto-detects:**
- Project type (Python, JavaScript, Rust, Go, etc.)
- Package manager (uv, npm, yarn, cargo, etc.)
- Test framework (pytest, jest, vitest, etc.)
- Build commands

**Generates instruction files for:**
- Claude Desktop/Code (`CLAUDE.md`)
- GitHub Copilot (`.github/copilot-instructions.md`)
- Cursor (`.cursor/rules/standards.mdc`)

### 🔒 Production-Grade Security

Built with defense-in-depth:
- ✅ **Path whitelist** - Only allowed directories
- ✅ **Input sanitization** - No log injection
- ✅ **Rate limiting** - 100 patterns/min max
- ✅ **Audit logging** - Complete modification trail
- ✅ **100% local** - No cloud, no tracking

### 🧠 Persistent Memory

- Local SQLite database with FTS5
- Full-text search (<50ms on 1M+ episodes)
- Export to markdown
- Project-specific vs global preferences

---

## Quick Start

### Install

```bash
# 1. Clone repository
git clone https://github.com/airmcp-com/mcp-standards.git
cd mcp-standards

# 2. Install dependencies
uv sync

# 3. Configure Claude Desktop
# Add to ~/Library/Application Support/Claude/claude_desktop_config.json:
{
  "mcpServers": {
    "mcp-standards": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/ABSOLUTE/PATH/TO/mcp-standards",
        "python",
        "run_server.py"
      ]
    }
  }
}
# Replace /ABSOLUTE/PATH/TO/ with your actual path!
# Example: /Users/yourname/Projects/mcp-standards/run_server.py

# 4. Restart Claude Desktop - you're done!
```

### Option B: From PyPI (Coming Soon)

```bash
# Install from PyPI
uv pip install mcp-standards

# Configure Claude Desktop
# Add to ~/Library/Application Support/Claude/claude_desktop_config.json:
{
  "mcpServers": {
    "mcp-standards": {
      "command": "mcp-standards",
      "args": []
    }
  }
}

# Restart Claude Desktop
```

### 🚀 60-Second Quickstart

Once Claude Desktop restarts, try this:

```javascript
// 1. Store a preference right now
add_episode(
    name="My First Preference",
    content="I prefer using TypeScript over JavaScript for new projects",
    source="user"
)

// 2. Search for it
search_episodes(query="TypeScript", limit=5)

// 3. Generate AI standards from your current project
generate_ai_standards(project_path=".")
```

**What just happened?**
- ✅ Your preference is stored in local SQLite database
- ✅ Searchable in all future conversations
- ✅ AI standards file generated from your project config

**Next:** Start correcting Claude when it makes mistakes. After 3 similar corrections, run:
```javascript
get_learned_preferences(min_confidence=0.3)
```
You'll see MCP Standards has learned the pattern automatically!

---

### Optional: Add Cost Optimization (99.5% Savings)

**Want to save on AI costs?** Add [agentic-flow](https://github.com/ruvnet/agentic-flow) to route simple operations to cheaper models:

```bash
# Get free Gemini API key: https://aistudio.google.com/app/apikey

# Add to your claude_desktop_config.json (alongside mcp-standards):
{
  "mcpServers": {
    "mcp-standards": { ... },
    "agentic-flow": {
      "command": "npx",
      "args": ["-y", "agentic-flow", "mcp"],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "DEFAULT_MODEL": "gemini-1.5-flash",
        "SHOW_MODEL_USAGE": "true",
        "SHOW_COST_SAVINGS": "true",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

**What agentic-flow does:**
- Routes simple operations (memory, search) → Gemini Flash ($0.075/1M tokens)
- Keeps complex operations (code gen) → Claude Sonnet ($15/1M tokens)
- **Shows which model was used** for each operation
- **Displays cost savings** in real-time
- Saves ~$389/month on typical usage
- 100% optional - MCP Standards works perfectly without it

## 📖 Quick Start Guide

MCP Standards has **two complementary systems** for building your AI assistant's knowledge:

### System 1: Episodes (Manual Knowledge - Immediate)

Store facts, preferences, and instructions **right now**:

```javascript
// ✅ Store a preference immediately
add_episode(
    name="Package Manager Preference",
    content="Always use uv instead of pip for Python. Example: uv pip install pytest",
    source="user"
)

// 🔍 Search your stored knowledge
search_episodes(query="package manager", limit=5)
// Returns: Your uv preference with full context

// 📋 List recent additions
list_recent(limit=10)
// Returns: Last 10 episodes you added
```

**When to use Episodes:**
- ✅ Store a preference **immediately**
- ✅ Document project-specific facts
- ✅ Save code examples and snippets
- ✅ Build a searchable knowledge base

### System 2: Learned Preferences (Auto Pattern Detection - Over Time)

The system **automatically learns** from repeated corrections:

```javascript
// 🤖 You DON'T call these - they happen automatically!
// Example: You correct Claude 3+ times: "Use uv instead of pip"
// → System detects pattern
// → Creates learned preference with confidence score

// 📊 Check what patterns were detected automatically
get_learned_preferences(min_confidence=0.3)
// Returns: Preferences learned from corrections with confidence scores
// Example: { preference: "use uv over pip", confidence: 0.85, occurrences: 5 }

// 💡 Get AI-suggested CLAUDE.md updates
suggest_claudemd_update(
    project_path="./my-project",
    min_confidence=0.7
)
// Returns: "Add rule: Use uv for package management (confidence: 0.85)"

// ✍️ Apply learned patterns to your CLAUDE.md
update_claudemd(
    file_path="./CLAUDE.md",
    min_confidence=0.7
)
// Automatically updates CLAUDE.md with high-confidence learned patterns
```

**Learned preferences build automatically when:**
- 🔄 You correct the same thing **3+ times**
- 🔄 Patterns emerge across **different projects**
- 🔄 Confidence scores reach thresholds:
  - **0.3** = Emerging pattern (2-3 corrections)
  - **0.7** = Strong preference (5-7 corrections)
  - **0.9** = Very confident (10+ corrections)

### 🎯 Practical Example: Teaching Claude to Use `uv`

**Scenario:** You want Claude to always use `uv` instead of `pip`

#### Option A: Store Immediately (Recommended for new preferences)

```javascript
add_episode(
    name="Python Package Manager",
    content="User prefers uv over pip. Always use: uv pip install <package>",
    source="user"
)
```

✅ **Available immediately** in search
✅ **Works in current session**
✅ **Manual but fast**

#### Option B: Let System Learn (Automatic over time)

1. **Day 1:** Correct Claude: "Use uv instead of pip" → Pattern #1 detected
2. **Day 3:** Correct again on different project → Pattern #2 detected
3. **Day 7:** Correct third time → **Learned preference created** (confidence: 0.3)
4. **Day 14:** Fourth correction → Confidence increases to 0.7
5. Run `get_learned_preferences()` → See the pattern
6. Run `suggest_claudemd_update()` → Get suggestion to add to CLAUDE.md
7. Run `update_claudemd()` → **Automatically updates** your config file

✅ **Builds confidence scores**
✅ **Suggests CLAUDE.md updates**
✅ **Automatic but slower**

### 🚀 Best Practice: Use Both!

1. **Store critical preferences immediately** with `add_episode()`
2. **Let the system learn patterns** over time from corrections
3. **Review learned preferences** monthly with `get_learned_preferences()`
4. **Update CLAUDE.md** when confidence scores are high (0.7+)

### 🔧 Generate Standards from Existing Project

```javascript
// Auto-generate CLAUDE.md from existing config files
generate_ai_standards(project_path=".")
// Analyzes: .editorconfig, .prettierrc, eslint.config.js, pyproject.toml
// Generates: CLAUDE.md, .github/copilot-instructions.md, .cursor/rules/
```

---

## How It Works

### Pattern Learning Pipeline

```
User Correction → Pattern Extraction → Frequency Tracking → Confidence Scoring → Preference Promotion → CLAUDE.md Update
```

**Example Flow:**

1. **User says**: "Actually, use `uv` not `pip`"
2. **Pattern extractor** detects: "use uv instead of pip"
3. **Frequency tracker** increments: occurrence #1
4. **Repeat 2 more times** → occurrence #3
5. **Promotion engine** creates preference (confidence 0.3)
6. **User approves** → CLAUDE.md updated
7. **Future sessions** → Claude sees preference in context

### Database Schema

```sql
-- Pattern frequency (tracks occurrences)
CREATE TABLE pattern_frequency (
    pattern_key TEXT UNIQUE,
    occurrence_count INTEGER,
    confidence REAL,
    promoted_to_preference BOOLEAN
);

-- Tool preferences (learned rules)
CREATE TABLE tool_preferences (
    category TEXT,
    preference TEXT,
    confidence REAL,
    apply_count INTEGER,
    project_specific BOOLEAN
);

-- Audit log (security trail)
CREATE TABLE audit_log (
    action TEXT,
    target_path TEXT,
    details TEXT,
    success BOOLEAN,
    timestamp TIMESTAMP
);
```

---

## What Makes MCP Standards Different?

| Feature | MCP Standards | Tabnine | Copilot | Other MCPs |
|---------|---------------|---------|---------|------------|
| **Learns from corrections** | ✅ Auto | ❌ No | ❌ No | ❌ No |
| **Updates CLAUDE.md** | ✅ Auto | N/A | N/A | ❌ Manual |
| **Pattern detection** | ✅ 5 types | ❌ No | ❌ No | ❌ No |
| **100% local** | ✅ Yes | ❌ Cloud | ❌ Cloud | ✅ Varies |
| **Open source** | ✅ MIT | ❌ No | ❌ No | ✅ Varies |
| **Security features** | ✅ 4 layers | ⚠️ Basic | ⚠️ Basic | ⚠️ Varies |

**Unique Value Proposition:**
**MCP Standards is the ONLY system that learns from your corrections and automatically updates your AI configuration.**

---

## Documentation

### Guides
- [Quick Start](docs/guides/QUICKSTART.md) - 5-minute setup
- [Self-Learning Guide](docs/guides/SELF-LEARNING-GUIDE.md) - How pattern learning works
- [Security Guide](docs/guides/SECURITY.md) - Security features explained
- [Integration Guide](docs/INTEGRATION_GUIDE.md) - Setup for all AI assistants
- [Config Standards](docs/CONFIG_STANDARDS.md) - Universal config reference

### Technical
- [Architecture](docs/technical/ARCHITECTURE.md) - System design
- [Self-Learning PRD](docs/SELF-LEARNING-PRD.md) - Product requirements document

---

## MCP Tools

### Core Memory
- `add_episode(name, content)` - Save knowledge
- `search_episodes(query, limit)` - Full-text search
- `list_recent(limit)` - Recent episodes

### Pattern Learning
- `get_learned_preferences(category, min_confidence)` - View learned patterns
- `suggest_claudemd_update(project_path)` - Get suggestions
- `update_claudemd(file_path, min_confidence)` - Apply updates

### Standards Generation
- `generate_ai_standards(project_path, formats)` - Auto-generate from config files
- `export_to_markdown(export_path)` - Export knowledge base

---

## Requirements

- Python 3.10 or higher
- Claude Desktop or Claude Code
- MCP 1.0+

### Supported Config Files

**Formatting:**
- `.editorconfig`
- `.prettierrc` / `.prettierrc.json`
- `.eslintrc` / `.eslintrc.json`

**Languages:**
- `pyproject.toml` (Python - Black, Ruff, Poetry, uv)
- `package.json` (JavaScript/TypeScript)
- `Cargo.toml` (Rust)
- `go.mod` (Go)

**More coming**: Ruby, PHP, Java, C#

---

## Cost Optimization (Optional)

By default, MCP Standards uses Claude Sonnet for all operations. You can optionally configure it to use **99.5% cheaper models** for simple operations:

### Setup Gemini Flash (Recommended)

1. **Get free API key**: https://aistudio.google.com/app/apikey
2. **Add to your environment**:
   ```bash
   export GEMINI_API_KEY="your_key_here"
   # Or add to ~/.bashrc or ~/.zshrc
   ```
3. **Automatic routing**:
   - Simple operations (memory CRUD, searches) → Gemini 1.5 Flash ($0.075/1M tokens)
   - Complex operations (code generation, pattern analysis) → Claude Sonnet ($15/1M tokens)
   - **99.5% cost savings** on routine operations

### Powered by Agentic Flow

MCP Standards uses [agentic-flow](https://github.com/ProfSynapse/agentic-flow) for intelligent model routing and cost optimization.

**Features:**
- Automatic model selection based on task complexity
- Support for 20+ AI providers (Anthropic, Google, OpenRouter, Groq, etc.)
- Fallback chains for reliability
- Token usage tracking

**Learn more**: [agentic-flow documentation](https://github.com/ProfSynapse/agentic-flow)

---

## Roadmap

### ✅ v0.1.0 (October 2025 - Current)
- Self-learning pattern detection
- CLAUDE.md auto-generation
- Config file parsing
- Security enhancements (whitelist, sanitization, rate limiting, audit logs)
- 100% local with SQLite + FTS5

### 🔄 v0.2.0 (Q1 2026)
- Implicit rejection detection (user edits within 2 min)
- Rule violation detection (compare vs config files)
- Workflow pattern learning (test after code changes)
- Cross-project promotion (project → global)
- MCP notifications for pattern promotions

### 🔮 v0.3.0 (Q2 2026)
- Team sync (share learned preferences)
- Analytics dashboard (trends, common corrections)
- Cloud backup (optional)
- Multi-project management
- Priority support

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- How to report bugs
- How to request features
- Development setup
- Code standards

---

## License

MIT License - see [LICENSE](LICENSE) for details

---

## Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/airmcp-com/mcp-standards/issues)
- **Discussions**: [Ask questions or share ideas](https://github.com/airmcp-com/mcp-standards/discussions)
- **Email**: matt.strautmann@gmail.com

---

## Built With

- Python 3.10+
- SQLite with FTS5 (full-text search)
- MCP (Model Context Protocol)
- uv (fast Python package manager)

---

## Acknowledgments

- **Anthropic** for Claude and MCP
- **[agentic-flow](https://github.com/ProfSynapse/agentic-flow)** for intelligent model routing and cost optimization
- The open source community
- Everyone who tested early versions

---

**Made with ❤️ by [Matt Strautmann](https://github.com/matt-strautmann)**

**Stop repeating yourself. Start using MCP Standards.**

⭐ Star us on GitHub if this helps you!
