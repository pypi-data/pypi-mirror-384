# server
# 推荐算法

from diglife.models import UpdateItem, DeleteResponse, DeleteRequest, QueryItem
from fastapi import APIRouter, Depends, HTTPException, status
from diglife.core.recommended import Recommend
from diglife import logger

router = APIRouter(tags=["recommended"])

rep = Recommend()

@router.post(
    "/update",  # 推荐使用POST请求进行数据更新
    summary="更新或添加文本嵌入",
    description="将给定的文本内容与一个ID关联并更新到Embedding池中。",
    response_description="表示操作是否成功。",
)
def recommended_update(item: UpdateItem):
    """记忆卡片是0  传记是1
    记忆卡片是0
    记忆卡片上传的是记忆卡片的内容 str
    记忆卡片id
    0

    传记是1
    上传的是传记简介  str
    传记id
    1

    数字分身是2
    上传数字分身简介和性格描述  str
    数字分身id
    2
    """
    try:
        if item.type in [0, 1, 2]:  # 上传的是卡片
            rep.update(text=item.text, id=item.id, type=item.type)
        else:
            logger.error(f"Error updating EmbeddingPool for ID '{item.id}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update embedding for ID '{item.id}': {e}",
            )

        return {"status": "success", "message": f"ID '{item.id}' updated successfully."}

    except ValueError as e:  # 假设EmbeddingPool.update可能抛出ValueError
        logger.warning(f"Validation error during update: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating EmbeddingPool for ID '{item.id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update embedding for ID '{item.id}': {e}",
        )


@router.post("/delete", response_model=DeleteResponse, description="delete")
async def delete_server(request: DeleteRequest):
    rep.delete(id=request.id)  # 包裹的内核函数
    ########
    return DeleteResponse(
        status="success",
    )

@router.post(
    "/search_biographies_and_cards",
    summary="搜索传记和记忆卡片",
    description="搜索传记和记忆卡片",
    response_description="搜索结果列表。",
)
async def recommended_biographies_and_cards(query_item: QueryItem):
    try:
        clear_result = await rep.recommended_biographies_and_cards(user_id = query_item.user_id,
             )

        return {
            "status": "success",
            "result": clear_result,
            "query": query_item.user_id,
        }

    except Exception as e:
        logger.error(
            f"Error searching EmbeddingPool for query '{query_item.user_id}': {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform search: {e}",
        )

@router.post(
    "/search_figure_person",
    description="搜索数字分身的",
)
async def recommended_figure_person(query_item: QueryItem):
    try:

        clear_result = await rep.recommended_figure_person(user_id = query_item.user_id,
             )
        return {
            "status": "success",
            "result": clear_result,
            "query": query_item.user_id,
        }

    except Exception as e:
        logger.error(
            f"Error searching EmbeddingPool for query '{query_item.user_id}': {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform search: {e}",
        )

