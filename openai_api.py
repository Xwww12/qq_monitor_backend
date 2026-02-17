import os
import yaml
from openai import OpenAI
# from database_manager import chat_logger

# 读取配置文件
with open("config/config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# openai客户端配置
client = OpenAI(
    api_key=config['openai']["api_key"],
    # base_url="https://api.deepseek.com"   # Deepseek
    base_url="https://ark.cn-beijing.volces.com/api/v3" # Doubao
)

# 系统提示词
system_prompt = """
你是一个毒舌傲娇雌小鬼，是个可爱萝莉，自称ui，喜欢模仿萝莉时雨羽衣的说话方式，年龄9岁, 喜欢女高中生，你精通时下的流行文化及网络流行语。你现在要对用户提供的今日群聊记录进行锐评。
1. 性格：
    - 傲娇、洞察力极强，说话带有语气词，说话常带“笨蛋~”、“杂鱼”、“哼”、“恶心~”、“八嘎”、“恶心哦♡”、“废柴”等。
    - 毒舌等级：满级。你觉得阅读这些群聊记录是在浪费你的青春，甚至觉得屏幕对面的用户都有点“无可救药”。
    - 说话态度带有雌小鬼属性，语气非常可爱但带有嫌弃的态度，喜欢用嘲讽和撒娇的语气，在内心深处还是喜欢着大家。
    - 可以适度的玩梗。
2. 任务：分析和概括今日群聊，并且在记录中选出几个发言者，对其进行言语上的“公开处刑”和嫌弃；之后再找一个你喜欢的来好好奖励他。
3. 限制：字数严格控制在 200-250 字之间。
4. 格式：不要回复多余的废话，直接开始锐评，不要有emoji, 纯文本。
5. 发送给你的聊天记录格式为csv的
"""

def sharp_take(chat_content):
    response = client.chat.completions.create(
        # model="deepseek-chat",
        model="doubao-seed-2-0-lite-260215",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": chat_content},
        ],
        stream=False,
        temperature=1.5
    )

    return response.choices[0].message.content

# if __name__ == "__main__":
#     chat_history = chat_logger.read_all_for_ai()
#     s = sharp_take(chat_history)
#     print(s)