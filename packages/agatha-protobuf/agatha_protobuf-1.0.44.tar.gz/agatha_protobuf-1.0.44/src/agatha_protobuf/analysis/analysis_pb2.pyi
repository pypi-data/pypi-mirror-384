from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import field_mask_pb2 as _field_mask_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CreateAnalysisRequest(_message.Message):
    __slots__ = ("user", "text", "context", "model")
    USER_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    user: str
    text: str
    context: str
    model: str
    def __init__(self, user: _Optional[str] = ..., text: _Optional[str] = ..., context: _Optional[str] = ..., model: _Optional[str] = ...) -> None: ...

class Analysis(_message.Message):
    __slots__ = ("id", "context", "created_at", "model", "response", "score", "text", "updated_at", "user")
    ID_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    id: str
    context: str
    created_at: str
    model: str
    response: str
    score: str
    text: str
    updated_at: str
    user: str
    def __init__(self, id: _Optional[str] = ..., context: _Optional[str] = ..., created_at: _Optional[str] = ..., model: _Optional[str] = ..., response: _Optional[str] = ..., score: _Optional[str] = ..., text: _Optional[str] = ..., updated_at: _Optional[str] = ..., user: _Optional[str] = ...) -> None: ...

class GetAnalysisRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class ListAnalysesRequest(_message.Message):
    __slots__ = ("model", "user", "page_size", "page_token", "score", "created_from", "created_to")
    MODEL_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    CREATED_FROM_FIELD_NUMBER: _ClassVar[int]
    CREATED_TO_FIELD_NUMBER: _ClassVar[int]
    model: str
    user: str
    page_size: int
    page_token: str
    score: int
    created_from: str
    created_to: str
    def __init__(self, model: _Optional[str] = ..., user: _Optional[str] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ..., score: _Optional[int] = ..., created_from: _Optional[str] = ..., created_to: _Optional[str] = ...) -> None: ...

