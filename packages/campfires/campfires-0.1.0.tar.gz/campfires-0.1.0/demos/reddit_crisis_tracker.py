#!/usr/bin/env python3
"""
Reddit Crisis Tracker Demo

This demo shows how to use the Campfires framework to monitor Reddit posts
for crisis situations and generate appropriate responses using LLM capabilities.

This is a mock implementation that simulates Reddit data for demonstration purposes.
"""

import asyncio
import json
import random
import sys
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campfires.core import (
    Torch, Camper, Campfire, StateManager, 
    OpenRouterClient, OpenRouterConfig, LLMCamperMixin
)
from campfires.party_box import LocalDriver
from campfires.mcp import MCPProtocol, AsyncQueueTransport
from campfires.utils import generate_torch_id


@dataclass
class RedditPost:
    """Mock Reddit post data structure."""
    id: str
    title: str
    content: str
    author: str
    subreddit: str
    score: int
    created_utc: datetime
    url: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'subreddit': self.subreddit,
            'score': self.score,
            'created_utc': self.created_utc.isoformat(),
            'url': self.url
        }


class MockRedditAPI:
    """Mock Reddit API that generates crisis-related posts."""
    
    CRISIS_KEYWORDS = [
        'suicide', 'depression', 'anxiety', 'panic attack', 'self harm',
        'mental health crisis', 'feeling hopeless', 'want to die',
        'can\'t go on', 'need help', 'crisis hotline', 'emergency'
    ]
    
    SUBREDDITS = [
        'depression', 'anxiety', 'mentalhealth', 'suicidewatch',
        'bipolar', 'ptsd', 'selfharm', 'getting_over_it'
    ]
    
    def __init__(self):
        self.post_counter = 0
    
    def generate_crisis_post(self) -> RedditPost:
        """Generate a mock crisis-related Reddit post."""
        self.post_counter += 1
        
        crisis_templates = [
            {
                'title': 'I can\'t take it anymore',
                'content': 'Everything feels hopeless. I\'ve been struggling with depression for months and nothing seems to help. I don\'t know what to do.'
            },
            {
                'title': 'Panic attacks getting worse',
                'content': 'Having multiple panic attacks daily. Can\'t leave my house. Need advice on coping strategies.'
            },
            {
                'title': 'Feeling suicidal thoughts',
                'content': 'I\'ve been having thoughts of self-harm. I know I should reach out but I don\'t know where to start.'
            },
            {
                'title': 'Lost my job, feeling hopeless',
                'content': 'Just got laid off and I can\'t handle the stress. My anxiety is through the roof and I feel like giving up.'
            }
        ]
        
        template = random.choice(crisis_templates)
        subreddit = random.choice(self.SUBREDDITS)
        
        return RedditPost(
            id=f"mock_{self.post_counter}",
            title=template['title'],
            content=template['content'],
            author=f"user_{random.randint(1000, 9999)}",
            subreddit=subreddit,
            score=random.randint(1, 50),
            created_utc=datetime.utcnow() - timedelta(minutes=random.randint(1, 60)),
            url=f"https://reddit.com/r/{subreddit}/comments/mock_{self.post_counter}"
        )
    
    async def get_recent_posts(self, limit: int = 10) -> List[RedditPost]:
        """Simulate fetching recent posts from Reddit."""
        await asyncio.sleep(0.1)  # Simulate API delay
        return [self.generate_crisis_post() for _ in range(limit)]


