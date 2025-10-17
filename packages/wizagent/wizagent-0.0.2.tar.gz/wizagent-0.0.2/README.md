# WizAgent

[![CI](https://github.com/caesar0301/wizagent/actions/workflows/ci.yml/badge.svg)](https://github.com/caesar0301/wizagent/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/wizagent.svg)](https://pypi.org/project/wizagent/)

**WizAgent** is a powerful, intelligent web automation and research framework that combines multi-engine web search, deep research capabilities, browser automation, and structured data extraction with advanced LLM support.

## Features

- 🔍 **Multi-Engine Web Search** - Simultaneous search across multiple engines (Tavily, DuckDuckGo, Google AI, SearXNG, Brave, Baidu, WeChat)
- 📚 **Deep Research Agent** - Autonomous research with iterative query refinement and source aggregation
- 🌐 **Browser Automation** - Intelligent browser control with natural language instructions powered by cogents-browser-use
- 📊 **Structured Data Extraction** - Extract structured data from websites using Pydantic models
- 🎯 **YAML-Based Schema Parser** - Define data models declaratively with the Gem Parser
- 🤖 **Multi-LLM Support** - Works with OpenAI (compatible), Ollama, and OpenRouter
- 🔄 **LangGraph Workflows** - Advanced agent orchestration with state management

## Quick Start

### Installation

```bash
pip install -U wizagent
```

### Basic Usage

```python
import asyncio
from wizagent import WizAgent

async def main():
    # Initialize the agent
    agent = WizAgent()
    
    # Web search
    search_result = await agent.search(
        query="artificial intelligence trends 2025",
        max_results_per_engine=5
    )
    print(search_result)
    
    # Deep research
    research_output = await agent.research(
        instruction="What are the latest developments in quantum computing?"
    )
    print(research_output.content)
    
    # Browser automation
    result = await agent.use_browser(
        instruction="Go to Wikipedia and find information about Python programming"
    )
    print(result)

asyncio.run(main())
```

## Core Components

### 1. Search Agent

Intelligent web search with query polishing, content crawling, and result reranking:

```python
from wizagent import SearchAgent

agent = SearchAgent(
    polish_query=True,           # LLM-powered query optimization
    rerank_results=True,          # Relevance-based reranking
    crawl_content=True,           # Crawl page content
    search_engines=["tavily", "duckduckgo"],
    max_results_per_engine=5
)

result = await agent.run("latest AI developments")
print(result)
```

### 2. Deep Research Agent

Multi-loop research with autonomous knowledge gap detection:

```python
from wizagent import DeepResearchAgent

researcher = DeepResearchAgent(
    max_research_loops=3,
    number_of_initial_queries=3,
    search_engines=["tavily", "duckduckgo"]
)

result = await researcher.research(
    user_message="Compare renewable energy adoption in US vs Europe"
)

print(result.content)  # Comprehensive research report
print(f"Sources: {len(result.sources)}")
```

### 3. Browser Automation & Data Extraction

Navigate websites and extract structured data:

```python
from pydantic import BaseModel, Field
from typing import List

class StockMetric(BaseModel):
    metric_name: str = Field(description="Metric name")
    value: str = Field(description="Metric value")
    
class StockData(BaseModel):
    stock_name: str
    key_metrics: List[StockMetric]

agent = WizAgent()

# Extract structured data
data = await agent.navigate_and_extract(
    url="https://example.com/stocks",
    instruction="Extract key financial metrics",
    schema=StockData,
    use_vision=True
)

print(data.stock_name)
print(data.key_metrics)
```

### 4. Gem Parser - YAML Schema Definition

Define complex Pydantic models using YAML for cleaner configuration:

```yaml
# snowman_balance.yml
task: StructuredExtraction
metadata:
  name: Stock Financial Metrics
data_models:
  - name: StockMetric
    fields:
    - name: metric_name
      type: str
      desc: Metric name
    - name: value
      type: str
      desc: Metric value
  - name: StockData
    fields:
    - name: stock_name
      type: str
      desc: Stock name
    - name: metrics
      type: List[StockMetric]
      desc: Key metrics
output_model: StockData
instruction: Extract financial metrics from the page
```

Load and use the schema:

```python
from wizagent.gems import parse_yaml_file

# Parse YAML to Pydantic models
result = parse_yaml_file("snowman_balance.yml")
StockData = result.target_model

# Use with WizAgent
agent = WizAgent()
data = await agent.navigate_and_extract(
    url="https://example.com",
    instruction=result.instruction,
    schema=StockData
)
```

## Advanced Examples

See the [examples/](examples/) directory for more use cases:

- `examples/agent/search_agent_demo.py` - Web search with crawling and reranking
- `examples/agent/deep_research_demo.py` - Autonomous research workflow
- `examples/agent/snowman_balance.py` - Structured data extraction from websites
- `examples/agent/visit_wikipedia.py` - Browser navigation and interaction
- `examples/gems/snowman_gem.py` - YAML-based schema parsing

## Architecture

WizAgent is built on top of:

- **cogents-core** - Core LLM abstractions and agent framework
- **cogents-browser-use** - Browser automation with intelligent control
- **wizsearch** - Multi-engine web search orchestration
- **LangGraph** - Workflow orchestration and state management
- **Pydantic** - Data validation and structured outputs

## Configuration

Set environment variables for LLM configuration. The configuration is provider-specific:

### OpenAI-compatible
```bash
export COGENTS_LLM_PROVIDER=openai
export OPENAI_API_KEY=your-api-key
export OPENAI_CHAT_MODEL=gpt-4  # optional, default: gpt-3.5-turbo
export OPENAI_BASE_URL=https://api.openai.com/v1  # optional
```

### Other Providers

**Ollama (local):**
```bash
export COGENTS_LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_CHAT_MODEL=llama2  # optional
```

**OpenRouter:**
```bash
export COGENTS_LLM_PROVIDER=openrouter
export OPENROUTER_API_KEY=your-api-key
export OPENROUTER_CHAT_MODEL=anthropic/claude-3-haiku  # optional
```

### Search Engine Configuration

For specific search engines, you may need additional API keys:

```bash
# Tavily (recommended)
export TAVILY_API_KEY=your-tavily-key

# Google AI Search
export GOOGLE_API_KEY=your-google-key

# Brave Search
export BRAVE_API_KEY=your-brave-key
```

See [env.example](env.example) for complete configuration reference.

## Development

```bash
# Install development dependencies
make install

# Run tests
make test

# Format code
make format

# Run quality checks
make quality

# Full development check
make dev-check
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **GitHub**: https://github.com/caesar0301/wizagent
- **PyPI**: https://pypi.org/project/wizagent/
- **Documentation**: https://deepwiki.com/caesar0301/wizagent
