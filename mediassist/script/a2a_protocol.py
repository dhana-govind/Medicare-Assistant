"""
A2A Protocol - Agent-to-Agent Communication Protocol
=====================================================

This module implements explicit agent-to-agent (A2A) messaging protocol
for the MediSync multi-agent system. It provides:

1. Message Queue System - For async communication between agents
2. Message Types - Request, Response, Broadcast, Notification
3. Message Handlers - Routing and processing
4. Communication Patterns - Request-Reply, Publish-Subscribe, Fire-and-Forget

Author: MediSync Team
Date: November 2025
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
import json
import uuid
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Message types for A2A communication."""
    REQUEST = "request"          # Agent A requests action from Agent B
    RESPONSE = "response"        # Agent B responds to Agent A's request
    BROADCAST = "broadcast"      # Send message to all agents
    NOTIFICATION = "notification"  # One-way notification
    ACKNOWLEDGMENT = "ack"       # Acknowledge receipt


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Message:
    """
    A2A Protocol Message Structure
    
    Represents a single message exchanged between agents.
    Each message has a unique ID, timestamp, and correlation tracking.
    """
    
    # Core message fields
    sender: str                 # Agent that sent the message
    recipient: str              # Intended recipient(s)
    message_type: MessageType   # Type of message (request, response, etc.)
    payload: Dict[str, Any]     # Message content/data
    
    # Metadata
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None  # Link related messages
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: MessagePriority = MessagePriority.NORMAL
    
    # Response handling
    requires_response: bool = False
    response_timeout: int = 30  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "priority": self.priority.name,
            "requires_response": self.requires_response,
        }
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        msg_dict = self.to_dict()
        msg_dict["priority"] = self.priority.name
        msg_dict["message_type"] = self.message_type.value
        return json.dumps(msg_dict, indent=2)


@dataclass
class MessageHandler:
    """Handles routing and processing of messages."""
    
    handler_fn: Callable
    message_type: MessageType
    sender: Optional[str] = None  # Specific sender or None for all
    priority: int = 0


