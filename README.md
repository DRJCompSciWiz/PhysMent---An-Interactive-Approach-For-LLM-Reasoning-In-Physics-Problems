# PhysMent - Physics Reasoning Benchmark System

**PhysMent** is an AI-driven physics reasoning benchmark system that evaluates Large Language Model (LLM) capabilities in solving physics problems through interactive simulation. The system implements an agentic loop where an LLM (GPT-4o) receives physics problems as prompts, interacts with a MuJoCo physics simulator using predefined tools, and provides numerical answers that are validated against ground truth.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Usage](#usage)
- [Known Issues and Bugs](#known-issues-and-bugs)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

PhysMent consists of 101 physics scenes covering mechanics, dynamics, energy, collisions, rotation, and oscillation. Each scene presents a physics problem that an LLM must solve by:

1. Receiving a detailed prompt describing the scene, objects, and task
2. Interacting with a MuJoCo physics simulator using 19 available tools
3. Iteratively exploring the simulation to understand the physics
4. Submitting a final answer that is validated against ground truth

The system tracks tool usage, iterations, correctness, and generates detailed experiment logs for analysis.

## Features

- **101 Physics Scenes**: Diverse problems covering multiple physics domains
- **19 Simulator Tools**: Comprehensive set of tools for manipulation and querying
- **Iterative Experiment Loop**: Default 5 max iterations with configurable limits
- **Answer Validation**: Automatic validation with 0.001 tolerance for numerical problems
- **Detailed Logging**: Full conversation logs and experiment statistics
- **Multiple Problem Types**: Comparison, computation, and boolean problems

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for GPT-4o)
- MuJoCo physics engine

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd PhysMent-1
```

### Step 2: Install Dependencies

```bash
pip install mujoco openai python-dotenv numpy
```

**Optional dependencies** for alternative models:
```bash
pip install transformers torch huggingface_hub  # For Llama via HuggingFace
```

### Step 3: Configure Environment

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY="sk-your-api-key-here"
```

### Step 4: Fix Path Configuration

**IMPORTANT**: The codebase currently has hardcoded Windows paths. Before running, you must update `Scene.py`:

1. Open `Scene.py`
2. Find line 23: `self.terminal = "utkarsh"`
3. Either:
   - Set it to match your system (if you're one of the developers)
   - Or modify the path construction to use relative paths (see [Known Issues](#known-issues-and-bugs))

## Quick Start

### Running a Single Scene

1. Edit `main.py` and set the scene ID:
```python
scene_ids = ["Scene_1"]  # Change to your desired scene
```

2. Run the experiment:
```bash
python main.py
```

3. Check results:
   - Console output: Answer summary and correctness
   - `aggregated_results.json`: Experiment metrics
   - `TestResults/Scene{N}/experimentslog_*.txt`: Full conversation logs

### Running Multiple Scenes

```python
scene_ids = ["Scene_1", "Scene_15", "Scene_100"]
```

## Architecture

### Core Components

The system consists of five main components:

#### 1. **main.py** - Entry Point
- Orchestrates scene execution
- Manages scene iteration
- Aggregates results to JSON

#### 2. **Experimental.py** - Experiment Orchestrator
- Manages LLM-simulator interaction loop
- Extracts and executes tool calls from LLM responses
- Validates answers against ground truth
- Generates experiment logs

**Key Methods:**
- `run_experiment()`: Main loop orchestrating LLM-simulator interaction
- `execute_tool_calls()`: Dynamic tool execution
- `extract_json_response()`: JSON extraction from LLM text

#### 3. **Scene.py** - Scene Management & Prompt Generation
- Loads scene metadata, objects, and permissions from JSON
- Generates comprehensive LLM prompts
- Provides ground truth answers

**Key Methods:**
- `__init__()`: Loads scene from JSON
- `generate_prompt()`: Creates comprehensive LLM prompt (5-10 KB)
- `get_correct_answer()`: Returns ground truth from JSON

#### 4. **Simulator.py** - MuJoCo Physics Wrapper
- Wraps MuJoCo physics engine with high-level tools
- Provides 19 physics manipulation and query tools
- Manages simulation state and time
- Renders visualization via passive viewer

**Key Methods:**
- `step(duration)`: Advance simulation by duration seconds
- `move_object()`: Set absolute position
- `apply_force()`: Apply force to object
- `get_velocity()`: Get velocity vector
- `get_position()`: Get position and time
- And 14 more tools...

#### 5. **OpenAIAgent.py** - LLM Interaction
- Simple wrapper for OpenAI ChatCompletion API
- Maintains full conversation history
- Uses GPT-4o model

**Key Methods:**
- `interact(user_input)`: Send message and receive response
- `get_context()`: Returns full conversation history
- `clear_context()`: Resets to just system prompt

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

## Usage

### Scene Structure

Scenes are located in `Scenes/Scene{N}/`:
- `scene{N}.json` - Metadata, objects, permissions, ground truth answer
- `scene{N}.xml` - MuJoCo XML physics definition

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
      "mass": true,
      "vel": true,
      ...
    }
  }
}
```

### Problem Types

1. **comparison**: Which object satisfies the task?
   - Answer format: Object ID(s) as string or comma-separated
   - Special case: "0" if all objects satisfy

2. **computation**: Calculate a numerical result
   - Answer format: Number rounded to nearest thousandths

3. **boolean**: True/false question
   - Answer format: "0" for true, "1" for false

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

### Available Tools

**Manipulation Tools:**
- `move_object(object_id, x, y, z)`: Set absolute position
- `apply_force(object_id, force_vector)`: Apply force
- `apply_torque(object_id, torque_vector)`: Apply torque
- `set_velocity(object_id, velocity_vector)`: Set velocity
- `change_position(object_id, dx, dy, dz, in_world_frame)`: Relative movement

**Time Control:**
- `step(duration)`: Advance simulation by duration seconds

**Query Tools:**
- `get_position(object_id)`: Returns position tuple + simulation time
- `get_velocity(object_id)`: Returns velocity vector [vx, vy, vz]
- `get_displacement(object_id)`: Distance from start position
- `get_parameters(object_id)`: Returns mass, bounding_box, type
- `detect_collision(obj1_id, obj2_id)`: Checks contact data
- `get_kinetic_energy(object_id, mass)`: KE = 0.5 * m * v²
- `get_potential_energy(object_id, mass, gravity)`: PE = m * g * h
- `get_momentum(object_id, mass)`: p = m * v
- `get_torque(object_id)`: Returns torque
- `get_center_of_mass()`: Scene center of mass
- `get_angular_momentum(object_id, mass)`: L = m * ω
- `quat_to_rot_matrix(q)`: Quaternion to 3x3 rotation matrix
- `compute_force(object_id, mass)`: F = ma calculation

**Answer Submission:**
- `answer(answer)`: Submit final answer for validation

## Known Issues and Bugs

### 🔴 Critical Issues

#### 1. **Missing `get_acceleration()` Implementation**
**Status**: ❌ NOT WORKING

**Location**: `Simulator.py`

**Problem**: 
- `get_acceleration()` is referenced in tool mappings (`Scene.py:118`, `Experimental.py:43`)
- Listed in tool descriptions in prompts (`Scene.py:173`)
- Called by `compute_force()` (`Simulator.py:133`)
- **BUT**: The method is not implemented in `Simulator.py`

**Impact**: 
- `compute_force()` will fail with `AttributeError` when called
- LLM may try to call `get_acceleration()` directly, causing errors
- Tool is advertised but non-functional

**Error Example**:
```python
AttributeError: 'Simulator' object has no attribute 'get_acceleration'
```

**Fix Required**:
```python
def get_acceleration(self, object_id: str) -> dict:
    """Returns the current acceleration vector of an object."""
    try:
        object_id = str(object_id)
        body_id = self.get_body_id(object_id)
        # Calculate acceleration from velocity changes or use MuJoCo's qacc
        dof_adr = self.model.body_dofadr[body_id]
        acc = self.data.qacc[dof_adr:dof_adr + 3]  # Linear acceleration
        return {"x": float(acc[0]), "y": float(acc[1]), "z": float(acc[2])}
    except Exception as e:
        return {"error": str(e)}
```

---

#### 2. **Hardcoded Windows Paths**
**Status**: ❌ NOT WORKING ON MAC/LINUX

**Location**: `Scene.py:23-37`

**Problem**:
- Paths are hardcoded for Windows (`C:\Users\...`)
- Only works for specific developers (utkarsh, robin, abhinav, sid)
- Breaks on Mac/Linux or other Windows users
- No fallback to relative paths

**Current Code**:
```python
self.terminal = "utkarsh"  # Hardcoded
if self.terminal == "utkarsh":
    base_dir = r"C:\Users\inbox\OneDrive\Desktop\Algoverse-updated-pipeline\Scenes"
```

**Impact**: 
- File not found errors on non-Windows systems
- Cannot run without manual path modification
- Not portable across different machines

**Fix Required**: Use relative paths based on script location:
```python
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
scenes_dir = os.path.join(script_dir, "Scenes")
self.file_path = os.path.join(scenes_dir, f"Scene{self.scene_number}", f"scene{self.scene_number}.json")
```

---

#### 3. **Bug in `get_parameters()` Method**
**Status**: ❌ NOT WORKING

**Location**: `Simulator.py:231-234`

**Problem**:
- Tries to use `object_id` (a string like "object_1" or "1") as an array index
- MuJoCo arrays require integer body IDs, not string object IDs

**Current Code**:
```python
return {
    "mass": float(self.model.body_mass[object_id]),  # ❌ object_id is string!
    "bounding_box": self.model.body_inertia[object_id].tolist(),  # ❌
    "type": int(self.model.body_parentid[object_id])  # ❌
}
```

**Error Example**:
```
TypeError: only integers, slices (`:`), ellipsis (`...`), numpy.newaxis (`None`) and integer or boolean arrays are valid indices
```

**Fix Required**:
```python
def get_parameters(self, object_id: str) -> dict:
    object_id = str(object_id)
    body_id = self.get_body_id(object_id)  # Convert to body ID first
    return {
        "mass": float(self.model.body_mass[body_id]),
        "bounding_box": self.model.body_inertia[body_id].tolist(),
        "type": int(self.model.body_parentid[body_id])
    }
```

---

#### 4. **Outdated OpenAI API Usage**
**Status**: ⚠️ DEPRECATED (may break in future)

**Location**: `OpenAIAgent.py:37`

**Problem**:
- Uses deprecated `openai.ChatCompletion.create()`
- Should use `openai.ChatCompletion.create()` from `openai` v0.x OR
- Should use `openai.chat.completions.create()` from `openai` v1.x+

**Current Code**:
```python
response = openai.ChatCompletion.create(
    model="gpt-4o",
    messages=self.context,
    api_key=self.api_key
)
```

**Impact**:
- May break with newer OpenAI library versions
- `api_key` parameter deprecated in favor of environment variable or client initialization

**Fix Required** (for OpenAI v1.x+):
```python
from openai import OpenAI

class OpenAIAgent:
    def __init__(self, api_key, ...):
        self.client = OpenAI(api_key=api_key)
        ...
    
    def interact(self, user_input):
        self.context.append({"role": "user", "content": user_input})
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=self.context
        )
        ai_message = response.choices[0].message.content
        ...
