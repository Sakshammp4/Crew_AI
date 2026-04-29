cat > README.md << 'EOF'
# CreeUI - CrewAI Project Collection

Collection of CrewAI multi-agent systems.

## Projects

| Project | Description | Run Command |
|---------|-------------|-------------|
| [startup_idea_validator/](cci:9://file:///Users/sakshamgupta/startup_idea_validator:0:0-0:0) | Validates startup ideas with multi-agent analysis | `cd startup_idea_validator && crewai run` |
| `customer_support_agent/` | AI customer support automation | `cd customer_support_agent && crewai run` |

## Quick Start

```bash
# Clone specific project only
git clone --depth 1 --filter=blob:none --sparse https://github.com/YOUR_USERNAME/CreeUI.git
cd CreeUI
git sparse-checkout set startup_idea_validator