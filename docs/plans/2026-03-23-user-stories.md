# STA VTT User Stories

**Date:** 2026-03-23  
**Project:** Star Trek Adventures (STA) Virtual Tabletop Simulator  
**Reference:** `docs/pages_overview.md`, `docs/references/game_machanics.md`, `docs/references/objects.md`, `docs/tasks/milestone10_tasks.md`

---

## PLAYER User Stories

### 1. Character Creation - Foundation Step

**Title:** As a Player, I want to create my character's Foundation so that I can establish my character's basic attributes and species.

**Acceptance Criteria:**
- **Given** I am on the character creation wizard at `/characters/new/wizard`
- **When** I am on the "Foundation" step (step 1)
- **Then** I can select a Species from the available options (Human, Vulcan, Andorian, etc.)
- **And** I can assign Attributes (Control, Daring, Fitness, Insight, Presence, Reason) within the 7-12 range
- **And** I can optionally enter Background information (Environment, Upbringing, Career Path)
- **And** I cannot proceed to the next step without completing required fields

**Priority:** Critical

**Test Case:** Navigate to `/characters/new/wizard`, complete Foundation step with species "Human" and attribute distribution, verify species trait is auto-applied and attributes are within valid range (7-12).

---

### 2. Character Creation - Specialization Step

**Title:** As a Player, I want to define my character's Specialization so that I can establish department ratings and select talents.

**Acceptance Criteria:**
- **Given** I have completed the Foundation step
- **When** I am on the "Specialization" step (step 2)
- **Then** I can assign Department Ratings (Command, Conn, Engineering, Medicine, Science, Security) within range 1-5
- **And** I can distribute 15 points across departments
- **And** I can select 3-4 Focuses relevant to my departments
- **And** I can select Talents from available pool filtered by prerequisites
- **And** I cannot proceed without at least 1 department rating

**Priority:** Critical

**Test Case:** Complete Foundation, navigate to Specialization, assign ratings to Command (3), Science (4), Engineering (2), select relevant Focuses, verify total points do not exceed 15.

---

### 3. Character Creation - Identity Step

**Title:** As a Player, I want to define my character's Identity so that I can create Values that drive story and mechanics.

**Acceptance Criteria:**
- **Given** I have completed the Specialization step
- **When** I am on the "Identity" step (step 3)
- **Then** I must define at least 2 Values with name and description
- **And** I can optionally add Directives (mission statements)
- **And** each Value must be tagged as "Helpful" or "Problematic"
- **And** I cannot proceed without at least 2 Values defined
- **And** my Determination starts at 1 (per rules)

**Priority:** Critical

**Test Case:** Complete Foundation and Specialization, navigate to Identity, create 2 Values ("Logic Above All" and "Protect the Crew"), verify Validation prevents proceeding with only 1 Value.

---

### 4. Character Creation - Equipment Step

**Title:** As a Player, I want to equip my character so that I can assign items, weapons, and rank.

**Acceptance Criteria:**
- **Given** I have completed the Identity step
- **When** I am on the "Equipment" step (step 4)
- **Then** I can add Personal Items from an inventory list
- **And** I can select Weapons (if Security focus)
- **And** I can assign a Starting Rank
- **And** my Stress maximum is auto-calculated as my Fitness attribute
- **And** I can submit the completed character

**Priority:** Critical

**Test Case:** Complete previous steps, navigate to Equipment, add personal items and rank, submit character, verify character appears in `/characters/{id}/sheet` with correct Stress max.

---

### 5. Dice Rolling for Task Resolution

**Title:** As a Player, I want to roll dice for task resolution so that I can resolve uncertain outcomes in the game.

**Acceptance Criteria:**
- **Given** I am in an active encounter at `/encounters/{id}/dice`
- **When** I select an Attribute (e.g., Control, Daring, Fitness, Insight, Presence, Reason)
- **And** I select a Department (e.g., Command, Conn, Engineering, Medicine, Science, Security)
- **Then** the Target Number is auto-calculated as: Attribute + Department
- **And** I can optionally toggle Focus (if my character has applicable focus)
- **And** I can see the current Difficulty (base 1, modified by Scene Traits)
- **And** when I click "Roll", I see individual dice results displayed (e.g., [4, 19, 12])
- **And** successes are calculated: roll <= Target = 1 success, roll = 1 = 2 successes (critical), roll <= Focus value = 2 successes
- **And** complications are shown based on Complication Range

