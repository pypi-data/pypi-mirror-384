
from typing import Dict, Any

from diglife import logger
import os
import httpx
from .embedding_pool import EmbeddingPool


recommended_biographies_cache_max_leng = int(os.getenv("recommended_biographies_cache_max_leng",2))
recommended_cache_max_leng = int(os.getenv("recommended_cache_max_leng",2))
recommended_top_k = 10
user_callback_url = os.getenv("user_callback_url")

async def aget_(url = ""):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()  # 如果状态码是 4xx 或 5xx，会抛出 HTTPStatusError 异常
            
            assert response.status_code == 200
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"An error occurred while requesting {e.request.url!r}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    return None



class Recommend():
    def __init__(self):
        self.ep = EmbeddingPool()
        self.recommended_biographies_cache: Dict[str, Dict[str, Any]] = {}
        self.recommended_figure_cache: Dict[str, Dict[str, Any]] = {}



    def update(self,text, id, type):
        self.ep.update(text=text, id=id, type=type)


    def delete(self,id):
        self.ep.delete(id)


    async def recommended_biographies_and_cards(self,user_id):
        user_profile_id_to_fetch = user_id
        memory_info = await aget_(url = user_callback_url + f"/api/inner/getMemoryCards?userProfileId={user_profile_id_to_fetch}")

        user_brief = '\n'.join([i.get('content') for i in memory_info['data']["memoryCards"][:4]])
        user_brief = user_brief or "这是一个简单的记忆卡片"

        result = self.ep.search_bac(query=user_brief) # 假如top_k = 1000
        print(len(result),'result')
        # 是否记录了该用户, 如果没记录, 创建空列表
        if self.recommended_biographies_cache.get(user_id):
            clear_result = [i for i in result if i.get("id") not in self.recommended_biographies_cache.get(user_id)]
        else:
            self.recommended_biographies_cache[user_id] = []
            clear_result = result
        clear_result = clear_result[:recommended_top_k]
        # 加入缓存 去重
        self.recommended_biographies_cache[user_id] += [i.get("id") for i in clear_result]
        self.recommended_biographies_cache[user_id] = list(
            set(self.recommended_biographies_cache[user_id])
        )
        print(clear_result,'clear_result')
        print(self.recommended_biographies_cache,'self.recommended_biographies_cache')
        # self.recommended_biographies_cache < len(result)
        print(len(self.recommended_biographies_cache[user_id]),'len(self.recommended_biographies_cache[user_id])')
        if len(self.recommended_biographies_cache[user_id]) > recommended_biographies_cache_max_leng:
            self.recommended_biographies_cache[user_id] = []
        return clear_result


    async def recommended_figure_person(self,user_id):
        user_profile_id_to_fetch = user_id
        avatar_info = await aget_(url = user_callback_url + f"/api/inner/getAvatarDesc?userProfileId={user_profile_id_to_fetch}")
        if avatar_info["code"] == 200:
            user_brief = avatar_info["data"].get("avatarDesc")
        else:
            user_brief = "这是一个简单的人"

        result = self.ep.search_figure_person(query=user_brief)  # 100+

        if self.recommended_figure_cache.get(user_id):
            clear_result = [i for i in result if i.get("id") not in self.recommended_figure_cache.get(user_id)]
        else:
            self.recommended_figure_cache[user_id] = []
            clear_result = result

        self.recommended_figure_cache[user_id] += [i.get("id") for i in result]
        self.recommended_figure_cache[user_id] = list(
            set(self.recommended_figure_cache[user_id])
        )
        if len(self.recommended_figure_cache[user_id]) > recommended_cache_max_leng:
            self.recommended_figure_cache[user_id] = []
        return clear_result


