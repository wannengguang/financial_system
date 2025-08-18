import streamlit as st

# 用户数据库（可替换为数据库）
USERS = {
    "司敏敏": {"password": "771221", "role": "可编辑用户"},
    "只读账号": {"password": "333333", "role": "只读用户"}
}

# 登录函数
def login(username, password):
    user = USERS.get(username)
    if user and user["password"] == password:
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        st.session_state["role"] = user["role"]
        st.rerun()
    else:
        st.error("❌ 用户名或密码错误")

# 登录页
def login_page():
    st.set_page_config(page_title="财务系统登录页")
    st.title("🔐 请先登录")
    with st.form("login_form"):
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        submitted = st.form_submit_button("登录")
        if submitted:
            login(username, password)