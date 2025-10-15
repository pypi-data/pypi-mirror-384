"""
Transport layer implementations for MCP.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from collections import deque


logger = logging.getLogger(__name__)


class Transport(ABC):
    """
    Abstract base class for MCP transport layers.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize transport.
        
        Args:
            config: Transport configuration
        """
        self.config = config or {}
        self.is_running = False
    
    @abstractmethod
    async def start(self) -> None:
        """Start the transport."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the transport."""
        pass
    
    @abstractmethod
    async def send(self, message: Dict[str, Any]) -> None:
        """
        Send a message.
        
        Args:
            message: Message to send
        """
        pass
    
    @abstractmethod
    async def receive(self) -> Optional[Dict[str, Any]]:
        """
        Receive a message.
        
        Returns:
            Received message or None if no message available
        """
        pass


class AsyncQueueTransport(Transport):
    """
    In-memory async queue transport for testing and single-process use.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize queue transport.
        
        Args:
            config: Transport configuration
        """
        super().__init__(config)
        self.send_queue: asyncio.Queue = asyncio.Queue()
        self.receive_queue: asyncio.Queue = asyncio.Queue()
        self.max_queue_size = self.config.get('max_queue_size', 1000)
    
    async def start(self) -> None:
        """Start the transport."""
        self.is_running = True
        logger.info("AsyncQueueTransport started")
    
    async def stop(self) -> None:
        """Stop the transport."""
        self.is_running = False
        logger.info("AsyncQueueTransport stopped")
    
    async def send(self, message: Dict[str, Any]) -> None:
        """
        Send a message by putting it in the send queue.
        
        Args:
            message: Message to send
        """
        if not self.is_running:
            raise RuntimeError("Transport not running")
        
        try:
            # In this simple implementation, send queue feeds into receive queue
            # In a real distributed system, this would send over network
            await self.receive_queue.put(message)
            logger.debug("Message sent via AsyncQueueTransport")
        except asyncio.QueueFull:
            logger.error("Send queue is full, dropping message")
    
    async def receive(self) -> Optional[Dict[str, Any]]:
        """
        Receive a message from the receive queue.
        
        Returns:
            Received message or None if timeout
        """
        if not self.is_running:
            return None
        
        try:
            # Wait for message with timeout
            message = await asyncio.wait_for(
                self.receive_queue.get(),
                timeout=1.0
            )
            return message
        except asyncio.TimeoutError:
            return None
    
    def get_queue_sizes(self) -> Dict[str, int]:
        """Get current queue sizes."""
        return {
            'send_queue': self.send_queue.qsize(),
            'receive_queue': self.receive_queue.qsize()
        }


