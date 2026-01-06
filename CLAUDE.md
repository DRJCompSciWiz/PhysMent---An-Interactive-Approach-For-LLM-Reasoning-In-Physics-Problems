# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PhysMent** is an AI-driven physics reasoning benchmark system that evaluates LLM capabilities in solving physics problems through interactive simulation. The system implements an agentic loop where an LLM (GPT-4o) receives physics problems as prompts, interacts with a MuJoCo physics simulator using 19 predefined tools, and provides numerical answers that are validated against ground truth.

**Key Statistics**:
- 101 physics scenes covering mechanics, dynamics, energy, collisions, rotation, and oscillation
- 19 simulator tools for manipulation and querying
- Iterative experiment loop (default: 5 max iterations)
- Answer validation with 0.001 tolerance for numerical problems

## Development Commands

### Running Experiments

```bash
# Run the main experiment script
python main.py
```

The main script:
1. Iterates through scene IDs configured in `scene_ids` list (main.py:L46)
2. For each scene: initializes Simulator → Scene → Experimental
3. Generates scene-specific prompts with tools and permissions
4. Runs experiment loop until answer found or max_iterations reached
5. Outputs results to console and files

**Generated Output**:
- Console: LLM answer, correct answer, correctness evaluation
- `aggregated_results.json`: Experiment metrics for all scenes
- `experimentslog_{scene_id}_{timestamp}.txt`: Full conversation logs in TestResults/

### Environment Setup

1. Create `.env` file with OpenAI API key:
```bash
OPENAI_API_KEY="sk-..."
```

2. Install dependencies:
```bash
pip install mujoco openai python-dotenv numpy
```

**Optional dependencies** for alternative models:
```bash
pip install transformers torch huggingface_hub  # For Llama via HuggingFace
```

### Scene Configuration

**Scene Structure**: `Scenes/Scene{N}/`
- `scene{N}.json` - Metadata, objects, permissions, ground truth answer
- `scene{N}.xml` - MuJoCo XML physics definition

**Running Specific Scenes**:
```python
# In main.py:L46
scene_ids = ["Scene_1", "Scene_15", "Scene_100"]  # Modify this list
```

**Scene Naming Convention**:
- Scene IDs: `Scene_{N}` format (e.g., "Scene_101")
- Directory names: Inconsistent (Scene1, Scene 45, scene15, Scene 100)
- File names: Always lowercase `scene{N}.json` and `scene{N}.xml`

## Architecture

### Core Components (1,113 total lines)

#### **Experimental.py** (323 lines) - Experiment Orchestrator

**Purpose**: Manages the LLM-simulator interaction loop and validates answers.

**Key Responsibilities**:
- Initializes Simulator, Scene, and OpenAIAgent
- Orchestrates iterative experiment loop (default max: 5 iterations)
- Extracts JSON tool calls from LLM text responses
- Dynamically executes tools on simulator via tool_mapping
- Validates submitted answers against ground truth
- Generates timestamped experiment logs

**Core Methods**:
- `run_experiment()`: Main loop orchestrating LLM-simulator interaction
  - Resets simulator to initial state
  - Gets scene prompt from Scene.generate_prompt()
  - Iterates until answer found or timeout:
    1. Send prompt to LLM via OpenAIAgent.interact()
    2. Extract JSON from response via extract_json_response()
    3. Execute tools via execute_tool_calls()
    4. Check for answer submission
    5. Validate answer correctness
    6. Feed results back as next prompt
  - Returns experiment results dict

- `execute_tool_calls(tool_calls_json)`: Dynamic tool execution
  - Parses JSON array of tool calls
  - Looks up tool functions in tool_mapping
  - Executes with provided parameters
  - Catches and logs errors gracefully
  - Returns results with simulation time

- `extract_json_response(llm_output)`: JSON extraction from LLM text
  - Finds JSON array `[...]` or object `{...}` in response
  - Validates JSON syntax
  - Wraps objects in arrays if needed
  - Falls back to reset_sim on parse failure