```

---

#### 5. **Scene Directory Naming Inconsistency**
**Status**: ⚠️ POTENTIAL ISSUES

**Location**: Throughout `Scenes/` directory

**Problem**:
- Inconsistent naming: "Scene1", "Scene 100" (with spaces), "scene15" (lowercase), "Scene 45" (with space)
- Path construction assumes `Scene{N}` format but reality varies
- May cause file not found errors

**Examples**:
- `Scene1/` vs `Scene 100/` vs `scene15/` vs `Scene 45/`

**Impact**:
- Some scenes may fail to load
- Path resolution may be incorrect

**Fix Required**: Standardize all scene directories to single format (e.g., `Scene{N}`)

---

#### 6. **MuJoCo Viewer Dependency**
**Status**: ⚠️ BREAKS IN HEADLESS ENVIRONMENTS

**Location**: `Simulator.py:33`

**Problem**:
- Launches passive viewer on initialization
- Fails in headless/server environments (no display)
- No error handling for viewer failures

**Current Code**:
```python
self.viewer = mujoco.viewer.launch_passive(self.model, self.data)
```

**Impact**:
- Cannot run on servers without displays
- May crash in Docker containers without X11
- Blocks execution if viewer fails

**Fix Required**: Make viewer optional:
```python
try:
    self.viewer = mujoco.viewer.launch_passive(self.model, self.data)
