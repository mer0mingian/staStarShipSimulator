# Immediate Tasks for Next Session (Post-M3)

**Milestone 3: Scene Management** is complete. Next focus: **Milestone 4: Character/Ship CRUD**.

## Outstanding Items from M3
- [x] Task 3.2: Scene connections
- [x] Task 3.3: Participants & ships CRUD
- [x] Task 3.4: Activation/termination/config
- [x] All M3 tests passing (43/43)
- [ ] Fix pre-existing test failures in `test_scene_participants.py` and `test_scene_ships.py` (campaign_id vs id mismatch)
- [ ] Initialize `pyproject.toml` for uv project
- [ ] Review and merge PR #8 to `vtt-scope` (user action)

## Next Steps (M4 Preparation)
1. Review `docs/milestone3_tasks.md` for complete M3 reference.
2. Create `docs/milestone4_tasks.md` with detailed task breakdown for Character/Ship CRUD.
3. Prepare agent configurations for parallel work on M4.
4. Consider Flask → FastAPI migration (optional M3.5) after M4.

## Notes
- Pre-existing test failures are unrelated to M3 and should be fixed before M4 work to keep test suite green.
- `uv` is now recommended for dependency management; see README.md for commands.
- Worktree-based parallel agent workflow proven successful for M3; document in learnings_and_decisions.md.
