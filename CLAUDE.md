# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

PhysMent is a physics-reasoning benchmark: an LLM is given a physics problem, iteratively calls tools on a MuJoCo simulator, and submits a numeric/keyword answer that is scored against ground truth. Scenes live under `Scenes/Scene{N}/` as a `scene{N}.json` (metadata, objects, permissions, `answer`) plus a `scene{N}.xml` MuJoCo definition. Results are written to `TestResults/{AgentType}/{scene_number}/`.

## Running

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in OPENAI_API_KEY / ANTHROPIC_API_KEY / TOGETHER_API_KEY / GEMINI_API_KEY
python main.py
```

- **There is no CLI for selecting scenes or models.** Everything is driven by `config.py`:
  - `start_scene` / `end_scene` — inclusive range iterated by `main.add_scenes`.
  - `iterations` — list of max-iteration caps; the full sweep runs once per value.
  - `agents` — list of agent class-name strings (e.g. `"QwenAgent"`, `"AnthropicAgent"`, `"OpenAIAgent"`). `initialize_agent` in `main.py` dispatches these to classes in `AgentClass.py`. Legacy per-model entries like `OpenAIAgentGPT4o` still exist; for new runs, prefer the bare `XxxAgent` name and set the model via the `*_MODEL` constants in `config.py`.
  - `max_tokens`, `timeout_limit` — per-call limits (no async timeout; the value is a soft cap enforced inside the experiment loop).
- `--enable-python-tool` exists as a flag but is force-disabled inside `main.py` (`args.enable_python_tool = False`). Re-enable deliberately.

### Validating scene answer formats

`python validate_answers.py` loads every `scene{N}.json` and runs the same normalization/matching logic used by `Experiment._check_answer` against synthetic LLM-formatted variants. This is the closest thing to a test suite — use it after touching answer parsing or adding new scenes. It does **not** require MuJoCo.

There is no pytest suite, no linter config, and no build step.

## Architecture

The runtime is a five-object pipeline wired together in `main.main()`:

```
main.py → initialize_agent() → Experiment(scene_id, agent, ...) → {Simulator, Scene, Agent}
                                        ↓
                         Experiment.run_experiment() loop
                                        ↓
                           Data.summarize_scenes() → TestResults/
