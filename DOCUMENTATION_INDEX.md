# Documentation Index

This repository now includes comprehensive documentation for the PhysMent codebase. This index helps you navigate the documentation files.

## Documentation Files

### 📘 [README.md](README.md) - Main Documentation
**Purpose**: Complete project documentation and user guide

**Contents**:
- Project overview and features
- Installation instructions
- Architecture explanation
- Usage guide
- Tool reference
- Known issues summary
- Troubleshooting guide

**Best for**: New users, getting started, understanding the system

---

### 🐛 [BUGS.md](BUGS.md) - Technical Bug Report
**Purpose**: Detailed technical documentation of bugs and issues

**Contents**:
- Critical bugs with code examples
- Error messages and stack traces
- Proposed fixes with code
- Testing recommendations
- Priority fix order

**Best for**: Developers fixing bugs, understanding technical issues

**Key Sections**:
- Bug #1: Missing `get_acceleration()` implementation
- Bug #2: `get_parameters()` array index bug
- Bug #3: Hardcoded Windows paths
- Issues #4-13: Additional problems and improvements

---

### 🚀 [QUICK_START.md](QUICK_START.md) - Quick Reference
**Purpose**: Fast setup and common solutions

**Contents**:
- Installation checklist
- First run steps
- Common issues table
- File structure overview
- Key commands

**Best for**: Quick setup, troubleshooting common problems

---

### 📝 [CLAUDE.md](CLAUDE.md) - Existing Documentation
**Purpose**: Original Claude Code documentation (already existed)

**Contents**:
- Detailed architecture
- Code flow diagrams
- Implementation details
- Scene structure
- Tool descriptions

**Best for**: Deep dive into implementation details

---

## Documentation by Use Case

### I want to...

**...get started quickly**
→ Read [QUICK_START.md](QUICK_START.md)

**...understand the project**
→ Read [README.md](README.md) Overview and Architecture sections

**...fix a bug**
→ Read [BUGS.md](BUGS.md) for detailed bug reports and fixes

**...run an experiment**
→ Read [README.md](README.md) Quick Start and Usage sections

**...add a new feature**
→ Read [README.md](README.md) Contributing section and [CLAUDE.md](CLAUDE.md) Extensibility Points

**...understand the code**
→ Read [CLAUDE.md](CLAUDE.md) for detailed implementation details

**...troubleshoot an error**
→ Check [README.md](README.md) Troubleshooting section and [BUGS.md](BUGS.md)

---

## Known Issues Summary

### Critical (Must Fix)
1. ❌ **Missing `get_acceleration()`** - Method referenced but not implemented
2. ❌ **`get_parameters()` bug** - Uses string as array index
3. ❌ **Hardcoded Windows paths** - Breaks on Mac/Linux

### High Priority
4. ⚠️ **Outdated OpenAI API** - May break with library updates
5. ⚠️ **Scene directory naming** - Inconsistent formats
6. ⚠️ **MuJoCo viewer dependency** - Breaks in headless environments

### Medium/Low Priority
7. Permission system not enforced
8. No experiment aggregation
9. Single model hardcoded
10. No progress indicators
11. Memory growth issues
12. Limited error recovery
13. No scene validation

See [BUGS.md](BUGS.md) for detailed information on each issue.

---

## Quick Links

- **Main Documentation**: [README.md](README.md)
- **Bug Reports**: [BUGS.md](BUGS.md)
- **Quick Start**: [QUICK_START.md](QUICK_START.md)
- **Detailed Architecture**: [CLAUDE.md](CLAUDE.md)

---

## Documentation Status

✅ **Complete**:
- Main README with full project documentation
- Detailed bug reports with fixes
- Quick start guide
- Troubleshooting guide

📋 **Existing**:
- Claude.md (original documentation)

🔄 **Future Improvements**:
- API reference documentation
- Scene creation guide
- Testing guide
- Performance optimization guide

---

**Last Updated**: January 2025
