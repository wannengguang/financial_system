import time

import streamlit as st
import pandas as pd
import sys
import os

# 设置路径和常量
BASE_DIR = os.path.dirname(__file__)
ACCOUNT_DATA_FILE = os.path.join(BASE_DIR, "account_data.csv")
ACCOUNT_NAMES = [
    "瑞东", "李磊", "玉坚", "上海恺玥", "北京迎皇",
    "上海艺禹", "安徽麦金利", "安徽领空传媒", "临沂道辰"
]

# 初始化session state
def init_session_data():
    if 'account_data' not in st.session_state:
        st.session_state.account_data = pd.DataFrame({
            '账户名称': ACCOUNT_NAMES,
            '期初余额': [0.0] * len(ACCOUNT_NAMES),  # 默认期初余额为0
        })
    return st.session_state.account_data

if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = None  # 'add' | 'edit' | None
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None


def save_account_data(df=None):
    """
    保存账户数据到文件
    参数:
        df: 要保存的DataFrame，如果为None则使用session_state中的数据
    """
    if df is None:
        if 'account_data' in st.session_state:
            df = st.session_state.account_data
        else:
            raise ValueError("没有可保存的账户数据")

    try:
        # 确保数据目录存在
        os.makedirs(os.path.dirname(ACCOUNT_DATA_FILE), exist_ok=True)

        # 保存到CSV文件
        df.to_csv(ACCOUNT_DATA_FILE, index=False, encoding='utf-8-sig')

        st.toast("账户数据保存成功!", icon="✅")
        time.sleep(0.5)
    except Exception as e:
        st.error(f"保存账户数据失败: {str(e)}")
        raise

def load_account_data():
    if os.path.exists(ACCOUNT_DATA_FILE):
        return pd.read_csv(ACCOUNT_DATA_FILE, parse_dates=['账户名称'])
    else:
        df = init_session_data()
        df.to_csv(ACCOUNT_DATA_FILE, index=False)
        return df
    # """从CSV加载账户数据"""
    # try:
    #     st.session_state.account_data = pd.read_csv(ACCOUNT_DATA_FILE)
    # except FileNotFoundError:
    #     st.session_state.account_data = pd.DataFrame({
    #         '账户名称': ACCOUNT_NAMES,
    #         '期初余额': [0.0] * len(ACCOUNT_NAMES),
    #     })

