{loop_template$:
    """  - `{{name}}`: `{{type}}`
    > {{description}}""",
    name=[p['name'] for p in parameters.values()],
    type=[p['type'] for p in parameters.values()],
    description=[p['description'] for p in parameters.values()],
    joiner="""
"""
}