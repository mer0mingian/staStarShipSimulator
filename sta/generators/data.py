"""Reference data for random generation."""

# Focuses by discipline (simplified list for alpha)
FOCUSES = {
    "command": [
        "Composure", "Diplomacy", "Inspiration", "Intimidation",
        "Negotiation", "Persuasion", "Strategy / Tactics", "Team Dynamics",
    ],
    "conn": [
        "Astronavigation", "Atmospheric Flight", "Helm Operations",
        "Impulse Engines", "Precision Maneuvering", "Small Craft",
        "Warp Drive", "Zero-G Combat",
    ],
    "engineering": [
        "Electro-Plasma Systems", "Emergency Repairs", "Energy Weapons",
        "Jury-Rigging", "Repairs and Maintenance", "Transporters / Replicators",
        "Warp Core Mechanics", "Troubleshooting",
    ],
    "security": [
        "Combat Maneuvers", "Hand Phasers", "Martial Arts",
        "Security Systems", "Small Unit Tactics", "Strategy",
        "Targeting Systems", "Torpedoes",
    ],
    "medicine": [
        "Combat Medic", "Diagnostics", "Emergency Medicine",
        "First Aid", "Genetics", "Surgery", "Triage", "Xenobiology",
    ],
    "science": [
        "Astronomy / Astrophysics", "Biology / Xenobiology", "Chemistry",
        "Geology", "Physics", "Research", "Sensor Operations",
        "Stellar Cartography",
    ],
}

# General talents (no species requirement)
GENERAL_TALENTS = [
    "Bold (Command)", "Bold (Conn)", "Bold (Engineering)",
    "Bold (Security)", "Bold (Medicine)", "Bold (Science)",
    "Cautious (Command)", "Cautious (Conn)", "Cautious (Engineering)",
    "Cautious (Security)", "Cautious (Medicine)", "Cautious (Science)",
    "Dauntless", "Technical Expertise", "Tough", "Studious",
    "Close-Knit Crew", "Constantly Watching", "Second Wind", "Well-Informed",
]

# Species list
SPECIES = [
    "Human", "Vulcan", "Andorian", "Tellarite", "Betazoid",
    "Trill", "Bajoran", "Bolian", "Denobulan", "Caitian",
]

# Ranks
RANKS = [
    "Ensign", "Lieutenant Junior Grade", "Lieutenant",
    "Lieutenant Commander", "Commander", "Captain",
]

