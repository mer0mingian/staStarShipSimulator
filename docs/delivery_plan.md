1: # VTT Transition Delivery Plan
2: 
3: ## Executive Summary
4: 
5: This document outlines the comprehensive plan for transitioning the Star Trek Adventures Starship Simulator from a dedicated combat encounter tool to a minimal Virtual Tabletop (VTT) experience. The plan covers all milestones with detailed task breakdowns, parallel work assignments, testing strategies, and acceptance criteria.
6: 
7: **Status**: M1-M8 **COMPLETE**. M8.2 (Rules Analysis) **IN PROGRESS** - Documentation synchronization underway.
8: 
9: ---
10: 
11: ## Milestone 8.2: Rules Understanding & Documentation Sync
12: 
13: ### Overview
14: Analyze core rulebook chapters (Ch 4, 5, 6, 7, 8, 9, 11) against VTT mechanics reference. Agent reports are synthesized into the **Acceptance Criteria** section below and the new file `docs/m8.2-open-questions.md`.
15: 
16: ### Status: 📊 IN PROGRESS (Implementation Complete, Cleanup in Progress)
17: 
18: ### Findings Synthesis
19: - **Key Conflict**: The generic Stress mechanic from Ch 8/11 conflicts with NPC rules (Ch 11) and is missing from the core mechanics reference (`game_mechanics_full.md`).
20: - **Key Extension**: Threat Spends (Ch 9) must be added to `game_mechanics_full.md` for Starship Combat.
21: 
### Implementation Completed
- [x] `ThreatManager` class (`sta/mechanics/threat_manager.py`) - 9 unit tests
- [x] `MomentumManager` class (`sta/mechanics/momentum_manager.py`) - 11 unit tests
- [x] Game mechanics documentation extended (`docs/references/game_mechanics.md`)
- [x] Campaign Resource Pools section documenting Momentum/Threat per Ch 4/9

### Cleanup Log (2026-03-18)
The following files were removed but can be restored from git history if needed:
- `CLAUDE.md`, `build_mac.sh`, `star_mac_logo.png`, `dev.sh` - Legacy/project files
- `requirements.txt` / `requirements-dev.txt` - pyproject.toml handles deps
- `SKILLS_SIMPLIFICATION_REPORT.md` - Report file
- `migrate*.py` / `scripts/migrate*.py` - One-off migration scripts (5 files)

To restore: `git checkout <commit> -- <filepath>`

