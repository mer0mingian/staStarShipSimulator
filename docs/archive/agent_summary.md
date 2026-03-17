# Agent Configuration Summary

## Available Agents and Their Capabilities

### 1. python-dev
**Role**: Implementation
**Phase**: Implementation
**Model**: `inherit` (will use default from opencode.json)
**Skills**: 
- superpowers/subagent-driven-development
- superpowers/test-driven-development
- superpowers/systematic-debugging
- superpowers/verification-before-completion
- python-development/async-python-patterns
- python-development/python-error-handling
- python-development/python-resource-management
- python-development/python-packaging
- python-development/python-testing-patterns
- python-development/python-type-safety
- python-development/python-code-style
- python-development/python-observability
- python-development/python-configuration
- python-dev-agents/python-pro

**Best For**: Core Python implementation, database work, API development
**Recommended Model**: `opencode/minimax-m2.5-free`
**Skills**: modern-python, solid, python-pro, test-driven-development, etc. (free tier)

### 2. code-reviewer
**Role**: Quality Assurance
**Phase**: Review
**Model**: `inherit` (will use default from opencode.json)
**Skills**: 
- superpowers/requesting-code-review
- superpowers/receiving-code-review
- comprehensive-review/code-reviewer
- comprehensive-review/security-auditor
- python-development/python-anti-patterns
- python-development/python-performance-optimization
- differential-review

**Best For**: Code quality reviews, security audits, architecture validation
**Recommended Model**: `opencode/claude-sonnet-4-5`
**Skills**: modern-python, code-reviewer, security-auditor, etc. (high quality for reviews)

### 3. code-auditor
**Role**: Quality Assurance
**Phase**: Audit
**Model**: `inherit` (will use default from opencode.json)
**Skills**: 
- superpowers/requesting-code-review
- superpowers/receiving-code-review
- comprehensive-review/code-reviewer
- comprehensive-review/security-auditor
- python-development/python-anti-patterns
- python-development/python-performance-optimization
- differential-review

**Best For**: Comprehensive code audits, security scanning, performance analysis
**Recommended Model**: `opencode/claude-sonnet-4-5` (high quality for audits)

### 4. architect
**Role**: Design & Planning
**Phase**: Planning, Design
**Model**: `inherit` (will use default from opencode.json)
**Skills**: 
- superpowers/writing-plans
- superpowers/using-git-worktrees
- software-architecture
- system-design
- solid
- comprehensive-review/architect-review
- python-development/python-design-patterns
- python-project-structure
- python-dev-agents/python-pro

**Best For**: System architecture, API design, planning documents
**Recommended Model**: `opencode/claude-sonnet-4-5` (high quality for design)

### 5. orchestrator
**Role**: Coordination
**Phase**: Brainstorming
**Model**: `inherit` (will use default from opencode.json)
**Skills**: 
- superpowers/using-superpowers
- superpowers/brainstorming
- superpowers/writing-plans

**Best For**: Workflow coordination, task management, progress tracking
**Recommended Model**: `opencode/minimax-m2.5-free` (free tier sufficient)

### 6. data-engineer
**Role**: Data & AI Integration
**Phase**: Implementation, Deployment
**Model**: `inherit` (will use default from opencode.json)
**Skills**: 
- databases
- embedding-strategies
- senior-ml-engineer
- python-development/python-performance-optimization

**Best For**: Database schema design, data pipelines, ML integration
**Recommended Model**: `opencode/minimax-m2.5-free` (free tier sufficient)

### 7. cloud-infra
**Role**: Cloud Integration & Deployment
**Phase**: Deployment
**Model**: `inherit` (will use default from opencode.json)
**Skills**: 
- cloudflare
- docker-expert
- building-mcp-server-on-cloudflare
- python-development/python-configuration
- python-development/python-packaging

**Best For**: Deployment, cloud infrastructure, Docker configuration
**Recommended Model**: `opencode/minimax-m2.5-free` (free tier sufficient)

## Model Configuration Strategy

### Current Configuration
The `opencode.json` file currently has:
```json
{
  "model": "anthropic/claude-haiku-4-5"
}
```

### Recommended Updates

#### For Development Work (python-dev, data-engineer, cloud-infra)
```json
{
  "model": "opencode/minimax-m2.5-free",
  "provider": {
    "opencode": {}
  }
}
```

#### For Code Reviews (code-reviewer, code-auditor, architect)
These agents should use higher-quality models for better analysis:
```json
{
  "model": "opencode/claude-sonnet-4-5",
  "provider": {
    "opencode": {}
  }
}
```

### Configuration Approach

Since agent configurations use `model: inherit`, they will use the default model from `opencode.json`. For this project:

1. **Set default to free tier** for most work: `opencode/minimax-m2.5-free`
2. **Override for reviews** by temporarily changing config when needed
3. **Alternative**: Use Task tool to specify model per invocation

## Updated Agent Skill Configuration

### Final Skill Assignment

| Agent | Has modern-python | Has python-pro | Has SOLID | Total Python Skills | Notes |
|-------|-------------------|----------------|-----------|---------------------|-------|
| python-dev | ✅ | ✅ | ✅ | 3 | Primary implementation agent |
| code-reviewer | ✅ | ❌ | ❌ | 1 | Code quality reviews |
| architect | ❌ | ✅ | ❌ | 1 | System design |
| data-engineer | ✅ | ❌ | ❌ | 1 | Database work |
| cloud-infra | ❌ | ❌ | ❌ | 0 | Not needed (local dev) |
| code-auditor | ❌ | ❌ | ❌ | 0 | Inherits from code-reviewer |
| orchestrator | ❌ | ❌ | ❌ | 0 | Coordination only |