**Tool Mapping** (18 tools):
```python
{
  "move_object": simulator.move_object,
  "get_position": simulator.get_position,
  "get_velocity": simulator.get_velocity,
  "get_acceleration": simulator.get_acceleration,
  "get_displacement": simulator.get_displacement,
  "apply_force": simulator.apply_force,
  "apply_torque": simulator.apply_torque,
  "set_velocity": simulator.set_velocity,
  "step": simulator.step,
  "detect_collision": simulator.detect_collision,
  "get_parameters": simulator.get_parameters,
  "compute_force": simulator.compute_force,
  "get_torque": simulator.get_torque,
  "get_momentum": simulator.get_momentum,
  "get_kinetic_energy": simulator.get_kinetic_energy,
  "get_potential_energy": simulator.get_potential_energy,
  "get_center_of_mass": simulator.get_center_of_mass,
  "get_angular_momentum": simulator.get_angular_momentum,
  "change_position": simulator.change_position,
  "quat_to_rot_matrix": simulator.quat_to_rot_matrix,
  "answer": lambda answer: {"result": answer}
}
```

**Experiment Results Format**:
```python
{
  'correct': bool,              # Answer matches ground truth
  'timeout': bool,              # Max iterations reached without answer
  'num_tool_calls': int,        # Total tool invocations
  'iterations': int,            # Iterations performed
  'answer_found': bool,         # LLM submitted answer (correct or not)
  'tool_usage': dict,           # Per-tool call counts
  'llm_answer': str/float,      # LLM's submitted answer
  'correct_answer': str/float   # Ground truth from JSON
}
```

#### **Scene.py** (292 lines) - Scene Management & Prompt Generation

**Purpose**: Loads physics scenes from JSON/XML and generates comprehensive LLM prompts.

**Key Responsibilities**:
- Loads scene metadata, objects, and permissions from JSON
- Constructs file paths based on terminal configuration (hardcoded Windows paths)
- Extracts object information and permission matrices
- Generates comprehensive prompts with tools, examples, and constraints
- Provides ground truth answers for validation

**Critical Methods**:
- `__init__(scene_id, simulator)`: Loads scene from JSON
  - Extracts scene number from scene_id
  - Constructs file path based on `terminal` variable (Scene.py:L23)
  - Loads JSON data if file exists
  - Calls metadata() and extract_objects_id_names_and_permissions()

- `metadata()`: Extracts scene metadata
  - `scene_name`: Human-readable scene title
  - `task`: Detailed problem description for LLM
  - `problem_type`: comparison|computation|boolean

- `extract_objects_id_names_and_permissions()`: Parses objects
  - Builds object_list: [{"object_id": "1", "name": "ball"}, ...]
  - Builds object_permissions: {"1": {"mass": true, "vel": false, ...}, ...}

- `generate_prompt()`: Creates comprehensive LLM prompt (5-10 KB)
  - Scene description and task
  - Available objects list with IDs and names
  - Permission matrix per object with explanations
  - 19 tool descriptions with arguments and return types
  - Example problem with full input/output demonstration
  - Problem-type-specific instructions
  - Final guidelines and formatting rules

- `get_correct_answer()`: Returns ground truth from JSON

**Path Configuration** (Scene.py:L23-37):
```python
self.terminal = "utkarsh"  # Change this for your environment

# Hardcoded Windows paths:
if self.terminal == "utkarsh":
    base_dir = r"C:\Users\inbox\OneDrive\Desktop\Algoverse-updated-pipeline\Scenes"
elif self.terminal == "robin":
    base_dir = r"C:\Users\robin\OneDrive\Documents\Algoverse\MuJoCo-Testing-Algoverse-main\Scenes"
# ... etc
```

**IMPORTANT**: These are Windows-specific hardcoded paths. For cross-platform compatibility, consider:
- Using relative paths from script location
- Environment variables
- Command-line arguments

#### **Simulator.py** (356 lines) - MuJoCo Physics Wrapper

**Purpose**: Wraps MuJoCo physics engine with high-level tools for LLM interaction.

