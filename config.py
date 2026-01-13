# NOTE: Testing configs
iterations: list[int] = [
    5,
]  # iterations LLM gets before hard stop
start_scene: int = 151  # first test scene
end_scene: int = 158  # last test scene

# NOTE: Agent management
agents: list[str] = [
    "OpenAIAgentGPT4omini",
]

# NOTE: Experimental methods
prompting_methods: list[str] = [
    "zero_shot",
    "one_shot",
    "one_shot_cot",
    "few_shot",
    "few_shot_cot",
]
