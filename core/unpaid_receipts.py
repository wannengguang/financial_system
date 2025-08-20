import pandas as pd
import streamlit as st
from datetime import datetime
from core.db import get_conn

_conn = get_conn()

# ------------------------------------------------------------------------------
# 1. 初始化空 DataFrame（英文列名）
# ------------------------------------------------------------------------------
def init_data():
    return pd.DataFrame(columns=[
        'date', 'voucher_number', 'project_name',
        'amount_of_income', 'amount_of_expense',
        'account_name', 'client_name', 'manager', 'use_case'
    ])

# ------------------------------------------------------------------------------
# 2. 读写函数（SQLite 版，完全对齐英文）
# ------------------------------------------------------------------------------
def load_unpaid_data():
    try:
        df = pd.read_sql_query("SELECT * FROM unpaid_financial_data", _conn)
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception:
        return init_data()

def save_unpaid_data(df: pd.DataFrame):
    _conn.execute("DELETE FROM unpaid_financial_data")
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    df.to_sql("unpaid_financial_data", _conn, if_exists="append", index=False, method="multi")
    _conn.commit()
    st.cache_data.clear()

# ------------------------------------------------------------------------------
# 3. 表单/展示逻辑：仅把返回/接收的 dict key 换成英文
# ------------------------------------------------------------------------------
def add_unpaid_form():
    with st.form("add_form_key"):
        cols = st.columns(2)
        date    = pd.Timestamp(st.date_input("日期*", datetime.now()))
        project = cols[1].text_input("项目名称*", "")

        cols = st.columns(3)
        income  = cols[0].number_input("收入金额", 0.0)
        expense = cols[1].number_input("支出金额", 0.0)
        accounts = ["瑞东","李磊","玉坚","上海恺玥","北京迎皇",
                    "上海艺禹","安徽麦金利","安徽领空传媒","临沂道辰"]
        account = cols[2].selectbox("使用账户*", accounts)

        client   = st.text_input("客户名称", "")
        manager  = st.text_input("经办人*", "")
        use_case = st.text_input("用途", "")

        cols = st.columns(2)
        with cols[0]:
            submitted = st.form_submit_button("✅ 保存记录")
        with cols[1]:
            close_clicked = st.form_submit_button("❌ 关闭", type="secondary")

        if submitted:
            if not all([project, account, manager]):
                st.error("带*的字段为必填项")
                st.stop()
            return {
                'date': date,
                'voucher_number': f"C-{int(load_unpaid_data().shape[0]) + 1:04d}",
                'project_name': project,
                'amount_of_income': income,
                'amount_of_expense': expense,
                'account_name': account,
                'client_name': client,
                'manager': manager,
                'use_case': use_case
            }

        if close_clicked:
            st.session_state.mode = None
            st.rerun()
    return None

def edit_unpaid_form(default):
    with st.form("edit_form_key"):
        cols = st.columns(2)
        date    = pd.Timestamp(st.date_input("日期*", default['date'].date()))
        project = cols[1].text_input("项目名称*", default['project_name'])

        cols = st.columns(3)
        income  = cols[0].number_input("收入金额", value=float(default['amount_of_income']))
        expense = cols[1].number_input("支出金额", value=float(default['amount_of_expense']))
        accounts = ["瑞东","李磊","玉坚","上海恺玥","北京迎皇",
                    "上海艺禹","安徽麦金利","安徽领空传媒","临沂道辰"]
        acc_idx = accounts.index(default['account_name'])
        account = cols[2].selectbox("使用账户*", accounts, index=acc_idx)

        client   = st.text_input("客户名称",  default['client_name'])
        manager  = st.text_input("经办人*", default['manager'])

        if st.form_submit_button("保存记录"):
            return {
                'date': date,
                'project_name': project,
                'amount_of_income': income,
                'amount_of_expense': expense,
                'account_name': account,
                'client_name': client,
                'manager': manager,
                'use_case': default['use_case']
            }
    return None