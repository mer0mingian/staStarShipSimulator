1: # Objects
2: 
3: This is to document some object properties and relations for the new VTT experience approach.
4: 
5: ## Chars
6: Have all the character properties that are shared between PCs and NPCs.
7: 
8: ### Generic Char Properties
9: - Stress Track (Max value, PC-specific)
10: - List of Images
11: - Description
12: - Tuple of Attributes (Control, Daring, Fitness, Insight, Presence, Reason)
13: - Tuple of Departments (Command, Conn, Engineering, Medicine, Science, Security)
14: - List of Traits (Category: Character)
15:   - Mandatory: Species Trait
16:   - State: [Ok, Defeated, Fatigued, Dead]
17: - Species String
18: - List of Talents
19: - Role String
20: - --> "Attacks" (representing different weapons but impact is char-specific)
21: - --> "Equipment"
22: - Max Threat Pool (Capacity for NPCs to avoid consequences)
23: 
24: ### NPCs
25: Have all the generic Char Properties.
26: - NPC Category [Major|Notable|Minor]
27: - Personal Threat Pool [0-24] (Note: This is the active pool; Line 22 is the maximum capacity)
28:   - Minor NPC: 0 Personal Threat; instantly defeated on any Injury; no Stress track
29:   - Notable NPC: 3 Personal Threat; Avoid Injury once per scene (cost = severity); no Stress track
30:   - Major NPC: 6 + 1 per Value Personal Threat; Avoid Injury unlimited per scene (cost = severity); no Stress track
31:   - Supporting Characters: 0 Values → no Stress; 1 Value → max Stress = Fitness ÷ 2 (round up); 2+ Values → max Stress = Fitness
32: - Location String
29: - NPC Background (all optional, some with drop-downs)
30:   - Archetype
31:   - Upbringing
32:   - Environment
33:   - Cultural Traits
34:   - Goals
35:   - Tactics
36:   - Federation Outlook / Affiliation
37:   - Life-Form Origin & Structure Traits
38:     - Life-Form Origins (Carbon-Based Type, Exotic-Based Type, Incorporeal Type, ...)
39:     - Body Structure Symmetry (Bilateral, Spherical, Biradial, Trilateral, Radial, Asymmetrical, ...)
40:     - Beast/Creature Traits
41:       - Size
42:       - Vertebrate or Invertebrate Class
43:       - Structural Adaptation
44:       - Behavioral Adaptation
45:       - Preferred Environment
46:     - Spaceborne Entity Traits
47:       - Mental Capacity/Awareness
48:       - Metabolic Energy Type
49:       - Morphology
50:       - Spaceborne Entity Preferred Environment
51: 
52: ### PCs
53: As described in Chapter 04.
54: Include a section for
55: - Personal Logs (tracking value usage),
56: - Mission Logs (fluff text provided by players)
57: - Scene Logs (who was part of which scene)
58: - Character Background texts, managable by players
59: - category Main vs Side (different rules apply)
60: 
61: ## Trait
62: - Category: [Character, Location, Situation, Equipment]
63: - Name: String
64: - Description: String
65: - Potency: Positive Integer (standard: 1)
66: 
67: ## Talent
68: - Player Selectable: Boolean
69: - Category: [Talent, Special Rule, Species Ability, Role Benefit]
70: - List of Conditions: (Logic for when the talent is active — see `docs/references/talent_system_design.md`)
71: - Description Text
72: - Game Mechanic Reference: Handler ID string (Phase 1) or structured predicate (Phase 2 — see `docs/references/talent_system_design.md`)
73: - Applicable To: [Character, Ship, NPC]
74: - Source: String (e.g., species name, role name)
75: - Mechanically Applies: Boolean (False = GM discretion / flagged for review)
76: - Stress Modifier: Integer | None (for Species Abilities that modify max Stress)
77: 
78: ### Special Rules for NPCs (Ch 11)
79: Special Rules are the same data model as Talent, category = "SpecialRule".
80: Additional field:
81: - Particular Task: String describing the limiting condition (e.g., "Security tasks", "when repairing systems")
82: See `docs/references/talent_system_design.md` Section 4 for implementation details.
83: 
84: ### Role Benefits (Ch 4)
85: Same data model as Talent, category = "RoleBenefit". Auto-granted based on character role selection.
86: 
87: ### Species Abilities (Ch 4)
88: Same data model as Talent, category = "SpeciesAbility". Auto-granted based on species selection.
89: - Species abilities that modify Stress: stored with `stress_modifier` field; flagged for GM review on character creation
90: - GM can override the stress modifier value per-character
91: 
92: ### NPC Special Rule Examples (Ch 11)
93: | Rule | Effect | Handler ID |
94: |------|--------|------------|
95: | PROFICIENCY | First bonus d20 free on particular task | `free_first_d20` |
96: | FAMILIARITY | Reduce Difficulty by 2 (min 0) on particular task | `reduce_difficulty:2` |
97: | GUIDANCE | When assisting, re-roll d20 | `assist_reroll` |
98: | ADDITIONAL THREAT SPENT | Spend 1 Threat for specific benefit | `threat_spend_bonus` |
99: | SUBSTITUTION | Use different department on particular task | `department_swap` |
100: | THREATENING | When buying d20s with Threat, re-roll 1 d20 | `threat_buy_reroll` |
101: 
102: See `docs/references/talent_system_design.md` Section 4.2 for full table.
103: 
104: ## Ships
75: Represent both Player and NPC vessels.
76: - Name String
77: - Ship Class / Frame
78: - --> "Mission Profile"
79: - Scale [1-7]
80: - Resistance (formula: ceil(Scale/2) + Structure bonus; see game_machanics.md)
81: - Systems (Comms, Computers, Engines, Sensors, Structure, Weapons)
82: - Departments (Command, Conn, Engineering, Medicine, Security)
83: - Power (Current/Max) --> Replace with "Reserve Power"
84: - Shields (Current/Max; formula: Structure + Scale + Security)
85: - Crew Quality [Basic|Proficient|Talented|Exceptional] --> Only for NPC ships
    - Basic: Attr 8 Dept 1 | Proficient: Attr 9 Dept 2 | Talented: Attr 10 Dept 3 | Exceptional: Attr 11 Dept 4
    - Use Crew Quality for NPC ship actions unless an NPC is explicitly assigned to a station (use NPC stats)
    - NPC ships: max one task per system per round; extra tasks cost 1 Threat each
