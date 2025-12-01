# Starship Combat Rules Reference

## Core Concepts

Starship combat uses the same action order as personal combat, but applies to **characters** rather than ships. Each character receives a turn to operate their ship.

## Environment & Zones

### Zone System
- Environment divided into zones based on physical objects and spatial phenomena
- Zones can be 3D (above/below) if desired
- Simple battles: 3-5 zones; Complex battles: many more zones
- No fixed size/shape - varies by situation and GM preference

### Range Categories

| Range | Distance | Description |
|-------|----------|-------------|
| **Contact** | Special state | Docking, landing - not a fixed range |
| **Close** | 0 zones | Within current zone |
| **Medium** | 1 zone | Adjacent zones |
| **Long** | 2 zones | Two zones away |
| **Extreme** | 3+ zones | Beyond long range |

## Movement & Terrain

### Movement Types
- **Maneuvering thrusters** - Movement within Close range
- **Impulse engines** - Sublight flight
- **Warp drive** - FTL travel

### Going to Warp

**Requirements:**
1. Reroute Reserve Power to engines
2. Take Prepare minor action (if in combat)
3. Control + Conn task (Difficulty 1), assisted by ship's Engines + Conn

**Success Options:**
- Move zones equal to ship's Engines score, OR
- Leave battlefield entirely (may trigger pursuit)

**Pursuit:** Each pursuing ship must go to warp and score more successes than fleeing ship.

### Terrain Types

#### Difficult Terrain
Requires spending Momentum to leave the zone. If insufficient Momentum, use Maneuver action (Difficulty 0 Control + Conn) to generate more.

| Terrain Type | Momentum Cost |
|--------------|---------------|
| Planetary Gravity Well, Dust Cloud, Debris Field | 1 |
| Stellar Gravity Well, Dense Nebula, Comet Tail | 2 |
| Singularity Gravity Well, Strange Space Anomaly | 3 |

#### Hazardous Terrain
Functions as difficult terrain, but if you add Threat instead of spending Momentum, that Threat is spent immediately to inflict damage or impose traits.

### Zone Effects
Zones may have:
- Concealment or interference
- Movement hindrance
- Hazards
- Altered interaction mechanics

## Actions in Combat

### Minor Actions
- 1 minor action per turn (base)
- Additional minor action costs 1 Momentum (Immediate)
- Specific actions vary by bridge position

### Major Actions
- 1 major action per turn (base)
- Second major action options:
  - **Direct action (Leadership):** Issue order to subordinate
  - **Spend 2 Momentum:** Second major action at +1 Difficulty
- **Maximum:** 2 major actions per round

## Combat Against Large Adversaries

For vessels/stations at Scale 7+:

**GM Options:**
1. Take all NPC turns (e.g., Scale 10 = 10 turns)
2. Match player turns (surplus NPC actions = bonus dice at 1-for-1)
3. Take as many turns as appropriate, narrate remainder

## Communication

Subspace communications are instantaneous within combat range (unless interfered with by nebulae, radiation, etc.).

## Sensors

Ships can scan several light-years in ideal conditions. Detection range and detail increase with proximity.

## Combat Actions

### Standard Minor Actions (All Stations)

| Action | Description |
|--------|-------------|
| **Change Position** | Move to any bridge station or ship location. Take control if unmanned, or when officer departs. Arrive at new location start of next turn |
| **Interact** | Interact with environment object. Complex interactions may require major action |
| **Prepare** | Prepare for or set up a task. Required before some tasks |
| **Restore** | Minor repairs/adjustments to restore system after disruption/minor damage |

### Standard Major Actions (All Stations)

| Action | Description |
|--------|-------------|
| **Assist** | Grant ally advantage. Assist their next task. Can give up turn to assist immediately |
| **Create Trait** | Create/change/remove trait. Difficulty 2 task using attribute + department |
| **Other Tasks** | Perform task at GM discretion. May be extended task or challenge |
| **Override** | Attempt action from another position (not commanding officer). Difficulty +1 |
| **Pass** | Choose not to attempt task |
| **Ready** | Choose major action as reaction to trigger. Interrupt when triggered, or lost if not |

