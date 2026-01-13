# PhysMent

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
