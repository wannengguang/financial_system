
import io
from datetime import datetime

import pandas as pd
import streamlit as st
from core.account_statistics import load_account_data,save_account_data,ACCOUNT_NAMES
from core.project_statistics import project_stats
from core.monthly_statistics import monthly_stats
from core.paid_receipts import load_paid_data,save_paid_data,add_paid_form,edit_paid_form
from core.unpaid_receipts import load_unpaid_data,save_unpaid_data,add_unpaid_form,edit_unpaid_form
from core.permission import login_page

def export_data(df):
    """添加数据导出功能"""
    st.sidebar.markdown("### 导出数据")

    # CSV导出
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button(
        label="导出CSV",
        data=csv,
        file_name="账户数据.csv",
        mime="text/csv",
        help="导出为CSV格式（支持中文）"
    )

    # Excel导出
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    st.sidebar.download_button(
        label="导出Excel",
        data=excel_buffer.getvalue(),
        file_name="账户数据.xlsx",
        mime="application/vnd.ms-excel",
        help="导出为Excel格式"
    )

def show_paid():
    # st.header("每日收支记录")
    # ---------- 侧边栏筛选 -----------
    st.sidebar.header("🔍 查询")
    df_all = load_paid_data()
    accounts = df_all['使用账户'].unique().tolist() if not df_all.empty else []
    projects = df_all['项目名称'].unique().tolist() if not df_all.empty else []
    operator = df_all['经办人'].unique().tolist() if not df_all.empty else []
    sel_account = st.sidebar.selectbox("按账户筛选", ["全部"] + accounts)
    sel_project = st.sidebar.selectbox("按项目名称筛选", ["全部"] + projects)
    sel_operator = st.sidebar.selectbox("按经办人筛选", ["全部"] + operator)
    date_range = st.sidebar.date_input("按日期区间", value=[], key="daterange")
    # ---------- 构造过滤后的表 -----------
    df_show = df_all.copy()  # 先复制，避免空表布尔索引报错
    if not df_show.empty:
        if sel_account != "全部":
            df_show = df_show[df_show['使用账户'] == sel_account]
        if sel_project != "全部":
            df_show = df_show[df_show['项目名称'] == sel_project]
        if sel_operator != "全部":
            df_show = df_show[df_show['经办人'] == sel_operator]
        if len(date_range) == 2:
            start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
            df_show = df_show[(df_show['日期'] >= start) & (df_show['日期'] <= end)]
    # 日期仅保留年月日（字符串）
    # df_show = df_show.dropna(subset=['日期'])
    print(df_show['日期'].dtype)
    print(df_show['日期'].head())
    # df_show['日期'] = pd.to_datetime(df_show['日期'], errors='coerce')
    if not df_show.empty and '日期' in df_show.columns:
        df_show['日期'] = df_show['日期'].dt.strftime('%Y-%m-%d')
    # ---------- 展示表格 -----------
    real_idx = None
    if df_show.empty:
        st.info("暂无记录")
    else:
        selected = st.dataframe(
            df_show,
            hide_index=True,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row",
        )
        idx = selected["selection"]["rows"][0] if selected["selection"]["rows"] else None
        # real_idx = df_all.index[df_all.index.isin(df_show.index)][idx] if idx is not None else None
        real_idx = df_show.index[idx] if idx is not None else None
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("➕ 新增"):
            st.session_state.mode = "add"
    with col2:
        if real_idx is not None and st.button("✏️ 修改"):
            st.session_state.mode = "edit"
            st.session_state.edit_idx = real_idx
    with col3:
        if real_idx is not None and st.button("🗑️ 删除"):
            df_all = df_all.drop(index=real_idx).reset_index(drop=True)
            save_paid_data(df_all)
            st.rerun()
    with col4:
        if not df_show.empty and st.button("📤 导出Excel"):
            # 创建内存中的Excel文件
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_show.to_excel(writer, index=False, sheet_name='收支记录')
            # 创建下载按钮
            st.download_button(
                label="下载Excel文件",
                data=output.getvalue(),
                file_name=f"收支记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    # st.write(f"Debug - real_idx: {real_idx}")
    if st.session_state.get("mode") == "add":
        st.subheader("➕ 新增记录")
        new_data = add_paid_form()
        if new_data:
            new_data['凭证号'] = f"C-{len(df_all) + 1:04d}"
            df_all = pd.concat([df_all, pd.DataFrame([new_data])], ignore_index=True)
            save_paid_data(df_all)
            st.success("已添加！")
            st.session_state.mode = None
            st.rerun()


    if st.session_state.get("mode") == "edit":
        st.subheader("✏️ 修改记录")
        idx = st.session_state.edit_idx
        edit_data = edit_paid_form(default=df_all.loc[idx])
        if edit_data:
            for k, v in edit_data.items():
                df_all.at[idx, k] = v
            save_paid_data(df_all)
            st.success("已更新！")
            st.session_state.mode = None
            st.rerun()

def show_unpaid():
    # ---------- 侧边栏筛选 -----------
    st.sidebar.header("🔍 查询")
    df_all = load_unpaid_data()
    accounts = df_all['使用账户'].unique().tolist() if not df_all.empty else []
    projects = df_all['项目名称'].unique().tolist() if not df_all.empty else []
    operator = df_all['经办人'].unique().tolist() if not df_all.empty else []
    sel_account = st.sidebar.selectbox("按账户筛选", ["全部"] + accounts)
    sel_project = st.sidebar.selectbox("按项目名称筛选", ["全部"] + projects)
    sel_operator = st.sidebar.selectbox("按经办人筛选", ["全部"] + operator)
    date_range = st.sidebar.date_input("按日期区间", value=[], key="daterange")
    # ---------- 构造过滤后的表 -----------
    df_show = df_all.copy()  # 先复制，避免空表布尔索引报错
    if not df_show.empty:
        if sel_account != "全部":
            df_show = df_show[df_show['使用账户'] == sel_account]
        if sel_project != "全部":
            df_show = df_show[df_show['项目名称'] == sel_project]
        if sel_operator != "全部":
            df_show = df_show[df_show['经办人'] == sel_operator]
        if len(date_range) == 2:
            start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
            df_show = df_show[(df_show['日期'] >= start) & (df_show['日期'] <= end)]
    # 日期仅保留年月日（字符串）
    # df_show = df_show.dropna(subset=['日期'])
    print(df_show['日期'].dtype)
    print(df_show['日期'].head())
    # df_show['日期'] = pd.to_datetime(df_show['日期'], errors='coerce')
    if not df_show.empty and '日期' in df_show.columns:
        df_show['日期'] = df_show['日期'].dt.strftime('%Y-%m-%d')
    # ---------- 展示表格 -----------
    real_idx = None
    if df_show.empty:
        st.info("暂无记录")
    else:
        selected = st.dataframe(
            df_show,
            hide_index=True,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row",
        )
        idx = selected["selection"]["rows"][0] if selected["selection"]["rows"] else None
        # real_idx = df_all.index[df_all.index.isin(df_show.index)][idx] if idx is not None else None
        real_idx = df_show.index[idx] if idx is not None else None
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("➕ 新增"):
            st.session_state.mode = "add"
    with col2:
        if real_idx is not None and st.button("✏️ 修改"):
            st.session_state.mode = "edit"
            st.session_state.edit_idx = real_idx
    with col3:
        if real_idx is not None and st.button("🗑️ 删除"):
            df_all = df_all.drop(index=real_idx).reset_index(drop=True)
            save_unpaid_data(df_all)
            st.rerun()
    with col4:
        if not df_show.empty and st.button("📤 导出Excel"):
            # 创建内存中的Excel文件
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_show.to_excel(writer, index=False, sheet_name='收支记录')
            # 创建下载按钮
            st.download_button(
                label="下载Excel文件",
                data=output.getvalue(),
                file_name=f"收支记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    # st.write(f"Debug - real_idx: {real_idx}")
    if st.session_state.get("mode") == "add":
        st.subheader("➕ 新增记录")
        new_data = add_unpaid_form()
        if new_data:
            new_data['凭证号'] = f"W-{len(df_all) + 1:04d}"
            df_all = pd.concat([df_all, pd.DataFrame([new_data])], ignore_index=True)
            save_unpaid_data(df_all)
            st.success("已添加！")
            st.session_state.mode = None
            st.rerun()

    if st.session_state.get("mode") == "edit":
        st.subheader("✏️ 修改记录")
        idx = st.session_state.edit_idx
        edit_data = edit_unpaid_form(default=df_all.loc[idx])
        if edit_data:
            for k, v in edit_data.items():
                df_all.at[idx, k] = v
            save_unpaid_data(df_all)
            st.success("已更新！")
            st.session_state.mode = None
            st.rerun()


def show_account(df):
    """账户管理页面（含期初余额、收入、支出和差额）"""
    # 初始化session state（确保包含所有必要列）
    if 'account_data' not in st.session_state:
        st.session_state.account_data = load_account_data()

        # 确保包含所有必要列
        required_columns = ['账户名称', '期初余额', '收入金额', '支出金额', '差额']
        for col in required_columns:
            if col not in st.session_state.account_data.columns:
                if col == '账户名称':
                    st.session_state.account_data[col] = ""
                else:
                    st.session_state.account_data[col] = 0.0

    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = None
    if 'edit_index' not in st.session_state:
        st.session_state.edit_index = None

    # 主功能区
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("账户资金统计")
    with col2:
        if st.button("➕ 新增账户", use_container_width=True):
            st.session_state.edit_mode = "add"
            st.session_state.edit_index = None

    # -------------------------------------------------
    # 1) 重新统计：只计算当前 df 里出现的账户
    # -------------------------------------------------
    if not df.empty and {'使用账户', '收入金额', '支出金额'}.issubset(df.columns):
        # 1.1 本次涉及的账户及其最新收支
        new_stats = (df
                     .groupby('使用账户', as_index=False)
                     .agg({'收入金额': 'sum', '支出金额': 'sum'}))

        # 1.2 把 DataFrame 转成“账户->金额”的字典，方便快速查找
        inc_dict = dict(zip(new_stats['使用账户'], new_stats['收入金额']))
        exp_dict = dict(zip(new_stats['使用账户'], new_stats['支出金额']))

        # 1.3 只更新这些账户
        mask = st.session_state.account_data['账户名称'].isin(inc_dict.keys())
        st.session_state.account_data.loc[mask, '收入金额'] = (
            st.session_state.account_data.loc[mask, '账户名称'].map(inc_dict)
        )
        st.session_state.account_data.loc[mask, '支出金额'] = (
            st.session_state.account_data.loc[mask, '账户名称'].map(exp_dict)
        )

    # -------------------------------------------------
    # 2) 如果某个账户在 df 里完全消失了（被删光）
    #    需要把它的收入/支出置 0
    # -------------------------------------------------
    all_accounts_in_df = set(df['使用账户']) if not df.empty else set()
    mask_missing = ~st.session_state.account_data['账户名称'].isin(all_accounts_in_df)
    st.session_state.account_data.loc[mask_missing, ['收入金额', '支出金额']] = 0.0

    # -------------------------------------------------
    # 3) 统一重新计算差额（只做一次）
    # -------------------------------------------------
    st.session_state.account_data['差额'] = (
            st.session_state.account_data['期初余额'] +
            st.session_state.account_data['收入金额'] -
            st.session_state.account_data['支出金额']
    )

    # 显示可编辑表格
    edited_df = st.data_editor(
        st.session_state.account_data,
        column_config={
            "期初余额": st.column_config.NumberColumn(
                "期初余额",
                format="%.2f ¥",
                min_value=0,
                step=0.01
            ),
            "收入金额": st.column_config.NumberColumn(
                "收入",
                format="%.2f ¥",
                disabled=True
            ),
            "支出金额": st.column_config.NumberColumn(
                "支出",
                format="%.2f ¥",
                disabled=True
            ),
            "差额": st.column_config.NumberColumn(
                "差额",
                format="%.2f ¥",
                disabled=True
            )
        },
        disabled=["账户名称", "收入金额", "支出金额", "差额"],
        hide_index=True,
        use_container_width=True,
        key="account_editor"
    )

    # 保存修改（只允许修改期初余额）
    if not st.session_state.account_data.equals(edited_df):
        try:
            # 只更新期初余额列
            st.session_state.account_data['期初余额'] = edited_df['期初余额']

            # 重新计算差额
            st.session_state.account_data['差额'] = (
                    st.session_state.account_data['期初余额'] +
                    st.session_state.account_data.get('收入金额', 0) -
                    st.session_state.account_data.get('支出金额', 0)
            )

            save_account_data(st.session_state.account_data)
            st.rerun()
        except Exception as e:
            st.error(f"保存数据时出错: {str(e)}")

    # 新增/编辑表单弹窗
    if st.session_state.edit_mode in ["add", "edit"]:
        with st.form(key="account_form"):
            title = "➕ 新增账户" if st.session_state.edit_mode == "add" else "✏️ 编辑账户"
            st.subheader(title)

            # 获取当前账户数据（编辑模式）
            current_data = {}
            if st.session_state.edit_mode == "edit":
                current_data = st.session_state.account_data.iloc[st.session_state.edit_index].to_dict()

            # 表单字段
            account_name = st.text_input(
                "账户名称*",
                value=current_data.get('账户名称', ''),
                placeholder="输入账户名称"
            )

            init_balance = st.number_input(
                "期初余额*",
                min_value=0.0,
                value=float(current_data.get('期初余额', 0.0)),
                format="%.2f",
                step=0.01
            )

            # 按钮布局
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("✅ 确认")
            with col2:
                cancel = st.form_submit_button("❌ 取消")

            if submit:
                if not account_name:
                    st.error("账户名称不能为空")
                else:
                    new_data = {
                        "账户名称": account_name,
                        "期初余额": init_balance,
                        "收入金额": current_data.get('收入金额', 0.0),
                        "支出金额": current_data.get('支出金额', 0.0),
                        "差额": init_balance  # 初始差额=期初余额
                    }

                    if st.session_state.edit_mode == "add":
                        st.session_state.account_data = pd.concat([
                            st.session_state.account_data,
                            pd.DataFrame([new_data])
                        ], ignore_index=True)
                    else:
                        st.session_state.account_data.iloc[st.session_state.edit_index] = new_data

                    save_account_data(st.session_state.account_data)
                    st.session_state.edit_mode = None
                    st.rerun()

            if cancel:
                st.session_state.edit_mode = None
                st.rerun()

    st.sidebar.header("数据导出")
    export_format = st.sidebar.radio(
        "导出格式",
        ["CSV", "Excel", "JSON"],
        horizontal=True
    )

    if st.sidebar.button("生成导出文件"):
        with st.spinner("正在生成文件..."):
            try:
                if export_format == "CSV":
                    csv = st.session_state.account_data.to_csv(index=False).encode('utf-8-sig')
                    st.sidebar.download_button(
                        label="下载CSV",
                        data=csv,
                        file_name="账户数据.csv",
                        mime="text/csv"
                    )

                elif export_format == "Excel":
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        st.session_state.account_data.to_excel(writer, index=False, sheet_name='账户数据')
                    st.sidebar.download_button(
                        label="下载Excel",
                        data=output.getvalue(),
                        file_name="账户数据.xlsx",
                        mime="application/vnd.ms-excel"
                    )

                elif export_format == "JSON":
                    json_str = st.session_state.account_data.to_json(orient='records', force_ascii=False)
                    st.sidebar.download_button(
                        label="下载JSON",
                        data=json_str,
                        file_name="账户数据.json",
                        mime="application/json"
                    )

            except Exception as e:
                st.error(f"导出失败: {str(e)}")


def run_main():
    # 鉴权
    st.write(f"欢迎，{st.session_state['username']}（{st.session_state['role']}）")

    # 加载数据
    df = load_paid_data()
    st.sidebar.title("财务管理系统")
    if st.sidebar.button("💰 已收支记录", use_container_width=True):
        st.session_state.current_page = "paid_record"
    if st.sidebar.button("⏳ 未收支记录", use_container_width=True):
        st.session_state.current_page = "unpaid_record"
    if st.sidebar.button("📊 账户统计", use_container_width=True):
        st.session_state.current_page = "account_stats"
    if st.sidebar.button("📈 项目统计", use_container_width=True):
        st.session_state.current_page = "project_stats"
    if st.sidebar.button("🗓️ 月度统计", use_container_width=True):
        st.session_state.current_page = "monthly_stats"


    # 判断目录
    if st.session_state.current_page == "paid_record":
        st.set_page_config(page_title="已收支记录", layout="wide")
        st.title("💰已收支记录")
        show_paid()

    elif st.session_state.current_page == "unpaid_record":
        st.set_page_config(page_title="未收支记录", layout="wide")
        st.title("⏳未收支记录")
        show_unpaid()
    # 各统计报表
    elif st.session_state.current_page == "account_stats":
        st.set_page_config(page_title="账户统计", layout="wide")
        # stats = account_stats(df)
        # st.dataframe(stats)
        show_account(df)
        # 可视化图表
        # st.bar_chart(stats.set_index('账户名称')['余额'])

    elif st.session_state.current_page == "project_stats":
        st.set_page_config(page_title="项目统计", layout="wide")
        st.header("项目盈亏统计")
        stats = project_stats(df)
        st.dataframe(stats)

        # 显示盈利/亏损项目
        col1, col2 = st.columns(2)
        col1.metric("盈利项目数", len(stats[stats['差额'] > 0]))
        col2.metric("亏损项目数", len(stats[stats['差额'] < 0]))

    elif st.session_state.current_page == "monthly_stats":
        st.set_page_config(page_title="月度统计", layout="wide")
        st.header("月度收支统计")
        stats = monthly_stats(df)
        st.dataframe(stats)

        # 显示最新月份数据
        if not stats.empty:
            latest = stats.iloc[-1]
            col1, col2, col3 = st.columns(3)
            col1.metric("月份", latest['月份'])
            col2.metric("总收入", f"¥{latest['收入金额']:,.2f}")
            col3.metric("净利润", f"¥{latest['差值']:,.2f}",
                        delta_color="inverse" if latest['差值'] < 0 else "normal")

def main():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        login_page()
        st.stop()  # ⚠️ 关键：阻止后续页面加载
    else:
        run_main()