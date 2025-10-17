# Agentic Context Engine (ACE) 🚀

**Build self-improving AI agents that learn from experience**

[![PyPI version](https://badge.fury.io/py/ace-framework.svg)](https://pypi.org/project/ace-framework/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/Kayba-ai/agentic-context-engine/actions/workflows/tests.yml/badge.svg)](https://github.com/Kayba-ai/agentic-context-engine/actions)
[![Paper](https://img.shields.io/badge/Paper-arXiv:2510.04618-red.svg)](https://arxiv.org/abs/2510.04618)

🧠 **ACE** is a framework for building AI agents that get smarter over time by learning from their mistakes and successes.

💡 Based on the paper "Agentic Context Engineering" from Stanford/SambaNova - ACE helps your LLM agents build a "playbook" of strategies that improves with each task.

🔌 **Works with any LLM** - OpenAI, Anthropic Claude, Google Gemini, and 100+ more providers out of the box!

## Quick Links

📦 [PyPI Package](https://pypi.org/project/ace-framework/) | 📚 [Documentation](https://github.com/Kayba-ai/agentic-context-engine/wiki) | 🐛 [Issues](https://github.com/Kayba-ai/agentic-context-engine/issues) | 💬 [Discussions](https://github.com/Kayba-ai/agentic-context-engine/discussions)

## Quick Start

**Minimum Python 3.9 required**

### Install ACE:
```bash
# Basic installation
pip install ace-framework

# With LangChain support (for advanced routing & chains)
pip install ace-framework[langchain]

# For development
pip install -r requirements.txt
```

### Set up your API key:
```bash
# Copy the example environment file
cp .env.example .env

# Add your OpenAI key (or Anthropic, Google, etc.)
echo "OPENAI_API_KEY=your-key-here" >> .env
```

### Run your first agent:
```python
from ace import LiteLLMClient, OfflineAdapter, Generator, Reflector, Curator
from ace import Playbook, Sample, TaskEnvironment, EnvironmentResult
from dotenv import load_dotenv

load_dotenv()

# Create your agent with any LLM
client = LiteLLMClient(model="gpt-3.5-turbo")  # or claude-3, gemini-pro, etc.

# Set up ACE components
adapter = OfflineAdapter(
    playbook=Playbook(),
    generator=Generator(client),
    reflector=Reflector(client),
    curator=Curator(client)
)

# Define a simple task
class SimpleEnv(TaskEnvironment):
    def evaluate(self, sample, output):
        correct = sample.ground_truth.lower() in output.final_answer.lower()
        return EnvironmentResult(
            feedback="Correct!" if correct else "Try again",
            ground_truth=sample.ground_truth
        )

# Train your agent
samples = [
    Sample(question="What is 2+2?", ground_truth="4"),
    Sample(question="Capital of France?", ground_truth="Paris"),
]

results = adapter.run(samples, SimpleEnv(), epochs=1)
print(f"Agent learned {len(adapter.playbook.bullets())} strategies!")
```

## How It Works

ACE uses three AI "roles" that work together to help your agent improve:

1. **🎯 Generator** - Tries to solve tasks using the current playbook
2. **🔍 Reflector** - Analyzes what went wrong (or right)
3. **📝 Curator** - Updates the playbook with new strategies

Think of it like a sports team reviewing game footage to get better!

### The ACE Learning Loop

```mermaid
flowchart TD
    Start([New Task/Question]) --> Generator

    subgraph Playbook ["📚 Playbook (Evolving Context)"]
        Bullets["📝 Strategy Bullets<br/>• Helpful strategies ✓<br/>• Harmful patterns ✗<br/>• Neutral observations ○"]
    end

    Generator["🎯 Generator<br/>Uses playbook strategies<br/>to produce answer"] --> Output[Answer Output]

    Playbook -.->|Provides Context| Generator

    Output --> Environment["🌍 Task Environment<br/>Evaluates answer<br/>Provides feedback"]

    Environment --> Reflector["🔍 Reflector<br/>Analyzes outcome<br/>Tags bullet contributions:<br/>• Which helped?<br/>• Which hurt?<br/>• What's missing?"]

    Reflector --> Curator["📝 Curator<br/>Emits delta operations"]

    Curator --> DeltaOps{{"🔄 Delta Operations<br/>ADD new strategies<br/>UPDATE existing ones<br/>TAG helpful/harmful<br/>REMOVE outdated"}}

    DeltaOps -->|Incremental<br/>Updates| Playbook

    Environment -->|Ground Truth +<br/>Feedback| Reflector

    style Playbook fill:#e1f5fe
    style Generator fill:#fff3e0
    style Reflector fill:#f3e5f5
    style Curator fill:#e8f5e9
    style DeltaOps fill:#fff9c4
```

**Key Insights:**
- **Incremental Learning**: The playbook evolves through small delta updates, not complete rewrites
- **No Context Collapse**: Strategies are preserved and refined, preventing loss of valuable knowledge
- **Self-Improving**: Each task makes the agent smarter by updating its strategy playbook
- **Three-Role Architecture**: Separation of concerns - generating, analyzing, and updating are distinct phases

## Examples

### Simple Q&A Agent
```python
python examples/simple_ace_example.py
```

### Advanced Examples with Different LLMs
```python
python examples/quickstart_litellm.py
```

### LangChain Integration (Advanced)
```python
# With routing and load balancing
python examples/langchain_example.py
```

### Save and Load Playbooks
```python
# Save a trained playbook for later use
adapter = OfflineAdapter(...)
results = adapter.run(samples, environment, epochs=3)
adapter.playbook.save_to_file("my_trained_playbook.json")

# Load a pre-trained playbook
from ace import Playbook, OnlineAdapter
playbook = Playbook.load_from_file("my_trained_playbook.json")
adapter = OnlineAdapter(playbook=playbook, ...)
```

Check out `examples/playbook_persistence.py` for a complete example!

Explore more in the `examples/` folder!

## Supported LLM Providers

ACE works with **100+ LLM providers** through LiteLLM:

- **OpenAI** - GPT-4, GPT-3.5-turbo
- **Anthropic** - Claude 3 (Opus, Sonnet, Haiku)
- **Google** - Gemini Pro, PaLM
- **Cohere** - Command models
- **Local Models** - Ollama, Transformers
- **And many more!**

Just change the model name:
```python
# OpenAI
client = LiteLLMClient(model="gpt-4")

# Anthropic Claude
client = LiteLLMClient(model="claude-3-sonnet-20240229")

# Google Gemini
client = LiteLLMClient(model="gemini-pro")

# With fallbacks for reliability
client = LiteLLMClient(
    model="gpt-4",
    fallbacks=["claude-3-haiku", "gpt-3.5-turbo"]
)
```

## Key Features

- ✅ **Self-Improving** - Agents learn from experience and build knowledge
- ✅ **Provider Agnostic** - Switch LLMs with one line of code
- ✅ **Production Ready** - Automatic retries, fallbacks, and error handling
- ✅ **Cost Efficient** - Track costs and use cheaper models as fallbacks
- ✅ **Async Support** - Built for high-performance applications
- ✅ **Fully Typed** - Great IDE support and type safety

## Advanced Usage

### Online Learning (Learn While Running)
```python
from ace import OnlineAdapter

# Agent improves while processing real tasks
adapter = OnlineAdapter(
    playbook=existing_playbook,  # Can start with existing knowledge
    generator=Generator(client),
    reflector=Reflector(client),
    curator=Curator(client)
)

# Process tasks one by one, learning from each
for task in real_world_tasks:
    result = adapter.process(task, environment)
    # Agent automatically updates its strategies
```

### Custom Task Environments
```python
class CodeTestingEnv(TaskEnvironment):
    def evaluate(self, sample, output):
        # Run the generated code
        test_passed = run_tests(output.final_answer)

        return EnvironmentResult(
            feedback=f"Tests {'passed' if test_passed else 'failed'}",
            ground_truth=sample.ground_truth,
            metrics={"pass_rate": 1.0 if test_passed else 0.0}
        )
```

### Streaming Responses
```python
# Get responses token by token
for chunk in client.complete_with_stream("Write a story"):
    print(chunk, end="", flush=True)
```

### Async Operations
```python
import asyncio

async def main():
    response = await client.acomplete("Solve this problem...")
    print(response.text)

asyncio.run(main())
```

## Experimental v2 Prompts (Beta)

We've developed enhanced v2 prompts that provide better performance through state-of-the-art prompt engineering. These are experimental and in active development.

### What's New in v2

- **🎯 Confidence Scoring**: Know when the AI is certain vs uncertain
- **📝 Enhanced Reasoning**: More detailed step-by-step explanations
- **🔧 Domain Optimization**: Specialized prompts for math and code
- **✅ Better Structure**: Based on analysis of 80+ production AI systems

### Quick Start with v2

```python
from ace.prompts_v2 import PromptManager

# Use v2 prompts (experimental)
manager = PromptManager(default_version="2.0")

# Create components with v2 prompts
generator = Generator(llm, prompt_template=manager.get_generator_prompt())
reflector = Reflector(llm, prompt_template=manager.get_reflector_prompt())
curator = Curator(llm, prompt_template=manager.get_curator_prompt())

# Or use domain-specific variants
math_generator = Generator(llm, prompt_template=manager.get_generator_prompt(domain="math"))
code_generator = Generator(llm, prompt_template=manager.get_generator_prompt(domain="code"))
```

### v1 vs v2 Comparison

| Feature | v1 (Default) | v2 (Experimental) |
|---------|--------------|-------------------|
| **Token Usage** | Baseline | +30-50% more |
| **Confidence Scoring** | ❌ | ✅ Tracks uncertainty |
| **Reasoning Detail** | Basic | Enhanced with steps |
| **Domain Variants** | ❌ | ✅ Math, Code optimized |
| **Output Validation** | Basic | Strict JSON schemas |
| **Status** | Stable | 🔬 Beta/Experimental |

### When to Use v2

- ✅ **Use v2 if you need**: Confidence scores, detailed reasoning, domain-specific optimization
- ⚠️ **Consider v1 if**: Token cost is critical, you need maximum stability
- 🔬 **Note**: v2 is experimental and actively evolving based on user feedback

### Examples

```python
# Compare v1 vs v2 performance
python examples/compare_v1_v2_prompts.py

# See v2 features in action
python examples/advanced_prompts_v2.py
```

See [PROMPT_ENGINEERING.md](docs/PROMPT_ENGINEERING.md) for detailed documentation on v2 prompts.

## Architecture

ACE implements the Agentic Context Engineering method from the research paper:

- **Playbook**: A structured memory that stores successful strategies
- **Bullets**: Individual strategies with helpful/harmful counters
- **Delta Operations**: Incremental updates that preserve knowledge
- **Three Roles**: Generator, Reflector, and Curator working together

The framework prevents "context collapse" - a common problem where agents forget important information over time.

## Repository Structure

```
ace/
├── ace/                    # Core library
│   ├── playbook.py        # Strategy storage & persistence
│   ├── roles.py           # Generator, Reflector, Curator
│   ├── adaptation.py      # Training loops
│   └── llm_providers/     # LLM integrations
├── examples/              # Ready-to-run examples
└── tests/                 # Unit tests
```

## Contributing

We welcome contributions! Feel free to:
- 🐛 Report bugs
- 💡 Suggest features
- 🔧 Submit PRs
- 📚 Improve documentation

## Citation

If you use ACE in your research or project, please cite the original papers:

### ACE Paper (Primary Reference)
```bibtex
@article{zhang2024ace,
  title={Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models},
  author={Zhang, Qizheng and Hu, Changran and Upasani, Shubhangi and Ma, Boyuan and Hong, Fenglu and
          Kamanuru, Vamsidhar and Rainton, Jay and Wu, Chen and Ji, Mengmeng and Li, Hanchen and
          Thakker, Urmish and Zou, James and Olukotun, Kunle},
  journal={arXiv preprint arXiv:2510.04618},
  year={2024}
}
```

### Dynamic Cheatsheet (Foundation Work)
ACE builds upon the adaptive memory concepts from Dynamic Cheatsheet:

```bibtex
@article{suzgun2025dynamiccheatsheet,
  title={Dynamic Cheatsheet: Test-Time Learning with Adaptive Memory},
  author={Suzgun, Mirac and Yuksekgonul, Mert and Bianchi, Federico and Jurafsky, Dan and Zou, James},
  year={2025},
  eprint={2504.07952},
  archivePrefix={arXiv},
  primaryClass={cs.LG},
  url={https://arxiv.org/abs/2504.07952}
}
```

### This Implementation
If you use this specific implementation, you can also reference:

```
This repository: https://github.com/Kayba-ai/agentic-context-engine
PyPI package: https://pypi.org/project/ace-framework/
Based on the open reproduction at: https://github.com/sci-m-wang/ACE-open
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Troubleshooting

### Installation Issues

**Problem**: `pip install ace-framework` fails
- **Solution**: Ensure Python 3.9+ is installed: `python --version`
- **Solution**: Upgrade pip: `pip install --upgrade pip`

**Problem**: ImportError when using LangChain integration
- **Solution**: Install with extras: `pip install ace-framework[langchain]`

**Problem**: LiteLLM API errors
- **Solution**: Check your API keys are set correctly in `.env`
- **Solution**: Verify your API key has sufficient credits/quota

### Common Errors

**"Unrecognized request argument"**: The LLM provider doesn't support a parameter
- This is usually handled automatically, but if it persists, please report an issue

**Memory issues with large playbooks**:
- Use online adaptation mode instead of offline
- Periodically save and reload playbooks

**Rate limiting errors**:
- Add delays between requests
- Use exponential backoff (built into LiteLLM)

For more help, check the [Issues](https://github.com/Kayba-ai/agentic-context-engine/issues) page.

---

**Note**: This is an independent implementation based on the ACE paper (arXiv:2510.04618) and builds upon concepts from Dynamic Cheatsheet. For the original reproduction scaffold, see [sci-m-wang/ACE-open](https://github.com/sci-m-wang/ACE-open).

Made with ❤️ by [Kayba](https://kayba.ai) and the open-source community