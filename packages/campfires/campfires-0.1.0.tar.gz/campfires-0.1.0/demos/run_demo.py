#!/usr/bin/env python3
"""
Simple demo runner for the Campfires framework.

This script demonstrates basic functionality without external API dependencies.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campfires.core import Torch, Camper, Campfire, StateManager
from campfires.party_box import LocalDriver
from campfires.mcp import MCPProtocol, AsyncQueueTransport
from campfires.utils import generate_torch_id


class TextAnalyzerCamper(Camper):
    """Simple camper that analyzes text content."""
    
    async def override_prompt(self, raw_prompt: str) -> dict:
        """Override the base prompt for text analysis."""
        return {
            "system": "You are a text analyzer that identifies keywords and sentiment.",
            "user": f"{raw_prompt}\nAnalyze the following text for keywords and sentiment."
        }
    
    async def process_torch(self, torch: Torch) -> Torch:
        """Analyze text content in the torch."""
        try:
            text = torch.data.get('text', '')
            
            # Simple text analysis
            analysis = {
                'word_count': len(text.split()),
                'character_count': len(text),
                'has_keywords': any(keyword in text.lower() for keyword in ['urgent', 'help', 'crisis']),
                'sentiment': 'negative' if any(word in text.lower() for word in ['bad', 'terrible', 'awful']) else 'neutral',
                'processed_at': datetime.utcnow().isoformat()
            }
            
            torch.add_result(self.name, analysis)
            
            # Add metadata for other campers
            if analysis['has_keywords']:
                torch.metadata['priority'] = 'high'
            
            return torch
            
        except Exception as e:
            torch.add_result(self.name, {
                'status': 'error',
                'message': f'Analysis failed: {str(e)}'
            })
            return torch


class SummarizerCamper(Camper):
    """Camper that creates summaries of text."""
    
    async def override_prompt(self, raw_prompt: str) -> dict:
        """Override the base prompt for summarization."""
        return {
            "system": "You are a text summarizer that creates concise summaries.",
            "user": f"{raw_prompt}\nCreate a concise summary of the following text."
        }
    
    async def process_torch(self, torch: Torch) -> Torch:
        """Create a summary of the text."""
        try:
            text = torch.data.get('text', '')
            
            # Simple summarization (first sentence + word count)
            sentences = text.split('.')
            first_sentence = sentences[0].strip() if sentences else text[:50]
            
            summary = {
                'summary': f"{first_sentence}..." if len(text) > 50 else text,
                'total_sentences': len([s for s in sentences if s.strip()]),
                'summary_ratio': min(len(first_sentence) / len(text) if text else 0, 1.0),
                'created_at': datetime.utcnow().isoformat()
            }
            
            torch.add_result(self.name, summary)
            return torch
            
        except Exception as e:
            torch.add_result(self.name, {
                'status': 'error',
                'message': f'Summarization failed: {str(e)}'
            })
            return torch


class LoggerCamper(Camper):
    """Camper that logs processing results."""
    
    def __init__(self, party_box, config: dict, state_manager: StateManager):
        super().__init__(party_box, config)
        self.state_manager = state_manager
    
    async def override_prompt(self, raw_prompt: str) -> dict:
        """Override the base prompt for logging."""
        return {
            "system": "You are a logging system that records processing results.",
            "user": f"{raw_prompt}\nLog the processing results."
        }
    
    async def process_torch(self, torch: Torch) -> Torch:
        """Log the torch processing results."""
        try:
            # Create log entry
            log_entry = {
                'torch_id': torch.id,
                'processing_results': torch.results,
                'metadata': torch.metadata,
                'logged_at': datetime.utcnow().isoformat()
            }
            
            # Store in state manager
            await self.state_manager.log_mcp_message(
                'torch_processing',
                json.dumps(log_entry),
                self.name
            )
            
            torch.add_result(self.name, {
                'status': 'logged',
                'log_id': f"log_{torch.id}",
                'logged_at': datetime.utcnow().isoformat()
            })
            
            return torch
            
        except Exception as e:
            torch.add_result(self.name, {
                'status': 'error',
                'message': f'Logging failed: {str(e)}'
            })
            return torch


async def run_simple_demo():
    """Run a simple demonstration of the Campfires framework."""
    print("🔥 Starting Simple Campfires Demo")
    print("=" * 40)
    
    # Initialize components
    box_driver = LocalDriver("./demo_storage")
    state_manager = StateManager("./demo_simple.db")
    await state_manager.initialize()
    
    # Create campers
    analyzer = TextAnalyzerCamper(box_driver, {"name": "TextAnalyzer"})
    summarizer = SummarizerCamper(box_driver, {"name": "Summarizer"})
    logger = LoggerCamper(box_driver, {"name": "Logger"}, state_manager)
    
    # Setup MCP protocol
    transport = AsyncQueueTransport()
    protocol = MCPProtocol(transport)
    
    # Create campfire
    campfire = Campfire(
        name="SimpleDemoCampfire",
        campers=[analyzer, summarizer, logger],
        party_box=box_driver,
        mcp_protocol=protocol
    )
    
    # Start the campfire
    await campfire.start()
    
    try:
        # Sample texts to process
        sample_texts = [
            "This is a simple test message for the Campfires framework.",
            "Help! This is an urgent message that needs immediate attention.",
            "The weather is terrible today. It's raining and I feel awful about the situation.",
            "Welcome to the Campfires framework. This system processes torches through multiple campers.",
            "Crisis situation detected. Please help with this urgent matter as soon as possible."
        ]
        
        print("📝 Processing sample texts...")
        
        for i, text in enumerate(sample_texts, 1):
            print(f"\n🔍 Processing Text {i}: {text[:50]}...")
            
            # Create torch
            torch = Torch(
                id=generate_torch_id(),
                data={'text': text},
                metadata={'source': 'demo', 'batch': i}
            )
            
            # Process through campfire
            processed_torch = await campfire.process_torch(torch)
            
            # Display results
            print(f"  📊 Analysis Results:")
            analyzer_result = processed_torch.results.get('TextAnalyzer', {})
            print(f"    Words: {analyzer_result.get('word_count', 0)}")
            print(f"    Sentiment: {analyzer_result.get('sentiment', 'unknown')}")
            print(f"    Has Keywords: {analyzer_result.get('has_keywords', False)}")
            
            summarizer_result = processed_torch.results.get('Summarizer', {})
            print(f"    Summary: {summarizer_result.get('summary', 'N/A')}")
            
            if processed_torch.metadata.get('priority') == 'high':
                print(f"    🚨 HIGH PRIORITY DETECTED")
        
        # Display final statistics
        print(f"\n📊 Demo Statistics")
        print("=" * 25)
        stats = await state_manager.get_stats()
        print(f"Total torches processed: {stats.get('total_torches', 0)}")
        print(f"Total processing events: {stats.get('total_processing_events', 0)}")
        print(f"Total MCP messages: {stats.get('total_mcp_messages', 0)}")
        
    finally:
        # Cleanup
        await campfire.stop()
        print("\n🔥 Demo completed successfully!")


if __name__ == "__main__":
    print("Simple Campfires Framework Demo")
    print("This demo shows basic text processing capabilities.")
    print()
    
    asyncio.run(run_simple_demo())