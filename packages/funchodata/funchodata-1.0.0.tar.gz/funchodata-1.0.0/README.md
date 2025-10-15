# FunchoData Python SDK

FunchoData官方Python SDK，提供简单易用的金融数据获取接口。

## 安装

### 通过pip安装（推荐）

```bash
pip install funchodata
```


## 快速开始

### 基本使用

```python
import fc

# 设置API密钥
fc.set_token('your_api_key_here')

# 获取数据
df = fc.get_df('para_main')
print(df.head())
```

### 带参数查询

```python
import fc

# 设置API密钥
fc.set_token('your_api_key_here')

# 指定查询参数和返回字段
params = {
    'page': '1',
    'size': '200',
    'para_clas_cd': 'BOND'
}

fields = ['id', 'para_clas_cd', 'para_name']

df = fc.get_df('para_main', params=params, fields=fields)
print(df.head())
```

### 获取所有分页数据

```python
import fc

fc.set_token('your_api_key_here')

# 自动获取所有分页数据
df_all = fc.get_all_pages('para_main', params={'para_clas_cd': 'BOND'})
print(f"总共获取 {len(df_all)} 条数据")
```

## API参考

### 主要函数

#### `fc.set_token(token)`
设置API密钥

**参数:**
- `token` (str): 由平台分配的API密钥

#### `fc.get_df(form_code, params=None, fields=None, **kwargs)`
获取DataFrame格式的数据

**参数:**
- `form_code` (str): 表单编码
- `params` (dict, optional): 查询参数，包含分页和筛选条件
- `fields` (list, optional): 需要返回的字段列表
- `**kwargs`: 其他查询参数

**返回:**
- `pandas.DataFrame`: 查询结果数据框

#### `fc.get_json(form_code, params=None, fields=None, **kwargs)`
获取JSON格式的原始数据

**参数:**
- `form_code` (str): 表单编码  
- `params` (dict, optional): 查询参数
- `fields` (list, optional): 需要返回的字段列表
- `**kwargs`: 其他查询参数

**返回:**
- `dict`: JSON格式的原始数据

#### `fc.get_all_pages(form_code, params=None, fields=None, max_pages=None)`
自动获取所有分页数据

**参数:**
- `form_code` (str): 表单编码
- `params` (dict, optional): 查询参数
- `fields` (list, optional): 需要返回的字段列表  
- `max_pages` (int, optional): 最大页数限制

**返回:**
- `pandas.DataFrame`: 所有页面的合并数据

### 配置函数

#### `fc.set_base_url(base_url)`
设置API基础URL（仅支持生产环境）

**参数:**
- `base_url` (str): 基础URL，仅支持生产环境 `https://www.funchodata.com`

## 使用示例

### 示例1：基本数据获取

```python
import fc

# 设置API密钥
fc.set_token('f80169d28d7c4094bbd057dde56753b8')

# 获取参数主表数据
df = fc.get_df('para_main', params={'page': '1', 'size': '50'})
print(f"获取到 {len(df)} 条数据")
print(df.columns.tolist())  # 查看所有列名
```

### 示例2：条件查询

```python
import fc

fc.set_token('your_api_key')

# 根据参数类别查询
df = fc.get_df('para_main', 
               params={'para_clas_cd': 'STOCK', 'size': '100'},
               fields=['id', 'para_clas_cd', 'para_name', 'para_value'])

print(df.head())
```

### 示例3：批量获取数据

```python
import fc

fc.set_token('your_api_key')

# 获取多个表单的数据
form_codes = ['para_main', 'market_data', 'company_info']
data_dict = {}

for code in form_codes:
    try:
        data_dict[code] = fc.get_df(code, params={'size': '200'})
        print(f"{code}: {len(data_dict[code])} 条数据")
    except Exception as e:
        print(f"获取 {code} 数据失败: {e}")
```

### 示例4：错误处理

```python
import fc
from fc.exceptions import AuthenticationError, APIError

fc.set_token('your_api_key')

try:
    df = fc.get_df('non_existent_form')
except AuthenticationError as e:
    print(f"认证错误: {e}")
except APIError as e:
    print(f"API错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```


## 常见问题

### Q: 如何获取API密钥？
A: 请联系FunchoData平台管理员获取API密钥。

### Q: 支持哪些Python版本？
A: 支持Python 3.6及以上版本。

### Q: 如何查看可用的表单编码？
A: 请参考FunchoData平台文档或联系技术支持。

### Q: 数据更新频率如何？
A: 数据更新频率取决于具体的数据源，请参考平台文档。

### Q: 有请求频率限制吗？
A: 具体的请求频率限制请参考您的API密钥权限设置。

## 技术支持

- 官网: https://www.funchodata.com

## 更新日志

### v1.0.0 (2025-10-15)
- 首个正式版本发布
- 支持简洁的API调用方式：`import fc; df = fc.get_df()`
- 支持多种数据格式：DataFrame、JSON
- 支持分页查询和字段筛选
- 支持自动获取所有分页数据
- 完善的错误处理机制

## 许可证

MIT License
