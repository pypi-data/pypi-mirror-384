#
from diglife.utils import extract_json, extract_article, super_log
from prompt_writing_assistant.prompt_helper import Intel,IntellectType
from llmada.core import BianXieAdapter
from diglife.models import MemoryCard, MemoryCardScore, MemoryCards
import math
import asyncio
import json

inters = Intel()
table_name="prompts_table"

from .utils import memoryCards2str
from diglife import logger


###


class DigitalAvatar:
    def __init__(self,model_name: str = "gemini-2.5-flash-preview-05-20-nothinking",
                      api_key: str = None):
        self.bx = BianXieAdapter(model_name=model_name,
                                 api_key= api_key,
                                 )

    async def desensitization(self, memory_cards: list[str]) -> list[str]:
        """
        数字分身脱敏 0100
        """
        prompt, _ = inters.get_prompts_from_sql(prompt_id="0100")
        tasks = []
        for memory_card in memory_cards:
            tasks.append(self.bx.aproduct(prompt + "\n" + memory_card.get("content")))
        results = await asyncio.gather(*tasks, return_exceptions=False)

        for i in range(len(memory_cards)):
            memory_cards[i]["content"] = extract_article(results[i])
        return memory_cards
    
    async def personality_extraction(self, memory_cards: list[dict],action:str,old_character:str) -> str:
        """
        数字分身性格提取 0099
        """
        memoryCards_str, _ = memoryCards2str(memory_cards)

        prompt, _ = inters.get_prompts_from_sql(prompt_id="0099")
        input_data = "\n操作方案:\n" + action + "\n旧人物性格:\n" + old_character +"\n记忆卡片:\n" +  memoryCards_str
        
        result = await self.bx.aproduct(prompt + input_data)
        
        return extract_article(result)

    
    async def abrief(self, memory_cards: list[dict]) -> dict:
        """
        数字分身介绍 0098
        """
        # TOOD 增加字数限制, tag标签 两个
        memoryCards_str, _ = memoryCards2str(memory_cards)

        prompt, _ = inters.get_prompts_from_sql(prompt_id="0098")
        input_data = "聊天历史:\n" + memoryCards_str
        
        result = await self.bx.aproduct(prompt + input_data)
        
        dict_ = json.loads(extract_json(result))
        return json.loads(extract_json(result))

    async def auser_relationship_extraction(self,text: str) -> dict:
        """
        用户关系提取 0097
        """
        prompt, _ = inters.get_prompts_from_sql(prompt_id="0097")
        input_data = "聊天历史" + text
        
        result = await self.bx.aproduct(prompt + input_data)
        

        return json.loads(extract_json(result))

    async def auser_overview(self,action: str,old_overview: str, memory_cards: list[dict],
                             version = None,
                             ) -> str:
        """
        用户概述 0096
        """
        memoryCards_str, _ = memoryCards2str(memory_cards)
        # prompt, _ = inters.get_prompts_from_sql(prompt_id="0096", table_name=table_name)
        input_data = "\n操作方案:\n" + action + "\n旧概述文本:\n" + old_overview +"\n记忆卡片:\n" +  memoryCards_str
        
        result = inters.intellect_3(input_data,
                           type = IntellectType.inference,
                           prompt_id = "0096",
                           demand = "用户的概述太多了, 还是要保持在100字左右?",
                           version = version,
                           )

        return result


