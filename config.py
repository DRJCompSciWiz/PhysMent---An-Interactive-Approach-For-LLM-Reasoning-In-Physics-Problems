# NOTE: Testing configs
iterations: list[int] = [
    5,
]  # iterations LLM gets before hard stop

# NOTE: FIX NUMBERING SCHEMA LATER...THIS IS JUST A TEMP FIX
start_scene: int = 70  # first test scene
end_scene: int = 70  # last test scene

# NOTE: Agent management
agents: list[str] = [
    "AnthropicAgentClaudeOpus4",
]

# NOTE: Experimental methods
prompting_methods: list[str] = [
    "zero_shot",
    "one_shot",
    "one_shot_cot",
    "few_shot",
    "few_shot_cot",
]
