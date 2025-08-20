import pandas as pd
import sys, os
from sqlalchemy import text
from core.db import engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def project_stats(df):
    """项目统计表"""
    """项目统计表：直接查库，不依赖传进来的 df"""
    sql = """
          SELECT project_name AS 项目名称,
                 SUM(amount_of_income)                 AS 收入,
                 SUM(amount_of_expense)                 AS 支出,
                 SUM(amount_of_income) - SUM(amount_of_expense) AS 差额
          FROM paid_financial_data
          GROUP BY project_name
          """
    return pd.read_sql(text(sql), engine)