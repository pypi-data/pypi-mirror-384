
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from diglife.embedding_pool import EmbeddingPool
from diglife.core import BiographyGenerate
from diglife.models import BiographyRequest, BiographyResult
from diglife import logger
import asyncio
import httpx
import uuid
import os


router = APIRouter(tags=["biography"])

user_callback_url = os.getenv("user_callback_url")

ep = EmbeddingPool()
bg = BiographyGenerate(model_name = os.getenv("llm_model_name") ,
                              api_key = os.getenv("llm_api_key"))



task_store: Dict[str, Dict[str, Any]] = {}


async def aget_(url = ""):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()  # 如果状态码是 4xx 或 5xx，会抛出 HTTPStatusError 异常
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Body: {response.json()}") # 假设返回的是 JSON
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"An error occurred while requesting {e.request.url!r}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    return None


async def _generate_biography(task_id: str, request_data: BiographyRequest):
    """
    模拟一个耗时的传记生成过程。
    在真实场景中，这里会调用LLM或其他复杂的生成逻辑。
    """
    memory_cards = request_data.model_dump()["memory_cards"]
    try:
        task_store[task_id]["status"] = "PROCESSING"
        task_store[task_id]["progress"] = 0.1
        logger.info(f"Task {task_id}: Starting generation ")

        # 素材整理
        material = await bg.amaterial_generate(
            vitae=request_data.vitae, memory_cards=memory_cards
        )
        task_store[task_id]["progress"] = 0.2
        task_store[task_id]["material"] = material
        # 生成大纲
        outline = await bg.aoutline_generate(material)

        task_store[task_id]["progress"] = 0.3

        task_store[task_id]["biography_title"] = "个人传记"
        task_store[task_id]["outline"] = outline

        # 生成传记简介
        brief = await bg.agener_biography_brief(outline)
        task_store[task_id]["biography_brief"] = brief

        task_store[task_id]["progress"] = 0.5
        biography_json = {}
        biography_name = []
        biography_place = []

        tasks = []
        for part, chapters in outline.items():
            for chapter in chapters:
                logger.info(
                    f"Creating task for chapter: {chapter.get('chapter_number')} {chapter.get('title')}"
                )
                tasks.append(
                    bg.awrite_chapter(
                        chapter,
                        master=request_data.user_name,
                        material=material,
                        outline=outline,
                    )
                )
        results = await asyncio.gather(*tasks, return_exceptions=False)

        for part, chapters in outline.items():
            biography_json[part] = []
            for chapter in chapters:
                chapter_number = chapter.get("chapter_number")
                for x in results:
                    if x.get("chapter_number") == chapter_number:
                        biography_json[part].append(x.get("article"))
                        biography_name += x.get("chapter_name")
                        biography_place += x.get("chapter_place")

        assert isinstance(biography_json, dict)
        assert isinstance(biography_name, list)
        assert isinstance(biography_place, list)

        biography_name = list(set(biography_name))
        biography_place = list(set(biography_place))
        task_store[task_id]["biography_json"] = biography_json
        task_store[task_id]["biography_name"] = biography_name
        task_store[task_id]["biography_place"] = biography_place
        task_store[task_id]["status"] = "COMPLETED"
        task_store[task_id]["progress"] = 1.0


        biography_callback_url_success = user_callback_url + f'/api/inner/notifyBiographyStatus?generateTaskId={task_id}&status=1'
        await aget_(url = biography_callback_url_success)


    except Exception as e:
        task_store[task_id]["status"] = "FAILED"
        task_store[task_id]["error_message"] = str(e)
        task_store[task_id]["progress"] = 1.0
        biography_callback_url_failed = user_callback_url + f'/api/inner/notifyBiographyStatus?generateTaskId={task_id}&status=0'
        await aget_(url = biography_callback_url_failed)



@router.post(
    "/generate_biography", response_model=BiographyResult, summary="提交传记生成请求"
)
async def generate_biography(request: BiographyRequest):
    """
    提交一个传记生成请求。

    此接口会立即返回一个任务ID，客户端可以使用此ID查询生成进度和结果。
    实际的生成过程会在后台异步执行。
    """
    task_id = str(uuid.uuid4())
    task_store[task_id] = {
        "task_id": task_id,
        "status": "PENDING",
        "biography_title": None,
        "biography_brief": None,
        "biography_json": None,
        "biography_name": None,
        "biography_place": None,
        "error_message": None,
        "progress": 0.0,
        "request_data": request.model_dump(),  # 存储请求数据以备后续使用
    }

    asyncio.create_task(_generate_biography(task_id, request))

    return BiographyResult(task_id=task_id, status="PENDING", progress=0.0)


@router.get(
    "/get_biography_result/{task_id}",
    response_model=BiographyResult,
    summary="查询传记生成结果",
)
async def get_biography_result(task_id: str):
    """
    根据任务ID查询传记生成任务的状态和结果。
    """
    task_info = task_store.get(task_id)
    if not task_info:
        raise HTTPException(
            status_code=404, detail=f"Task with ID '{task_id}' not found."
        )

    return BiographyResult(
        task_id=task_info["task_id"],
        status=task_info["status"],
        biography_title=task_info.get("biography_title", ""),
        biography_brief=task_info.get("biography_brief", ""),
        biography_json=task_info.get("biography_json", {}),
        biography_name=task_info.get("biography_name", []),
        biography_place=task_info.get("biography_place", []),
        error_message=task_info.get("error_message"),
        progress=task_info.get("progress", 0.0),
    )


# 免费版传记优化
@router.post("/generate_biography_free", summary="提交传记生成请求")
async def generate_biography(request: BiographyRequest):
    """
    提交一个传记生成请求。

    此接口会立即返回一个任务ID，客户端可以使用此ID查询生成进度和结果。
    实际的生成过程会在后台异步执行。
    """
    memory_cards = request.model_dump()["memory_cards"]
    result = await bg.agenerate_biography_free(
        user_name=request.user_name,
        memory_cards=memory_cards,
        vitae=request.vitae,
    )

    return {"title": result.get("title"), "content": result.get("content")}
