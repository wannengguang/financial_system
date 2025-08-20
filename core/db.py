import os
import sqlite3
import streamlit as st
from sqlalchemy import create_engine

DB_FILE= os.path.join(
    r"D:\Pycharm_project\financial_system\data",
    "financial_system.db"
)
engine = create_engine(f"sqlite:///{DB_FILE}", echo=False, future=True)


# 2. 建表 SQL
DDL_ACCOUNT = """
CREATE TABLE IF NOT EXISTS account_data (
    account_name      TEXT PRIMARY KEY,
    opening_balance   REAL,
    amount_of_income  REAL DEFAULT 0.0,
    amount_of_expense REAL DEFAULT 0.0,
    difference        REAL
);"""

DDL_PAID = """
CREATE TABLE IF NOT EXISTS paid_financial_data (
    date            TEXT,
    voucher_number  TEXT PRIMARY KEY,
    project_name    TEXT,
    amount_of_income  REAL,
    amount_of_expense REAL,
    account_name    TEXT,
    client_name     TEXT,
    manager         TEXT,
    use_case        TEXT
);"""


DDL_UNPAID = """
CREATE TABLE IF NOT EXISTS unpaid_financial_data (
    date            TEXT,
    voucher_number  TEXT PRIMARY KEY,
    project_name    TEXT,
    amount_of_income  REAL,
    amount_of_expense REAL,
    account_name    TEXT,
    client_name     TEXT,
    manager         TEXT,
    use_case        TEXT
);"""

# 3. 单一缓存连接
@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.executescript(DDL_ACCOUNT + DDL_PAID + DDL_UNPAID)
    conn.commit()
    return conn