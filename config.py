# NOTE: Networking timeout, set genously plz...I'm too lazy to implement async timeouts on here
timeout_limit = 600  # for context 600 = 10 min before exp gives up and moves on

# NOTE: Testing configs
iterations: list[int] = [
    10,
]  # iterations LLM gets before hard stop]
# max_token limit except for long thinking models
# max_tokens = 8192
# tmp double test
max_tokens = 16384


# NOTE: FIX NUMBERING SCHEMA LATER...THIS IS JUST A TEMP FIX
start_scene: int = 7  # first test scene
end_scene: int = 111  # last test scene

# NOTE: Serverless provider model management, consult respective docs for naming schema

ANTHROPIC_MODEL = "claude-opus-4-6"
OPENAI_MODEL = "gpt-5.4"
GEMINI_MODEL = "gemini-2.5-pro"
DEEPSEEK_MODEL = "deepseek-ai/DeepSeek-R1"  # ran through together.ai, so it has a "deepseek-ai/" beforehand
QWEN_MODEL = "Qwen/Qwen3.5-397B-A17B"
KIMI_MODEL = "moonshotai/Kimi-K2.5"
GLM_MODEL = "zai-org/GLM-5"

# OPENROUTER MODELS for bleeding edge & free-access models (MiniMax, Nemotron, MiMO-V2-Pro, etc)
# THESE ARE DATA LOGGED SO PLEASE ENSURE YOU ARE SENDING NOTHING IMPORTANT!!!
OPENROUTER_MODEL = "anthropic/claude-opus-4.6"


# NOTE: Agent management, leave as GPT in repo but change to what you are testing
agents: list[str] = [
    "OpenRouterAgent",
]

# NOTE: Experimental methods
prompting_methods: list[str] = [
    "zero_shot",
    "one_shot",
    "one_shot_cot",
    "few_shot",
    "few_shot_cot",
]