86: - Traits (List of Traits, category: Equipment/Location)
87: - Talents (List of Ship Talents)
88: - Weapons (List of Weapon Objects)
89: 
90: ## Scenes
91: The active room where gameplay happens.
92: - Name String
93: - Description Text
94: - Status [Active|Archived|Connected]
95: - Resource Pools:
96:   - Momentum [0-6]
97:   - Threat [GM Pool]
98: - Participants: --> Divide between player and non-player
99:   - List of Chars (Link to Universe/Campaign Library)
100:   - List of Ships
101: - Situation Traits
102: - Turn Order (Initiative Track)
103: - Logs (Action & Narrative history)
104: 
105: ## Items / Equipment
106: - Name
107: - Description
108: - Traits (category: Equipment)
109: - Opportunity/Cost
110: - Effects (Game Mechanics)
111: 
112: ## Extended Tasks
113: - Name
114: - Work (Track)
115: - Difficulty
116: - Magnitude
117: - Resistance
118: 
119: 
120: # Clarifying Questions
121: 
122: - Ship Shields: Should we maintain the quadrant-based shield tracks (Forward, Aft, Port, Starboard) from the current simulator, or is a simplified "Shield Health" value preferred for the VTT's broader scope? --> Use simplified shields, as introduced in the rules. We'll cover that with the ship properties.
123: 
124: - Momentum Scope: Is Momentum globally shared across all scenes in a Campaign (as per the standard STA 2e rules), or do you want it tracked per Scene? --> Momentum and Threat are campaign properties, but there should be a way to reset Momentum (by the beginning of a new game session that is not represented in the programming) and automated reduction of Momentum when transitioning between scenes.
125: 
126: - Connected Scenes: Does a "Connected" status imply a specific UI/logic (like a deck plan or map) for movement, or is it just a narrative flag for the GM? --> A connection between scenes should be represented in the following way: when the GM presses a button to end a scene, there is a dialogue for them that allows selecting a connected scene (that has not been ended), a ad-hoc creation of a new scene, or return to the GM overview, where they can select any other pregenerated scene or an already ended scene to be activated again.
127: 
128: - Extended Tasks: Should these be independent objects in a Scene, or are they always attached to a specific Char, Ship, or Situation Trait? --> they are independent objects within a scene.
129: 
130: - Traits/Talents Logic: You mentioned "Game Mechanic???" in the Talent diagram. For this initial data model, should these be purely descriptive (text only), or should they include a reference/ID to a functional code handler (similar to the current action_config.py system)? --> prepare a reference to a code handler, but this will only come in a late milestone.
131: 
132: (End of file - total 132 lines)