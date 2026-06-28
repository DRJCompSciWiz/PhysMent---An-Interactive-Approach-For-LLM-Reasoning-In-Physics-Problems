"""Runtime configuration for PhysMent benchmark experiments."""

# Per-experiment networking timeout in seconds (600 = 10 minutes before a
# scene is abandoned and the run moves on to the next one).
timeout_limit = 600

# Iteration budgets to evaluate. Each value is the number of agent turns
# allowed before the run is forced to stop.
iterations: list[int] = [
    10,
]

# Maximum tokens per model response (raised to accommodate long-form
# reasoning models).
max_tokens = 16384

# Inclusive scene-ID range to evaluate (canonical scenes run 7-111).
start_scene: int = 7
end_scene: int = 111

# Model identifiers per provider. Consult each provider's documentation for
# its exact model-naming scheme.
ANTHROPIC_MODEL = "claude-opus-4-6"
OPENAI_MODEL = "gpt-5.4"
GEMINI_MODEL = "gemini-2.5-pro"
DEEPSEEK_MODEL = "deepseek-ai/DeepSeek-R1"  # served via Together.ai (note the "deepseek-ai/" prefix)
QWEN_MODEL = "Qwen/Qwen3.5-397B-A17B"
KIMI_MODEL = "moonshotai/Kimi-K2.5"
GLM_MODEL = "zai-org/GLM-5"

# OpenRouter provides access to additional and bleeding-edge models (MiniMax,
# Nemotron, etc.). Note that requests may be logged by the provider, so do not
# send anything sensitive through it.
OPENROUTER_MODEL = "anthropic/claude-opus-4.6"

# Active agent(s) to run. Add an "<XXX>Agent" class name here and set the
# matching model above to choose which system is evaluated.
agents: list[str] = [
    "OpenRouterAgent",
]

# Prompting methods supported by Scene.set_prompt_method(). main.py currently
# runs "zero_shot"; the others are available for prompt-ablation experiments.
prompting_methods: list[str] = [
    "zero_shot",
    "one_shot",
    "one_shot_cot",
    "few_shot",
    "few_shot_cot",
]
