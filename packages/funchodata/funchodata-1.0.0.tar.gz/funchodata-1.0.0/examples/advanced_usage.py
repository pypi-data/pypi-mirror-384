"""
FunchoData SDK高级使用示例
"""

import fc
from fc.exceptions import AuthenticationError, APIError
import pandas as pd

def example_error_handling():
    """错误处理示例"""
    print("=== 错误处理示例 ===")
    
    # 测试无效API密钥
    try:
        fc.set_token('invalid_token')
        df = fc.get_df('para_main')
    except AuthenticationError as e:
        print(f"认证错误（预期）: {e}")
    except Exception as e:
        print(f"其他错误: {e}")
    
    # 恢复正确的token
    fc.set_token('your_api_key_here')
    
    # 测试不存在的表单
    try:
        df = fc.get_df('non_existent_form')
    except APIError as e:
        print(f"API错误（预期）: {e}")
    except Exception as e:
        print(f"其他错误: {e}")

def example_pagination():
    """分页查询示例"""
    print("\n=== 分页查询示例 ===")
    
    try:
        # 获取第一页数据
        page1 = fc.get_df('para_main', params={'page': '1', 'size': '5'})
        print(f"第1页: {len(page1)} 条数据")
        
        # 获取第二页数据
        page2 = fc.get_df('para_main', params={'page': '2', 'size': '5'})
        print(f"第2页: {len(page2)} 条数据")
        
        # 合并多页数据
        combined = pd.concat([page1, page2], ignore_index=True)
        print(f"合并后: {len(combined)} 条数据")
        
    except Exception as e:
        print(f"分页查询错误: {e}")

def example_field_selection():
    """字段选择示例"""
    print("\n=== 字段选择示例 ===")
    
    try:
        # 获取所有字段
        df_all = fc.get_df('para_main', params={'page': '1', 'size': '3'})
        print(f"所有字段: {df_all.columns.tolist()}")
        
        # 只获取指定字段
        fields = ['id', 'para_clas_cd']
        df_selected = fc.get_df('para_main', 
                               params={'page': '1', 'size': '3'}, 
                               fields=fields)
        print(f"选择字段: {df_selected.columns.tolist()}")
        print(df_selected)
        
    except Exception as e:
        print(f"字段选择错误: {e}")

def example_data_processing():
    """数据处理示例"""
    print("\n=== 数据处理示例 ===")
    
    try:
        df = fc.get_df('para_main', params={'page': '1', 'size': '20'})
        
        print(f"数据形状: {df.shape}")
        print(f"数据类型:\n{df.dtypes}")
        
        # 数据统计
        if len(df) > 0:
            print(f"数值列统计:")
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                print(df[numeric_cols].describe())
            
            # 分类统计
            categorical_cols = df.select_dtypes(include=['object']).columns
            for col in categorical_cols[:2]:  # 只显示前两个分类列
                print(f"\n{col} 值分布:")
                print(df[col].value_counts().head())
                
    except Exception as e:
        print(f"数据处理错误: {e}")


def main():
    """主函数"""
    print("FunchoData SDK高级使用示例")
    print("=" * 50)
    
    # 设置API密钥
    fc.set_token('your_api_key_here')  # 请替换为您的API密钥
    
    # 运行各种示例
    example_error_handling()
    example_pagination() 
    example_field_selection()
    example_data_processing()

if __name__ == "__main__":
    main() 