**Priority:** Critical

**Test Case:** In dice roll interface, select Control (8) + Command (3) = Target 11, roll [1, 5, 20], verify: 2 successes from roll=1, 1 success from roll=5, 1 complication from roll=20 (complication range 1).

---

### 6. Managing Values - Marking Used

**Title:** As a Player, I want to mark a Value as Used so that I can invoke it once per session to spend Determination.

**Acceptance Criteria:**
- **Given** I am on my character sheet at `/characters/{id}/sheet`
- **When** I view my Values panel
- **And** a Value shows status "Available"
- **And** I click "Mark Used" for that Value
- **Then** the Value status changes to "Used"
- **And** I can spend Determination for re-rolls (Moment of Inspiration) or set die to 1 (Perfect Opportunity)
- **And** the Value cannot be Used again until the next session (reset)
- **And** the interaction is logged in the Personal Log

**Priority:** Critical

**Test Case:** On character sheet, view Values, click "Mark Used" on "Logic Above All", verify status changes to "Used", verify API endpoint `/api/characters/{id}/value-interaction` records the change.

---

### 7. Managing Values - Marking Challenged

**Title:** As a Player, I want to mark a Value as Challenged so that I can gain 1 Determination when it conflicts with immediate goals.

**Acceptance Criteria:**
- **Given** I am on my character sheet at `/characters/{id}/sheet`
- **When** I click "Mark Challenged" on an Available Value
- **Then** a modal appears for description: "Why is this Value being challenged?"
- **And** after submitting, the Value status changes to "Challenged"
- **And** my Determination increases by 1 (up to max 3)
- **And** an entry is created in Mission Logs with timestamp and description

**Priority:** High

**Test Case:** Character has Determination 1/3, click "Mark Challenged" on "Protect the Crew", enter description "I must break protocol to save them", verify Determination increases to 2/3.

---

### 8. Managing Values - Marking Complied

**Title:** As a Player, I want to mark a Value as Complied so that I can gain 1 Determination when it aligns with goals but hinders progress.

**Acceptance Criteria:**
- **Given** I am on my character sheet at `/characters/{id}/sheet`
- **When** I click "Mark Complied" on an Available Value
- **Then** a modal appears for description: "Why is this Value being complied with?"
- **And** after submitting, the Value status changes to "Complied"
- **And** my Determination increases by 1 (up to max 3)
- **And** an entry is created in Mission Logs

**Priority:** High

**Test Case:** Character has Determination 2/3, click "Mark Complied" on "Follow Orders", enter description "Following captain's orders even though I disagree", verify Determination increases to 3/3.

---

### 9. Viewing Stress Track

**Title:** As a Player, I want to view my Stress track so that I can monitor my character's condition.

**Acceptance Criteria:**
- **Given** I am on my character sheet at `/characters/{id}/sheet`
- **When** I view the Stress display
- **Then** I see a visual progress bar from 0 to max (max = Fitness attribute)
- **And** I see color coding: Green (safe), Yellow (half), Red (near max)
- **And** I see current/max display: e.g., "Stress: 3/8"
- **And** I can optionally click to "Suffer Stress" as alternative to consequences

**Priority:** High

**Test Case:** Character has Fitness 8, view Stress display on character sheet, verify bar shows 0/8 with green color, then suffer 3 stress and verify display shows 3/8 with appropriate color.

---

### 10. Viewing Determination

**Title:** As a Player, I want to view my Determination so that I know how many points I have available to spend.

**Acceptance Criteria:**
- **Given** I am on my character sheet at `/characters/{id}/sheet`
- **When** I view the Determination display
- **Then** I see my current Determination (starts at 1, max 3)
- **And** I see distinct visuals for each point
- **And** spent points are clearly indicated

**Priority:** High

**Test Case:** New character, verify Determination shows 1/3 (1 filled, 2 empty), spend 1 for re-roll, verify display shows 0/3 (all empty).

---

### 11. Viewing and Participating in Scenes

