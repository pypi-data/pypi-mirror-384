# Campfires Framework

A Python framework for orchestrating multimodal Large Language Models (LLMs) and tools to achieve emergent, task-driven behavior.

![The Valley of Campfires](images/campfires.jpg)
*A peaceful valley at twilight, where AI agents gather around glowing campfires to collaborate, share knowledge through torches, and exchange resources via the central Party Box. Each campfire represents a collaborative workspace, while the glowing Party Box in the center connects all communities across the valley.*

## The Valley of Campfires

Imagine a peaceful valley at twilight, dotted with glowing campfires. Around each campfire, a group of **Campers** (AI agents) sit together, sharing stories, analyzing information, and working on tasks. Each campfire represents a **Campfire** - a collaborative workspace where agents can communicate and coordinate their efforts.

### The Campfire Community

At your campfire, **Campers** pass around **Torches** - glowing vessels that carry information, data, and insights from one agent to another. Each torch illuminates the conversation, bringing new perspectives and knowledge to the circle. As campers examine and discuss what each torch reveals, they add their own insights, transforming the information before passing it along.

### The Party Box Exchange

Between the campfires sits a magical **Party Box** - a shared storage space where campfires can exchange gifts, artifacts, and resources. When your campers discover something valuable (documents, images, audio files, or data), they can place it in the Party Box for other campfires to discover and use. It's like a community treasure chest that connects all the campfires in the valley.

### The Torch Bearer Network

When something important happens at your campfire - a breakthrough discovery, a completed task, or an urgent message - a **Torch Bearer** can carry the news to other campfires throughout the valley. These torch bearers use the **MCP Protocol** (Model Context Protocol) to deliver information packets, ensuring that all campfires stay connected and informed about events, notifications, and shared resources.

### Your Valley, Your Rules

Each campfire operates independently, with its own group of specialized campers, but they're all part of the same vibrant valley community. Whether you're running a single intimate campfire or orchestrating multiple campfires across the valley, the framework provides the tools to create emergent, collaborative AI behaviors that feel as natural as friends gathering around a fire.

Welcome to the valley. Pull up a log, grab a torch, and let's build something amazing together.

## Features

- **Modular Architecture**: Build complex AI workflows using composable "Campers" (AI agents)
- **LLM Integration**: Built-in support for OpenRouter and other LLM providers
- **MCP Protocol**: Model Context Protocol for inter-agent communication
- **Storage Management**: Flexible "Party Box" system for asset storage
- **State Management**: Persistent state tracking with SQLite backend
- **Template System**: Dynamic prompt templating with Jinja2

## Installation

### From PyPI (Recommended)

```bash
pip install campfires
```

### From Source

```bash
git clone https://github.com/campfires/campfires.git
cd campfires
pip install -e .
```

## Quick Start

### Basic Usage

```python
import asyncio
from campfires import Campfire, Camper, Torch, OpenRouterConfig, LLMCamperMixin

class MyCamper(Camper, LLMCamperMixin):
    async def process(self, torch: Torch) -> Torch:
        # Process the input torch and return a new torch
        response = await self.llm_completion(f"Analyze: {torch.claim}")
        return Torch(
            claim=response,
            confidence=0.8,
            metadata={"processed_by": "MyCamper"}
        )

async def main():
    # Setup LLM configuration
    config = OpenRouterConfig(
        api_key="your-openrouter-api-key",
        default_model="anthropic/claude-3-sonnet"
    )
    
    # Create camper and setup LLM
    camper = MyCamper("my-camper")
    camper.setup_llm(config)
    
    # Create campfire and add camper
    campfire = Campfire("my-campfire")
    campfire.add_camper(camper)
    
    # Start the campfire
    await campfire.start()
    
    # Send a torch for processing
    input_torch = Torch(claim="Hello, world!")
    await campfire.send_torch(input_torch)
    
    # Stop the campfire
    await campfire.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Crisis Detection Example

```python
import asyncio
from campfires import (
    Campfire, Camper, Torch, 
    OpenRouterConfig, LLMCamperMixin,
    MCPProtocol, AsyncQueueTransport
)

class CrisisDetectionCamper(Camper, LLMCamperMixin):
    async def process(self, torch: Torch) -> Torch:
        # Analyze text for crisis indicators
        prompt = f"""
        Analyze this text for crisis indicators:
        "{torch.claim}"
        
        Return JSON with crisis_probability (0-1) and key_indicators.
        """
        
        response = await self.llm_completion_with_mcp(
            prompt, 
            channel="crisis_detection"
        )
        
        return Torch(
            claim=f"Crisis analysis: {response}",
            confidence=0.9,
            metadata={"analysis_type": "crisis_detection"}
        )