class A2AProtocol:
    """
    Agent-to-Agent Protocol Manager
    
    Manages message queue, routing, and communication between agents.
    Implements publish-subscribe and request-response patterns.
    """
    
    def __init__(self, max_queue_size: int = 1000):
        """Initialize A2A Protocol manager."""
        self.max_queue_size = max_queue_size
        
        # Message storage
        self.message_queue: List[Message] = []
        self.processed_messages: List[Message] = []
        self.failed_messages: List[Message] = []
        
        # Handlers and subscriptions
        self.handlers: Dict[str, List[MessageHandler]] = {}  # key = "message_type:sender"
        self.subscribers: Dict[str, Set[str]] = {}  # Topics to subscriber agents
        self.pending_responses: Dict[str, Message] = {}  # correlation_id -> original_message
        
        # Agent registry
        self.registered_agents: Set[str] = set()
        
        # Statistics
        self.stats = {
            "total_messages": 0,
            "processed_messages": 0,
            "failed_messages": 0,
            "average_latency": 0.0,
        }
    
    def register_agent(self, agent_id: str) -> None:
        """Register a new agent with the protocol."""
        if agent_id in self.registered_agents:
            logger.warning(f"Agent {agent_id} already registered")
            return
        
        self.registered_agents.add(agent_id)
        logger.info(f"Agent {agent_id} registered with A2A Protocol")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the protocol."""
        if agent_id not in self.registered_agents:
            logger.warning(f"Agent {agent_id} not found in registry")
            return
        
        self.registered_agents.discard(agent_id)
        logger.info(f"Agent {agent_id} unregistered from A2A Protocol")
    
    def subscribe(self, agent_id: str, topic: str) -> None:
        """Subscribe an agent to a broadcast topic."""
        if topic not in self.subscribers:
            self.subscribers[topic] = set()
        
        self.subscribers[topic].add(agent_id)
        logger.info(f"Agent {agent_id} subscribed to topic: {topic}")
    
    def unsubscribe(self, agent_id: str, topic: str) -> None:
        """Unsubscribe an agent from a topic."""
        if topic in self.subscribers:
            self.subscribers[topic].discard(agent_id)
            logger.info(f"Agent {agent_id} unsubscribed from topic: {topic}")
    
    def register_handler(
        self,
        handler_fn: Callable,
        message_type: MessageType,
        sender: Optional[str] = None
    ) -> str:
        """Register a message handler for specific message types."""
        handler_key = f"{message_type.value}:{sender or 'all'}"
        
        if handler_key not in self.handlers:
            self.handlers[handler_key] = []
        
        handler = MessageHandler(handler_fn, message_type, sender)
        self.handlers[handler_key].append(handler)
        
        logger.info(f"Handler registered for {handler_key}")
        return handler_key
    
    def send_message(self, message: Message) -> str:
        """
        Send a message to recipient agent(s).
        
        Args:
            message: Message object to send
            
        Returns:
            message_id: Unique identifier for the sent message
        """
        # Validate sender
        if message.sender not in self.registered_agents:
            logger.warning(f"Sender {message.sender} not registered")
        
        # Add to queue
        if len(self.message_queue) >= self.max_queue_size:
            removed = self.message_queue.pop(0)
            logger.warning(f"Message queue full, removed oldest message: {removed.message_id}")
        
        self.message_queue.append(message)
        self.stats["total_messages"] += 1
        
        logger.info(
            f"Message sent from {message.sender} to {message.recipient}: "
            f"{message.message_type.value} (ID: {message.message_id})"
        )
        
        return message.message_id
    
    def send_request(
        self,
        sender: str,
        recipient: str,
        action: str,
        data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> str:
        """
        Send a request message from one agent to another.
        
        Args:
            sender: Sending agent ID
            recipient: Recipient agent ID
            action: Action to perform
            data: Action parameters
            priority: Message priority
            
        Returns:
            message_id: Unique message identifier
        """
        message = Message(
            sender=sender,
            recipient=recipient,
            message_type=MessageType.REQUEST,
            payload={"action": action, "data": data},
            priority=priority,
            requires_response=True,
            correlation_id=str(uuid.uuid4())
        )
        
        return self.send_message(message)
    
    def send_response(
        self,
        sender: str,
        recipient: str,
        correlation_id: str,
        result: Dict[str, Any],
        success: bool = True
    ) -> str:
        """
        Send a response message.
        
        Args:
            sender: Responding agent ID
            recipient: Original requester ID
            correlation_id: ID linking to original request
            result: Response data
            success: Whether operation succeeded
            
        Returns:
            message_id: Unique message identifier
        """
        message = Message(
            sender=sender,
            recipient=recipient,
            message_type=MessageType.RESPONSE,
            payload={
                "success": success,
                "result": result,
            },
            correlation_id=correlation_id,
            priority=MessagePriority.NORMAL
        )
        
        return self.send_message(message)
    
    def broadcast_message(
        self,
        sender: str,
        topic: str,
        data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> str:
        """
        Broadcast a message to all subscribers of a topic.
        
        Args:
            sender: Sending agent ID
            topic: Broadcast topic
            data: Message data
            priority: Message priority
            
        Returns:
            message_id: Unique message identifier
        """
        subscribers = self.subscribers.get(topic, set())
        recipient_list = ",".join(subscribers) if subscribers else "all"
        
        message = Message(
            sender=sender,
            recipient=recipient_list,
            message_type=MessageType.BROADCAST,
            payload={"topic": topic, "data": data},
            priority=priority
        )
        
        return self.send_message(message)
    
    def notify(
        self,
        sender: str,
        recipient: str,
        event: str,
        details: Dict[str, Any]
    ) -> str:
        """
        Send a one-way notification.
        
        Args:
            sender: Sending agent ID
            recipient: Recipient agent ID
            event: Event type/name
            details: Event details
            
        Returns:
            message_id: Unique message identifier
        """
        message = Message(
            sender=sender,
            recipient=recipient,
            message_type=MessageType.NOTIFICATION,
            payload={"event": event, "details": details},
            priority=MessagePriority.NORMAL
        )
        
        return self.send_message(message)
    
    def process_message(self, message: Message) -> Optional[Message]:
        """
        Process a single message by routing to appropriate handlers.
        
        Args:
            message: Message to process
            
        Returns:
            Response message if applicable, None otherwise
        """
        try:
            # Find matching handlers
            handler_key = f"{message.message_type.value}:all"
            specific_key = f"{message.message_type.value}:{message.sender}"
            
            handlers = (
                self.handlers.get(handler_key, []) +
                self.handlers.get(specific_key, [])
            )
            
            if not handlers:
                logger.warning(f"No handler found for message type: {message.message_type.value}")
                self.failed_messages.append(message)
                self.stats["failed_messages"] += 1
                return None
            
            # Execute first matching handler
            handler = handlers[0]
            result = handler.handler_fn(message)
            
            self.processed_messages.append(message)
            self.stats["processed_messages"] += 1
            
            logger.info(f"Message {message.message_id} processed successfully")
            
            # Track response if needed
            if result and isinstance(result, Message):
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {str(e)}")
            self.failed_messages.append(message)
            self.stats["failed_messages"] += 1
            return None
    
    def process_queue(self) -> List[Message]:
        """
        Process all messages in the queue.
        
        Returns:
            List of response messages generated
        """
        responses = []
        messages_to_process = list(self.message_queue)
        self.message_queue.clear()
        
        for message in messages_to_process:
            response = self.process_message(message)
            if response:
                responses.append(response)
        
        logger.info(f"Processed {len(messages_to_process)} messages")
        return responses
    
    def get_messages_for_agent(self, agent_id: str) -> List[Message]:
        """Get all unprocessed messages for a specific agent."""
        return [
            msg for msg in self.message_queue
            if agent_id in msg.recipient or msg.recipient == "all"
        ]
    
    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Retrieve a specific message by ID."""
        # Search in queue
        for msg in self.message_queue:
            if msg.message_id == message_id:
                return msg
        
        # Search in processed
        for msg in self.processed_messages:
            if msg.message_id == message_id:
                return msg
        
        # Search in failed
        for msg in self.failed_messages:
            if msg.message_id == message_id:
                return msg
        
        return None
    
    def get_correlation_chain(self, correlation_id: str) -> List[Message]:
        """Get all messages related by correlation ID."""
        all_messages = (
            self.message_queue +
            self.processed_messages +
            self.failed_messages
        )
        
        return [
            msg for msg in all_messages
            if msg.correlation_id == correlation_id
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get protocol statistics."""
        return {
            **self.stats,
            "registered_agents": len(self.registered_agents),
            "queue_size": len(self.message_queue),
            "processed_count": len(self.processed_messages),
            "failed_count": len(self.failed_messages),
            "topics": len(self.subscribers),
        }
    
    def clear_history(self) -> None:
        """Clear processed and failed message history."""
        self.processed_messages.clear()
        self.failed_messages.clear()
        logger.info("Message history cleared")
    
    def export_messages(self, limit: Optional[int] = None) -> str:
        """Export messages as JSON for audit/logging."""
        all_messages = (
            self.message_queue +
            self.processed_messages +
            self.failed_messages
        )
        
        if limit:
            all_messages = all_messages[-limit:]
        
        messages_dict = [msg.to_dict() for msg in all_messages]
        return json.dumps(messages_dict, indent=2)


# Global A2A Protocol instance (singleton pattern)
_protocol_instance: Optional[A2AProtocol] = None


def get_a2a_protocol() -> A2AProtocol:
    """Get or create the global A2A Protocol instance."""
    global _protocol_instance
    if _protocol_instance is None:
        _protocol_instance = A2AProtocol()
    return _protocol_instance


def reset_protocol() -> None:
    """Reset the global protocol instance (for testing)."""
    global _protocol_instance
    _protocol_instance = None
