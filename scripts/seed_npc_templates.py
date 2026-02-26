"""Seed script for adding generic NPC templates to the global manifest."""

import json
from sta.database.db import get_session
from sta.database.schema import NPCRecord


def seed_npc_templates():
    """Add generic NPC templates to the global manifest."""
    session = get_session()

    npc_templates = [
        {
            "name": "Starfleet Security Officer",
            "npc_type": "minor",
            "attributes": {
                "control": 9,
                "fitness": 9,
                "presence": 8,
                "daring": 10,
                "insight": 8,
                "reason": 8,
            },
            "disciplines": {
                "command": 1,
                "conn": 1,
                "engineering": 1,
                "medicine": 0,
                "science": 0,
                "security": 2,
            },
            "stress": 5,
            "stress_max": 5,
            "appearance": "Starfleet uniform, phaser on hip",
            "motivation": "Protect the crew",
            "affiliation": "Starfleet",
            "location": "Security",
            "notes": "Standard security personnel. Armed with phaser type-1.",
        },
        {
            "name": "Starfleet Medical Officer",
            "npc_type": "minor",
            "attributes": {
                "control": 10,
                "fitness": 8,
                "presence": 9,
                "daring": 7,
                "insight": 10,
                "reason": 9,
            },
            "disciplines": {
                "command": 1,
                "conn": 0,
                "engineering": 0,
                "medicine": 2,
                "science": 1,
                "security": 0,
            },
            "stress": 5,
            "stress_max": 5,
            "appearance": "Starfleet medical uniform, tricorder",
            "motivation": "Heal the injured",
            "affiliation": "Starfleet",
            "location": "Sickbay",
            "notes": "Medical personnel. Can provide First Aid in combat.",
        },
        {
            "name": "Starfleet Engineer",
            "npc_type": "minor",
            "attributes": {
                "control": 10,
                "fitness": 8,
                "presence": 8,
                "daring": 8,
                "insight": 8,
                "reason": 10,
            },
            "disciplines": {
                "command": 0,
                "conn": 1,
                "engineering": 2,
                "medicine": 0,
                "science": 1,
                "security": 0,
            },
            "stress": 5,
            "stress_max": 5,
            "appearance": "Starfleet engineering uniform, engineering kit",
            "motivation": "Keep systems running",
            "affiliation": "Starfleet",
            "location": "Engineering",
            "notes": "Engineering personnel. Good at repairs and technical tasks.",
        },
        {
            "name": "Starfleet Science Officer",
            "npc_type": "minor",
            "attributes": {
                "control": 10,
                "fitness": 7,
                "presence": 8,
                "daring": 7,
                "insight": 9,
                "reason": 10,
            },
            "disciplines": {
                "command": 0,
                "conn": 1,
                "engineering": 1,
                "medicine": 1,
                "science": 2,
                "security": 0,
            },
            "stress": 5,
            "stress_max": 5,
            "appearance": "Starfleet science uniform, scanner device",
            "motivation": "Discover new things",
            "affiliation": "Starfleet",
            "location": "Science Lab",
            "notes": "Science personnel. Good at analysis and research tasks.",
        },
        {
            "name": "Klingon Warrior",
            "npc_type": "notable",
            "attributes": {
                "control": 8,
                "fitness": 11,
                "presence": 10,
                "daring": 11,
                "insight": 8,
                "reason": 7,
            },
            "disciplines": {
                "command": 2,
                "conn": 1,
                "engineering": 0,
                "medicine": 0,
                "science": 0,
                "security": 3,
            },
            "stress": 6,
            "stress_max": 6,
            "appearance": "Klingon battle armor, bat'leth or disruptor",
            "motivation": "Battle honor",
            "affiliation": "Klingon Empire",
            "location": "Unknown",
            "notes": "Klingon veteran warrior. Has Protection 1 from armor. D'k tahg: Deadly 2, Melee. Disruptor: Deadly 4, Ranged.",
        },
        {
            "name": "Romulan Soldier",
            "npc_type": "minor",
            "attributes": {
                "control": 9,
                "fitness": 9,
                "presence": 9,
                "daring": 9,
                "insight": 8,
                "reason": 8,
            },
            "disciplines": {
                "command": 1,
                "conn": 1,
                "engineering": 0,
                "medicine": 0,
                "science": 1,
                "security": 2,
            },
            "stress": 5,
            "stress_max": 5,
            "appearance": "Romulan military uniform, disruptor pistol",
            "motivation": "Serve the Empire",
            "affiliation": "Romulan Star Empire",
            "location": "Unknown",
            "notes": "Romulan soldier. Armed with disruptor pistol (Deadly 4).",
        },
        {
            "name": "Borg Drone",
            "npc_type": "minor",
            "attributes": {
                "control": 10,
                "fitness": 10,
                "presence": 5,
                "daring": 10,
                "insight": 5,
                "reason": 10,
            },
            "disciplines": {
                "command": 0,
                "conn": 0,
                "engineering": 2,
                "medicine": 0,
                "science": 1,
                "security": 2,
            },
            "stress": 8,
            "stress_max": 8,
            "appearance": "Cybernetic implants, Borg rifle",
            "motivation": "Assimilate",
            "affiliation": "Borg Collective",
            "location": "Unknown",
            "notes": "Borg drone. High stress. Armed with Borg rifle. Immune to stun attacks (treat as deadly).",
        },
        {
            "name": "Gorn Captain",
            "npc_type": "major",
            "attributes": {
                "control": 9,
                "fitness": 12,
                "presence": 9,
                "daring": 10,
                "insight": 8,
                "reason": 8,
            },
            "disciplines": {
                "command": 3,
                "conn": 2,
                "engineering": 1,
                "medicine": 0,
                "science": 1,
                "security": 3,
            },
            "stress": 8,
            "stress_max": 8,
            "appearance": "Gorn military attire, plasma cannon",
            "motivation": "Territorial expansion",
            "affiliation": "Gorn Hegemony",
            "location": "Unknown",
            "notes": "Gorn commander. Powerful melee (Deadly 4). Armed with plasma cannon. Has Protection 1 from natural armor.",
        },
        {
            "name": "Federation Away Team Member",
            "npc_type": "minor",
            "attributes": {
                "control": 10,
                "fitness": 9,
                "presence": 9,
                "daring": 9,
                "insight": 9,
                "reason": 9,
            },
            "disciplines": {
                "command": 1,
                "conn": 1,
                "engineering": 1,
                "medicine": 1,
                "science": 1,
                "security": 1,
            },
            "stress": 5,
            "stress_max": 5,
            "appearance": "Standard Starfleet uniform",
            "motivation": "Complete the mission",
            "affiliation": "Starfleet",
            "location": "Away Team",
            "notes": "Versatile away team member. Balanced stats.",
        },
        {
            "name": "Hostile Alien",
            "npc_type": "minor",
            "attributes": {
                "control": 9,
                "fitness": 10,
                "presence": 8,
                "daring": 10,
                "insight": 7,
                "reason": 7,
            },
            "disciplines": {
                "command": 1,
                "conn": 1,
                "engineering": 0,
                "medicine": 0,
                "science": 0,
                "security": 2,
            },
            "stress": 5,
            "stress_max": 5,
            "appearance": "Alien physiology, natural weapons",
            "motivation": "Unknown",
            "affiliation": "Unknown",
            "location": "Unknown",
            "notes": "Generic hostile alien. Natural weapons (claw, bite) can inflict Stun 2.",
        },
    ]

    added = 0
    skipped = 0

    for npc_data in npc_templates:
        existing = session.query(NPCRecord).filter_by(name=npc_data["name"]).first()
        if existing:
            skipped += 1
            continue

        npc = NPCRecord(
            name=npc_data["name"],
            npc_type=npc_data["npc_type"],
            attributes_json=json.dumps(npc_data.get("attributes", {})),
            disciplines_json=json.dumps(npc_data.get("disciplines", {})),
            stress=npc_data.get("stress", 5),
            stress_max=npc_data.get("stress_max", 5),
            appearance=npc_data.get("appearance"),
            motivation=npc_data.get("motivation"),
            affiliation=npc_data.get("affiliation"),
            location=npc_data.get("location"),
            notes=npc_data.get("notes"),
        )
        session.add(npc)
        added += 1

    session.commit()
    session.close()

    return added, skipped


if __name__ == "__main__":
    added, skipped = seed_npc_templates()
    print(f"Added {added} NPC templates, skipped {skipped} existing.")