async def main():
    # Setup MCP protocol for inter-camper communication
    transport = AsyncQueueTransport()
    mcp_protocol = MCPProtocol(transport)
    await mcp_protocol.start()
    
    # Setup LLM configuration
    config = OpenRouterConfig(
        api_key="your-openrouter-api-key",
        default_model="anthropic/claude-3-sonnet"
    )
    
    # Create and configure camper
    camper = CrisisDetectionCamper("crisis-detector")
    camper.setup_llm(config, mcp_protocol)
    
    # Create campfire with MCP support
    campfire = Campfire("crisis-campfire", mcp_protocol=mcp_protocol)
    campfire.add_camper(camper)
    
    await campfire.start()
    
    # Process some text
    torch = Torch(claim="I'm feeling really overwhelmed and don't know what to do")
    await campfire.send_torch(torch)
    
    await campfire.stop()
    await mcp_protocol.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Core Concepts

### Torches - The Light of Knowledge
In our valley, **Torches** are glowing vessels that carry information, insights, and data between campers. Each torch illuminates a piece of knowledge with its own confidence level - some burn bright with certainty, others flicker with uncertainty:

```python
from campfires import Torch

torch = Torch(
    claim="The weather is sunny today",
    confidence=0.95,  # How brightly this torch burns
    metadata={"source": "weather_api", "location": "NYC"}
)
```

### Campers - The Valley Inhabitants
**Campers** are the AI agents sitting around your campfire. Each camper has their own expertise and personality. When a torch is passed to them, they examine it, add their insights, and pass along a new torch with their findings:

```python
from campfires import Camper, Torch

class WeatherCamper(Camper):
    async def process(self, torch: Torch) -> Torch:
        # This camper specializes in weather analysis
        return Torch(claim=f"Weather insight: {torch.claim}")
```

### Campfires - The Gathering Circles
A **Campfire** is where your campers gather to collaborate. It orchestrates the conversation, ensuring torches are passed in the right order and that every camper gets a chance to contribute their expertise:

```python
from campfires import Campfire

campfire = Campfire("weather-analysis")
campfire.add_camper(weather_camper)
campfire.add_camper(analysis_camper)
# Now they can work together around the fire
```

### Party Box - The Valley's Treasure Chest
The **Party Box** is the shared storage system where campfires can exchange valuable artifacts - documents, images, audio files, and data. It's like a magical chest that connects all campfires in the valley:

```python
from campfires import LocalDriver

# Store something in the party box
party_box = LocalDriver("./demo_storage")
await party_box.store_asset(file_data, "shared_document.pdf")
```

### MCP Protocol - The Torch Bearer Network
The **Model Context Protocol** is how torch bearers carry messages between campfires throughout the valley. It ensures that important information, events, and notifications reach every campfire that needs to know:

```python
from campfires import MCPProtocol, AsyncQueueTransport

transport = AsyncQueueTransport()
mcp_protocol = MCPProtocol(transport)
await mcp_protocol.start()
# Now torch bearers can carry messages across the valley
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_DEFAULT_MODEL=anthropic/claude-3-sonnet
CAMPFIRES_LOG_LEVEL=INFO
CAMPFIRES_DB_PATH=./campfires.db
```

### OpenRouter Configuration

```python
from campfires import OpenRouterConfig

config = OpenRouterConfig(
    api_key="your-api-key",
    default_model="anthropic/claude-3-sonnet",
    max_tokens=1000,
    temperature=0.7
)
```

## Examples

Check out the `demos/` directory for complete examples:

- `reddit_crisis_tracker.py`: Crisis detection system for social media
- `run_demo.py`: Simple demonstration of basic concepts

## Development

### Setting up for Development

```bash
git clone https://github.com/campfires/campfires.git
cd campfires
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black campfires/
```

### Type Checking

```bash
mypy campfires/
```

## Optional Dependencies

### AWS Support
```bash
pip install "campfires[aws]"
```

### Redis Support
```bash
pip install "campfires[redis]"
```

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: https://campfires.readthedocs.io
- GitHub Issues: https://github.com/campfires/campfires/issues
- Discussions: https://github.com/campfires/campfires/discussions