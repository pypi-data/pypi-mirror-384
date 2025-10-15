# Campfires Framework Demos

This directory contains demonstration scripts that showcase the capabilities of the Campfires framework.

## Available Demos

### 1. Simple Demo (`run_demo.py`)

A basic demonstration that shows core Campfires functionality without external dependencies.

**Features:**
- Text analysis (word count, sentiment, keyword detection)
- Text summarization
- Result logging to SQLite database
- Torch processing through multiple campers

**To run:**
```bash
python demos/run_demo.py
```

### 2. Reddit Crisis Tracker (`reddit_crisis_tracker.py`)

A comprehensive demo that simulates monitoring Reddit posts for mental health crisis situations.

**Features:**
- Mock Reddit API for generating crisis-related posts
- Crisis detection using keyword matching and LLM analysis
- Automated response generation for crisis posts
- Incident logging and tracking
- Integration with OpenRouter API for LLM capabilities

**Note:** This demo uses mock data and simulated API responses. To use with real APIs, you would need:
- Reddit API credentials (PRAW library)
- Valid OpenRouter API key
- Proper rate limiting and error handling

**To run:**
```bash
python demos/reddit_crisis_tracker.py
```

## Demo Architecture

Both demos follow the same Campfires architecture pattern:

1. **Torches**: Data containers that flow through the system
2. **Campers**: Processing units that transform torch data
3. **Campfire**: Orchestrator that manages campers and torch flow
4. **Box Driver**: Storage backend for assets and data
5. **State Manager**: Persistent state and logging
6. **MCP Protocol**: Message communication between components

## Output

When you run the demos, you'll see:
- Real-time processing logs
- Analysis results for each torch
- Summary statistics
- Database storage confirmation

## Extending the Demos

You can extend these demos by:
- Adding new camper types for different processing tasks
- Integrating with real APIs (Reddit, Twitter, etc.)
- Adding more sophisticated analysis algorithms
- Implementing different storage backends
- Creating custom MCP transport layers

## Requirements

The demos use only the core Campfires framework components. For the Reddit demo with real API integration, you would additionally need:
- `praw` for Reddit API
- `openai` or similar for LLM integration
- API keys and credentials