**Title:** As a Player, I want to view and participate in active scenes so that I can engage with the current gameplay.

**Acceptance Criteria:**
- **Given** I am logged into a campaign at `/player/home`
- **When** a scene is active in my campaign
- **Then** I can see the scene listed on my dashboard
- **And** I can navigate to `/scenes/{id}` to view the scene
- **And** I can see the scene description and objectives
- **And** I can see other participants in the scene
- **And** I can interact with the scene (roll dice, etc.)

**Priority:** Critical

**Test Case:** GM activates scene, player logs in, views scene at `/scenes/{id}`, verifies scene description, participants list, and dice roll access.

---

### 12. Reading Other Players' Personal Logs

**Title:** As a Player, I want to read other players' Personal Logs so that I can understand their character's perspective and backstory.

**Acceptance Criteria:**
- **Given** I am on a character sheet at `/characters/{id}/sheet`
- **When** I view the Personal Logs tab
- **Then** I can read all Personal Logs from other players in the same campaign
- **And** I can see entries I have created myself
- **But** I cannot see my own Personal Logs (to maintain mystery for roleplay)
- **And** logs are displayed with timestamp and player attribution

**Priority:** Medium

**Test Case:** Player A creates Personal Log entry, Player B navigates to Player A's character sheet, verifies Personal Logs tab is visible and entry is readable. Player A cannot see their own Personal Logs on their sheet.

---

## GM User Stories

### 13. Creating Campaigns

**Title:** As a GM, I want to create campaigns so that I can organize my STA 2E games.

**Acceptance Criteria:**
- **Given** I am logged in as GM at `/gm`
- **When** I navigate to `/campaigns/new`
- **Then** I can enter campaign name and description
- **And** I can set initial Threat pool (default 24)
- **And** I can set initial Momentum (default 0)
- **And** I can save the campaign
- **And** the campaign appears in my GM dashboard

**Priority:** Critical

**Test Case:** GM navigates to `/campaigns/new`, creates campaign "Deep Space Exploration", saves, verifies campaign appears at `/campaigns/{id}` with correct Threat/Momentum values.

---

### 14. Creating Scenes

**Title:** As a GM, I want to create scenes so that I can organize gameplay into manageable segments.

**Acceptance Criteria:**
- **Given** I am viewing a campaign at `/campaigns/{id}`
- **When** I create a new scene
- **Then** I can enter scene name and description
- **And** I can add Situation Traits (e.g., "Dark Environment", "Hostile Territory")
- **And** I can add participants (PCs and NPCs from Universe Library)
- **And** I can configure encounter settings (Difficulty, Complication Range)
- **And** the scene is saved as Draft status

**Priority:** Critical

**Test Case:** In campaign, create scene "Kobayashi Maru Test", add 2 player characters, 1 NPC antagonist, set Trait "No-Win Scenario" (+1 Complication), verify scene saved with correct configuration.

---

### 15. Activating Scenes

**Title:** As a GM, I want to activate scenes so that players can participate in the current gameplay.

**Acceptance Criteria:**
- **Given** I have a scene in Draft status at `/scenes/{id}/edit`
- **When** I click "Activate Scene"
- **Then** the scene status changes to "Active"
- **And** the scene appears on player dashboards at `/player/home`
- **And** players can navigate to `/scenes/{id}` to participate
- **And** an encounter is automatically derived from the scene configuration
- **And** Mission Logs auto-generate scene entry for all participants

**Priority:** Critical

**Test Case:** Scene in Draft, click "Activate", verify status changes to "Active", log in as player, verify scene appears on player dashboard, verify log entry created.

---

### 16. Managing Threat - Spending

**Title:** As a GM, I want to spend Threat so that I can introduce complications and control game tension.

**Acceptance Criteria:**
- **Given** I am at the GM Console `/campaigns/{id}/gm-console`
- **When** I view the Threat panel
- **Then** I see the current Threat pool (campaign-wide, max 24)
- **And** I can spend Threat with buttons showing cost:
  - Apply Trait: 1-3 Threat
  - Reinforce Scene: 1-2 Threat (Minor/Notable NPCs)
  - Introduce Hazard: 2 Threat
  - Reversal: 2 Threat
  - NPC Complications: 2 Threat
  - Extended Task Progress: 1 Threat