class WebSocketTransport(Transport):
    """
    WebSocket transport for network communication.
    Note: This is a basic implementation - production use would need more robust error handling.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize WebSocket transport.
        
        Args:
            config: Transport configuration with 'url' and optional 'headers'
        """
        super().__init__(config)
        self.url = self.config.get('url', 'ws://localhost:8765')
        self.headers = self.config.get('headers', {})
        self.websocket = None
        self.receive_queue: asyncio.Queue = asyncio.Queue()
        self._receive_task = None
    
    async def start(self) -> None:
        """Start the WebSocket connection."""
        try:
            import websockets
            
            self.websocket = await websockets.connect(
                self.url,
                extra_headers=self.headers
            )
            self.is_running = True
            
            # Start receive task
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            logger.info(f"WebSocketTransport connected to {self.url}")
            
        except ImportError:
            raise RuntimeError("websockets library not installed. Install with: pip install websockets")
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the WebSocket connection."""
        self.is_running = False
        
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        if self.websocket:
            await self.websocket.close()
        
        logger.info("WebSocketTransport stopped")
    
    async def send(self, message: Dict[str, Any]) -> None:
        """
        Send a message via WebSocket.
        
        Args:
            message: Message to send
        """
        if not self.is_running or not self.websocket:
            raise RuntimeError("Transport not running")
        
        try:
            import json
            message_str = json.dumps(message)
            await self.websocket.send(message_str)
            logger.debug("Message sent via WebSocket")
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            raise
    
    async def receive(self) -> Optional[Dict[str, Any]]:
        """
        Receive a message from the WebSocket.
        
        Returns:
            Received message or None if timeout
        """
        if not self.is_running:
            return None
        
        try:
            message = await asyncio.wait_for(
                self.receive_queue.get(),
                timeout=1.0
            )
            return message
        except asyncio.TimeoutError:
            return None
    
    async def _receive_loop(self) -> None:
        """Background task to receive WebSocket messages."""
        import json
        
        try:
            async for message_str in self.websocket:
                try:
                    message = json.loads(message_str)
                    await self.receive_queue.put(message)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode WebSocket message: {e}")
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")
        except Exception as e:
            logger.error(f"WebSocket receive loop error: {e}")
        finally:
            self.is_running = False


class RedisTransport(Transport):
    """
    Redis pub/sub transport for distributed communication.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Redis transport.
        
        Args:
            config: Redis configuration with 'host', 'port', 'db', etc.
        """
        super().__init__(config)
        self.host = self.config.get('host', 'localhost')
        self.port = self.config.get('port', 6379)
        self.db = self.config.get('db', 0)
        self.password = self.config.get('password')
        self.channel_prefix = self.config.get('channel_prefix', 'campfires:')
        
        self.redis_client = None
        self.pubsub = None
        self.receive_queue: asyncio.Queue = asyncio.Queue()
        self._receive_task = None
    
    async def start(self) -> None:
        """Start the Redis connection."""
        try:
            import redis.asyncio as redis
            
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            # Setup pub/sub
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe(f"{self.channel_prefix}*")
            
            self.is_running = True
            
            # Start receive task
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            logger.info(f"RedisTransport connected to {self.host}:{self.port}")
            
        except ImportError:
            raise RuntimeError("redis library not installed. Install with: pip install redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the Redis connection."""
        self.is_running = False
        
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("RedisTransport stopped")
    
    async def send(self, message: Dict[str, Any]) -> None:
        """
        Send a message via Redis pub/sub.
        
        Args:
            message: Message to send
        """
        if not self.is_running or not self.redis_client:
            raise RuntimeError("Transport not running")
        
        try:
            import json
            
            channel = message.get('channel', 'default')
            redis_channel = f"{self.channel_prefix}{channel}"
            message_str = json.dumps(message)
            
            await self.redis_client.publish(redis_channel, message_str)
            logger.debug(f"Message published to Redis channel: {redis_channel}")
            
        except Exception as e:
            logger.error(f"Failed to publish Redis message: {e}")
            raise
    
    async def receive(self) -> Optional[Dict[str, Any]]:
        """
        Receive a message from Redis pub/sub.
        
        Returns:
            Received message or None if timeout
        """
        if not self.is_running:
            return None
        
        try:
            message = await asyncio.wait_for(
                self.receive_queue.get(),
                timeout=1.0
            )
            return message
        except asyncio.TimeoutError:
            return None
    
    async def _receive_loop(self) -> None:
        """Background task to receive Redis messages."""
        import json
        
        try:
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        await self.receive_queue.put(data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode Redis message: {e}")
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
        except Exception as e:
            logger.error(f"Redis receive loop error: {e}")
        finally:
            self.is_running = False


class FileTransport(Transport):
    """
    File-based transport for debugging and testing.
    Messages are written to/read from files.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize file transport.
        
        Args:
            config: Configuration with 'directory' for file storage
        """
        super().__init__(config)
        self.directory = self.config.get('directory', './mcp_messages')
        self.send_file = f"{self.directory}/send.jsonl"
        self.receive_file = f"{self.directory}/receive.jsonl"
        self.message_counter = 0
        
        # Create directory
        import os
        os.makedirs(self.directory, exist_ok=True)
    
    async def start(self) -> None:
        """Start the file transport."""
        self.is_running = True
        logger.info(f"FileTransport started with directory: {self.directory}")
    
    async def stop(self) -> None:
        """Stop the file transport."""
        self.is_running = False
        logger.info("FileTransport stopped")
    
    async def send(self, message: Dict[str, Any]) -> None:
        """
        Send a message by writing to file.
        
        Args:
            message: Message to send
        """
        if not self.is_running:
            raise RuntimeError("Transport not running")
        
        try:
            import json
            import aiofiles
            
            # Add timestamp and counter
            message['_transport_timestamp'] = asyncio.get_event_loop().time()
            message['_transport_counter'] = self.message_counter
            self.message_counter += 1
            
            # Write to send file (and also to receive file for loopback)
            message_str = json.dumps(message) + '\n'
            
            async with aiofiles.open(self.send_file, 'a') as f:
                await f.write(message_str)
            
            # For testing, also write to receive file
            async with aiofiles.open(self.receive_file, 'a') as f:
                await f.write(message_str)
            
            logger.debug("Message written to file")
            
        except Exception as e:
            logger.error(f"Failed to write message to file: {e}")
            raise
    
    async def receive(self) -> Optional[Dict[str, Any]]:
        """
        Receive a message by reading from file.
        
        Returns:
            Received message or None if no new messages
        """
        if not self.is_running:
            return None
        
        try:
            import json
            import aiofiles
            import os
            
            if not os.path.exists(self.receive_file):
                return None
            
            # Read all lines and return the last unprocessed one
            # This is a simple implementation - production would need better tracking
            async with aiofiles.open(self.receive_file, 'r') as f:
                lines = await f.readlines()
            
            if lines:
                # Return the last line (most recent message)
                last_line = lines[-1].strip()
                if last_line:
                    return json.loads(last_line)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to read message from file: {e}")
            return None


# Transport factory for easy creation
def create_transport(transport_type: str, config: Dict[str, Any] = None) -> Transport:
    """
    Create a transport instance.
    
    Args:
        transport_type: Type of transport ('queue', 'websocket', 'redis', 'file')
        config: Transport configuration
        
    Returns:
        Transport instance
    """
    transport_map = {
        'queue': AsyncQueueTransport,
        'websocket': WebSocketTransport,
        'redis': RedisTransport,
        'file': FileTransport
    }
    
    transport_class = transport_map.get(transport_type.lower())
    if not transport_class:
        raise ValueError(f"Unknown transport type: {transport_type}")
    
    return transport_class(config)