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
	- [ ] command
		- [ ] Direct (spend 1 Momentum, ally takes major action, assist with Control + Command)
		- [ ] Rally (Presence + Command, Difficulty 0, generate Momentum)
	- [ ] engineering
		- [ ] Damage Control (Presence + Engineering, Difficulty 2 + potency, patch breach)
		- [ ] Regain Power (Control + Engineering, Difficulty 1+, restore Reserve Power)
		- [ ] Regenerate Shields (requires Reserve Power, Control + Engineering, regain shields)
		- [ ] Reroute Power (requires Reserve Power, boost next action using that system)
	- [ ] conn/helm
		- [ ] Impulse (minor - move up to 2 zones)
		- [ ] Thrusters (minor - move within current zone, can dock/land)
		- [ ] Attack Pattern (assist all ship attacks, but attacks against ship get -1 Difficulty)
		- [ ] Evasive Action (attacks vs ship are opposed, ship's attacks +1 Difficulty)
		- [ ] Maneuver (Control + Conn, generate Momentum for difficult terrain)
		- [ ] Ram (Daring + Conn, Difficulty 2, collision damage)
		- [ ] Warp (requires Reserve Power + Prepare, move zones = Engines or leave battlefield)
	- [ ] tactical
		- [x] Fire (attack with weapon - DONE)
		- [ ] Calibrate Weapons (minor - next attack damage +1)
		- [ ] Prepare (minor - raise/lower shields, arm/disarm weapons)
		- [ ] Targeting Solution (minor - next attack can re-roll or choose system hit)
		- [ ] Defensive Fire (opposed roll, spend 2 Momentum to counterattack)
		- [ ] Modulate Shields (Resistance +2 until next turn)
		- [ ] Tractor Beam (Control + Security, immobilize target at Close range)
	- [ ] science/sensors
		- [ ] Calibrate Sensors (minor - next sensor action ignores trait or re-rolls 1d20)
		- [ ] Launch Probe (minor - launch to Long range for remote sensing)
		- [ ] Reveal (Reason + Science, Difficulty 3, reveal cloaked vessel)
		- [ ] Scan For Weakness (Control + Science, Difficulty 2, next attack +2 damage or Piercing)
		- [ ] Sensor Sweep (Reason + Science, Difficulty 1, get info on zone)
- [ ] Switch to game master to fire back at the player ship
- [ ] Move ships and keep track of relative positions
- [ ] only let people use extra dice based on actual momentum they have (according to buying rules)
- [ ] allow players to use full momentum spend action table


# Beta Release (NOT STARTED)
This release brings in multiple players, as well as a console for the game master and a viewscreen for all players.

## Feature List

- [ ] let game master create starships for encounters
	- [ ] random starship
	- [ ] bespoke starship
- [ ] main viewscreen
	- [ ] shows momentum / threat
	- [ ] shows a map of enemy ships
	- [ ] shows ship's shields and any breaches
- [ ] turn management
	- [ ] prevent players from taking a turn until it's their turn
	- [ ] show whose turn it is
		- [ ] player screens
		- [ ] view screen
	- [ ] gamemaster can see whose turn it is


# Version 1.0 (NOT STARTED)
- [ ] LCARS styling (all sections)
- [ ] finalize lesser important stations
	- [ ] medical
	- [ ] operations