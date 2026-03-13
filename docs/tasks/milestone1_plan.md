# Milestone 1: Database Schema Migration - Implementation Plan

## Overview
This document outlines the detailed implementation plan for Milestone 1: Database Schema Migration.

## Branch Information
- **Branch**: `feature/m1-database-schema`
- **Base**: `main` (after PR #4 merge)
- **Model**: `opencode/minimax-m2.5-free` (configured in opencode.json)
- **Worktree**: `/home/mer0/m1-worktree`

## Tasks Breakdown

### Task 1.1: Create VTT Database Schema (python-dev agent)
**Estimated Time**: 2-3 days

#### Subtasks:
1. **Create SQLAlchemy models** for VTT entities:
   - `CharacterRecord` (VTT version) - `sta/database/schema.py`
   - `ShipRecord` (VTT version) - `sta/database/schema.py`
   - `SceneRecord` (enhanced) - `sta/database/schema.py`
   - `CampaignRecord` (enhanced) - `sta/database/schema.py`
   - `UniverseLibraryRecord` - `sta/database/schema.py`
   - `TraitRecord`, `TalentRecord`, `WeaponRecord` - `sta/database/schema.py`

2. **Add migration scripts** in `sta/database/migrations/`:
   - Create Alembic migration for new VTT tables
   - Add indexes for performance
   - Create foreign key relationships

3. **Implement ORM methods**:
   - `to_model()` methods for Pydantic conversion
   - `from_model()` methods for database persistence
   - Add validation for VTT-specific constraints

**Files to Modify**:
- `sta/database/schema.py` (primary)
- `sta/database/migrations/*.py` (new files)
- `tests/conftest.py` (test fixtures)

**Success Criteria**:
- ✅ All VTT tables created in database (verified: 6 tables exist)
- ✅ ORM conversion methods tested (verified: Character and Ship conversions work)
- ✅ All models pass validation tests (verified: 203 tests pass)
- ✅ Legacy documentation complete (verified: legacy_index.md complete)

---

## Milestone 1 Completion Summary

**Completed**: 2026-03-06

### Verification Results:
1. **Database Tables**: 6 VTT tables verified in database
   - vtt_characters, vtt_ships, universe_library, traits, talents, weapons
2. **ORM Methods**: Both VTTCharacterRecord and VTTShipRecord conversions work
3. **Test Suite**: 203 tests passing
4. **Documentation**: legacy_index.md complete

---

### Task 1.2: Implement VTT Model ORM (python-dev agent)
**Estimated Time**: 1-2 days

#### Subtasks:
1. **Create Pydantic ↔ SQLAlchemy converters**:
   - Implement bidirectional conversion
   - Handle nested relationships
   - Add error handling

2. **Implement validation** for VTT-specific constraints:
   - Attribute ranges (7-12 for humanoids)
   - Department ranges (0-5)
   - System values (7-12)
   - Scale validation (1-7)

3. **Create test fixtures** for new models:
   - Sample characters (PC, NPC)
   - Sample ships (player, NPC)
   - Sample scenes (narrative, combat)
   - Sample campaigns

**Files to Modify**:
- `sta/database/schema.py` (conversion methods)
- `tests/conftest.py` (fixtures)
- `tests/test_models.py` (new tests)

**Success Criteria**:
- ✅ Bidirectional conversion working
- ✅ All validation rules enforced
- ✅ Test fixtures available
- ✅ 90%+ test coverage for models

### Task 1.3: Legacy Inventory & Documentation (code-reviewer agent)
**Estimated Time**: 1 day

#### Subtasks:
1. **Complete `docs/legacy_index.md`**:
   - Document all legacy database tables
   - List all legacy model classes
   - Identify all legacy route endpoints
   - Note configuration files to review

2. **Create migration guide**:
   - Step-by-step migration process
   - Data conversion scripts
   - Rollback procedures
   - Testing checklist

3. **Add deprecation warnings**:
   - Mark legacy code with deprecation notices
   - Add migration timelines
   - Document replacement APIs

**Files to Create/Modify**:
- `docs/legacy_index.md` (complete)
- `docs/migration_guide.md` (new)
- Legacy code files (add warnings)

**Success Criteria**:
- ✅ Legacy inventory complete
- ✅ Migration guide documented
- ✅ Deprecation warnings added
- ✅ Rollback procedures defined

## Testing Strategy

### Unit Tests
- Model validation tests
- Serialization/deserialization tests
- Constraint enforcement tests
- ORM conversion tests

### Integration Tests
- Database transaction tests
- Foreign key relationship tests
- Migration script tests
- Data integrity tests

### Regression Tests
- Legacy system still functional
- No breaking changes to existing features
- Backward compatibility maintained

### Test Execution
```bash
# Run all tests
pytest tests/test_models.py tests/test_database.py

# Run with coverage
pytest --cov=sta/database --cov-report=term-missing

# Specific test groups
pytest tests/test_models.py::TestCharacterRecord
pytest tests/test_database.py::TestMigration
```

## Agent Assignment

### python-dev Agent (Primary Implementation)
**Skills**: modern-python, solid, python-pro, test-driven-development
**Model**: `opencode/minimax-m2.5-free`
**Tasks**: 1.1, 1.2

### code-reviewer Agent (Quality Assurance)
**Skills**: modern-python, code-reviewer, security-auditor
**Model**: `opencode/claude-sonnet-4-5`
**Tasks**: 1.3, code reviews

## Workflow

### Development Cycle
1. **python-dev implements** feature in worktree
2. **Run tests** locally
3. **code-reviewer reviews** with quality model
4. **Fix issues** identified
5. **Commit to feature branch**
6. **Push to remote**
7. **Create PR** for integration

### Git Commands
```bash
# In worktree
cd /home/mer0/m1-worktree

# Commit changes
git add .
git commit -m "feat(m1): implement VTT database schema"

# Push to remote
git push origin feature/m1-database-schema

# Create PR
gh pr create --title "feat(m1): VTT database schema" --body "Implements Milestone 1 database migration"
```

## Success Criteria

### Technical
- ✅ All VTT database tables created
- ✅ Alembic migrations functional
- ✅ ORM conversion methods working
- ✅ Validation constraints enforced
- ✅ Test coverage ≥ 90%
- ✅ All tests passing

### Documentation
- ✅ Legacy inventory complete
- ✅ Migration guide created
- ✅ Deprecation warnings added
- ✅ Code comments updated

### Quality
- ✅ Code review approved
- ✅ No breaking changes
- ✅ Performance acceptable
- ✅ Security considerations addressed

## Timeline
- **Total**: 4-5 days
- **Day 1-2**: Database schema implementation
- **Day 3**: ORM and validation
- **Day 4**: Testing and code review
- **Day 5**: Documentation and finalization

## Next Steps

1. **Activate python-dev agent** for Task 1.1
2. **Implement database schema**
3. **Run initial tests**
4. **Activate code-reviewer agent** for review
5. **Iterate until approval**
6. **Proceed to Task 1.2**

**Ready to begin implementation!**

**Question**: Should I activate the python-dev agent to start Task 1.1: Create VTT Database Schema?