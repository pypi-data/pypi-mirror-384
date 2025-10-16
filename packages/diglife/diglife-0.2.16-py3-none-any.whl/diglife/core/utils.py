# 工具箱
from diglife.models import MemoryCards

def memoryCards2str(memory_cards: MemoryCards):
    memoryCards_str = ""
    memoryCards_time_str = ""
    for memory_card in memory_cards:
        memory_card_str = memory_card["title"] + "\n" + memory_card["content"] + "\n"
        memoryCards_str += memory_card_str
        memoryCards_time_str += "\n"
        memoryCards_time_str += memory_card["time"]
    return memoryCards_str, memoryCards_time_str
