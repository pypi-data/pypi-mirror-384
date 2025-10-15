"""
Conversation State Management for VRIN SDK
Adds stateful conversation support to VRINClient

Usage:
    from vrin import VRINClient
    from vrin.conversation import ConversationMixin

    # Or use directly:
    client = VRINClient(api_key="vrin_your_key")
    client.start_conversation()
    response = client.query("What is machine learning?")
    # Continue conversation with context...
"""

import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationMixin:
    """
    Mixin to add conversation state management to VRINClient

    Provides:
    - Multi-turn conversations with context
    - Automatic session management
    - Conversation history retrieval
    - Session listing and management
    """

    def __init__(self):
        self.current_session_id: Optional[str] = None
        self.session_history: List[str] = []
        self._pending_specialization_id: Optional[str] = None

    def start_conversation(self, user_specialization_id: Optional[str] = None):
        """
        Start a new conversation session

        Args:
            user_specialization_id: Optional custom AI expert configuration

        Returns:
            self (for method chaining)

        Example:
            client.start_conversation().query("First question")
        """
        self.current_session_id = None  # Will be created on first query
        self._pending_specialization_id = user_specialization_id

        logger.info("Started new conversation session")
        return self

    def query(
        self,
        query: str,
        maintain_context: bool = True,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Query VRIN with automatic conversation context management

        Args:
            query: The question to ask
            maintain_context: If True, maintains conversation context (default)
                            If False, starts fresh stateless query
            session_id: Optional explicit session ID (overrides current_session_id)
            **kwargs: Additional parameters to pass to the query

        Returns:
            {
                'success': True,
                'summary': 'Answer text...',
                'session_id': 'conv_abc123',
                'conversation_turn': 3,
                'total_facts': 25,
                'entities_found': ['Entity1', 'Entity2'],
                'search_time': '2.5s'
            }

        Example:
            # Multi-turn conversation
            client.start_conversation()
            r1 = client.query("What was Cadence's 2010 stock value?")
            r2 = client.query("What about 2011?")  # Has context from r1
            r3 = client.query("What was the percentage increase?")  # Has full context

            # Stateless query (no context)
            r4 = client.query("Unrelated question", maintain_context=False)
        """
        payload = {
            'query': query,
            'maintain_context': maintain_context,
            **kwargs
        }

        # Use explicit session_id or current session
        if session_id:
            payload['session_id'] = session_id
        elif maintain_context and self.current_session_id:
            payload['session_id'] = self.current_session_id
        elif maintain_context and self._pending_specialization_id:
            payload['user_specialization_id'] = self._pending_specialization_id

        try:
            response = requests.post(
                f"{self.rag_base_url}/query",
                headers=self.headers,
                json=payload,
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            # Store session ID for next query
            if maintain_context and result.get('session_id'):
                if not self.current_session_id:
                    logger.info(f"Created new session: {result['session_id']}")
                self.current_session_id = result['session_id']

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Query request failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to execute query'
            }

    def end_conversation(self):
        """
        End current conversation session

        Example:
            client.start_conversation()
            # ... multiple queries ...
            client.end_conversation()
        """
        if self.current_session_id:
            self.session_history.append(self.current_session_id)
            logger.info(f"Ended conversation session: {self.current_session_id}")
            self.current_session_id = None

        return self

    def get_conversation_history(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve full conversation history for a session

        Args:
            session_id: Session ID to retrieve (defaults to current session)

        Returns:
            {
                'session_id': 'conv_abc123',
                'title': 'Cadence Stock Analysis',
                'created_at': '2025-09-30T10:00:00Z',
                'last_updated': '2025-09-30T10:15:00Z',
                'turn_count': 5,
                'is_active': True,
                'messages': [
                    {'role': 'user', 'content': '...', 'timestamp': '...'},
                    {'role': 'assistant', 'content': '...', 'timestamp': '...'}
                ],
                'metadata': {
                    'total_tokens': 1500,
                    'active_entities': ['Cadence', 'Stock'],
                    'learned_facts_count': 2,
                    'summary': '...'
                }
            }

        Example:
            history = client.get_conversation_history()
            print(f"Conversation: {history['title']}")
            print(f"Turns: {history['turn_count']}")
        """
        target_session_id = session_id or self.current_session_id

        if not target_session_id:
            return {
                'success': False,
                'error': 'No active session'
            }

        try:
            # Use new conversation history API
            response = requests.get(
                f"https://rthl3rcg2b.execute-api.us-east-1.amazonaws.com/dev/conversations/{target_session_id}",
                headers=self.headers,
                timeout=10
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve conversation history: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def list_conversations(self, limit: int = 50, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        List user's conversations

        Args:
            limit: Maximum number of conversations to return (default 50)
            include_archived: Include archived conversations (default False)

        Returns:
            [
                {
                    'session_id': 'conv_abc123',
                    'title': 'Cadence Stock Analysis',
                    'created_at': '2025-09-30T10:00:00Z',
                    'last_updated': '2025-09-30T10:15:00Z',
                    'turn_count': 5,
                    'message_count': 10,
                    'preview': 'What was Cadence\'s 2010 stock value?...',
                    'is_active': True
                },
                ...
            ]

        Example:
            conversations = client.list_conversations(limit=10)
            for conv in conversations:
                print(f"{conv['title']} ({conv['turn_count']} turns)")
        """
        try:
            # Use new conversation history API
            response = requests.get(
                f"https://rthl3rcg2b.execute-api.us-east-1.amazonaws.com/dev/conversations",
                headers=self.headers,
                params={'limit': limit, 'include_archived': str(include_archived).lower()},
                timeout=10
            )

            response.raise_for_status()
            result = response.json()
            return result.get('conversations', [])

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list conversations: {str(e)}")
            return []

    def resume_conversation(self, session_id: str):
        """
        Resume a previous conversation session

        Args:
            session_id: Session ID to resume

        Returns:
            self (for method chaining)

        Example:
            # Start and save session ID
            r1 = client.start_conversation().query("Question 1")
            session_id = r1['session_id']

            # Later, resume the conversation
            client.resume_conversation(session_id)
            r2 = client.query("Follow-up question")  # Has context from session
        """
        self.current_session_id = session_id
        logger.info(f"Resumed conversation session: {session_id}")
        return self

    def get_learned_facts(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get facts that were learned during a conversation

        Args:
            session_id: Session ID (defaults to current session)

        Returns:
            [
                {
                    'fact_id': 'learned_fact_abc123',
                    'subject': 'Cadence Design Systems',
                    'predicate': 'percentage_increase_2010_2011',
                    'object': '37.9%',
                    'confidence': 0.85,
                    'learned_from_query': 'What was the percentage increase?',
                    'turn_number': 3,
                    'created_at': '2025-09-30T10:05:00Z'
                },
                ...
            ]

        Example:
            # After a conversation where facts were learned
            learned = client.get_learned_facts()
            print(f"Learned {len(learned)} new facts during conversation")
        """
        target_session_id = session_id or self.current_session_id

        if not target_session_id:
            return []

        try:
            response = requests.get(
                f"{self.rag_base_url}/conversation/{target_session_id}/learned-facts",
                headers=self.headers,
                timeout=10
            )

            response.raise_for_status()
            result = response.json()
            return result.get('learned_facts', [])

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve learned facts: {str(e)}")
            return []

    def delete_conversation(self, session_id: str) -> bool:
        """
        Archive/delete a conversation

        Args:
            session_id: Session ID to archive

        Returns:
            True if successful, False otherwise

        Example:
            client.delete_conversation('conv_abc123')
        """
        try:
            response = requests.delete(
                f"https://rthl3rcg2b.execute-api.us-east-1.amazonaws.com/dev/conversations/{session_id}",
                headers=self.headers,
                timeout=10
            )

            response.raise_for_status()
            logger.info(f"Archived conversation: {session_id}")

            # Clear current session if it was deleted
            if self.current_session_id == session_id:
                self.current_session_id = None

            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to archive conversation: {str(e)}")
            return False

    def update_conversation_title(self, session_id: str, title: str) -> bool:
        """
        Update conversation title

        Args:
            session_id: Session ID to update
            title: New title for the conversation

        Returns:
            True if successful, False otherwise

        Example:
            client.update_conversation_title('conv_abc123', 'My Analysis Session')
        """
        try:
            response = requests.put(
                f"https://rthl3rcg2b.execute-api.us-east-1.amazonaws.com/dev/conversations/{session_id}/title",
                headers=self.headers,
                json={'title': title},
                timeout=10
            )

            response.raise_for_status()
            logger.info(f"Updated title for conversation {session_id}: {title}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update conversation title: {str(e)}")
            return False

    @property
    def in_conversation(self) -> bool:
        """Check if currently in an active conversation"""
        return self.current_session_id is not None


# Extend VRINClient with conversation capabilities
def add_conversation_support(client_class):
    """
    Decorator to add conversation support to VRINClient

    Usage:
        @add_conversation_support
        class VRINClient:
            ...
    """
    # Add ConversationMixin methods to the client class
    for attr_name in dir(ConversationMixin):
        if not attr_name.startswith('_') and callable(getattr(ConversationMixin, attr_name)):
            attr = getattr(ConversationMixin, attr_name)
            setattr(client_class, attr_name, attr)

    # Add conversation state attributes to __init__
    original_init = client_class.__init__

    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        # Initialize conversation state
        self.current_session_id = None
        self.session_history = []
        self._pending_specialization_id = None

    client_class.__init__ = new_init

    return client_class


# Standalone conversation-aware client
class VRINConversationalClient:
    """
    Standalone conversational client (alternative to mixin approach)

    Use this if you want explicit conversation management without modifying VRINClient

    Example:
        from vrin.conversation import VRINConversationalClient

        client = VRINConversationalClient(api_key="vrin_your_key")
        client.start_conversation()
        r1 = client.query("What is machine learning?")
        r2 = client.query("How does it work?")  # Has context from r1
    """

    def __init__(self, api_key: str, **kwargs):
        """Initialize conversational client"""
        # Import here to avoid circular dependency
        from .client_v2 import VRINClient

        # Create underlying client
        self._client = VRINClient(api_key=api_key, **kwargs)

        # Add conversation state
        self.current_session_id = None
        self.session_history = []
        self._pending_specialization_id = None

        # Copy important attributes
        self.rag_base_url = self._client.rag_base_url
        self.auth_base_url = self._client.auth_base_url
        self.headers = self._client.headers
        self.api_key = api_key

    # Delegate non-conversation methods to underlying client
    def __getattr__(self, name):
        """Delegate to underlying client"""
        return getattr(self._client, name)


# Make conversation methods available to ConversationMixin instances
for method_name in ['start_conversation', 'query', 'end_conversation',
                    'get_conversation_history', 'list_conversations',
                    'resume_conversation', 'get_learned_facts', 'delete_conversation',
                    'update_conversation_title', 'in_conversation']:
    if hasattr(ConversationMixin, method_name):
        setattr(VRINConversationalClient, method_name, getattr(ConversationMixin, method_name))
