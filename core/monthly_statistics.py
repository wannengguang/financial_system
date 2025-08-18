import pandas as pd
import sys, os


def monthly_stats(df):
    """月度统计表"""
    if df.empty:
        return pd.DataFrame(columns=['月份', '收入', '支出', '差值'])
    df = df.copy()
    # 1) 确保日期列是 datetime
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    # 2) 去掉非法日期
    df = df.dropna(subset=['日期'])
    df['月份'] = df['日期'].dt.to_period('M')
    stats = df.groupby('月份').agg({
        '收入金额': 'sum',
        '支出金额': 'sum'
    }).reset_index()

    stats['差值'] = stats['收入金额'] - stats['支出金额']
    stats['月份'] = stats['月份'].astype(str)
    return stats