from logs import setup_logging
import json
import websockets
from database_manager import DBManager
import asyncio
import yaml

# 打日志对象
log = setup_logging()

# 数据库对象
db = DBManager()

# websocket连接对象
ws = None

# 读取配置文件
with open("config/config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# ---  WebSocket 连接QQ机器人 ---
async def websocket_client_task():
    global ws
    # 连接需要的信息
    uri = config["websocket"]["uri"]
    token = config["websocket"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 自动重连机制
    try_cnt = 0
    while True:
        try:
            log.info(f"正在连接到远端 WebSocket: {uri}")
            async with websockets.connect(uri, additional_headers=headers) as websocket:
                ws = websocket
                try_cnt = 0
                log.info("远端 WebSocket 连接成功！")
                async for message in websocket:
                    process_data(message)
        except Exception as e:
            ws = None
            try_cnt += 1
            if try_cnt > 10:
                log.info(f"达到最大重连次数")
                # 设置机器人状态为下线
                db.set_bot_status(status=0)
                break
            log.info(f"WebSocket 连接断开或报错: {e}，5秒后尝试重连...")
            await asyncio.sleep(5)

# 处理接收到的消息
def process_data(message):
    data = json.loads(message)
    # 没有post_type的话就为None, 往群里发消息的返回里面没有post_type
    post_type = data.get('post_type')
    # 判断数据类型
    if post_type == 'meta_event':
        if data['meta_event_type'] == 'heartbeat':
            # 心跳检测
            db.set_bot_status(status=1)
    elif post_type == 'message' and str(data['group_id']) == config['qq']['group_id']:
        # 消息数+1，且记录最后发言人
        sender_name = data['sender']['nickname'] if data['sender']['card'] == '' else data['sender']['card']
        db.update_current(count=db.get_current()['count'] + 1, sender_name=sender_name)
        # 记录发言人今日总消息数，会自动+1
        db.increment_sender_count(sender_name)
        # 设置机器人状态
        db.set_bot_status(status=1)
    else:
        log.info(f'未知类型消息：{data}')


async def send_group_msg(message):
    """往群里发送消息"""
    # 构造 API 调用包
    api_request = {
        "action": "send_group_msg",
        "params": {
            "group_id": config['qq']['group_id'],
            "message": message,
        },
        "post_type": "POST"
    }

    # 发送请求
    if ws is not None:
        await ws.send(json.dumps(api_request))
