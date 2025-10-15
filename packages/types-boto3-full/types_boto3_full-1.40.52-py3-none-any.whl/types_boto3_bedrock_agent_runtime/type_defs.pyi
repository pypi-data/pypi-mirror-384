"""
Type annotations for bedrock-agent-runtime service type definitions.

[Documentation](https://youtype.github.io/types_boto3_docs/types_boto3_bedrock_agent_runtime/type_defs/)

Copyright 2025 Vlad Emelianov

Usage::

    ```python
    from types_boto3_bedrock_agent_runtime.type_defs import S3IdentifierTypeDef

    data: S3IdentifierTypeDef = ...
    ```
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import IO, Any, Union

from botocore.eventstream import EventStream
from botocore.response import StreamingBody

from .literals import (
    ActionGroupSignatureType,
    ActionInvocationTypeType,
    AgentCollaborationType,
    AttributeTypeType,
    ConfirmationStateType,
    ConversationRoleType,
    CreationModeType,
    ExecutionTypeType,
    ExternalSourceTypeType,
    FileSourceTypeType,
    FileUseCaseType,
    FlowCompletionReasonType,
    FlowControlNodeTypeType,
    FlowErrorCodeType,
    FlowExecutionEventTypeType,
    FlowExecutionStatusType,
    FlowNodeInputCategoryType,
    FlowNodeIODataTypeType,
    GuadrailActionType,
    GuardrailActionType,
    GuardrailContentFilterConfidenceType,
    GuardrailContentFilterTypeType,
    GuardrailPiiEntityTypeType,
    GuardrailSensitiveInformationPolicyActionType,
    ImageFormatType,
    ImageInputFormatType,
    InvocationTypeType,
    NodeErrorCodeType,
    NodeTypeType,
    OrchestrationTypeType,
    ParameterTypeType,
    PayloadTypeType,
    PerformanceConfigLatencyType,
    PromptStateType,
    PromptTypeType,
    RelayConversationHistoryType,
    RequireConfirmationType,
    RerankDocumentTypeType,
    RerankingMetadataSelectionModeType,
    ResponseStateType,
    RetrievalResultContentColumnTypeType,
    RetrievalResultContentTypeType,
    RetrievalResultLocationTypeType,
    RetrieveAndGenerateTypeType,
    SearchTypeType,
    SessionStatusType,
    SourceType,
    TypeType,
)

if sys.version_info >= (3, 9):
    from builtins import dict as Dict
    from builtins import list as List
    from collections.abc import Mapping, Sequence
else:
    from typing import Dict, List, Mapping, Sequence
if sys.version_info >= (3, 12):
    from typing import Literal, NotRequired, TypedDict
else:
    from typing_extensions import Literal, NotRequired, TypedDict

__all__ = (
    "APISchemaTypeDef",
    "AccessDeniedExceptionTypeDef",
    "ActionGroupExecutorTypeDef",
    "ActionGroupInvocationInputTypeDef",
    "ActionGroupInvocationOutputTypeDef",
    "AgentActionGroupTypeDef",
    "AgentCollaboratorInputPayloadTypeDef",
    "AgentCollaboratorInvocationInputTypeDef",
    "AgentCollaboratorInvocationOutputTypeDef",
    "AgentCollaboratorOutputPayloadTypeDef",
    "AnalyzePromptEventTypeDef",
    "ApiInvocationInputTypeDef",
    "ApiParameterTypeDef",
    "ApiRequestBodyTypeDef",
    "ApiResultOutputTypeDef",
    "ApiResultTypeDef",
    "ApiResultUnionTypeDef",
    "AttributionTypeDef",
    "BadGatewayExceptionTypeDef",
    "BedrockModelConfigurationsTypeDef",
    "BedrockRerankingConfigurationTypeDef",
    "BedrockRerankingModelConfigurationTypeDef",
    "BedrockSessionContentBlockOutputTypeDef",
    "BedrockSessionContentBlockTypeDef",
    "BlobTypeDef",
    "ByteContentDocTypeDef",
    "ByteContentFileTypeDef",
    "CallerTypeDef",
    "CitationEventTypeDef",
    "CitationTypeDef",
    "CodeInterpreterInvocationInputTypeDef",
    "CodeInterpreterInvocationOutputTypeDef",
    "CollaboratorConfigurationTypeDef",
    "CollaboratorTypeDef",
    "ConditionResultEventTypeDef",
    "ConflictExceptionTypeDef",
    "ContentBlockTypeDef",
    "ContentBodyOutputTypeDef",
    "ContentBodyTypeDef",
    "ContentBodyUnionTypeDef",
    "ConversationHistoryTypeDef",
    "CreateInvocationRequestTypeDef",
    "CreateInvocationResponseTypeDef",
    "CreateSessionRequestTypeDef",
    "CreateSessionResponseTypeDef",
    "CustomOrchestrationTraceEventTypeDef",
    "CustomOrchestrationTraceTypeDef",
    "CustomOrchestrationTypeDef",
    "DeleteAgentMemoryRequestTypeDef",
    "DeleteSessionRequestTypeDef",
    "DependencyFailedExceptionTypeDef",
    "EndSessionRequestTypeDef",
    "EndSessionResponseTypeDef",
    "ExternalSourceTypeDef",
    "ExternalSourcesGenerationConfigurationTypeDef",
    "ExternalSourcesRetrieveAndGenerateConfigurationTypeDef",
    "FailureTraceTypeDef",
    "FieldForRerankingTypeDef",
    "FilePartTypeDef",
    "FileSourceTypeDef",
    "FilterAttributeTypeDef",
    "FinalResponseTypeDef",
    "FlowCompletionEventTypeDef",
    "FlowExecutionContentTypeDef",
    "FlowExecutionErrorTypeDef",
    "FlowExecutionEventTypeDef",
    "FlowExecutionInputEventTypeDef",
    "FlowExecutionOutputEventTypeDef",
    "FlowExecutionSummaryTypeDef",
    "FlowFailureEventTypeDef",
    "FlowInputContentTypeDef",
    "FlowInputFieldTypeDef",
    "FlowInputTypeDef",
    "FlowMultiTurnInputContentTypeDef",
    "FlowMultiTurnInputRequestEventTypeDef",
    "FlowOutputContentTypeDef",
    "FlowOutputEventTypeDef",
    "FlowOutputFieldTypeDef",
    "FlowResponseStreamTypeDef",
    "FlowTraceConditionNodeResultEventTypeDef",
    "FlowTraceConditionTypeDef",
    "FlowTraceDependencyEventTypeDef",
    "FlowTraceEventTypeDef",
    "FlowTraceNodeActionEventTypeDef",
    "FlowTraceNodeInputContentTypeDef",
    "FlowTraceNodeInputEventTypeDef",
    "FlowTraceNodeInputExecutionChainItemTypeDef",
    "FlowTraceNodeInputFieldTypeDef",
    "FlowTraceNodeInputSourceTypeDef",
    "FlowTraceNodeOutputContentTypeDef",
    "FlowTraceNodeOutputEventTypeDef",
    "FlowTraceNodeOutputFieldTypeDef",
    "FlowTraceNodeOutputNextTypeDef",
    "FlowTraceTypeDef",
    "FunctionDefinitionTypeDef",
    "FunctionInvocationInputTypeDef",
    "FunctionParameterTypeDef",
    "FunctionResultOutputTypeDef",
    "FunctionResultTypeDef",
    "FunctionResultUnionTypeDef",
    "FunctionSchemaTypeDef",
    "GenerateQueryRequestTypeDef",
    "GenerateQueryResponseTypeDef",
    "GeneratedQueryTypeDef",
    "GeneratedResponsePartTypeDef",
    "GenerationConfigurationTypeDef",
    "GetAgentMemoryRequestPaginateTypeDef",
    "GetAgentMemoryRequestTypeDef",
    "GetAgentMemoryResponseTypeDef",
    "GetExecutionFlowSnapshotRequestTypeDef",
    "GetExecutionFlowSnapshotResponseTypeDef",
    "GetFlowExecutionRequestTypeDef",
    "GetFlowExecutionResponseTypeDef",
    "GetInvocationStepRequestTypeDef",
    "GetInvocationStepResponseTypeDef",
    "GetSessionRequestTypeDef",
    "GetSessionResponseTypeDef",
    "GuardrailAssessmentTypeDef",
    "GuardrailConfigurationTypeDef",
    "GuardrailConfigurationWithArnTypeDef",
    "GuardrailContentFilterTypeDef",
    "GuardrailContentPolicyAssessmentTypeDef",
    "GuardrailCustomWordTypeDef",
    "GuardrailEventTypeDef",
    "GuardrailManagedWordTypeDef",
    "GuardrailPiiEntityFilterTypeDef",
    "GuardrailRegexFilterTypeDef",
    "GuardrailSensitiveInformationPolicyAssessmentTypeDef",
    "GuardrailTopicPolicyAssessmentTypeDef",
    "GuardrailTopicTypeDef",
    "GuardrailTraceTypeDef",
    "GuardrailWordPolicyAssessmentTypeDef",
    "ImageBlockOutputTypeDef",
    "ImageBlockTypeDef",
    "ImageInputOutputTypeDef",
    "ImageInputSourceOutputTypeDef",
    "ImageInputSourceTypeDef",
    "ImageInputSourceUnionTypeDef",
    "ImageInputTypeDef",
    "ImageInputUnionTypeDef",
    "ImageSourceOutputTypeDef",
    "ImageSourceTypeDef",
    "ImplicitFilterConfigurationTypeDef",
    "InferenceConfigTypeDef",
    "InferenceConfigurationOutputTypeDef",
    "InferenceConfigurationTypeDef",
    "InferenceConfigurationUnionTypeDef",
    "InlineAgentFilePartTypeDef",
    "InlineAgentPayloadPartTypeDef",
    "InlineAgentResponseStreamTypeDef",
    "InlineAgentReturnControlPayloadTypeDef",
    "InlineAgentTracePartTypeDef",
    "InlineBedrockModelConfigurationsTypeDef",
    "InlineSessionStateTypeDef",
    "InputFileTypeDef",
    "InputPromptTypeDef",
    "InternalServerExceptionTypeDef",
    "InvocationInputMemberTypeDef",
    "InvocationInputTypeDef",
    "InvocationResultMemberOutputTypeDef",
    "InvocationResultMemberTypeDef",
    "InvocationResultMemberUnionTypeDef",
    "InvocationStepPayloadOutputTypeDef",
    "InvocationStepPayloadTypeDef",
    "InvocationStepPayloadUnionTypeDef",
    "InvocationStepSummaryTypeDef",
    "InvocationStepTypeDef",
    "InvocationSummaryTypeDef",
    "InvokeAgentRequestTypeDef",
    "InvokeAgentResponseTypeDef",
    "InvokeFlowRequestTypeDef",
    "InvokeFlowResponseTypeDef",
    "InvokeInlineAgentRequestTypeDef",
    "InvokeInlineAgentResponseTypeDef",
    "KnowledgeBaseConfigurationTypeDef",
    "KnowledgeBaseLookupInputTypeDef",
    "KnowledgeBaseLookupOutputTypeDef",
    "KnowledgeBaseQueryTypeDef",
    "KnowledgeBaseRetrievalConfigurationPaginatorTypeDef",
    "KnowledgeBaseRetrievalConfigurationTypeDef",
    "KnowledgeBaseRetrievalResultTypeDef",
    "KnowledgeBaseRetrieveAndGenerateConfigurationTypeDef",
    "KnowledgeBaseTypeDef",
    "KnowledgeBaseVectorSearchConfigurationPaginatorTypeDef",
    "KnowledgeBaseVectorSearchConfigurationTypeDef",
    "ListFlowExecutionEventsRequestPaginateTypeDef",
    "ListFlowExecutionEventsRequestTypeDef",
    "ListFlowExecutionEventsResponseTypeDef",
    "ListFlowExecutionsRequestPaginateTypeDef",
    "ListFlowExecutionsRequestTypeDef",
    "ListFlowExecutionsResponseTypeDef",
    "ListInvocationStepsRequestPaginateTypeDef",
    "ListInvocationStepsRequestTypeDef",
    "ListInvocationStepsResponseTypeDef",
    "ListInvocationsRequestPaginateTypeDef",
    "ListInvocationsRequestTypeDef",
    "ListInvocationsResponseTypeDef",
    "ListSessionsRequestPaginateTypeDef",
    "ListSessionsRequestTypeDef",
    "ListSessionsResponseTypeDef",
    "ListTagsForResourceRequestTypeDef",
    "ListTagsForResourceResponseTypeDef",
    "MemorySessionSummaryTypeDef",
    "MemoryTypeDef",
    "MessageTypeDef",
    "MetadataAttributeSchemaTypeDef",
    "MetadataConfigurationForRerankingTypeDef",
    "MetadataTypeDef",
    "ModelInvocationInputTypeDef",
    "ModelNotReadyExceptionTypeDef",
    "ModelPerformanceConfigurationTypeDef",
    "NodeActionEventTypeDef",
    "NodeDependencyEventTypeDef",
    "NodeExecutionContentTypeDef",
    "NodeFailureEventTypeDef",
    "NodeInputEventTypeDef",
    "NodeInputExecutionChainItemTypeDef",
    "NodeInputFieldTypeDef",
    "NodeInputSourceTypeDef",
    "NodeOutputEventTypeDef",
    "NodeOutputFieldTypeDef",
    "NodeOutputNextTypeDef",
    "NodeTraceElementsTypeDef",
    "ObservationTypeDef",
    "OptimizePromptRequestTypeDef",
    "OptimizePromptResponseTypeDef",
    "OptimizedPromptEventTypeDef",
    "OptimizedPromptStreamTypeDef",
    "OptimizedPromptTypeDef",
    "OrchestrationConfigurationTypeDef",
    "OrchestrationExecutorTypeDef",
    "OrchestrationModelInvocationOutputTypeDef",
    "OrchestrationTraceTypeDef",
    "OutputFileTypeDef",
    "PaginatorConfigTypeDef",
    "ParameterDetailTypeDef",
    "ParameterTypeDef",
    "PayloadPartTypeDef",
    "PerformanceConfigurationTypeDef",
    "PostProcessingModelInvocationOutputTypeDef",
    "PostProcessingParsedResponseTypeDef",
    "PostProcessingTraceTypeDef",
    "PreProcessingModelInvocationOutputTypeDef",
    "PreProcessingParsedResponseTypeDef",
    "PreProcessingTraceTypeDef",
    "PromptConfigurationTypeDef",
    "PromptCreationConfigurationsTypeDef",
    "PromptOverrideConfigurationTypeDef",
    "PromptTemplateTypeDef",
    "PropertyParametersTypeDef",
    "PutInvocationStepRequestTypeDef",
    "PutInvocationStepResponseTypeDef",
    "QueryGenerationInputTypeDef",
    "QueryTransformationConfigurationTypeDef",
    "RationaleTypeDef",
    "RawResponseTypeDef",
    "ReasoningContentBlockTypeDef",
    "ReasoningTextBlockTypeDef",
    "RepromptResponseTypeDef",
    "RequestBodyTypeDef",
    "RerankDocumentOutputTypeDef",
    "RerankDocumentTypeDef",
    "RerankDocumentUnionTypeDef",
    "RerankQueryTypeDef",
    "RerankRequestPaginateTypeDef",
    "RerankRequestTypeDef",
    "RerankResponseTypeDef",
    "RerankResultTypeDef",
    "RerankSourceTypeDef",
    "RerankTextDocumentTypeDef",
    "RerankingConfigurationTypeDef",
    "RerankingMetadataSelectiveModeConfigurationTypeDef",
    "ResourceNotFoundExceptionTypeDef",
    "ResponseMetadataTypeDef",
    "ResponseStreamTypeDef",
    "RetrievalFilterPaginatorTypeDef",
    "RetrievalFilterTypeDef",
    "RetrievalResultConfluenceLocationTypeDef",
    "RetrievalResultContentColumnTypeDef",
    "RetrievalResultContentTypeDef",
    "RetrievalResultCustomDocumentLocationTypeDef",
    "RetrievalResultKendraDocumentLocationTypeDef",
    "RetrievalResultLocationTypeDef",
    "RetrievalResultS3LocationTypeDef",
    "RetrievalResultSalesforceLocationTypeDef",
    "RetrievalResultSharePointLocationTypeDef",
    "RetrievalResultSqlLocationTypeDef",
    "RetrievalResultWebLocationTypeDef",
    "RetrieveAndGenerateConfigurationTypeDef",
    "RetrieveAndGenerateInputTypeDef",
    "RetrieveAndGenerateOutputEventTypeDef",
    "RetrieveAndGenerateOutputTypeDef",
    "RetrieveAndGenerateRequestTypeDef",
    "RetrieveAndGenerateResponseTypeDef",
    "RetrieveAndGenerateSessionConfigurationTypeDef",
    "RetrieveAndGenerateStreamRequestTypeDef",
    "RetrieveAndGenerateStreamResponseOutputTypeDef",
    "RetrieveAndGenerateStreamResponseTypeDef",
    "RetrieveRequestPaginateTypeDef",
    "RetrieveRequestTypeDef",
    "RetrieveResponseTypeDef",
    "RetrievedReferenceTypeDef",
    "ReturnControlPayloadTypeDef",
    "ReturnControlResultsTypeDef",
    "RoutingClassifierModelInvocationOutputTypeDef",
    "RoutingClassifierTraceTypeDef",
    "S3IdentifierTypeDef",
    "S3LocationTypeDef",
    "S3ObjectDocTypeDef",
    "S3ObjectFileTypeDef",
    "SatisfiedConditionTypeDef",
    "ServiceQuotaExceededExceptionTypeDef",
    "SessionStateTypeDef",
    "SessionSummaryTypeDef",
    "SpanTypeDef",
    "StartFlowExecutionRequestTypeDef",
    "StartFlowExecutionResponseTypeDef",
    "StopFlowExecutionRequestTypeDef",
    "StopFlowExecutionResponseTypeDef",
    "StreamingConfigurationsTypeDef",
    "TagResourceRequestTypeDef",
    "TextInferenceConfigTypeDef",
    "TextPromptTypeDef",
    "TextResponsePartTypeDef",
    "TextToSqlConfigurationTypeDef",
    "TextToSqlKnowledgeBaseConfigurationTypeDef",
    "ThrottlingExceptionTypeDef",
    "TimestampTypeDef",
    "TraceElementsTypeDef",
    "TracePartTypeDef",
    "TraceTypeDef",
    "TransformationConfigurationTypeDef",
    "UntagResourceRequestTypeDef",
    "UpdateSessionRequestTypeDef",
    "UpdateSessionResponseTypeDef",
    "UsageTypeDef",
    "ValidationExceptionTypeDef",
    "VectorSearchBedrockRerankingConfigurationTypeDef",
    "VectorSearchBedrockRerankingModelConfigurationTypeDef",
    "VectorSearchRerankingConfigurationTypeDef",
)

class S3IdentifierTypeDef(TypedDict):
    s3BucketName: NotRequired[str]
    s3ObjectKey: NotRequired[str]

class AccessDeniedExceptionTypeDef(TypedDict):
    message: NotRequired[str]

ActionGroupExecutorTypeDef = TypedDict(
    "ActionGroupExecutorTypeDef",
    {
        "lambda": NotRequired[str],
        "customControl": NotRequired[Literal["RETURN_CONTROL"]],
    },
)
ParameterTypeDef = TypedDict(
    "ParameterTypeDef",
    {
        "name": NotRequired[str],
        "type": NotRequired[str],
        "value": NotRequired[str],
    },
)

class AnalyzePromptEventTypeDef(TypedDict):
    message: NotRequired[str]

ApiParameterTypeDef = TypedDict(
    "ApiParameterTypeDef",
    {
        "name": NotRequired[str],
        "type": NotRequired[str],
        "value": NotRequired[str],
    },
)

class BadGatewayExceptionTypeDef(TypedDict):
    message: NotRequired[str]
    resourceName: NotRequired[str]

class PerformanceConfigurationTypeDef(TypedDict):
    latency: NotRequired[PerformanceConfigLatencyType]

class BedrockRerankingModelConfigurationTypeDef(TypedDict):
    modelArn: str
    additionalModelRequestFields: NotRequired[Mapping[str, Mapping[str, Any]]]

BlobTypeDef = Union[str, bytes, IO[Any], StreamingBody]

class CallerTypeDef(TypedDict):
    agentAliasArn: NotRequired[str]

class CodeInterpreterInvocationInputTypeDef(TypedDict):
    code: NotRequired[str]
    files: NotRequired[List[str]]

class CollaboratorConfigurationTypeDef(TypedDict):
    collaboratorName: str
    collaboratorInstruction: str
    agentAliasArn: NotRequired[str]
    relayConversationHistory: NotRequired[RelayConversationHistoryType]

class GuardrailConfigurationWithArnTypeDef(TypedDict):
    guardrailIdentifier: str
    guardrailVersion: str

class SatisfiedConditionTypeDef(TypedDict):
    conditionName: str

class ConflictExceptionTypeDef(TypedDict):
    message: NotRequired[str]

class ContentBlockTypeDef(TypedDict):
    text: NotRequired[str]

class CreateInvocationRequestTypeDef(TypedDict):
    sessionIdentifier: str
    invocationId: NotRequired[str]
    description: NotRequired[str]

class ResponseMetadataTypeDef(TypedDict):
    RequestId: str
    HTTPStatusCode: int
    HTTPHeaders: Dict[str, str]
    RetryAttempts: int
    HostId: NotRequired[str]

class CreateSessionRequestTypeDef(TypedDict):
    sessionMetadata: NotRequired[Mapping[str, str]]
    encryptionKeyArn: NotRequired[str]
    tags: NotRequired[Mapping[str, str]]

class CustomOrchestrationTraceEventTypeDef(TypedDict):
    text: NotRequired[str]

OrchestrationExecutorTypeDef = TypedDict(
    "OrchestrationExecutorTypeDef",
    {
        "lambda": NotRequired[str],
    },
)

class DeleteAgentMemoryRequestTypeDef(TypedDict):
    agentId: str
    agentAliasId: str
    memoryId: NotRequired[str]
    sessionId: NotRequired[str]

class DeleteSessionRequestTypeDef(TypedDict):
    sessionIdentifier: str

class DependencyFailedExceptionTypeDef(TypedDict):
    message: NotRequired[str]
    resourceName: NotRequired[str]

class EndSessionRequestTypeDef(TypedDict):
    sessionIdentifier: str

class S3ObjectDocTypeDef(TypedDict):
    uri: str

class GuardrailConfigurationTypeDef(TypedDict):
    guardrailId: str
    guardrailVersion: str

class PromptTemplateTypeDef(TypedDict):
    textPromptTemplate: NotRequired[str]

class FieldForRerankingTypeDef(TypedDict):
    fieldName: str

OutputFileTypeDef = TypedDict(
    "OutputFileTypeDef",
    {
        "name": NotRequired[str],
        "type": NotRequired[str],
        "bytes": NotRequired[bytes],
    },
)

class S3ObjectFileTypeDef(TypedDict):
    uri: str

class FilterAttributeTypeDef(TypedDict):
    key: str
    value: Mapping[str, Any]

class FlowCompletionEventTypeDef(TypedDict):
    completionReason: FlowCompletionReasonType

class FlowExecutionContentTypeDef(TypedDict):
    document: NotRequired[Dict[str, Any]]

class FlowExecutionErrorTypeDef(TypedDict):
    nodeName: NotRequired[str]
    error: NotRequired[Literal["ExecutionTimedOut"]]
    message: NotRequired[str]

class FlowFailureEventTypeDef(TypedDict):
    timestamp: datetime
    errorCode: FlowErrorCodeType
    errorMessage: str

class NodeActionEventTypeDef(TypedDict):
    nodeName: str
    timestamp: datetime
    requestId: str
    serviceName: str
    operationName: str
    operationRequest: NotRequired[Dict[str, Any]]
    operationResponse: NotRequired[Dict[str, Any]]

class NodeFailureEventTypeDef(TypedDict):
    nodeName: str
    timestamp: datetime
    errorCode: NodeErrorCodeType
    errorMessage: str

class FlowExecutionSummaryTypeDef(TypedDict):
    executionArn: str
    flowAliasIdentifier: str
    flowIdentifier: str
    flowVersion: str
    status: FlowExecutionStatusType
    createdAt: datetime
    endedAt: NotRequired[datetime]

class FlowInputContentTypeDef(TypedDict):
    document: NotRequired[Mapping[str, Any]]

class FlowMultiTurnInputContentTypeDef(TypedDict):
    document: NotRequired[Dict[str, Any]]

class FlowOutputContentTypeDef(TypedDict):
    document: NotRequired[Dict[str, Any]]

class InternalServerExceptionTypeDef(TypedDict):
    message: NotRequired[str]
    reason: NotRequired[str]

class ResourceNotFoundExceptionTypeDef(TypedDict):
    message: NotRequired[str]

class ServiceQuotaExceededExceptionTypeDef(TypedDict):
    message: NotRequired[str]

class ThrottlingExceptionTypeDef(TypedDict):
    message: NotRequired[str]

class ValidationExceptionTypeDef(TypedDict):
    message: NotRequired[str]

class FlowTraceConditionTypeDef(TypedDict):
    conditionName: str

class FlowTraceNodeActionEventTypeDef(TypedDict):
    nodeName: str
    timestamp: datetime
    requestId: str
    serviceName: str
    operationName: str
    operationRequest: NotRequired[Dict[str, Any]]
    operationResponse: NotRequired[Dict[str, Any]]

class FlowTraceNodeInputContentTypeDef(TypedDict):
    document: NotRequired[Dict[str, Any]]

FlowTraceNodeInputExecutionChainItemTypeDef = TypedDict(
    "FlowTraceNodeInputExecutionChainItemTypeDef",
    {
        "nodeName": str,
        "type": FlowControlNodeTypeType,
        "index": NotRequired[int],
    },
)

class FlowTraceNodeInputSourceTypeDef(TypedDict):
    nodeName: str
    outputFieldName: str
    expression: str

class FlowTraceNodeOutputContentTypeDef(TypedDict):
    document: NotRequired[Dict[str, Any]]

class FlowTraceNodeOutputNextTypeDef(TypedDict):
    nodeName: str
    inputFieldName: str

ParameterDetailTypeDef = TypedDict(
    "ParameterDetailTypeDef",
    {
        "type": ParameterTypeType,
        "description": NotRequired[str],
        "required": NotRequired[bool],
    },
)
FunctionParameterTypeDef = TypedDict(
    "FunctionParameterTypeDef",
    {
        "name": NotRequired[str],
        "type": NotRequired[str],
        "value": NotRequired[str],
    },
)
QueryGenerationInputTypeDef = TypedDict(
    "QueryGenerationInputTypeDef",
    {
        "type": Literal["TEXT"],
        "text": str,
    },
)
GeneratedQueryTypeDef = TypedDict(
    "GeneratedQueryTypeDef",
    {
        "type": NotRequired[Literal["REDSHIFT_SQL"]],
        "sql": NotRequired[str],
    },
)

class PaginatorConfigTypeDef(TypedDict):
    MaxItems: NotRequired[int]
    PageSize: NotRequired[int]
    StartingToken: NotRequired[str]

class GetAgentMemoryRequestTypeDef(TypedDict):
    agentId: str
    agentAliasId: str
    memoryType: Literal["SESSION_SUMMARY"]
    memoryId: str
    nextToken: NotRequired[str]
    maxItems: NotRequired[int]

class GetExecutionFlowSnapshotRequestTypeDef(TypedDict):
    flowIdentifier: str
    flowAliasIdentifier: str
    executionIdentifier: str

class GetFlowExecutionRequestTypeDef(TypedDict):
    flowIdentifier: str
    flowAliasIdentifier: str
    executionIdentifier: str

class GetInvocationStepRequestTypeDef(TypedDict):
    invocationIdentifier: str
    invocationStepId: str
    sessionIdentifier: str

class GetSessionRequestTypeDef(TypedDict):
    sessionIdentifier: str

GuardrailContentFilterTypeDef = TypedDict(
    "GuardrailContentFilterTypeDef",
    {
        "type": NotRequired[GuardrailContentFilterTypeType],
        "confidence": NotRequired[GuardrailContentFilterConfidenceType],
        "action": NotRequired[Literal["BLOCKED"]],
    },
)

class GuardrailCustomWordTypeDef(TypedDict):
    match: NotRequired[str]
    action: NotRequired[Literal["BLOCKED"]]

class GuardrailEventTypeDef(TypedDict):
    action: NotRequired[GuadrailActionType]

GuardrailManagedWordTypeDef = TypedDict(
    "GuardrailManagedWordTypeDef",
    {
        "match": NotRequired[str],
        "type": NotRequired[Literal["PROFANITY"]],
        "action": NotRequired[Literal["BLOCKED"]],
    },
)
GuardrailPiiEntityFilterTypeDef = TypedDict(
    "GuardrailPiiEntityFilterTypeDef",
    {
        "type": NotRequired[GuardrailPiiEntityTypeType],
        "match": NotRequired[str],
        "action": NotRequired[GuardrailSensitiveInformationPolicyActionType],
    },
)

class GuardrailRegexFilterTypeDef(TypedDict):
    name: NotRequired[str]
    regex: NotRequired[str]
    match: NotRequired[str]
    action: NotRequired[GuardrailSensitiveInformationPolicyActionType]

GuardrailTopicTypeDef = TypedDict(
    "GuardrailTopicTypeDef",
    {
        "name": NotRequired[str],
        "type": NotRequired[Literal["DENY"]],
        "action": NotRequired[Literal["BLOCKED"]],
    },
)
ImageInputSourceOutputTypeDef = TypedDict(
    "ImageInputSourceOutputTypeDef",
    {
        "bytes": NotRequired[bytes],
    },
)

class S3LocationTypeDef(TypedDict):
    uri: str

MetadataAttributeSchemaTypeDef = TypedDict(
    "MetadataAttributeSchemaTypeDef",
    {
        "key": str,
        "type": AttributeTypeType,
        "description": str,
    },
)

class TextInferenceConfigTypeDef(TypedDict):
    temperature: NotRequired[float]
    topP: NotRequired[float]
    maxTokens: NotRequired[int]
    stopSequences: NotRequired[Sequence[str]]

class InferenceConfigurationOutputTypeDef(TypedDict):
    temperature: NotRequired[float]
    topP: NotRequired[float]
    topK: NotRequired[int]
    maximumLength: NotRequired[int]
    stopSequences: NotRequired[List[str]]

class InferenceConfigurationTypeDef(TypedDict):
    temperature: NotRequired[float]
    topP: NotRequired[float]
    topK: NotRequired[int]
    maximumLength: NotRequired[int]
    stopSequences: NotRequired[Sequence[str]]

class TextPromptTypeDef(TypedDict):
    text: str

class KnowledgeBaseLookupInputTypeDef(TypedDict):
    text: NotRequired[str]
    knowledgeBaseId: NotRequired[str]

class InvocationStepSummaryTypeDef(TypedDict):
    sessionId: str
    invocationId: str
    invocationStepId: str
    invocationStepTime: datetime

class InvocationSummaryTypeDef(TypedDict):
    sessionId: str
    invocationId: str
    createdAt: datetime

class PromptCreationConfigurationsTypeDef(TypedDict):
    previousConversationTurnsToInclude: NotRequired[int]
    excludePreviousThinkingSteps: NotRequired[bool]

class StreamingConfigurationsTypeDef(TypedDict):
    streamFinalResponse: NotRequired[bool]
    applyGuardrailInterval: NotRequired[int]

class KnowledgeBaseQueryTypeDef(TypedDict):
    text: str

class ListFlowExecutionEventsRequestTypeDef(TypedDict):
    flowIdentifier: str
    flowAliasIdentifier: str
    executionIdentifier: str
    eventType: FlowExecutionEventTypeType
    maxResults: NotRequired[int]
    nextToken: NotRequired[str]

class ListFlowExecutionsRequestTypeDef(TypedDict):
    flowIdentifier: str
    flowAliasIdentifier: NotRequired[str]
    maxResults: NotRequired[int]
    nextToken: NotRequired[str]

class ListInvocationStepsRequestTypeDef(TypedDict):
    sessionIdentifier: str
    invocationIdentifier: NotRequired[str]
    nextToken: NotRequired[str]
    maxResults: NotRequired[int]

class ListInvocationsRequestTypeDef(TypedDict):
    sessionIdentifier: str
    nextToken: NotRequired[str]
    maxResults: NotRequired[int]

class ListSessionsRequestTypeDef(TypedDict):
    maxResults: NotRequired[int]
    nextToken: NotRequired[str]

class SessionSummaryTypeDef(TypedDict):
    sessionId: str
    sessionArn: str
    sessionStatus: SessionStatusType
    createdAt: datetime
    lastUpdatedAt: datetime

class ListTagsForResourceRequestTypeDef(TypedDict):
    resourceArn: str

class MemorySessionSummaryTypeDef(TypedDict):
    memoryId: NotRequired[str]
    sessionId: NotRequired[str]
    sessionStartTime: NotRequired[datetime]
    sessionExpiryTime: NotRequired[datetime]
    summaryText: NotRequired[str]

class UsageTypeDef(TypedDict):
    inputTokens: NotRequired[int]
    outputTokens: NotRequired[int]

class ModelNotReadyExceptionTypeDef(TypedDict):
    message: NotRequired[str]

class NodeExecutionContentTypeDef(TypedDict):
    document: NotRequired[Dict[str, Any]]

NodeInputExecutionChainItemTypeDef = TypedDict(
    "NodeInputExecutionChainItemTypeDef",
    {
        "nodeName": str,
        "type": FlowControlNodeTypeType,
        "index": NotRequired[int],
    },
)

class NodeInputSourceTypeDef(TypedDict):
    nodeName: str
    outputFieldName: str
    expression: str

class NodeOutputNextTypeDef(TypedDict):
    nodeName: str
    inputFieldName: str

class RepromptResponseTypeDef(TypedDict):
    text: NotRequired[str]
    source: NotRequired[SourceType]

QueryTransformationConfigurationTypeDef = TypedDict(
    "QueryTransformationConfigurationTypeDef",
    {
        "type": Literal["QUERY_DECOMPOSITION"],
    },
)

class RawResponseTypeDef(TypedDict):
    content: NotRequired[str]

class RationaleTypeDef(TypedDict):
    traceId: NotRequired[str]
    text: NotRequired[str]

class PostProcessingParsedResponseTypeDef(TypedDict):
    text: NotRequired[str]

class PreProcessingParsedResponseTypeDef(TypedDict):
    rationale: NotRequired[str]
    isValid: NotRequired[bool]

TimestampTypeDef = Union[datetime, str]

class ReasoningTextBlockTypeDef(TypedDict):
    text: str
    signature: NotRequired[str]

class RerankTextDocumentTypeDef(TypedDict):
    text: NotRequired[str]

class RetrievalResultConfluenceLocationTypeDef(TypedDict):
    url: NotRequired[str]

RetrievalResultContentColumnTypeDef = TypedDict(
    "RetrievalResultContentColumnTypeDef",
    {
        "columnName": NotRequired[str],
        "columnValue": NotRequired[str],
        "type": NotRequired[RetrievalResultContentColumnTypeType],
    },
)
RetrievalResultCustomDocumentLocationTypeDef = TypedDict(
    "RetrievalResultCustomDocumentLocationTypeDef",
    {
        "id": NotRequired[str],
    },
)

class RetrievalResultKendraDocumentLocationTypeDef(TypedDict):
    uri: NotRequired[str]

class RetrievalResultS3LocationTypeDef(TypedDict):
    uri: NotRequired[str]

class RetrievalResultSalesforceLocationTypeDef(TypedDict):
    url: NotRequired[str]

class RetrievalResultSharePointLocationTypeDef(TypedDict):
    url: NotRequired[str]

class RetrievalResultSqlLocationTypeDef(TypedDict):
    query: NotRequired[str]

class RetrievalResultWebLocationTypeDef(TypedDict):
    url: NotRequired[str]

class RetrieveAndGenerateInputTypeDef(TypedDict):
    text: str

class RetrieveAndGenerateOutputEventTypeDef(TypedDict):
    text: str

class RetrieveAndGenerateOutputTypeDef(TypedDict):
    text: str

class RetrieveAndGenerateSessionConfigurationTypeDef(TypedDict):
    kmsKeyArn: str

class SpanTypeDef(TypedDict):
    start: NotRequired[int]
    end: NotRequired[int]

class StopFlowExecutionRequestTypeDef(TypedDict):
    flowIdentifier: str
    flowAliasIdentifier: str
    executionIdentifier: str

class TagResourceRequestTypeDef(TypedDict):
    resourceArn: str
    tags: Mapping[str, str]

class TextToSqlKnowledgeBaseConfigurationTypeDef(TypedDict):
    knowledgeBaseArn: str

class UntagResourceRequestTypeDef(TypedDict):
    resourceArn: str
    tagKeys: Sequence[str]

class UpdateSessionRequestTypeDef(TypedDict):
    sessionIdentifier: str
    sessionMetadata: NotRequired[Mapping[str, str]]

class VectorSearchBedrockRerankingModelConfigurationTypeDef(TypedDict):
    modelArn: str
    additionalModelRequestFields: NotRequired[Mapping[str, Mapping[str, Any]]]

class APISchemaTypeDef(TypedDict):
    s3: NotRequired[S3IdentifierTypeDef]
    payload: NotRequired[str]

class PropertyParametersTypeDef(TypedDict):
    properties: NotRequired[List[ParameterTypeDef]]

class RequestBodyTypeDef(TypedDict):
    content: NotRequired[Dict[str, List[ParameterTypeDef]]]

class BedrockModelConfigurationsTypeDef(TypedDict):
    performanceConfig: NotRequired[PerformanceConfigurationTypeDef]

class InlineBedrockModelConfigurationsTypeDef(TypedDict):
    performanceConfig: NotRequired[PerformanceConfigurationTypeDef]

class ModelPerformanceConfigurationTypeDef(TypedDict):
    performanceConfig: NotRequired[PerformanceConfigurationTypeDef]

class BedrockRerankingConfigurationTypeDef(TypedDict):
    modelConfiguration: BedrockRerankingModelConfigurationTypeDef
    numberOfResults: NotRequired[int]

class ByteContentDocTypeDef(TypedDict):
    identifier: str
    contentType: str
    data: BlobTypeDef

class ByteContentFileTypeDef(TypedDict):
    mediaType: str
    data: BlobTypeDef

ImageInputSourceTypeDef = TypedDict(
    "ImageInputSourceTypeDef",
    {
        "bytes": NotRequired[BlobTypeDef],
    },
)

class ConditionResultEventTypeDef(TypedDict):
    nodeName: str
    timestamp: datetime
    satisfiedConditions: List[SatisfiedConditionTypeDef]

class MessageTypeDef(TypedDict):
    role: ConversationRoleType
    content: Sequence[ContentBlockTypeDef]

class CreateInvocationResponseTypeDef(TypedDict):
    sessionId: str
    invocationId: str
    createdAt: datetime
    ResponseMetadata: ResponseMetadataTypeDef

class CreateSessionResponseTypeDef(TypedDict):
    sessionId: str
    sessionArn: str
    sessionStatus: SessionStatusType
    createdAt: datetime
    ResponseMetadata: ResponseMetadataTypeDef

class EndSessionResponseTypeDef(TypedDict):
    sessionId: str
    sessionArn: str
    sessionStatus: SessionStatusType
    ResponseMetadata: ResponseMetadataTypeDef

class GetExecutionFlowSnapshotResponseTypeDef(TypedDict):
    flowIdentifier: str
    flowAliasIdentifier: str
    flowVersion: str
    executionRoleArn: str
    definition: str
    customerEncryptionKeyArn: str
    ResponseMetadata: ResponseMetadataTypeDef

class GetSessionResponseTypeDef(TypedDict):
    sessionId: str
    sessionArn: str
    sessionStatus: SessionStatusType
    createdAt: datetime
    lastUpdatedAt: datetime
    sessionMetadata: Dict[str, str]
    encryptionKeyArn: str
    ResponseMetadata: ResponseMetadataTypeDef

class ListTagsForResourceResponseTypeDef(TypedDict):
    tags: Dict[str, str]
    ResponseMetadata: ResponseMetadataTypeDef

class PutInvocationStepResponseTypeDef(TypedDict):
    invocationStepId: str
    ResponseMetadata: ResponseMetadataTypeDef

class StartFlowExecutionResponseTypeDef(TypedDict):
    executionArn: str
    ResponseMetadata: ResponseMetadataTypeDef

class StopFlowExecutionResponseTypeDef(TypedDict):
    executionArn: str
    status: FlowExecutionStatusType
    ResponseMetadata: ResponseMetadataTypeDef

class UpdateSessionResponseTypeDef(TypedDict):
    sessionId: str
    sessionArn: str
    sessionStatus: SessionStatusType
    createdAt: datetime
    lastUpdatedAt: datetime
    ResponseMetadata: ResponseMetadataTypeDef

class CustomOrchestrationTraceTypeDef(TypedDict):
    traceId: NotRequired[str]
    event: NotRequired[CustomOrchestrationTraceEventTypeDef]

class CustomOrchestrationTypeDef(TypedDict):
    executor: NotRequired[OrchestrationExecutorTypeDef]

class RerankingMetadataSelectiveModeConfigurationTypeDef(TypedDict):
    fieldsToInclude: NotRequired[Sequence[FieldForRerankingTypeDef]]
    fieldsToExclude: NotRequired[Sequence[FieldForRerankingTypeDef]]

class FilePartTypeDef(TypedDict):
    files: NotRequired[List[OutputFileTypeDef]]

class InlineAgentFilePartTypeDef(TypedDict):
    files: NotRequired[List[OutputFileTypeDef]]

RetrievalFilterPaginatorTypeDef = TypedDict(
    "RetrievalFilterPaginatorTypeDef",
    {
        "equals": NotRequired[FilterAttributeTypeDef],
        "notEquals": NotRequired[FilterAttributeTypeDef],
        "greaterThan": NotRequired[FilterAttributeTypeDef],
        "greaterThanOrEquals": NotRequired[FilterAttributeTypeDef],
        "lessThan": NotRequired[FilterAttributeTypeDef],
        "lessThanOrEquals": NotRequired[FilterAttributeTypeDef],
        "in": NotRequired[FilterAttributeTypeDef],
        "notIn": NotRequired[FilterAttributeTypeDef],
        "startsWith": NotRequired[FilterAttributeTypeDef],
        "listContains": NotRequired[FilterAttributeTypeDef],
        "stringContains": NotRequired[FilterAttributeTypeDef],
        "andAll": NotRequired[Sequence[Mapping[str, Any]]],
        "orAll": NotRequired[Sequence[Mapping[str, Any]]],
    },
)
RetrievalFilterTypeDef = TypedDict(
    "RetrievalFilterTypeDef",
    {
        "equals": NotRequired[FilterAttributeTypeDef],
        "notEquals": NotRequired[FilterAttributeTypeDef],
        "greaterThan": NotRequired[FilterAttributeTypeDef],
        "greaterThanOrEquals": NotRequired[FilterAttributeTypeDef],
        "lessThan": NotRequired[FilterAttributeTypeDef],
        "lessThanOrEquals": NotRequired[FilterAttributeTypeDef],
        "in": NotRequired[FilterAttributeTypeDef],
        "notIn": NotRequired[FilterAttributeTypeDef],
        "startsWith": NotRequired[FilterAttributeTypeDef],
        "listContains": NotRequired[FilterAttributeTypeDef],
        "stringContains": NotRequired[FilterAttributeTypeDef],
        "andAll": NotRequired[Sequence[Mapping[str, Any]]],
        "orAll": NotRequired[Sequence[Mapping[str, Any]]],
    },
)

class FlowInputFieldTypeDef(TypedDict):
    name: str
    content: FlowExecutionContentTypeDef

class FlowOutputFieldTypeDef(TypedDict):
    name: str
    content: FlowExecutionContentTypeDef

class GetFlowExecutionResponseTypeDef(TypedDict):
    executionArn: str
    status: FlowExecutionStatusType
    startedAt: datetime
    endedAt: datetime
    errors: List[FlowExecutionErrorTypeDef]
    flowAliasIdentifier: str
    flowIdentifier: str
    flowVersion: str
    ResponseMetadata: ResponseMetadataTypeDef

class ListFlowExecutionsResponseTypeDef(TypedDict):
    flowExecutionSummaries: List[FlowExecutionSummaryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class FlowInputTypeDef(TypedDict):
    nodeName: str
    content: FlowInputContentTypeDef
    nodeOutputName: NotRequired[str]
    nodeInputName: NotRequired[str]

class FlowMultiTurnInputRequestEventTypeDef(TypedDict):
    nodeName: str
    nodeType: NodeTypeType
    content: FlowMultiTurnInputContentTypeDef

class FlowOutputEventTypeDef(TypedDict):
    nodeName: str
    nodeType: NodeTypeType
    content: FlowOutputContentTypeDef

class FlowTraceConditionNodeResultEventTypeDef(TypedDict):
    nodeName: str
    timestamp: datetime
    satisfiedConditions: List[FlowTraceConditionTypeDef]

FlowTraceNodeInputFieldTypeDef = TypedDict(
    "FlowTraceNodeInputFieldTypeDef",
    {
        "nodeInputName": str,
        "content": FlowTraceNodeInputContentTypeDef,
        "source": NotRequired[FlowTraceNodeInputSourceTypeDef],
        "type": NotRequired[FlowNodeIODataTypeType],
        "category": NotRequired[FlowNodeInputCategoryType],
        "executionChain": NotRequired[List[FlowTraceNodeInputExecutionChainItemTypeDef]],
    },
)
FlowTraceNodeOutputFieldTypeDef = TypedDict(
    "FlowTraceNodeOutputFieldTypeDef",
    {
        "nodeOutputName": str,
        "content": FlowTraceNodeOutputContentTypeDef,
        "next": NotRequired[List[FlowTraceNodeOutputNextTypeDef]],
        "type": NotRequired[FlowNodeIODataTypeType],
    },
)

class FunctionDefinitionTypeDef(TypedDict):
    name: str
    description: NotRequired[str]
    parameters: NotRequired[Mapping[str, ParameterDetailTypeDef]]
    requireConfirmation: NotRequired[RequireConfirmationType]

class FunctionInvocationInputTypeDef(TypedDict):
    actionGroup: str
    parameters: NotRequired[List[FunctionParameterTypeDef]]
    function: NotRequired[str]
    actionInvocationType: NotRequired[ActionInvocationTypeType]
    agentId: NotRequired[str]
    collaboratorName: NotRequired[str]

class GenerateQueryResponseTypeDef(TypedDict):
    queries: List[GeneratedQueryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef

class GetAgentMemoryRequestPaginateTypeDef(TypedDict):
    agentId: str
    agentAliasId: str
    memoryType: Literal["SESSION_SUMMARY"]
    memoryId: str
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class ListFlowExecutionEventsRequestPaginateTypeDef(TypedDict):
    flowIdentifier: str
    flowAliasIdentifier: str
    executionIdentifier: str
    eventType: FlowExecutionEventTypeType
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class ListFlowExecutionsRequestPaginateTypeDef(TypedDict):
    flowIdentifier: str
    flowAliasIdentifier: NotRequired[str]
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class ListInvocationStepsRequestPaginateTypeDef(TypedDict):
    sessionIdentifier: str
    invocationIdentifier: NotRequired[str]
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class ListInvocationsRequestPaginateTypeDef(TypedDict):
    sessionIdentifier: str
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class ListSessionsRequestPaginateTypeDef(TypedDict):
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class GuardrailContentPolicyAssessmentTypeDef(TypedDict):
    filters: NotRequired[List[GuardrailContentFilterTypeDef]]

class GuardrailWordPolicyAssessmentTypeDef(TypedDict):
    customWords: NotRequired[List[GuardrailCustomWordTypeDef]]
    managedWordLists: NotRequired[List[GuardrailManagedWordTypeDef]]

class GuardrailSensitiveInformationPolicyAssessmentTypeDef(TypedDict):
    piiEntities: NotRequired[List[GuardrailPiiEntityFilterTypeDef]]
    regexes: NotRequired[List[GuardrailRegexFilterTypeDef]]

class GuardrailTopicPolicyAssessmentTypeDef(TypedDict):
    topics: NotRequired[List[GuardrailTopicTypeDef]]

ImageInputOutputTypeDef = TypedDict(
    "ImageInputOutputTypeDef",
    {
        "format": ImageInputFormatType,
        "source": ImageInputSourceOutputTypeDef,
    },
)
ImageSourceOutputTypeDef = TypedDict(
    "ImageSourceOutputTypeDef",
    {
        "bytes": NotRequired[bytes],
        "s3Location": NotRequired[S3LocationTypeDef],
    },
)
ImageSourceTypeDef = TypedDict(
    "ImageSourceTypeDef",
    {
        "bytes": NotRequired[BlobTypeDef],
        "s3Location": NotRequired[S3LocationTypeDef],
    },
)

class ImplicitFilterConfigurationTypeDef(TypedDict):
    metadataAttributes: Sequence[MetadataAttributeSchemaTypeDef]
    modelArn: str

class InferenceConfigTypeDef(TypedDict):
    textInferenceConfig: NotRequired[TextInferenceConfigTypeDef]

ModelInvocationInputTypeDef = TypedDict(
    "ModelInvocationInputTypeDef",
    {
        "traceId": NotRequired[str],
        "text": NotRequired[str],
        "type": NotRequired[PromptTypeType],
        "overrideLambda": NotRequired[str],
        "promptCreationMode": NotRequired[CreationModeType],
        "inferenceConfiguration": NotRequired[InferenceConfigurationOutputTypeDef],
        "parserMode": NotRequired[CreationModeType],
        "foundationModel": NotRequired[str],
    },
)
InferenceConfigurationUnionTypeDef = Union[
    InferenceConfigurationTypeDef, InferenceConfigurationOutputTypeDef
]

class InputPromptTypeDef(TypedDict):
    textPrompt: NotRequired[TextPromptTypeDef]

class OptimizedPromptTypeDef(TypedDict):
    textPrompt: NotRequired[TextPromptTypeDef]

class ListInvocationStepsResponseTypeDef(TypedDict):
    invocationStepSummaries: List[InvocationStepSummaryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class ListInvocationsResponseTypeDef(TypedDict):
    invocationSummaries: List[InvocationSummaryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class ListSessionsResponseTypeDef(TypedDict):
    sessionSummaries: List[SessionSummaryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class MemoryTypeDef(TypedDict):
    sessionSummary: NotRequired[MemorySessionSummaryTypeDef]

class MetadataTypeDef(TypedDict):
    startTime: NotRequired[datetime]
    endTime: NotRequired[datetime]
    totalTimeMs: NotRequired[int]
    operationTotalTimeMs: NotRequired[int]
    clientRequestId: NotRequired[str]
    usage: NotRequired[UsageTypeDef]

NodeInputFieldTypeDef = TypedDict(
    "NodeInputFieldTypeDef",
    {
        "name": str,
        "content": NodeExecutionContentTypeDef,
        "source": NotRequired[NodeInputSourceTypeDef],
        "type": NotRequired[FlowNodeIODataTypeType],
        "category": NotRequired[FlowNodeInputCategoryType],
        "executionChain": NotRequired[List[NodeInputExecutionChainItemTypeDef]],
    },
)
NodeOutputFieldTypeDef = TypedDict(
    "NodeOutputFieldTypeDef",
    {
        "name": str,
        "content": NodeExecutionContentTypeDef,
        "next": NotRequired[List[NodeOutputNextTypeDef]],
        "type": NotRequired[FlowNodeIODataTypeType],
    },
)

class ReasoningContentBlockTypeDef(TypedDict):
    reasoningText: NotRequired[ReasoningTextBlockTypeDef]
    redactedContent: NotRequired[bytes]

RerankDocumentOutputTypeDef = TypedDict(
    "RerankDocumentOutputTypeDef",
    {
        "type": RerankDocumentTypeType,
        "textDocument": NotRequired[RerankTextDocumentTypeDef],
        "jsonDocument": NotRequired[Dict[str, Any]],
    },
)
RerankDocumentTypeDef = TypedDict(
    "RerankDocumentTypeDef",
    {
        "type": RerankDocumentTypeType,
        "textDocument": NotRequired[RerankTextDocumentTypeDef],
        "jsonDocument": NotRequired[Mapping[str, Any]],
    },
)
RerankQueryTypeDef = TypedDict(
    "RerankQueryTypeDef",
    {
        "type": Literal["TEXT"],
        "textQuery": RerankTextDocumentTypeDef,
    },
)
RetrievalResultContentTypeDef = TypedDict(
    "RetrievalResultContentTypeDef",
    {
        "type": NotRequired[RetrievalResultContentTypeType],
        "text": NotRequired[str],
        "byteContent": NotRequired[str],
        "row": NotRequired[List[RetrievalResultContentColumnTypeDef]],
    },
)
RetrievalResultLocationTypeDef = TypedDict(
    "RetrievalResultLocationTypeDef",
    {
        "type": RetrievalResultLocationTypeType,
        "s3Location": NotRequired[RetrievalResultS3LocationTypeDef],
        "webLocation": NotRequired[RetrievalResultWebLocationTypeDef],
        "confluenceLocation": NotRequired[RetrievalResultConfluenceLocationTypeDef],
        "salesforceLocation": NotRequired[RetrievalResultSalesforceLocationTypeDef],
        "sharePointLocation": NotRequired[RetrievalResultSharePointLocationTypeDef],
        "customDocumentLocation": NotRequired[RetrievalResultCustomDocumentLocationTypeDef],
        "kendraDocumentLocation": NotRequired[RetrievalResultKendraDocumentLocationTypeDef],
        "sqlLocation": NotRequired[RetrievalResultSqlLocationTypeDef],
    },
)

class TextResponsePartTypeDef(TypedDict):
    text: NotRequired[str]
    span: NotRequired[SpanTypeDef]

TextToSqlConfigurationTypeDef = TypedDict(
    "TextToSqlConfigurationTypeDef",
    {
        "type": Literal["KNOWLEDGE_BASE"],
        "knowledgeBaseConfiguration": NotRequired[TextToSqlKnowledgeBaseConfigurationTypeDef],
    },
)

class ApiRequestBodyTypeDef(TypedDict):
    content: NotRequired[Dict[str, PropertyParametersTypeDef]]

class ActionGroupInvocationInputTypeDef(TypedDict):
    actionGroupName: NotRequired[str]
    verb: NotRequired[str]
    apiPath: NotRequired[str]
    parameters: NotRequired[List[ParameterTypeDef]]
    requestBody: NotRequired[RequestBodyTypeDef]
    function: NotRequired[str]
    executionType: NotRequired[ExecutionTypeType]
    invocationId: NotRequired[str]

RerankingConfigurationTypeDef = TypedDict(
    "RerankingConfigurationTypeDef",
    {
        "type": Literal["BEDROCK_RERANKING_MODEL"],
        "bedrockRerankingConfiguration": BedrockRerankingConfigurationTypeDef,
    },
)

class ExternalSourceTypeDef(TypedDict):
    sourceType: ExternalSourceTypeType
    s3Location: NotRequired[S3ObjectDocTypeDef]
    byteContent: NotRequired[ByteContentDocTypeDef]

class FileSourceTypeDef(TypedDict):
    sourceType: FileSourceTypeType
    s3Location: NotRequired[S3ObjectFileTypeDef]
    byteContent: NotRequired[ByteContentFileTypeDef]

ImageInputSourceUnionTypeDef = Union[ImageInputSourceTypeDef, ImageInputSourceOutputTypeDef]

class ConversationHistoryTypeDef(TypedDict):
    messages: NotRequired[Sequence[MessageTypeDef]]

class MetadataConfigurationForRerankingTypeDef(TypedDict):
    selectionMode: RerankingMetadataSelectionModeType
    selectiveModeConfiguration: NotRequired[RerankingMetadataSelectiveModeConfigurationTypeDef]

class FlowExecutionInputEventTypeDef(TypedDict):
    nodeName: str
    timestamp: datetime
    fields: List[FlowInputFieldTypeDef]

class FlowExecutionOutputEventTypeDef(TypedDict):
    nodeName: str
    timestamp: datetime
    fields: List[FlowOutputFieldTypeDef]

class InvokeFlowRequestTypeDef(TypedDict):
    flowIdentifier: str
    flowAliasIdentifier: str
    inputs: Sequence[FlowInputTypeDef]
    enableTrace: NotRequired[bool]
    modelPerformanceConfiguration: NotRequired[ModelPerformanceConfigurationTypeDef]
    executionId: NotRequired[str]

class StartFlowExecutionRequestTypeDef(TypedDict):
    flowIdentifier: str
    flowAliasIdentifier: str
    inputs: Sequence[FlowInputTypeDef]
    flowExecutionName: NotRequired[str]
    modelPerformanceConfiguration: NotRequired[ModelPerformanceConfigurationTypeDef]

class FlowTraceNodeInputEventTypeDef(TypedDict):
    nodeName: str
    timestamp: datetime
    fields: List[FlowTraceNodeInputFieldTypeDef]

class FlowTraceNodeOutputEventTypeDef(TypedDict):
    nodeName: str
    timestamp: datetime
    fields: List[FlowTraceNodeOutputFieldTypeDef]

class FunctionSchemaTypeDef(TypedDict):
    functions: NotRequired[Sequence[FunctionDefinitionTypeDef]]

class GuardrailAssessmentTypeDef(TypedDict):
    topicPolicy: NotRequired[GuardrailTopicPolicyAssessmentTypeDef]
    contentPolicy: NotRequired[GuardrailContentPolicyAssessmentTypeDef]
    wordPolicy: NotRequired[GuardrailWordPolicyAssessmentTypeDef]
    sensitiveInformationPolicy: NotRequired[GuardrailSensitiveInformationPolicyAssessmentTypeDef]

class ContentBodyOutputTypeDef(TypedDict):
    body: NotRequired[str]
    images: NotRequired[List[ImageInputOutputTypeDef]]

ImageBlockOutputTypeDef = TypedDict(
    "ImageBlockOutputTypeDef",
    {
        "format": ImageFormatType,
        "source": ImageSourceOutputTypeDef,
    },
)
ImageBlockTypeDef = TypedDict(
    "ImageBlockTypeDef",
    {
        "format": ImageFormatType,
        "source": ImageSourceTypeDef,
    },
)

class ExternalSourcesGenerationConfigurationTypeDef(TypedDict):
    promptTemplate: NotRequired[PromptTemplateTypeDef]
    guardrailConfiguration: NotRequired[GuardrailConfigurationTypeDef]
    inferenceConfig: NotRequired[InferenceConfigTypeDef]
    additionalModelRequestFields: NotRequired[Mapping[str, Mapping[str, Any]]]
    performanceConfig: NotRequired[PerformanceConfigurationTypeDef]

class GenerationConfigurationTypeDef(TypedDict):
    promptTemplate: NotRequired[PromptTemplateTypeDef]
    guardrailConfiguration: NotRequired[GuardrailConfigurationTypeDef]
    inferenceConfig: NotRequired[InferenceConfigTypeDef]
    additionalModelRequestFields: NotRequired[Mapping[str, Mapping[str, Any]]]
    performanceConfig: NotRequired[PerformanceConfigurationTypeDef]

class OrchestrationConfigurationTypeDef(TypedDict):
    promptTemplate: NotRequired[PromptTemplateTypeDef]
    inferenceConfig: NotRequired[InferenceConfigTypeDef]
    additionalModelRequestFields: NotRequired[Mapping[str, Mapping[str, Any]]]
    queryTransformationConfiguration: NotRequired[QueryTransformationConfigurationTypeDef]
    performanceConfig: NotRequired[PerformanceConfigurationTypeDef]

class PromptConfigurationTypeDef(TypedDict):
    promptType: NotRequired[PromptTypeType]
    promptCreationMode: NotRequired[CreationModeType]
    promptState: NotRequired[PromptStateType]
    basePromptTemplate: NotRequired[str]
    inferenceConfiguration: NotRequired[InferenceConfigurationUnionTypeDef]
    parserMode: NotRequired[CreationModeType]
    foundationModel: NotRequired[str]
    additionalModelRequestFields: NotRequired[Mapping[str, Any]]

OptimizePromptRequestTypeDef = TypedDict(
    "OptimizePromptRequestTypeDef",
    {
        "input": InputPromptTypeDef,
        "targetModelId": str,
    },
)

class OptimizedPromptEventTypeDef(TypedDict):
    optimizedPrompt: NotRequired[OptimizedPromptTypeDef]

class GetAgentMemoryResponseTypeDef(TypedDict):
    memoryContents: List[MemoryTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class ActionGroupInvocationOutputTypeDef(TypedDict):
    text: NotRequired[str]
    metadata: NotRequired[MetadataTypeDef]

class CodeInterpreterInvocationOutputTypeDef(TypedDict):
    executionOutput: NotRequired[str]
    executionError: NotRequired[str]
    files: NotRequired[List[str]]
    executionTimeout: NotRequired[bool]
    metadata: NotRequired[MetadataTypeDef]

class FailureTraceTypeDef(TypedDict):
    traceId: NotRequired[str]
    failureReason: NotRequired[str]
    failureCode: NotRequired[int]
    metadata: NotRequired[MetadataTypeDef]

class FinalResponseTypeDef(TypedDict):
    text: NotRequired[str]
    metadata: NotRequired[MetadataTypeDef]

class RoutingClassifierModelInvocationOutputTypeDef(TypedDict):
    traceId: NotRequired[str]
    rawResponse: NotRequired[RawResponseTypeDef]
    metadata: NotRequired[MetadataTypeDef]

class NodeInputEventTypeDef(TypedDict):
    nodeName: str
    timestamp: datetime
    fields: List[NodeInputFieldTypeDef]

class NodeOutputEventTypeDef(TypedDict):
    nodeName: str
    timestamp: datetime
    fields: List[NodeOutputFieldTypeDef]

class OrchestrationModelInvocationOutputTypeDef(TypedDict):
    traceId: NotRequired[str]
    rawResponse: NotRequired[RawResponseTypeDef]
    metadata: NotRequired[MetadataTypeDef]
    reasoningContent: NotRequired[ReasoningContentBlockTypeDef]

class PostProcessingModelInvocationOutputTypeDef(TypedDict):
    traceId: NotRequired[str]
    parsedResponse: NotRequired[PostProcessingParsedResponseTypeDef]
    rawResponse: NotRequired[RawResponseTypeDef]
    metadata: NotRequired[MetadataTypeDef]
    reasoningContent: NotRequired[ReasoningContentBlockTypeDef]

class PreProcessingModelInvocationOutputTypeDef(TypedDict):
    traceId: NotRequired[str]
    parsedResponse: NotRequired[PreProcessingParsedResponseTypeDef]
    rawResponse: NotRequired[RawResponseTypeDef]
    metadata: NotRequired[MetadataTypeDef]
    reasoningContent: NotRequired[ReasoningContentBlockTypeDef]

class RerankResultTypeDef(TypedDict):
    index: int
    relevanceScore: float
    document: NotRequired[RerankDocumentOutputTypeDef]

RerankDocumentUnionTypeDef = Union[RerankDocumentTypeDef, RerankDocumentOutputTypeDef]

class KnowledgeBaseRetrievalResultTypeDef(TypedDict):
    content: RetrievalResultContentTypeDef
    location: NotRequired[RetrievalResultLocationTypeDef]
    score: NotRequired[float]
    metadata: NotRequired[Dict[str, Dict[str, Any]]]

class RetrievedReferenceTypeDef(TypedDict):
    content: NotRequired[RetrievalResultContentTypeDef]
    location: NotRequired[RetrievalResultLocationTypeDef]
    metadata: NotRequired[Dict[str, Dict[str, Any]]]

class GeneratedResponsePartTypeDef(TypedDict):
    textResponsePart: NotRequired[TextResponsePartTypeDef]

class TransformationConfigurationTypeDef(TypedDict):
    mode: Literal["TEXT_TO_SQL"]
    textToSqlConfiguration: NotRequired[TextToSqlConfigurationTypeDef]

class ApiInvocationInputTypeDef(TypedDict):
    actionGroup: str
    httpMethod: NotRequired[str]
    apiPath: NotRequired[str]
    parameters: NotRequired[List[ApiParameterTypeDef]]
    requestBody: NotRequired[ApiRequestBodyTypeDef]
    actionInvocationType: NotRequired[ActionInvocationTypeType]
    agentId: NotRequired[str]
    collaboratorName: NotRequired[str]

class InputFileTypeDef(TypedDict):
    name: str
    source: FileSourceTypeDef
    useCase: FileUseCaseType

ImageInputTypeDef = TypedDict(
    "ImageInputTypeDef",
    {
        "format": ImageInputFormatType,
        "source": ImageInputSourceUnionTypeDef,
    },
)

class VectorSearchBedrockRerankingConfigurationTypeDef(TypedDict):
    modelConfiguration: VectorSearchBedrockRerankingModelConfigurationTypeDef
    numberOfRerankedResults: NotRequired[int]
    metadataConfiguration: NotRequired[MetadataConfigurationForRerankingTypeDef]

class AgentActionGroupTypeDef(TypedDict):
    actionGroupName: str
    description: NotRequired[str]
    parentActionGroupSignature: NotRequired[ActionGroupSignatureType]
    actionGroupExecutor: NotRequired[ActionGroupExecutorTypeDef]
    apiSchema: NotRequired[APISchemaTypeDef]
    functionSchema: NotRequired[FunctionSchemaTypeDef]
    parentActionGroupSignatureParams: NotRequired[Mapping[str, str]]

class GuardrailTraceTypeDef(TypedDict):
    action: NotRequired[GuardrailActionType]
    traceId: NotRequired[str]
    inputAssessments: NotRequired[List[GuardrailAssessmentTypeDef]]
    outputAssessments: NotRequired[List[GuardrailAssessmentTypeDef]]
    metadata: NotRequired[MetadataTypeDef]

class ApiResultOutputTypeDef(TypedDict):
    actionGroup: str
    httpMethod: NotRequired[str]
    apiPath: NotRequired[str]
    confirmationState: NotRequired[ConfirmationStateType]
    responseState: NotRequired[ResponseStateType]
    httpStatusCode: NotRequired[int]
    responseBody: NotRequired[Dict[str, ContentBodyOutputTypeDef]]
    agentId: NotRequired[str]

class FunctionResultOutputTypeDef(TypedDict):
    actionGroup: str
    confirmationState: NotRequired[ConfirmationStateType]
    function: NotRequired[str]
    responseBody: NotRequired[Dict[str, ContentBodyOutputTypeDef]]
    responseState: NotRequired[ResponseStateType]
    agentId: NotRequired[str]

class BedrockSessionContentBlockOutputTypeDef(TypedDict):
    text: NotRequired[str]
    image: NotRequired[ImageBlockOutputTypeDef]

class BedrockSessionContentBlockTypeDef(TypedDict):
    text: NotRequired[str]
    image: NotRequired[ImageBlockTypeDef]

class ExternalSourcesRetrieveAndGenerateConfigurationTypeDef(TypedDict):
    modelArn: str
    sources: Sequence[ExternalSourceTypeDef]
    generationConfiguration: NotRequired[ExternalSourcesGenerationConfigurationTypeDef]

class PromptOverrideConfigurationTypeDef(TypedDict):
    promptConfigurations: Sequence[PromptConfigurationTypeDef]
    overrideLambda: NotRequired[str]

class OptimizedPromptStreamTypeDef(TypedDict):
    optimizedPromptEvent: NotRequired[OptimizedPromptEventTypeDef]
    analyzePromptEvent: NotRequired[AnalyzePromptEventTypeDef]
    internalServerException: NotRequired[InternalServerExceptionTypeDef]
    throttlingException: NotRequired[ThrottlingExceptionTypeDef]
    validationException: NotRequired[ValidationExceptionTypeDef]
    dependencyFailedException: NotRequired[DependencyFailedExceptionTypeDef]
    accessDeniedException: NotRequired[AccessDeniedExceptionTypeDef]
    badGatewayException: NotRequired[BadGatewayExceptionTypeDef]

class PostProcessingTraceTypeDef(TypedDict):
    modelInvocationInput: NotRequired[ModelInvocationInputTypeDef]
    modelInvocationOutput: NotRequired[PostProcessingModelInvocationOutputTypeDef]

class PreProcessingTraceTypeDef(TypedDict):
    modelInvocationInput: NotRequired[ModelInvocationInputTypeDef]
    modelInvocationOutput: NotRequired[PreProcessingModelInvocationOutputTypeDef]

class RerankResponseTypeDef(TypedDict):
    results: List[RerankResultTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

RerankSourceTypeDef = TypedDict(
    "RerankSourceTypeDef",
    {
        "type": Literal["INLINE"],
        "inlineDocumentSource": RerankDocumentUnionTypeDef,
    },
)

class RetrieveResponseTypeDef(TypedDict):
    retrievalResults: List[KnowledgeBaseRetrievalResultTypeDef]
    guardrailAction: GuadrailActionType
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class KnowledgeBaseLookupOutputTypeDef(TypedDict):
    retrievedReferences: NotRequired[List[RetrievedReferenceTypeDef]]
    metadata: NotRequired[MetadataTypeDef]

class CitationTypeDef(TypedDict):
    generatedResponsePart: NotRequired[GeneratedResponsePartTypeDef]
    retrievedReferences: NotRequired[List[RetrievedReferenceTypeDef]]

class GenerateQueryRequestTypeDef(TypedDict):
    queryGenerationInput: QueryGenerationInputTypeDef
    transformationConfiguration: TransformationConfigurationTypeDef

class InvocationInputMemberTypeDef(TypedDict):
    apiInvocationInput: NotRequired[ApiInvocationInputTypeDef]
    functionInvocationInput: NotRequired[FunctionInvocationInputTypeDef]

ImageInputUnionTypeDef = Union[ImageInputTypeDef, ImageInputOutputTypeDef]
VectorSearchRerankingConfigurationTypeDef = TypedDict(
    "VectorSearchRerankingConfigurationTypeDef",
    {
        "type": Literal["BEDROCK_RERANKING_MODEL"],
        "bedrockRerankingConfiguration": NotRequired[
            VectorSearchBedrockRerankingConfigurationTypeDef
        ],
    },
)

class InvocationResultMemberOutputTypeDef(TypedDict):
    apiResult: NotRequired[ApiResultOutputTypeDef]
    functionResult: NotRequired[FunctionResultOutputTypeDef]

class InvocationStepPayloadOutputTypeDef(TypedDict):
    contentBlocks: NotRequired[List[BedrockSessionContentBlockOutputTypeDef]]

class InvocationStepPayloadTypeDef(TypedDict):
    contentBlocks: NotRequired[Sequence[BedrockSessionContentBlockTypeDef]]

class OptimizePromptResponseTypeDef(TypedDict):
    optimizedPrompt: EventStream[OptimizedPromptStreamTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef

class RerankRequestPaginateTypeDef(TypedDict):
    queries: Sequence[RerankQueryTypeDef]
    sources: Sequence[RerankSourceTypeDef]
    rerankingConfiguration: RerankingConfigurationTypeDef
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class RerankRequestTypeDef(TypedDict):
    queries: Sequence[RerankQueryTypeDef]
    sources: Sequence[RerankSourceTypeDef]
    rerankingConfiguration: RerankingConfigurationTypeDef
    nextToken: NotRequired[str]

class AttributionTypeDef(TypedDict):
    citations: NotRequired[List[CitationTypeDef]]

class CitationEventTypeDef(TypedDict):
    citation: NotRequired[CitationTypeDef]
    generatedResponsePart: NotRequired[GeneratedResponsePartTypeDef]
    retrievedReferences: NotRequired[List[RetrievedReferenceTypeDef]]

class RetrieveAndGenerateResponseTypeDef(TypedDict):
    sessionId: str
    output: RetrieveAndGenerateOutputTypeDef
    citations: List[CitationTypeDef]
    guardrailAction: GuadrailActionType
    ResponseMetadata: ResponseMetadataTypeDef

class InlineAgentReturnControlPayloadTypeDef(TypedDict):
    invocationInputs: NotRequired[List[InvocationInputMemberTypeDef]]
    invocationId: NotRequired[str]

class ReturnControlPayloadTypeDef(TypedDict):
    invocationInputs: NotRequired[List[InvocationInputMemberTypeDef]]
    invocationId: NotRequired[str]

class ContentBodyTypeDef(TypedDict):
    body: NotRequired[str]
    images: NotRequired[Sequence[ImageInputUnionTypeDef]]

KnowledgeBaseVectorSearchConfigurationPaginatorTypeDef = TypedDict(
    "KnowledgeBaseVectorSearchConfigurationPaginatorTypeDef",
    {
        "numberOfResults": NotRequired[int],
        "overrideSearchType": NotRequired[SearchTypeType],
        "filter": NotRequired[RetrievalFilterPaginatorTypeDef],
        "rerankingConfiguration": NotRequired[VectorSearchRerankingConfigurationTypeDef],
        "implicitFilterConfiguration": NotRequired[ImplicitFilterConfigurationTypeDef],
    },
)
KnowledgeBaseVectorSearchConfigurationTypeDef = TypedDict(
    "KnowledgeBaseVectorSearchConfigurationTypeDef",
    {
        "numberOfResults": NotRequired[int],
        "overrideSearchType": NotRequired[SearchTypeType],
        "filter": NotRequired[RetrievalFilterTypeDef],
        "rerankingConfiguration": NotRequired[VectorSearchRerankingConfigurationTypeDef],
        "implicitFilterConfiguration": NotRequired[ImplicitFilterConfigurationTypeDef],
    },
)

class ReturnControlResultsTypeDef(TypedDict):
    invocationId: NotRequired[str]
    returnControlInvocationResults: NotRequired[List[InvocationResultMemberOutputTypeDef]]

class InvocationStepTypeDef(TypedDict):
    sessionId: str
    invocationId: str
    invocationStepId: str
    invocationStepTime: datetime
    payload: InvocationStepPayloadOutputTypeDef

InvocationStepPayloadUnionTypeDef = Union[
    InvocationStepPayloadTypeDef, InvocationStepPayloadOutputTypeDef
]
InlineAgentPayloadPartTypeDef = TypedDict(
    "InlineAgentPayloadPartTypeDef",
    {
        "bytes": NotRequired[bytes],
        "attribution": NotRequired[AttributionTypeDef],
    },
)
PayloadPartTypeDef = TypedDict(
    "PayloadPartTypeDef",
    {
        "bytes": NotRequired[bytes],
        "attribution": NotRequired[AttributionTypeDef],
    },
)

class RetrieveAndGenerateStreamResponseOutputTypeDef(TypedDict):
    output: NotRequired[RetrieveAndGenerateOutputEventTypeDef]
    citation: NotRequired[CitationEventTypeDef]
    guardrail: NotRequired[GuardrailEventTypeDef]
    internalServerException: NotRequired[InternalServerExceptionTypeDef]
    validationException: NotRequired[ValidationExceptionTypeDef]
    resourceNotFoundException: NotRequired[ResourceNotFoundExceptionTypeDef]
    serviceQuotaExceededException: NotRequired[ServiceQuotaExceededExceptionTypeDef]
    throttlingException: NotRequired[ThrottlingExceptionTypeDef]
    accessDeniedException: NotRequired[AccessDeniedExceptionTypeDef]
    conflictException: NotRequired[ConflictExceptionTypeDef]
    dependencyFailedException: NotRequired[DependencyFailedExceptionTypeDef]
    badGatewayException: NotRequired[BadGatewayExceptionTypeDef]

AgentCollaboratorOutputPayloadTypeDef = TypedDict(
    "AgentCollaboratorOutputPayloadTypeDef",
    {
        "type": NotRequired[PayloadTypeType],
        "text": NotRequired[str],
        "returnControlPayload": NotRequired[ReturnControlPayloadTypeDef],
    },
)
ContentBodyUnionTypeDef = Union[ContentBodyTypeDef, ContentBodyOutputTypeDef]

class KnowledgeBaseRetrievalConfigurationPaginatorTypeDef(TypedDict):
    vectorSearchConfiguration: KnowledgeBaseVectorSearchConfigurationPaginatorTypeDef

class KnowledgeBaseRetrievalConfigurationTypeDef(TypedDict):
    vectorSearchConfiguration: KnowledgeBaseVectorSearchConfigurationTypeDef

AgentCollaboratorInputPayloadTypeDef = TypedDict(
    "AgentCollaboratorInputPayloadTypeDef",
    {
        "type": NotRequired[PayloadTypeType],
        "text": NotRequired[str],
        "returnControlResults": NotRequired[ReturnControlResultsTypeDef],
    },
)

class GetInvocationStepResponseTypeDef(TypedDict):
    invocationStep: InvocationStepTypeDef
    ResponseMetadata: ResponseMetadataTypeDef

class PutInvocationStepRequestTypeDef(TypedDict):
    sessionIdentifier: str
    invocationIdentifier: str
    invocationStepTime: TimestampTypeDef
    payload: InvocationStepPayloadUnionTypeDef
    invocationStepId: NotRequired[str]

class RetrieveAndGenerateStreamResponseTypeDef(TypedDict):
    stream: EventStream[RetrieveAndGenerateStreamResponseOutputTypeDef]
    sessionId: str
    ResponseMetadata: ResponseMetadataTypeDef

class AgentCollaboratorInvocationOutputTypeDef(TypedDict):
    agentCollaboratorName: NotRequired[str]
    agentCollaboratorAliasArn: NotRequired[str]
    output: NotRequired[AgentCollaboratorOutputPayloadTypeDef]
    metadata: NotRequired[MetadataTypeDef]

class ApiResultTypeDef(TypedDict):
    actionGroup: str
    httpMethod: NotRequired[str]
    apiPath: NotRequired[str]
    confirmationState: NotRequired[ConfirmationStateType]
    responseState: NotRequired[ResponseStateType]
    httpStatusCode: NotRequired[int]
    responseBody: NotRequired[Mapping[str, ContentBodyUnionTypeDef]]
    agentId: NotRequired[str]

class FunctionResultTypeDef(TypedDict):
    actionGroup: str
    confirmationState: NotRequired[ConfirmationStateType]
    function: NotRequired[str]
    responseBody: NotRequired[Mapping[str, ContentBodyUnionTypeDef]]
    responseState: NotRequired[ResponseStateType]
    agentId: NotRequired[str]

class RetrieveRequestPaginateTypeDef(TypedDict):
    knowledgeBaseId: str
    retrievalQuery: KnowledgeBaseQueryTypeDef
    retrievalConfiguration: NotRequired[KnowledgeBaseRetrievalConfigurationPaginatorTypeDef]
    guardrailConfiguration: NotRequired[GuardrailConfigurationTypeDef]
    PaginationConfig: NotRequired[PaginatorConfigTypeDef]

class KnowledgeBaseConfigurationTypeDef(TypedDict):
    knowledgeBaseId: str
    retrievalConfiguration: KnowledgeBaseRetrievalConfigurationTypeDef

class KnowledgeBaseRetrieveAndGenerateConfigurationTypeDef(TypedDict):
    knowledgeBaseId: str
    modelArn: str
    retrievalConfiguration: NotRequired[KnowledgeBaseRetrievalConfigurationTypeDef]
    generationConfiguration: NotRequired[GenerationConfigurationTypeDef]
    orchestrationConfiguration: NotRequired[OrchestrationConfigurationTypeDef]

class KnowledgeBaseTypeDef(TypedDict):
    knowledgeBaseId: str
    description: str
    retrievalConfiguration: NotRequired[KnowledgeBaseRetrievalConfigurationTypeDef]

class RetrieveRequestTypeDef(TypedDict):
    knowledgeBaseId: str
    retrievalQuery: KnowledgeBaseQueryTypeDef
    retrievalConfiguration: NotRequired[KnowledgeBaseRetrievalConfigurationTypeDef]
    guardrailConfiguration: NotRequired[GuardrailConfigurationTypeDef]
    nextToken: NotRequired[str]

AgentCollaboratorInvocationInputTypeDef = TypedDict(
    "AgentCollaboratorInvocationInputTypeDef",
    {
        "agentCollaboratorName": NotRequired[str],
        "agentCollaboratorAliasArn": NotRequired[str],
        "input": NotRequired[AgentCollaboratorInputPayloadTypeDef],
    },
)
ObservationTypeDef = TypedDict(
    "ObservationTypeDef",
    {
        "traceId": NotRequired[str],
        "type": NotRequired[TypeType],
        "actionGroupInvocationOutput": NotRequired[ActionGroupInvocationOutputTypeDef],
        "agentCollaboratorInvocationOutput": NotRequired[AgentCollaboratorInvocationOutputTypeDef],
        "knowledgeBaseLookupOutput": NotRequired[KnowledgeBaseLookupOutputTypeDef],
        "finalResponse": NotRequired[FinalResponseTypeDef],
        "repromptResponse": NotRequired[RepromptResponseTypeDef],
        "codeInterpreterInvocationOutput": NotRequired[CodeInterpreterInvocationOutputTypeDef],
    },
)
ApiResultUnionTypeDef = Union[ApiResultTypeDef, ApiResultOutputTypeDef]
FunctionResultUnionTypeDef = Union[FunctionResultTypeDef, FunctionResultOutputTypeDef]
RetrieveAndGenerateConfigurationTypeDef = TypedDict(
    "RetrieveAndGenerateConfigurationTypeDef",
    {
        "type": RetrieveAndGenerateTypeType,
        "knowledgeBaseConfiguration": NotRequired[
            KnowledgeBaseRetrieveAndGenerateConfigurationTypeDef
        ],
        "externalSourcesConfiguration": NotRequired[
            ExternalSourcesRetrieveAndGenerateConfigurationTypeDef
        ],
    },
)

class CollaboratorTypeDef(TypedDict):
    foundationModel: str
    instruction: str
    customerEncryptionKeyArn: NotRequired[str]
    idleSessionTTLInSeconds: NotRequired[int]
    actionGroups: NotRequired[Sequence[AgentActionGroupTypeDef]]
    knowledgeBases: NotRequired[Sequence[KnowledgeBaseTypeDef]]
    guardrailConfiguration: NotRequired[GuardrailConfigurationWithArnTypeDef]
    promptOverrideConfiguration: NotRequired[PromptOverrideConfigurationTypeDef]
    agentCollaboration: NotRequired[AgentCollaborationType]
    collaboratorConfigurations: NotRequired[Sequence[CollaboratorConfigurationTypeDef]]
    agentName: NotRequired[str]

class InvocationInputTypeDef(TypedDict):
    traceId: NotRequired[str]
    invocationType: NotRequired[InvocationTypeType]
    actionGroupInvocationInput: NotRequired[ActionGroupInvocationInputTypeDef]
    knowledgeBaseLookupInput: NotRequired[KnowledgeBaseLookupInputTypeDef]
    codeInterpreterInvocationInput: NotRequired[CodeInterpreterInvocationInputTypeDef]
    agentCollaboratorInvocationInput: NotRequired[AgentCollaboratorInvocationInputTypeDef]

class InvocationResultMemberTypeDef(TypedDict):
    apiResult: NotRequired[ApiResultUnionTypeDef]
    functionResult: NotRequired[FunctionResultUnionTypeDef]

RetrieveAndGenerateRequestTypeDef = TypedDict(
    "RetrieveAndGenerateRequestTypeDef",
    {
        "input": RetrieveAndGenerateInputTypeDef,
        "sessionId": NotRequired[str],
        "retrieveAndGenerateConfiguration": NotRequired[RetrieveAndGenerateConfigurationTypeDef],
        "sessionConfiguration": NotRequired[RetrieveAndGenerateSessionConfigurationTypeDef],
    },
)
RetrieveAndGenerateStreamRequestTypeDef = TypedDict(
    "RetrieveAndGenerateStreamRequestTypeDef",
    {
        "input": RetrieveAndGenerateInputTypeDef,
        "sessionId": NotRequired[str],
        "retrieveAndGenerateConfiguration": NotRequired[RetrieveAndGenerateConfigurationTypeDef],
        "sessionConfiguration": NotRequired[RetrieveAndGenerateSessionConfigurationTypeDef],
    },
)

class OrchestrationTraceTypeDef(TypedDict):
    rationale: NotRequired[RationaleTypeDef]
    invocationInput: NotRequired[InvocationInputTypeDef]
    observation: NotRequired[ObservationTypeDef]
    modelInvocationInput: NotRequired[ModelInvocationInputTypeDef]
    modelInvocationOutput: NotRequired[OrchestrationModelInvocationOutputTypeDef]

class RoutingClassifierTraceTypeDef(TypedDict):
    invocationInput: NotRequired[InvocationInputTypeDef]
    observation: NotRequired[ObservationTypeDef]
    modelInvocationInput: NotRequired[ModelInvocationInputTypeDef]
    modelInvocationOutput: NotRequired[RoutingClassifierModelInvocationOutputTypeDef]

InvocationResultMemberUnionTypeDef = Union[
    InvocationResultMemberTypeDef, InvocationResultMemberOutputTypeDef
]

class TraceTypeDef(TypedDict):
    guardrailTrace: NotRequired[GuardrailTraceTypeDef]
    preProcessingTrace: NotRequired[PreProcessingTraceTypeDef]
    orchestrationTrace: NotRequired[OrchestrationTraceTypeDef]
    postProcessingTrace: NotRequired[PostProcessingTraceTypeDef]
    routingClassifierTrace: NotRequired[RoutingClassifierTraceTypeDef]
    failureTrace: NotRequired[FailureTraceTypeDef]
    customOrchestrationTrace: NotRequired[CustomOrchestrationTraceTypeDef]

class InlineSessionStateTypeDef(TypedDict):
    sessionAttributes: NotRequired[Mapping[str, str]]
    promptSessionAttributes: NotRequired[Mapping[str, str]]
    returnControlInvocationResults: NotRequired[Sequence[InvocationResultMemberUnionTypeDef]]
    invocationId: NotRequired[str]
    files: NotRequired[Sequence[InputFileTypeDef]]
    conversationHistory: NotRequired[ConversationHistoryTypeDef]

class SessionStateTypeDef(TypedDict):
    sessionAttributes: NotRequired[Mapping[str, str]]
    promptSessionAttributes: NotRequired[Mapping[str, str]]
    returnControlInvocationResults: NotRequired[Sequence[InvocationResultMemberUnionTypeDef]]
    invocationId: NotRequired[str]
    files: NotRequired[Sequence[InputFileTypeDef]]
    knowledgeBaseConfigurations: NotRequired[Sequence[KnowledgeBaseConfigurationTypeDef]]
    conversationHistory: NotRequired[ConversationHistoryTypeDef]

class InlineAgentTracePartTypeDef(TypedDict):
    sessionId: NotRequired[str]
    trace: NotRequired[TraceTypeDef]
    callerChain: NotRequired[List[CallerTypeDef]]
    eventTime: NotRequired[datetime]
    collaboratorName: NotRequired[str]

class TracePartTypeDef(TypedDict):
    sessionId: NotRequired[str]
    trace: NotRequired[TraceTypeDef]
    callerChain: NotRequired[List[CallerTypeDef]]
    eventTime: NotRequired[datetime]
    collaboratorName: NotRequired[str]
    agentId: NotRequired[str]
    agentAliasId: NotRequired[str]
    agentVersion: NotRequired[str]

class InvokeInlineAgentRequestTypeDef(TypedDict):
    foundationModel: str
    instruction: str
    sessionId: str
    customerEncryptionKeyArn: NotRequired[str]
    idleSessionTTLInSeconds: NotRequired[int]
    actionGroups: NotRequired[Sequence[AgentActionGroupTypeDef]]
    knowledgeBases: NotRequired[Sequence[KnowledgeBaseTypeDef]]
    guardrailConfiguration: NotRequired[GuardrailConfigurationWithArnTypeDef]
    promptOverrideConfiguration: NotRequired[PromptOverrideConfigurationTypeDef]
    agentCollaboration: NotRequired[AgentCollaborationType]
    collaboratorConfigurations: NotRequired[Sequence[CollaboratorConfigurationTypeDef]]
    agentName: NotRequired[str]
    endSession: NotRequired[bool]
    enableTrace: NotRequired[bool]
    inputText: NotRequired[str]
    streamingConfigurations: NotRequired[StreamingConfigurationsTypeDef]
    promptCreationConfigurations: NotRequired[PromptCreationConfigurationsTypeDef]
    inlineSessionState: NotRequired[InlineSessionStateTypeDef]
    collaborators: NotRequired[Sequence[CollaboratorTypeDef]]
    bedrockModelConfigurations: NotRequired[InlineBedrockModelConfigurationsTypeDef]
    orchestrationType: NotRequired[OrchestrationTypeType]
    customOrchestration: NotRequired[CustomOrchestrationTypeDef]

class InvokeAgentRequestTypeDef(TypedDict):
    agentId: str
    agentAliasId: str
    sessionId: str
    sessionState: NotRequired[SessionStateTypeDef]
    endSession: NotRequired[bool]
    enableTrace: NotRequired[bool]
    inputText: NotRequired[str]
    memoryId: NotRequired[str]
    bedrockModelConfigurations: NotRequired[BedrockModelConfigurationsTypeDef]
    streamingConfigurations: NotRequired[StreamingConfigurationsTypeDef]
    promptCreationConfigurations: NotRequired[PromptCreationConfigurationsTypeDef]
    sourceArn: NotRequired[str]

class InlineAgentResponseStreamTypeDef(TypedDict):
    chunk: NotRequired[InlineAgentPayloadPartTypeDef]
    trace: NotRequired[InlineAgentTracePartTypeDef]
    returnControl: NotRequired[InlineAgentReturnControlPayloadTypeDef]
    internalServerException: NotRequired[InternalServerExceptionTypeDef]
    validationException: NotRequired[ValidationExceptionTypeDef]
    resourceNotFoundException: NotRequired[ResourceNotFoundExceptionTypeDef]
    serviceQuotaExceededException: NotRequired[ServiceQuotaExceededExceptionTypeDef]
    throttlingException: NotRequired[ThrottlingExceptionTypeDef]
    accessDeniedException: NotRequired[AccessDeniedExceptionTypeDef]
    conflictException: NotRequired[ConflictExceptionTypeDef]
    dependencyFailedException: NotRequired[DependencyFailedExceptionTypeDef]
    badGatewayException: NotRequired[BadGatewayExceptionTypeDef]
    files: NotRequired[InlineAgentFilePartTypeDef]

class NodeTraceElementsTypeDef(TypedDict):
    agentTraces: NotRequired[List[TracePartTypeDef]]

class ResponseStreamTypeDef(TypedDict):
    chunk: NotRequired[PayloadPartTypeDef]
    trace: NotRequired[TracePartTypeDef]
    returnControl: NotRequired[ReturnControlPayloadTypeDef]
    internalServerException: NotRequired[InternalServerExceptionTypeDef]
    validationException: NotRequired[ValidationExceptionTypeDef]
    resourceNotFoundException: NotRequired[ResourceNotFoundExceptionTypeDef]
    serviceQuotaExceededException: NotRequired[ServiceQuotaExceededExceptionTypeDef]
    throttlingException: NotRequired[ThrottlingExceptionTypeDef]
    accessDeniedException: NotRequired[AccessDeniedExceptionTypeDef]
    conflictException: NotRequired[ConflictExceptionTypeDef]
    dependencyFailedException: NotRequired[DependencyFailedExceptionTypeDef]
    badGatewayException: NotRequired[BadGatewayExceptionTypeDef]
    modelNotReadyException: NotRequired[ModelNotReadyExceptionTypeDef]
    files: NotRequired[FilePartTypeDef]

class TraceElementsTypeDef(TypedDict):
    agentTraces: NotRequired[List[TracePartTypeDef]]

class InvokeInlineAgentResponseTypeDef(TypedDict):
    completion: EventStream[InlineAgentResponseStreamTypeDef]
    contentType: str
    sessionId: str
    ResponseMetadata: ResponseMetadataTypeDef

class NodeDependencyEventTypeDef(TypedDict):
    nodeName: str
    timestamp: datetime
    traceElements: NodeTraceElementsTypeDef

class InvokeAgentResponseTypeDef(TypedDict):
    completion: EventStream[ResponseStreamTypeDef]
    contentType: str
    sessionId: str
    memoryId: str
    ResponseMetadata: ResponseMetadataTypeDef

class FlowTraceDependencyEventTypeDef(TypedDict):
    nodeName: str
    timestamp: datetime
    traceElements: TraceElementsTypeDef

class FlowExecutionEventTypeDef(TypedDict):
    flowInputEvent: NotRequired[FlowExecutionInputEventTypeDef]
    flowOutputEvent: NotRequired[FlowExecutionOutputEventTypeDef]
    nodeInputEvent: NotRequired[NodeInputEventTypeDef]
    nodeOutputEvent: NotRequired[NodeOutputEventTypeDef]
    conditionResultEvent: NotRequired[ConditionResultEventTypeDef]
    nodeFailureEvent: NotRequired[NodeFailureEventTypeDef]
    flowFailureEvent: NotRequired[FlowFailureEventTypeDef]
    nodeActionEvent: NotRequired[NodeActionEventTypeDef]
    nodeDependencyEvent: NotRequired[NodeDependencyEventTypeDef]

class FlowTraceTypeDef(TypedDict):
    nodeInputTrace: NotRequired[FlowTraceNodeInputEventTypeDef]
    nodeOutputTrace: NotRequired[FlowTraceNodeOutputEventTypeDef]
    conditionNodeResultTrace: NotRequired[FlowTraceConditionNodeResultEventTypeDef]
    nodeActionTrace: NotRequired[FlowTraceNodeActionEventTypeDef]
    nodeDependencyTrace: NotRequired[FlowTraceDependencyEventTypeDef]

class ListFlowExecutionEventsResponseTypeDef(TypedDict):
    flowExecutionEvents: List[FlowExecutionEventTypeDef]
    ResponseMetadata: ResponseMetadataTypeDef
    nextToken: NotRequired[str]

class FlowTraceEventTypeDef(TypedDict):
    trace: FlowTraceTypeDef

class FlowResponseStreamTypeDef(TypedDict):
    flowOutputEvent: NotRequired[FlowOutputEventTypeDef]
    flowCompletionEvent: NotRequired[FlowCompletionEventTypeDef]
    flowTraceEvent: NotRequired[FlowTraceEventTypeDef]
    internalServerException: NotRequired[InternalServerExceptionTypeDef]
    validationException: NotRequired[ValidationExceptionTypeDef]
    resourceNotFoundException: NotRequired[ResourceNotFoundExceptionTypeDef]
    serviceQuotaExceededException: NotRequired[ServiceQuotaExceededExceptionTypeDef]
    throttlingException: NotRequired[ThrottlingExceptionTypeDef]
    accessDeniedException: NotRequired[AccessDeniedExceptionTypeDef]
    conflictException: NotRequired[ConflictExceptionTypeDef]
    dependencyFailedException: NotRequired[DependencyFailedExceptionTypeDef]
    badGatewayException: NotRequired[BadGatewayExceptionTypeDef]
    flowMultiTurnInputRequestEvent: NotRequired[FlowMultiTurnInputRequestEventTypeDef]

class InvokeFlowResponseTypeDef(TypedDict):
    responseStream: EventStream[FlowResponseStreamTypeDef]
    executionId: str
    ResponseMetadata: ResponseMetadataTypeDef
