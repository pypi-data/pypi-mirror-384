#
from diglife.utils import extract_json, extract_article, super_log
from prompt_writing_assistant.prompt_helper import Intel,IntellectType
from llmada.core import BianXieAdapter
from diglife.models import MemoryCard, MemoryCardScore, MemoryCards
import math
import asyncio
import json

inters = Intel(model_name = "doubao-1-5-pro-256k-250115")
table_name="prompts_table"

from .utils import memoryCards2str
from diglife import logger


###

class DigitalAvatar:
    def __init__(self):
        pass
    async def desensitization(self, memory_cards: list[str]) -> list[str]:
        """
        数字分身脱敏 0100
        """
        output_format = """
输出格式
```article 
输出内容 
```
"""
        tasks = []
        for memory_card in memory_cards:
            tasks.append(inters.aintellect_remove(input_data=memory_card.get("content"),
                                 output_format=output_format,
                                 prompt_id="0100",
                                 inference_save_case=False,
                                 ))
        results = await asyncio.gather(*tasks, return_exceptions=False)
    
        for i, memory_card in enumerate(memory_cards):
            memory_card["content"] = extract_article(results[i])

        return memory_cards
    
    async def personality_extraction(self, memory_cards: list[dict],action:str,old_character:str) -> str:
        """
        数字分身性格提取 0099
        """
        output_format = """
输出格式
```article 
输出内容 
```
"""
        memoryCards_str, _ = memoryCards2str(memory_cards)
        input_data = "\n操作方案:\n" + action + "\n旧人物性格:\n" + old_character +"\n记忆卡片:\n" +  memoryCards_str
        
        result = await inters.aintellect_remove(
                                    input_data= input_data,
                                    output_format=output_format,
                                    prompt_id ="0099",
                                    version = None,
                                    inference_save_case=False
                                    )

        return extract_article(result)

    
    async def abrief(self, memory_cards: list[dict]) -> dict:
        """
        数字分身介绍 0098
        """
        # TOOD 增加字数限制, tag标签 两个
        memoryCards_str, _ = memoryCards2str(memory_cards)
        output_format = """
输出格式
```json
{
  "title":"标题",
  "content":"内容",
  "tags":["标签1","标签2"]
}
```
"""
        result = await inters.aintellect_remove(input_data="聊天历史:\n" + memoryCards_str,
                                         output_format=output_format,
                                         prompt_id ="0098",
                                         version = None,
                                         inference_save_case=False)

        dict_ = json.loads(extract_json(result))


        
        return dict_

    async def auser_relationship_extraction(self,text: str) -> dict:
        """
        用户关系提取 0097
        """

        output_format = """
输出格式
```json
{
  "角色": {
    "relationship": "关系",
    "profession": "职业",
    "birthday": 出生日期
  },
  ...
}
```
"""
        result = await inters.aintellect_remove(input_data="聊天历史" + text,
                                         output_format=output_format,
                                         prompt_id ="0097",
                                         version = None,
                                         inference_save_case=False)
        
        dict_ = json.loads(extract_json(result))        
        return dict_


    async def auser_overview(self,action: str,old_overview: str, memory_cards: list[dict],
                             version = None,
                             ) -> str:
        """
        用户概述 0096
        """
        output_format = """"""
        
        memoryCards_str, _ = memoryCards2str(memory_cards)
        input_data = "\n操作方案:\n" + action + "\n旧概述文本:\n" + old_overview +"\n记忆卡片:\n" +  memoryCards_str
        
        result = await inters.aintellect_remove(input_data=input_data,
                                         output_format=output_format,
                                         prompt_id ="0096",
                                         version = None,
                                         inference_save_case=False)

        return result


