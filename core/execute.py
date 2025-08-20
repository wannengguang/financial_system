
import io
from datetime import datetime
import pandas as pd
import streamlit as st
from core.account_statistics import load_account_data,save_account_data,ACCOUNT_NAMES
from core.db import engine
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

def paid_mapping():
    COL_EN = ['date', 'voucher_number', 'project_name',
              'amount_of_income', 'amount_of_expense',
              'account_name', 'client_name', 'manager', 'use_case']

    COL_CN = ['日期', '凭证号', '项目名称', '收入金额', '支出金额',
              '使用账户', '客户名称', '经办人', '用途']

    COL_MAP = dict(zip(COL_EN, COL_CN))
    return COL_MAP


def show_paid():
    st.sidebar.header("🔍 查询")
    df_all = load_paid_data()
    # 下拉框英文列名
    accounts   = df_all['account_name'].unique().tolist() if not df_all.empty else []
    projects   = df_all['project_name'].unique().tolist() if not df_all.empty else []
    managers   = df_all['manager'].unique().tolist()      if not df_all.empty else []

    # 侧边栏筛选
    sel_account  = st.sidebar.selectbox("按账户筛选",   ["全部"] + accounts)
    sel_project  = st.sidebar.selectbox("按项目筛选",   ["全部"] + projects)
    sel_manager  = st.sidebar.selectbox("按经办人筛选", ["全部"] + managers)
    date_range   = st.sidebar.date_input("按日期区间", value=[], key="daterange")

    # ---------- 构造过滤表 ----------
    df_show = df_all.copy()
    if not df_show.empty:
        if sel_account != "全部":
            df_show = df_show[df_show['account_name'] == sel_account]
        if sel_project != "全部":
            df_show = df_show[df_show['project_name'] == sel_project]
        if sel_manager != "全部":
            df_show = df_show[df_show['manager'] == sel_manager]
        if len(date_range) == 2:
            start = pd.Timestamp(date_range[0])
            end   = pd.Timestamp(date_range[1])
            df_show = df_show[(df_show['date'] >= start) & (df_show['date'] <= end)]

    df_display = df_show.rename(columns=paid_mapping())
    # 展示前把日期转字符串
    if not df_display.empty:
        df_display['日期'] = df_show['date'].dt.strftime('%Y-%m-%d')

    # ---------- 展示 ----------
    real_idx = None
    if df_display.empty:
        st.info("暂无记录")
    else:
        selected = st.dataframe(
            df_display,
            hide_index=True,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row",
        )
        idx = selected["selection"]["rows"][0] if selected["selection"]["rows"] else None
        real_idx = df_display.index[idx] if idx is not None else None

    # ---------- 按钮 ----------
    col1, col2, col3, col4, col5 = st.columns(5)
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
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # 导出时转回中文列名（可选）
                df_export = df_show.rename(columns={
                    'date': '日期',
                    'voucher_number': '凭证号',
                    'project_name': '项目名称',
                    'amount_of_income': '收入金额',
                    'amount_of_expense': '支出金额',
                    'account_name': '账户名称',
                    'client_name': '客户名称',
                    'manager': '经办人',
                    'use_case': '用途'
                })
                df_export.to_excel(writer, index=False, sheet_name='收支记录')
            st.download_button(
                label="下载Excel文件",
                data=output.getvalue(),
                file_name=f"收支记录_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    with col5:
        # ===== 📥 导入 Excel =====
        if st.button("📥 导入Excel"):
            st.session_state.show_import = True
        if st.session_state.get("show_import"):
            uploaded = st.file_uploader(
                "请选择要导入的 Excel 文件",
                type=["xlsx"],
                key="paid_import"
            )
            if uploaded is not None:
                try:
                    df_up = pd.read_excel(uploaded)
                    df_up.columns = df_up.columns.str.strip()  # 去掉空格
                    rename_map = {
                        "日期": "date", "凭证号": "voucher_number", "项目名称": "project_name",
                        "收入金额": "amount_of_income", "支出金额": "amount_of_expense",
                        "使用账户": "account_name", "客户名称": "client_name",
                        "经办人": "manager", "用途": "use_case"
                    }
                    # 把字典 key 也转成小写，防止大小写不一致
                    rename_map = {k.lower(): v for k, v in rename_map.items()}
                    df_up = df_up.rename(columns=lambda c: rename_map.get(c.lower(), c))

                    # 1. 先尝试英文列名
                    need = {"date", "voucher_number", "project_name", "amount_of_income", "amount_of_expense",
                            "account_name", "client_name", "manager", "use_case"}

                    # 2. 如果不是英文，按中文映射
                    if not need.issubset(df_up.columns):
                        rename_map = {
                            "日期": "date", "凭证号": "voucher_number", "项目名称": "project_name",
                            "收入金额": "amount_of_income", "支出金额": "amount_of_expense",
                            "使用账户": "account_name", "客户名称": "client_name",
                            "经办人": "manager", "用途": "use_case"
                        }
                        df_up = df_up.rename(columns=rename_map)

                    # 3. 再次校验
                    missing = need - set(df_up.columns)
                    if missing:
                        st.error(f"列名不符，仍缺少：{missing}")
                        st.stop()

                    # 类型转换
                    df_up["date"] = pd.to_datetime(df_up["date"], errors="coerce")
                    num_cols = ["amount_of_income", "amount_of_expense"]
                    df_up[num_cols] = df_up[num_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

                    # 写入 SQLite
                    df_up.to_sql("paid_financial_data", engine, if_exists="append", index=False, method="multi")
                    st.success(f"已导入 {len(df_up)} 条记录！")
                    st.rerun()
                except Exception as e:
                    st.error(f"导入失败：{e}")

    # ---------- 弹窗 ----------
    if st.session_state.get("mode") == "add":
        st.subheader("➕ 新增记录")
        new_data = add_paid_form()
        if new_data:
            new_data['voucher_number'] = f"C-{len(df_all)+1:04d}"
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
    df_all = load_unpaid_data()          # 英文列名
    accounts = df_all['account_name'].unique().tolist() if not df_all.empty else []
    projects = df_all['project_name'].unique().tolist() if not df_all.empty else []
    managers = df_all['manager'].unique().tolist()      if not df_all.empty else []

    sel_account = st.sidebar.selectbox("按账户筛选",   ["全部"] + accounts)
    sel_project = st.sidebar.selectbox("按项目筛选",   ["全部"] + projects)
    sel_manager = st.sidebar.selectbox("按经办人筛选", ["全部"] + managers)
    date_range  = st.sidebar.date_input("按日期区间", value=[], key="daterange")

    # ---------- 构造过滤后的表 -----------
    df_show = df_all.copy()
    if not df_show.empty:
        if sel_account != "全部":
            df_show = df_show[df_show['account_name'] == sel_account]
        if sel_project != "全部":
            df_show = df_show[df_show['project_name'] == sel_project]
        if sel_manager != "全部":
            df_show = df_show[df_show['manager'] == sel_manager]
        if len(date_range) == 2:
            start = pd.Timestamp(date_range[0])
            end   = pd.Timestamp(date_range[1])
            df_show = df_show[(df_show['date'] >= start) & (df_show['date'] <= end)]

    # 日期 → yyyy-mm-dd 字符串（展示用）
    df_display = df_show.copy()
    if not df_display.empty:
        df_display['date'] = df_display['date'].dt.strftime('%Y-%m-%d')

    # 列名转中文展示（可选）
    zh_map = {
        'date':'日期','voucher_number':'凭证号','project_name':'项目名称',
        'amount_of_income':'收入金额','amount_of_expense':'支出金额',
        'account_name':'使用账户','client_name':'客户名称',
        'manager':'经办人','use_case':'用途'
    }
    df_display = df_display.rename(columns=zh_map)

    # ---------- 展示 ----------
    real_idx = None
    if df_display.empty:
        st.info("暂无记录")
    else:
        selected = st.dataframe(
            df_display,
            hide_index=True,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row",
        )
        idx = selected["selection"]["rows"][0] if selected["selection"]["rows"] else None
        real_idx = df_show.index[idx] if idx is not None else None

    # ---------- 按钮 ----------
    col1, col2, col3, col4, col5 = st.columns(5)
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
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_show.rename(columns=zh_map).to_excel(writer, index=False, sheet_name='收支记录')
            st.download_button(
                label="下载Excel文件",
                data=output.getvalue(),
                file_name=f"收支记录_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    with col5:
        if st.button("📥 导入Excel"):
            st.session_state.show_import = True
        if st.session_state.get("show_import"):
            uploaded = st.file_uploader(
                "请选择要导入的 Excel 文件",
                type=["xlsx"],
                key="unpaid_import"
            )
            if uploaded is not None:
                try:
                    df_up = pd.read_excel(uploaded)
                    # 统一空格+大小写+中文→英文
                    df_up.columns = df_up.columns.str.strip()
                    rename_map = {
                        "日期":"date","凭证号":"voucher_number","项目名称":"project_name",
                        "收入金额":"amount_of_income","支出金额":"amount_of_expense",
                        "账户名称":"account_name","客户名称":"client_name",
                        "经办人":"manager","用途":"use_case"
                    }
                    rename_map = {k.lower(): v for k, v in rename_map.items()}
                    df_up = df_up.rename(columns=lambda c: rename_map.get(c.lower(), c))

                    need = set(rename_map.values())
                    if not need.issubset(df_up.columns):
                        st.error(f"列名不符，缺少：{need - set(df_up.columns)}")
                        st.stop()

                    df_up["date"] = pd.to_datetime(df_up["date"], errors="coerce")
                    num_cols = ["amount_of_income","amount_of_expense"]
                    df_up[num_cols] = df_up[num_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

                    df_up.to_sql("unpaid_financial_data", engine, if_exists="append", index=False, method="multi")
                    st.success(f"已导入 {len(df_up)} 条记录！")
                    st.session_state.show_import = False
                    del st.session_state['unpaid_import']  # 强制 file_uploader 重置
                    st.rerun()
                except Exception as e:
                    st.error(f"导入失败：{e}")

    # ---------- 弹窗 ----------
    if st.session_state.get("mode") == "add":
        st.subheader("➕ 新增记录")
        new_data = add_unpaid_form()
        if new_data:
            new_data['voucher_number'] = f"W-{len(df_all)+1:04d}"
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



def account_mapping():
    ACCOUNT_COL_MAP = {
        'account_name': '账户名称',
        'opening_balance': '期初余额',
        'amount_of_income': '收入金额',
        'amount_of_expense': '支出金额',
        'difference': '差额'
    }
    return ACCOUNT_COL_MAP


def show_account(df):
    """账户管理页面（内部英文列，前端中文展示）"""
    # ---------- 初始化 Session ----------
    if 'account_data' not in st.session_state:
        st.session_state.account_data = load_account_data()

        required = ['account_name', 'opening_balance',
                    'amount_of_income', 'amount_of_expense', 'difference']
        for col in required:
            if col not in st.session_state.account_data.columns:
                st.session_state.account_data[col] = 0.0 if col != 'account_name' else ''

    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = None
    if 'edit_index' not in st.session_state:
        st.session_state.edit_index = None

    # ---------- 顶部按钮 ----------
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("账户资金统计")
    with col2:
        if st.button("➕ 新增账户", use_container_width=True):
            st.session_state.edit_mode = "add"
            st.session_state.edit_index = None

    # ---------- 1) 重新统计收支 ----------
    if not df.empty and {'account_name', 'amount_of_income', 'amount_of_expense'}.issubset(df.columns):
        new_stats = (df.groupby('account_name', as_index=False)
                       .agg({'amount_of_income': 'sum',
                             'amount_of_expense': 'sum'}))

        inc_dict = dict(zip(new_stats['account_name'], new_stats['amount_of_income']))
        exp_dict = dict(zip(new_stats['account_name'], new_stats['amount_of_expense']))

        mask = st.session_state.account_data['account_name'].isin(inc_dict.keys())
        st.session_state.account_data.loc[mask, 'amount_of_income'] = \
            st.session_state.account_data.loc[mask, 'account_name'].map(inc_dict)
        st.session_state.account_data.loc[mask, 'amount_of_expense'] = \
            st.session_state.account_data.loc[mask, 'account_name'].map(exp_dict)

    # ---------- 2) 已删账户清零 ----------
    all_accounts_in_df = set(df['account_name']) if not df.empty else set()
    mask_missing = ~st.session_state.account_data['account_name'].isin(all_accounts_in_df)
    st.session_state.account_data.loc[mask_missing, ['amount_of_income', 'amount_of_expense']] = 0.0

    # ---------- 3) 重新计算差额 ----------
    st.session_state.account_data['difference'] = (
        st.session_state.account_data['opening_balance'] +
        st.session_state.account_data['amount_of_income'] -
        st.session_state.account_data['amount_of_expense']
    )

    # ---------- 4) 中文列展示 ----------
    df_display = st.session_state.account_data.rename(columns=account_mapping())

    edited_display = st.data_editor(
        df_display,
        column_config={
            "期初余额": st.column_config.NumberColumn("期初余额", format="%.2f ¥", min_value=0, step=0.01),
            "收入金额": st.column_config.NumberColumn("收入", format="%.2f ¥", disabled=True),
            "支出金额": st.column_config.NumberColumn("支出", format="%.2f ¥", disabled=True),
            "差额":    st.column_config.NumberColumn("差额", format="%.2f ¥", disabled=True),
        },
        disabled=["账户名称", "收入金额", "支出金额", "差额"],
        hide_index=True,
        use_container_width=True,
        key="account_editor"
    )

    # ---------- 5) 保存 ----------
    edited_en = edited_display.rename(columns={v: k for k, v in account_mapping().items()})
    if not st.session_state.account_data.equals(edited_en):
        try:
            st.session_state.account_data = edited_en
            save_account_data(st.session_state.account_data)
            st.rerun()
        except Exception as e:
            st.error(f"保存数据时出错: {str(e)}")

    # ---------- 6) 新增 / 编辑弹窗 ----------
    if st.session_state.edit_mode in ["add", "edit"]:
        with st.form(key="account_form"):
            title = "➕ 新增账户" if st.session_state.edit_mode == "add" else "✏️ 编辑账户"
            st.subheader(title)

            cur = {}
            if st.session_state.edit_mode == "edit":
                cur = st.session_state.account_data.iloc[st.session_state.edit_index].to_dict()

            account_name = st.text_input("账户名称*", value=cur.get('account_name', ''))
            init_balance = st.number_input("期初余额*", min_value=0.0,
                                           value=float(cur.get('opening_balance', 0.0)),
                                           format="%.2f", step=0.01)

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("✅ 确认")
            with col2:
                cancel = st.form_submit_button("❌ 取消")

            if submit and account_name:
                new_row = {
                    "account_name": account_name,
                    "opening_balance": init_balance,
                    "amount_of_income": cur.get('amount_of_income', 0.0),
                    "amount_of_expense": cur.get('amount_of_expense', 0.0),
                    "difference": init_balance
                }
                if st.session_state.edit_mode == "add":
                    st.session_state.account_data = pd.concat([
                        st.session_state.account_data,
                        pd.DataFrame([new_row])
                    ], ignore_index=True)
                else:
                    st.session_state.account_data.iloc[st.session_state.edit_index] = new_row

                save_account_data(st.session_state.account_data)
                st.session_state.edit_mode = None
                st.rerun()
            elif submit:
                st.error("账户名称不能为空")

            if cancel:
                st.session_state.edit_mode = None
                st.rerun()

    # ---------- 7) 侧边栏导出 ----------
    st.sidebar.header("数据导出")
    export_format = st.sidebar.radio("导出格式", ["CSV", "Excel", "JSON"], horizontal=True)

    if st.sidebar.button("生成导出文件"):
        with st.spinner("正在生成文件..."):
            try:
                export_df = st.session_state.account_data.rename(columns=account_mapping())
                if export_format == "CSV":
                    data = export_df.to_csv(index=False).encode('utf-8-sig')
                    st.sidebar.download_button("下载CSV", data, "账户数据.csv", "text/csv")
                elif export_format == "Excel":
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as w:
                        export_df.to_excel(w, index=False, sheet_name='账户数据')
                    st.sidebar.download_button("下载Excel", buffer.getvalue(), "账户数据.xlsx",
                                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                elif export_format == "JSON":
                    st.sidebar.download_button("下载JSON", export_df.to_json(orient='records', force_ascii=False),
                                               "账户数据.json", "application/json")
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
        stats = monthly_stats()
        st.dataframe(stats)

        # 显示最新月份数据
        if not stats.empty:
            latest = stats.iloc[-1]
            col1, col2, col3 = st.columns(3)
            col1.metric("月份", latest['月份'])
            col2.metric("总收入", f"¥{latest['收入']:,.2f}")
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