**Key Responsibilities**:
- Initializes MuJoCo models from XML files
- Provides 19 physics manipulation and query tools
- Manages simulation state and time
- Renders visualization via passive viewer
- Handles coordinate frames and transformations

**Initialization** (`__init__`):
- Constructs XML path from scene_id via get_model_path()
- Loads MuJoCo model: `mujoco.MjModel.from_xml_path()`
- Creates data structure: `mujoco.MjData(model)`
- Launches passive viewer: `mujoco.viewer.launch_passive()`
- Stores initial positions: `self.start_pos = np.copy(data.qpos)`
- Zeros initial velocities: `data.qvel[:] = 0.0`
- Initializes time tracker: `self.time = 0`

**Physics Manipulation Tools**:
- `step(duration)`: Advance simulation by duration seconds
  - Calculates num_steps from timestep
  - Calls mujoco.mj_step() repeatedly
  - Syncs viewer after each step
  - Increments self.time accumulator

- `move_object(object_id, x, y, z)`: Set absolute position
  - Finds joint via mj_name2id with "{object_id}_joint"
  - Sets qpos at joint address
  - Calls mj_forward() to update state

- `apply_force(object_id, force_vector)`: Apply force
  - Sets xfrc_applied[:3] for linear force

- `apply_torque(object_id, torque_vector)`: Apply torque
  - Sets xfrc_applied[3:6] for angular torque

- `set_velocity(object_id, velocity_vector)`: Set velocity
  - Finds body via get_body_id()
  - Sets qvel for body's degrees of freedom

- `change_position(object_id, dx, dy, dz, in_world_frame)`: Relative movement
  - Adds delta to current qpos
  - Supports world frame or local frame

**Physics Query Tools**:
- `get_position(object_id)`: Returns position tuple + simulation time
- `get_velocity(object_id)`: Returns velocity vector [vx, vy, vz]
  - Normalizes object_id format (handles int, string, "object_N")
  - Uses body_dofadr to extract correct qvel segment
- `get_acceleration(object_id)`: Returns acceleration vector (not implemented in provided code)
- `get_displacement(object_id)`: Distance from start_pos
- `get_parameters(object_id)`: Returns mass, bounding_box, type
  - Has permission check (only tool with enforcement)
- `compute_force(object_id, mass)`: F = ma calculation
- `detect_collision(obj1_id, obj2_id)`: Checks contact data
- `get_kinetic_energy(object_id, mass)`: KE = 0.5 * m * v²
- `get_potential_energy(object_id, mass, gravity)`: PE = m * g * h
- `get_momentum(object_id, mass)`: p = m * v
- `get_torque(object_id)`: Returns torque from qfrc_applied
- `get_center_of_mass()`: Scene center of mass from subtree_com
- `get_angular_momentum(object_id, mass)`: L = m * ω
- `quat_to_rot_matrix(q)`: Quaternion to 3x3 rotation matrix

**Utility Methods**:
- `get_model_path(scene_id)`: Constructs XML path
  - Extracts scene number: `scene_id.split("_")[-1]`
  - Builds path: `Scenes/Scene{N}/scene{N}.xml`
  - Verifies file existence

- `get_body_id(object_id)`: Maps object_id to MuJoCo body ID
  - Uses mj_name2id with mjOBJ_BODY
  - Raises ValueError if not found

- `reset_sim()`: Reset to initial state
  - Copies start_pos to qpos
  - Zeros qvel
  - Calls mj_forward()
  - Resets time to 0

- `load_scene(scene_id)`: Dynamically load new scene
  - Closes existing viewer
  - Reinitializes with new XML

**Coordinate System**:
- X, Y: Horizontal planes
- Z: Vertical plane (up)
- Gravity: `[0, 0, -9.81]` by default

#### **OpenAIAgent.py** (57 lines) - LLM Interaction

**Purpose**: Simple wrapper for OpenAI ChatCompletion API with context management.

**Key Features**:
- Maintains full conversation history
- Uses GPT-4o model
- Includes detailed system prompt for physics reasoning

