import random
from datetime import datetime, timedelta
from database_manager import db, chat_logger
from logs import log
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from websocket_manager import send_group_msg
from openai_api import sharp_take
import base64


# 创建异步调度器
scheduler = AsyncIOScheduler()

def save_hour_data():
    log.info(f"[{datetime.now()}] 正在进行每小时数据汇总...")
    current = db.get_current()
    count = current['count'] if current else 0
    now_hour = datetime.now().strftime('%Y-%m-%d %H')
    db.upsert_hourly(now_hour, count)
    # 重置当前计数
    db.update_current(count=0, sender_name='')


async def save_day_data():
    log.info(f"[{datetime.now()}] 正在进行每天数据汇总...")
    hour_data = db.get_hourly_range(limit=25)
    if hour_data:
        total = 0
        yesterday = (datetime.now() - timedelta(days=1)).date()
        for data in hour_data:
            # 转换数据库中的时间字符串
            record_date = datetime.strptime(data['hour_time'], "%Y-%m-%d %H").date()
            if record_date == yesterday:
                total += data['count']

        db.upsert_daily(day_str=yesterday.strftime('%Y-%m-%d'), count=total)
        # 获取今日发言最多的用户名及发言数
        summary = ""
        top_sender = db.get_top_sender()
        emojis = ['😘', '👁👁', '💪🐷']
        weeks = ['周一', '周二', '周三', '疯狂木曜日', '周五', '周六', '周日']
        if top_sender is not None:
            top_sender = dict(top_sender)
            summary = f"{emojis[random.randint(0, len(emojis) - 1)]}今日时间完毕\n日期：{yesterday.strftime('%Y-%m-%d')}，{weeks[yesterday.weekday()]}\n总消息数：{total}\n水群冠军：🎉{top_sender['sender_name']}🎉({top_sender['count']}条)\n时间面板：http://yuudachi.icu/shi-jian"
        else:
            summary = f"{emojis[random.randint(0, len(emojis) - 1)]}今日时间完毕\n日期：{yesterday.strftime('%Y-%m-%d')}，{weeks[yesterday.weekday()]}\n总消息数：{total}\n时间面板：http://yuudachi.icu/shi-jian"

        # ai总结
        chat_history = chat_logger.read_all_for_ai()
        ai_summary = ""
        if chat_history and chat_history != "":
            ai_summary = sharp_take(chat_history)
            summary += f"\n今日锐评：{ai_summary}"
        # 清空聊天记录
        chat_logger.clear_logs()

        # 打日志
        log.info(summary)

        # 消息带着的表情包
        img = get_image_cq('data/img/img1.png')
        summary += img

        # 往群里发送总结
        await send_group_msg(summary)
        # 清空今日发言数
        db.clear_daily_rank()


def start_scheduler():
    scheduler.add_job(save_hour_data, 'cron', minute=0)  # 每小时整点
    scheduler.add_job(save_day_data, 'cron', hour=0, minute=1)  # 每天 00:01
    # scheduler.add_job(save_day_data, 'interval', seconds=60)  # 测试用

    # 启动后台线程运行定时任务
    scheduler.start()
    log.info("⏰ 定时任务已在后台启动")
    return scheduler


def get_image_cq(file_path):
    with open(file_path, "rb") as f:
        base64_data = base64.b64encode(f.read()).decode()
    return f"[CQ:image,file=base64://{base64_data}]"