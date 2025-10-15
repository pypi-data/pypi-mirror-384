# Campfires Framework Specification

## Overview

Campfires is a Python framework for orchestrating multimodal Large Language Models (LLMs) and tools to achieve emergent, task-driven behavior. It mimics neural patterns: models cluster into focused groups ("campfires"), process tasks, and pass distilled results ("torches") through a Model Context Protocol (MCP) to other groups. A central, driver-based "Party Box" stores assets, keeping communication lean and scalable.

## Core Metaphor

- **Campfires**: Small groups of models or tools (e.g., LLMs, APIs) working on a specific task, like neurons in a brain region.
- **Campers**: Individual models or tools within a campfire, collaborating to produce a single, refined output.
- **Torchbearer**: The camper who generates the final answer, automatically tasked with passing a "torch" (a JSON summary of results) to other campfires via MCP channels.
- **Torch**: A lightweight message carrying only text (e.g., `{"claim": "bridge down", "path": "./party_box/abc123.jpg"}`), representing the campfire's output.
- **Party Box**: A central, driver-agnostic storage for assets (images, audio, etc.), accessed by all campfires to avoid heavy data transfers.

## Functional Requirements

1. **Campfire Structure**:

   - Implemented as a Python class `Campfire`.
   - Each campfire hosts 1–N campers, defined by a config (e.g., `ScrapeCampfire(reddit)`, `SentimentCampfire(grok-mini)`).
   - Processes tasks internally, producing one torch per cycle.
   - Subscribes to specific MCP channels (e.g., `crisis-update`, `weather-crosscheck`) for input/output.

2. **Camper Behavior**:

   - Base class `Camper`, extensible via inheritance.
   - Methods:
     - `load_rag(template_path)`: Loads a JSON/YAML template, embeds dynamic values (e.g., `{time}`, `{asset_path}`), returns a prompt.
     - `override_prompt(raw_prompt)`: Abstract method for custom API calls (e.g., to Grok, LLaMA). Devs implement their existing wrappers.
     - Returns a torch: `{"claim": "...", "path": "...", "confidence": 0.8}`.
   - Holds a reference to the Party Box for asset access.

3. **Torchbearer Selection**:

   - No fixed role; the camper producing the final answer in a cycle becomes the torchbearer.
   - Automatically gains write access to a designated MCP channel.
   - Sends torch as JSON, then reverts to listener mode.

4. **Party Box**:

   - Interface `BoxDriver`, abstract base for storage backends.
   - Default: `LocalDriver(path="./party_box")` for local filesystem.
   - Extensible: `S3Driver(bucket, key)`, `RedisDriver(host, port)`, etc.
   - Methods:
     - `put(key, data)`: Stores asset (image, audio) and returns a unique hash (e.g., `abc123`).
     - `get(key)`: Retrieves asset by hash, as path or stream.
   - Checksums prevent duplicate writes; assets older than 20 minutes auto-delete to keep lean.
   - Torch only carries text: `path: ./party_box/abc123.jpg` or `url: s3://campfires/abc123.wav`.

5. **MCP Integration**:

   - Uses Model Context Protocol (MCP) for communication.
   - Channels (e.g., `crisis-update`) act as conduits; only subscribed campfires receive torches.
   - Ensures no crosstalk; torches are filtered by channel subscription.
   - Supports OpenRouter’s free-tier models (e.g., LLaMA, Mistral, Grok-mini) via API keys.

6. **State Management**:

   - SQLite log (`torch_log.db`) tracks:
     - Current torchbearer per campfire.
     - Campfire status (active, idle).
     - Timestamps for debugging/replay.
   - Keeps framework stateless otherwise; no persistent model state.

7. **Multimodal Support**:

   - Handles text, image, audio, etc., via Party Box.
   - Campfires process raw assets (e.g., image model analyzes bridge.jpg), but torches only carry metadata (e.g., `caption: cracked archway, path: ./party_box/abc123.jpg`).
   - Next campfire decides whether to fetch the asset.

## Demo Example

- **Scenario**: Reddit-based crisis tracker.
- **Setup**:
  - Four campfires:
    1. **ScrapeCampfire**: Pulls headlines from r/worldnews (e.g., "London blackout hits five boroughs").
    2. **SentimentCampfire**: Analyzes comments from r/london (e.g., "Panic rising, 80% negative").
    3. **VerifyCampfire**: Cross-checks with public APIs (e.g., weather, traffic cams: "Storm-related, not hack").
    4. **SummaryCampfire**: Outputs alert (e.g., "Storm outage, no power until 3 AM, TFL down").
  - Party Box: Local filesystem (`./party_box`), stores maps, audio clips.
  - Torches: JSON packets (e.g., `{"claim": "blackout confirmed", "path": "./party_box/map_456.jpg"}`).
- **Flow**:
  - ScrapeCampfire lights torch, passes to SentimentCampfire.
  - SentimentCampfire adds sentiment, stores comment summary in Party Box, passes torch.
  - VerifyCampfire checks APIs, adds verification, passes torch.
  - SummaryCampfire crafts alert, outputs to user channel.
- **Code**: Include `/examples/live_alert.py`, a runnable script:
  - Uses OpenRouter free models (e.g., Grok-mini for sentiment).
  - Simulates Reddit data with a static JSON dataset for testing.
  - Prints final alert to console.
  - No external auth; uses public Reddit API or mock data.

## Non-Functional Requirements

- **Scalability**: Supports 1–100 campfires, dynamic channel subscriptions.
- **Performance**: Torches &lt;1KB, Party Box handles assets up to 10MB without MCP traffic.
- **Extensibility**: Devs inherit `Camper` for custom models; `BoxDriver` for new storage.
- **Cost**: Free-tier compatible (OpenRouter, local storage).
- **Debugging**: SQLite log enables full replay of torch handoffs.

## Constraints

- No raw asset transfers over MCP-only text metadata.
- Rate limits: Respect OpenRouter’s free-tier caps (e.g., 1000 calls/day).
- No persistent model state; campfires restart fresh per cycle.

## Deliverable

- Python library: `campfires`, pip-installable.
- `/examples/live_alert.py`: Fully functional demo, copy-paste runnable.
- Docs: Explain campfire, camper, torchbearer, Party Box in &lt;500 words, with campfire analogy.