**System Prompt**:
```
You are an expert AI agent designed to solve physics problems by interacting
directly with a physics simulator. You have access to a variety of tools to
manipulate objects, query object states, and simulate physics progression.

Guidelines:
1) ALWAYS provide clear reasoning for every action
2) ALWAYS return actions formatted as valid JSON arrays of tool calls
3) Simulate time progression explicitly using the step function
4) Query object states to get context (not automatically provided)
5) Submit your answer only when confident, using the answer function
```

**Methods**:
- `__init__(api_key, system_prompt)`: Initialize with API key and instructions
- `interact(user_input)`: Send message and receive response
  - Appends user message to context
  - Calls openai.ChatCompletion.create() with GPT-4o
  - Appends assistant response to context
  - Returns AI message text
- `get_context()`: Returns full conversation history
- `clear_context()`: Resets to just system prompt

#### **main.py** (85 lines) - Entry Point

**Purpose**: Experiment runner script that orchestrates scene execution.

**Flow**:
1. Define scene_ids list (currently `["Scene_101"]`)
2. Initialize aggregated_results dict
3. For each scene_id:
   - Create Simulator(scene_id)
   - Create Scene(scene_id, simulator)
   - Generate and print prompt
   - Create Experimental(scene_id)
   - Run experiment: `results = experiment.run_experiment()`
   - Print answer summary
   - Store results in aggregated_results
4. Save aggregated_results to `aggregated_results.json`

### Data Flow

```
JSON Scene File (scene{N}.json, scene{N}.xml)
    ↓
Scene.__init__() loads metadata, objects, permissions
    ↓
Scene.generate_prompt() creates comprehensive LLM prompt
    ↓
OpenAIAgent.interact(prompt) → LLM response (reasoning + JSON tools)
    ↓
Experimental.extract_json_response() → Validated JSON array
    ↓
Experimental.execute_tool_calls() → Dynamic function invocation
    ↓
Simulator methods execute → Physics state changes
    ↓
Results dict {tool, parameters, result, sim_time}
    ↓
Check if "answer" tool called → Validate against ground truth
    ↓
If no answer: Feed results back to LLM for next iteration
If answer: Terminate and return experiment results
    ↓
Log to experimentslog_{scene_id}_{timestamp}.txt
Aggregate to aggregated_results.json
```

### Alternative LLM Implementations

**API/openAI-Backup.py** (22 lines):
- Legacy OpenAI Completion API
- Uses text-davinci-003 or GPT-4
- Status: Deprecated/backup

**API/HuggingFace-Llama.py** (30 lines):
- Local Llama-3.2-3B-Instruct inference
- Uses transformers + torch
- Requires GPU for reasonable performance
- Alternative to OpenAI API

## Scene Structure

### Scene JSON Format

```json
{
  "metadata": {
    "scene_name": "Human-readable title",
    "task": "Detailed problem description for LLM",
    "problem_type": "comparison|computation|boolean"
  },
  "answer": "Ground truth answer (string or number)",
  "expected_behavior": "How LLM should approach the problem",
  "reasoning": "Physics principle explanation",
  "number_of_objects": "Integer count as string",
  "objects": {
    "object_1": {"name": "ball", "object_id": "1"},
    "object_2": {"name": "ground", "object_id": "2"}
  },
  "object_permissions": {
    "object_1_permissions": {
      "type": true,
      "density": false,
      "mass": true,
      "pos": true,
      "vel": true,
      ...
    }
  }
}
```

### Problem Types

**comparison**: Which object satisfies the task?
- Answer format: Object ID(s) as string or comma-separated
- Special case: "0" if all objects satisfy
- Example: "Which sphere rolls faster down the incline?" → "2"

**computation**: Calculate a numerical result
- Answer format: Number rounded to nearest thousandths
- Example: "What is the acceleration of the system?" → "1.960"

**boolean**: True/false question
- Answer format: "0" for true, "1" for false
- Example: "Will the objects collide?" → "0"

### Object Permissions System (25 Categories)

