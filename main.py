import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database_manager import db
from response_utils import ApiResponse
from schedule_task import start_scheduler
from logs import log
from websocket_manager import websocket_client_task
import yaml

# --- 使用 FastAPI 生命周期管理后台任务 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：创建 WebSocket 后台任务
    task = asyncio.create_task(websocket_client_task())
    # 创建定时任务
    scheduler = start_scheduler()
    yield
    # 关闭时：取消任务
    task.cancel()
    # 关闭定时任务
    scheduler.shutdown()

# 读取配置文件
with open("config/config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# fastAPI对象
app = FastAPI(lifespan=lifespan)
# 允许跨域的列表
origins = [
    f"http://{config['server']['frontend_address']}",
    f"http://{config['server']['frontend_address']}:80",
    f"http://{config['server']['frontend_address']}:5173",
    "http://localhost",
    "http://localhost:80",
    "http://localhost:5173",
    "http://yuudachi.icu",
    "http://yuudachi.icu:80",
    "http://yuudachi.icu:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # 允许的源
    allow_credentials=True,
    allow_methods=["*"],         # 允许所有方法 (GET, POST 等)
    allow_headers=["*"],         # 允许所有请求头
)

# --- 提供给前端的 HTTP 接口 ---
@app.get("/get_status")
async def get_status():
    """
    获取机器人状态
    """
    status = db.get_bot_status()['status']
    return ApiResponse.success(data=status)


@app.get("/get_last_speaker")
async def get_last_speaker():
    """
    获取最后一个说话的人
    """
    current = db.get_current()
    data = {
        "id": current['id'],
        "count": current['count'],
        "sender_name": current['sender_name'],
        "updated_at": current['updated_at'],
    }
    return ApiResponse.success(data=data)


@app.post("/get_hour_msg_cnt")
async def get_hour_msg_cnt(para: dict):
    """
    获取每小时消息数
    """
    limit = para['limit']
    if limit is None or limit <= 0:
        return ApiResponse.error(message='参数错误')
    data = db.get_hourly_range(limit=limit)
    # 转换成字典并正序排序给前端显示
    data = [dict(r) for r in data]
    data.sort(key=lambda x: x['hour_time'])
    return ApiResponse.success(data=data)


@app.post("/get_day_msg_cnt")
async def get_day_msg_cnt(para: dict):
    """
    获取每天消息数
    """
    limit = para['limit']
    if limit is None or limit <= 0:
        return ApiResponse.error(message='参数错误')
    data = db.get_daily_range(limit=limit)
    data = [dict(r) for r in data]
    return ApiResponse.success(data=data)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=config['server']['port'])