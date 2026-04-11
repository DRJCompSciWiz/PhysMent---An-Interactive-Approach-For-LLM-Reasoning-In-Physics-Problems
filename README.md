# PhysMent - Physics Reasoning Benchmark System

**PhysMent** is an AI-driven physics reasoning benchmark system that evaluates Large Language Model (LLM) capabilities in solving physics problems through interactive simulation. The system implements an agentic loop where an LLM (GPT-4o) receives physics problems as prompts, interacts with a MuJoCo physics simulator using predefined tools, and provides numerical answers that are validated against ground truth.

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/physment.git
cd physment
```

### 2. Python Installation

Ensure that you are using **Python 3.9 - 3.12**. You can manage Python versions using [pyenv](https://github.com/pyenv/pyenv):

```bash
pyenv install 3.12.0
pyenv local 3.12.0
```

### 3. Install Dependencies

Install the required packages using `pip`:

```bash
pip install mujoco==3.3.3
pip install openai anthropic together google-generativeai
pip install rich
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory and add your API keys:

```dotenv
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
TOGETHER_API_KEY=your_together_api_key
GOOGLE_API_KEY=your_google_api_key
```

### 5. Configure & Run the Pipeline

Manage testing parameters in `config.py` these will be used during runtime.

Run the main pipeline:

```bash
python main.py
```

---

## 📊 Results

| Task | GPT 4.1 | GPT 4.1 |  GPT 4o |  Claude | Gemini  | Gemma 2 | Llama 4 | DeepSeek|

|      |         |   mini  |   mini  |Haiku 3.5| 2.5 Pro |    9B   |   Scout |  R1     |
| ---- | ------- | ------- | ------- | ------- | ------- | ------- | ------- | ------- |
| 1    |         |         |         |         |         |         |         |         |
| 2    |         |         |         |         |         |         |         |         |
| 3    |         |         |         |         |         |         |         |         |
| 4    |         |         |         |         |         |         |         |         |
| 5    |         |         |         |         |         |         |         |         |
| 6    |         |         |         |         |         |         |         |         |
| 7    |         |         |         |         |         |         |         |         |
| 8    |         |         |         |         |         |         |         |         |
| 9    |         |         |         |         |         |         |         |         |

---

## 📚 BibTeX Reference

```bibtex
@misc{physment2025,
  author       = {S. Saravalle et al.},
  title        = {PhysMent: A Multi-Agent Physics Benchmarking Pipeline},
  year         = {2025},
  publisher    = {GitHub},
  journal      = {GitHub repository},
  howpublished = {\url{https://github.com/your-username/physment}}
}
```

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