Each object has granular access control for properties:

**Basic Properties**:
- `type`: Object type (sphere, plane, box, etc.)
- `name`: Human-readable name
- `density`: Material density
- `mass`: Object mass

**Geometric Properties**:
- `size`: Bounding box dimensions [length, width, height]
- `radius`: Sphere/cylinder radius

**Kinematic Properties**:
- `pos`: Position vector [x, y, z]
- `vel`: Linear velocity [vx, vy, vz]
- `acc`: Linear acceleration [ax, ay, az]
- `rot`: Rotation/orientation (quaternion or matrix)
- `angvel`: Angular velocity [wx, wy, wz]
- `angacc`: Angular acceleration

**Physical Properties**:
- `inertia`: Rotational inertia tensor
- `friction`: Static/dynamic friction coefficients
- `restitution`: Bounciness (0=inelastic, 1=elastic)
- `material`: Material type (metal, rubber, wood, etc.)

**Visual Properties**:
- `color`: RGB color values
- `texture`: Applied texture

**Simulation Properties**:
- `contact`: Contact information with other objects
- `geom`: Collision geometry
- `joint`: Joint configuration (if articulated)
- `qpos`: Generalized position state
- `qvel`: Generalized velocity state
- `xfrc_applied`: External forces and torques
- `torque`: Current acting torque
- `force`: Current net force
- `com`: Center of mass position
- `parentid`: Parent in hierarchy
- `childid`: Child bodies/links

**Permission Enforcement**:
- Defined in JSON but NOT enforced in most tools
- Only `get_parameters()` checks permissions
- System relies on semantic restriction (documented to LLM)
- LLM should respect permissions based on prompt instructions

### Example Scenes

**Scene 1: Solid vs Hollow Sphere**
- Task: Determine which sphere is hollow by rolling behavior
- Objects: solid_sphere, hollow_sphere, surface, incline
- Problem type: comparison
- Answer: "2" (hollow sphere)
- Physics: Moment of inertia affects rolling acceleration

**Scene 15: Pendulum Period Comparison**
- Task: Which pendulum has longer period?
- Objects: pendulum_short, pendulum_long, support
- Problem type: comparison
- Answer: "2" (longer pendulum)
- Physics: Period = 2π√(L/g)

**Scene 100: Mass-Spring Damping**
- Task: Determine critical damping coefficient
- Objects: mass, spring, damping
- Problem type: computation
- Answer: "3"
- Physics: Critical damping = 2√(km)

## Key Implementation Details

### Tool Call Format

LLM must return tool calls as JSON array:
```json
[
  {"tool": "move_object", "parameters": {"object_id": "object_1", "x": 0, "y": 10, "z": 0}},
  {"tool": "step", "parameters": {"duration": 0.5}},
  {"tool": "get_velocity", "parameters": {"object_id": "object_1"}},
  {"tool": "answer", "parameters": {"answer": "4.9"}}
]
```

**Object ID Format**: `"object_{N}"` where N is the object number
- Example: "object_1", "object_2"
- get_velocity() normalizes various formats

**Tool Execution Results**:
```json
{
  "tool": "get_velocity",
  "parameters": {"object_id": "object_1"},
  "result": {"velocity": [0.0, -4.9, 0.0]},
  "sim_time": 0.5
}
```

### Answer Validation Logic (Experimental.py:L236-249)

**Numerical Answers**:
```python
if isinstance(final_answer, (int, float)) or is_numeric_string(final_answer):
    final_float = float(final_answer)
    correct_float = float(correct_answer)
    correct = abs(final_float - correct_float) < 0.001  # Tolerance
```

**String Answers**:
```python
correct = str(final_answer).strip().lower() in str(correct_answer).strip().lower()
```

**Fallback**: String comparison if type conversion fails

### Simulation Time Management

- `step(duration)` progresses time by duration seconds
- `Simulator.time` accumulates total elapsed time
- Each tool result includes `"sim_time": float`
- Time only advances during `step()` calls
- Used for post-hoc analysis of simulation progression

### Error Handling

