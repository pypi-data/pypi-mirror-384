# Quick Start: Self-Learning Claude Code

**Get started in 5 minutes!**

---

## Installation

```bash
# Clone the repository
git clone https://github.com/airmcp-com/mcp-standards.git
cd mcp-standards

# Install dependencies
uv sync

# Restart Claude Desktop
# macOS: Cmd+Q, then reopen
```

---

## Test It Works

### 1. Basic Memory Test
```javascript
add_episode(
  name="Setup Test",
  content="Self-learning system operational!",
  source="quickstart"
)
```

**Expected**: Success with routing info showing Gemini Flash (cost: ~$0.000075)

### 2. Cost Savings Check
```javascript
get_cost_savings()
```

**Expected**: Report showing savings vs Claude pricing

### 3. Learning Test - Make 3 Corrections

```javascript
// Correction 1 - System captures it
"Use uv instead of pip for this project"
// → Captured in database, pattern noted

// Correction 2 - System strengthens pattern
"No, use uv not pip"
// → Pattern count: 2, confidence increasing

// Correction 3 - System promotes to preference!
"Always use uv for Python packages"
// → Automatically added to tool_preferences
// → CLAUDE.md will update
// → Future sessions apply automatically
```

### 4. Generate AI Standards
```javascript
generate_ai_standards(
  project_path="/path/to/your/project",
  formats=["claude", "cursor", "copilot"]
)
```

**Expected**: Generated CLAUDE.md with learned preferences

---

## What's Happening Automatically

✅ **Every tool execution** → Captured by hooks
✅ **Corrections detected** → Patterns extracted
✅ **3+ repetitions** → Promoted to preferences
✅ **CLAUDE.md updates** → Auto-generated from patterns
✅ **Agent usage** → Performance tracked
✅ **Costs optimized** → 99.5% savings via smart routing

---

## Common Workflows

### Learn a Preference Manually
```javascript
learn_preference(
  category="python-testing",
  context="After code changes",
  preference="Always run pytest before committing"
)
```

### Check Agent Performance
```javascript
query_agent_performance(
  time_range_days=30
)
```

### Validate Against Spec
```javascript
validate_spec(
  task_description="Build user authentication with JWT",
  deliverable_summary="Implemented JWT auth with login/logout endpoints"
)
```

### Check Quality Gates
```javascript
check_quality_gates(
  project_path="/path/to/project",
  gate_types=["tests", "docs"]
)
```

---

## Cost Savings Examples

### Memory Operations (Simple → Gemini Flash)
```javascript
// 100 operations
add_episode(...) // ×100

// Cost: $0.0075 (Gemini Flash)
// vs $1.50 (Claude)
// Savings: $1.49 per 100 operations
```

### Pattern Analysis (Moderate → DeepSeek)
```javascript
// 50 pattern extractions
// Runs automatically via hooks

// Cost: $0.014 (DeepSeek)
// vs $1.50 (Claude)
// Savings: $1.486 per 50 extractions
```

### CLAUDE.md Generation (Complex → Claude)
```javascript
// 10 generations
generate_claudemd(...) // ×10

// Cost: $0.45 (Claude - needed for quality)
// Still uses premium model when it matters!
```

**Monthly Savings**: ~$389 on typical usage

---

## Troubleshooting

### Hooks Not Capturing
```bash
# Check hooks file
cat ~/.claude/hooks.json

# Verify path is correct
which python3

# Test manually
python3 /path/to/hooks/capture_hook.py
```

### Cost Optimization Not Working
```bash
# Check environment
echo $COST_OPTIMIZATION

# Verify Gemini key
cat .env | grep GEMINI_API_KEY

# Test agentic-flow MCP
# In Claude: /mcp
# Should show: agentic-flow (connected)
```

### Database Issues
```bash
# Check database
sqlite3 ~/.mcp-standards/knowledge.db "SELECT COUNT(*) FROM tool_preferences"

# Re-run migrations
cd /path/to/mcp-standards
uv run python src/mcp_standards/schema_migration.py
```

---

## Next Steps

1. ✅ **Use it naturally** - System learns automatically
2. ✅ **Make corrections** - Gets smarter with each one
3. ✅ **Check savings weekly** - `get_cost_savings()`
4. ✅ **Review CLAUDE.md** - See what it learned
5. ✅ **Trust the system** - It learns your patterns

---

## Documentation

- **Full PRD**: `docs/SELF-LEARNING-PRD.md`
- **Cost Details**: `docs/COST-OPTIMIZATION-AGENTIC-FLOW.md`
- **Complete Summary**: `docs/IMPLEMENTATION-COMPLETE.md`

---

## Key Insight

**Stop telling Claude Code what to do repeatedly.**
**Let it learn once and remember forever.**

The system transforms:
- "Use uv not pip" × 100 times ❌
- "Use uv not pip" × 3 times → learned! ✅

---

**That's it! Start using Claude Code normally - it learns automatically.** 🚀