except Exception as e:
    logging.warning(f"Could not launch viewer: {e}. Running in headless mode.")
    self.viewer = None
```

---

#### 7. **Permission System Not Enforced**
**Status**: ⚠️ SECURITY/LOGIC ISSUE

**Location**: `Simulator.py` (most tools)

**Problem**:
- Permissions defined in JSON but only checked in `get_parameters()`
- Other tools don't validate permissions
- Relies on LLM respecting semantic restrictions

**Impact**:
- LLM can access restricted object properties
- Permissions are advisory, not enforced
- May lead to incorrect problem solving

**Fix Required**: Add permission checks to all query tools:
```python
def get_velocity(self, object_id: str) -> dict:
    # Check permissions
    if not self._check_permission(object_id, "vel"):
        return {"error": "Permission denied: vel access not allowed"}
    # ... rest of implementation
```

---

### 🟡 Minor Issues

#### 8. **No Experiment Aggregation**
- Each run overwrites `aggregated_results.json`
- No historical comparison across runs
- TestResults logs not parsed or analyzed

#### 9. **Single Model Hardcoded**
- OpenAIAgent only supports GPT-4o
- No easy way to switch models

#### 10. **No Progress Indicators**
- Long experiments have no status updates
- No ETA or progress bar

#### 11. **Memory Growth**
- Conversation context grows unbounded
- May hit token limits for long experiments

#### 12. **Limited Error Recovery**
- Some errors terminate experiment
- No retry logic for transient failures

#### 13. **No Scene Validation**
- Invalid JSON/XML not caught early
- Errors only appear at runtime

## Troubleshooting

### Issue: "File not found" errors

**Cause**: Hardcoded Windows paths in `Scene.py`

**Solution**: 
1. Open `Scene.py`
2. Change line 23 to use relative paths (see Fix #2 above)
3. Or set `self.terminal` to match your system if you're a developer

### Issue: "AttributeError: 'Simulator' object has no attribute 'get_acceleration'"

**Cause**: Missing `get_acceleration()` implementation

**Solution**: Add the method to `Simulator.py` (see Fix #1 above)

### Issue: "TypeError: only integers... are valid indices" in `get_parameters()`

**Cause**: Using string object_id as array index

**Solution**: Fix `get_parameters()` to use `get_body_id()` first (see Fix #3 above)

### Issue: "Body with name '1' not found in the scene"

**Cause**: Object ID format mismatch - LLM using numeric ID instead of "object_N"

**Solution**: This is expected behavior. The LLM should use "object_1" format. The error is correctly returned and the LLM should retry with correct format.

### Issue: Viewer fails to launch

**Cause**: Running in headless environment or missing display

**Solution**: Make viewer optional (see Fix #6 above) or run with `DISPLAY` environment variable set

### Issue: OpenAI API errors

**Cause**: Outdated API usage or invalid API key

**Solution**: 
1. Check API key in `.env` file
2. Update `OpenAIAgent.py` to use latest OpenAI library (see Fix #4 above)

## Contributing

### Adding New Tools

1. Implement method in `Simulator.py`
2. Add to `tool_mapping` in `Scene.py` and `Experimental.py`
3. Add tool description to `Scene.generate_prompt()` tools list

### Creating New Scenes

1. Create directory: `Scenes/Scene{N}/`
2. Create `scene{N}.json` with required fields
3. Create `scene{N}.xml` with MuJoCo model definition
4. Add `Scene_{N}` to scene_ids in `main.py`

### Testing

1. Run individual scenes to verify functionality
2. Check experiment logs in `TestResults/`
3. Validate answers against ground truth

## License

[Add license information here]

## Contact

[Add contact information here]

---

**Last Updated**: January 2025
**Codebase Size**: ~1,113 lines (core files)
**Total Scenes**: 101 physics problems
**Active Model**: OpenAI GPT-4o
