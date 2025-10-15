"""
LLM service with conversation session management.

This module provides LLMRingSession, a stateful extension of LLMRing that manages
conversation sessions on llmring-server. Use this when you need:
- Multi-turn conversations with persistent history
- Conversation metadata (title, system prompt, settings)
- Server-side conversation storage and retrieval

For stateless, single-shot LLM calls, use the base LLMRing class instead.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from llmring.schemas import LLMRequest, LLMResponse
from llmring.server_client import ServerClient
from llmring.service import LLMRing

logger = logging.getLogger(__name__)


class LLMRingSession(LLMRing):
    """
    LLM service with conversation session management.

    Extends LLMRing with stateful conversation tracking on llmring-server.
    Each session can create, manage, and retrieve conversation history.

    Requires llmring-server for conversation persistence.
    """

    def __init__(
        self,
        origin: str = "llmring",
        registry_url: Optional[str] = None,
        lockfile_path: Optional[str] = None,
        server_url: Optional[str] = None,
        api_key: Optional[str] = None,
        enable_conversations: bool = True,
        message_logging_level: str = "full",
    ):
        """
        Initialize the session-based LLM service.

        Args:
            origin: Origin identifier for tracking
            registry_url: Optional custom registry URL
            lockfile_path: Optional path to lockfile
            server_url: llmring-server URL for conversation storage (required for sessions)
            api_key: API key for llmring-server or llmring-api
            enable_conversations: Whether to enable conversation tracking (default: True)
            message_logging_level: Level of message logging (none, metadata, full)
        """
        # Pass server_url and api_key to parent for usage logging
        super().__init__(origin, registry_url, lockfile_path, server_url, api_key)

        # Session-specific features
        self.enable_conversations = enable_conversations
        self.message_logging_level = message_logging_level

        # Note: server_client is now inherited from parent (LLMRing)
        # No need to initialize separately

    async def create_conversation(
        self,
        title: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model_alias: str = "default",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Optional[UUID]:
        """
        Create a new conversation.

        Args:
            title: Optional conversation title
            system_prompt: Optional system prompt
            model_alias: Model alias to use
            temperature: Temperature setting
            max_tokens: Max tokens per response

        Returns:
            Conversation ID if server is configured, None otherwise
        """
        if not self.server_client or not self.enable_conversations:
            return None

        try:
            response = await self.server_client.post(
                "/api/v1/conversations",
                json={
                    "title": title,
                    "system_prompt": system_prompt,
                    "model_alias": model_alias,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            return UUID(response["id"])
        except Exception as e:
            logger.warning(f"Failed to create conversation: {e}")
            return None

    async def chat_with_conversation(
        self,
        request: LLMRequest,
        conversation_id: Optional[UUID] = None,
        store_messages: bool = True,
        profile: Optional[str] = None,
    ) -> LLMResponse:
        """
        Send a chat request with optional conversation tracking.

        Args:
            request: LLM request with messages and parameters
            conversation_id: Optional conversation ID to track messages
            store_messages: Whether to store messages in the conversation
            profile: Optional profile name for alias resolution

        Returns:
            LLM response with cost information if available
        """
        # Set conversation_id BEFORE calling parent to avoid duplicate logging
        # The parent's logging service will include this ID in its logs
        if conversation_id and self.logging_service:
            self.logging_service.set_conversation_id(str(conversation_id))

        try:
            # Call parent chat method (this will log usage with conversation_id)
            response = await super().chat(request, profile)
        finally:
            # Clear conversation_id after the call to avoid leaking to subsequent requests
            # Defensive: wrap in try/except to ensure cleanup never fails
            if conversation_id and self.logging_service:
                try:
                    self.logging_service.clear_conversation_id()
                except Exception as e:
                    logger.warning(f"Failed to clear conversation_id: {e}")
                    # Continue execution - cleanup failure shouldn't break the request

        # Store messages if configured
        if (
            self.server_client
            and self.enable_conversations
            and conversation_id
            and store_messages
            and response.usage
        ):
            try:
                # Prepare messages for storage
                messages_to_store = []

                # Add user message(s)
                for msg in request.messages:
                    messages_to_store.append(
                        {
                            "role": msg.role,
                            "content": msg.content,
                            "metadata": {
                                "model_requested": request.model,
                                "temperature": request.temperature,
                            },
                        }
                    )

                # Add assistant response
                # LLMResponse has content and tool_calls, not choices
                messages_to_store.append(
                    {
                        "role": "assistant",
                        "content": response.content,
                        "input_tokens": response.usage.get("prompt_tokens"),
                        "output_tokens": response.usage.get("completion_tokens"),
                        "metadata": {
                            "model_used": response.model,
                            "finish_reason": response.finish_reason,
                            "tool_calls": (
                                response.tool_calls if hasattr(response, "tool_calls") else None
                            ),
                        },
                    }
                )

                # Send to server
                await self.server_client.post(
                    f"/api/v1/conversations/{conversation_id}/messages/batch",
                    json={
                        "conversation_id": str(conversation_id),
                        "messages": messages_to_store,
                        "logging_level": self.message_logging_level,
                    },
                )
                logger.debug(
                    f"Stored {len(messages_to_store)} messages in conversation {conversation_id}"
                )

            except Exception as e:
                logger.warning(f"Failed to store messages: {e}")

        return response

    async def get_conversation_history(
        self,
        conversation_id: UUID,
        limit: int = 100,
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation history with messages.

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to retrieve

        Returns:
            Conversation data with messages if available
        """
        if not self.server_client:
            return None

        try:
            response = await self.server_client.get(
                f"/conversations/{conversation_id}", params={"message_limit": limit}
            )
            return response
        except Exception as e:
            logger.warning(f"Failed to get conversation history: {e}")
            return None

    async def list_conversations(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List conversations for the authenticated user.

        Args:
            limit: Maximum number of conversations to retrieve
            offset: Offset for pagination

        Returns:
            List of conversations
        """
        if not self.server_client:
            return []

        try:
            response = await self.server_client.get(
                "/conversations", params={"limit": limit, "offset": offset}
            )
            return response
        except Exception as e:
            logger.warning(f"Failed to list conversations: {e}")
            return []


# Backward compatibility alias (deprecated)
class LLMRingExtended(LLMRingSession):
    """
    Deprecated: Use LLMRingSession instead.

    This class is maintained for backward compatibility and will be removed
    in a future version. Please migrate to LLMRingSession.
    """

    def __init__(self, *args, **kwargs):
        import warnings

        warnings.warn(
            "LLMRingExtended is deprecated and will be removed in v2.0. "
            "Use LLMRingSession instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


class ConversationManager:
    """Helper class for managing conversations with LLMRingSession."""

    def __init__(self, llm_service: LLMRingSession):
        """
        Initialize conversation manager.

        Args:
            llm_service: Extended LLM service instance
        """
        self.llm = llm_service
        self.current_conversation_id: Optional[UUID] = None
        self.message_history: List[Dict[str, Any]] = []

    async def start_conversation(
        self,
        title: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model_alias: str = "default",
    ) -> Optional[UUID]:
        """Start a new conversation."""
        self.current_conversation_id = await self.llm.create_conversation(
            title=title,
            system_prompt=system_prompt,
            model_alias=model_alias,
        )

        if self.current_conversation_id:
            self.message_history = []
            if system_prompt:
                self.message_history.append(
                    {
                        "role": "system",
                        "content": system_prompt,
                    }
                )

        return self.current_conversation_id

    async def send_message(
        self,
        content: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Send a message in the current conversation.

        Args:
            content: Message content
            model: Optional model override
            temperature: Optional temperature override
            max_tokens: Optional max tokens override

        Returns:
            LLM response
        """
        # Add user message to history
        self.message_history.append(
            {
                "role": "user",
                "content": content,
            }
        )

        # Create request
        request = LLMRequest(
            messages=self.message_history,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Send with conversation tracking
        response = await self.llm.chat_with_conversation(
            request=request,
            conversation_id=self.current_conversation_id,
            store_messages=True,
        )

        # Add assistant response to history
        # LLMResponse has content, not choices
        self.message_history.append(
            {
                "role": "assistant",
                "content": response.content,
            }
        )

        return response

    async def load_conversation(self, conversation_id: UUID) -> bool:
        """
        Load an existing conversation.

        Args:
            conversation_id: Conversation ID to load

        Returns:
            True if loaded successfully
        """
        conversation = await self.llm.get_conversation_history(conversation_id)
        if conversation:
            self.current_conversation_id = UUID(conversation["id"])
            self.message_history = [
                {
                    "role": msg["role"],
                    "content": msg["content"],
                }
                for msg in conversation.get("messages", [])
            ]
            return True
        return False

    def clear_history(self):
        """Clear the current message history (keeps conversation ID)."""
        self.message_history = []

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the current message history."""
        return self.message_history.copy()
