import time
import streamlit as st
import pandas as pd
from core.db import get_conn


ACCOUNT_NAMES = [
    "瑞东", "李磊", "玉坚", "上海恺玥", "北京迎皇",
    "上海艺禹", "安徽麦金利", "安徽领空传媒", "临沂道辰"
]

_conn = get_conn()

# ------------------ 数据加载 ------------------
def load_account_data() -> pd.DataFrame:
    """从 SQLite 读取账户余额表"""
    df = pd.read_sql_query("SELECT * FROM account_data ORDER BY account_name", _conn)
    if df.empty:                     # 首次启动 → 用默认值
        df = pd.DataFrame({
            "account_name": ACCOUNT_NAMES,
            "opening_balance": [0.0] * len(ACCOUNT_NAMES),
            "amount_of_income": [0.0] * len(ACCOUNT_NAMES),
            "amount_of_expense": [0.0] * len(ACCOUNT_NAMES),
            "difference":    [0.0] * len(ACCOUNT_NAMES)
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