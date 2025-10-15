from enum import Enum


class ProviderEnum(str, Enum):
    openai = "openai"
    deepseek = "deepseek"
    hyperbolic = "Hyperbolic"
    togetherai = "togetherai"
    local = "local"


class StatusEnum(str, Enum):
    deleted = "deleted"
    active = "active"
    queued = "queued"
    in_progress = "in_progress"
    pending_action = "action_required"
    completed = "completed"
    failed = "failed"
    cancelling = "cancelling"
    cancelled = "cancelled"
    pending = "pending"
    processing = "processing"
    expired = "expired"
    retrying = "retrying"


PLATFORM_TOOLS = [
    "code_interpreter",
    "web_search",
    "vector_store_search",
    "computer",
    "file_search",
]
