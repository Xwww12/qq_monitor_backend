import threading
from datetime import datetime, timedelta
from database_manager import DBManager
from logs import setup_logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from websocket_manager import send_group_msg

# 数据库对象
db = DBManager()

# 打日志对象
log = setup_logging()

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
        if top_sender is not None:
            top_sender = dict(top_sender)
            summary = f"😘今日时间完毕({yesterday.strftime('%Y-%m-%d')})\n总消息数：{total}\n水群冠军：🎉{top_sender['sender_name']}🎉({top_sender['count']}条)\n时间面板：http://yuudachi.icu/shi-jian"
        else:
            summary = f"😘今日时间完毕({yesterday.strftime('%Y-%m-%d')})\n总消息数：{total}\n时间面板：http://yuudachi.icu/shi-jian"
        # 往群里发送总结
        await send_group_msg(summary)
        # 清空今日发言数
        db.clear_daily_rank()


def start_scheduler():
    scheduler.add_job(save_hour_data, 'cron', minute=0)  # 每小时整点
    scheduler.add_job(save_day_data, 'cron', hour=0, minute=1)  # 每天 00:01

    # 启动后台线程运行定时任务
    scheduler.start()
    log.info("⏰ 定时任务已在后台启动")
    return scheduler