"""The llmring package."""

__version__ = "1.1.0"

from .base import BaseLLMProvider

# Import exceptions
from .exceptions import (
    ConfigurationError,
    ConversationNotFoundError,
    LLMRingError,
    ModelNotFoundError,
    ProviderError,
    ProviderNotFoundError,
    ServerConnectionError,
)

# Import file utilities
from .file_utils import (  # Core functions; Content creation; Convenience functions
    analyze_image,
    compare_images,
    create_base64_image_content,
    create_data_url,
    create_image_content,
    create_multi_image_content,
    encode_file_to_base64,
    extract_text_from_image,
    get_file_mime_type,
    validate_image_file,
)
from .schemas import LLMRequest, LLMResponse, Message

# Import logging decorators
from .logging import log_llm_call, log_llm_stream

# Import main components
from .service import LLMRing
from .service_extended import ConversationManager, LLMRingSession, LLMRingExtended

__all__ = [
    # Core classes
    "LLMRing",
    "LLMRingSession",
    "LLMRingExtended",  # Deprecated, kept for backward compatibility
    "ConversationManager",
    "BaseLLMProvider",
    # Logging decorators
    "log_llm_call",
    "log_llm_stream",
    # Exceptions
    "LLMRingError",
    "ConfigurationError",
    "ProviderError",
    "ProviderNotFoundError",
    "ModelNotFoundError",
    "ConversationNotFoundError",
    "ServerConnectionError",
    # Schemas
    "LLMRequest",
    "LLMResponse",
    "Message",
    # File utilities
    "encode_file_to_base64",
    "create_data_url",
    "get_file_mime_type",
    "validate_image_file",
    "create_image_content",
    "create_multi_image_content",
    "create_base64_image_content",
    "analyze_image",
    "extract_text_from_image",
    "compare_images",
]
