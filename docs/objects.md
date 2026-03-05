# Objects

This is to document some object properties and relations for the new VTT experience approach.

## Chars
Have all the character properties that are shared between PCs and NPCs.

### Generic Char Properties
- Stress Track
- List of Images
- Description
- Tuple of Attributes (Control, Daring, Fitness, Insight, Presence, Reason)
- Tuple of Departments (Command, Conn, Engineering, Medicine, Science, Security)
- List of Traits (Category: Character)
  - Mandatory: Species Trait
  - State: [Ok, Defeated, Fatigued, Dead]
- Species String
- List of Talents
- Role String
- --> "Attacks" (representing different weapons but impact is char-specific)
- --> "Equipment"

### NPCs
Have all the generic Char Properties.
- NPC Category [Major|Notable|Minor]
- Personal Threat Pool [0-24]
- Location String
- NPC Background (all optional, some with drop-downs)
  - Archetype
  - Upbringing
  - Environment
  - Cultural Traits
  - Goals
  - Tactics
  - Federation Outlook / Affiliation
  - Life-Form Origin & Structure Traits
    - Life-Form Origins (Carbon-Based Type, Exotic-Based Type, Incorporeal Type, ...)
    - Body Structure Symmetry (Bilateral, Spherical, Biradial, Trilateral, Radial, Asymmetrical, ...)
    - Beast/Creature Traits
      - Size
      - Vertebrate or Invertebrate Class
      - Structural Adaptation
      - Behavioral Adaptation
      - Preferred Environment
    - Spaceborne Entity Traits
      - Mental Capacity/Awareness
      - Metabolic Energy Type
      - Morphology
      - Spaceborne Entity Preferred Environment

### PCs
As described in Chapter 04.
Include a section for
- Personal Logs (tracking value usage),
- Mission Logs (fluff text provided by players)
- Scene Logs (who was part of which scene)
- Character Background texts, managable by players
- category Main vs Side (different rules apply)

## Trait
- Category: [Character, Location, Situation, Equipment]
- Name: String
- Description: String
- Potency: Positive Integer (standard: 1)

## Talent
- Player Selectable: Boolean
- Category: [Talent, Special Rule, Species Ability]
- List of Conditions: (Logic for when the talent is active)
- Description Text
- Game Mechanic: (Reference to automated logic/handler)

## Ships
Represent both Player and NPC vessels.
- Name String
- Ship Class / Frame
- --> "Mission Profile"
- Scale [1-7]
- Resistance
- Systems (Comms, Computers, Engines, Sensors, Structure, Weapons)
- Departments (Command, Conn, Engineering, Medicine, Science, Security)
- Power (Current/Max) --> Replace with "Reserve Power"
- Shields (Current/Max)
- Crew Quality [2-5] --> Only for NPC ships
- Traits (List of Traits, category: Equipment/Location)
- Talents (List of Ship Talents)
- Weapons (List of Weapon Objects)

## Scenes
The active room where gameplay happens.
- Name String
- Description Text
- Status [Active|Archived|Connected]
- Resource Pools:
  - Momentum [0-6]
  - Threat [GM Pool]
- Participants: --> Divide between player and non-player
  - List of Chars (Link to Universe/Campaign Library)
  - List of Ships
- Situation Traits
- Turn Order (Initiative Track)
- Logs (Action & Narrative history)

## Items / Equipment
- Name
- Description
- Traits (category: Equipment)
- Opportunity/Cost
- Effects (Game Mechanics)

## Extended Tasks
- Name
- Work (Track)
- Difficulty
- Magnitude
- Resistance


# Clarifying Questions

- Ship Shields: Should we maintain the quadrant-based shield tracks (Forward, Aft, Port, Starboard) from the current simulator, or is a simplified "Shield Health" value preferred for the VTT's broader scope? --> Use simplified shields, as introduced in the rules. We'll cover that with the ship properties.

- Momentum Scope: Is Momentum globally shared across all scenes in a Campaign (as per the standard STA 2e rules), or do you want it tracked per Scene? --> Momentum and Threat are campaign properties, but there should be a way to reset Momentum (by the beginning of a new game session that is not represented in the programming) and automated reduction of Momentum when transitioning between scenes.

- Connected Scenes: Does a "Connected" status imply a specific UI/logic (like a deck plan or map) for movement, or is it just a narrative flag for the GM? --> A connection between scenes should be represented in the following way: when the GM presses a button to end a scene, there is a dialogue for them that allows selecting a connected scene (that has not been ended), a ad-hoc creation of a new scene, or return to the GM overview, where they can select any other pregenerated scene or an already ended scene to be activated again.

- Extended Tasks: Should these be independent objects in a Scene, or are they always attached to a specific Char, Ship, or Situation Trait? --> they are independent objects within a scene.

- Traits/Talents Logic: You mentioned "Game Mechanic???" in the Talent diagram. For this initial data model, should these be purely descriptive (text only), or should they include a reference/ID to a functional code handler (similar to the current action_config.py system)? --> prepare a reference to a code handler, but this will only come in a late milestone.
