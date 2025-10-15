"""
FunchoData SDK基本使用示例
"""

import fc

def main():
    # 设置API密钥
    print("设置API密钥...")
    fc.set_token('your_api_key_here')  # 请替换为您的API密钥
    
    # 示例1：基本数据获取
    print("\n=== 示例1：基本数据获取 ===")
    try:
        df = fc.get_df('para_main', params={'page': '1', 'size': '10'})
        print(f"获取到 {len(df)} 条数据")
        print("列名:", df.columns.tolist())
        print("前5行数据:")
        print(df.head())
    except Exception as e:
        print(f"错误: {e}")
    
    # 示例2：指定字段查询
    print("\n=== 示例2：指定字段查询 ===")
    try:
        params = {
            'page': '1',
            'size': '5',
            'para_clas_cd': ''
        }
        fields = ['id', 'para_clas_cd']
        
        df = fc.get_df('para_main', params=params, fields=fields)
        print(f"获取到 {len(df)} 条数据")
        print(df)
    except Exception as e:
        print(f"错误: {e}")
    
    # 示例3：获取JSON格式数据
    print("\n=== 示例3：获取JSON格式数据 ===")
    try:
        data = fc.get_json('para_main', params={'page': '1', 'size': '3'})
        print("JSON数据结构:")
        print(f"- success: {data.get('success', 'N/A')}")
        print(f"- message: {data.get('message', 'N/A')}")
        print(f"- data count: {len(data.get('data', []))}")
        if data.get('data'):
            print("第一条数据:", data['data'][0])
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main() 