## Command Station Actions

Ship may have second command position (executive officer) if Command 4+. Executive officer cannot contradict commanding officer.

### Command Major Actions

| Action | Description |
|--------|-------------|
| **Assist** | Standard Assist, but can pick two characters instead of one |
| **Create Trait** | Standard Create Trait. Often Control/Insight/Reason + Command for battle plans/strategies |
| **Direct** | Spend 1 Momentum. Select bridge ally who immediately attempts major action. Assist with Control + Command (1d20) |
| **Rally** | Inspire crew. Presence + Command, Difficulty 0, to generate Momentum |

## Communications Station Actions

### Communications Notes
- Opening internal comms (whole ship or specific locations): free action anytime
- Sending/responding to hails: free action
- Other activities (encryption, interception, priority comms): use standard major actions

### Communications Major Actions

| Action | Description |
|--------|-------------|
| **Create Trait** | Often for boosting/recalibrating comms, encryption/decryption, or coordinating personnel/ships |
| **Damage Control** | Direct repair team. Choose breach, Presence + Engineering Difficulty 2 (+1 per Potency). Success: breach patched (not removed) |
| **Transport** | Send instructions to transporter room. Difficulty +1 when operated from bridge |

## Helm Station Actions

May be combined with navigator into conn position.

### Helm Minor Actions

| Action | Description |
|--------|-------------|
| **Impulse** | Use impulse engines. Move up to 2 zones (anywhere within Long range). If move only 1 zone: terrain Momentum cost -1 |
| **Thrusters** | Maneuvering thrusters, fine adjustments. Move anywhere within current zone. May safely move into Contact (docking/landing) |

### Helm Major Actions

| Action | Description |
|--------|-------------|
| **Attack Pattern** | Fly steadily for targeting. Assist each ship attack (Control + Conn) until next turn. Attacks against ship: Difficulty -1 |
| **Create Trait** | Often for careful positioning or skilled maneuvering |
| **Evasive Action** | Unpredictable maneuvering. Attacks vs ship = opposed (Daring + Conn, assisted by Structure + Conn). Win: move 1 zone. Ship's attacks: Difficulty +1. Cannot use with Defensive Fire |
| **Maneuver** | Careful flight control. Control + Conn Difficulty 0, assisted by Engines + Conn. Generate Momentum for difficult terrain |
| **Ram** | Choose enemy at Close range, move into Contact. Attack: Daring + Conn Difficulty 2, assisted by Engines + Conn. Success: inflict collision damage (Intense) on target, suffer target's collision damage |
| **Warp** | Requires Reserve Power and Prepare minor. Control + Conn Difficulty 1, assisted by Engines + Conn. Move zones = Engines score OR leave battlefield |

## Navigator Station Actions

May be combined with helm into conn position. Typically creates traits (plotted courses, charted hazards) or assists helm.

### Navigator Major Actions

| Action | Description |
|--------|-------------|
| **Assist** | Commonly assists helm officer |
| **Create Trait** | Often for plotting courses or studying terrain |

## Operations/Engineering Station Actions

Can be performed from operations or main engineering. Ship may have second position if Engineering 4+.

### Operations/Engineering Major Actions

| Action | Description |
|--------|-------------|
| **Create Trait** | Often for modifications to ship systems |
| **Damage Control** | Choose breach. Presence + Engineering Difficulty 2 (+1 per Potency). Success: breach patched (not removed) |
| **Regain Power** | Control + Engineering Difficulty 1. May Succeed at Cost. Success: restore Reserve Power. Difficulty +1 each attempt per scene |
| **Regenerate Shields** | Requires Reserve Power. Control + Engineering Difficulty 2 (or 3 if shields at 0), assisted by Structure + Engineering. Success: regain shields = Engineering rating, +2 per Momentum (Repeatable) |
| **Reroute Power** | Requires Reserve Power. Reroute to specific system for next action using that system |
| **Transport** | Remotely operate transporters. Difficulty +1 from bridge |