```

1. **`main.py`** — orchestrator. For every `(agent_type, iteration, scene_id)` it **re-instantiates the agent per scene** (comment: "prevent token exhaustion"). It catches rate-limit / quota / context-length errors and `break`s out of the *scene* loop for that agent (skipping remaining scenes for that model), while other exceptions only `continue` past the single scene. `JsonLogger` + `Tee` duplicate stdout/logging into a per-scene JSON under `TestResults/{agent}/{scene_number}/log_{timestamp}.json`.

2. **`Experiment.py`** — the agent ↔ simulator loop.
   - `tool_mapping` binds a flat dict of tool names → `Simulator` methods. `answer` is the sentinel that terminates the loop; its lambda just acknowledges and the real answer is pulled from the parameters.
   - `_normalize_answer` / `_check_answer` implement the scoring. Tolerances, unit stripping, `object_` prefix stripping, CSV multi-value handling, and word-boundary containment are all here. **Note:** the README says tolerance is 0.001, but the actual tolerance in code is `0.1`. Don't "fix" one without updating the other intentionally.
   - `validate_answers.py` mirrors this logic — if you change matching in `Experiment.py`, update `validate_answers.py` too.

3. **`Scene.py`** — loads `Scenes/Scene{N}/scene{N}.{json,xml}`, exposes metadata and `object_permissions` (the JSON keys are stripped of `object_` / `_permissions` at load time, so downstream code uses bare ids like `"1"`, not `"object_1_permissions"`), and builds the large LLM prompt via `generate_prompt()`. `set_prompt_method(...)` selects one of `zero_shot | one_shot | one_shot_cot | few_shot | few_shot_cot`; `main.py` currently hard-codes `"zero_shot"` and leaves a commented-out loop as the template for sweeping across methods.

4. **`Simulator.py`** — MuJoCo wrapper exposing the ~25 tools listed in `Experiment.tool_mapping` (manipulation, queries, energy/momentum, collision, step, reset, and dynamic create/find/attach/delete). Each scene instantiates its own Simulator from the scene XML.

5. **`AgentClass.py`** — one class per provider (`OpenAIAgent`, `AnthropicAgent`, `GeminiAgent`, plus Together.ai-hosted `LlamaAgent`, `Llama3370BAgent`, `GemmaAgent`, `DeepSeekAgent`, `QwenAgent`, `MixtralAgent`, `KimiAgent`, `GLMAgent`). All expose `.interact(user_input)` and maintain their own `self.context` conversation history. Defaults pull model IDs from `config.py` (`OPENAI_MODEL`, `ANTHROPIC_MODEL`, `GEMINI_MODEL`, `DEEPSEEK_MODEL`, `QWEN_MODEL`, `KIMI_MODEL`, `GLM_MODEL`).

6. **`Data.py`** — post-run summarization. Appends a structured summary for the scene to the JSON log created by `JsonLogger`.

### Problem types

Scene JSON `metadata.problem_type` is one of:
- `comparison` — answer is an object id string, or comma-separated ids, or `"0"` meaning "all".
- `computation` — numeric answer; `_check_answer` tolerance is `0.1` (not 0.001 despite the README).
- `boolean` — `"0"` = true, `"1"` = false.

The LLM must return a JSON array of tool calls (including a final `{"tool": "answer", "parameters": {"answer": ...}}`); `Experiment.extract_json_response` parses them out of the model's reasoning text.

### Test outputs

Two parallel output streams per scene:
- `TestResults/{agent}/{scene_number}/summary_{timestamp}.txt` — human-readable experiment log created by `Experiment.__init__`.
- `TestResults/{agent}/{scene_number}/log_{timestamp}.json` — structured stdout+logging capture from `main.JsonLogger`.

`XMLFileCreation/{AgentType}/UpdatedXML/` holds per-agent edited scene XML variants used by some tool paths — don't conflate with the canonical `Scenes/Scene{N}/scene{N}.xml`.

## Gotchas

- **Scene 110 was replaced.** The original Scene 110 was a duplicate of Scene 102 (same "Horizontal Launch and Velocity Calculation" problem with a wrong ground-truth answer). It was removed and the old Scene 112 ("Collision Detection and Torque") was renumbered to Scene 110 to keep the sequence contiguous (7–111).
- **Scene ids are strings that look like integers.** `add_scenes` pushes `str(i)` for `i in [start_scene..end_scene]`; `Scene.__init__` does `int(self.scene_id)` to build the path. Non-integer scene ids will crash.
- **`config.py` model names may not correspond to real model IDs.** Treat the strings in `config.py` as the source of truth the user is *trying* to hit, and only "correct" them to known-good IDs if the user explicitly asks or a run is failing because of them.
- **`OPENROUTER_MODEL` in `config.py` is a trap.** There is no `OpenRouterAgent` class in `AgentClass.py` and the corresponding branch in `main.initialize_agent` is commented out (`main.py:152-153`). Setting `agents = ["OpenRouterAgent"]` will raise `ValueError: Unknown agent type`.
- **`config.prompting_methods` is currently dead.** `main.py` hard-codes `scene.set_prompt_method("zero_shot")` and also defines its own local `methods = [...]` list that nothing reads. To sweep methods, wire one of these lists into the `run_experiment()` call — the commented template at `main.py:238-240` shows the intended shape.
- Adding a new provider requires: (a) a new class in `AgentClass.py` exposing `.interact()`, (b) an `elif` branch in `main.initialize_agent`, (c) inclusion in the `isinstance(agent, (...))` tuple at the top of `Experiment.__init__` (otherwise it silently falls back to `gpt-4o-mini`).
- The `BUG_FIXES_*.md`, `BUGS.md`, and `FULL_SYSTEM_VALIDATION_REPORT.md` files in the root are historical engineering notes, not live documentation — check git blame / dates before trusting them.
