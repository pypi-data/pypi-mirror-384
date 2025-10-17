# server
# 推荐算法

from ..models import UpdateItem, DeleteResponse, DeleteRequest, QueryItem
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from diglife.embedding_pool import EmbeddingPool
from diglife.log import Log
import os
import httpx

from dotenv import load_dotenv, find_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path, override=True)



router = APIRouter(tags=["recommended"])

logger = Log.logger

recommended_biographies_cache_max_leng = os.getenv("recommended_biographies_cache_max_leng",2) #config.get("recommended_biographies_cache_max_leng", 2)
recommended_biographies_cache_max_leng = int(recommended_biographies_cache_max_leng)
recommended_cache_max_leng = os.getenv("recommended_cache_max_leng",2) #config.get("recommended_cache_max_leng", 2)
recommended_cache_max_leng = int(recommended_cache_max_leng)
user_server_base_url = "http://182.92.107.224:7000"

ep = EmbeddingPool()
recommended_biographies_cache: Dict[str, Dict[str, Any]] = {}
recommended_figure_cache: Dict[str, Dict[str, Any]] = {}

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
    # TODO 需要一个反馈状态
    try:
        if item.type in [0, 1, 2]:  # 上传的是卡片
            ep.update(text=item.text, id=item.id, type=item.type)
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

    logger.info("running delete_server")

    # TODO 需要一个反馈状态
    result = ep.delete(id=request.id)  # 包裹的内核函数

    ########
    return DeleteResponse(
        status="success",
    )




# async def aget_content_by_id(url = ""):
#     # url = url.format(user_profile_id = user_profile_id)
#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.get(url)
#             response.raise_for_status()  # 如果状态码是 4xx 或 5xx，会抛出 HTTPStatusError 异常
            
#             print(f"Status Code: {response.status_code}")
#             print(f"Response Body: {response.json()}") # 假设返回的是 JSON
#             return response.json()
#         except httpx.HTTPStatusError as e:
#             print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
#         except httpx.RequestError as e:
#             print(f"An error occurred while requesting {e.request.url!r}: {e}")
#         except Exception as e:
#             print(f"An unexpected error occurred: {e}")
#     return None

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

@router.post(
    "/search_biographies_and_cards",
    summary="搜索传记和记忆卡片",
    description="搜索传记和记忆卡片",
    response_description="搜索结果列表。",
)
async def recommended_biographies_and_cards(query_item: QueryItem):
    """
        # result = [
        #     {
        #         "id": "1916693308020916225",  # 传记ID
        #         "type": 1,
        #         "order": 0,
        #     },
        #     {
        #         "id": "1962459564012359682",  # 卡片ID
        #         "type": 0,
        #         "order": 1,
        #     },
        #     {
        #         "id": "1916389315373727745",  # 传记ID
        #         "type": 1,
        #         "order": 2,
        #     },
        # ]

        {
        "text":"这是一个传记001",
        "id":"1916693308020916225",
        "type":1
    }
    {
        "text":"这是一个传记002",
        "id":"1916389315373727745",
        "type":1
    }
    {
        "text":"这是一个卡片001",
        "id":"1962459564012359682",
        "type":0
    }
    """
    try:
        # TODO 需要一个通过id 获取对应内容的接口
        # TODO 调用id 获得对应的用户简介 query_item.user_id


        user_profile_id_to_fetch = query_item.user_id
        # memory_info = await aget_content_by_id(user_profile_id_to_fetch,url = user_server_base_url + "/api/inner/getMemoryCards?userProfileId={user_profile_id}")
        memory_info = await aget_(url = user_server_base_url + f"/api/inner/getMemoryCards?userProfileId={user_profile_id_to_fetch}")
        # memory_info = await get_memorycards_by_id(user_profile_id_to_fetch)
        user_brief = '\n'.join([i.get('content') for i in memory_info['data']["memoryCards"][:4]])


        result = ep.search_bac(query=user_brief)

        if recommended_biographies_cache.get(query_item.user_id):
            clear_result = [
                i
                for i in result
                if i.get("id")
                not in recommended_biographies_cache.get(query_item.user_id)
            ]
        else:
            recommended_biographies_cache[query_item.user_id] = []
            clear_result = result

        recommended_biographies_cache[query_item.user_id] += [
            i.get("id") for i in result
        ]
        recommended_biographies_cache[query_item.user_id] = list(
            set(recommended_biographies_cache[query_item.user_id])
        )
        if (
            len(recommended_biographies_cache[query_item.user_id])
            > recommended_biographies_cache_max_leng
        ):
            recommended_biographies_cache[query_item.user_id] = []

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
    """

    """
    try:

        user_profile_id_to_fetch = query_item.user_id
        # avatar_info = await aget_avatar_desc_by_id(user_profile_id_to_fetch)
        # avatar_info = await aget_content_by_id(user_profile_id_to_fetch,url = user_server_base_url + "/api/inner/getAvatarDesc?userProfileId={user_profile_id}")
        avatar_info = await aget_(url = user_server_base_url + f"/api/inner/getAvatarDesc?userProfileId={user_profile_id_to_fetch}")
        print(avatar_info,'avatar_info')
        if avatar_info["code"] == 200:
            user_brief = avatar_info["data"].get("avatarDesc")
        else:
            user_brief = "这是一个简单的人"

        result = ep.search_figure_person(query=user_brief)  # 100+

        if recommended_figure_cache.get(query_item.user_id):
            # 不需要创建
            clear_result = [
                i
                for i in result
                if i.get("id") not in recommended_figure_cache.get(query_item.user_id)
            ]
        else:
            recommended_figure_cache[query_item.user_id] = []
            clear_result = result

        recommended_figure_cache[query_item.user_id] += [i.get("id") for i in result]
        recommended_figure_cache[query_item.user_id] = list(
            set(recommended_figure_cache[query_item.user_id])
        )
        if (
            len(recommended_figure_cache[query_item.user_id])
            > recommended_cache_max_leng
        ):
            recommended_figure_cache[query_item.user_id] = []
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

