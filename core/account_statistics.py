# import time
#
# import streamlit as st
# import pandas as pd
# import os
#
# # 设置路径和常量
# ACCOUNT_DATA_FILE = r"D:\Pycharm_project\financial_system\data\account_data.csv"
# # BASE_DIR = os.path.dirname(__file__)
# # ACCOUNT_DATA_FILE = os.path.join(BASE_DIR, "account_data.csv")
# ACCOUNT_NAMES = [
#     "瑞东", "李磊", "玉坚", "上海恺玥", "北京迎皇",
#     "上海艺禹", "安徽麦金利", "安徽领空传媒", "临沂道辰"
# ]
#
# # 初始化session state
# def init_session_data():
#     if 'account_data' not in st.session_state:
#         st.session_state.account_data = pd.DataFrame({
#             '账户名称': ACCOUNT_NAMES,
#             '期初余额': [0.0] * len(ACCOUNT_NAMES),  # 默认期初余额为0
#         })
#     return st.session_state.account_data
#
# if 'edit_mode' not in st.session_state:
#     st.session_state.edit_mode = None  # 'add' | 'edit' | None
# if 'edit_index' not in st.session_state:
#     st.session_state.edit_index = None
#
#
# def save_account_data(df=None):
#     """
#     保存账户数据到文件
#     参数:
#         df: 要保存的DataFrame，如果为None则使用session_state中的数据
#     """
#     if df is None:
#         if 'account_data' in st.session_state:
#             df = st.session_state.account_data
#         else:
#             raise ValueError("没有可保存的账户数据")
#
#     try:
#         # 确保数据目录存在
#         os.makedirs(os.path.dirname(ACCOUNT_DATA_FILE), exist_ok=True)
#
#         # 保存到CSV文件
#         df.to_csv(ACCOUNT_DATA_FILE, index=False, encoding='utf-8-sig')
#
#         st.toast("账户数据保存成功!", icon="✅")
#         time.sleep(0.5)
#     except Exception as e:
#         st.error(f"保存账户数据失败: {str(e)}")
#         raise
#
# def load_account_data():
#     if os.path.exists(ACCOUNT_DATA_FILE):
#         return pd.read_csv(ACCOUNT_DATA_FILE, parse_dates=['账户名称'])
#     else:
#         df = init_session_data()
#         df.to_csv(ACCOUNT_DATA_FILE, index=False)
#         return df

import time
import streamlit as st
import pandas as pd
import sqlite3
import os

# ------------------ 路径常量（只改了这一处） ------------------
# 原来是 CSV 路径，现在改成同目录下的 SQLite 文件
ACCOUNT_DATA_FILE = os.path.join(
    os.path.dirname(__file__), "data", "account_data.db"
)
os.makedirs(os.path.dirname(ACCOUNT_DATA_FILE), exist_ok=True)

ACCOUNT_NAMES = [
    "瑞东", "李磊", "玉坚", "上海恺玥", "北京迎皇",
    "上海艺禹", "安徽麦金利", "安徽领空传媒", "临沂道辰"
]

# ------------------ 数据库连接（单例） ------------------
@st.cache_resource
def _get_conn():
    conn = sqlite3.connect(ACCOUNT_DATA_FILE, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS account_data (
            账户名称 TEXT PRIMARY KEY,
            期初余额 REAL,
            收入金额 REAL DEFAULT 0.0,
            支出金额 REAL DEFAULT 0.0,
            差额    REAL
        );
        """
    )
    conn.commit()
    return conn

_conn = _get_conn()

# ------------------ 数据加载 ------------------
def load_account_data() -> pd.DataFrame:
    """从 SQLite 读取账户余额表"""
    df = pd.read_sql_query("SELECT * FROM account_data ORDER BY 账户名称", _conn)
    if df.empty:                     # 首次启动 → 用默认值
        df = pd.DataFrame({
            "账户名称": ACCOUNT_NAMES,
            "期初余额": [0.0] * len(ACCOUNT_NAMES),
            "收入金额": [0.0] * len(ACCOUNT_NAMES),
            "支出金额": [0.0] * len(ACCOUNT_NAMES),
            "差额":    [0.0] * len(ACCOUNT_NAMES)
        })
        save_account_data(df)        # 立即写回
    return df

# ------------------ 数据保存 ------------------
def save_account_data(df=None):
    """把 DataFrame 覆盖写回 SQLite"""
    if df is None:
        df = st.session_state.account_data

    try:
        _conn.execute("DELETE FROM account_data")          # 清空旧数据
        df.to_sql("account_data", _conn, if_exists="append", index=False, method="multi")
        _conn.commit()
        st.toast("账户数据保存成功!", icon="✅")
        time.sleep(0.5)
    except Exception as e:
        st.error(f"保存账户数据失败: {str(e)}")
        raise

# ------------------ session state 初始化 ------------------
def init_session_data():
    if 'account_data' not in st.session_state:
        st.session_state.account_data = load_account_data()
    return st.session_state.account_data

if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = None
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None