# Ship classes with their stats
SHIP_CLASSES = {
    "Constitution": {
        "scale": 4,
        "systems": {"comms": 7, "computers": 7, "engines": 8, "sensors": 8, "structure": 7, "weapons": 7},
        "departments": {"command": 1, "conn": 0, "engineering": 0, "medicine": 0, "science": 1, "security": 1},
        "weapons": ["Phaser Banks", "Photon Torpedoes"],
        "era": "23rd century",
    },
    "Miranda": {
        "scale": 3,
        "systems": {"comms": 7, "computers": 7, "engines": 7, "sensors": 8, "structure": 6, "weapons": 7},
        "departments": {"command": 0, "conn": 0, "engineering": 1, "medicine": 0, "science": 1, "security": 1},
        "weapons": ["Phaser Banks", "Photon Torpedoes"],
        "era": "23rd century",
    },
    "Excelsior": {
        "scale": 5,
        "systems": {"comms": 8, "computers": 8, "engines": 9, "sensors": 8, "structure": 8, "weapons": 8},
        "departments": {"command": 1, "conn": 1, "engineering": 1, "medicine": 0, "science": 0, "security": 0},
        "weapons": ["Phaser Arrays", "Photon Torpedoes"],
        "era": "23rd-24th century",
    },
    "Galaxy": {
        "scale": 6,
        "systems": {"comms": 9, "computers": 10, "engines": 9, "sensors": 10, "structure": 9, "weapons": 9},
        "departments": {"command": 1, "conn": 0, "engineering": 1, "medicine": 1, "science": 1, "security": 0},
        "weapons": ["Phaser Arrays", "Photon Torpedoes"],
        "era": "24th century",
    },
    "Intrepid": {
        "scale": 4,
        "systems": {"comms": 9, "computers": 10, "engines": 10, "sensors": 10, "structure": 8, "weapons": 8},
        "departments": {"command": 0, "conn": 1, "engineering": 1, "medicine": 0, "science": 2, "security": 0},
        "weapons": ["Phaser Arrays", "Photon Torpedoes"],
        "era": "24th century",
    },
    "Defiant": {
        "scale": 3,
        "systems": {"comms": 8, "computers": 9, "engines": 10, "sensors": 9, "structure": 9, "weapons": 10},
        "departments": {"command": 0, "conn": 1, "engineering": 0, "medicine": 0, "science": 0, "security": 3},
        "weapons": ["Pulse Phaser Cannons", "Quantum Torpedoes"],
        "era": "24th century",
    },
    "Akira": {
        "scale": 4,
        "systems": {"comms": 8, "computers": 9, "engines": 9, "sensors": 9, "structure": 9, "weapons": 10},
        "departments": {"command": 0, "conn": 0, "engineering": 1, "medicine": 0, "science": 0, "security": 2},
        "weapons": ["Phaser Arrays", "Photon Torpedoes", "Quantum Torpedoes"],
        "era": "24th century",
    },
    "Bird-of-Prey": {
        "scale": 3,
        "systems": {"comms": 7, "computers": 7, "engines": 9, "sensors": 8, "structure": 6, "weapons": 8},
        "departments": {"command": 0, "conn": 1, "engineering": 0, "medicine": 0, "science": 0, "security": 2},
        "weapons": ["Disruptor Cannons", "Photon Torpedoes"],
        "era": "23rd-24th century",
        "faction": "Klingon",
    },
    "D7 Battlecruiser": {
        "scale": 4,
        "systems": {"comms": 7, "computers": 7, "engines": 8, "sensors": 7, "structure": 8, "weapons": 9},
        "departments": {"command": 1, "conn": 0, "engineering": 0, "medicine": 0, "science": 0, "security": 2},
        "weapons": ["Disruptor Banks", "Photon Torpedoes"],
        "era": "23rd century",
        "faction": "Klingon",
    },
    "Warbird": {
        "scale": 5,
        "systems": {"comms": 8, "computers": 8, "engines": 8, "sensors": 9, "structure": 8, "weapons": 9},
        "departments": {"command": 1, "conn": 0, "engineering": 1, "medicine": 0, "science": 1, "security": 1},
        "weapons": ["Disruptor Arrays", "Plasma Torpedoes"],
        "era": "24th century",
        "faction": "Romulan",
    },
}

# Ship talents
SHIP_TALENTS = [
    "Ablative Armor", "Advanced Shields", "Backup EPS Conduits",
    "Improved Hull Integrity", "Redundant Systems (Engines)",
    "Redundant Systems (Weapons)", "Expanded Munitions",
    "Fast Targeting Systems", "High-Power Tractor Beam",
    "Improved Impulse Drive", "Improved Warp Drive",
    "Advanced Sensor Suites", "High-Resolution Sensors",
    "Modular Laboratories", "Rugged Design", "Improved Damage Control",
]

# Weapon templates
WEAPON_TEMPLATES = {
    "Phaser Banks": {"type": "energy", "damage": 4, "range": "medium", "qualities": ["Versatile 2"]},
    "Phaser Arrays": {"type": "energy", "damage": 4, "range": "medium", "qualities": ["Versatile 2", "Area or Spread"]},
    "Pulse Phaser Cannons": {"type": "energy", "damage": 6, "range": "close", "qualities": ["Versatile 2"]},
    "Disruptor Banks": {"type": "energy", "damage": 4, "range": "medium", "qualities": ["Intense"]},
    "Disruptor Cannons": {"type": "energy", "damage": 5, "range": "close", "qualities": ["Intense"]},
    "Disruptor Arrays": {"type": "energy", "damage": 4, "range": "medium", "qualities": ["Intense", "Area or Spread"]},
    "Photon Torpedoes": {"type": "torpedo", "damage": 3, "range": "long", "qualities": ["High Yield"]},
    "Quantum Torpedoes": {"type": "torpedo", "damage": 4, "range": "long", "qualities": ["High Yield", "Intense", "Calibration"]},
    "Plasma Torpedoes": {"type": "torpedo", "damage": 5, "range": "long", "qualities": ["Persistent", "Calibration", "Cumbersome"]},
}

