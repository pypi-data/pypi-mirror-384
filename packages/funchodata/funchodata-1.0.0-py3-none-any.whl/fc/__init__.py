"""
FunchoData SDK - 简化的数据获取工具

使用方法:
    import fc
    
    # 设置API密钥
    fc.set_token('your_api_key')
    
    # 获取数据
    df = fc.get_df('para_main', params={'para_clas_cd': ''}, fields=['id', 'para_clas_cd'])
"""

from .client import FunchoClient
from .exceptions import FunchoException, AuthenticationError, APIError

__version__ = "1.0.0"
__author__ = "FunchoData"

# 全局客户端实例
_client = FunchoClient()

def set_token(token):
    """设置API密钥
    
    Args:
        token (str): API密钥
    """
    _client.set_token(token)

def set_base_url(base_url):
    """设置基础URL（仅支持生产环境）
    
    Args:
        base_url (str): 基础URL，仅支持生产环境 https://www.funchodata.com
    """
    _client.set_base_url(base_url)

def get_df(form_code, params=None, fields=None, **kwargs):
    """获取DataFrame数据
    
    Args:
        form_code (str): 表单编码
        params (dict, optional): 查询参数，包含分页参数和条件参数
        fields (list, optional): 需要返回的字段列表
        **kwargs: 其他参数
        
    Returns:
        pandas.DataFrame: 返回的数据框
        
    Example:
        >>> import fc
        >>> fc.set_token('your_api_key')
        >>> df = fc.get_df('para_main', params={'page': '1', 'size': '200'}, fields=['id', 'para_clas_cd'])
    """
    return _client.get_df(form_code, params, fields, **kwargs)

def get_json(form_code, params=None, fields=None, **kwargs):
    """获取JSON数据
    
    Args:
        form_code (str): 表单编码
        params (dict, optional): 查询参数
        fields (list, optional): 需要返回的字段列表
        **kwargs: 其他参数
        
    Returns:
        dict: 返回的JSON数据
    """
    return _client.get_json(form_code, params, fields, **kwargs)

def get_all_pages(form_code, params=None, fields=None, max_pages=None):
    """获取所有分页数据
    
    Args:
        form_code (str): 表单编码
        params (dict, optional): 查询参数
        fields (list, optional): 需要返回的字段列表
        max_pages (int, optional): 最大页数限制
        
    Returns:
        pandas.DataFrame: 合并后的数据框
    """
    return _client.get_all_pages(form_code, params, fields, max_pages)

# 向后兼容的别名
pro_api = get_df 