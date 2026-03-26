# Bug Report and Issues Documentation

This document provides detailed technical information about bugs and issues in the PhysMent codebase.

## Critical Bugs (Must Fix)

### Bug #1: Missing `get_acceleration()` Implementation

**Severity**: 🔴 CRITICAL - Breaks `compute_force()` and advertised functionality

**Files Affected**:
- `Simulator.py` (missing method)
- `Scene.py:118` (tool mapping)
- `Scene.py:173` (tool description in prompt)
- `Experimental.py:43` (tool mapping)
- `Simulator.py:133` (called by `compute_force()`)

**Current State**:
```python
# Simulator.py:130-138
def compute_force(self, object_id: str, mass: float) -> dict:
    """Compute the force on an object using F = ma."""
    object_id = str(object_id)
    acceleration = self.get_acceleration(object_id)  # ❌ Method doesn't exist!
    return {
        "x": mass * acceleration["x"],
        "y": mass * acceleration["y"],
        "z": mass * acceleration["z"]
    }
```

**Error When Triggered**:
```python
AttributeError: 'Simulator' object has no attribute 'get_acceleration'
```

**Impact**:
1. `compute_force()` will always fail
2. LLM may try to call `get_acceleration()` directly (it's in the tool list)
3. Tool is advertised to LLM but non-functional
4. Breaks F=ma calculations

**Proposed Fix**:
```python
def get_acceleration(self, object_id: str) -> dict:
    """
    Returns the current acceleration vector of an object.
    
    Args:
        object_id (str): Object identifier (e.g., "object_1")
    
    Returns:
        dict: Acceleration vector with keys "x", "y", "z" or {"error": "message"}
    """
    try:
        object_id = str(object_id)
        body_id = self.get_body_id(object_id)
        
        # Get degrees of freedom address for this body
        dof_adr = self.model.body_dofadr[body_id]
        
        # Extract linear acceleration from qacc (generalized acceleration)
        acc = self.data.qacc[dof_adr:dof_adr + 3]
        
        return {
            "x": float(acc[0]),
            "y": float(acc[1]),
            "z": float(acc[2])
        }
    except Exception as e:
        logging.error(f"Error in get_acceleration for object_id='{object_id}': {str(e)}")
        return {"error": str(e)}
```

**Testing**:
```python
# Test case
simulator = Simulator("Scene_1")
acc = simulator.get_acceleration("object_1")
assert "x" in acc and "y" in acc and "z" in acc
assert isinstance(acc["x"], float)
```

---

### Bug #2: `get_parameters()` Uses String as Array Index

**Severity**: 🔴 CRITICAL - Always fails when called

**Files Affected**:
- `Simulator.py:223-235`

**Current Code**:
```python
def get_parameters(self, object_id: str) -> dict:
    """Retrieve parameters of an object, respecting scene-defined permissions."""
    object_id = str(object_id)
    permissions = getattr(self, 'permissions', {}).get(object_id, {})
    if not permissions.get("get_parameters", True):
        raise PermissionError(f"Access to parameters of object with ID {object_id} is not allowed.")

    return {
        "mass": float(self.model.body_mass[object_id]),  # ❌ object_id is string!
        "bounding_box": self.model.body_inertia[object_id].tolist(),  # ❌
        "type": int(self.model.body_parentid[object_id])  # ❌
    }
```

**Error When Triggered**:
```
TypeError: only integers, slices (`:`), ellipsis (`...`), numpy.newaxis (`None`) and integer or boolean arrays are valid indices
```

**Root Cause**:
- `object_id` is a string (e.g., "object_1" or "1")
- MuJoCo arrays (`body_mass`, `body_inertia`, `body_parentid`) require integer indices
- Need to convert `object_id` to body ID first using `get_body_id()`

**Evidence from Logs**:
```
TestResults/Scene1/experimentslog_Scene_1_20250413_194313.txt:375
'result': {'error': 'only integers, slices (`:`), ellipsis (`...`), numpy.newaxis (`None`) and integer or boolean arrays are valid indices'}
```

**Proposed Fix**:
```python
def get_parameters(self, object_id: str) -> dict:
    """Retrieve parameters of an object, respecting scene-defined permissions."""
    object_id = str(object_id)
    permissions = getattr(self, 'permissions', {}).get(object_id, {})
    if not permissions.get("get_parameters", True):
        raise PermissionError(f"Access to parameters of object with ID {object_id} is not allowed.")

    # Convert object_id to body_id first
    body_id = self.get_body_id(object_id)
    
    return {
        "mass": float(self.model.body_mass[body_id]),
        "bounding_box": self.model.body_inertia[body_id].tolist(),
        "type": int(self.model.body_parentid[body_id])
    }
```

**Testing**:
```python
# Test case
simulator = Simulator("Scene_1")
params = simulator.get_parameters("object_1")
assert "mass" in params
assert "bounding_box" in params
assert "type" in params
```

---

### Bug #3: Hardcoded Windows Paths

**Severity**: 🔴 CRITICAL - Breaks on Mac/Linux and non-developer machines

**Files Affected**:
- `Scene.py:23-37`

**Current Code**:
```python
self.terminal = "utkarsh"  # Hardcoded developer name

if self.terminal == "utkarsh":
    base_dir = r"C:\Users\inbox\OneDrive\Desktop\Algoverse-updated-pipeline\Scenes"
elif self.terminal == "robin":
    base_dir = r"C:\Users\robin\OneDrive\Documents\Algoverse\MuJoCo-Testing-Algoverse-main\Scenes"
elif self.terminal == "abhinav":
    base_dir = r"C:\Users\epicg\Algoverse\MuJoCo-Testing-Algoverse\Scenes"
elif self.terminal == "sid":
    base_dir = r"C:\Users\siddh\OneDrive\Desktop\Algoverse\MuJoCo-Testing-Algoverse\Scenes"
```

**Problems**:
1. Windows-only paths (`C:\Users\...`)
2. Only works for 4 specific developers
3. Breaks on Mac/Linux (different path separators)
4. Not portable
5. Requires manual code modification for each user

**Impact**:
- File not found errors on non-Windows systems
- Cannot run without manual path modification
- Not usable by new developers/users

**Proposed Fix**:
```python
def __init__(self, scene_id: str, simulator: Simulator):
    self.scene_id = scene_id
    self.simulator = simulator
    self.scene_number = int(scene_id.split("_")[-1])
    
    # Use relative paths based on script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scenes_dir = os.path.join(script_dir, "Scenes")
    
    # Handle inconsistent scene directory naming
    # Try multiple possible formats
    possible_paths = [
        os.path.join(scenes_dir, f"Scene{self.scene_number}", f"scene{self.scene_number}.json"),
        os.path.join(scenes_dir, f"Scene {self.scene_number}", f"scene{self.scene_number}.json"),
        os.path.join(scenes_dir, f"scene{self.scene_number}", f"scene{self.scene_number}.json"),
    ]
    
    self.file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            self.file_path = path
            break
    
    if not self.file_path:
        # Fallback: use first format and let error be raised
        self.file_path = possible_paths[0]
    
    print("Looking for file at:", self.file_path)
    
    # Load the JSON data if it exists
    if os.path.exists(self.file_path):
        print("File successfully found")
        with open(self.file_path, "r") as file:
            self.data = json.load(file)
    else:
        print(f"File not found at: {self.file_path}")
        print(f"Tried paths: {possible_paths}")
        self.data = None
```

**Alternative Fix** (Environment Variable):
```python
# Use environment variable for custom paths
scenes_dir = os.getenv("PHYSMENT_SCENES_DIR")
if scenes_dir:
    base_dir = scenes_dir
else:
    # Default to relative path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(script_dir, "Scenes")
```

---

## High Priority Issues

### Issue #4: Outdated OpenAI API Usage

**Severity**: 🟡 HIGH - May break with library updates

**Files Affected**:
- `OpenAIAgent.py:37-41`

**Current Code**:
```python
response = openai.ChatCompletion.create(
    model="gpt-4o",
    messages=self.context,
    api_key=self.api_key
)
```

**Problems**:
1. Uses deprecated `openai.ChatCompletion.create()` (v0.x style)
2. `api_key` parameter deprecated in v1.x+
3. May break with newer OpenAI library versions

**Proposed Fix** (OpenAI v1.x+):
```python
from openai import OpenAI

class OpenAIAgent:
    def __init__(self, api_key, system_prompt=...):
        self.client = OpenAI(api_key=api_key)
        self.context = [{"role": "system", "content": system_prompt}]
    
    def interact(self, user_input):
        self.context.append({"role": "user", "content": user_input})
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=self.context
        )
        
        ai_message = response.choices[0].message.content
        self.context.append({"role": "assistant", "content": ai_message})
        return ai_message
```

**Migration Notes**:
- Install: `pip install openai>=1.0.0`
- Remove `api_key` parameter from `create()` call
- Use `OpenAI()` client initialization instead

---

### Issue #5: Scene Directory Naming Inconsistency

**Severity**: 🟡 HIGH - Causes path resolution failures

**Problem**:
Scene directories use inconsistent naming:
- `Scene1/` (no space, capital S)
- `Scene 100/` (with space, capital S)
- `scene15/` (lowercase)
- `Scene 45/` (with space)

**Impact**:
- Path construction assumes `Scene{N}` format
- Some scenes may fail to load
- Inconsistent behavior

**Evidence**:
```
Scenes/Scene1/
Scenes/Scene 100/
Scenes/scene15/
Scenes/Scene 45/
```

**Proposed Fix**:
1. Standardize all directories to `Scene{N}/` format
2. Update path construction to handle multiple formats (see Bug #3 fix)
3. Add validation script to check consistency

**Script to Standardize**:
```python
import os
import shutil

scenes_dir = "Scenes"
for item in os.listdir(scenes_dir):
    old_path = os.path.join(scenes_dir, item)
    if os.path.isdir(old_path):
        # Extract number
        number = ''.join(filter(str.isdigit, item))
        if number:
            new_name = f"Scene{number}"
            new_path = os.path.join(scenes_dir, new_name)
            if old_path != new_path:
                print(f"Renaming {item} -> {new_name}")
                shutil.move(old_path, new_path)
```

---

### Issue #6: MuJoCo Viewer Dependency

**Severity**: 🟡 HIGH - Breaks in headless environments

**Files Affected**:
- `Simulator.py:33`

**Current Code**:
```python
self.viewer = mujoco.viewer.launch_passive(self.model, self.data)
```

**Problems**:
1. Requires display/X11
2. Fails in Docker containers without display
3. Fails on headless servers
4. No error handling

**Impact**:
- Cannot run on servers without displays
- Blocks execution if viewer fails
- Not suitable for batch processing

**Proposed Fix**:
```python
def __init__(self, scene_id: str, headless: bool = False):
    self.scene_id = scene_id
    self.model_path = self.get_model_path(scene_id)
    
    try:
        self.model = mujoco.MjModel.from_xml_path(self.model_path)
        self.data = mujoco.MjData(self.model)
        
        # Make viewer optional
        self.viewer = None
        if not headless:
            try:
                self.viewer = mujoco.viewer.launch_passive(self.model, self.data)
            except Exception as e:
                logging.warning(f"Could not launch viewer: {e}. Running in headless mode.")
        
        self.start_pos = np.copy(self.data.qpos)
        self.time = 0
        self.prev_velocities = {}
        self.data.qvel[:] = 0.0
        
    except Exception as e:
        logging.error(f"MuJoCo initialization failed: {e}")
        raise

def render(self):
    """Render the current simulation frame."""
    if self.viewer is not None:
        self.viewer.sync()
        return self.viewer.capture_frame()
    return None
```

**Usage**:
```python
# Headless mode
simulator = Simulator("Scene_1", headless=True)

# With viewer (default)
simulator = Simulator("Scene_1")
```

---

## Medium Priority Issues

### Issue #7: Permission System Not Enforced

**Severity**: 🟠 MEDIUM - Security/logic issue

**Problem**:
- Permissions defined in JSON but only checked in `get_parameters()`
- Other tools don't validate permissions
- Relies on LLM respecting semantic restrictions

**Impact**:
- LLM can access restricted object properties
- Permissions are advisory, not enforced
- May lead to incorrect problem solving

**Proposed Fix**:
Add permission checking to all query tools:

```python
def _check_permission(self, object_id: str, permission_key: str) -> bool:
    """Check if object has permission for a given property."""
    permissions = getattr(self, 'permissions', {})
    obj_perms = permissions.get(object_id, {})
    return obj_perms.get(permission_key, True)  # Default to allowed

def get_velocity(self, object_id: str) -> dict:
    """Fetch the linear velocity of a given object in the simulation."""
    try:
        object_id = str(object_id)
        
        # Check permission
        if not self._check_permission(object_id, "vel"):
            return {"error": "Permission denied: vel access not allowed for this object"}
        
        # ... rest of implementation
```

---

### Issue #8: No Experiment Aggregation

**Severity**: 🟠 MEDIUM - Missing functionality

**Problem**:
- Each run overwrites `aggregated_results.json`
- No historical comparison across runs
- TestResults logs not parsed or analyzed

**Proposed Fix**:
- Append results with timestamps
- Create analysis scripts
- Add result comparison tools

---

## Low Priority Issues

### Issue #9: Single Model Hardcoded
- OpenAIAgent only supports GPT-4o
- No easy way to switch models

### Issue #10: No Progress Indicators
- Long experiments have no status updates
- No ETA or progress bar

### Issue #11: Memory Growth
- Conversation context grows unbounded
- May hit token limits for long experiments

### Issue #12: Limited Error Recovery
- Some errors terminate experiment
- No retry logic for transient failures

### Issue #13: No Scene Validation
- Invalid JSON/XML not caught early
- Errors only appear at runtime

---

## Testing Recommendations

### Unit Tests Needed

1. **Test `get_acceleration()`**:
```python
def test_get_acceleration():
    simulator = Simulator("Scene_1")
    acc = simulator.get_acceleration("object_1")
    assert "x" in acc
    assert isinstance(acc["x"], float)
```

2. **Test `get_parameters()`**:
```python
def test_get_parameters():
    simulator = Simulator("Scene_1")
    params = simulator.get_parameters("object_1")
    assert "mass" in params
    assert params["mass"] > 0
```

3. **Test path resolution**:
```python
def test_scene_path_resolution():
    scene = Scene("Scene_1", simulator)
    assert scene.file_path is not None
    assert os.path.exists(scene.file_path)
```

### Integration Tests Needed

1. Test full experiment loop
2. Test error handling
3. Test permission enforcement
4. Test answer validation

---

## Priority Fix Order

1. ✅ **Bug #1**: Missing `get_acceleration()` - Blocks functionality
2. ✅ **Bug #2**: `get_parameters()` array index - Always fails
3. ✅ **Bug #3**: Hardcoded paths - Blocks cross-platform use
4. ⚠️ **Issue #4**: Outdated API - May break soon
5. ⚠️ **Issue #5**: Directory naming - Causes failures
6. ⚠️ **Issue #6**: Viewer dependency - Blocks headless use

---

**Last Updated**: January 2025
**Total Issues Documented**: 13
**Critical Bugs**: 3
**High Priority**: 3
**Medium Priority**: 2
**Low Priority**: 5
