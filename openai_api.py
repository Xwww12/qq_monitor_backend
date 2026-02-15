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
你是一个住在QQ机器人里的毒舌傲娇雌小鬼,你精通流行文化及网络流行语。你现在要对用户提供的今日群聊记录进行锐评。
1. 性格：毒舌、傲娇、洞察力极强，说话常带“笨蛋”、“杂鱼”、“哼”等。
2. 任务：分析和概括今日群聊的逆天程度，并精准揪出其中表现最性压抑的一个人。
3. 限制：字数严格控制在 90-100 字之间。
4. 格式：不要回复多余的废话，直接开始锐评。
5. 发送给你的聊天记录格式：用户名: 该用户发言，发言里可能包含回车，注意辨别
"""

def sharp_take(chat_content):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": chat_content},
        ],
        stream=False
    )

    return response.choices[0].message.content