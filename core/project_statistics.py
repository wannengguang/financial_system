import pandas as pd
import sys, os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def project_stats(df):
    """项目统计表"""
    if df.empty:
        return pd.DataFrame(columns=['项目名称', '收入', '支出', '差额'])

    stats = df.groupby('项目名称').agg({
        '收入金额': 'sum',
        '支出金额': 'sum'
    }).reset_index()

    stats['差额'] = stats['收入金额'] - stats['支出金额']
    return stats