## Milestone 9: Web UI & Theme Support (Future)
24: ## Table of Contents
25: 
26: - [Project Overview](#project-overview)
27: - [Model Configuration](#model-configuration)
28: - [Git Workflow](#git-workflow)
29: - [Milestone 1: Database Schema Migration](#milestone-1-database-schema-migration)
30: - [Milestone 2: Campaign Management](#milestone-2-campaign-management)
31: - [Milestone 3: Scene Management](#milestone-3-scene-management)
32: - [Milestone 4: Character/Ship CRUD](#milestone-4-charactership-crud)
33: - [Milestone 5: Combat Integration](#milestone-5-combat-integration)
34: - [Milestone 6: UI/UX Overhaul](#milestone-6-uiux-overhaul)
35: - [Milestone 7: Import/Export & Final Integration](#milestone-7-importexport--final-integration)
36: - [Milestone 8.2: Rules Understanding](#milestone-82-rules-understanding)
37: - [Parallel Work Strategy](#parallel-work-strategy)
38: - [Testing Strategy](#testing-strategy)
39: - [Code Review Process](#code-review-process)
40: - [Acceptance Criteria](#acceptance-criteria)
41: - [Risk Management](#risk-management)
42: 
43: ## Project Overview
44: 
45: ### Current State
46: - ✅ Working combat encounter system (legacy)
47: - ✅ VTT data models defined (Pydantic schemas)
48: - ✅ Partial campaign/scene implementation
49: - ✅ SQLAlchemy database with legacy schema
50: - ✅ Declarative action system (10-line configs)
51: 
52: ### Target State
53: - ✅ Full VTT experience with campaigns, scenes, characters
54: - ✅ Integrated combat system
55: - ✅ Mobile-responsive UI
56: - ✅ Real-time synchronization
57: - ✅ GM and player workflows
58: 
59: ### Key Constraints
60: - **Model Budget**: Use free models (MiniMax M2.5 Free, Big Pickle) for development
61: - **Code Quality**: All changes must pass code auditor review
62: - **Testing**: Comprehensive test coverage required
63: - **Legacy**: Clean break from legacy system (no data migration needed)
64: 
65: ## Model Configuration
66: 
67: ### Development Models
68: ```json
69: {
70:   "model": "opencode/minimax-m2.5-free",
71:   "provider": {
72:     "opencode": {}
73:   }
74: }
75: ```
76: 
77: ### Code Review Models
78: ```json
79: {
80:   "model": "opencode/claude-sonnet-4-5",
81:   "provider": {
82:     "opencode": {}
83:   }
84: }
85: ```
86: 
87: **Agent Configuration**:
88: - **python-dev agents**: Use `opencode/minimax-m2.5-free` (free tier)
89: - **code-reviewer agents**: Use `opencode/claude-sonnet-4-5` (high quality)
90: - **All agents**: Use `modern-python` skill for best practices
91: 
92: ## Git Workflow
93: 
94: ### Branch Structure
95: ```
96: main (protected)
97:   ├── develop (integration branch)
98:   │   ├── feature/m1-database-schema
99:   │   ├── feature/m2-campaign-mgmt
100:   │   ├── feature/m3-scene-mgmt
101:   │   ├── feature/m4-char-ship-crud
102:   │   ├── feature/m5-combat-integration
103:   │   └── feature/m6-ui-ux-overhaul
104: ```
105: 
106: ### Workflow Rules
107: 1. **Never commit directly to `main`**
108: 2. **Feature branches** created from `main`
109: 3. **Git worktrees** for isolation (managed by agents)
110: 4. **PR to `develop`** for integration testing
111: 5. **PR to `main`** after milestone validation
112: 6. **Code auditor review** before user review
113: 7. **User approval** required for all merges
114: 
115: ### Worktree Management
116: ```bash
117: # Create worktree for feature
118: git worktree add ../feature-m1-database develop
119: 
120: # Work in isolated directory
121: cd ../feature-m1-database
122: 
123: # Create feature branch
124: git checkout -b feature/m1-database-schema
125: 
126: # Work, commit, push
127: # ...
128: 
129: # Cleanup when done
130: git worktree remove ../feature-m1-database
131: ```
132: 
133: ## Milestone 1: Database Schema Migration
134: 
135: ### Overview
136: Create new VTT database schema alongside legacy tables, prepare for clean migration.
137: 
138: ### Status: ✅ COMPLETE (2026-03-06)
139: 
140: ### Tasks
141: 
142: #### Task 1.1: Create VTT Database Schema
143: **Agent**: python-dev
144: **Skills**: modern-python, databases
145: **Model**: `opencode/minimax-m2.5-free`
146: 
147: - [x] Create SQLAlchemy models for VTT entities:
148:   - `VTTCharacterRecord` (VTT version)
149:   - `VTTShipRecord` (VTT version)
150:   - `UniverseLibraryRecord`
151:   - `TraitRecord`, `TalentRecord`, `WeaponRecord`
152: - [x] Create migration in `sta/database/migrations/versions/`
153: - [x] Add indexes for performance
154: 
155: **Files**: `sta/database/vtt_schema.py`, `sta/database/migrations/versions/001_create_vtt_tables.py`
156: 
157: #### Task 1.2: Implement VTT Model ORM
158: **Agent**: python-dev  
159: **Skills**: modern-python
160: **Model**: `opencode/minimax-m2.5-free`
161: 
162: - [x] Create `to_model()` and `from_model()` methods
163: - [x] Add validation for VTT-specific constraints
164: - [x] Test fixtures verified working
165: 
166: **Files**: `sta/database/vtt_schema.py`
167: 
168: #### Task 1.3: Legacy Inventory & Documentation
169: **Agent**: code-reviewer
170: **Skills**: documentation, analysis
171: **Model**: `opencode/claude-sonnet-4-5`
172: 
173: - [x] Complete `docs/legacy_index.md`
174: - [x] Document all legacy components
175: 
176: **Files**: `docs/legacy_index.md`
177: 
178: ### Verification Results
179: - ✅ 6 VTT tables exist in database
180: - ✅ ORM conversion methods tested (Character and Ship)
181: - ✅ 203 tests passing
182: - ✅ Documentation complete
183: 
184: ### Timeline: COMPLETE
185: 
186: ### Testing Strategy
187: - **Unit Tests**: Model validation, serialization
188: - **Integration Tests**: Database operations, transactions
189: - **Regression Tests**: Ensure legacy still works
190: - **Migration Tests**: Data conversion scripts
191: 
192: ### Acceptance Criteria
193: - ✅ New VTT tables created in database
194: - ✅ All models pass validation tests
195: - ✅ Legacy system still functional
196: - ✅ Migration scripts tested
197: - ✅ Documentation complete
198: 
199: ### Timeline: 3-5 days
200: 
201: ## Milestone 2: Campaign Management
202: 
203: ### Overview
204: Full campaign lifecycle management with GM controls and player access.
205: 
206: ### Status: ✅ COMPLETE (2026-03-06)
207: 
208: ### Detailed Tasks
209: See `docs/tasks/milestone2_tasks.md` for specific implementation steps.
210: 
211: ### Current State (as of M2 completion)
212: - Campaign resource pools (Momentum/Threat) exist
213: - Universe Library API functional
214: - VTT character/ship integration with campaigns
215: - Session token system with expiration
216: 
217: ---
218: 
219: #### Task 2.1: Campaign CRUD API
220: **Agent**: python-dev
221: **Skills**: modern-python, fastapi-pro
222: **Model**: `opencode/minimax-m2.5-free`
223: 
224: - [ ] Implement `/api/campaigns/*` endpoints:
225:   - `POST /api/campaigns` - Create campaign
226:   - `GET /api/campaigns/{id}` - Get campaign
227:   - `PUT /api/campaigns/{id}` - Update campaign
228:   - `DELETE /api/campaigns/{id}` - Delete campaign
229:   - `GET /api/campaigns` - List campaigns
230: - [ ] Add GM authentication middleware
231: - [ ] Implement resource pool management (Momentum/Threat)
232: 
233: **Files**: `sta/web/routes/campaigns.py`, `sta/web/routes/api.py`
234: 
235: #### Task 2.2: Universe Library
236: **Agent**: python-dev
237: **Skills**: modern-python
238: **Model**: `opencode/minimax-m2.5-free`
239: 
240: - [ ] Implement `/api/universe/*` endpoints:
241:   - Character library management
242:   - Ship library management  
243:   - Item/equipment library
244:   - Document templates
245: - [ ] Add category filtering (PCs, NPCs, Creatures, Ships)
246: - [ ] Implement GM-only access controls
247: 
248: **Files**: `sta/web/routes/universe.py` (new)
249: 
250: #### Task 2.3: Player Management
251: **Agent**: python-dev
252: **Skills**: modern-python
253: **Model**: `opencode/minimax-m2.5-free`
254: 
255: - [ ] Implement `/api/campaigns/{id}/players` endpoints
256: - [ ] Add character assignment workflow
257: - [ ] Implement session token system
258: - [ ] Add position assignment (Captain, Helm, etc.)
259: 
260: **Files**: `sta/web/routes/campaigns.py`
261: 
262: ### Testing Strategy
263: - **Unit Tests**: API endpoint validation
264: - **Integration Tests**: Campaign lifecycle workflows
265: - **Security Tests**: Authentication and authorization
266: - **Concurrency Tests**: Multiple players joining
267: 
268: ### Acceptance Criteria
269: - ✅ Campaign CRUD fully functional
270: - ✅ Universe library with categories
271: - ✅ Player management with character assignment
272: - ✅ GM authentication working
273: - ✅ All tests passing
274: 
275: ### Status: ✅ COMPLETE
276: 
277: ### Detailed Tasks
278: See `docs/tasks/milestone2_tasks.md` for implementation details and test results.
279: 
280: ### Completed Features
281: - Campaign resource pools (Momentum/Threat)
282: - Universe Library API (characters/ships with categories)
283: - VTT character/ship integration (linking tables, endpoints)
284: - Session token enhancement (expiration, refresh)
285: 
286: All 257 tests passing (including 54 new M2 tests).
287: 
288: ---
289: 
290: ## Milestone 3: Scene Management
291: 
292: ### Overview
293: Complete scene lifecycle with narrative and combat support.
294: 
295: ### Status: ✅ COMPLETE
296: 
297: ### Testing Strategy
298: See `docs/tasks/milestone3_tasks.md` for complete task breakdown.
299: 
300: ---
301: 
302: ## Milestone 5: VTT Scene Lifecycle & Combat Integration
303: 
304: ### Overview
305: Complete migration from Flask to FastAPI and implement new 4-state scene lifecycle with multi-scene support.
306: 
307: ### Status: ✅ COMPLETE (2026-03-17)
308: 
309: ### Scene Lifecycle (NEW - 2026-03-15)
310: 
311: The VTT now supports a 4-state scene lifecycle:
312: 
313: | State | Description | Visibility |
314: |-------|-------------|------------|
315: | **draft** | No title or player character list | GM only, never visible to players |
316: | **ready** | Has title + GM-short-description | Available in scene-transition dialogue |
317: | **active** | Currently in progress | All participants, can have multiple |
318: | **completed** | Archived | Can be re-activated or copied |
319: 
320: #### State Transitions
321: 
322: ```
323: draft ──(GM adds title+PCs)──► ready ──(GM activates)──► active ──(GM ends)──► completed
324:                                             ▲                      │
325:                                             │                      ▼
326:                                             └────(re-activate)─────┘
327:                                             └────(copy)──────────► ready (new)
328: ```
329: 
330: #### Scene Transition Dialogue
331: 
332: When completing a scene, GM sees:
333: 1. **Connected scenes** (first) - scenes linked to current
334: 2. **Ready scenes** (dropdown last) - available to activate
335: 3. **Create new scene** - on-the-fly creation
336: 
337: #### Split-Party Support (NEW)
338: 
339: - Multiple scenes can be **active** simultaneously
340: - GM can **switch focus** between parallel active scenes
341: - **All party members visible** even when not in active scene
342: 
343: #### Connection Termination
344: 
345: - Completing a scene **terminates its connections**
346: - Connected scenes must be re-linked after re-activation
347: 
348: ### Tasks
349: 
350: #### Task 5.1: FastAPI App Factory
351: **Agent**: python-dev
352: **Model**: `opencode/minimax-m2.5-free`
353: 
354: - [x] Create FastAPI application factory in `sta/web/app.py`
355: - [x] Implement router registration for all endpoints
356: - [x] Add async database session handling
357: - [x] Configure CORS and middleware
358: 
359: **Files**: `sta/web/app.py`
360: 
361: #### Task 5.2: Route Migration
362: **Agent**: python-dev
363: **Model**: `opencode/minimax-m2.5-free`
364: 
365: - [x] Migrate campaigns_router.py to FastAPI
366: - [x] Migrate universe_router.py to FastAPI
367: - [x] Migrate api_router.py to FastAPI
368: - [x] Migrate scenes_router.py to FastAPI
369: - [x] Migrate characters_router.py to FastAPI
370: - [x] Migrate ships_router.py to FastAPI
371: - [x] Migrate encounters_router.py to FastAPI
372: 
373: **Files**: `sta/web/routes/*.py`
374: 
375: #### Task 5.3: Test Infrastructure Update
376: **Agent**: python-dev
377: **Model**: `opencode/minimax-m2.5-free`
378: 
379: - [x] Update conftest.py for FastAPI TestClient
380: - [x] Fix async database fixtures
381: - [x] Add session token cookie handling
382: 
383: **Files**: `tests/conftest.py`
384: 
385: ### Test Progress
386: 
387: | Metric | Before | After |
388: |--------|--------|-------|
389: | Failed Tests | N/A | 130 |
390: | Passed Tests | N/A | 284 |
391: | Total Tests | 414 | 414 |
392: 
393: ### Key Accomplishments
394: 
395: 1. **Router infrastructure** - All major routes now registered in FastAPI
396: 2. **Action endpoints** - claim-turn, release-turn, next-turn, fire, ram
397: 3. **Import/Export** - characters, ships, NPCs, backup endpoints
398: 4. **Scene endpoints** - participants, ships, activation
399: 5. **Minor action enforcement** - prevents 2nd minor action (403)
400: 6. **Model fixes** - sensors attribute access
401: 
402: ### Remaining Issues (130 failures)
403: 
404: | Category | Count | Issue |
405: |----------|-------|-------|
406: | Scene tests | 41 | Validation/logic |
407: | Import/Export | 30 | Specific fields |
408: | Personnel | 10 | Validation |
409: | Session Tokens | 8 | Flask redirects |
410: | Other | 41 | Various |
411: 
412: ### Current Test State (2026-03-15)
413: 
414: | Metric | Value |
415: |--------|-------|
416: | Failed Tests | 122 → 110 → 102 → 93 → 86 → 47 → 39 → 37 → 38 → 34 |
417: | Passed Tests | 292 → 304 → 312 → 321 → 328 → 334 → 342 → 344 → 343 → 347 |
418: | Total Tests | 414 → 370 → 381 |
419: 
420: ### Key Issues Identified
421: 
422: | Category | Count | Examples |
423: |----------|-------|----------|
424: | **404 Route Errors** | ~30 | Scene API endpoints returning 404 (FastAPI routing issues) |
425: | **Flask 3.x API Changes** | ~15 | `get_data()` removed, `delete_cookie` missing |
426: | **Async/SQLAlchemy Issues** | ~10 | MissingGreenlet, AsyncEngine inspection errors |
427: | **Status Code Mismatches** | ~15 | 422 vs 400, 200 vs 400, 404 vs 302 |
428: | **Logic Errors** | ~5 | Scene activation returns 'draft' instead of 'active' |
429: 
430: ### Proposed Fix Order
431: 
432: 1. **Fix FastAPI Routing** - Routes not properly registered (likely `/api/` prefix issues)
433: 2. **Fix/Remove Flask Remainders** - Update tests for Flask 3.x TestClient API changes
434: 3. **Fix Async Issues** - Use `run_sync` for SQLAlchemy inspection in async context
435: 4. **Fix Scene Activation** - Clarify logic bug returning wrong status
436: 
437: ### Acceptance Criteria
438: 
439: - [ ] Core routing migration complete
440: - [ ] All endpoints return non-404 responses
441: - [ ] Turn order logic working
442: - [ ] All tests passing (target: 0 failed)
443: 
444: ---
445: 
446: ## Milestone 4: Character/Ship CRUD
447: 
448: ### Overview
449: Complete character and ship creation, management, and library integration.
450: 
451: ### Tasks
452: 
453: #### Task 4.1: Character Management
454: **Agent**: python-dev
455: **Skills**: modern-python
456: **Model**: `opencode/minimax-m2.5-free`
457: 
458: - [ ] Implement `/api/characters/*` endpoints:
459:   - CRUD for PCs and NPCs
460:   - Attribute/department management
461:   - Trait/talent assignment
462:   - Equipment and attack management
463:   - State tracking (Ok, Defeated, Fatigued, Dead)
464: - [ ] Add character import/export
465: - [ ] Implement species and role management
466: 
467: **Files**: `sta/web/routes/characters.py` (new)
468: 
469: #### Task 4.2: Ship Management
470: **Agent**: python-dev
471: **Skills**: modern-python
472: **Model**: `opencode/minimax-m2.5-free`
473: 
474: - [ ] Implement `/api/ships/*` endpoints:
475:   - CRUD for player and NPC ships
476:   - System/department management
477:   - Weapon and talent assignment
478:   - Power/shield tracking
479:   - Trait management
480: - [ ] Add ship class and scale validation
481: - [ ] Implement crew quality for NPC ships
482: 
483: **Files**: `sta/web/routes/ships.py` (new)
484: 
485: #### Task 4.3: Library Integration
486: **Agent**: python-dev
487: **Skills**: modern-python
488: **Model**: `opencode/minimax-m2.5-free`
489: 
490: - [ ] Connect characters/ships to Universe Library
491: - [ ] Implement library search and filtering
492: - [ ] Add duplicate detection
493: - [ ] Create template system for quick creation
494: - [ ] Implement GM-only library management
495: 
496: **Files**: `sta/web/routes/universe.py`, `sta/web/routes/characters.py`, `sta/web/routes/ships.py`
497: 
498: ### Testing Strategy
499: - **Unit Tests**: Model validation and constraints
500: - **Integration Tests**: CRUD workflows
501: - **Import/Export Tests**: Data serialization
502: - **Library Tests**: Search and filtering
503: 
504: ### Acceptance Criteria
505: - ✅ Character CRUD with all attributes
506: - ✅ Ship CRUD with systems and weapons
507: - ✅ Library integration with templates
508: - ✅ Import/export functionality
509: - ✅ All tests passing
510: 
511: ### Timeline: 5-7 days
512: 
513: ## Milestone 5: Combat Integration
514: 
515: ### Overview
516: Integrate existing combat system with new VTT architecture.
517: 
518: ### Tasks
519: 
520: #### Task 5.1: Combat Scene Type
521: **Agent**: python-dev
522: **Skills**: modern-python
523: **Model**: `opencode/minimax-m2.5-free`
524: 
525: - [ ] Enhance Scene model for combat support
526: - [ ] Add tactical map integration
527: - [ ] Implement hex grid system
528: - [ ] Add terrain and visibility rules
529: - [ ] Create combat state tracking
530: 
531: **Files**: `sta/models/vtt/models.py`, `sta/mechanics/combat.py` (new)
532: 
533: #### Task 5.2: Action System Integration
534: **Agent**: python-dev
535: **Skills**: modern-python
536: **Model**: `opencode/minimax-m2.5-free`
537: 
538: - [ ] Adapt declarative action system for VTT
539: - [ ] Integrate with new Scene model
540: - [ ] Add range and system requirement checks
541: - [ ] Implement action logging
542: - [ ] Create combat turn management
543: 
544: **Files**: `sta/mechanics/action_config.py`, `sta/web/routes/api.py`
545: 
546: #### Task 5.3: Combat UI Integration
547: **Agent**: python-dev
548: **Skills**: modern-python
549: **Model**: `opencode/minimax-m2.5-free`
550: 
551: - [ ] Update combat templates for VTT
552: - [ ] Integrate with scene views
553: - [ ] Add GM combat controls
554: - [ ] Implement player action interface
555: - [ ] Create combat log display
556: 
557: **Files**: `sta/web/templates/combat.html`, `sta/web/templates/scenes.html`
558: 
559: ### Testing Strategy
560: - **Unit Tests**: Combat mechanics and calculations
561: - **Integration Tests**: Combat workflows
562: - **Regression Tests**: Existing combat still works
563: - **Action Tests**: All actions functional
564: 
565: ### Acceptance Criteria
566: - ✅ Combat scenes fully functional
567: - ✅ Action system integrated
568: - ✅ Tactical map working
569: - ✅ Combat UI updated
570: - ✅ All tests passing
571: 
572: ### Timeline: 7-10 days
573: 
574: ## Milestone 6: UI/UX Overhaul
575: 
576: ### Overview
577: Complete UI/UX redesign for mobile-responsive VTT experience.
578: 
579: ### Status: 🚧 IN PROGRESS
580: 
581: #### 6.1: Campaign Dashboard
582: **Agent**: python-dev
583: **Skills**: modern-python
584: **Model**: `opencode/minimax-m2.5-free`
585: 
586: - [ ] Redesign campaign selection interface
587: - [ ] Create campaign overview dashboard
588: - [ ] Implement mobile-responsive layout
589: - [ ] Add campaign statistics display
590: - [ ] Create GM/player view toggles
591: 
592: **Files**: `sta/web/templates/campaigns.html`, `sta/static/css/`
593: 
594: #### 6.2: Scene Management UI
595: **Agent**: python-dev
596: **Skills**: modern-python
597: **Model**: `opencode/minimax-m2.5-free`
598: 
599: - [ ] Redesign scene creation interface
600: - [ ] Create scene navigation system
601: - [ ] Implement scene type selection
602: - [ ] Add participant management UI
603: - [ ] Create scene transition controls
604: 
605: **Files**: `sta/web/templates/scenes.html`, `sta/static/js/scenes.js`
606: 
607: #### 6.3: Character/Ship Builders
608: **Agent**: python-dev
609: **Skills**: modern-python
610: **Model**: `opencode/minimax-m2.5-free`
611: 
612: - [ ] Create character builder interface
613: - [ ] Design ship configuration UI
614: - [ ] Implement library browser
615: - [ ] Add template selection
616: - [ ] Create import/export interface
617: 
618: **Files**: `sta/web/templates/characters.html`, `sta/web/templates/ships.html`
619: 
620: ### Testing Strategy
621: - **Unit Tests**: Template rendering
622: - **Integration Tests**: UI workflows
623: - **Browser Tests**: Cross-browser compatibility
624: - **Mobile Tests**: Responsive design
625: - **Accessibility Tests**: WCAG compliance
626: 
627: ### Acceptance Criteria
628: - ✅ Mobile-responsive design
629: - ✅ Intuitive navigation
630: - ✅ Character/ship builders functional
631: - ✅ GM and player views optimized
632: - ✅ All tests passing
633: 
634: ### Timeline: 10-14 days
635: 
636: ## Milestone 7: Import/Export & Final Integration
637: 
638: ### Overview
639: Implement import/export functionality and complete VTT integration.
640: 
641: ### Status: 📋 Planned
642: 
643: ### Tasks
644: 
645: #### Task 7.1: VTT Character Export/Import
646: - Export characters to JSON
647: - Import characters from JSON
648: - Handle updates to existing characters
649: 
650: #### Task 7.2: VTT Ship Export/Import
651: - Export ships to JSON
652: - Import ships from JSON
653: - Handle updates to existing ships
654: 
655: #### Task 7.3: Full Campaign Backup
656: - Export entire campaign to JSON
657: - Import full campaign backup
658: - Validate backup structure
659: 
660: ### Reference
661: See `docs/tasks/milestone7_tasks.md` for detailed specification.
662: 
663: ### Timeline: 3-5 days
664: 
665: ## Parallel Work Strategy
666: 
667: ### Agent Assignment
668: 
669: | Milestone | Agent 1 (Database/API) | Agent 2 (Models/Logic) | Agent 3 (Tests/Integration) |
670: |-----------|------------------------|------------------------|-----------------------------|
671: | M1 | Database schema | VTT models | Migration tests |
672: | M2 | Campaign API | Universe library | Campaign tests |
673: | M3 | Scene API | Scene transitions | Scene tests |
674: | M4 | Character API | Ship management | CRUD tests |
675: | M5 | Combat integration | Action system | Combat tests |
676: | M6 | UI components | UI logic | UI tests |
677: 
678: ### Workflow
679: 
680: 1. **Daily Standup**: Agents report progress, blockers
681: 2. **Continuous Integration**: Merge to `develop` frequently
682: 3. **Code Reviews**: Cross-agent reviews before PR
683: 4. **User Demos**: Show progress after each milestone
684: 
685: ### Communication
686: 
687: - **Shared Context**: All agents read `docs/learnings_and_decisions.md`
688: - **Blockers**: Escalate to user immediately
689: - **Decisions**: Document in learning log
690: - **Conflicts**: User arbitrates
691: 
692: ## Testing Strategy
693: 
694: ### Test Coverage Requirements
695: 
696: - **Unit Tests**: 90%+ coverage for business logic
697: - **Integration Tests**: All critical workflows
698: - **Regression Tests**: Legacy functionality preserved
699: - **E2E Tests**: Major user journeys
700: 
701: ### Test Execution
702: 
703: ```bash
704: # Before every commit
705: pytest
706: 
707: # Before PR
708: pytest --cov=sta --cov-report=term-missing
709: 
710: # Specific tests
711: pytest tests/test_*.py -v
712: ```
713: 
714: ### Test Categories
715: 
716: 1. **Model Tests**: Pydantic validation, serialization
717: 2. **Database Tests**: CRUD operations, transactions
718: 3. **API Tests**: Endpoint validation, error handling
719: 4. **Integration Tests**: Workflow testing
720: 5. **UI Tests**: Template rendering, JavaScript
721: 6. **Regression Tests**: Legacy compatibility
722: 
723: ## Code Review Process
724: 
725: ### Review Workflow
726: 
727: 1. **Agent implements feature** in feature branch
728: 2. **Agent runs tests** and fixes issues
729: 3. **Code auditor reviews** with `opencode/claude-sonnet-4-5`
730: 4. **Agent fixes review issues**
731: 5. **Agent creates PR** to `develop`
732: 6. **User reviews and approves**
733: 7. **Merge to develop** for integration
734: 8. **Repeat for main** after milestone complete
735: 
736: ### Review Checklist
737: 
738: - [ ] Code follows existing patterns
739: - [ ] Tests pass (including new tests)
740: - [ ] Documentation updated
741: - [ ] No breaking changes
742: - [ ] Error handling adequate
743: - [ ] Performance acceptable
744: - [ ] Security considerations addressed
745: 
746: ## Acceptance Criteria
747: 
748: ### Per Milestone
749: 
750: - ✅ All tasks completed
751: - ✅ All tests passing
752: - ✅ Code review approved
753: - ✅ Documentation updated
754: - ✅ User acceptance obtained
755: - ✅ No regressions introduced
756: 
757: ### Final Delivery
758: 
759: - ✅ All 6 milestones completed
760: - ✅ Full VTT functionality working
761: - ✅ Legacy code removed
762: - ✅ Comprehensive test suite
763: - ✅ User documentation complete
764: - ✅ Production ready
765: 
766: ## Risk Management
767: 
768: ### Identified Risks
769: 
770: 1. **Model Limitations**: Free models may have context limits
771:    - **Mitigation**: Break tasks into smaller chunks
772: 
773: 2. **Merge Conflicts**: Parallel work may cause conflicts
774:    - **Mitigation**: Use git worktrees, frequent integration
775: 
776: 3. **Legacy Dependencies**: Undiscovered dependencies on old code
777:    - **Mitigation**: Comprehensive testing, gradual deprecation
778: 
779: 4. **Performance Issues**: New VTT features may be slow
780:    - **Mitigation**: Add indexes, optimize queries, load testing
781: 
782: 5. **UI Complexity**: Mobile-responsive design challenges
783:    - **Mitigation**: Use framework (Bootstrap/Tailwind), test on devices
784: 
785: ### Contingency Plans
786: 
787: 1. **Fallback Models**: If free models underperform, use `opencode/claude-haiku-4-5`
788: 2. **Feature Flags**: Disable problematic features temporarily
789: 3. **Rollback Plan**: Keep legacy system until VTT stable
790: 4. **Performance Optimization**: Profile and optimize critical paths
791: 
792: ## Success Metrics
793: 
794: ### Quantitative
795: - ✅ 90%+ test coverage
796: - ✅ 0 critical bugs in production
797: - ✅ < 2s response time for API endpoints
798: - ✅ < 5s page load time
799: - ✅ 100% milestone completion
800: 
801: ### Qualitative
802: - ✅ Intuitive user experience
803: - ✅ GM has sufficient control
804: - ✅ Players enjoy the interface
805: - ✅ Mobile-friendly on tablets
806: - ✅ Stable and reliable
807: 
808: ## Immediate Next Steps (2026-03-17)
809: 
810: ### Current State
811: - M6 PR #14 merged to vtt-scope
812: - M7 branch created: `m7-branch`
813: - M7 task document ready: `docs/tasks/milestone7_tasks.md`
814: 
815: ### Pending: M7 Agent Deployment
816: 
817: **Three agents to deploy in parallel:**
818: 
819: | Agent | Task | Worktree Branch |
820: |-------|------|------------------|
821: | Agent 1 | M7.1 Character Export/Import | feature/m7-character-import-export |
822: | Agent 2 | M7.2 Ship Export/Import | feature/m7-ship-import-export |
823: | Agent 3 | M7.3 Campaign Backup | feature/m7-campaign-backup |
824: 
825: **Commands to create worktrees (for agents):**
826: ```bash
827: # Agent 1
828: git worktree add -b feature/m7-character-import-export ../m7-character-import-export m7-branch
829: cd ../m7-character-import-export && uv venv && uv pip install -r requirements.txt -r requirements-dev.txt
830: 
831: # Agent 2
832: git worktree add -b feature/m7-ship-import-export ../m7-ship-import-export m7-branch
833: cd ../m7-ship-import-export && uv venv && uv pip install -r requirements.txt -r requirements-dev.txt
834: 
835: # Agent 3
836: git worktree add -b feature/m7-campaign-backup ../m7-campaign-backup m7-branch
837: cd ../m7-campaign-backup && uv venv && uv pip install -r requirements.txt -r requirements-dev.txt
838: ```
839: 
840: **After Agents Complete:**
841: 1. Merge feature/m7-character-import-export → m7-branch
842: 2. Merge feature/m7-ship-import-export → m7-branch
843: 3. Merge feature/m7-campaign-backup → m7-branch
844: 4. Run full test suite: `uv run pytest -q`
845: 5. Clean up worktrees
846: 6. Push m7-branch to origin
847: 7. Create PR to vtt-scope
848: 
849: ### Documentation Updates After M7
850: - Mark M7 complete in README.md
851: - Mark M7 complete in docs/delivery_plan.md
852: - Mark M7 complete in docs/README.md
853: - Update milestone status in docs/tasks/milestone7_tasks.md
854: 
855: ---
856: 
857: ## Next Steps (Original)
858: 
859: 1. **User Review**: Please review this delivery plan
860: 2. **Approvals**: Confirm approach and timeline
861: 3. **Adjustments**: Make any needed changes
862: 4. **Kickoff**: Begin Milestone 1 implementation
863: 
864: **Question**: Does this plan meet your expectations? Are there any adjustments needed before we proceed?

(End of file - total 864 lines)
</content>