**JSON Parsing Errors**:
- LLM receives: "Error: Invalid JSON syntax for tool(s). Please try again with proper syntax."
- Iteration counter incremented
- Loop continues with error feedback

**Tool Execution Errors**:
- Caught in try/except blocks
- Result includes: `{"error": "error message"}`
- LLM receives error in next prompt
- Allows retry with corrected parameters

**Null Answers**:
- Logged as warning
- Marked as answer_found=False
- LLM prompted to retry with valid value

**Timeout**:
- After max_iterations without answer submission
- Experiment terminates
- Results include timeout=True flag

## Output Files

### aggregated_results.json

Located in project root. Contains results for all scenes run in current execution:

```json
{
  "Scene_101": {
    "correct": false,
    "timeout": false,
    "num_tool_calls": 8,
    "iterations": 6,
    "answer_found": true,
    "tool_usage": {
      "get_position": 3,
      "move_object": 2,
      "step": 2,
      "answer": 1
    },
    "llm_answer": "5.2",
    "correct_answer": "3"
  }
}
```

### Experiment Log Files

Located in `TestResults/{scene_name}/experimentslog_{scene_id}_{timestamp}.txt`

**Format**:
```
=== Experiment Log for Scene_101 ===

--- Iteration 1 ---
LLM Input Prompt Below:
[Full prompt with scene description, objects, permissions, tools, examples]

LLM Response Below:
[LLM reasoning + JSON tool calls]

--- Iteration 2 ---
...

=== Final Experiment Summary ===

--- Final Answer Submitted ---
LLM's Final Answer: 5.2
Correct Answer: 3
Is Correct: False
Answer Found: True
Timeout Occurred: False

--- Tool Usage Statistics ---
Total number of tool calls: 8
Tools used:
  - move_object: 2 times
  - step: 2 times
  - get_position: 3 times
  - answer: 1 times

--- Tool Call History ---
  [1] [{"tool": "move_object", ...}]
  [2] [{"tool": "step", ...}]
  ...

--- Tool Call Results ---
  [1] {"tool": "move_object", ..., "result": {"position": [0, 10, 0]}, "sim_time": 0}
  [2] {"tool": "step", ..., "result": null, "sim_time": 0.5}
  ...

Total number of iterations: 6
```

## Known Issues and Limitations

### Critical Issues

1. **Hardcoded Windows Paths** (Scene.py:L23-37)
   - Multiple developer-specific hardcoded paths
   - Windows-only (C:\ drive paths)
   - Breaks on Mac/Linux without modification
   - **Fix**: Use relative paths or environment variables

2. **Scene Directory Naming Inconsistency**
   - Some: "Scene1", "Scene 100" (with spaces)
   - Others: "scene15", "scene41" (lowercase)
   - May cause path resolution failures
   - **Fix**: Standardize to single format

3. **Permission System Not Enforced**
   - Permissions defined but only checked in get_parameters()
   - Other tools don't validate permissions
   - Relies on LLM respecting semantic restrictions
   - **Fix**: Add permission checks to all query tools

4. **MuJoCo Viewer Dependency**
   - Launches passive viewer on initialization
   - Fails in headless/server environments
   - No error handling for viewer failures
   - **Fix**: Make viewer optional or use headless mode

5. **No Experiment Aggregation**
   - Each run overwrites aggregated_results.json
   - No historical comparison across runs
   - TestResults logs not parsed or analyzed
   - **Fix**: Append results with timestamps, add analysis scripts

### Minor Issues

6. **Single Model Hardcoded**: OpenAIAgent only supports GPT-4o
7. **No Progress Indicators**: Long experiments have no status updates
8. **Limited Error Recovery**: Some errors terminate experiment
9. **Memory Growth**: Conversation context grows unbounded
10. **No Scene Validation**: Invalid JSON/XML not caught early

## Extensibility Points

### Adding New LLM Models

Create new agent class in `API/`:
```python
class CustomLLMAgent:
    def __init__(self, api_key):
        # Initialize your model
        pass

    def interact(self, user_input):
        # Return model response as string
        pass
```