class CrisisDetectionCamper(Camper, LLMCamperMixin):
    """Camper that detects crisis situations in Reddit posts."""
    
    def __init__(self, party_box, config: dict, openrouter_config: OpenRouterConfig):
        super().__init__(party_box, config)
        self.setup_llm(openrouter_config)
        self.current_torch = None  # Store current input torch
        self.crisis_keywords = [
            'suicide', 'self harm', 'kill myself', 'end it all',
            'hopeless', 'can\'t go on', 'want to die'
        ]
    
    async def process(self, input_torch: Optional[Torch] = None) -> Torch:
        """Override process to store the input torch and add crisis detection results to it."""
        self.current_torch = input_torch
        
        # Process the torch normally
        output_torch = await super().process(input_torch)
        
        # Add crisis detection results to the input torch metadata so other campers can see it
        if input_torch and output_torch.metadata:
            input_torch.metadata.update({
                'crisis_detected': output_torch.metadata.get('crisis_detected', False),
                'crisis_score': output_torch.metadata.get('crisis_score', 0),
                'crisis_level': output_torch.metadata.get('crisis_level'),
                'keyword_matches': output_torch.metadata.get('keyword_matches', []),
                'llm_analysis': output_torch.metadata.get('llm_analysis', {})
            })
        
        return output_torch
    
    async def override_prompt(self, raw_prompt: str) -> dict:
        """Override the base prompt for crisis detection."""
        try:
            print(f"🔍 CrisisDetectionCamper processing...")
            
            if not self.current_torch:
                return {
                    'claim': 'Error: No input torch available',
                    'confidence': 0.0,
                    'metadata': {
                        'status': 'error',
                        'message': 'No input torch available',
                        'camper_name': self.name
                    }
                }
            
            post_data = self.current_torch.metadata.get('reddit_post', {})
            if not post_data:
                return {
                    'claim': 'Error: No Reddit post data found',
                    'confidence': 0.0,
                    'metadata': {
                        'status': 'error',
                        'message': 'No Reddit post data found',
                        'camper_name': self.name
                    }
                }
            
            # Basic keyword detection (more flexible matching)
            text_to_analyze = f"{post_data['title']} {post_data['content']}".lower()
            keyword_matches = []
            for keyword in self.crisis_keywords:
                # Check for partial matches and variations
                if keyword in text_to_analyze or any(word in text_to_analyze for word in keyword.split()):
                    keyword_matches.append(keyword)
            
            # Use LLM for more sophisticated analysis
            llm_analysis = await self._analyze_with_llm(post_data)
            
            # More sensitive scoring - lower threshold for crisis detection
            keyword_score = min(len(keyword_matches) * 0.2, 0.4)  # Cap keyword contribution
            llm_score = llm_analysis.get('crisis_probability', 0) * 0.8
            crisis_score = keyword_score + llm_score
            crisis_detected = crisis_score > 0.3  # Lower threshold for better sensitivity
            
            # Create output metadata
            output_metadata = {
                'crisis_detected': crisis_detected,
                'crisis_score': crisis_score,
                'keyword_matches': keyword_matches,
                'llm_analysis': llm_analysis,
                'post_id': post_data['id'],
                'subreddit': post_data['subreddit'],
                'camper_name': self.name,
                'reddit_post': post_data  # Pass along the original post data
            }
            
            # Add crisis flag for other campers
            if crisis_detected:
                output_metadata['crisis_level'] = 'high' if crisis_score > 0.8 else 'medium'
            
            claim = f"Crisis {'detected' if crisis_detected else 'not detected'} in Reddit post: {post_data['title'][:50]}"
            
            return {
                'claim': claim,
                'confidence': crisis_score if crisis_detected else 1.0 - crisis_score,
                'metadata': output_metadata
            }
            
        except Exception as e:
            return {
                'claim': f"Error in crisis detection: {str(e)}",
                'confidence': 0.0,
                'metadata': {
                    'status': 'error',
                    'message': f'Crisis detection failed: {str(e)}',
                    'camper_name': self.name
                }
            }
    
    async def _analyze_with_llm(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze post for crisis indicators."""
        try:
            prompt = f"""
            Analyze the following Reddit post for signs of mental health crisis or suicidal ideation.
            
            Title: {post_data['title']}
            Content: {post_data['content']}
            Subreddit: r/{post_data['subreddit']}
            
            Provide a JSON response with:
            - crisis_probability: float between 0-1 indicating likelihood of crisis
            - urgency_level: "low", "medium", or "high"
            - key_indicators: list of concerning phrases or patterns
            - recommended_action: suggested response approach
            """
            
            print(f"🔍 Calling LLM via MCP for post: {post_data['title'][:50]}...")
            response = await self.llm_completion_with_mcp(prompt, channel="crisis_detection")
            print(f"📝 LLM Response: {response[:200]}...")
            
            # Try to parse JSON response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Fallback if LLM doesn't return valid JSON
                return {
                    'crisis_probability': 0.5,
                    'urgency_level': 'medium',
                    'key_indicators': ['Unable to parse LLM response'],
                    'recommended_action': 'Manual review required'
                }
                
        except Exception as e:
            return {
                'crisis_probability': 0.0,
                'urgency_level': 'unknown',
                'key_indicators': [],
                'recommended_action': f'LLM analysis failed: {str(e)}'
            }


class ResponseGeneratorCamper(Camper, LLMCamperMixin):
    """Camper that generates appropriate responses to crisis posts."""
    
    def __init__(self, party_box, config: dict, openrouter_config: OpenRouterConfig):
        super().__init__(party_box, config)
        self.setup_llm(openrouter_config)
        self.current_torch = None
    
    async def process(self, input_torch: Optional[Torch] = None) -> Torch:
        """Override process to store the input torch."""
        self.current_torch = input_torch
        return await super().process(input_torch)
    
    async def override_prompt(self, raw_prompt: str) -> dict:
        """Override the base prompt for response generation."""
        return {
            "system": "You are a compassionate mental health support specialist. Generate helpful, supportive responses.",
            "user": f"{raw_prompt}\nGenerate a supportive response for this crisis situation."
        }
    
    async def override_prompt(self, raw_prompt: str) -> Dict[str, Any]:
        """Override the base prompt for response generation."""
        try:
            print(f"💬 ResponseGeneratorCamper processing...")
            
            if not self.current_torch:
                return {
                    'claim': 'Error: No input torch available',
                    'confidence': 0.0,
                    'metadata': {
                        'status': 'error',
                        'message': 'No input torch available'
                    }
                }
            
            # Check if this is a crisis situation
            crisis_detected = self.current_torch.metadata.get('crisis_detected', False)
            post_data = self.current_torch.metadata.get('reddit_post', {})
            
            if not crisis_detected:
                return {
                    'claim': 'No response needed - no crisis detected',
                    'confidence': 1.0,
                    'metadata': {
                        'response_generated': False,
                        'reason': 'No crisis detected'
                    }
                }
            
            # Generate response for crisis situation
            response = await self._generate_response(post_data)
            
            return {
                'claim': f"Generated supportive response for crisis post: {post_data.get('title', 'Unknown')[:50]}",
                'confidence': 0.9,
                'metadata': {
                    'response_generated': True,
                    'response_text': response,
                    'post_id': post_data.get('id'),
                    'crisis_level': self.current_torch.metadata.get('crisis_level', 'unknown')
                }
            }
            
        except Exception as e:
            return {
                'claim': f"Error generating response: {str(e)}",
                'confidence': 0.0,
                'metadata': {
                    'status': 'error',
                    'message': f'Response generation failed: {str(e)}'
                }
            }
    
    async def _generate_response(self, post_data: Dict[str, Any]) -> str:
        """Generate empathetic and helpful response."""
        crisis_level = self.current_torch.metadata.get('crisis_level', 'medium')
        
        prompt = f"""
        Generate a compassionate, helpful response to this Reddit post showing signs of mental health crisis.
        
        Post Title: {post_data['title']}
        Post Content: {post_data['content']}
        Crisis Level: {crisis_level}
        
        Guidelines:
        - Be empathetic and non-judgmental
        - Provide immediate crisis resources if urgency is high
        - Suggest professional help
        - Offer hope and support
        - Keep response under 200 words
        - Include crisis hotline numbers if appropriate
        
        Response:
        """
        
        return await self.llm_completion_with_mcp(prompt, channel="response_generation")


class CrisisLoggerCamper(Camper):
    """Camper that logs crisis incidents for tracking and analysis."""
    
    def __init__(self, party_box, config: dict, state_manager: StateManager):
        super().__init__(party_box, config)
        self.state_manager = state_manager
        self.current_torch = None
    
    async def process(self, input_torch: Optional[Torch] = None) -> Torch:
        """Override process to store the input torch."""
        self.current_torch = input_torch
        return await super().process(input_torch)
    
    async def override_prompt(self, raw_prompt: str) -> dict:
        """Override the base prompt for logging."""
        return {
            "system": "You are a crisis event logger.",
            "user": raw_prompt
        }
    
    async def override_prompt(self, raw_prompt: str) -> Dict[str, Any]:
        """Override the base prompt for crisis logging."""
        try:
            print(f"📝 CrisisLoggerCamper processing...")
            
            if not self.current_torch:
                return {
                    'claim': 'Error: No input torch available',
                    'confidence': 0.0,
                    'metadata': {
                        'status': 'error',
                        'message': 'No input torch available'
                    }
                }
            
            # Check if this is a crisis situation
            crisis_detected = self.current_torch.metadata.get('crisis_detected', False)
            post_data = self.current_torch.metadata.get('reddit_post', {})
            
            if not crisis_detected:
                return {
                    'claim': 'No logging needed - no crisis detected',
                    'confidence': 1.0,
                    'metadata': {
                        'logged': False,
                        'reason': 'No crisis detected'
                    }
                }
            
            # Log the crisis incident
            incident_data = {
                'timestamp': datetime.now().isoformat(),
                'post_id': post_data.get('id'),
                'subreddit': post_data.get('subreddit'),
                'title': post_data.get('title'),
                'crisis_score': self.current_torch.metadata.get('crisis_score', 0),
                'crisis_level': self.current_torch.metadata.get('crisis_level', 'unknown'),
                'keyword_matches': self.current_torch.metadata.get('keyword_matches', []),
                'llm_analysis': self.current_torch.metadata.get('llm_analysis', {})
            }
            
            # Store in state manager
            await self._log_crisis_incident(incident_data)
            
            return {
                'claim': f"Logged crisis incident for post: {post_data.get('title', 'Unknown')[:50]}",
                'confidence': 1.0,
                'metadata': {
                    'logged': True,
                    'incident_id': incident_data['post_id'],
                    'timestamp': incident_data['timestamp'],
                    'crisis_level': incident_data['crisis_level']
                }
            }
            
        except Exception as e:
            return {
                'claim': f"Error logging crisis: {str(e)}",
                'confidence': 0.0,
                'metadata': {
                    'status': 'error',
                    'message': f'Crisis logging failed: {str(e)}'
                }
            }
    
    async def _log_crisis_incident(self, incident_data: dict) -> None:
        """Log crisis incident to the state manager."""
        try:
            # Store the incident in the state manager
            await self.state_manager.log_mcp_message(
                message_id=f"crisis_{incident_data.get('post_id', 'unknown')}_{int(time.time())}",
                channel="crisis_alerts",
                message_type="crisis_incident",
                data=incident_data,
                direction="sent"
            )
        except Exception as e:
            print(f"Error logging to state manager: {e}")
            # Could also log to a file as backup
            print(f"Crisis incident data: {json.dumps(incident_data, indent=2)}")


async def run_reddit_crisis_demo():
    """Run the Reddit crisis tracker demo."""
    print("🔥 Starting Reddit Crisis Tracker Demo")
    print("=" * 50)
    
    # Initialize components
    reddit_api = MockRedditAPI()
    
    # Setup OpenRouter with environment variables and specified model
    openrouter_config = OpenRouterConfig(
        default_model="openai/gpt-oss-20b:free"
    )
    
    # Initialize storage and state management
    print("🔧 Initializing storage and state management...")
    box_driver = LocalDriver("./demo_storage")
    state_manager = StateManager("./demo_crisis_tracker.db")
    await state_manager.initialize()
    print("✅ State manager initialized")
    
    # Setup MCP protocol first
    print("🔗 Setting up MCP protocol...")
    transport = AsyncQueueTransport()
    protocol = MCPProtocol(transport)
    
    # Start the MCP protocol
    await protocol.start()
    print("✅ MCP protocol started")
    
    # Create campers with MCP protocol
    print("👥 Creating campers...")
    crisis_detector = CrisisDetectionCamper(box_driver, {"name": "CrisisDetectionCamper"}, openrouter_config)
    crisis_detector.setup_llm(openrouter_config, mcp_protocol=protocol)
    
    response_generator = ResponseGeneratorCamper(box_driver, {"name": "ResponseGeneratorCamper"}, openrouter_config)
    response_generator.setup_llm(openrouter_config, mcp_protocol=protocol)
    
    crisis_logger = CrisisLoggerCamper(box_driver, {"name": "CrisisLoggerCamper"}, state_manager)
    print("✅ Campers created with MCP support")
    
    # Create campfire
    print("🔥 Creating campfire...")
    campfire = Campfire(
        name="RedditCrisisTracker",
        campers=[crisis_detector, response_generator, crisis_logger],
        party_box=box_driver,
        mcp_protocol=protocol
    )
    print("✅ Campfire created")
    
    # Start the campfire in background
    print("🚀 Starting campfire...")
    campfire_task = asyncio.create_task(campfire.start())
    
    # Give it a moment to start up
    await asyncio.sleep(1)
    print("✅ Campfire started")
    
    try:
        print("📡 Monitoring Reddit for crisis posts...")
        
        # Simulate monitoring loop
        for round_num in range(3):
            print(f"\n🔍 Monitoring Round {round_num + 1}")
            
            # Fetch mock Reddit posts
            posts = await reddit_api.get_recent_posts(limit=5)
            
            for post in posts:
                print(f"\n📝 Processing post: {post.title[:50]}...")
                
                # Create torch for this post
                torch = Torch(
                    claim=f"Reddit post analysis: {post.title[:50]}",
                    metadata={'reddit_post': post.to_dict(), 'source': 'reddit', 'subreddit': post.subreddit},
                    source_campfire="reddit_crisis_tracker",
                    channel="crisis_detection"
                )
                
                # Process through campfire
                output_torches = await campfire.process_torch(torch)
                print(f"  📊 Received {len(output_torches)} output torches")
                
                # Find results from each camper
                crisis_torch = None
                response_torch = None
                logger_torch = None
                
                for i, output_torch in enumerate(output_torches):
                    camper_name = output_torch.metadata.get('camper_name')
                    print(f"    Torch {i}: camper_name='{camper_name}', claim='{output_torch.claim[:50]}...'")
                    if camper_name == 'CrisisDetectionCamper':
                        crisis_torch = output_torch
                        print(f"    Crisis detected: {output_torch.metadata.get('crisis_detected', 'unknown')}")
                    elif camper_name == 'ResponseGeneratorCamper':
                        response_torch = output_torch
                    elif camper_name == 'CrisisLoggerCamper':
                        logger_torch = output_torch
                
                # Display results
                if crisis_torch and crisis_torch.metadata.get('crisis_detected'):
                    crisis_score = crisis_torch.metadata.get('crisis_score', 0)
                    print(f"  🚨 CRISIS DETECTED (Score: {crisis_score:.2f})")
                    print(f"  📍 Subreddit: r/{post.subreddit}")
                    print(f"  🔑 Keywords: {crisis_torch.metadata.get('keyword_matches', [])}")
                    
                    if response_torch and response_torch.metadata.get('generated_response'):
                        response_text = response_torch.metadata['generated_response']
                        print(f"  💬 Generated Response Preview:")
                        print(f"     {response_text[:100]}...")
                    
                    if logger_torch and logger_torch.metadata.get('incident_id'):
                        print(f"  📝 Logged as: {logger_torch.metadata['incident_id']}")
                else:
                    print(f"  ✅ No crisis detected")
            
            # Wait before next round
            await asyncio.sleep(2)
        
        # Display summary statistics
        print(f"\n📊 Demo Summary")
        print("=" * 30)
        stats = await state_manager.get_statistics()
        print(f"Total torches processed: {stats.get('total_torches', 0)}")
        print(f"Total processing records: {stats.get('total_processing_records', 0)}")
        print(f"Successful processing: {stats.get('successful_processing', 0)}")
        print(f"Failed processing: {stats.get('failed_processing', 0)}")
        print(f"Total campfires: {stats.get('total_campfires', 0)}")
        print(f"Running campfires: {stats.get('running_campfires', 0)}")
        
    finally:
        # Cleanup
        print("\n🛑 Stopping campfire...")
        await campfire.stop()
        campfire_task.cancel()
        try:
            await campfire_task
        except asyncio.CancelledError:
            pass
        
        # Stop MCP protocol
        print("🔗 Stopping MCP protocol...")
        await protocol.stop()
        print("✅ MCP protocol stopped")
        
        print("🔥 Demo completed!")


if __name__ == "__main__":
    # Note: This demo uses mock data and won't make real API calls
    # To use with real Reddit API and OpenRouter, you would need:
    # 1. Reddit API credentials (praw library)
    # 2. Valid OpenRouter API key
    # 3. Proper error handling for rate limits
    
    print("Reddit Crisis Tracker Demo")
    print("This demo simulates crisis detection in Reddit posts using the Campfires framework.")
    print("Note: Uses mock data - no real API calls are made.")
    print()
    
    asyncio.run(run_reddit_crisis_demo())