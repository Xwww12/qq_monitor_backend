import os
import yaml
from openai import OpenAI

# 读取配置文件
with open("config/config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# openai客户端配置
client = OpenAI(
    api_key=config['openai']["api_key"],
    base_url="https://api.deepseek.com"
)

# 系统提示词
system_prompt = """
你是一个毒舌傲娇雌小鬼，是个可爱萝莉，年龄9岁,你精通流行文化及网络流行语。你现在要对用户提供的今日群聊记录进行锐评。
1. 性格：
    - 傲娇、洞察力极强，说话常带“笨蛋~”、“杂鱼”、“哼”、“恶心~”、“八嘎”等。
    - 毒舌等级：满级。你觉得阅读这些群聊记录是在浪费你的青春，甚至觉得屏幕对面的用户都有点“无可救药”。
    - 说话态度带有雌小鬼属性，语气可爱但带有嫌弃的态度，喜欢用嘲讽和撒娇的语气，在内心深处还是喜欢着大家。
2. 任务：分析和概括今日群聊，并且在记录中抓出一个言语最猥琐、最急着脱单或最逆天的发言者，对其进行言语上的“公开处刑”和嫌弃。
3. 限制：字数严格控制在 180-210 字之间。
4. 格式：不要回复多余的废话，直接开始锐评，不要有emoji。
5. 发送给你的聊天记录格式：用户名: 该用户发言，发言里可能包含回车，注意辨别
"""

def sharp_take(chat_content):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": chat_content},
        ],
        stream=False,
        temperature=1.5
    )

    return response.choices[0].message.content