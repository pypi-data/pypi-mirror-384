# src/projectdavid_common/validation.py
from projectdavid_common.schemas.actions_schema import (
    ActionBase,
    ActionCreate,
    ActionList,
    ActionRead,
    ActionStatus,
    ActionUpdate,
)
from projectdavid_common.schemas.api_key_schemas import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyDetails,
    ApiKeyListResponse,
)
from projectdavid_common.schemas.assistants_schema import (
    AssistantCreate,
    AssistantRead,
    AssistantUpdate,
)
from projectdavid_common.schemas.enums import ProviderEnum, StatusEnum
from projectdavid_common.schemas.files_schema import (
    FileDeleteResponse,
    FileResponse,
    FileUploadRequest,
)
from projectdavid_common.schemas.inference_schema import ProcessOutput
from projectdavid_common.schemas.messages_schema import (
    MessageCreate,
    MessageDeleted,
    MessageRead,
    MessageRole,
    MessagesList,
    MessageUpdate,
    ToolMessageCreate,
)
from projectdavid_common.schemas.runs_schema import (
    Run,
    RunCreate,
    RunListResponse,
    RunReadDetailed,
    RunStatus,
    RunStatusUpdate,
    TruncationStrategy,
)
from projectdavid_common.schemas.stream_schema import StreamRequest
from projectdavid_common.schemas.threads_schema import (
    ThreadCreate,
    ThreadDeleted,
    ThreadIds,
    ThreadParticipant,
    ThreadRead,
    ThreadReadDetailed,
    ThreadUpdate,
)
from projectdavid_common.schemas.tools_schema import (
    Tool,
    ToolCreate,
    ToolFunction,
    ToolList,
    ToolRead,
    ToolUpdate,
)
from projectdavid_common.schemas.users_schema import (
    UserBase,
    UserCreate,
    UserDeleteResponse,
    UserRead,
    UserUpdate,
)
from projectdavid_common.schemas.vector_search_envelope import (
    AssistantMessage,
    FileCitation,
    FileSearchCall,
    FileSearchEnvelope,
    OutputText,
)
from projectdavid_common.schemas.vectors_schema import (
    EnhancedVectorSearchResult,
    SearchExplanation,
    VectorStoreAddRequest,
    VectorStoreCreate,
    VectorStoreCreateWithSharedId,
    VectorStoreFileCreate,
    VectorStoreFileList,
    VectorStoreFileRead,
    VectorStoreFileUpdate,
    VectorStoreFileUpdateStatus,
    VectorStoreLinkAssistant,
    VectorStoreList,
    VectorStoreRead,
    VectorStoreSearchResult,
    VectorStoreUnlinkAssistant,
    VectorStoreUpdate,
)


class ValidationInterface:
    """
    Exposes Pydantic validation classes, retaining their original naming.

    This interface allows consumers to access the various schemas like:
        - ValidationInterface.FileUploadRequest
        - ValidationInterface.ActionCreate
        - etc.
    """

    # Actions schemas
    ActionBase = ActionBase
    ActionStatus = ActionStatus
    ActionCreate = ActionCreate
    ActionRead = ActionRead
    ActionList = ActionList
    ActionUpdate = ActionUpdate

    # Assistants schemas
    AssistantCreate = AssistantCreate
    AssistantRead = AssistantRead
    AssistantUpdate = AssistantUpdate
    VectorStoreRead = VectorStoreRead

    # Enum schemas
    ProviderEnum = ProviderEnum
    StatusEnum = StatusEnum

    # Files schemas
    FileUploadRequest = FileUploadRequest
    FileResponse = FileResponse
    FileDeleteResponse = FileDeleteResponse

    # Inference schemas
    ProcessOutput = ProcessOutput

    # Messages schemas
    MessageRole = MessageRole
    MessageCreate = MessageCreate
    MessageRead = MessageRead
    MessageUpdate = MessageUpdate
    ToolMessageCreate = ToolMessageCreate
    MessagesList = MessagesList
    MessageDeleted = MessageDeleted

    # Runs schemas
    Run = Run
    RunCreate = RunCreate
    RunReadDetailed = RunReadDetailed
    RunStatus = RunStatus
    TruncationStrategy = TruncationStrategy
    RunStatusUpdate = RunStatusUpdate
    RunListResponse = RunListResponse

    # Threads schemas
    ThreadCreate = ThreadCreate
    ThreadRead = ThreadRead
    ThreadUpdate = ThreadUpdate
    ThreadParticipant = ThreadParticipant
    ThreadReadDetailed = ThreadReadDetailed
    ThreadIds = ThreadIds
    ThreadDeleted = ThreadDeleted

    # Tools schemas
    ToolFunction = ToolFunction
    Tool = Tool
    ToolCreate = ToolCreate
    ToolRead = ToolRead
    ToolUpdate = ToolUpdate
    ToolList = ToolList

    # Users schemas
    UserBase = UserBase
    UserCreate = UserCreate
    UserRead = UserRead
    UserUpdate = UserUpdate
    UserDeleteResponse = UserDeleteResponse

    # Vector Store schemas

    # Core Vector Store CRUD
    VectorStoreCreate = VectorStoreCreate
    VectorStoreCreateWithSharedId = VectorStoreCreateWithSharedId
    VectorStoreRead = VectorStoreRead
    VectorStoreUpdate = VectorStoreUpdate
    VectorStoreList = VectorStoreList

    # File-level operations
    VectorStoreFileCreate = VectorStoreFileCreate
    VectorStoreFileRead = VectorStoreFileRead
    VectorStoreFileUpdate = VectorStoreFileUpdate
    VectorStoreFileUpdateStatus = VectorStoreFileUpdateStatus
    VectorStoreFileList = VectorStoreFileList

    # Search & Results
    VectorStoreSearchResult = VectorStoreSearchResult
    EnhancedVectorSearchResult = EnhancedVectorSearchResult
    SearchExplanation = SearchExplanation

    # Assistant linking
    VectorStoreLinkAssistant = VectorStoreLinkAssistant
    VectorStoreUnlinkAssistant = VectorStoreUnlinkAssistant

    # Optional: Request wrapper
    VectorStoreAddRequest = VectorStoreAddRequest

    # Key
    ApiKeyCreateRequest = ApiKeyCreateRequest
    ApiKeyCreateResponse = ApiKeyCreateResponse
    ApiKeyDetails = ApiKeyDetails
    ApiKeyListResponse = ApiKeyListResponse

    # Stream
    StreamRequest = StreamRequest

    # Vector Search
    FileCitation = FileCitation
    OutputText = OutputText
    AssistantMessage = AssistantMessage
    FileSearchCall = FileSearchCall
    FileSearchEnvelope = FileSearchEnvelope
