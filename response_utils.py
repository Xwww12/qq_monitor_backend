from dataclasses import dataclass, asdict
from typing import Any, Optional

@dataclass
class ApiResponse:
    code: int           # 状态码：如 200 成功, 400 业务错误, 500 系统错误
    message: str        # 提示信息
    data: Optional[Any] = None  # 返回的具体数据，默认为空

    def to_dict(self):
        """将类实例转换为字典，方便后续 JSON 序列化"""
        return asdict(self)

    @staticmethod
    def success(data=None, message="Success"):
        """便捷方法：生成成功响应"""
        return ApiResponse(code=200, message=message, data=data).to_dict()

    @staticmethod
    def error(message="Error", code=400):
        """便捷方法：生成失败响应"""
        return ApiResponse(code=code, message=message, data=None).to_dict()