# Ship name prefixes/components for generation
SHIP_NAME_PREFIXES = [
    "USS", "USS", "USS",  # Weighted toward Federation
    "IKS",  # Klingon
    "IRW",  # Romulan
]

SHIP_NAMES_FEDERATION = [
    "Enterprise", "Defiant", "Voyager", "Discovery", "Reliant",
    "Excelsior", "Endeavour", "Intrepid", "Prometheus", "Titan",
    "Aventine", "Thunderchild", "Saratoga", "Hood", "Lexington",
    "Potemkin", "Yorktown", "Challenger", "Victory", "Equinox",
    "Bellerophon", "Cairo", "Centaur", "Cochrane", "Dauntless",
]

SHIP_NAMES_KLINGON = [
    "Bortas", "Rotarran", "Hegh'ta", "Pagh", "Ch'Tang",
    "Kronos One", "Amar", "Klothos", "Fek'lhr", "Negh'Var",
]

SHIP_NAMES_ROMULAN = [
    "Valdore", "Belak", "Khazara", "Terix", "Haakona",
    "Devoras", "Narada", "Scimitar", "Decius", "T'Met",
]

# First names by species
FIRST_NAMES = {
    "Human": ["James", "Jean-Luc", "Benjamin", "Kathryn", "Jonathan", "Michael", "Philippa", "Christopher", "Carol", "Hikaru", "Nyota", "Pavel", "William", "Deanna", "Beverly", "Wesley", "Miles", "Jadzia", "Julian", "Tom", "B'Elanna", "Harry", "Seven", "Travis", "Hoshi", "Malcolm"],
    "Vulcan": ["Spock", "Sarek", "T'Pol", "Tuvok", "Soval", "T'Pau", "Saavik", "Vorik", "Solok", "T'Pring", "Sybok", "Valeris", "Sakonna", "T'Lar"],
    "Andorian": ["Shran", "Talas", "Talla", "Thy'lek", "Thelin", "Tarah", "Telev", "Keval", "Jhamel"],
    "Tellarite": ["Gral", "Gav", "Naarg", "Tev", "Brunt", "Phlox"],
    "Betazoid": ["Lwaxana", "Tam", "Lon", "Devinoni"],
    "Trill": ["Curzon", "Ezri", "Tobin", "Emony", "Audrid", "Torias", "Joran", "Lenara"],
    "Bajoran": ["Kira", "Ro", "Opaka", "Winn", "Bareil", "Shakaar", "Leeta", "Kai"],
    "Bolian": ["Mot", "Rixx", "Zim", "Hars", "Boq'ta"],
    "Denobulan": ["Phlox", "Feezal", "Yutani"],
    "Caitian": ["M'Ress", "S'Rrel", "Rriarr"],
}

LAST_NAMES = {
    "Human": ["Kirk", "Picard", "Sisko", "Janeway", "Archer", "Burnham", "Georgiou", "Pike", "Marcus", "Sulu", "Uhura", "Chekov", "Riker", "Troi", "Crusher", "O'Brien", "Bashir", "Paris", "Torres", "Kim", "Mayweather", "Sato", "Reed"],
    "Vulcan": [],  # Vulcans typically use single names
    "Andorian": [],  # Often single names or clan names
    "Tellarite": [],
    "Betazoid": ["Troi", "Elbrun", "Suder", "Ral"],
    "Trill": ["Dax", "Kahn", "Odan"],
    "Bajoran": ["Nerys", "Laren", "Adami", "Antos", "Edon"],  # Note: Bajoran family name comes first
    "Bolian": [],
    "Denobulan": [],
    "Caitian": [],
}