- **And** after spending, the Threat pool decreases
- **And** the action is logged

**Priority:** Critical

**Test Case:** GM Console shows Threat 15/24, click "Introduce Hazard" (cost 2), verify Threat decreases to 13/24, verify event logged in GM console.

---

### 17. Managing Threat - Claiming Momentum

**Title:** As a GM, I want to claim Momentum as Threat so that I can convert player successes into GM resources.

**Acceptance Criteria:**
- **Given** I am at the GM Console with Momentum > 0
- **When** I click "Claim Momentum"
- **Then** 2 Momentum is converted to 1 Threat
- **And** Momentum decreases by 2
- **And** Threat increases by 1
- **And** this is logged as a GM action

**Priority:** High

**Test Case:** GM Console shows Momentum 4, Threat 10, click "Claim Momentum", verify Momentum becomes 2, Threat becomes 11.

---

### 18. Running Encounters

**Title:** As a GM, I want to run encounters so that I can manage combat and challenge resolution.

**Acceptance Criteria:**
- **Given** I am viewing an encounter at `/encounters/{id}`
- **When** I access the GM combat view `/encounters/{id}/combat`
- **Then** I can see all participants (PCs and NPCs)
- **And** I can manage initiative/turn order
- **And** I can resolve NPC actions
- **And** I can track damage, stress, and conditions
- **And** I can view the viewscreen at `/encounters/{id}/view` for shared display

**Priority:** Critical

**Test Case:** In GM combat view, see 3 player characters and 2 NPCs, resolve NPC attacks, track damage on NPCs, verify changes reflected in player views.

---

### 19. Adding Traits to Modify Difficulty

**Title:** As a GM, I want to add Traits to scenes so that I can modify task difficulty and complication ranges.

**Acceptance Criteria:**
- **Given** I am editing a scene at `/scenes/{id}/edit`
- **When** I access the Trait editor via `/encounters/{id}/traits`
- **Then** I can add Traits that modify Difficulty or Complication Range
- **And** I can select from common presets or create custom Traits
- **And** Traits are displayed on the GM Console and affect player dice rolls
- **And** removing a Trait removes its effect

**Priority:** High

**Test Case:** Scene has base difficulty 1, add Trait "Dimensional Instability" (+2 Difficulty), player rolls with displayed difficulty 3, verify Trait affects dice roll interface.

---

### 20. Round Tracking

**Title:** As a GM, I want to track rounds so that I can manage the flow of encounters without fixed turn order.

**Acceptance Criteria:**
- **Given** I am in an encounter at `/encounters/{id}/rounds`
- **When** I view the round tracker
- **Then** I see the current Round number
- **And** I see all participants with "Ready" or "Action Taken" status
- **And** I can click to toggle a participant's action status
- **And** I can click "Start New Round" to reset all participants to "Ready"
- **And** participants are grouped by side (Players vs. NPCs)

**Priority:** High

**Test Case:** Round 1, all participants "Ready", GM toggles 2 PCs and 1 NPC to "Action Taken", clicks "Start New Round", verify Round becomes 2, all participants reset to "Ready".

---

### 21. Viewing Player Resource Status

**Title:** As a GM, I want to view all players' resource status so that I can make informed decisions about Threat spending.

**Acceptance Criteria:**
- **Given** I am at the GM Console `/campaigns/{id}/gm-console`
- **When** I view the Active Players panel
- **Then** I see all player characters in the scene
- **And** each shows current Stress, Determination status
- **And** each shows Value status icons:
  - Available (green check)
  - Used (orange, this session)
  - Challenged (diamond, gained Determination)
  - Complied (blue diamond, gained Determination)
- **And** the panel updates in real-time

**Priority:** High

**Test Case:** 2 players, Player 1 has used Value A, Player 2 has Determination 3/3 and Value B challenged, verify GM Console shows correct status for both.

---

### 22. Scene Viewscreen

**Title:** As a GM, I want to display scene information on a viewscreen so that all players can see the current situation.

**Acceptance Criteria:**
- **Given** I am managing a scene at `/scenes/{id}/gm`
- **When** I want to share scene information
- **Then** I can display `/scenes/{id}/view` on a shared screen
- **And** players see the scene description and objectives
- **And** players see current situation Traits
- **But** players do not see GM-only information