## Sensor Operations Station Actions

Ship may have second position if Science 4+.

### Sensor Operations Minor Actions

| Action | Description |
|--------|-------------|
| **Calibrate Sensors** | Fine-tune sensors. Next Sensor action: ignore one trait OR re-roll 1d20 |
| **Launch Probe** | Launch to any zone within Long range. Sensor actions may use probe's location. Probe destroyed if takes any damage |

### Sensor Operations Major Actions

Difficulty affected by interference, conditions, phenomena. Difficulty +1 per range beyond Close.

| Action | Description |
|--------|-------------|
| **Create Trait** | Often for important detected/discovered information |
| **Reveal** | Scan for cloaked/concealed vessels. Reason + Science Difficulty 3, assisted by Sensors + Science. Success: reveal one hidden vessel's zone within Long range. Attacks vs revealed vessel: Difficulty +2 until it moves |
| **Scan For Weakness** | Choose enemy vessel. Control + Science Difficulty 2, assisted by Sensors + Security. Success: next attack vs that ship: damage +2 OR gains Piercing |
| **Sensor Sweep** | Select zone. Reason + Science Difficulty 1, assisted by Sensors + Science. Success: GM provides basic info on ships/objects/phenomena. Spend Momentum for extra info |

## Tactical Station Actions

Ship may have second position if Security 4+.

### Tactical Minor Actions

| Action | Description |
|--------|-------------|
| **Calibrate Weapons** | Fine-tune energy weapons/torpedo yield. Next attack: damage +1 |
| **Prepare** | Raise/lower shields OR arm/disarm weapons. Lowered shields: max = 0. Raised: restore to max or previous total. Armed weapons required for attacks but detectable |
| **Targeting Solution** | Lock onto enemy within Long range. Next attack vs that vessel: re-roll d20 OR choose which system hit |

### Tactical Major Actions

| Action | Description |
|--------|-------------|
| **Create Trait** | Often for weapon modifications or targeting data |
| **Defensive Fire** | Choose one energy weapon. Attacks vs ship = opposed (Daring + Security, assisted by Weapons + Security). Success: spend 2 Momentum to counterattack with weapon's damage. Cannot use with Evasive Action |
| **Fire** | Select energy or torpedo weapon. Choose target. Make Attack (see Attack Process). Torpedo attacks add 1 Threat |
| **Modulate Shields** | Cannot use if shields at 0. Until next turn: Resistance +2 |
| **Tractor Beam** | Control + Security Difficulty 2, assisted by Structure + Security. Close range only. Success: target immobilized until breaks free (Difficulty = tractor beam strength) |

## Attack Process

### Making a Starship Attack

1. **Select Attack:** Choose weapon type (energy or torpedo). If multiple weapons, choose one
2. **Select Target:** Choose vessel/viable target visible to ship (within weapon range)
3. **Attempt Attack:** Control + Security, assisted by Weapons + Security
   - Energy weapons: Difficulty 2
   - Torpedoes: Difficulty 3
   - Ram: Difficulty 2
4. **Resolve Attack:** If successful, inflict damage. Roll on Random System Hit table (or choose if used Targeting Solution)

### Random System Hit Table

| d20 | System Hit |
|-----|------------|
| 1 | Communications |
| 2 | Computers |
| 3-6 | Engines |
| 7-9 | Sensors |
| 10-17 | Structure |
| 18-20 | Weapons |

### Starship Combat Momentum Spends