### Key Updates

1. **python-dev**: Now has ALL required skills
   - ✅ modern-python (modern tooling: uv, ruff, ty)
   - ✅ solid (SOLID principles)
   - ✅ python-pro (Python development patterns)

2. **cloud-infra**: Not needed for local development
   - Removed from active agent list
   - Will not be used for this project

3. **All other agents**: Maintain their specialized skills

## Agent Assignment Plan

### Milestone 1: Database Schema Migration

| Task | Agent | Model | Skills Needed |
|------|-------|-------|----------------|
| Database schema | python-dev | minimax-m2.5-free | databases, python-pro |
| VTT models | python-dev | minimax-m2.5-free | python-pro, test-driven-development |
| Migration tests | python-dev | minimax-m2.5-free | python-testing-patterns |
| Code review | code-reviewer | claude-sonnet-4-5 | code-reviewer, security-auditor |

### Milestone 2: Campaign Management

| Task | Agent | Model | Skills Needed |
|------|-------|-------|----------------|
| Campaign API | python-dev | minimax-m2.5-free | python-pro, fastapi-pro |
| Universe library | python-dev | minimax-m2.5-free | python-pro |
| Player management | python-dev | minimax-m2.5-free | python-pro |
| Code review | code-reviewer | claude-sonnet-4-5 | code-reviewer |

### Milestone 3: Scene Management

| Task | Agent | Model | Skills Needed |
|------|-------|-------|----------------|
| Scene API | python-dev | minimax-m2.5-free | python-pro |
| Scene transitions | python-dev | minimax-m2.5-free | python-pro |
| Participant management | python-dev | minimax-m2.5-free | python-pro |
| Code review | code-reviewer | claude-sonnet-4-5 | code-reviewer |

## Configuration Instructions

### Option 1: Update opencode.json (Recommended)
```bash
# For development phases
cp opencode.json opencode.json.backup
cat > opencode.json << 'EOF'
{
  "$schema": "https://opencode.ai/config.json",
  "model": "opencode/minimax-m2.5-free",
  "provider": {
    "opencode": {}
  }
}
EOF

# For code review phases
cat > opencode.json << 'EOF'
{
  "$schema": "https://opencode.ai/config.json",
  "model": "opencode/claude-sonnet-4-5",
  "provider": {
    "opencode": {}
  }
}
EOF
```

### Option 2: Per-Agent Configuration
Modify each agent's `.md` file to specify model:
```yaml
---
name: python-dev
model: opencode/minimax-m2.5-free
---
```

### Option 3: Task Tool Specification
When launching agents via Task tool, specify model in prompt:
```
task(description="Database schema work", prompt="/python-dev implement database schema", subagent_type="python-dev", model="opencode/minimax-m2.5-free")
```

## Pydantic Models Analysis

### VTT Models (NEW - Not Legacy)
**Location**: `sta/models/vtt/`

1. **types.py** - Core enumerations and type definitions
   - `Attribute`, `Department`, `System` enums
   - `TraitCategory`, `TalentCategory`, `NpcCategory` enums
   - `Attributes`, `Departments`, `Systems` type aliases

2. **models.py** - Main VTT data models (Pydantic BaseModel)
   - `Trait` - Trait system
   - `Talent` - Talent/ability system  
   - `Weapon` - Weapon definitions
   - `Attack` - Attack patterns
   - `Character` - Base character (Pydantic)
   - `Npc` - NPC extension
   - `Pc` - Player character extension
   - `Ship` - Starship model (Pydantic)
   - `Scene` - Scene model (Pydantic)

3. **campaign.py** - Campaign management models
   - `Campaign` - Campaign model (Pydantic)
   - `UniverseLibrary` - GM content library
   - `TemplateLibrary` - Pre-generated templates

### Legacy Models (Dataclasses)
**Location**: `sta/models/`

1. **character.py** - Legacy character (dataclass)
2. **starship.py** - Legacy starship (dataclass)  
3. **combat.py** - Legacy combat models (dataclass)

### Key Differences

| Aspect | VTT Models (NEW) | Legacy Models |
|--------|------------------|---------------|
| **Technology** | Pydantic BaseModel | Python dataclass |
| **Validation** | Built-in validation | Manual validation |
| **Serialization** | Automatic JSON | Manual conversion |
| **Location** | `sta/models/vtt/` | `sta/models/` |
| **Usage** | New VTT system | Legacy combat |
| **Status** | Active development | To be deprecated |

### Conclusion

✅ **VTT models are NEW, not legacy** - they use modern Pydantic
✅ **Legacy models use dataclasses** - will be replaced
✅ **Clear separation** between old and new systems

## Next Steps

1. **Update opencode.json** with recommended model configuration
2. **Begin Milestone 1** with python-dev agents
3. **Use code-reviewer** with higher-quality model for reviews
4. **Document model usage** in learnings_and_decisions.md

**Recommendation**: Use Option 1 (update opencode.json) for simplicity, switching between free model for development and quality model for reviews.