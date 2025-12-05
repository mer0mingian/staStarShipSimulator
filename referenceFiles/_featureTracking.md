# Feature Tracking

Hey Claude, Gemini or Codex! This file keep track of features we want to add. 

# Alpha Release (IN PROGRESS)
The purpose of the alpha release is to test out the core mechanics for firing and keeping track of damage to ships and stuff.

## Feature List

- [x] Allow players to fire on a ship and for the ships to reflect damage
	- [x] make sure complication rolls reduce damage
	- [x] make sure resistance is factored in in damage calculations
	- [x] get breaches working right!
		- [x] make sure warp core breaches are working
- [ ] finalize core stations (mechanics for each action type, making sure ship states are affected)
	- [ ] tactical (PRIORITY)
		- [x] Fire (attack with weapon - DONE)
		- [x] Calibrate Weapons (minor - next attack damage +1)
		- [x] Prepare (minor - raise/lower shields, arm/disarm weapons)
		- [x] Targeting Solution (minor - next attack can re-roll or choose system hit)
			- [x] BUG: does not actually let the player re-roll any die
		- [RFT] Defensive Fire (opposed roll, spend 2 Momentum to counterattack)
			- [x] Player activates with energy weapon selection (like Fire)
			- [x] Creates ActiveEffect with `duration: "next_turn"`, stores weapon index
			- [x] Cannot combine with Evasive Action (mutual exclusion)
			- [x] When enemy attacks (GM triggers), check for Defensive Fire effect
			- [x] If active: Opposed roll (Daring + Security, assisted by Weapons + Security)
			- [x] If defender wins: Attack misses, offer 2 Momentum counterattack option
		- [x] Modulate Shields (task roll - Resistance +2 until next turn)
			- [x] BUG: resistance did not take effect
			- [x] tweak: should be a difficulty of 1
		- [ ] Tractor Beam (Control + Security, immobilize target at Close range)
	- [ ] engineering
		- [RFT] Damage Control (Presence + Engineering, Difficulty 2 + potency, patch breach)
		- [RFT] Regain Power (Control + Engineering, Difficulty 1+, restore Reserve Power)
		- [RFT] Regenerate Shields (requires Reserve Power, Control + Engineering, regain shields)
		- [ ] Reroute Power (requires Reserve Power, boost next action using that system)
	- [ ] conn/helm
		- [ ] Impulse (minor - move up to 2 zones)
		- [ ] Thrusters (minor - move within current zone, can dock/land)
		- [RFT] Attack Pattern (buff - assist all ship attacks, but attacks against ship get -1 Difficulty)
		- [RFT] Evasive Action (buff - attacks vs ship are opposed, ship's attacks +1 Difficulty)
		- [RFT] Maneuver (Control + Conn, generate Momentum for difficult terrain)
		- [ ] Ram (Daring + Conn, Difficulty 2, collision damage)
		- [ ] Warp (requires Reserve Power + Prepare, move zones = Engines or leave battlefield)
	- [ ] science/sensors
		- [RFT] Calibrate Sensors (minor - next sensor action ignores trait or re-rolls 1d20)
		- [ ] Launch Probe (minor - launch to Long range for remote sensing)
		- [ ] Reveal (Reason + Science, Difficulty 3, reveal cloaked vessel)
		- [RFT] Scan For Weakness (Control + Science, Difficulty 2, next attack +2 damage or Piercing)
		- [RFT] Sensor Sweep (Reason + Science, Difficulty 1, get info on zone)
- [RFT] **GM/Player Screen Separation (PRIORITY - unblocks Defensive Fire, Evasive Action, etc.)**
	- [RFT] Create separate Player interface (current combat.html, but player-focused)
		- [RFT] Player can only act on their turn
		- [RFT] Shows player's available actions based on their station
	- [RFT] Create Game Master interface
		- [RFT] GM can trigger enemy ship attacks against player ship
		- [RFT] GM can see all ships, momentum, threat
		- [RFT] GM controls when turns advance
	- [RFT] Enemy attack resolution
		- [x] GM selects attacking enemy ship and weapon
		- [x] System checks for Defensive Fire / Evasive Action effects
		- [x] If defensive effect active: Run opposed roll, show results
		- [x] If defender wins opposed roll: Offer counterattack option (2 Momentum)
		- [x] If attacker wins or no defensive effect: Normal damage resolution
	- [RFT] Turn management
		- [RFT] Prevent players from acting when not their turn
		- [RFT] Show whose turn it is on all screens
		- [RFT] GM can advance turns
- [ ] Move ships and keep track of relative positions
- [ ] only let people use extra dice based on actual momentum they have (according to buying rules)
- [ ] allow players to use full momentum spend action table


# Beta Release (NOT STARTED)
This release brings in multiple players, as well as a console for the game master and a viewscreen for all players.

## Feature List

- [ ] **GM Rollable Actions (PRIORITY)**
	- [x] Add Crew Quality system to NPC ships
		- [x] Add `crew_quality` field to Starship model (Basic/Proficient/Talented/Exceptional)
		- [x] Crew Quality provides Attribute + Department for all NPC rolls:
			- Basic: Attribute 8, Department 1
			- Proficient: Attribute 9, Department 2
			- Talented: Attribute 10, Department 3
			- Exceptional: Attribute 11, Department 4
		- [x] NPC crew always have applicable Focus (crits on 1s AND 2s)
		- [x] Update ship creation UI to set crew quality
		- [x] Default new enemy ships to "Talented" (existing ships handle NULL gracefully)
	- [x] GM Action Panel (when NPC turn)
		- [x] GM selects which enemy ship is acting
		- [x] Show available NPC actions (filtered list - see below)
		- [x] Roll uses: Crew Quality Attribute + Crew Quality Department
		- [x] Ship assists with: Ship System + Ship Department (TODO: add ship assist die)
		- [x] Dice panel works same as player
	- [x] NPC-Available Actions (NPCs do NOT have Reserve Power!)
		- [x] **Attack**: Fire (use existing GM attack button)
		- [x] **Tactical Buffs**: Calibrate Weapons, Targeting Solution
		- [x] **Defense**: Modulate Shields, Evasive Action (Defensive Fire TODO)
		- [x] **Toggles**: Raise/Lower Shields, Arm/Disarm Weapons
		- [x] **Conn**: Attack Pattern, Maneuver (Ram TODO)
		- [x] **Engineering**: Damage Control (only - no power actions!)
		- [x] **Science**: Scan For Weakness, Sensor Sweep, Calibrate Sensors
		- [ ] **Utility**: Tractor Beam (TODO)
	- [x] Actions NPCs CANNOT use (per rules):
		- Assist, Direct, Rally (require individual crew)
		- Regain Power, Regenerate Shields, Reroute Power, Warp (require Reserve Power)
	- [ ] Same-System Tracking (defer to later)
		- [ ] Track which systems each NPC ship has used this round
		- [ ] 2nd/3rd use of same system costs 1 Threat each
- [ ] **Turn System Overhaul**
	- [ ] Replace binary "player/enemy turn" with individual turn tracking
	- [ ] Turn economy per round:
		- Player side: 1 turn per active bridge officer
		- NPC side: 1 turn per point of Scale per enemy ship (Scale 5 = 5 turns!)
	- [ ] Turns alternate: Player → NPC → Player → NPC...
	- [ ] Track turns remaining for each side in current round
	- [ ] GM selects which NPC ship acts on each NPC turn
	- [ ] UI updates:
		- [ ] Show "Turn X of Y" for current side
		- [ ] Show which ships/characters have acted this round
		- [ ] Auto-advance to next side when all turns used
- [ ] **Keep the Initiative** (defer to later)
	- [ ] After any turn, option to Keep the Initiative
	- [ ] Players: costs 2 Momentum, select which player goes next
	- [ ] GM/NPCs: costs 2 Threat, select which NPC ship goes next
	- [ ] Cannot Keep Initiative twice in a row on same side
	- [ ] Talents that modify Keep the Initiative cost (Quick to Action, etc.)
- [ ] command station
	- [ ] Direct (spend 1 Momentum, ally takes major action, assist with Control + Command)
	- [ ] Rally (Presence + Command, Difficulty 0, generate Momentum)
- [ ] let game master create starships for encounters
	- [ ] random starship
	- [ ] bespoke starship
- [ ] main viewscreen
	- [ ] shows momentum / threat
	- [ ] shows a map of enemy ships
	- [ ] shows ship's shields and any breaches
- [ ] multiple player support
	- [ ] each player has their own screen/station
	- [ ] players can only see their own actions


# Version 1.0 (NOT STARTED)
- [ ] LCARS styling (all sections)
- [ ] finalize lesser important stations
	- [ ] medical
	- [ ] operations