**Priority:** Medium

**Test Case:** Scene active with description "Kobayashi Maru Test" and Trait "No-Win Scenario", display viewscreen, verify players see description and Trait but not GM controls.

---

## Summary Table

| ID | Role | Story | Priority |
|----|------|-------|----------|
| P1 | Player | Character Creation - Foundation | Critical |
| P2 | Player | Character Creation - Specialization | Critical |
| P3 | Player | Character Creation - Identity | Critical |
| P4 | Player | Character Creation - Equipment | Critical |
| P5 | Player | Dice Rolling for Task Resolution | Critical |
| P6 | Player | Managing Values - Marking Used | Critical |
| P7 | Player | Managing Values - Marking Challenged | High |
| P8 | Player | Managing Values - Marking Complied | High |
| P9 | Player | Viewing Stress Track | High |
| P10 | Player | Viewing Determination | High |
| P11 | Player | Viewing and Participating in Scenes | Critical |
| P12 | Player | Reading Other Players' Personal Logs | Medium |
| GM1 | GM | Creating Campaigns | Critical |
| GM2 | GM | Creating Scenes | Critical |
| GM3 | GM | Activating Scenes | Critical |
| GM4 | GM | Managing Threat - Spending | Critical |
| GM5 | GM | Managing Threat - Claiming Momentum | High |
| GM6 | GM | Running Encounters | Critical |
| GM7 | GM | Adding Traits to Modify Difficulty | High |
| GM8 | GM | Round Tracking | High |
| GM9 | GM | Viewing Player Resource Status | High |
| GM10 | GM | Scene Viewscreen | Medium |

---

## Routes Reference

### Player Routes
- `/characters/new/wizard` - Character creation wizard
- `/characters/{id}/sheet` - Character sheet with Values, Stress, Determination
- `/encounters/{id}/dice` - Dice roll interface
- `/scenes/{id}` - Player scene view
- `/player/home` - Player dashboard

### GM Routes
- `/gm` - GM dashboard
- `/campaigns/new` - Create campaign
- `/campaigns/{id}` - Campaign management
- `/campaigns/{id}/gm-console` - Threat panel, resource tracking
- `/scenes/{id}/edit` - Edit scene
- `/scenes/{id}/gm` - GM scene view
- `/encounters/{id}/traits` - Manage scene Traits
- `/encounters/{id}/rounds` - Round tracker
- `/encounters/{id}/combat` - GM combat view

### API Endpoints
- `POST /api/characters/{id}/roll` - Dice roll
- `POST /api/characters/{id}/value-interaction` - Use/Challenge/Comply Value
- `POST /api/characters/{id}/spend-determination` - Spend Determination
- `POST /api/campaigns/{id}/threat/spend` - Spend Threat
- `POST /api/campaigns/{id}/threat/claim` - Claim Momentum to Threat
- `POST /api/scenes/{id}/activate` - Activate scene
- `GET/PUT /api/scenes/{id}/traits` - Get/Update scene Traits

---

## Game Rules Reference

### Dice Mechanics (STA 2E Ch 5)
- Target Number = Attribute + Discipline
- Roll <= Target = 1 Success
- Roll = 1 = 2 Successes (Critical)
- Roll <= Focus value = 2 Successes
- Complications on rolls >= (21 - Complication Range)

### Player Resources (STA 2E Ch 7)
| Resource | Max | Start | Reset |
|----------|-----|-------|-------|
| Stress | Fitness | Fitness | Between scenes |
| Determination | 3 | 1 | Each mission |
| Momentum | 6 | 0 | Between sessions |

### Value Mechanics (STA 2E Ch 4)
- Used: Once per session, allows Determination spend
- Challenged: Gain 1 Determination (Value conflicts with goals)
- Complied: Gain 1 Determination (Value aligns but hinders progress)
- Minimum 2 Values required per character

### Threat (STA 2E Ch 9)
- Campaign-wide pool, max 24
- Claim Momentum: 2 Momentum = 1 Threat
- Various spends: Traits (1-3), Hazards (2), Reversals (2)