Update `Experimental.__init__()` to use new agent.

### Adding New Simulator Tools

1. Implement method in `Simulator.py`:
```python
def get_angular_velocity(self, object_id: str) -> dict:
    # Implementation
    return {"angular_velocity": [wx, wy, wz]}
```

2. Add to tool_mapping in `Scene.py` and `Experimental.py`:
```python
self.tool_mapping["get_angular_velocity"] = self.simulator.get_angular_velocity
```

3. Add tool description to Scene.generate_prompt() tools list:
```python
{"name": "get_angular_velocity",
 "description": "returns angular velocity of object",
 "arguments": {"object_id": "str"},
 "return type": {"angular_velocity": "list[float]"}}
```

### Creating New Scenes

1. Create directory: `Scenes/Scene{N}/`
2. Create `scene{N}.json` with required fields:
   - metadata: scene_name, task, problem_type
   - answer: ground truth
   - number_of_objects
   - objects: object definitions
   - object_permissions: permission matrices
3. Create `scene{N}.xml` with MuJoCo model definition
4. Add `Scene_{N}` to scene_ids in main.py

### Analyzing Results

Parse experiment logs:
```python
import json
import glob

# Load all experiment results
logs = glob.glob("TestResults/*/experimentslog_*.txt")
for log_path in logs:
    with open(log_path) as f:
        content = f.read()
        # Parse iterations, tool usage, correctness
        # Aggregate statistics
```

## Development Guidelines

### Code Conventions

- **Object IDs**: Use `"object_{N}"` format consistently
- **Error Handling**: Return `{"error": "message"}` dicts, don't raise
- **Logging**: Use logging module, not print statements
- **Type Hints**: Add type hints to new functions
- **Docstrings**: Document all public methods

### Testing Approach

1. **Unit Test Individual Tools**: Test each Simulator method in isolation
2. **Integration Test Scenes**: Run experiments on known scenes
3. **Validate Answers**: Check correctness across all 101 scenes
4. **Performance Profile**: Measure tool execution times
5. **Error Injection**: Test error handling with malformed inputs

### Debugging Tips

1. **Check Experiment Logs**: Full conversation in TestResults/
2. **Enable Debug Logging**: Set `logging.basicConfig(level=logging.DEBUG)`
3. **Inspect Tool Results**: Each result includes sim_time and full output
4. **Verify Scene Paths**: Check terminal variable matches your system
5. **Test JSON Parsing**: Validate LLM JSON output manually

## Quick Reference

### Common File Locations

- Entry point: `main.py`
- Core logic: `Experimental.py`
- Prompt generation: `Scene.py`
- Physics engine: `Simulator.py`
- LLM interface: `OpenAIAgent.py`
- Scene data: `Scenes/Scene{N}/scene{N}.json`
- Scene physics: `Scenes/Scene{N}/scene{N}.xml`
- Experiment logs: `TestResults/{scene}/experimentslog_*.txt`
- Aggregated results: `aggregated_results.json` (project root)

### Key Constants

- Max iterations: 5 (Experimental.py:L18)
- Answer tolerance: 0.001 (Experimental.py:L243)
- Model: "gpt-4o" (OpenAIAgent.py:L38)
- Gravity: [0, 0, -9.81] (MuJoCo XML files)
- Total scenes: 101
- Total tools: 19

### Tool Categories

**Manipulation**: move_object, apply_force, apply_torque, set_velocity, change_position
**Time**: step
**Position**: get_position, get_displacement
**Motion**: get_velocity, get_acceleration
**Dynamics**: compute_force, get_momentum, get_kinetic_energy, get_potential_energy
**Rotation**: get_torque, get_angular_momentum, quat_to_rot_matrix
**System**: get_parameters, detect_collision, get_center_of_mass
**Answer**: answer

---

**Last Updated**: January 6, 2026
**Codebase Size**: 1,113 lines (core files)
**Total Scenes**: 101 physics problems
**Active Model**: OpenAI GPT-4o
