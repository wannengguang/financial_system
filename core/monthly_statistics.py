# import pandas as pd
# import sys, os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
#
# def monthly_stats(df):
#     """月度统计表"""
#     if df.empty:
#         return pd.DataFrame(columns=['月份', '收入', '支出', '差值'])
#     df = df.copy()
#     # 1) 确保日期列是 datetime
#     df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
#     # 2) 去掉非法日期
#     df = df.dropna(subset=['日期'])
#     df['月份'] = df['日期'].dt.to_period('M')
#     stats = df.groupby('月份').agg({
#         '收入金额': 'sum',
#         '支出金额': 'sum'
#     }).reset_index()
#
#     stats['差值'] = stats['收入金额'] - stats['支出金额']
#     stats['月份'] = stats['月份'].astype(str)
#     return stats

import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.db import get_conn   # 复用前面封装的连接函数

def monthly_stats():
    """
    从数据库 unpaid_financial_data 表中读取数据，返回月度统计
    返回值：DataFrame[月份, 收入, 支出, 差值]
    """
    conn = get_conn()
    try:
        df = pd.read_sql_query(
            "SELECT date, amount_of_income, amount_of_expense FROM paid_financial_data",
            conn
        )
    except Exception:
        # 表不存在或查询失败时返回空表
        return pd.DataFrame(columns=['月份', '收入', '支出', '差值'])

    if df.empty:
        return pd.DataFrame(columns=['月份', '收入', '支出', '差值'])

    # 日期列转 datetime
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    # 生成月份分组
    df['月份'] = df['date'].dt.to_period('M')
    stats = (
        df.groupby('月份')
          .agg({'amount_of_income': 'sum', 'amount_of_expense': 'sum'})
          .reset_index()
    )

    stats.columns = ['月份', '收入', '支出']
    stats['差值'] = stats['收入'] - stats['支出']
    stats['月份'] = stats['月份'].astype(str)

    return stats[['月份', '收入', '支出', '差值']]