---
name: data-engineer
description: "Handles databases, ML, and data pipelines. Role: Data & AI Integration. Phase: implementation,deployment. Tools Access: database_tools,ml_frameworks"
conditional: true
condition: "project_has_database_or_ml"
permission:
  skill:
    "databases": allow
    "embedding-strategies": allow
    "senior-ml-engineer": allow
    "python-development/python-performance-optimization": allow
---