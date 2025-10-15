"""
FunchoData API客户端
"""

import json
import requests
import pandas as pd
from typing import Dict, List, Optional, Any
from .exceptions import FunchoException, AuthenticationError, APIError


class FunchoClient:
    """FunchoData API客户端"""
    
    def __init__(self, token: str = None, base_url: str = None):
        """初始化客户端
        
        Args:
            token (str, optional): API密钥
            base_url (str, optional): 基础URL
        """
        self.token = token
        self.base_url = base_url or "https://www.funchodata.com"
        self.session = requests.Session()
        
    def set_token(self, token: str):
        """设置API密钥"""
        self.token = token
        
    def set_base_url(self, base_url: str):
        """设置基础URL"""
        self.base_url = base_url
        
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        if not self.token:
            raise AuthenticationError("未设置API密钥，请先调用 fc.set_token('your_api_key')")
            
        return {
            "Content-Type": "application/json",
            "api-key": self.token
        }
    
    def _make_request(self, form_code: str, params: Dict = None, fields: List[str] = None) -> Dict:
        """发送API请求
        
        Args:
            form_code (str): 表单编码
            params (dict): 请求参数
            fields (list): 字段列表
            
        Returns:
            dict: API响应数据
        """
        url = f"{self.base_url}/c-api/form/v1/dataframe/{form_code}"
        headers = self._get_headers()
        
        # 构建请求体
        request_data = {}
        
        if params:
            request_data["params"] = params
        else:
            request_data["params"] = {"page": "1", "size": "200"}
            
        if fields:
            request_data["fields"] = fields
            
        try:
            response = self.session.post(url, json=request_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # 检查新的响应格式
                if data.get('code') != 200:
                    if data.get('code') == 401:
                        raise AuthenticationError(f"认证失败: {data.get('msg', 'API密钥无效或已过期')}")
                    else:
                        raise APIError(f"API返回错误: {data.get('msg', '未知错误')} (code: {data.get('code')})")
                return data
            elif response.status_code == 401:
                raise AuthenticationError("HTTP 401: API密钥无效或已过期")
            elif response.status_code == 404:
                raise APIError(f"HTTP 404: 表单编码 '{form_code}' 不存在")
            else:
                raise APIError(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")
                
        except requests.exceptions.Timeout:
            raise APIError("请求超时，请稍后重试")
        except requests.exceptions.ConnectionError:
            raise APIError("网络连接错误，请检查网络连接")
        except requests.exceptions.RequestException as e:
            raise APIError(f"请求异常: {str(e)}")
    
    def get_json(self, form_code: str, params: Dict = None, fields: List[str] = None, **kwargs) -> Dict:
        """获取JSON格式数据
        
        Args:
            form_code (str): 表单编码
            params (dict): 查询参数
            fields (list): 字段列表
            
        Returns:
            dict: JSON数据
        """
        # 合并kwargs到params
        if kwargs:
            if params is None:
                params = {}
            params.update(kwargs)
            
        return self._make_request(form_code, params, fields)
    
    def get_df(self, form_code: str, params: Dict = None, fields: List[str] = None, **kwargs) -> pd.DataFrame:
        """获取DataFrame格式数据
        
        Args:
            form_code (str): 表单编码
            params (dict): 查询参数
            fields (list): 字段列表
            
        Returns:
            pandas.DataFrame: 数据框
        """
        # 合并kwargs到params
        if kwargs:
            if params is None:
                params = {}
            params.update(kwargs)
            
        data = self._make_request(form_code, params, fields)
        
        # 转换为DataFrame
        if 'data' in data:
            if data['data'] is None:
                # 空数据时返回空DataFrame
                if fields:
                    return pd.DataFrame(columns=fields)
                else:
                    return pd.DataFrame()
            elif isinstance(data['data'], list):
                # 直接是列表格式：[{"col1": "val1"}, ...]
                if len(data['data']) > 0:
                    return pd.DataFrame(data['data'])
                else:
                    # 空数据时返回空DataFrame
                    if fields:
                        return pd.DataFrame(columns=fields)
                    else:
                        return pd.DataFrame()
            elif isinstance(data['data'], dict):
                # 处理字典格式的data，支持多种结构
                if 'list' in data['data']:
                    rows = data['data']['list']
                    
                    if len(rows) > 0:
                        # 检查list中的元素类型
                        if isinstance(rows[0], dict):
                            # 新格式：list中直接是字典 [{"id": "1", "name": "test"}, ...]
                            df = pd.DataFrame(rows)
                        elif isinstance(rows[0], (list, tuple)):
                            # 旧格式：list中是数组，需要fields字段 [["1", "test"], ...]
                            if 'fields' in data['data']:
                                field_names = data['data']['fields']
                                records = []
                                for row in rows:
                                    record = dict(zip(field_names, row))
                                    records.append(record)
                                df = pd.DataFrame(records)
                            else:
                                raise APIError("API返回的数据格式不正确：list中是数组但缺少fields字段")
                        else:
                            raise APIError(f"API返回的list元素类型不支持: {type(rows[0])}")
                        
                        # 如果指定了字段筛选，则只返回指定字段
                        if fields:
                            available_fields = [f for f in fields if f in df.columns]
                            if available_fields:
                                df = df[available_fields]
                            else:
                                # 如果指定的字段都不存在，返回空DataFrame
                                return pd.DataFrame(columns=fields)
                        
                        return df
                    else:
                        # 空数据时返回空DataFrame
                        if fields:
                            return pd.DataFrame(columns=fields)
                        else:
                            return pd.DataFrame()
                else:
                    raise APIError("API返回的data字段格式不正确，缺少'list'字段")
            else:
                raise APIError(f"API返回的data字段类型不正确: {type(data['data'])}")
        else:
            raise APIError("API返回的数据中没有'data'字段")
    
    def get_all_pages(self, form_code: str, params: Dict = None, fields: List[str] = None, 
                      max_pages: int = None) -> pd.DataFrame:
        """获取所有分页数据
        
        Args:
            form_code (str): 表单编码
            params (dict): 查询参数
            fields (list): 字段列表
            max_pages (int): 最大页数限制
            
        Returns:
            pandas.DataFrame: 合并后的数据框
        """
        if params is None:
            params = {}
            
        # 设置默认分页参数
        params.setdefault('page', '1')
        params.setdefault('size', '200')
        
        all_data = []
        page = int(params['page'])
        
        while True:
            params['page'] = str(page)
            data = self._make_request(form_code, params, fields)
            
            if 'data' in data and data['data'] is not None:
                current_data = []
                
                if isinstance(data['data'], list):
                    # 直接是列表格式
                    current_data = data['data']
                elif isinstance(data['data'], dict) and 'list' in data['data']:
                    rows = data['data'].get('list', [])
                    
                    if len(rows) > 0:
                        if isinstance(rows[0], dict):
                            # 新格式：list中直接是字典
                            current_data = rows
                        elif isinstance(rows[0], (list, tuple)):
                            # 旧格式：list中是数组，需要fields字段
                            field_names = data['data'].get('fields', [])
                            for row in rows:
                                record = dict(zip(field_names, row))
                                current_data.append(record)
                        else:
                            # 未知格式，跳过
                            pass
                
                if len(current_data) == 0:
                    break  # 没有更多数据
                    
                all_data.extend(current_data)
                
                # 检查是否还有更多页
                if len(current_data) < int(params['size']):
                    break  # 当前页数据少于页面大小，说明是最后一页
                    
                page += 1
                
                # 检查最大页数限制
                if max_pages and page > max_pages:
                    break
            else:
                break
                
        if all_data:
            return pd.DataFrame(all_data)
        else:
            if fields:
                return pd.DataFrame(columns=fields)
            else:
                return pd.DataFrame() 