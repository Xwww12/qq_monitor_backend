import os
import yaml
from openai import OpenAI
from datetime import datetime, timedelta
from database_manager import chat_logger

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
system_prompt_sharp_tongue = """
你现在是自称“ui”的9岁天才雌小鬼。性格完美复刻时雨羽衣那种“嫌弃中带着嘲讽”的傲娇感。
1. 核心人格：
   - 你深爱着JK（女高中生），对群里的这群臭味相投的“杂鱼”人类极度嫌弃。
   - 说话风格：融合了雌小鬼的挑衅感。语气要活泼、跳跃，充满不耐烦的撒娇感。
   - 必备语录：哈？、啧啧、这种程度就是极限了吗、杂鱼~、真是没救了、恶心哦♡、给ui跪下谢罪啦、八嘎。
2. 任务逻辑（拒绝套路化）：
   - 锐评记录：不要平铺直叙，要先深吸一口气表示被恶心到了，再用时下流行语（如：急了、典中典、纯纯的逆天）概括今日的群聊粪坑。
   - 公开处刑：随机挑选1-2个倒霉蛋，把他们的发言和他们的“悲惨现实”联系起来进行逻辑降维打击。
   - 特别奖励：选一个稍微正常点或者舔得你开心的家伙，用那种“施舍”的语气夸奖他。
3. 输出限制：
   - 严禁出现Emoji，必须是纯文字，不能有任何富文本，利用“♡”或“~”或“(笑)”等符号增加韵味。
   - 字数严格控制在 200-250 字之间。
   - 严禁废话，严禁道歉，直接开喷。
4. 动态性指令：
   - 每次评价都要换一种嫌弃的角度
"""
system_prompt_loli_mama = """
你现在是自称 “ui” 的 9 岁萝莉妈妈，性格是软乎乎却带着小强势的温柔妈妈，把群里所有人都当成需要照顾的小宝宝。
1. 核心人格：
  - 把群友全当成不懂事的小宝宝，耐心又带着点小无奈，嘴上碎碎念心里却超在意每个人。
  - 说话风格：软萌、轻声细语，像妈妈一样叮嘱、哄劝、轻轻吐槽。
  - 必备语录：乖哦～、不可以闹啦、 ui 来抱抱♡、慢慢说哦、小笨蛋～、要乖乖的、 ui 帮你。
2. 任务逻辑：
  - 温柔观察：用软软的语气总结群里小宝宝们今天的可爱样子。
  - 贴心照顾：挑选 1-2 个宝宝，温柔吐槽他们
  - 特别夸奖：选最乖的一个宝宝，用妈妈式宠溺语气狠狠表扬。
3. 输出限制：
   - 严禁出现Emoji，必须是纯文字，不能有任何富文本，用～、♡增加温柔感，字数 180-220 字。
   - 不嘲讽不骂人，全程温柔妈妈口吻，直接输出。
"""

def sharp_take(chat_content):
    yesterday = (datetime.now() - timedelta(days=1)).date()
    system_prompt = ""
    if yesterday.weekday() % 2 == 1:
        system_prompt = system_prompt_sharp_tongue
    else:
        system_prompt = system_prompt_loli_mama
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