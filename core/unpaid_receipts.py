import pandas as pd
import streamlit as st
from datetime import datetime
import os
from core.paid_receipts import init_data

# 文件存储路径
# BASE_DIR = os.path.dirname(__file__)
# UNPAID_DATA_FILE = os.path.join(BASE_DIR, "unpaid_financial_data.csv")
UNPAID_DATA_FILE = r"D:\Pycharm_project\financial_system\data\unpaid_financial_data.csv"


def load_unpaid_data():
    """加载或创建数据文件"""
    if os.path.exists(UNPAID_DATA_FILE):
        return pd.read_csv(UNPAID_DATA_FILE, parse_dates=['日期'])
    else:
        df = init_data()
        df.to_csv(UNPAID_DATA_FILE, index=False)
        return df

def save_unpaid_data(df):
    df.to_csv(UNPAID_DATA_FILE, index=False)
    st.cache_data.clear()

def add_unpaid_form():
    with st.form("add_form_key"):          # ← 纯字符串，永不变化
        cols = st.columns(2)
        date    = pd.Timestamp(st.date_input("日期*", datetime.now()))
        project = cols[1].text_input("项目名称*", "")

        cols = st.columns(3)
        income  = cols[0].number_input("收入金额", 0.0)
        expense = cols[1].number_input("支出金额", 0.0)
        accounts = ["瑞东","李磊","玉坚","上海恺玥","北京迎皇",
                    "上海艺禹","安徽麦金利","安徽领空传媒","临沂道辰"]
        account = cols[2].selectbox("使用账户*", accounts)

        client  = st.text_input("客户名称", "")
        operator= st.text_input("经办人*", "")
        purpose = st.text_input("用途", "")

        cols = st.columns(2)
        with cols[0]:
            submitted = st.form_submit_button("✅ 保存记录")  # 表单提交按钮
        with cols[1]:
            # 注意：表单内的普通按钮需要用特殊方式处理
            close_clicked = st.form_submit_button("❌ 关闭", type="secondary")
        if submitted:
            if not all([project, account, operator]):
                st.error("带*的字段为必填项")
                st.stop()
            return {
                '日期': date, '项目名称': project,
                '收入金额': income, '支出金额': expense,
                '使用账户': account, '客户名称': client,
                '经办人': operator, '用途': purpose
            }

            # 处理关闭逻辑
        if close_clicked:
            st.session_state.mode = None  # 或 st.session_state.add_dialog = False
            st.rerun()
    return None

def edit_unpaid_form(default):
    with st.form("edit_form_key"):         # ← 纯字符串，永不变化
        cols = st.columns(2)
        date = pd.Timestamp(st.date_input("日期*", default['日期'].date()))
        project = cols[1].text_input("项目名称*", default['项目名称'])

        cols = st.columns(3)
        income  = cols[0].number_input("收入金额", value=float(default['收入金额']))
        expense = cols[1].number_input("支出金额", value=float(default['支出金额']))
        accounts = ["瑞东","李磊","玉坚","上海恺玥","北京迎皇",
                    "上海艺禹","安徽麦金利","安徽领空传媒","临沂道辰"]
        acc_idx = accounts.index(default['使用账户'])
        account = cols[2].selectbox("使用账户*", accounts, index=acc_idx)

        client  = st.text_input("客户名称",  default['客户名称'])
        operator= st.text_input("经办人*", default['经办人'])
        purpose = st.text_input("用途", default['用途'])
        if st.form_submit_button("保存记录"):
            return {
                '日期': date, '项目名称': project, '收入金额': income,
                '支出金额': expense, '使用账户': account,
                '客户名称': client, '经办人': operator, '用途':purpose,
            }
    return None