
# server
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, model_validator


# 记忆合并
class MemoryCardsRequest(BaseModel):
    memory_cards: list[str] = Field(..., description="记忆卡片列表")

class MemoryCard(BaseModel):
    title: str
    content: str
    time: str


class MemoryCardScore(BaseModel):
    score: int
    reason: str

class MemoryCards(BaseModel):
    memory_cards: list[MemoryCard] = Field(..., description="记忆卡片列表")


class MemoryCardGenerate(BaseModel):
    title: str
    content: str
    time: str
    score: int
    tag: str
    topic: int


class MemoryCardsGenerate(BaseModel):
    memory_cards: list[MemoryCardGenerate] = Field(..., description="记忆卡片列表")




class BiographyRequest(BaseModel):
    """
    请求传记生成的数据模型。
    """

    user_name: str = Field(None, description="用户名字")
    vitae: str = Field(None, description="用户简历")
    memory_cards: list[MemoryCard] = Field(..., description="记忆卡片列表")
    # 可以在这里添加更多用于生成传记的输入字段


class UseroverviewRequests(BaseModel):
    action: str
    old_overview: str
    memory_cards: list[MemoryCard]


class AvatarXGRequests(BaseModel):
    action: str
    old_character: str
    memory_cards: list[MemoryCard]


class ChatHistoryOrText(BaseModel):
    text: str = Field(..., description="聊天内容或者文本内容")




class UserRelationshipExtractionRequest(BaseModel):
    text: str


class BriefResponse(BaseModel):
    title: str
    content: str
    tags: list[str]


class DeleteRequest(BaseModel):
    id: str


class DeleteResponse(BaseModel):
    status: str = "success"  # 假设返回一个状态表示删除成功


class UpdateItem(BaseModel):
    text: str = Field(
        ..., min_length=1, max_length=2000, description="要更新的文本内容。"
    )
    id: str = Field(
        ..., min_length=1, max_length=100, description="与文本关联的唯一ID。"
    )
    type: int = Field(..., description="上传的类型")


class QueryItem(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=500, description="user_id")


class BiographyResult(BaseModel):
    """
    传记生成结果的数据模型。
    """

    task_id: str = Field(..., description="任务的唯一标识符。")
    status: str = Field(
        ...,
        description="任务的当前状态 (e.g., 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED').",
    )
    biography_title: Optional[str] = Field(None, description="传记标题")

    biography_brief: Optional[str] = Field(
        None, description="生成的传记简介，仅在状态为 'COMPLETED' 时存在。"
    )
    biography_json: dict | None = Field(
        None, description="生成的传记文本，仅在状态为 'COMPLETED' 时存在。"
    )
    biography_name: list[str] | None = Field(
        None, description="生成的传记文本中的人名，仅在状态为 'COMPLETED' 时存在。"
    )
    biography_place: list[str] | None = Field(
        None, description="生成的传记文本中的地名，仅在状态为 'COMPLETED' 时存在。"
    )
    error_message: Optional[str] = Field(
        None, description="错误信息，仅在状态为 'FAILED' 时存在。"
    )
    progress: float = Field(
        0.0, ge=0.0, le=1.0, description="任务处理进度，0.0到1.0之间。"
    )



class LifeTopicScoreRequest(BaseModel):
    S_list: List[int] = Field(..., description="List of scores, each between 1 and 10.")
    K: float = Field(0.8, description="Weighting factor K.")
    total_score: int = Field(0, description="Initial total score.")
    epsilon: float = Field(0.001, description="Epsilon value for calculation.")

    @model_validator(mode="after")
    def validate_s_list(self):
        if not all(0 <= x <= 10 for x in self.S_list):
            raise ValueError(
                "All elements in 'S_list' must be integers between 1 and 10 (inclusive)."
            )
        return self


class ScoreRequest(BaseModel):
    S_list: List[float] = Field(
        ...,
        description="List of string representations of scores, each between 1 and 10.",
    )
    K: float = Field(0.3, description="Coefficient K for score calculation.")
    total_score: int = Field(0, description="Total score to be added.")
    epsilon: float = Field(0.0001, description="Epsilon value for score calculation.")

    @model_validator(mode="after")
    def check_s_list_values(self):
        for s_val in self.S_list:
            try:
                int_s_val = float(s_val)
                if not (0 <= int_s_val <= 100):
                    raise ValueError(
                        "Each element in 'S_list' must be an integer between 1 and 10."
                    )
            except ValueError:
                raise ValueError(
                    "Each element in 'S_list' must be a valid integer string."
                )
        return self

