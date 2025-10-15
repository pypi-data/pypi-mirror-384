"""
Model Context Protocol (MCP) implementation for Campfires.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
from abc import ABC, abstractmethod

from .transport import Transport, AsyncQueueTransport


logger = logging.getLogger(__name__)


class MCPMessage:
    """
    Represents an MCP message.
    """
    
    def __init__(
        self,
        channel: str,
        data: Dict[str, Any],
        message_type: str = "torch",
        timestamp: Optional[datetime] = None,
        message_id: Optional[str] = None
    ):
        """
        Initialize an MCP message.
        
        Args:
            channel: Channel name for routing
            data: Message payload
            message_type: Type of message (torch, control, etc.)
            timestamp: Message timestamp
            message_id: Unique message identifier
        """
        self.channel = channel
        self.data = data
        self.message_type = message_type
        self.timestamp = timestamp or datetime.utcnow()
        self.message_id = message_id or self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate a unique message ID."""
        import uuid
        return str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            'channel': self.channel,
            'data': self.data,
            'message_type': self.message_type,
            'timestamp': self.timestamp.isoformat(),
            'message_id': self.message_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Create message from dictionary."""
        timestamp = datetime.fromisoformat(data['timestamp'])
        return cls(
            channel=data['channel'],
            data=data['data'],
            message_type=data.get('message_type', 'torch'),
            timestamp=timestamp,
            message_id=data.get('message_id')
        )
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MCPMessage':
        """Create message from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class ChannelManager:
    """
    Manages channel subscriptions and message routing.
    """
    
    def __init__(self):
        """Initialize the channel manager."""
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.channel_history: Dict[str, List[MCPMessage]] = {}
        self.max_history_per_channel = 100
    
    async def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to a channel.
        
        Args:
            channel: Channel name to subscribe to
            callback: Function to call when message received
        """
        if channel not in self.subscriptions:
            self.subscriptions[channel] = []
        
        self.subscriptions[channel].append(callback)
        logger.info(f"Subscribed to channel: {channel}")
    
    async def unsubscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Unsubscribe from a channel.
        
        Args:
            channel: Channel name to unsubscribe from
            callback: Callback function to remove
        """
        if channel in self.subscriptions:
            try:
                self.subscriptions[channel].remove(callback)
                if not self.subscriptions[channel]:
                    del self.subscriptions[channel]
                logger.info(f"Unsubscribed from channel: {channel}")
            except ValueError:
                logger.warning(f"Callback not found for channel: {channel}")
    
    async def publish(self, message: MCPMessage) -> None:
        """
        Publish a message to a channel.
        
        Args:
            message: Message to publish
        """
        channel = message.channel
        
        # Store in history
        if channel not in self.channel_history:
            self.channel_history[channel] = []
        
        self.channel_history[channel].append(message)
        
        # Trim history if too long
        if len(self.channel_history[channel]) > self.max_history_per_channel:
            self.channel_history[channel] = self.channel_history[channel][-self.max_history_per_channel:]
        
        # Notify subscribers
        if channel in self.subscriptions:
            for callback in self.subscriptions[channel]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message.data)
                    else:
                        callback(message.data)
                except Exception as e:
                    logger.error(f"Error in channel callback for {channel}: {e}")
        
        logger.debug(f"Published message to channel: {channel}")
    
    def get_channel_history(self, channel: str, limit: int = 10) -> List[MCPMessage]:
        """
        Get recent messages from a channel.
        
        Args:
            channel: Channel name
            limit: Maximum number of messages to return
            
        Returns:
            List of recent messages
        """
        if channel not in self.channel_history:
            return []
        
        return self.channel_history[channel][-limit:]
    
    def get_active_channels(self) -> List[str]:
        """Get list of channels with active subscriptions."""
        return list(self.subscriptions.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get channel manager statistics."""
        return {
            'active_channels': len(self.subscriptions),
            'total_subscriptions': sum(len(subs) for subs in self.subscriptions.values()),
            'channels_with_history': len(self.channel_history),
            'total_messages_in_history': sum(len(hist) for hist in self.channel_history.values())
        }


class MCPProtocol:
    """
    Main MCP protocol implementation.
    """
    
    def __init__(self, transport: Optional[Transport] = None):
        """
        Initialize the MCP protocol.
        
        Args:
            transport: Transport layer for message delivery
        """
        self.transport = transport or AsyncQueueTransport()
        self.channel_manager = ChannelManager()
        self.is_running = False
        self._message_handlers: Dict[str, Callable] = {}
        
        # Setup default message handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self) -> None:
        """Setup default message type handlers."""
        self._message_handlers['torch'] = self._handle_torch_message
        self._message_handlers['control'] = self._handle_control_message
        self._message_handlers['heartbeat'] = self._handle_heartbeat_message
    
    async def start(self) -> None:
        """Start the MCP protocol."""
        if self.is_running:
            logger.warning("MCP protocol is already running")
            return
        
        self.is_running = True
        logger.info("Starting MCP protocol")
        
        # Start transport
        await self.transport.start()
        
        # Start message processing loop
        asyncio.create_task(self._message_processing_loop())
    
    async def stop(self) -> None:
        """Stop the MCP protocol."""
        logger.info("Stopping MCP protocol")
        self.is_running = False
        
        # Stop transport
        await self.transport.stop()
    
    async def send_message(self, channel: str, data: Dict[str, Any], message_type: str = "torch") -> None:
        """
        Send a message via MCP.
        
        Args:
            channel: Target channel
            data: Message data
            message_type: Type of message
        """
        message = MCPMessage(
            channel=channel,
            data=data,
            message_type=message_type
        )
        
        await self.transport.send(message.to_dict())
        logger.debug(f"Sent {message_type} message to channel: {channel}")
    
    async def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to a channel.
        
        Args:
            channel: Channel to subscribe to
            callback: Callback function for messages
        """
        await self.channel_manager.subscribe(channel, callback)
    
    async def unsubscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Unsubscribe from a channel.
        
        Args:
            channel: Channel to unsubscribe from
            callback: Callback function to remove
        """
        await self.channel_manager.unsubscribe(channel, callback)
    
    async def _message_processing_loop(self) -> None:
        """Main message processing loop."""
        while self.is_running:
            try:
                # Receive message from transport
                message_data = await self.transport.receive()
                
                if message_data:
                    message = MCPMessage.from_dict(message_data)
                    await self._process_message(message)
                
            except Exception as e:
                logger.error(f"Error in message processing loop: {e}")
                await asyncio.sleep(1)
    
    async def _process_message(self, message: MCPMessage) -> None:
        """
        Process an incoming message.
        
        Args:
            message: Message to process
        """
        try:
            # Handle message based on type
            handler = self._message_handlers.get(message.message_type)
            if handler:
                await handler(message)
            else:
                logger.warning(f"No handler for message type: {message.message_type}")
            
            # Publish to channel subscribers
            await self.channel_manager.publish(message)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _handle_torch_message(self, message: MCPMessage) -> None:
        """
        Handle torch messages.
        
        Args:
            message: Torch message
        """
        logger.debug(f"Handling torch message on channel: {message.channel}")
        # Torch messages are handled by channel subscribers
    
    async def _handle_control_message(self, message: MCPMessage) -> None:
        """
        Handle control messages.
        
        Args:
            message: Control message
        """
        logger.debug(f"Handling control message: {message.data}")
        
        # Handle different control commands
        command = message.data.get('command')
        if command == 'ping':
            await self._send_pong(message.channel)
        elif command == 'shutdown':
            await self.stop()
        elif command == 'stats':
            await self._send_stats(message.channel)
    
    async def _handle_heartbeat_message(self, message: MCPMessage) -> None:
        """
        Handle heartbeat messages.
        
        Args:
            message: Heartbeat message
        """
        logger.debug("Received heartbeat")
        # Heartbeats are used to keep connections alive
    
    async def _send_pong(self, channel: str) -> None:
        """Send pong response."""
        await self.send_message(channel, {'response': 'pong'}, 'control')
    
    async def _send_stats(self, channel: str) -> None:
        """Send protocol statistics."""
        stats = {
            'protocol_running': self.is_running,
            'transport_type': self.transport.__class__.__name__,
            'channel_stats': self.channel_manager.get_stats()
        }
        await self.send_message(channel, {'stats': stats}, 'control')
    
    def add_message_handler(self, message_type: str, handler: Callable[[MCPMessage], None]) -> None:
        """
        Add a custom message handler.
        
        Args:
            message_type: Type of message to handle
            handler: Handler function
        """
        self._message_handlers[message_type] = handler
    
    def get_stats(self) -> Dict[str, Any]:
        """Get protocol statistics."""
        return {
            'is_running': self.is_running,
            'transport_type': self.transport.__class__.__name__,
            'channel_manager_stats': self.channel_manager.get_stats(),
            'message_handlers': list(self._message_handlers.keys())
        }


class MCPClient:
    """
    Simple MCP client for testing and basic usage.
    """
    
    def __init__(self, protocol: MCPProtocol):
        """
        Initialize MCP client.
        
        Args:
            protocol: MCP protocol instance
        """
        self.protocol = protocol
        self.received_messages: List[MCPMessage] = []
    
    async def send_torch(self, channel: str, torch_data: Dict[str, Any]) -> None:
        """
        Send a torch message.
        
        Args:
            channel: Target channel
            torch_data: Torch data
        """
        await self.protocol.send_message(channel, torch_data, 'torch')
    
    async def subscribe_to_channel(self, channel: str) -> None:
        """
        Subscribe to a channel and store received messages.
        
        Args:
            channel: Channel to subscribe to
        """
        await self.protocol.subscribe(channel, self._message_callback)
    
    async def _message_callback(self, data: Dict[str, Any]) -> None:
        """Callback for received messages."""
        # Note: This is simplified - in practice you'd want to reconstruct the full message
        self.received_messages.append(data)
    
    def get_received_messages(self) -> List[Dict[str, Any]]:
        """Get all received messages."""
        return self.received_messages.copy()
    
    def clear_received_messages(self) -> None:
        """Clear received messages."""
        self.received_messages.clear()