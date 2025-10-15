
from diglife.utils import extract_json, extract_article, super_log
from prompt_writing_assistant.prompt_helper import Intel,IntellectType
from llmada.core import BianXieAdapter
from diglife.models import MemoryCard, MemoryCardScore, MemoryCards
import math
import asyncio
import json

inters = Intel()
table_name="prompts_table"

from diglife import logger
from .utils import memoryCards2str


class MemoryCardManager:
    def __init__(self,model_name: str = "gemini-2.5-flash-preview-05-20-nothinking",
                      api_key: str = None):
        self.bx = BianXieAdapter(model_name=model_name,
                                 api_key= api_key,
                                 )

    @staticmethod
    def get_score_overall(
        S: list[int], total_score: int = 0, epsilon: float = 0.001, K: float = 0.8
    ) -> float:
        """
        计算 y = sqrt(1/600 * x) 的值。
        计算人生总进度
        """
        x = sum(S)
        return math.sqrt((1/600) * x)  * 100

    @staticmethod
    def get_score(
        S: list[int], total_score: int = 0, epsilon: float = 0.001, K: float = 0.1
    ) -> float:
        # 人生主题分值计算
        # 一个根据 列表分数 计算总分数的方法 如[1,4,5,7,1,5] 其中元素是 1-10 的整数

        # 一个非常小的正数，确保0分也有微弱贡献，100分也不是完美1
        # 调整系数，0 < K <= 1。K越大，总分增长越快。


        for score in S:
            # 1. 标准化每个分数到 (0, 1) 区间
            normalized_score = (score + epsilon) / (10 + epsilon)

            # 2. 更新总分
            # 每次增加的是“距离满分的剩余空间”的一个比例
            total_score = total_score + (100 - total_score) * normalized_score * K

            # 确保不会因为浮点数精度问题略微超过100，虽然理论上不会
            if total_score >= 100 - 1e-9:  # 留一点点余地，避免浮点数误差导致判断为100
                total_score = 100 - 1e-9  # 强制设置一个非常接近100但不等于100的值
                break  # 如果已经非常接近100，可以提前终止

        return total_score

    async def ascore_from_memory_card(self, memory_cards: list[str]) -> list[int]:
        # 记忆卡片打分
        score_memory_card_prompt, _ = inters.get_prompts_from_sql(
            prompt_id="0088"
        )

        tasks = []
        for memory_card in memory_cards:
            tasks.append(
                self.bx.aproduct(score_memory_card_prompt + "\n" + memory_card)
            )
        results = await asyncio.gather(*tasks, return_exceptions=False)

        result_1 = [json.loads(extract_json(result)) for result in results]
        try:
            for score in result_1:
                MemoryCardScore(**score)
        except:
            # log
            pass
        return result_1

    async def amemory_card_merge(self, memory_cards: list[str]):
        # 记忆卡片合并
        memory_card_merge_prompt, _ = inters.get_prompts_from_sql(
            prompt_id="0089"
        )

        memoryCards_str, memoryCards_time_str = memoryCards2str(memory_cards)
        result = await self.bx.aproduct(
            memory_card_merge_prompt
            + "\n"
            + memoryCards_str
            + "\n 各记忆卡片的时间"
            + memoryCards_time_str
        )
        result_1 = json.loads(extract_json(result))

        try:
            MemoryCard(**result_1)
        except:
            # log
            pass

        return result_1

    async def amemory_card_polish(self, memory_card: dict) -> dict:
        # 记忆卡片润色
        # TODO 要将时间融入到内容中润色
        memory_card_polish_prompt, _ = inters.get_prompts_from_sql(
            prompt_id="0090"
        )

        super_log(
            "\n记忆卡片标题: "
            + memory_card["title"]
            + "\n记忆卡片内容: "
            + memory_card["content"]
            + "\n记忆卡片发生时间: "
            + memory_card["time"],
            "work",
        )
        result = await self.bx.aproduct(
            memory_card_polish_prompt
            + "\n记忆卡片标题: "
            + memory_card["title"]
            + "\n记忆卡片内容: "
            + memory_card["content"]
            + "\n记忆卡片发生时间: "
            + memory_card["time"]
        )
        super_log(result, "result")

        result_1 = json.loads(extract_json(result))
        try:
            MemoryCard(**result_1)
        except:
            # log
            pass

        return result_1


    async def agenerate_memory_card_by_text(
        self, chat_history_str: str, weight: int = 1000
    ):
        # 0091 上传文件生成记忆卡片-memory_card_system_prompt
        # 0092 上传文件生成记忆卡片-time_prompt

        memory_card_system_prompt, _ = inters.get_prompts_from_sql(prompt_id="0091")
        time_prompt, _ = inters.get_prompts_from_sql(prompt_id="0092")

        number_ = len(chat_history_str) // weight + 1
        base_prompt = (
            memory_card_system_prompt.format(number=number_) + chat_history_str
        )

        try:
            result = await self.bx.aproduct(base_prompt)
            result_dict = json.loads(extract_json(result))

            chapters = result_dict["chapters"]
            for i in chapters:
                super_log(
                    f"# chat_history: {chat_history_str} # chapter:" + i.get("content")
                )
                time_result = await self.bx.aproduct(
                    time_prompt
                    + f"# chat_history: {chat_history_str} # chapter:"
                    + i.get("content")
                )
                time_dict = json.loads(extract_json(time_result))
                i.update(time_dict)

            return chapters
        except Exception as e:
            print(f"Error processing  {chat_history_str[:30]}: {e}")
            return ""

    async def agenerate_memory_card(self, chat_history_str: str, weight: int = 1000):
        # 0093 聊天历史生成记忆卡片-memory_card_system_prompt
        # 0094 聊天历史生成记忆卡片-time_prompt

        memory_card_system_prompt, _ = inters.get_prompts_from_sql(prompt_id="0093")
        time_prompt, _ = inters.get_prompts_from_sql(prompt_id="0094")

        number_ = len(chat_history_str) // weight + 1
        base_prompt = (
            memory_card_system_prompt.format(number=number_) + chat_history_str
        )
        try:
            result = await self.bx.aproduct(base_prompt)
            result_dict = json.loads(extract_json(result))
            super_log(result_dict,'result_dict')
            chapters = result_dict["chapters"]
            for i in chapters:
                time_result = await self.bx.aproduct(
                    time_prompt
                    + f"# chat_history: {chat_history_str} # chapter:"
                    + i.get("content")
                )
                time_dict = json.loads(extract_json(time_result))
                super_log(time_dict, "time_dict")
                i.update(time_dict)
                i.update({"topic": 0})

            return chapters
        except Exception as e:
            print(f"Error processing  {chat_history_str[:30]}: {e}")
            return ""


