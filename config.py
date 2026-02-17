# NOTE: Testing configs
iterations: list[int] = [
    5,
]  # iterations LLM gets before hard stop

# NOTE: FIX NUMBERING SCHEMA LATER...THIS IS JUST A TEMP FIX
start_scene: int = 7  # first test scene
end_scene: int = 112  # last test scene

# NOTE: Agent management, leave as GPT in repo but change to what you are testing
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
