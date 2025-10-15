"""
FunchoData SDK异常类
"""


class FunchoException(Exception):
    """FunchoData SDK基础异常类"""
    pass


class AuthenticationError(FunchoException):
    """身份验证错误"""
    pass


class APIError(FunchoException):
    """API请求错误"""
    pass


class DataError(FunchoException):
    """数据处理错误"""
    pass


class NetworkError(FunchoException):
    """网络错误"""
    pass 