###


class BiographyGenerate:
    def __init__(self,model_name: str = "gemini-2.5-flash-preview-05-20-nothinking",
                      api_key: str = None):
        self.bx = BianXieAdapter(model_name=model_name,
                                 api_key= api_key,
                                 )

    async def extract_person_name(self, bio_chunk: str):
        """0087 提取人名"""
        extract_person_name_prompt, _ = inters.get_prompts_from_sql(
            prompt_id="0087"
        )
        result = await self.bx.aproduct(extract_person_name_prompt + "\n" + bio_chunk)
        return json.loads(extract_json(result))

    async def extract_person_place(self, bio_chunk: str):
        """0086 提取地名"""
        extract_place_name_prompt, _ = inters.get_prompts_from_sql(
            prompt_id="0086"
        )
        result = await self.bx.aproduct(extract_place_name_prompt + "\n" + bio_chunk)
        return json.loads(extract_json(result))

    async def amaterial_generate(self, vitae: str, memory_cards: list[str]) -> str:
        """
        素材整理
        vitae : 简历
        memory_cards : 记忆卡片们
        0085 素材整理
        0082 素材增量生成
        """
        interview_material_clean_prompt, _ = inters.get_prompts_from_sql(
            prompt_id="0085"
        )
        interview_material_add_prompt, _ = inters.get_prompts_from_sql(
            prompt_id="0082"
        )

        def split_into_chunks(my_list, chunk_size=5):
            """
            使用列表推导式将列表分割成大小为 chunk_size 的块。
            """
            return [
                my_list[i : i + chunk_size] for i in range(0, len(my_list), chunk_size)
            ]

        # --- 示例 ---
        chunks = split_into_chunks(memory_cards, chunk_size=2)

        material = ""
        for i, chunk in enumerate(chunks):
            chunk = json.dumps(chunk, ensure_ascii=False)
            if i == 0:
                base_prompt = interview_material_clean_prompt + vitae + chunk
            else:
                super_log(
                    "#素材:\n" + material + "\n#记忆卡片:\n" + chunk,
                    "0082 素材增量生成",
                )
                base_prompt = (
                    interview_material_add_prompt
                    + "#素材:\n"
                    + material
                    + "#记忆卡片:\n"
                    + chunk
                )
            try:
                material = await self.bx.aproduct(base_prompt)
            except Exception as e:
                raise TypeError("maters素材整理的时候出问题了")

        return material

    async def aoutline_generate(self, material: str) -> str:
        """
        0084 大纲生成
        """

        outline_prompt, _ = inters.get_prompts_from_sql(
            prompt_id="0084"
        )
        super_log(material, "0084 大纲生成")
        try:
            outline_origin = await self.bx.aproduct(outline_prompt + material)
        except Exception as e:
            raise TypeError("生成大纲的时候出问题")
        outline = extract_json(outline_origin)
        return json.loads(outline)

    async def agener_biography_brief(self, outline: dict) -> str:
        """
        0083 传记简介
        """
        biography_brief_prompt, _ = inters.get_prompts_from_sql(
            prompt_id="0083"
        )
        outline = json.dumps(outline, ensure_ascii=False)
        super_log(outline, "0083 传记简介")
        brief = await self.bx.aproduct(biography_brief_prompt + outline)
        return brief

    async def awrite_chapter(
        self,
        chapter,
        master="",
        material="",
        outline: dict = {},
        suggest_number_words=3000,
    ):
        created_material = ""
        try:
            # 0080 prompt_get_infos
            # 0081 prompt_base
            await asyncio.sleep(0.1)
            prompt_get_infos, _ = inters.get_prompts_from_sql(
                prompt_id="0080"
            )
            prompt_base, _ = inters.get_prompts_from_sql(
                prompt_id="0081"
            )

            material_prompt = prompt_get_infos.format(
                material=material,
                frame=json.dumps(outline),
                requirements=json.dumps(chapter),
            )
            try:
                material = await self.bx.aproduct(material_prompt)
            except Exception as e:
                raise TypeError("素材整理的时候出问题了")
            words = prompt_base.format(
                master=master,
                chapter=f'{chapter.get("chapter_number")} {chapter.get("title")}',
                topic=chapter.get("topic"),
                number_words=suggest_number_words,
                material=material,
                reference="",
                port_chapter_summery="",
            )
            try:
                article = await self.bx.aproduct(words)
            except Exception as e:
                raise TypeError("写传记的时候出问题了")
            try:
                chapter_name = await self.extract_person_name(article)
                chapter_place = await self.extract_person_place(article)
            except Exception as e:
                raise TypeError(f"提取东西的时候出问题了 {e}")

            assert isinstance(chapter_name, list)
            assert isinstance(chapter_place, list)

            return {
                "chapter_number": chapter.get("chapter_number"),
                "article": extract_article(article),
                "material": material,
                "created_material": created_material,
                "chapter_name": chapter_name,
                "chapter_place": chapter_place,
            }

        except Exception as e:
            print(f"Error processing chapter {chapter.get('chapter_number')}: {e}")
            return {
                "chapter_number": chapter.get("chapter_number"),
                "article": "",
                "material": "material",
                "created_material": "created_material",
                "chapter_name": "chapter_name",
                "chapter_place": "chapter_place",
            }

    async def agenerate_biography_free(
        self, user_name: str, vitae: str, memory_cards: list[dict]
    ):
        # 简要版说法
        prompt, _ = inters.get_prompts_from_sql(prompt_id="0095")
        memoryCards_str, _ = memoryCards2str(memory_cards)
        print("\n" + f"{user_name},{vitae},{memoryCards_str}")
        result = await self.bx.aproduct(
            prompt + "\n" + f"{user_name},{vitae},{memoryCards_str}"
        )
        result = json.loads(extract_json(result))
        return result