class ListAnalysesResponse(_message.Message):
    __slots__ = ("analyses", "next_page_token")
    ANALYSES_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    analyses: _containers.RepeatedCompositeFieldContainer[Analysis]
    next_page_token: str
    def __init__(self, analyses: _Optional[_Iterable[_Union[Analysis, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class UpdateAnalysisRequest(_message.Message):
    __slots__ = ("analysis", "update_mask")
    ANALYSIS_FIELD_NUMBER: _ClassVar[int]
    UPDATE_MASK_FIELD_NUMBER: _ClassVar[int]
    analysis: Analysis
    update_mask: _field_mask_pb2.FieldMask
    def __init__(self, analysis: _Optional[_Union[Analysis, _Mapping]] = ..., update_mask: _Optional[_Union[_field_mask_pb2.FieldMask, _Mapping]] = ...) -> None: ...

class DeleteAnalysisRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class DeleteAnalysisResponse(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class Feedback(_message.Message):
    __slots__ = ("id", "analyze", "created_at", "feedback", "model", "response", "score", "text", "updated_at", "user")
    ID_FIELD_NUMBER: _ClassVar[int]
    ANALYZE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    FEEDBACK_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    id: str
    analyze: str
    created_at: str
    feedback: str
    model: str
    response: str
    score: str
    text: str
    updated_at: str
    user: str
    def __init__(self, id: _Optional[str] = ..., analyze: _Optional[str] = ..., created_at: _Optional[str] = ..., feedback: _Optional[str] = ..., model: _Optional[str] = ..., response: _Optional[str] = ..., score: _Optional[str] = ..., text: _Optional[str] = ..., updated_at: _Optional[str] = ..., user: _Optional[str] = ...) -> None: ...

class CreateFeedbackRequest(_message.Message):
    __slots__ = ("_id", "scale", "analyze", "feedback", "input", "build", "model")
    _ID_FIELD_NUMBER: _ClassVar[int]
    SCALE_FIELD_NUMBER: _ClassVar[int]
    ANALYZE_FIELD_NUMBER: _ClassVar[int]
    FEEDBACK_FIELD_NUMBER: _ClassVar[int]
    INPUT_FIELD_NUMBER: _ClassVar[int]
    BUILD_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    _id: str
    scale: str
    analyze: str
    feedback: str
    input: str
    build: str
    model: str
    def __init__(self, _id: _Optional[str] = ..., scale: _Optional[str] = ..., analyze: _Optional[str] = ..., feedback: _Optional[str] = ..., input: _Optional[str] = ..., build: _Optional[str] = ..., model: _Optional[str] = ...) -> None: ...

class GetFeedbackRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class ListFeedbacksRequest(_message.Message):
    __slots__ = ("analyze", "page_size", "page_token")
    ANALYZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    analyze: str
    page_size: int
    page_token: str
    def __init__(self, analyze: _Optional[str] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ...) -> None: ...

class ListFeedbacksResponse(_message.Message):
    __slots__ = ("feedbacks", "next_page_token")
    FEEDBACKS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    feedbacks: _containers.RepeatedCompositeFieldContainer[Feedback]
    next_page_token: str
    def __init__(self, feedbacks: _Optional[_Iterable[_Union[Feedback, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class UpdateFeedbackRequest(_message.Message):
    __slots__ = ("feedback", "update_mask")
    FEEDBACK_FIELD_NUMBER: _ClassVar[int]
    UPDATE_MASK_FIELD_NUMBER: _ClassVar[int]
    feedback: Feedback
    update_mask: _field_mask_pb2.FieldMask
    def __init__(self, feedback: _Optional[_Union[Feedback, _Mapping]] = ..., update_mask: _Optional[_Union[_field_mask_pb2.FieldMask, _Mapping]] = ...) -> None: ...

class DeleteFeedbackRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class DeleteFeedbackResponse(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class CreateAnalysisFromLLMSRequest(_message.Message):
    __slots__ = ("user", "text", "context", "model")
    USER_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    user: str
    text: str
    context: str
    model: str
    def __init__(self, user: _Optional[str] = ..., text: _Optional[str] = ..., context: _Optional[str] = ..., model: _Optional[str] = ...) -> None: ...

class CreateAnalysisFromLLMSResponse(_message.Message):
    __slots__ = ("llms",)
    LLMS_FIELD_NUMBER: _ClassVar[int]
    llms: _containers.RepeatedCompositeFieldContainer[LLM]
    def __init__(self, llms: _Optional[_Iterable[_Union[LLM, _Mapping]]] = ...) -> None: ...

class GetAnalysisFromLLMSRequest(_message.Message):
    __slots__ = ("id", "user")
    ID_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    id: str
    user: str
    def __init__(self, id: _Optional[str] = ..., user: _Optional[str] = ...) -> None: ...

class GetAnalysisFromLLMSResponse(_message.Message):
    __slots__ = ("llms",)
    LLMS_FIELD_NUMBER: _ClassVar[int]
    llms: _containers.RepeatedCompositeFieldContainer[LLM]
    def __init__(self, llms: _Optional[_Iterable[_Union[LLM, _Mapping]]] = ...) -> None: ...

class LLM(_message.Message):
    __slots__ = ("name", "analysis")
    NAME_FIELD_NUMBER: _ClassVar[int]
    ANALYSIS_FIELD_NUMBER: _ClassVar[int]
    name: str
    analysis: Analysis
    def __init__(self, name: _Optional[str] = ..., analysis: _Optional[_Union[Analysis, _Mapping]] = ...) -> None: ...

class CreateMigrationResponse(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class CreateMoodHistoryRequest(_message.Message):
    __slots__ = ("user", "mood", "note")
    USER_FIELD_NUMBER: _ClassVar[int]
    MOOD_FIELD_NUMBER: _ClassVar[int]
    NOTE_FIELD_NUMBER: _ClassVar[int]
    user: str
    mood: str
    note: str
    def __init__(self, user: _Optional[str] = ..., mood: _Optional[str] = ..., note: _Optional[str] = ...) -> None: ...

class MoodHistory(_message.Message):
    __slots__ = ("id", "user", "mood", "note", "created_at", "updated_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    MOOD_FIELD_NUMBER: _ClassVar[int]
    NOTE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    user: str
    mood: str
    note: str
    created_at: str
    updated_at: str
    def __init__(self, id: _Optional[str] = ..., user: _Optional[str] = ..., mood: _Optional[str] = ..., note: _Optional[str] = ..., created_at: _Optional[str] = ..., updated_at: _Optional[str] = ...) -> None: ...

class ListMoodHistoryRequest(_message.Message):
    __slots__ = ("user", "page_size", "page_token", "mood")
    USER_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    MOOD_FIELD_NUMBER: _ClassVar[int]
    user: str
    page_size: int
    page_token: str
    mood: str
    def __init__(self, user: _Optional[str] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ..., mood: _Optional[str] = ...) -> None: ...

class ListMoodHistoryResponse(_message.Message):
    __slots__ = ("mood_histories", "next_page_token")
    MOOD_HISTORIES_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    mood_histories: _containers.RepeatedCompositeFieldContainer[MoodHistory]
    next_page_token: str
    def __init__(self, mood_histories: _Optional[_Iterable[_Union[MoodHistory, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class ListMoodsRequest(_message.Message):
    __slots__ = ("category",)
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    category: str
    def __init__(self, category: _Optional[str] = ...) -> None: ...

class Tip(_message.Message):
    __slots__ = ("description", "link", "title")
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    LINK_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    description: str
    link: str
    title: str
    def __init__(self, description: _Optional[str] = ..., link: _Optional[str] = ..., title: _Optional[str] = ...) -> None: ...

class Asset(_message.Message):
    __slots__ = ("type", "url")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    type: str
    url: str
    def __init__(self, type: _Optional[str] = ..., url: _Optional[str] = ...) -> None: ...

class Mood(_message.Message):
    __slots__ = ("id", "color", "cover", "description", "identifier", "label", "category", "order", "text_color", "tips", "video")
    ID_FIELD_NUMBER: _ClassVar[int]
    COLOR_FIELD_NUMBER: _ClassVar[int]
    COVER_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    TEXT_COLOR_FIELD_NUMBER: _ClassVar[int]
    TIPS_FIELD_NUMBER: _ClassVar[int]
    VIDEO_FIELD_NUMBER: _ClassVar[int]
    id: str
    color: str
    cover: Asset
    description: str
    identifier: str
    label: str
    category: MoodCategory
    order: int
    text_color: str
    tips: _containers.RepeatedCompositeFieldContainer[Tip]
    video: Asset
    def __init__(self, id: _Optional[str] = ..., color: _Optional[str] = ..., cover: _Optional[_Union[Asset, _Mapping]] = ..., description: _Optional[str] = ..., identifier: _Optional[str] = ..., label: _Optional[str] = ..., category: _Optional[_Union[MoodCategory, _Mapping]] = ..., order: _Optional[int] = ..., text_color: _Optional[str] = ..., tips: _Optional[_Iterable[_Union[Tip, _Mapping]]] = ..., video: _Optional[_Union[Asset, _Mapping]] = ...) -> None: ...

class MoodCategory(_message.Message):
    __slots__ = ("id", "label", "identifier", "order", "platform")
    ID_FIELD_NUMBER: _ClassVar[int]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    PLATFORM_FIELD_NUMBER: _ClassVar[int]
    id: str
    label: str
    identifier: str
    order: int
    platform: str
    def __init__(self, id: _Optional[str] = ..., label: _Optional[str] = ..., identifier: _Optional[str] = ..., order: _Optional[int] = ..., platform: _Optional[str] = ...) -> None: ...

class ListMoodsResponse(_message.Message):
    __slots__ = ("moods",)
    MOODS_FIELD_NUMBER: _ClassVar[int]
    moods: _containers.RepeatedCompositeFieldContainer[Mood]
    def __init__(self, moods: _Optional[_Iterable[_Union[Mood, _Mapping]]] = ...) -> None: ...

class CreateMoodRequest(_message.Message):
    __slots__ = ("color", "cover", "description", "identifier", "label", "category", "order", "text_color", "tips", "video")
    COLOR_FIELD_NUMBER: _ClassVar[int]
    COVER_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    TEXT_COLOR_FIELD_NUMBER: _ClassVar[int]
    TIPS_FIELD_NUMBER: _ClassVar[int]
    VIDEO_FIELD_NUMBER: _ClassVar[int]
    color: str
    cover: Asset
    description: str
    identifier: str
    label: str
    category: str
    order: int
    text_color: str
    tips: _containers.RepeatedCompositeFieldContainer[Tip]
    video: Asset
    def __init__(self, color: _Optional[str] = ..., cover: _Optional[_Union[Asset, _Mapping]] = ..., description: _Optional[str] = ..., identifier: _Optional[str] = ..., label: _Optional[str] = ..., category: _Optional[str] = ..., order: _Optional[int] = ..., text_color: _Optional[str] = ..., tips: _Optional[_Iterable[_Union[Tip, _Mapping]]] = ..., video: _Optional[_Union[Asset, _Mapping]] = ...) -> None: ...

class UpdateMoodRequest(_message.Message):
    __slots__ = ("id", "color", "cover", "description", "identifier", "label", "category", "order", "text_color", "tips", "video")
    ID_FIELD_NUMBER: _ClassVar[int]
    COLOR_FIELD_NUMBER: _ClassVar[int]
    COVER_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    ORDER_FIELD_NUMBER: _ClassVar[int]
    TEXT_COLOR_FIELD_NUMBER: _ClassVar[int]
    TIPS_FIELD_NUMBER: _ClassVar[int]
    VIDEO_FIELD_NUMBER: _ClassVar[int]
    id: str
    color: str
    cover: Asset
    description: str
    identifier: str
    label: str
    category: str
    order: int
    text_color: str
    tips: _containers.RepeatedCompositeFieldContainer[Tip]
    video: Asset
    def __init__(self, id: _Optional[str] = ..., color: _Optional[str] = ..., cover: _Optional[_Union[Asset, _Mapping]] = ..., description: _Optional[str] = ..., identifier: _Optional[str] = ..., label: _Optional[str] = ..., category: _Optional[str] = ..., order: _Optional[int] = ..., text_color: _Optional[str] = ..., tips: _Optional[_Iterable[_Union[Tip, _Mapping]]] = ..., video: _Optional[_Union[Asset, _Mapping]] = ...) -> None: ...

class GetMoodRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class DeleteMoodRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class DeleteMoodResponse(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...
