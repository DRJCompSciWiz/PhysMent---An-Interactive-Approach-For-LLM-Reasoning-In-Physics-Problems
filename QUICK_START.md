# Quick Start Guide

## Installation Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed: `pip install mujoco openai python-dotenv numpy`
- [ ] `.env` file created with `OPENAI_API_KEY`
- [ ] Path configuration fixed in `Scene.py` (see [BUGS.md](BUGS.md) #3)

## First Run

1. **Fix paths in `Scene.py`**:
   ```python
   # Change line 23-37 to use relative paths
   script_dir = os.path.dirname(os.path.abspath(__file__))
   scenes_dir = os.path.join(script_dir, "Scenes")
   self.file_path = os.path.join(scenes_dir, f"Scene{self.scene_number}", f"scene{self.scene_number}.json")
   ```

2. **Fix missing `get_acceleration()` in `Simulator.py`** (see [BUGS.md](BUGS.md) #1)

3. **Fix `get_parameters()` bug in `Simulator.py`** (see [BUGS.md](BUGS.md) #2)

4. **Edit `main.py`**:
   ```python
   scene_ids = ["Scene_1"]  # Start with one scene
   ```

5. **Run**:
   ```bash
   python main.py
   ```

## Common Issues

| Issue | Solution |
|-------|----------|
| "File not found" | Fix paths in `Scene.py` (Bug #3) |
| "AttributeError: get_acceleration" | Add method to `Simulator.py` (Bug #1) |
| "TypeError: only integers..." | Fix `get_parameters()` (Bug #2) |
| OpenAI API errors | Update `OpenAIAgent.py` (Issue #4) |

## File Structure

```
PhysMent-1/
├── main.py              # Entry point
├── Experimental.py      # Experiment orchestrator
├── Scene.py             # Scene management
├── Simulator.py         # MuJoCo wrapper
├── OpenAIAgent.py       # LLM interface
├── Scenes/              # Scene data
│   └── Scene{N}/
│       ├── scene{N}.json
│       └── scene{N}.xml
├── TestResults/         # Experiment logs
└── .env                 # API key (create this)
```

## Key Commands

```bash
# Run experiment
python main.py

# Check logs
cat TestResults/Scene1/experimentslog_*.txt

# View results
cat aggregated_results.json
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [BUGS.md](BUGS.md) for known issues
- Review experiment logs in `TestResults/`