| Spend | Cost | Description |
|-------|------|-------------|
| **Added Damage** | 2 Momentum (Repeatable) | Increase attack damage by 1 per 2 Momentum spent |
| **Devastating Attack** | 2 Momentum | Roll additional system. That system suffers hit dealing half attack's damage (round up) |

## Cover and Concealment

**Cover:** Interferes with attacks against vessel  
**Concealment:** Makes detection/targeting more difficult

- Function as traits increasing attack Difficulty or making attacks impossible
- May increase complication range
- Cover: circumvent by attacking from different direction or displacing cover
- Concealment: circumvent by finding other detection methods

## Damage System

### Damage Calculation

1. **Determine Damage:** Base damage from weapon (may be modified by talents/factors)
2. **Apply Resistance:** Reduce damage by 1 per point of Resistance (minimum 1)
3. **Complications:** Each complication may reduce damage by 1

### Applying Damage

Damage reduces shields by 1 per point. Check against these thresholds:

| Shield Status | Effect |
|---------------|--------|
| **Below 50%** | Ship is **shaken** - commanding officer picks damage result |
| **Below 25%** | Ship is **shaken** again. If already shaken this attack, suffers **breach** instead |
| **Shields at 0** | Shields down - ship suffers **breach** |

**If shields already at 0:** Ship suffers breach immediately (no shield reduction).

### Breaches

**Breach** = trait representing serious damage to ship/crew, associated with specific system.

**Effects:**
- Increases Difficulty of tasks
- May make some tasks impossible
- Multiple identical breaches can combine into Potent traits (e.g., Hull Breach 2)

**System Destroyed:** When breaches ≥ half ship's Scale, system destroyed. Tasks assisted by that system automatically fail.

**Critical Damage:** When total breaches > ship's Scale:
- Ship can no longer function
- No further actions possible
- Additional breaches = ship destroyed
- NPC vessels may be destroyed immediately (GM discretion)

### Collision Damage

**Collision Damage Rating** = Ship's Scale + (zones moved ÷ 2)
- Has Devastating and Piercing qualities
- Ramming adds Intense quality
- Both ships take each other's collision damage

### Warp Core Breach

If ship suffers critical damage AND Engines system destroyed:
- Roll d20 at end of each round
- If roll > ship's Engineering rating: reactor explodes
- **Explosion:** Destroys ship, kills all aboard, inflicts (Scale +1) Piercing damage to all ships at Close range

**Prevention Options:**
- **Stabilize Reactor:** Extended task, Progress = ship's Engines, Difficulty 3 (Daring/Control + Engineering)
- **Eject Reactor:** Difficulty 2 (Daring + Engineering). Still explodes but doesn't destroy ship outright

## Repairs

### Combat Repairs (Damage Control)

**Methods:**
1. **Damage Control action:** Send repair team (page 303 reference)
2. **Personal repair:** Use Change Position minor action, move to damage site (Daring + Engineering)

**Difficulty:** 
- Base: 2
- +1 for each additional breach to same system

**Effect:** Patches breach (removes penalties), but doesn't fully repair. If system takes new breach, all patched breaches return.

### Long-Term Repairs

**Time:** 6 hours per breach

**Difficulty:** 
- Control + Engineering, Difficulty 3
- Difficulty 2 if breach was patched
- No roll needed if undisturbed

**Simultaneous Repairs:** Ship can repair breaches = Engineering rating at once

**Starbase Benefits:**
- Difficulty reduced by 2
- Time reduced by half

### Abandon Ship

If critical damage or desperate situation:
- Boarding escape pod: Change Position minor action + Daring + Conn (Difficulty 0)
- Each pod holds 4 (max 6)
- Half crew escapes by end of round order given
- Remaining half escape following round

## Key Notes

- Attacks against starships are rarely final (unlike personal combat)
- Strong shields weather damage; nimble ships avoid attacks
- Once shields fail, hull and systems take grievous damage
- Battles are costly - dozens or hundreds may die
- Combat typically occurs in interesting locations (strategic value)