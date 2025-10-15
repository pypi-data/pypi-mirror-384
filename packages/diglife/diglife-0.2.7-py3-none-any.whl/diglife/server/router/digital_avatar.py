
from fastapi import APIRouter
from diglife.core import DigitalAvatar
from diglife.models import BriefResponse, MemoryCards, AvatarXGRequests

import os


da = DigitalAvatar(model_name = os.getenv("llm_model_name"),
                              api_key = os.getenv("llm_api_key"))

router = APIRouter(tags=["digital_avatar"])

@router.post(
    "/brief", response_model=BriefResponse, description="数字分身介绍"
)
async def brief_server(request: MemoryCards):
    memory_cards = request.model_dump()["memory_cards"]
    result = await da.abrief(memory_cards=memory_cards)
    return BriefResponse(
        title=result.get("title"),
        content=result.get("content"),
        tags=result.get("tags")[:2],
    )


@router.post("/personality_extraction")
async def digital_avatar_personality_extraction(request: AvatarXGRequests):
    """数字分身性格提取"""
    memory_cards = request.model_dump()["memory_cards"]
    result = await da.personality_extraction(memory_cards=memory_cards,action = request.action,old_character = request.old_character)
    return {"text": result}


@router.post("/desensitization")
async def digital_avatar_desensitization(request: MemoryCards):
    """
    数字分身脱敏
    """
    memory_cards = request.model_dump()["memory_cards"]
    result = await da.desensitization(memory_cards=memory_cards)
    memory_cards = {"memory_cards": result}
    return MemoryCards(**memory_cards)
