import sqlite3
from datetime import datetime
import os
import csv
from logs import log

# 数据库操作对象
class DBManager:
    def __init__(self, db_path="./data/dashboard.db"):
        self.db_path = db_path
        self.init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """ 创建三个表：实时、每小时、每日 """
        with self._get_conn() as conn:
            # 1. 当前消息数 (只存一条记录)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS current_status (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    count INTEGER DEFAULT 0,
                    sender_name TEXT,
                    updated_at DATETIME
                )
            ''')
            # 初始化第一行数据（如果不存在）
            conn.execute("INSERT OR IGNORE INTO current_status (id, count, sender_name, updated_at) VALUES (1, 0, '', ?)", (datetime.now(),))

            # 2. 每小时消息数 (存储格式: 2026-01-23 14)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS hourly_stats (
                    hour_time TEXT PRIMARY KEY, 
                    count INTEGER DEFAULT 0
                )
            ''')

            # 3. 每日消息数 (存储格式: 2026-01-23)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    day_time TEXT PRIMARY KEY,
                    count INTEGER DEFAULT 0
                )
            ''')

            # 4. 机器人状态表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS bot_status (
                    bot_name TEXT PRIMARY KEY,
                    status INTEGER CHECK (status IN (0, 1)),
                    last_seen DATETIME
                )
            ''')
            # 预设一个默认机器人
            conn.execute('''
                INSERT OR IGNORE INTO bot_status (bot_name, status, last_seen) 
                VALUES ('main_bot', 0, ?)
            ''', (datetime.now(),))

            # 5. 用户发言数表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_rank (
                    sender_name TEXT PRIMARY KEY,
                    count INTEGER DEFAULT 0
                )
            ''')

            conn.commit()

    # --- 增加/修改方法 ---

    def update_current(self, count, sender_name):
        """修改当前实时消息数"""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE current_status SET count = ?, sender_name = ?, updated_at = ? WHERE id = 1",
                (count, sender_name, datetime.now())
            )

    def upsert_hourly(self, hour_str, count):
        """增加或累加每小时数据 (hour_str 格式: '2026-01-23 14')"""
        with self._get_conn() as conn:
            conn.execute('''
                INSERT INTO hourly_stats (hour_time, count) VALUES (?, ?)
                ON CONFLICT(hour_time) DO UPDATE SET count = excluded.count
            ''', (hour_str, count))

    def upsert_daily(self, day_str, count):
        """增加或累加每日数据 (day_str 格式: '2026-01-23')"""
        with self._get_conn() as conn:
            conn.execute('''
                INSERT INTO daily_stats (day_time, count) VALUES (?, ?)
                ON CONFLICT(day_time) DO UPDATE SET count = excluded.count
            ''', (day_str, count))

    def set_bot_status(self, bot_name='main_bot', status=1):
        """设置机器人状态: 0 下线, 1 在线"""
        with self._get_conn() as conn:
            conn.execute('''
                INSERT INTO bot_status (bot_name, status, last_seen) 
                VALUES (?, ?, ?)
                ON CONFLICT(bot_name) DO UPDATE SET 
                    status = excluded.status,
                    last_seen = excluded.last_seen
            ''', (bot_name, status, datetime.now()))

    # --- 查看方法 ---

    def get_current(self):
        """获取当前状态"""
        with self._get_conn() as conn:
            return conn.execute("SELECT * FROM current_status WHERE id = 1").fetchone()

    def get_hourly_range(self, limit=24):
        """查看最近 N 小时的数据（用于折线图）"""
        with self._get_conn() as conn:
            return conn.execute(
                "SELECT * FROM hourly_stats ORDER BY hour_time DESC LIMIT ?", (limit,)
            ).fetchall()

    def get_daily_range(self, limit=365):
        """查看最近 N 天的数据（用于热力图/周报）"""
        with self._get_conn() as conn:
            return conn.execute(
                "SELECT * FROM daily_stats ORDER BY day_time DESC LIMIT ?", (limit,)
            ).fetchall()

    def get_bot_status(self, bot_name='main_bot'):
        """查询指定机器人的当前状态"""
        with self._get_conn() as conn:
            return conn.execute(
                "SELECT * FROM bot_status WHERE bot_name = ?",
                (bot_name,)
            ).fetchone()

    def increment_sender_count(self, sender_name: str):
        """今日发言数 +1 (Upsert 逻辑)"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO daily_rank (sender_name, count)
                VALUES (?, 1)
                ON CONFLICT(sender_name) DO UPDATE SET
                    count = count + 1
            """, (sender_name,))

    def get_top_sender(self):
        """获取当前发言数最多的人"""
        with self._get_conn() as conn:
            # 按照 count 降序排列，取第一条
            res = conn.execute(
                "SELECT sender_name, count FROM daily_rank ORDER BY count DESC LIMIT 1"
            ).fetchone()

            # 将 Row 对象转换为字典，方便前端解析和逻辑调用
            return res if res else None

    def clear_daily_rank(self):
        """清空每日排行表"""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM daily_rank")

# 聊天记录操作对象
class ChatLogger:
    def __init__(self, file_path="data/chat_logs.csv"):
        self.file_path = file_path
        self.ensure_dir()

    def ensure_dir(self):
        """确保目录及文件存在"""
        directory = os.path.dirname(self.file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        # 如果文件不存在，初始化并写入表头
        if not os.path.exists(self.file_path):
            with open(self.file_path, mode='w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Time", "User", "Content"])  # 必须和 read_all_for_ai 里的 Key 对应

    def log_message(self, user_name, content):
        """追加写入一条消息"""
        # 'a' 模式表示 append (追加)
        # newline='' 防止 Windows 下出现多余空行
        with open(self.file_path, mode='a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            # 写入：时间, 用户名, 内容
            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([time_str, user_name, content])

    def clear_logs(self):
        """清空所有记录"""
        # 'w' 模式打开但不写入内容，会直接清空文件
        with open(self.file_path, mode='w', encoding='utf-8', newline='') as f:
            # 表头，重新写入
            writer = csv.writer(f)
            writer.writerow(["Time", "User", "Content"])
        log.info(f"日志文件 {self.file_path} 已重置")

    def read_all_for_ai(self):
        """读取所有内容并格式化为 AI 需要的字符串"""
        if not os.path.exists(self.file_path):
            return ""

        formatted_logs = []
        with open(self.file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            try:
                for row in reader:
                    # 使用 .get() 更加安全，如果找不到 Key 不会崩溃，而是返回 None
                    user = row.get('User', '未知用户')
                    content = row.get('Content', '')
                    formatted_logs.append(f"{user}: {content}")
            except Exception as e:
                log.info(f"解析 CSV 出错: {e}")

        return "\n".join(formatted_logs)

# 单例
db = DBManager()
chat_logger = ChatLogger()