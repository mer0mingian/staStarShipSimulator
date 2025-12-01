# Adding New Actions - Quick Guide

The refactored action system makes adding new actions **incredibly fast** - no custom code required for most actions!

## How Fast Is It?

- **Before refactoring**: ~100 lines of code per action (database schema, API endpoint, UI handler)
- **After refactoring**: ~10 lines of configuration per action ⚡

## Action Types

### 1. Buff Actions (Simplest!)

These create temporary effects that modify future actions. **No roll required.**

Examples: Calibrate Weapons, Calibrate Sensors, Targeting Solution

#### How to Add:

1. **Add configuration** to `sta/mechanics/action_config.py`:

```python
"Your Action Name": {
    "type": "buff",
    "effect": {
        "applies_to": "attack",  # or "defense", "sensor", "movement", "all"
        "duration": "next_action",  # or "end_of_turn", "end_of_round"
        "damage_bonus": 1,  # Optional: +damage
        "resistance_bonus": 2,  # Optional: +resistance
        "can_reroll": True,  # Optional: allow re-roll
        "can_choose_system": True,  # Optional: target specific system
        "piercing": True,  # Optional: ignore resistance
    }
},
```

2. **Update UI** in `sta/web/templates/combat.html` - add to `selectAction()`:

```javascript
else if (name === 'Your Action Name') {
    executeGenericAction('Your Action Name');
}
```

3. **Add the helper function** (one time only, if not exists):

```javascript
async function executeGenericAction(actionName) {
    const response = await fetch(`/api/encounter/${encounterId}/execute-action`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action_name: actionName })
    });
    const data = await response.json();

    // Show result in dice panel
    const resultsDiv = document.getElementById('dice-results');
    const displayDiv = document.getElementById('dice-display');
    resultsDiv.style.display = 'block';

    if (data.success) {
        displayDiv.innerHTML = `
            <div class="alert alert-success" style="padding: 15px; background: #1a3a1a; border: 2px solid var(--lcars-green);">
                <strong>${data.message.toUpperCase()}</strong>
            </div>
        `;
    } else {
        displayDiv.innerHTML = `
            <div class="alert alert-error" style="padding: 15px; background: #3a1a1a; border: 2px solid var(--lcars-red);">
                <strong>ERROR:</strong> ${data.error}
            </div>
        `;
    }
}
```

**That's it!** The action is now fully functional.

---

### 2. Task Roll Actions

These require a 2d20 roll and do something on success.

Examples: Rally, Damage Control, Scan For Weakness, Sensor Sweep

#### How to Add:

1. **Add configuration** to `sta/mechanics/action_config.py`:

```python
"Your Action Name": {
    "type": "task_roll",
    "roll": {
        "attribute": "control",  # or "presence", "reason", "daring", etc.
        "discipline": "security",  # or "command", "science", "engineering", etc.
        "difficulty": 2,
        "focus_eligible": True,
    },
    "on_success": {
        # Choose one or more:
        "generate_momentum": True,  # Add momentum from extra successes
        "patch_breach": True,  # Remove a breach
        "restore_power": True,  # Restore Reserve Power
        "create_effect": {  # Create a buff (same as buff actions)
            "applies_to": "attack",
            "duration": "next_action",
            "damage_bonus": 2,
        }
    },
    # Optional requirements:
    "requires_reserve_power": True,  # Only if ship has Reserve Power
},
```

2. **Update UI** - for task rolls that use the dice panel, **nothing more needed!** They automatically work with the generic dice roller.

   Or, for actions with custom UI (like choosing which breach to patch), create a custom handler similar to `executeFireAction()`.

**That's it!**

---

## Real Examples

### Example 1: Modulate Shields

**Complexity**: Task roll that creates a buff on success

```python
"Modulate Shields": {
    "type": "task_roll",
    "roll": {
        "attribute": "control",
        "discipline": "security",
        "difficulty": 1,
        "focus_eligible": True,
    },
    "on_success": {
        "create_effect": {
            "applies_to": "defense",
            "duration": "end_of_turn",
            "resistance_bonus": 2,
        }
    }
},
```

**Time to implement**: 30 seconds

---

### Example 2: Scan For Weakness

**Complexity**: Task roll that creates a powerful attack buff

```python
"Scan For Weakness": {
    "type": "task_roll",
    "roll": {
        "attribute": "control",
        "discipline": "science",
        "difficulty": 2,
        "focus_eligible": True,
    },
    "on_success": {
        "create_effect": {
            "applies_to": "attack",
            "duration": "next_action",
            "damage_bonus": 2,
            "piercing": True,  # Ignores resistance!
        }
    }
},
```

**Time to implement**: 30 seconds

---

### Example 3: Rally

**Complexity**: Simple task roll that generates Momentum

```python
"Rally": {
    "type": "task_roll",
    "roll": {
        "attribute": "presence",
        "discipline": "command",
        "difficulty": 0,  # Always succeeds unless you roll 20s
        "focus_eligible": True,
    },
    "on_success": {
        "generate_momentum": True,
    }
},
```

**Time to implement**: 20 seconds

---

## Effect Modifiers Reference

| Modifier | Type | Description | Example Use |
|----------|------|-------------|-------------|
| `damage_bonus` | int | +damage to attacks | Calibrate Weapons: +1 |
| `resistance_bonus` | int | +resistance to defense | Modulate Shields: +2 |
| `difficulty_modifier` | int | Modify roll difficulty | Attack Pattern: -1 (easier) |
| `can_reroll` | bool | Allow re-rolling 1d20 | Calibrate Sensors, Targeting Solution |
| `can_choose_system` | bool | Choose which system to hit | Targeting Solution |
| `piercing` | bool | Ignore target resistance | Scan For Weakness |

## Duration Options

| Duration | Clears When |
|----------|-------------|
| `next_action` | After the next applicable action (e.g., next attack) |
| `end_of_turn` | When the player's turn ends |
| `end_of_round` | When the round ends (both player & enemy turns) |

## Applies To Options

| Value | Applies To |
|-------|------------|
| `attack` | Weapon attacks (Fire action) |
| `defense` | Incoming attacks |
| `sensor` | Sensor/science actions |
| `movement` | Movement/navigation actions |
| `all` | All actions |

---

## What About Complex Actions?

For actions that don't fit the templates (like Ram, Tractor Beam, etc.), you can still use the configuration system for requirements checking, then add custom logic in a new handler function.

But **80% of actions** can be implemented with just configuration!

---

## Testing Your New Action

1. Start the server: `python scripts/run_server.py`
2. Create an encounter
3. Select your action from the appropriate list
4. Verify it works as expected

---

## Migration Note

The old `calibrate_weapons_active` database field has been replaced with `active_effects_json`. Run the migration if you have an existing database:

```bash
python migrate_to_effects_system.py
```

---

Happy action building! 🚀
